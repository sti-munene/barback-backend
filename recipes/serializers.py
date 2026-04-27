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


from rest_framework import serializers

from .models import IngredientCategory


class IngredientCategorySerializer(serializers.ModelSerializer):
    parent = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = IngredientCategory
        fields = ("id", "title", "parent", "subcategories")

    def get_parent(self, obj):
        if obj.parent:
            return {"id": obj.parent.id, "title": obj.parent.title}
        return None

    def get_subcategories(self, obj):
        # Recursively call the same serializer for children
        children = obj.children.all()
        if children.exists():
            return IngredientCategorySerializer(children, many=True).data
        return []


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="ingredient.title")
    category = IngredientCategorySerializer(source="ingredient.category")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "category", "amount", "measurement_unit", "note")


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
