"""
quizzes/tests/test_start.py

Tests for POST /api/quizzes/ — starting a new quiz session.
"""

import pytest
from rest_framework import status

from quizzes.models import QuizSession
from quizzes.tests.conftest import RecipeFactory

ENDPOINT = "/api/quizzes/"


@pytest.mark.django_db
class TestAnonymousStart:

    def test_anonymous_user_can_start_a_quiz(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_response_contains_session_id(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        assert "session_id" in resp.data

    def test_response_contains_total_questions(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        assert resp.data["total_questions"] == 3

    def test_anonymous_session_has_no_user_attached(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        session = QuizSession.objects.get(pk=resp.data["session_id"])
        assert session.user is None

    def test_questions_are_generated_on_start(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        session = QuizSession.objects.get(pk=resp.data["session_id"])
        assert session.questions.count() == 3


@pytest.mark.django_db
class TestAuthenticatedStart:

    def test_authenticated_user_can_start_a_quiz(self, auth_client, recipe_pool):
        resp = auth_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_authenticated_session_has_user_attached(
        self, auth_client, user, recipe_pool
    ):
        resp = auth_client.post(ENDPOINT, {"total_questions": 3}, format="json")
        session = QuizSession.objects.get(pk=resp.data["session_id"])
        assert session.user == user


@pytest.mark.django_db
class TestStartValidation:

    def test_zero_questions_is_rejected(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": 0}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_negative_questions_is_rejected(self, api_client, recipe_pool):
        resp = api_client.post(ENDPOINT, {"total_questions": -1}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_exceeding_pool_size_is_rejected(self, api_client, recipe_pool):
        # recipe_pool has 5 recipes
        resp = api_client.post(ENDPOINT, {"total_questions": 20}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_category_filter_is_rejected(self, api_client, recipe_pool):
        resp = api_client.post(
            ENDPOINT,
            {"total_questions": 3, "filter_category": "beer"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_invalid_method_filter_is_rejected(self, api_client, recipe_pool):
        resp = api_client.post(
            ENDPOINT,
            {"total_questions": 3, "filter_method": "teleportation"},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_ingredient_category_is_rejected(self, api_client, recipe_pool):
        resp = api_client.post(
            ENDPOINT,
            {"total_questions": 3, "filter_ingredient_category": 99999},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestStartWithFilters:

    def test_can_start_with_category_filter(self, api_client, db):
        from recipes.enums import DrinkCategory

        RecipeFactory.recipe_pool(n=5, category=DrinkCategory.COCKTAIL)
        resp = api_client.post(
            ENDPOINT,
            {"total_questions": 3, "filter_category": DrinkCategory.COCKTAIL},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED

    def test_can_start_with_ingredient_category_filter(self, api_client, db):
        ing_cat = RecipeFactory.ingredient_category(title="Rum")
        for _ in range(5):
            recipe = RecipeFactory.recipe()
            ing = RecipeFactory.ingredient(category=ing_cat)
            RecipeFactory.recipe_ingredient(recipe, ingredient=ing)
        resp = api_client.post(
            ENDPOINT,
            {"total_questions": 3, "filter_ingredient_category": ing_cat.id},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
