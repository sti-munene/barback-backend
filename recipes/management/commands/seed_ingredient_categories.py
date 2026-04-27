from django.core.management.base import BaseCommand

from recipes.models import IngredientCategory


class Command(BaseCommand):
    help = "Seeds the base Ingredient Category tree using singular naming conventions."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding Ingredient Categories...")

        # 1. Root Categories
        spirit, _ = IngredientCategory.objects.get_or_create(
            title="Spirit", parent=None
        )
        wine, _ = IngredientCategory.objects.get_or_create(title="Wine", parent=None)
        liqueur, _ = IngredientCategory.objects.get_or_create(
            title="Liqueur", parent=None
        )
        bitter, _ = IngredientCategory.objects.get_or_create(
            title="Bitter", parent=None
        )
        mixer, _ = IngredientCategory.objects.get_or_create(title="Mixer", parent=None)

        # 2. Spirit Subcategories
        whiskey, _ = IngredientCategory.objects.get_or_create(
            title="Whiskey", parent=spirit
        )
        IngredientCategory.objects.get_or_create(title="Bourbon", parent=whiskey)
        IngredientCategory.objects.get_or_create(title="Rye Whiskey", parent=whiskey)
        IngredientCategory.objects.get_or_create(title="Scotch Whiskey", parent=whiskey)
        IngredientCategory.objects.get_or_create(title="Irish Whiskey", parent=whiskey)
        IngredientCategory.objects.get_or_create(
            title="Japanese Whiskey", parent=whiskey
        )

        IngredientCategory.objects.get_or_create(title="Vodka", parent=spirit)
        IngredientCategory.objects.get_or_create(title="Tequila", parent=spirit)
        IngredientCategory.objects.get_or_create(title="Gin", parent=spirit)

        rum, _ = IngredientCategory.objects.get_or_create(title="Rum", parent=spirit)
        IngredientCategory.objects.get_or_create(title="Dark Rum", parent=rum)
        IngredientCategory.objects.get_or_create(title="Amber Rum", parent=rum)
        IngredientCategory.objects.get_or_create(title="Light Rum", parent=rum)

        brandy, _ = IngredientCategory.objects.get_or_create(
            title="Brandy", parent=spirit
        )
        IngredientCategory.objects.get_or_create(title="Pisco", parent=brandy)
        IngredientCategory.objects.get_or_create(title="Cognac", parent=brandy)
        IngredientCategory.objects.get_or_create(title="Armagnac", parent=brandy)
        IngredientCategory.objects.get_or_create(title="Pomace Brandy", parent=brandy)

        # 3. Wine Subcategories
        IngredientCategory.objects.get_or_create(title="Fortified Wine", parent=wine)
        IngredientCategory.objects.get_or_create(title="Sparkling Wine", parent=wine)

        # 4. Bitter Subcategories
        IngredientCategory.objects.get_or_create(title="Potable Bitter", parent=bitter)
        IngredientCategory.objects.get_or_create(
            title="Non-Potable Bitter", parent=bitter
        )

        # 5. Mixer Subcategories
        IngredientCategory.objects.get_or_create(title="Juice", parent=mixer)
        IngredientCategory.objects.get_or_create(title="Syrup", parent=mixer)

        sugar, _ = IngredientCategory.objects.get_or_create(title="Sugar", parent=mixer)
        IngredientCategory.objects.get_or_create(title="Sugar Cube", parent=sugar)

        IngredientCategory.objects.get_or_create(title="Texturizer", parent=mixer)
        IngredientCategory.objects.get_or_create(title="Soda", parent=mixer)

        IngredientCategory.objects.get_or_create(title="Fruit", parent=None)

        self.stdout.write(self.style.SUCCESS("Category Tree seeded successfully!"))
