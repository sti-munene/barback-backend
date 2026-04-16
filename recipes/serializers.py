from rest_framework import serializers

from recipes.models import (
    GarnishType,
    IngredientCategory,
    Recipe,
    RecipeGarnish,
    RecipeIngredient,
    Tag,
    Vessel,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
        ]


class VesselSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vessel
        fields = ["id", "name"]


class GarnishTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GarnishType
        fields = [
            "id",
            "name",
        ]


class RecipeGarnishSerializer(serializers.ModelSerializer):
    garnish_type = GarnishTypeSerializer(read_only=True)

    class Meta:
        model = RecipeGarnish
        fields = ["id", "garnish_type", "is_primary"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngredientCategory
        fields = [
            "id",
            "title",
        ]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="ingredient.title")
    category = RecipeIngredientSerializer(source="ingredient.category")
    oz_amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "category", "ml_amount", "oz_amount", "note")


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source="recipe_ingredients", many=True, read_only=True
    )
    primary_vessel = VesselSerializer()
    alt_vessels = VesselSerializer(many=True)
    garnishes = RecipeGarnishSerializer(
        source="recipe_garnishes", many=True, read_only=True
    )
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "category",
            "serving_temperature",
            "method",
            "ingredients",
            "primary_vessel",
            "alt_vessels",
            "garnishes",
            "tags",
        ]
