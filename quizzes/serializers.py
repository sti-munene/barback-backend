from rest_framework import serializers

from quizzes.enums import QuestionType
from quizzes.models import QuizChoice, QuizQuestion, QuizSession
from quizzes.services.generator import generate_quiz_questions

# ---------------------------------------------------------------------------
# Inbound: start a quiz
# ---------------------------------------------------------------------------


class QuizStartSerializer(serializers.Serializer):
    """Validates the quiz setup form and creates the session + questions."""

    total_questions = serializers.IntegerField(min_value=1, max_value=30)
    filter_category = serializers.CharField(required=False, allow_blank=True)
    filter_method = serializers.CharField(required=False, allow_blank=True)
    filter_ingredient_category = serializers.IntegerField(
        required=False, allow_null=True
    )

    def validate_filter_category(self, value):
        from recipes.enums import DrinkCategory

        if value and value not in DrinkCategory.values:
            raise serializers.ValidationError(
                f"Invalid category. Choices: {DrinkCategory.values}"
            )
        return value or None

    def validate_filter_method(self, value):
        from recipes.enums import PreparationMethod

        if value and value not in PreparationMethod.values:
            raise serializers.ValidationError(
                f"Invalid method. Choices: {PreparationMethod.values}"
            )
        return value or None

    def validate_filter_ingredient_category(self, value):
        if value is None:
            return None
        from recipes.models import IngredientCategory

        if not IngredientCategory.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Ingredient category not found.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user if request.user.is_authenticated else None

        ingredient_category_id = validated_data.pop("filter_ingredient_category", None)

        session = QuizSession.objects.create(
            user=user,
            total_questions=validated_data["total_questions"],
            filter_category=validated_data.get("filter_category"),
            filter_method=validated_data.get("filter_method"),
            filter_ingredient_category_id=ingredient_category_id,
        )

        try:
            generate_quiz_questions(session)
        except ValueError as exc:
            # Not enough recipes — clean up and surface a friendly error
            session.delete()
            raise serializers.ValidationError({"detail": str(exc)})

        return session


# ---------------------------------------------------------------------------
# Outbound: question display
# ---------------------------------------------------------------------------


class QuizChoiceSerializer(serializers.ModelSerializer):
    """Safe — never includes is_correct."""

    class Meta:
        model = QuizChoice
        fields = ["id", "display_text", "order"]


class QuizQuestionSerializer(serializers.ModelSerializer):
    """
    Returns the question prompt + shuffled choices.
    The prompt is derived from question_type + recipe so we don't store
    redundant text in the DB.
    """

    choices = QuizChoiceSerializer(many=True, read_only=True)
    prompt = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "order",
            "question_type",
            "prompt",
            "choices",
            "answered",
            "progress",
        ]

    def get_prompt(self, obj: QuizQuestion) -> str:
        recipe_name = obj.recipe.title

        if obj.question_type == QuestionType.INGREDIENTS:
            return f"Which of these ingredients is in a {recipe_name}?"

        if obj.question_type == QuestionType.NEGATIVE:
            return f"Which of these is NOT an ingredient in a {recipe_name}?"

        if obj.question_type == QuestionType.AMOUNT:
            ingredient_name = (
                obj.target_ingredient.title
                if obj.target_ingredient
                else "this ingredient"
            )
            return f"How much {ingredient_name} goes in a {recipe_name}?"

        if obj.question_type == QuestionType.IDENTIFY_RECIPE:
            return f"Which of these ingredient lists makes a {recipe_name}?"

        if obj.question_type == QuestionType.IDENTIFY_VESSEL:
            return f"What glass is a {recipe_name} served in?"

        if obj.question_type == QuestionType.IDENTIFY_METHOD:
            return f"How is a {recipe_name} prepared?"

        return f"Question about {recipe_name}"

    def get_progress(self, obj: QuizQuestion) -> dict:
        session = obj.session
        return {
            "current": obj.order + 1,  # 1-based for display
            "total": session.total_questions,
            "score": session.score,
        }


# ---------------------------------------------------------------------------
# Inbound: submit an answer
# ---------------------------------------------------------------------------


