import uuid

from django.conf import settings
from django.db import models

from quizzes.enums import QuestionType
from recipes.enums import DrinkCategory, PreparationMethod


class QuizSession(models.Model):
    """
    One quiz attempt. Anonymous or authenticated.
    Filter fields are nullable — only the ones the user picked are set.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Optional: populated if the user is logged in
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quiz_sessions",
    )

    # --- Filters Chosen at Quiz Setup ---
    # All nullable: None means "no filter applied on this axis"
    filter_category = models.CharField(
        max_length=20,
        choices=DrinkCategory.choices,
        null=True,
        blank=True,
        help_text="Filter by drink category (Cocktail/Mocktail etc.)",
    )
    filter_method = models.CharField(
        max_length=128,
        choices=PreparationMethod.choices,
        null=True,
        blank=True,
        help_text="Filter by preparation method (Shaken/Stirred/Built etc.)",
    )
    filter_ingredient_category = models.ForeignKey(
        "recipes.IngredientCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quiz_sessions",
        help_text="Filter recipes that contain at least one ingredient from this category.",
    )

    # --- Progress & Scoring ---
    total_questions = models.PositiveSmallIntegerField()
    score = models.PositiveSmallIntegerField(default=0)
    is_complete = models.BooleanField(default=False)

    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        user_label = self.user.username if self.user else "anonymous"
        return f"QuizSession({user_label}, {self.total_questions}q, score={self.score})"

    @property
    def current_question_index(self):
        """0-based index of the next unanswered question."""
        return self.questions.filter(answered=True).count()

    @property
    def is_started(self):
        return self.questions.filter(answered=True).exists()

    class Meta:
        ordering = ["-created_on"]
        verbose_name = "Quiz Session"
        verbose_name_plural = "Quiz Sessions"


class QuizQuestion(models.Model):
    """
    A single question within a session.
    The 'correct answer' is derived from recipe + question_type at scoring time —
    it is never sent to the client directly.
    """

    session = models.ForeignKey(
        "quizzes.QuizSession",
        on_delete=models.CASCADE,
        related_name="questions",
    )
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="quiz_questions",
        help_text="The recipe this question is about.",
    )
    question_type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
    )

    # Position in the quiz (0-based)
    order = models.PositiveSmallIntegerField()

    # Tracks whether the user has submitted an answer for this question
    answered = models.BooleanField(default=False)
    answered_correctly = models.BooleanField(null=True, blank=True)

    # For AMOUNT questions we need to know which ingredient is being asked about
    # (e.g. "How much Campari goes in a Negroni?")
    target_ingredient = models.ForeignKey(
        "recipes.Ingredient",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="For AMOUNT question type only — the specific ingredient being asked about.",
    )

    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q{self.order} [{self.question_type}] — {self.recipe.title}"

    class Meta:
        ordering = ["order"]
        unique_together = [("session", "order")]
        verbose_name = "Quiz Question"
        verbose_name_plural = "Quiz Questions"


class QuizChoice(models.Model):
    """
    One of the shuffled answer choices for a question.
    Generated server-side. is_correct is stored but never sent to the client
    until after the user submits their answer.
    """

    question = models.ForeignKey(
        "quizzes.QuizQuestion",
        on_delete=models.CASCADE,
        related_name="choices",
    )

    # Human-readable label shown to the user (e.g. "Campari", "30ml", "Lime Juice")
    display_text = models.CharField(max_length=256)

    is_correct = models.BooleanField(default=False)

    # Display order (shuffled at generation time)
    order = models.PositiveSmallIntegerField()

    def __str__(self):
        marker = "✓" if self.is_correct else "✗"
        return f"{marker} {self.display_text}"

    class Meta:
        ordering = ["order"]
        unique_together = [("question", "order")]
        verbose_name = "Quiz Choice"
        verbose_name_plural = "Quiz Choices"
