from django.db import models


class QuestionType(models.TextChoices):
    """
    INGREDIENTS  — "Which of these are in a Negroni?" (multi-select ingredient list)
    AMOUNT       — "How much Campari goes in a Negroni?" (pick the correct ml/oz)
    NEGATIVE     — "Which of these is NOT in a Mojito?" (one distractor is correct)
    """

    # "Which of these is an ingredient in a Negroni?"
    INGREDIENTS = "ingredients", "What's in this cocktail?"

    # "How much Campari goes in a Negroni?"
    AMOUNT = "amount", "How much of this ingredient?"

    # "Which of these is NOT an ingredient in a Mojito?"
    NEGATIVE = "negative", "Which is NOT an ingredient?"

    # "Which of these ingredient lists makes a Margarita?"
    # Choices are full formatted recipe specs — hardest type
    IDENTIFY_RECIPE = "identify_recipe", "Which list matches this cocktail?"

    # "What glass is a Negroni served in?"
    # Choices are vessel names
    IDENTIFY_VESSEL = "identify_vessel", "What glass is this served in?"

    # "How is a Daiquiri prepared?"
    # Choices are preparation methods (Shaken / Stirred / Built / Blended)
    IDENTIFY_METHOD = "identify_method", "How is this cocktail prepared?"
