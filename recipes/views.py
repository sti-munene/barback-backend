from rest_framework import filters, viewsets

from recipes.models import Recipe
from recipes.serializers import RecipeSerializer
from utils.pagination import BasePaginationSet


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().order_by("-created_on")
    serializer_class = RecipeSerializer
    pagination_class = BasePaginationSet
    search_fields = ["title"]
    filter_backends = (filters.SearchFilter,)
