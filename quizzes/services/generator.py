import random

from django.db import transaction

from quizzes.enums import QuestionType
from quizzes.models import QuizChoice, QuizQuestion, QuizSession
from recipes.enums import MeasurementUnit
from recipes.models import Recipe, RecipeIngredient

NUM_CHOICES = 4  # 1 correct + 3 distractors


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@transaction.atomic
def generate_quiz_questions(session: QuizSession) -> list[QuizQuestion]:
    """
    Select recipes, create QuizQuestion + QuizChoice rows, return the questions.
    Raises ValueError if there aren't enough recipes to build the quiz.
    """
    pool = _get_recipe_pool(session)

    if len(pool) < session.total_questions:
        raise ValueError(
            f"Not enough recipes for these filters. "
            f"Found {len(pool)}, need {session.total_questions}."
        )

    selected = random.sample(pool, session.total_questions)
    questions = []

    for order, recipe in enumerate(selected):
        q_type = _pick_question_type(recipe)
        question = QuizQuestion.objects.create(
            session=session,
            recipe=recipe,
            question_type=q_type,
            order=order,
        )
        _generate_choices(question, recipe, q_type, pool)
        questions.append(question)

    return questions


# ---------------------------------------------------------------------------
# Recipe pool
# ---------------------------------------------------------------------------


def _get_recipe_pool(session: QuizSession) -> list[Recipe]:
    qs = Recipe.objects.prefetch_related(
        "recipe_ingredients__ingredient__category",
        "primary_vessel",
    )

    if session.filter_category:
        qs = qs.filter(category=session.filter_category)

    if session.filter_method:
        qs = qs.filter(method=session.filter_method)

    if session.filter_ingredient_category:
        # tree_queries: match the category or any of its descendants
        qs = qs.filter(
            ingredients__category__in=session.filter_ingredient_category.descendants(
                include_self=True
            )
        ).distinct()

    return list(qs)


# ---------------------------------------------------------------------------
# Question type selection
# ---------------------------------------------------------------------------


