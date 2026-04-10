from django.contrib import admin

from .models import (
    GarnishType,
    GlassType,
    Ingredient,
    MeasurementUnit,
    Recipe,
    RecipeGarnish,
)


class RecipeGarnishInline(admin.TabularInline):
    model = RecipeGarnish
    extra = 1  # Number of empty rows to show by default
    fields = ("garnish",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "method", "primary_glass")
    list_filter = ("method", "primary_glass")
    search_fields = ("title",)
    inlines = [RecipeGarnishInline]


@admin.register(GarnishType)
class GarnishTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "created_on")
    search_fields = ("name",)


admin.site.register(GlassType)
admin.site.register(MeasurementUnit)
admin.site.register(Ingredient)
