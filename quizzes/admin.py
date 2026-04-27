from django.contrib import admin

from quizzes.models import QuizChoice, QuizQuestion, QuizSession


class QuizChoiceInline(admin.TabularInline):
    model = QuizChoice
    extra = 0
    readonly_fields = ["display_text", "is_correct", "order"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 0
    readonly_fields = [
        "order",
        "recipe",
        "question_type",
        "target_ingredient",
        "answered",
        "answered_correctly",
    ]
    can_delete = False
    show_change_link = True  # lets you click through to the QuizQuestion detail page

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(QuizSession)
class QuizSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "total_questions",
        "score",
        "percentage",
        "is_complete",
        "filter_category",
        "filter_method",
        "filter_ingredient_category",
        "created_on",
    ]
    list_filter = [
        "is_complete",
        "filter_category",
        "filter_method",
        "filter_ingredient_category",
    ]
    search_fields = ["user__username", "id"]
    readonly_fields = [
        "id",
        "user",
        "total_questions",
        "score",
        "is_complete",
        "filter_category",
        "filter_method",
        "filter_ingredient_category",
        "created_on",
        "last_modified",
        "percentage",
        "current_question_index",
    ]
    inlines = [QuizQuestionInline]

    def percentage(self, obj: QuizSession) -> str:
        if obj.total_questions == 0:
            return "—"
        pct = round((obj.score / obj.total_questions) * 100, 1)
        return f"{pct}%"

    percentage.short_description = "Score %"

    def current_question_index(self, obj: QuizSession) -> int:
        return obj.current_question_index

    current_question_index.short_description = "Questions answered"

    def has_add_permission(self, request):
        # Sessions are only created via the API
        return False


@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "session_id",
        "order",
        "recipe",
        "question_type",
        "target_ingredient",
        "answered",
        "answered_correctly",
    ]
    list_filter = ["question_type", "answered", "answered_correctly"]
    search_fields = ["recipe__title", "session__id"]
    readonly_fields = [
        "session",
        "recipe",
        "question_type",
        "target_ingredient",
        "order",
        "answered",
        "answered_correctly",
        "created_on",
    ]
    inlines = [QuizChoiceInline]

    def session_id(self, obj: QuizQuestion) -> str:
        # Show a truncated UUID for readability
        return str(obj.session.id)[:8] + "…"

    session_id.short_description = "Session"

    def has_add_permission(self, request):
        return False


@admin.register(QuizChoice)
class QuizChoiceAdmin(admin.ModelAdmin):
    list_display = ["id", "question", "display_text", "is_correct", "order"]
    list_filter = ["is_correct"]
    search_fields = ["display_text", "question__recipe__title"]
    readonly_fields = ["question", "display_text", "is_correct", "order"]

    def has_add_permission(self, request):
        return False
