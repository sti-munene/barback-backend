from django.core.management.base import BaseCommand

from recipes.enums import (
    DrinkCategory,
    MeasurementUnit,
    PreparationMethod,
    ServingTemperature,
)
from recipes.models import (
    GarnishType,
    Ingredient,
    IngredientCategory,
    Recipe,
    RecipeGarnish,
    RecipeIngredient,
    Vessel,
)


class Command(BaseCommand):
    help = "Seeds the database with 30 official IBA cocktail recipes."

    def handle(self, *args, **kwargs):
        if not IngredientCategory.objects.exists():
            self.stdout.write(self.style.ERROR("Run 'seed_categories' first!"))
            return

        # Map categories to local variables for speed
        c = {cat.title: cat for cat in IngredientCategory.objects.all()}

        # Setup Vessels
        v = {
            name: Vessel.objects.get_or_create(name=name)[0]
            for name in [
                "Martini Glass",
                "Old Fashioned Glass",
                "Highball Glass",
                "Coupe Glass",
                "Collins Glass",
                "Champagne Flute",
                "Hurricane Glass",
            ]
        }

        iba_data = [
            {
                "title": "Dry Martini",
                "method": PreparationMethod.STIRRED,
                "temp": ServingTemperature.COLD,
                "vessel": v["Martini Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 60, MeasurementUnit.ML),
                    ("Dry Vermouth", c["Fortified Wine"], 10, MeasurementUnit.ML),
                ],
                "garnishes": ["Lemon Zest"],
            },
            {
                "title": "Negroni",
                "method": PreparationMethod.STIRRED,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 30, MeasurementUnit.ML),
                    ("Campari", c["Liqueur"], 30, MeasurementUnit.ML),
                    ("Sweet Red Vermouth", c["Fortified Wine"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Orange slice"],
            },
            {
                "title": "Margarita",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Coupe Glass"],
                "ingredients": [
                    ("Tequila", c["Tequila"], 50, MeasurementUnit.ML),
                    ("Triple Sec", c["Liqueur"], 20, MeasurementUnit.ML),
                    ("Lime Juice", c["Juice"], 15, MeasurementUnit.ML),
                ],
                "garnishes": ["Salt rim"],
            },
            {
                "title": "Old Fashioned",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Bourbon", c["Bourbon"], 45, MeasurementUnit.ML),
                    ("Sugar Cube", c["Sugar Cube"], 1, MeasurementUnit.WHOLE),
                    (
                        "Angostura Bitters",
                        c["Non-Potable Bitter"],
                        2,
                        MeasurementUnit.DASH,
                    ),
                ],
                "garnishes": ["Orange zest"],
            },
            {
                "title": "Daiquiri",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Coupe Glass"],
                "ingredients": [
                    ("Light Rum", c["Light Rum"], 45, MeasurementUnit.ML),
                    ("Lime Juice", c["Juice"], 25, MeasurementUnit.ML),
                    ("Simple Syrup", c["Syrup"], 15, MeasurementUnit.ML),
                ],
                "garnishes": ["Lime wheel"],
            },
            {
                "title": "Manhattan",
                "method": PreparationMethod.STIRRED,
                "temp": ServingTemperature.COLD,
                "vessel": v["Martini Glass"],
                "ingredients": [
                    ("Rye Whiskey", c["Rye Whiskey"], 50, MeasurementUnit.ML),
                    ("Sweet Red Vermouth", c["Fortified Wine"], 20, MeasurementUnit.ML),
                    (
                        "Angostura Bitters",
                        c["Non-Potable Bitter"],
                        2,
                        MeasurementUnit.DASH,
                    ),
                ],
                "garnishes": ["Maraschino cherry"],
            },
            {
                "title": "Whiskey Sour",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Bourbon", c["Bourbon"], 45, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 30, MeasurementUnit.ML),
                    ("Simple Syrup", c["Syrup"], 15, MeasurementUnit.ML),
                    ("Egg White", c["Texturizer"], 10, MeasurementUnit.ML),
                ],
                "garnishes": ["Lemon zest"],
            },
            {
                "title": "Espresso Martini",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Coupe Glass"],
                "ingredients": [
                    ("Vodka", c["Vodka"], 50, MeasurementUnit.ML),
                    ("Kahlua", c["Liqueur"], 30, MeasurementUnit.ML),
                    ("Espresso", c["Mixer"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Coffee beans"],
            },
            {
                "title": "Mai Tai",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Dark Rum", c["Dark Rum"], 30, MeasurementUnit.ML),
                    ("Light Rum", c["Light Rum"], 30, MeasurementUnit.ML),
                    ("Orgeat Syrup", c["Syrup"], 15, MeasurementUnit.ML),
                ],
                "garnishes": ["Mint sprig"],
            },
            {
                "title": "Aperol Spritz",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Prosecco", c["Sparkling Wine"], 90, MeasurementUnit.ML),
                    ("Aperol", c["Liqueur"], 60, MeasurementUnit.ML),
                    ("Soda Water", c["Soda"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Orange slice"],
            },
            {
                "title": "Mojito",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Light Rum", c["Light Rum"], 45, MeasurementUnit.ML),
                    ("Lime Juice", c["Juice"], 20, MeasurementUnit.ML),
                    ("Soda Water", c["Soda"], 40, MeasurementUnit.ML),
                ],
                "garnishes": ["Mint sprig"],
            },
            {
                "title": "Bloody Mary",
                "method": PreparationMethod.STIRRED,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Vodka", c["Vodka"], 45, MeasurementUnit.ML),
                    ("Tomato Juice", c["Juice"], 90, MeasurementUnit.ML),
                ],
                "garnishes": ["Celery stalk"],
            },
            {
                "title": "Gimlet",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Coupe Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 60, MeasurementUnit.ML),
                    ("Simple Syrup", c["Syrup"], 22.5, MeasurementUnit.ML),
                    ("Lime Juice", c["Juice"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Lime slice"],
            },
            {
                "title": "Aviation",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Martini Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 45, MeasurementUnit.ML),
                    ("Maraschino Liqueur", c["Liqueur"], 15, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 15, MeasurementUnit.ML),
                ],
                "garnishes": ["Cherry"],
            },
            {
                "title": "Moscow Mule",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Vodka", c["Vodka"], 45, MeasurementUnit.ML),
                    ("Ginger Beer", c["Soda"], 120, MeasurementUnit.ML),
                ],
                "garnishes": ["Lime wedge"],
            },
            {
                "title": "Tom Collins",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Collins Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 45, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 30, MeasurementUnit.ML),
                    ("Soda Water", c["Soda"], 60, MeasurementUnit.ML),
                ],
                "garnishes": ["Lemon slice"],
            },
            {
                "title": "Cosmopolitan",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Martini Glass"],
                "ingredients": [
                    ("Vodka", c["Vodka"], 40, MeasurementUnit.ML),
                    ("Cointreau", c["Liqueur"], 15, MeasurementUnit.ML),
                    ("Cranberry Juice", c["Juice"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Lime peel"],
            },
            {
                "title": "Boulevardier",
                "method": PreparationMethod.STIRRED,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Bourbon", c["Bourbon"], 45, MeasurementUnit.ML),
                    ("Campari", c["Liqueur"], 30, MeasurementUnit.ML),
                    ("Sweet Red Vermouth", c["Fortified Wine"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Orange zest"],
            },
            {
                "title": "Gin Fizz",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 45, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 30, MeasurementUnit.ML),
                    ("Soda Water", c["Soda"], 80, MeasurementUnit.ML),
                ],
                "garnishes": ["Lemon slice"],
            },
            {
                "title": "French 75",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Champagne Flute"],
                "ingredients": [
                    ("Gin", c["Gin"], 30, MeasurementUnit.ML),
                    ("Champagne", c["Sparkling Wine"], 60, MeasurementUnit.ML),
                ],
                "garnishes": ["Lemon zest"],
            },
            {
                "title": "Pina Colada",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Hurricane Glass"],
                "ingredients": [
                    ("Light Rum", c["Light Rum"], 50, MeasurementUnit.ML),
                    ("Coconut Cream", c["Mixer"], 30, MeasurementUnit.ML),
                    ("Pineapple Juice", c["Juice"], 50, MeasurementUnit.ML),
                ],
                "garnishes": ["Pineapple wedge"],
            },
            {
                "title": "Dark 'n Stormy",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Dark Rum", c["Dark Rum"], 60, MeasurementUnit.ML),
                    ("Ginger Beer", c["Soda"], 100, MeasurementUnit.ML),
                ],
                "garnishes": ["Lime wedge"],
            },
            {
                "title": "White Lady",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Martini Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 40, MeasurementUnit.ML),
                    ("Triple Sec", c["Liqueur"], 30, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 20, MeasurementUnit.ML),
                ],
                "garnishes": ["Lemon zest"],
            },
            {
                "title": "Sidecar",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Coupe Glass"],
                "ingredients": [
                    ("Cognac", c["Cognac"], 50, MeasurementUnit.ML),
                    ("Triple Sec", c["Liqueur"], 20, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 20, MeasurementUnit.ML),
                ],
                "garnishes": ["Sugar rim"],
            },
            {
                "title": "Caipirinha",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Cachaca", c["Rum"], 60, MeasurementUnit.ML),
                    ("Sugar", c["Sugar"], 2, MeasurementUnit.BARSPOON),
                    ("Lime Wedges", c["Fruit"], 2, MeasurementUnit.WHOLE),
                ],
                "garnishes": ["Lime wedge"],
            },
            {
                "title": "Paloma",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Highball Glass"],
                "ingredients": [
                    ("Tequila", c["Tequila"], 50, MeasurementUnit.ML),
                    ("Grapefruit Soda", c["Soda"], 100, MeasurementUnit.ML),
                ],
                "garnishes": ["Salt rim"],
            },
            {
                "title": "Americano",
                "method": PreparationMethod.BUILT,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Campari", c["Liqueur"], 30, MeasurementUnit.ML),
                    ("Sweet Red Vermouth", c["Fortified Wine"], 30, MeasurementUnit.ML),
                ],
                "garnishes": ["Orange slice"],
            },
            {
                "title": "Pisco Sour",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Coupe Glass"],
                "ingredients": [
                    ("Pisco", c["Pisco"], 60, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 30, MeasurementUnit.ML),
                    ("Egg White", c["Texturizer"], 10, MeasurementUnit.ML),
                ],
                "garnishes": ["Bitters drop"],
            },
            {
                "title": "Clover Club",
                "method": PreparationMethod.SHAKEN,
                "temp": ServingTemperature.COLD,
                "vessel": v["Martini Glass"],
                "ingredients": [
                    ("Gin", c["Gin"], 45, MeasurementUnit.ML),
                    ("Raspberry Syrup", c["Syrup"], 15, MeasurementUnit.ML),
                    ("Lemon Juice", c["Juice"], 15, MeasurementUnit.ML),
                    ("Egg White", c["Texturizer"], 10, MeasurementUnit.ML),
                ],
                "garnishes": ["Raspberry"],
            },
            {
                "title": "Sazerac",
                "method": PreparationMethod.STIRRED,
                "temp": ServingTemperature.COLD,
                "vessel": v["Old Fashioned Glass"],
                "ingredients": [
                    ("Cognac", c["Cognac"], 50, MeasurementUnit.ML),
                    (
                        "Peychaud Bitters",
                        c["Non-Potable Bitter"],
                        2,
                        MeasurementUnit.DASH,
                    ),
                ],
                "garnishes": ["Lemon zest"],
            },
        ]

        for data in iba_data:
            recipe, created = Recipe.objects.get_or_create(
                title=data["title"],
                defaults={
                    "method": data["method"],
                    "serving_temperature": data["temp"],
                    "primary_vessel": data["vessel"],
                    "category": DrinkCategory.COCKTAIL,
                },
            )

            if created:
                for name, cat_obj, amt, unit in data["ingredients"]:
                    ing, _ = Ingredient.objects.get_or_create(
                        title=name, category=cat_obj
                    )
                    RecipeIngredient.objects.create(
                        recipe=recipe, ingredient=ing, amount=amt, measurement_unit=unit
                    )
                for g_name in data["garnishes"]:
                    g_type, _ = GarnishType.objects.get_or_create(name=g_name)
                    RecipeGarnish.objects.create(recipe=recipe, garnish_type=g_type)
                self.stdout.write(f"Added: {recipe.title}")

        self.stdout.write(self.style.SUCCESS("30 Cocktails seeded!"))
