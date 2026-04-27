"""
Tests for quizzes/services/generator.py.
Focuses on the core question-building logic in isolation —
no HTTP, no serializers.
"""

import pytest

from quizzes.enums import QuestionType
from quizzes.models import QuizChoice, QuizQuestion
from quizzes.services.generator import generate_quiz_questions
from quizzes.tests.conftest import QuizFactory, RecipeFactory


@pytest.mark.django_db
class TestGeneratorQuestionCount:

    def test_creates_exact_number_of_questions(self, recipe_pool):
        session = QuizFactory.session(total_questions=3)
        questions = generate_quiz_questions(session)
        assert len(questions) == 3

    def test_questions_persisted_to_db(self, recipe_pool):
        session = QuizFactory.session(total_questions=3)
        generate_quiz_questions(session)
        assert QuizQuestion.objects.filter(session=session).count() == 3

    def test_raises_when_pool_too_small(self, recipe_pool):
        # recipe_pool has 5 recipes — requesting more should fail
        session = QuizFactory.session(total_questions=10)
        with pytest.raises(ValueError, match="Not enough recipes"):
            generate_quiz_questions(session)


@pytest.mark.django_db
class TestGeneratorChoices:

    def test_every_question_has_at_least_two_choices(self, recipe_pool):
        session = QuizFactory.session(total_questions=3)
        questions = generate_quiz_questions(session)
        for question in questions:
            count = QuizChoice.objects.filter(question=question).count()
            assert count >= 2, f"Question {question.id} only has {count} choice(s)"

    def test_every_question_has_exactly_one_correct_choice(self, recipe_pool):
        session = QuizFactory.session(total_questions=3)
        questions = generate_quiz_questions(session)
        for question in questions:
            correct_count = QuizChoice.objects.filter(
                question=question, is_correct=True
            ).count()
            assert (
                correct_count == 1
            ), f"Question {question.id} has {correct_count} correct choice(s)"

    def test_choices_are_shuffled_across_runs(self, db):
        """
        The correct choice should not always land in position 0.
        Run 10 independent sessions and assert we see more than one position.
        """
        RecipeFactory.recipe_pool(n=5)
        positions = set()
        for _ in range(10):
            session = QuizFactory.session(total_questions=1)
            generate_quiz_questions(session)
            question = QuizQuestion.objects.filter(session=session).first()
            correct = QuizChoice.objects.get(question=question, is_correct=True)
            positions.add(correct.order)

        assert (
            len(positions) > 1
        ), "Correct choice always in position 0 — shuffle not working"


@pytest.mark.django_db
class TestGeneratorQuestionTypes:

    def test_all_question_types_are_valid(self, recipe_pool):
        valid_types = {qt.value for qt in QuestionType}
        session = QuizFactory.session(total_questions=5)
        questions = generate_quiz_questions(session)
        for question in questions:
            assert question.question_type in valid_types

    def test_amount_questions_always_have_a_target_ingredient(self, recipe_pool):
        session = QuizFactory.session(total_questions=5)
        questions = generate_quiz_questions(session)
        for question in questions:
            if question.question_type == QuestionType.AMOUNT:
                assert (
                    question.target_ingredient is not None
                ), f"AMOUNT question {question.id} missing target_ingredient"

    def test_non_amount_questions_have_no_target_ingredient(self, recipe_pool):
        session = QuizFactory.session(total_questions=5)
        questions = generate_quiz_questions(session)
        for question in questions:
            if question.question_type != QuestionType.AMOUNT:
                assert question.target_ingredient is None


@pytest.mark.django_db
class TestGeneratorFilters:

    def test_category_filter_excludes_other_categories(self, db):
        from recipes.enums import DrinkCategory

        RecipeFactory.recipe_pool(n=5, category=DrinkCategory.COCKTAIL)
        RecipeFactory.recipe_pool(n=5, category=DrinkCategory.MOCKTAIL)

        session = QuizFactory.session(
            total_questions=3,
            filter_category=DrinkCategory.COCKTAIL,
        )
        generate_quiz_questions(session)

        for question in QuizQuestion.objects.filter(session=session):
            assert question.recipe.category == DrinkCategory.COCKTAIL

    def test_method_filter_excludes_other_methods(self, db):
        from recipes.enums import PreparationMethod

        RecipeFactory.recipe_pool(n=5)  # default: STIRRED
        for _ in range(5):
            recipe = RecipeFactory.full_recipe()
            recipe.method = PreparationMethod.SHAKEN
            recipe.save()

        session = QuizFactory.session(
            total_questions=3,
            filter_method=PreparationMethod.STIRRED,
        )
        generate_quiz_questions(session)

        for question in QuizQuestion.objects.filter(session=session):
            assert question.recipe.method == PreparationMethod.STIRRED