class QuizAnswerSerializer(serializers.Serializer):
    """
    Accepts a choice ID, validates it belongs to the question,
    scores it, and marks the question answered.
    """

    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField()

    def validate(self, data):
        try:
            question = QuizQuestion.objects.select_related("session").get(
                pk=data["question_id"]
            )
        except QuizQuestion.DoesNotExist:
            raise serializers.ValidationError({"question_id": "Question not found."})

        if question.answered:
            raise serializers.ValidationError(
                {"question_id": "This question has already been answered."}
            )

        if question.session.is_complete:
            raise serializers.ValidationError(
                {"detail": "This quiz session is already complete."}
            )

        try:
            choice = QuizChoice.objects.get(pk=data["choice_id"], question=question)
        except QuizChoice.DoesNotExist:
            raise serializers.ValidationError(
                {"choice_id": "Choice not found for this question."}
            )

        data["question"] = question
        data["choice"] = choice
        return data

    def save(self, **kwargs):
        question: QuizQuestion = self.validated_data["question"]
        choice: QuizChoice = self.validated_data["choice"]
        session: QuizSession = question.session

        is_correct = choice.is_correct

        # Mark question
        question.answered = True
        question.answered_correctly = is_correct
        question.save(update_fields=["answered", "answered_correctly"])

        # Update score
        if is_correct:
            session.score += 1

        # Check if this was the last question
        answered_count = session.questions.filter(answered=True).count()
        if answered_count >= session.total_questions:
            session.is_complete = True

        session.save(update_fields=["score", "is_complete", "last_modified"])

        return {
            "correct": is_correct,
            "correct_choices": QuizChoiceSerializer(
                choice.__class__.objects.filter(question=question, is_correct=True),
                many=True,
            ).data,
            "is_complete": session.is_complete,
            "next_question_index": (
                question.order + 1 if not session.is_complete else None
            ),
        }


# ---------------------------------------------------------------------------
# Outbound: results
# ---------------------------------------------------------------------------


class QuizQuestionResultSerializer(serializers.ModelSerializer):
    """Per-question breakdown shown on the results screen."""

    recipe_name = serializers.CharField(source="recipe.title", read_only=True)
    prompt = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()
    your_answer = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = [
            "id",
            "order",
            "question_type",
            "recipe_name",
            "prompt",
            "answered_correctly",
            "correct_answer",
            "your_answer",
        ]

    def get_prompt(self, obj: QuizQuestion) -> str:
        # Reuse the same logic as QuizQuestionSerializer
        return QuizQuestionSerializer().get_prompt(obj)

    def get_correct_answer(self, obj: QuizQuestion) -> list[str]:
        """
        Returns all correct answers — a list because some question types
        (e.g. IDENTIFY_VESSEL) can have multiple valid answers (primary + alt vessels).
        """
        return list(
            obj.choices.filter(is_correct=True).values_list("display_text", flat=True)
        )

    def get_your_answer(self, obj: QuizQuestion) -> str | None:
        # We don't store which choice the user picked — only whether they were correct.
        # If you want to show their exact pick later, add a `user_choice` FK to QuizQuestion.
        return None


class QuizResultsSerializer(serializers.ModelSerializer):
    questions = QuizQuestionResultSerializer(many=True, read_only=True)
    percentage = serializers.SerializerMethodField()
    filters_applied = serializers.SerializerMethodField()

    class Meta:
        model = QuizSession
        fields = [
            "id",
            "total_questions",
            "score",
            "percentage",
            "is_complete",
            "filters_applied",
            "questions",
            "created_on",
        ]

    def get_percentage(self, obj: QuizSession) -> float:
        if obj.total_questions == 0:
            return 0.0
        return round((obj.score / obj.total_questions) * 100, 1)

    def get_filters_applied(self, obj: QuizSession) -> dict:
        return {
            "category": obj.filter_category,
            "method": obj.filter_method,
            "ingredient_category": (
                obj.filter_ingredient_category.title
                if obj.filter_ingredient_category
                else None
            ),
        }


# ---------------------------------------------------------------------------
# Outbound: session list (history for logged-in users)
# ---------------------------------------------------------------------------


class QuizSessionListSerializer(serializers.ModelSerializer):
    percentage = serializers.SerializerMethodField()

    class Meta:
        model = QuizSession
        fields = [
            "id",
            "total_questions",
            "score",
            "percentage",
            "is_complete",
            "filter_category",
            "filter_method",
            "created_on",
        ]

    def get_percentage(self, obj: QuizSession) -> float:
        if obj.total_questions == 0:
            return 0.0
        return round((obj.score / obj.total_questions) * 100, 1)
