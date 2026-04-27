"""
Resulting endpoints:
  POST   /api/quizzes/               → start quiz
  GET    /api/quizzes/               → list history (auth required)
  GET    /api/quizzes/{id}/question/ → current question
  POST   /api/quizzes/{id}/answer/   → submit answer
  GET    /api/quizzes/{id}/results/  → full results
"""

from rest_framework.routers import DefaultRouter

from quizzes.views import QuizSessionViewSet

router = DefaultRouter()
router.register(r"quizzes", QuizSessionViewSet, basename="quizzes")

urlpatterns = router.urls
