"""
quizzes/tests/test_history.py

Tests for GET /api/quizzes/ (session history) and session ownership rules
across all endpoints.
"""

import pytest
from rest_framework import status

from quizzes.tests.conftest import QuizFactory

ENDPOINT = "/api/quizzes/"


@pytest.mark.django_db
class TestHistory:

    def test_anonymous_user_cannot_list_history(self, api_client, db):
        resp = api_client.get(ENDPOINT)
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_authenticated_user_can_list_history(self, auth_client, user, recipe_pool):
        QuizFactory.started_session(total_questions=3, user=user)
        resp = auth_client.get(ENDPOINT)
        assert resp.status_code == status.HTTP_200_OK

    def test_user_sees_only_their_own_sessions(
        self, auth_client, user, other_user, recipe_pool
    ):
        QuizFactory.started_session(total_questions=3, user=user)
        QuizFactory.started_session(total_questions=3, user=other_user)
        resp = auth_client.get(ENDPOINT)
        assert len(resp.data) == 1

    def test_user_with_no_sessions_gets_empty_list(self, auth_client, db):
        resp = auth_client.get(ENDPOINT)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data == []

    def test_multiple_sessions_all_returned(self, auth_client, user, recipe_pool):
        QuizFactory.started_session(total_questions=3, user=user)
        QuizFactory.started_session(total_questions=3, user=user)
        resp = auth_client.get(ENDPOINT)
        assert len(resp.data) == 2

    def test_history_item_includes_score_and_percentage(
        self, auth_client, user, recipe_pool
    ):
        QuizFactory.completed_session(total_questions=3, user=user, all_correct=True)
        resp = auth_client.get(ENDPOINT)
        item = resp.data[0]
        assert "score" in item
        assert "percentage" in item

    def test_history_item_includes_completion_status(
        self, auth_client, user, recipe_pool
    ):
        QuizFactory.completed_session(total_questions=3, user=user)
        resp = auth_client.get(ENDPOINT)
        assert "is_complete" in resp.data[0]


@pytest.mark.django_db
class TestSessionOwnershipOnQuestion:
    """Other users and anonymous cannot access a user-owned session."""

    def test_owner_can_fetch_their_own_question(self, api_client, user, recipe_pool):
        session = QuizFactory.started_session(total_questions=3, user=user)
        api_client.force_authenticate(user=user)
        resp = api_client.get(f"/api/quizzes/{session.id}/question/")
        assert resp.status_code == status.HTTP_200_OK

    def test_other_user_cannot_fetch_question_from_another_users_session(
        self, api_client, user, other_user, recipe_pool
    ):
        session = QuizFactory.started_session(total_questions=3, user=user)
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"/api/quizzes/{session.id}/question/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_cannot_fetch_question_from_user_session(
        self, api_client, user, recipe_pool
    ):
        session = QuizFactory.started_session(total_questions=3, user=user)
        api_client.force_authenticate(user=None)
        resp = api_client.get(f"/api/quizzes/{session.id}/question/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_can_access_anonymous_session(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert resp.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSessionOwnershipOnAnswer:

    def test_other_user_cannot_answer_another_users_question(
        self, api_client, user, other_user, recipe_pool
    ):
        from quizzes.models import QuizChoice

        session = QuizFactory.started_session(total_questions=3, user=user)
        question = session.questions.order_by("order").first()
        choice = QuizChoice.objects.filter(question=question).first()

        api_client.force_authenticate(user=other_user)
        resp = api_client.post(
            f"/api/quizzes/{session.id}/answer/",
            {"question_id": question.id, "choice_id": choice.id},
            format="json",
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestSessionOwnershipOnResults:

    def test_other_user_cannot_view_another_users_results(
        self, api_client, user, other_user, recipe_pool
    ):
        session = QuizFactory.completed_session(total_questions=3, user=user)
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"/api/quizzes/{session.id}/results/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
