"""
quizzes/tests/test_answer.py

Tests for POST /api/quizzes/{id}/answer/
The most critical endpoint — handles scoring, feedback, and session completion.
"""

import pytest
from rest_framework import status

from quizzes.models import QuizChoice


def get_first_unanswered(session):
    return session.questions.filter(answered=False).order_by("order").first()


def correct_choice_for(question):
    return QuizChoice.objects.get(question=question, is_correct=True)


def wrong_choice_for(question):
    return QuizChoice.objects.filter(question=question, is_correct=False).first()


def submit_answer(api_client, session, question, choice):
    return api_client.post(
        f"/api/quizzes/{session.id}/answer/",
        {"question_id": question.id, "choice_id": choice.id},
        format="json",
    )


@pytest.mark.django_db
class TestCorrectAnswer:

    def test_returns_200(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = correct_choice_for(question)
        resp = submit_answer(api_client, started_session, question, choice)
        assert resp.status_code == status.HTTP_200_OK

    def test_correct_flag_is_true(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = correct_choice_for(question)
        resp = submit_answer(api_client, started_session, question, choice)
        assert resp.data["correct"] is True

    def test_score_increments_by_one(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = correct_choice_for(question)
        submit_answer(api_client, started_session, question, choice)
        started_session.refresh_from_db()
        assert started_session.score == 1


@pytest.mark.django_db
class TestWrongAnswer:

    def test_returns_200(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = wrong_choice_for(question)
        resp = submit_answer(api_client, started_session, question, choice)
        assert resp.status_code == status.HTTP_200_OK

    def test_correct_flag_is_false(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = wrong_choice_for(question)
        resp = submit_answer(api_client, started_session, question, choice)
        assert resp.data["correct"] is False

    def test_score_does_not_increment(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = wrong_choice_for(question)
        submit_answer(api_client, started_session, question, choice)
        started_session.refresh_from_db()
        assert started_session.score == 0

    def test_response_reveals_correct_choice(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = wrong_choice_for(question)
        resp = submit_answer(api_client, started_session, question, choice)
        assert "correct_choices" in resp.data
        assert isinstance(resp.data["correct_choices"], list)
        assert len(resp.data["correct_choices"]) >= 1
        assert "display_text" in resp.data["correct_choices"][0]


@pytest.mark.django_db
class TestAnswerFeedback:

    def test_response_always_includes_is_complete_flag(
        self, api_client, started_session
    ):
        question = get_first_unanswered(started_session)
        resp = submit_answer(
            api_client, started_session, question, correct_choice_for(question)
        )
        assert "is_complete" in resp.data

    def test_next_question_index_present_when_not_last(
        self, api_client, started_session
    ):
        question = get_first_unanswered(started_session)
        resp = submit_answer(
            api_client, started_session, question, correct_choice_for(question)
        )
        assert resp.data["next_question_index"] is not None

    def test_next_question_index_is_none_on_last_question(
        self, api_client, started_session
    ):
        # Answer all but the last question first
        questions = list(started_session.questions.order_by("order"))
        for question in questions[:-1]:
            submit_answer(
                api_client, started_session, question, correct_choice_for(question)
            )

        last = questions[-1]
        resp = submit_answer(
            api_client, started_session, last, correct_choice_for(last)
        )
        assert resp.data["next_question_index"] is None

    def test_is_complete_true_after_final_answer(self, api_client, started_session):
        for question in started_session.questions.order_by("order"):
            resp = submit_answer(
                api_client, started_session, question, correct_choice_for(question)
            )
        assert resp.data["is_complete"] is True


@pytest.mark.django_db
class TestAnswerValidation:

    def test_cannot_answer_same_question_twice(self, api_client, started_session):
        question = get_first_unanswered(started_session)
        choice = correct_choice_for(question)
        submit_answer(api_client, started_session, question, choice)
        resp = submit_answer(api_client, started_session, question, choice)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_choice_from_different_question_is_rejected(
        self, api_client, started_session
    ):
        questions = list(started_session.questions.order_by("order"))
        q1, q2 = questions[0], questions[1]
        # Use a choice from q2 to answer q1
        wrong_question_choice = QuizChoice.objects.filter(question=q2).first()
        resp = submit_answer(api_client, started_session, q1, wrong_question_choice)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_nonexistent_question_id_is_rejected(self, api_client, started_session):
        resp = api_client.post(
            f"/api/quizzes/{started_session.id}/answer/",
            {"question_id": 99999, "choice_id": 99999},
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_answer_a_completed_session(self, api_client, started_session):
        # Complete the session
        for question in started_session.questions.order_by("order"):
            submit_answer(
                api_client, started_session, question, correct_choice_for(question)
            )

        # Try to answer again
        first_question = started_session.questions.order_by("order").first()
        resp = api_client.post(
            f"/api/quizzes/{started_session.id}/answer/",
            {
                "question_id": first_question.id,
                "choice_id": correct_choice_for(first_question).id,
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSessionCompletionOnAnswer:

    def test_session_marked_complete_after_final_answer(
        self, api_client, started_session
    ):
        for question in started_session.questions.order_by("order"):
            submit_answer(
                api_client, started_session, question, correct_choice_for(question)
            )
        started_session.refresh_from_db()
        assert started_session.is_complete is True

    def test_session_not_complete_after_partial_answers(
        self, api_client, started_session
    ):
        question = get_first_unanswered(started_session)
        submit_answer(
            api_client, started_session, question, correct_choice_for(question)
        )
        started_session.refresh_from_db()
        assert started_session.is_complete is False
