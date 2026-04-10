from django.db import models


class GlassType(models.Model):
    name = models.CharField(max_length=128)
    image = models.ImageField(upload_to="glasses/", null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MeasurementUnit(models.Model):
    title = models.CharField(max_length=128)
    symbol = models.CharField(max_length=28)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-id"]
        verbose_name = "Measurement Unit"
        verbose_name_plural = "Measurement Units"


class Ingredient(models.Model):
    title = models.CharField(max_length=128)
    amount = models.IntegerField()
    unit = models.ForeignKey(
        "recipes.MeasurementUnit",
        on_delete=models.CASCADE,
        related_name="ingredient",
    )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["-id"]
        verbose_name = "Ingredient"
        verbose_name_plural = "Ingredients"


# General GarnishType (eg Lime Wheel, Lime Wedge etc)
class GarnishType(models.Model):
    name = models.CharField(max_length=128)
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


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
        return f"{self.garnish.name}"


class PreparationMethod(models.TextChoices):
    SHAKEN = "SHAKEN", "Shaken"
    STIRRED = "STIRRED", "Stirred"
    BUILT = "BUILT", "Built"
    MUDDLED = "MUDDLED", "Muddled"
    BLENDED = "BLENDED", "Blended"


class Recipe(models.Model):
    title = models.CharField(max_length=128)
    ingredients = models.ManyToManyField(Ingredient)
    method = models.CharField(
        max_length=128,
        choices=PreparationMethod.choices,
        default=PreparationMethod.BUILT,
    )
    primary_glass = models.ForeignKey(
        GlassType, on_delete=models.SET_NULL, null=True, related_name="primary_recipes"
    )
    alt_glasses = models.ManyToManyField(
        GlassType, blank=True, related_name="alt_recipes"
    )
    garnishes = models.ManyToManyField(
        "recipes.GarnishType", through="recipes.RecipeGarnish", related_name="recipes"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ("created_on",)
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
