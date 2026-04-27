from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class MeasurementUnit(TextChoices):
    ML = "ML", "Millilitres"
    DASH = "DASH", "Dash"
    DROP = "DROP", "Drop"
    BARSPOON = "BARSPOON", "Bar Spoon"
    WHOLE = "WHOLE", "Whole"  # e.g. "2 mint sprigs"


class PreparationMethod(TextChoices):
    SHAKEN = "SHAKEN", "Shaken"
    STIRRED = "STIRRED", "Stirred"
    BUILT = "BUILT", "Built"
    BLENDED = (
        "BLENDED",
        "Blended",
    )


class DrinkCategory(TextChoices):
    COCKTAIL = "COCKTAIL", "Cocktail"
    MOCKTAIL = "MOCKTAIL", "Mocktail"
    COFFEE = "COFFEE", "Coffee"
    TEA = "TEA", "Tea"


class ServingTemperature(TextChoices):
    HOT = "HOT", "Hot"
    COLD = "COLD", "Cold"
    ROOM = "ROOM", "Room Temperature"
    FROZEN = "FROZEN", "Frozen/Blended"
