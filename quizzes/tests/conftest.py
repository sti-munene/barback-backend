import pytest
from faker import Faker
from rest_framework.test import APIClient

from quizzes.models import QuizChoice, QuizSession
from quizzes.services.generator import generate_quiz_questions
from recipes.enums import DrinkCategory, MeasurementUnit, PreparationMethod
from recipes.models import (
    Ingredient,
    IngredientCategory,
    Recipe,
    RecipeIngredient,
    Vessel,
)

"""
All factories and shared pytest fixtures live here.
Imported automatically by pytest for every test in this package.

Factories
All return model instances saved to the DB.
Every factory is a plain function so it's easy to call with overrides.

"""

fake = Faker()


class RecipeFactory:
    """Creates Recipe-related objects with sensible faker defaults."""

    @staticmethod
    def vessel(name=None):
        return Vessel.objects.create(name=name or fake.word())

    @staticmethod
    def ingredient_category(title=None):
        return IngredientCategory.objects.create(title=title or fake.word())

    @staticmethod
    def ingredient(title=None, category=None):
        return Ingredient.objects.create(
            title=title or fake.word(),
            category=category or RecipeFactory.ingredient_category(),
        )

    @staticmethod
    def recipe(
        title=None,
        category=DrinkCategory.COCKTAIL,
        method=PreparationMethod.STIRRED,
        serving_temperature="cold",
        vessel=None,
    ):
        return Recipe.objects.create(
            title=title or fake.unique.bothify("???? ????").title(),
            category=category,
            method=method,
            serving_temperature=serving_temperature,
            primary_vessel=vessel or RecipeFactory.vessel(),
        )

    @staticmethod
    def recipe_ingredient(
        recipe, ingredient=None, measurement_unit=MeasurementUnit.ML, amount=30
    ):
        return RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient or RecipeFactory.ingredient(),
            measurement_unit=measurement_unit,
            amount=amount,
        )

    @staticmethod
    def full_recipe(title=None, n_ingredients=3, category=DrinkCategory.COCKTAIL):
        """
        A recipe with n ingredients attached — the minimum needed
        for the generator to produce meaningful choices.
        """
        recipe = RecipeFactory.recipe(title=title, category=category)
        for i in range(n_ingredients):
            ing = RecipeFactory.ingredient()
            RecipeFactory.recipe_ingredient(recipe, ingredient=ing, amount=(i + 1) * 15)
        return recipe

    @staticmethod
    def recipe_pool(n=5, category=DrinkCategory.COCKTAIL):
        """A list of n distinct full recipes — used as the generator pool."""
        return [RecipeFactory.full_recipe(category=category) for _ in range(n)]


class QuizFactory:
    """Creates QuizSession objects and drives them through states."""

    @staticmethod
    def session(total_questions=3, user=None, **kwargs):
        return QuizSession.objects.create(
            total_questions=total_questions,
            user=user,
            **kwargs,
        )

    @staticmethod
    def started_session(total_questions=3, user=None, **kwargs):
        """Session with questions generated — ready to play."""
        session = QuizFactory.session(
            total_questions=total_questions,
            user=user,
            **kwargs,
        )
        generate_quiz_questions(session)
        return session

    @staticmethod
    def completed_session(total_questions=3, user=None, all_correct=True):
        """
        A fully answered session.
        all_correct=True  → every question answered correctly (max score)
        all_correct=False → every question answered wrong (score = 0)
        """
        session = QuizFactory.started_session(
            total_questions=total_questions,
            user=user,
        )
        for question in session.questions.order_by("order"):
            choice = QuizChoice.objects.filter(
                question=question,
                is_correct=all_correct,
            ).first()
            question.answered = True
            question.answered_correctly = all_correct
            question.save(update_fields=["answered", "answered_correctly"])

            if all_correct:
                session.score += 1

        session.is_complete = True
        session.save(update_fields=["score", "is_complete", "last_modified"])
        return session


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        username=fake.unique.user_name(),
        password=fake.password(),
    )


@pytest.fixture
def other_user(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.create_user(
        username=fake.unique.user_name(),
        password=fake.password(),
    )


@pytest.fixture
def auth_client(api_client, user):
    """An APIClient already authenticated as `user`."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def recipe_pool(db):
    """Five cocktail recipes — enough for a 3-question quiz with distractors."""
    return RecipeFactory.recipe_pool(n=5)


@pytest.fixture
def started_session(db, recipe_pool):
    """A 3-question session with questions generated, ready to play."""
    return QuizFactory.started_session(total_questions=3)


@pytest.fixture
def completed_session(db, recipe_pool):
    """A fully answered session with a perfect score."""
    return QuizFactory.completed_session(total_questions=3, all_correct=True)
