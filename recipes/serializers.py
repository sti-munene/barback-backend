from rest_framework import serializers

from .models import (
    GarnishType,
    GlassType,
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeGarnish,
)


class MeasurementUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementUnit
        fields = ["id", "title", "symbol"]


class GlassTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GlassType
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


class IngredientSerializer(serializers.ModelSerializer):
    unit = MeasurementUnitSerializer()

    class Meta:
        model = Ingredient
        fields = ["id", "title", "amount", "unit"]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True)
    primary_glass = GlassTypeSerializer()
    alt_glasses = GlassTypeSerializer(many=True)
    garnishes = RecipeGarnishSerializer(
        source="recipe_garnishes", many=True, read_only=True
    )

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "ingredients",
            "primary_glass",
            "alt_glasses",
            "garnishes",
        ]
