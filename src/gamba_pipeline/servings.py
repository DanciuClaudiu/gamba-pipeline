"""Named servings (SPEC §3.7): a label and the grams in one of it."""

from dataclasses import dataclass

# Weight units the app converts itself, so a serving named after one adds nothing.
WEIGHT_UNITS = frozenset({"g", "gram", "grams", "kg", "oz", "ounce", "lb", "pound"})
# USDA lab pairings, not portions anyone eats.
LAB_UNITS = frozenset({"paired raw w", "paired cooked w"})


@dataclass(frozen=True)
class Serving:
    label: str
    grams: float


def usda_serving(
    amount: float | None, unit: str | None, modifier: str | None, gram_weight: float | None
) -> Serving | None:
    """One USDA portion as a serving of one unit. Foundation Foods name the unit ("tablespoon") and
    sometimes a modifier ("chopped"); SR Legacy uses the unit "undetermined" and describes the
    portion in the modifier ("can (12 fl oz)")."""
    if not amount or amount <= 0 or not gram_weight or gram_weight <= 0:
        return None
    unit = (unit or "").strip()
    modifier = (modifier or "").strip()
    if unit.lower() in LAB_UNITS:
        return None
    if unit.lower() in ("", "undetermined"):
        label = modifier
    else:
        label = f"{unit}, {modifier}" if modifier else unit
    if not label or label.lower() in WEIGHT_UNITS:
        return None
    return Serving(label=label, grams=round(gram_weight / amount, 2))


def dedupe(servings: list[Serving]) -> list[Serving]:
    """The first serving for each label, ignoring case, in the source's order."""
    seen: set[str] = set()
    kept = []
    for serving in servings:
        key = serving.label.lower()
        if key not in seen:
            seen.add(key)
            kept.append(serving)
    return kept
