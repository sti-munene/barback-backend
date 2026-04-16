from django.urls import path

from recipes.views import RecipeViewSet

recipe_list = RecipeViewSet.as_view({"get": "list"})
recipe_detail = RecipeViewSet.as_view({"get": "retrieve"})


urlpatterns = [
    path(
        "",
        recipe_list,
        name="recipe_list",
    ),
    path(
        "<int:pk>/",
        recipe_detail,
        name="recipe_detail",
    ),
]
