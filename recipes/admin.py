from django.contrib import admin

from recipes.models import (
    GarnishType,
    Ingredient,
    IngredientCategory,
    Recipe,
    RecipeGarnish,
    RecipeIngredient,
    Tag,
    Vessel,
)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1  # Number of empty rows to show by default
    fields = ("ingredient", "amount", "measurement_unit", "note")


class RecipeGarnishInline(admin.TabularInline):
    model = RecipeGarnish
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "method", "primary_vessel", "created_on")
    search_fields = ("title",)
    list_filter = ("method", "tags")
    exclude = (
        "ingredients",
    )  # Exclude 'ingredients' because the Inline handles the through-relationship
    inlines = [RecipeIngredientInline, RecipeGarnishInline]
    filter_horizontal = (
        "alt_vessels",
        "tags",
    )  # This helps with UI if we have many Tags/Vessels


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("title",)
    list_filter = ("category",)
    search_fields = ("title",)


admin.site.register(Vessel)
admin.site.register(IngredientCategory)
admin.site.register(GarnishType)
admin.site.register(Tag)
