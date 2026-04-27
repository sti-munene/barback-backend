from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin, ListModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from quizzes.models import QuizSession
from quizzes.serializers import (
    QuizAnswerSerializer,
    QuizQuestionSerializer,
    QuizResultsSerializer,
    QuizSessionListSerializer,
    QuizStartSerializer,
)


class QuizSessionViewSet(CreateModelMixin, ListModelMixin, GenericViewSet):
    """
    ViewSet for quiz sessions.

    Anonymous users can start and play quizzes.
    Only authenticated users can list their history.

    One viewset, five actions:

    POST   /quizzes/                       → start (create)
    GET    /quizzes/                       → list  (history, auth required)
    GET    /quizzes/{id}/question/         → current unanswered question
    POST   /quizzes/{id}/answer/           → submit an answer
    GET    /quizzes/{id}/results/          → full results breakdown
    """

    # Default — overridden per-action in get_permissions()
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        List only returns the current user's sessions.
        All other actions look up by UUID pk.
        """
        if self.request.user.is_authenticated:
            return QuizSession.objects.filter(user=self.request.user).prefetch_related(
                "questions__choices",
                "questions__recipe",
                "questions__target_ingredient",
                "filter_ingredient_category",
            )
        return QuizSession.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return QuizStartSerializer
        if self.action == "list":
            return QuizSessionListSerializer
        if self.action == "answer":
            return QuizAnswerSerializer
        if self.action == "results":
            return QuizResultsSerializer
        if self.action == "question":
            return QuizQuestionSerializer
        return QuizSessionListSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsAuthenticated()]
        return [AllowAny()]

    # POST  →  Start a new quiz
    def create(self, request, *args, **kwargs):
        serializer = QuizStartSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        session = serializer.save()

        return Response(
            {
                "session_id": str(session.id),
                "total_questions": session.total_questions,
                "message": "Quiz started. Fetch your first question.",
            },
            status=status.HTTP_201_CREATED,
        )

    # GET →  session history (authenticated users only)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = QuizSessionListSerializer(queryset, many=True)
        return Response(serializer.data)

    # GET →  fetch the current question
    @action(detail=True, methods=["get"], url_path="question")
    def question(self, request, pk=None):
        session = self._get_session(pk)
        if session is None:
            return Response(
                {"detail": "Quiz session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.is_complete:
            return Response(
                {"detail": "Quiz is already complete.", "session_id": str(session.id)},
                status=status.HTTP_200_OK,
            )

        # Next unanswered question
        question = (
            session.questions.filter(answered=False)
            .select_related("recipe", "target_ingredient", "session")
            .prefetch_related("choices")
            .order_by("order")
            .first()
        )

        if question is None:
            return Response(
                {"detail": "No unanswered questions remaining."},
                status=status.HTTP_200_OK,
            )

        serializer = QuizQuestionSerializer(question)
        return Response(serializer.data)

    # POST /quizzes/{id}/answer/  →  submit an answer
    @action(detail=True, methods=["post"], url_path="answer")
    def answer(self, request, pk=None):
        session = self._get_session(pk)
        if session is None:
            return Response(
                {"detail": "Quiz session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Inject question_id constraint — must belong to this session
        data = {**request.data, "session_id": str(session.id)}

        serializer = QuizAnswerSerializer(
            data=request.data, context={"session": session}
        )
        serializer.is_valid(raise_exception=True)
        result = serializer.save()

        return Response(result, status=status.HTTP_200_OK)

    # GET /quizzes/{id}/results/  →  full results breakdown
    @action(detail=True, methods=["get"], url_path="results")
    def results(self, request, pk=None):
        session = self._get_session(pk)
        if session is None:
            return Response(
                {"detail": "Quiz session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if not session.is_complete:
            return Response(
                {
                    "detail": "Quiz is not yet complete.",
                    "questions_remaining": session.total_questions
                    - session.current_question_index,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_with_data = QuizSession.objects.prefetch_related(
            "questions__choices",
            "questions__recipe",
            "questions__target_ingredient",
            "filter_ingredient_category",
        ).get(pk=pk)

        serializer = QuizResultsSerializer(session_with_data)
        return Response(serializer.data)

    # Private helpers
    def _get_session(self, pk) -> QuizSession | None:
        """
        Fetch a session by UUID pk.
        Anonymous users can access any session by UUID (no guessing risk).
        Authenticated users can only access their own or anonymous sessions.
        """
        try:
            session = QuizSession.objects.get(pk=pk)
        except (QuizSession.DoesNotExist, ValueError):
            return None

        # If the session belongs to another user, deny it
        if session.user and session.user != self.request.user:
            return None

        return session