def _pick_question_type(recipe: Recipe) -> str:
    """
    Weighted random selection across all applicable types for this recipe.
    Complex types are weighted lower so the quiz stays varied.
    """
    options = [
        # (type, weight)
        (QuestionType.INGREDIENTS, 2),
        (QuestionType.NEGATIVE, 2),
        (QuestionType.IDENTIFY_RECIPE, 3),  # most instructive — weighted highest
        (QuestionType.IDENTIFY_VESSEL, 1),
        (QuestionType.IDENTIFY_METHOD, 1),
    ]

    # AMOUNT only applies if the recipe has measurable ml ingredients
    has_ml = recipe.recipe_ingredients.filter(
        measurement_unit=MeasurementUnit.ML, amount__gt=0
    ).exists()
    if has_ml:
        options.append((QuestionType.AMOUNT, 1))

    # IDENTIFY_VESSEL only applies if the recipe has a primary vessel
    if not recipe.primary_vessel:
        options = [(t, w) for t, w in options if t != QuestionType.IDENTIFY_VESSEL]

    types, weights = zip(*options)
    return random.choices(types, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Choice generation — dispatcher
# ---------------------------------------------------------------------------


def _generate_choices(
    question: QuizQuestion,
    recipe: Recipe,
    q_type: str,
    pool: list[Recipe],
):
    dispatch = {
        QuestionType.INGREDIENTS: _choices_ingredients,
        QuestionType.AMOUNT: _choices_amount,
        QuestionType.NEGATIVE: _choices_negative,
        QuestionType.IDENTIFY_RECIPE: _choices_identify_recipe,
        QuestionType.IDENTIFY_VESSEL: _choices_identify_vessel,
        QuestionType.IDENTIFY_METHOD: _choices_identify_method,
    }
    dispatch[q_type](question, recipe, pool)


# ---------------------------------------------------------------------------
# Simple question types
# ---------------------------------------------------------------------------


def _choices_ingredients(question: QuizQuestion, recipe: Recipe, pool: list[Recipe]):
    """
    "Which of these is an ingredient in [recipe]?"
    Correct: one real ingredient. Distractors: ingredients from other recipes.
    """
    recipe_ingredient_ids = set(
        recipe.recipe_ingredients.values_list("ingredient_id", flat=True)
    )
    correct_ri = random.choice(list(recipe.recipe_ingredients.all()))
    correct_text = correct_ri.ingredient.title

    distractors = _distractor_ingredient_names(
        exclude_ids=recipe_ingredient_ids,
        pool=pool,
        count=NUM_CHOICES - 1,
    )
    _save_choices(question, [correct_text], distractors)


def _choices_amount(question: QuizQuestion, recipe: Recipe, pool: list[Recipe]):
    """
    "How much [ingredient] goes in [recipe]?"
    Correct: the actual amount. Distractors: other real amounts or bartender measures.
    """
    measurable = list(
        recipe.recipe_ingredients.filter(
            measurement_unit=MeasurementUnit.ML, amount__gt=0
        )
    )
    target_ri: RecipeIngredient = random.choice(measurable)

    question.target_ingredient = target_ri.ingredient
    question.save(update_fields=["target_ingredient"])

    correct_ml = float(target_ri.amount)
    correct_text = _format_ml(correct_ml)

    other_amounts = list(
        RecipeIngredient.objects.filter(
            ingredient=target_ri.ingredient, measurement_unit=MeasurementUnit.ML
        )
        .exclude(recipe=recipe)
        .exclude(amount=target_ri.amount)
        .values_list("amount", flat=True)
        .distinct()
    )
    other_texts = [_format_ml(float(a)) for a in other_amounts]

    if len(other_texts) < NUM_CHOICES - 1:
        for m in _bartender_measures(exclude_ml=correct_ml):
            t = _format_ml(m)
            if t not in other_texts and t != correct_text:
                other_texts.append(t)
            if len(other_texts) >= NUM_CHOICES - 1:
                break

    distractors = random.sample(other_texts, min(NUM_CHOICES - 1, len(other_texts)))
    _save_choices(question, [correct_text], distractors)


def _choices_negative(question: QuizQuestion, recipe: Recipe, pool: list[Recipe]):
    """
    "Which of these is NOT an ingredient in [recipe]?"
    The correct answer is the ingredient that does NOT belong.
    Distractors are real ingredients from this recipe.
    """
    recipe_ingredient_ids = set(
        recipe.recipe_ingredients.values_list("ingredient_id", flat=True)
    )
    not_in_recipe = _distractor_ingredient_names(
        exclude_ids=recipe_ingredient_ids,
        pool=pool,
        count=1,
    )
    if not not_in_recipe:
        _choices_ingredients(question, recipe, pool)
        return

    correct_text = not_in_recipe[0]
    real_ingredients = list(
        recipe.recipe_ingredients.values_list("ingredient__title", flat=True)
    )
    distractors = random.sample(
        real_ingredients, min(NUM_CHOICES - 1, len(real_ingredients))
    )
    _save_choices(question, [correct_text], distractors)


# ---------------------------------------------------------------------------
# Complex question types
# ---------------------------------------------------------------------------


def _choices_identify_recipe(
    question: QuizQuestion, recipe: Recipe, pool: list[Recipe]
):
    """
    "Which of these ingredient lists makes a [recipe]?"

    Correct choice: the full formatted ingredient list for this recipe.
    Distractors: full ingredient lists from the most similar other recipes
    (same method first, then same category, then random from pool).

    This is the hardest type — the player must recognise the complete spec.
    """
    correct_text = _format_ingredient_list(recipe)

    # Prefer similar recipes as distractors — same method makes it harder
    similar = sorted(
        [r for r in pool if r.pk != recipe.pk],
        key=lambda r: (
            r.method != recipe.method,  # same method = more similar = harder
            r.category != recipe.category,
        ),
    )

    distractor_pool = similar[: max(NUM_CHOICES - 1, 6)]  # take up to 6, pick 3
    distractors = []
    seen_texts = {correct_text}

    for r in distractor_pool:
        text = _format_ingredient_list(r)
        if text not in seen_texts:
            distractors.append(text)
            seen_texts.add(text)
        if len(distractors) >= NUM_CHOICES - 1:
            break

    # Fall back to remaining pool if we didn't get enough
    if len(distractors) < NUM_CHOICES - 1:
        for r in pool:
            if r.pk == recipe.pk:
                continue
            text = _format_ingredient_list(r)
            if text not in seen_texts:
                distractors.append(text)
                seen_texts.add(text)
            if len(distractors) >= NUM_CHOICES - 1:
                break

    _save_choices(question, [correct_text], distractors)


def _choices_identify_vessel(
    question: QuizQuestion, recipe: Recipe, pool: list[Recipe]
):
    """
    "What glass is a [recipe] served in?"

    All valid vessels (primary + alt) are marked correct.
    Distractors are vessel names that are genuinely not associated with this recipe.
    """
    # Collect every valid vessel name for this recipe
    valid_vessel_names = set()
    if recipe.primary_vessel:
        valid_vessel_names.add(recipe.primary_vessel.name)
    for vessel in recipe.alt_vessels.all():
        valid_vessel_names.add(vessel.name)

    # Distractors: vessel names from the pool that are NOT valid for this recipe
    other_vessels = list(
        {
            r.primary_vessel.name
            for r in pool
            if r.primary_vessel and r.primary_vessel.name not in valid_vessel_names
        }
    )
    random.shuffle(other_vessels)
    distractors = other_vessels[: NUM_CHOICES - len(valid_vessel_names)]

    # Pad with fallbacks if pool doesn't have enough vessel variety
    fallback_vessels = [
        "Cocktail Glass",
        "Old Fashioned Glass",
        "Highball Glass",
        "Collins Glass",
        "Champagne Flute",
        "Copper Mug",
        "Hurricane Glass",
        "Margarita Glass",
    ]
    for v in fallback_vessels:
        if v not in valid_vessel_names and v not in distractors:
            distractors.append(v)
        if len(distractors) >= NUM_CHOICES - len(valid_vessel_names):
            break

    _save_choices(question, list(valid_vessel_names), distractors)


def _choices_identify_method(
    question: QuizQuestion, recipe: Recipe, pool: list[Recipe]
):
    """
    "How is a [recipe] prepared?"
    Correct: the recipe's preparation method label.
    Distractors: all other preparation method labels.
    """
    from recipes.enums import PreparationMethod

    correct_text = recipe.get_method_display()

    distractors = [
        label for value, label in PreparationMethod.choices if label != correct_text
    ]
    random.shuffle(distractors)

    _save_choices(question, [correct_text], distractors[: NUM_CHOICES - 1])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_amount_unit(amount_decimal, measurement_unit: str) -> str:
    """
    Formats an amount + unit into a clean human-readable string.

    Rules:
      ml        → no space, lowercase       e.g. "30ml", "22.5ml"
      dash      → space + pluralise         e.g. "1 dash", "2 dashes"
      drop      → space + pluralise         e.g. "1 drop", "3 drops"
      barspoon  → space + pluralise         e.g. "1 barspoon", "2 barspoons"
      whole     → space, no unit label      e.g. "3" (label comes from ingredient name)
      splash    → space, always singular    e.g. "1 splash"
      pinch     → space + pluralise         e.g. "1 pinch", "2 pinches"
    """
    amount_str = format(amount_decimal, "f").rstrip("0").rstrip(".")
    amount_val = float(amount_decimal)
    unit = measurement_unit.lower()

    if unit == "ml":
        return f"{amount_str}ml"

    if unit == "whole":
        # The ingredient name already implies what it is e.g. "3 Fresh Strawberries"
        return amount_str

    plurals = {
        "dash": "dashes",
        "drop": "drops",
        "barspoon": "barspoons",
        "pinch": "pinches",
        "splash": "splashes",
    }

    singular = unit
    plural = plurals.get(unit, unit + "s")
    label = singular if amount_val == 1 else plural

    return f"{amount_str} {label}"


def _format_ingredient_list(recipe: Recipe) -> str:
    """
    Formats a recipe's ingredients as a compact, readable list.
    Example: "30ml Campari · 30ml Gin · 30ml Sweet Vermouth"
    Sorted alphabetically so order doesn't give away the answer.
    """
    parts = []
    for ri in recipe.recipe_ingredients.select_related("ingredient").order_by(
        "ingredient__title"
    ):
        formatted = _format_amount_unit(ri.amount, ri.measurement_unit)
        unit = ri.measurement_unit.lower()
        if unit == "ml":
            parts.append(f"{formatted} {ri.ingredient.title}")
        else:
            parts.append(f"{formatted} of {ri.ingredient.title}")
    return " · ".join(parts)


def _format_ml(ml: float) -> str:
    return f"{ml:g}ml ({round(ml / 30, 2):g}oz)"


def _bartender_measures(exclude_ml: float) -> list[float]:
    common = [7.5, 15, 22.5, 30, 37.5, 45, 60, 90, 120]
    return [m for m in common if m != exclude_ml]


def _distractor_ingredient_names(
    exclude_ids: set[int],
    pool: list[Recipe],
    count: int,
) -> list[str]:
    candidates: set[str] = set()
    for recipe in pool:
        for ri in recipe.recipe_ingredients.all():
            if ri.ingredient_id not in exclude_ids:
                candidates.add(ri.ingredient.title)
    candidates = list(candidates)
    random.shuffle(candidates)
    return candidates[:count]


def _save_choices(
    question: QuizQuestion,
    correct_texts: list[str],
    distractor_texts: list[str],
):
    """
    Shuffles and persists all choices for a question.
    Accepts a list of correct texts to support questions with multiple
    valid answers (e.g. IDENTIFY_VESSEL with primary + alt vessels).
    """
    correct_set = set(correct_texts)
    choices = [(t, True) for t in correct_texts] + [
        (t, False) for t in distractor_texts if t not in correct_set
    ]
    random.shuffle(choices)
    QuizChoice.objects.bulk_create(
        [
            QuizChoice(
                question=question,
                display_text=text,
                is_correct=is_correct,
                order=i,
            )
            for i, (text, is_correct) in enumerate(choices)
        ]
    )
