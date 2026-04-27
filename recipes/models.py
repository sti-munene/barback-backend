from django.db import models
from tree_queries.models import TreeNode

from recipes.enums import (
    DrinkCategory,
    MeasurementUnit,
    PreparationMethod,
    ServingTemperature,
)


class Vessel(models.Model):
    name = models.CharField(max_length=128)
    image = models.ImageField(upload_to="glasses/", null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("created_on",)
        verbose_name = "Vessel (Glass/Cup)"
        verbose_name_plural = "Vessels (Glasses/Cups)"


class IngredientCategory(TreeNode):
    """
    Self-referential category tree.

    Examples:
        Spirit  (parent=None)
        └── Rum  (parent=Spirit)
            ├── White Rum  (parent=Rum)
            ├── Dark Rum   (parent=Rum)
            └── Aged Rum   (parent=Rum)

    Use `parent=None` for top-level categories.
    """

    title = models.CharField(max_length=128)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.parent:
            return f"{self.parent.title} > {self.title}"

        return self.title

    class Meta:
        ordering = ["-id"]
        verbose_name = "Ingredient Category"
        verbose_name_plural = "Ingredient Categories"


class Ingredient(models.Model):
    title = models.CharField(max_length=128)
    category = models.ForeignKey(
        "recipes.IngredientCategory",
        on_delete=models.CASCADE,
        related_name="ingredient",
        null=True,
        blank=True,
    )

    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-id"]
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        "recipes.Recipe", on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        "recipes.Ingredient",
        on_delete=models.CASCADE,
    )

    # Specific to EACH recipe
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    measurement_unit = models.CharField(max_length=20, choices=MeasurementUnit.choices)

    note = models.CharField(max_length=100, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    @property
    def oz_amount(self):
        """
        Bartender Math: 30ml = 1oz.
        Only meaningful when unit is ml — returns None otherwise.
        """
        if self.measurement_unit == MeasurementUnit.ML and self.amount:
            val = float(self.amount) / 30

            # If it's a clean number like 0.75, keep it.
            #  If it's 0.3333, round it to 2 decimal places.

            return round(val, 2)
        return None

    @property
    def display(self):
        """
        Human-readable amount string for UI display.

        Examples:
            "45ml (1.5oz)"
            "2 dash"
            "3 whole"
            "1 barspoon"
        """
        amount = self.amount.normalize()
        if self.measurement_unit == MeasurementUnit.ML and self.oz_amount:
            return f"{amount}ml ({self.oz_amount}oz)"

        # Pluralise whole units naturally
        if self.measurement_unit == MeasurementUnit.WHOLE:
            label = "WHOLE" if amount == 1 else "WHOLE"
            return f"{amount} {label}"
        return f"{amount} {self.get_measurement_unit_display()}"

    def __str__(self):
        return f"{self.display} of {self.ingredient.title}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Recipe Ingredient"
        verbose_name_plural = "Recipe Ingredients"


# General GarnishType (eg Lime Wheel, Lime Wedge etc)
class GarnishType(models.Model):
    name = models.CharField(max_length=128)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Garnish Type"
        verbose_name_plural = "Garnish Types"


# Specific Recipe Garnish
class RecipeGarnish(models.Model):
    garnish_type = models.ForeignKey("recipes.GarnishType", on_delete=models.CASCADE)
    recipe = models.ForeignKey(
        "recipes.Recipe",
        on_delete=models.CASCADE,
        related_name="recipe_garnishes",  # Friendly name
    )
    is_primary = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.garnish_type.name}"

    class Meta:
        ordering = ["-id"]
        verbose_name = "Recipe Garnish"
        verbose_name_plural = "Recipe Garnishes"


class Tag(models.Model):
    name = models.CharField(max_length=128)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("created_on",)
        verbose_name = "Recipe Tag"
        verbose_name_plural = "Recipe Tags"


class Recipe(models.Model):
    title = models.CharField(max_length=128)
    ingredients = models.ManyToManyField(
        "recipes.Ingredient",
        through="RecipeIngredient",  # This is the magic link
        related_name="recipes",
    )
    category = models.CharField(
        max_length=20, choices=DrinkCategory.choices, default=DrinkCategory.COCKTAIL
    )
    serving_temperature = models.CharField(
        max_length=20,
        choices=ServingTemperature.choices,
    )
    method = models.CharField(
        max_length=128,
        choices=PreparationMethod.choices,
        default=PreparationMethod.BUILT,
    )
    primary_vessel = models.ForeignKey(
        "recipes.Vessel",
        on_delete=models.SET_NULL,
        null=True,
        related_name="primary_recipes",
    )
    alt_vessels = models.ManyToManyField(
        "recipes.Vessel",
        related_name="alt_recipes",
        blank=True,
        verbose_name="Alternative Vessels",  # Make the Label prettier
    )
    garnishes = models.ManyToManyField(
        "recipes.GarnishType",
        through="recipes.RecipeGarnish",
        related_name="recipes",
        blank=True,
    )
    tags = models.ManyToManyField(
        "recipes.Tag", related_name="tags", blank=True, verbose_name="Recipe Tags"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("created_on",)
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
