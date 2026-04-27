import pytest
from rest_framework import status

from quizzes.tests.conftest import QuizFactory


@pytest.mark.django_db
class TestResultsAccess:

    def test_results_blocked_while_quiz_is_incomplete(
        self, api_client, started_session
    ):
        resp = api_client.get(f"/api/quizzes/{started_session.id}/results/")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_results_available_after_completion(self, api_client, completed_session):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        assert resp.status_code == status.HTTP_200_OK

    def test_unknown_session_returns_404(self, api_client, db):
        fake_id = "00000000-0000-0000-0000-000000000000"
        resp = api_client.get(f"/api/quizzes/{fake_id}/results/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestResultsScoring:

    def test_perfect_score_reported_correctly(self, api_client, recipe_pool):
        session = QuizFactory.completed_session(total_questions=3, all_correct=True)
        resp = api_client.get(f"/api/quizzes/{session.id}/results/")
        assert resp.data["score"] == 3
        assert resp.data["percentage"] == 100.0

    def test_zero_score_reported_correctly(self, api_client, recipe_pool):
        session = QuizFactory.completed_session(total_questions=3, all_correct=False)
        resp = api_client.get(f"/api/quizzes/{session.id}/results/")
        assert resp.data["score"] == 0
        assert resp.data["percentage"] == 0.0

    def test_percentage_rounds_to_one_decimal(self, api_client, recipe_pool):
        # 1 correct out of 3 = 33.3%
        session = QuizFactory.started_session(total_questions=3)
        questions = list(session.questions.order_by("order"))

        from quizzes.models import QuizChoice

        def submit(q, correct):
            choice = QuizChoice.objects.filter(question=q, is_correct=correct).first()
            q.answered = True
            q.answered_correctly = correct
            q.save(update_fields=["answered", "answered_correctly"])
            if correct:
                session.score += 1

        submit(questions[0], True)
        submit(questions[1], False)
        submit(questions[2], False)
        session.is_complete = True
        session.save(update_fields=["score", "is_complete", "last_modified"])

        resp = api_client.get(f"/api/quizzes/{session.id}/results/")
        assert resp.data["percentage"] == 33.3


@pytest.mark.django_db
class TestResultsShape:

    def test_response_includes_question_breakdown(self, api_client, completed_session):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        assert "questions" in resp.data
        assert len(resp.data["questions"]) == completed_session.total_questions

    def test_each_question_in_breakdown_has_recipe_name(
        self, api_client, completed_session
    ):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        for q in resp.data["questions"]:
            assert "recipe_name" in q
            assert len(q["recipe_name"]) > 0

    def test_each_question_in_breakdown_has_correct_answer(
        self, api_client, completed_session
    ):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        for q in resp.data["questions"]:
            assert "correct_answer" in q
            assert isinstance(q["correct_answer"], list)
            assert len(q["correct_answer"]) >= 1

    def test_each_question_has_answered_correctly_flag(
        self, api_client, completed_session
    ):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        for q in resp.data["questions"]:
            assert "answered_correctly" in q

    def test_response_includes_filters_applied(self, api_client, completed_session):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        assert "filters_applied" in resp.data
        filters = resp.data["filters_applied"]
        assert "category" in filters
        assert "method" in filters
        assert "ingredient_category" in filters

    def test_response_includes_total_questions(self, api_client, completed_session):
        resp = api_client.get(f"/api/quizzes/{completed_session.id}/results/")
        assert resp.data["total_questions"] == completed_session.total_questions
