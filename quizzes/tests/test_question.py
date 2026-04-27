"""
quizzes/tests/test_question.py

Tests for GET /api/quizzes/{id}/question/
"""

import pytest
from rest_framework import status

from quizzes.tests.conftest import QuizFactory


@pytest.mark.django_db
class TestFetchQuestion:

    def test_returns_200_for_valid_session(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert resp.status_code == status.HTTP_200_OK

    def test_response_contains_prompt(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert "prompt" in resp.data
        assert len(resp.data["prompt"]) > 0

    def test_response_contains_choices(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert "choices" in resp.data
        assert len(resp.data["choices"]) >= 2

    def test_response_contains_question_type(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert "question_type" in resp.data

    def test_response_contains_progress(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        progress = resp.data["progress"]
        assert progress["current"] == 1
        assert progress["total"] == started_session.total_questions

    def test_unknown_session_returns_404(self, api_client, db):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = api_client.get(f"/api/quizzes/{fake_id}/question/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestChoicesSafety:

    def test_is_correct_field_is_never_exposed(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        for choice in resp.data["choices"]:
            assert "is_correct" not in choice

    def test_each_choice_has_display_text(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        for choice in resp.data["choices"]:
            assert "display_text" in choice
            assert len(choice["display_text"]) > 0

    def test_each_choice_has_an_id(self, api_client, started_session):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        for choice in resp.data["choices"]:
            assert "id" in choice


@pytest.mark.django_db
class TestProgressTracking:

    def test_progress_advances_after_answering(self, api_client, started_session):
        from quizzes.models import QuizChoice

        # Answer question 1
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        question_id = resp.data["id"]
        choice_id = resp.data["choices"][0]["id"]
        api_client.post(
            f"/api/quizzes/{started_session.id}/answer/",
            {"question_id": question_id, "choice_id": choice_id},
            format="json",
        )

        # Fetch question 2
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert resp.data["progress"]["current"] == 2

    def test_completed_session_returns_complete_message(
        self, api_client, completed_session
    ):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/question/")
        assert resp.status_code == status.HTTP_200_OK
        assert "complete" in resp.data.get("detail", "").lower()


@pytest.mark.django_db
class TestSessionOwnershipOnQuestion:

    def test_other_user_cannot_fetch_another_users_question(
        self, api_client, other_user, recipe_pool, user
    ):
        session = QuizFactory.started_session(total_questions=3, user=user)
        api_client.force_authenticate(user=other_user)
        resp = api_client.get(f"/api/quizzes/{session.id}/question/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_anonymous_user_can_access_anonymous_session(
        self, api_client, started_session
    ):
        # started_session has no user attached
        resp = api_client.get(f"/api/quizzes/{started_session.id}/question/")
        assert resp.status_code == status.HTTP_200_OK
