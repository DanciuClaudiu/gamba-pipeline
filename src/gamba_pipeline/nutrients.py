"""The eight tracked nutrients (SPEC §3.7), per 100 g. A missing value stays None, never 0."""

from dataclasses import dataclass

KJ_PER_KCAL = 4.184


@dataclass(frozen=True)
class Nutrients:
    kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    sugars_g: float | None = None
    fat_g: float | None = None
    sat_fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None


# USDA FoodData Central nutrient IDs for each nutrient, in order of preference.
USDA_SOURCES: dict[str, tuple[int, ...]] = {
    # Energy; many Foundation Foods report only the Atwater Specific or General variants.
    "kcal": (1008, 2048, 2047),
    "protein_g": (1003,),
    # Carbohydrate by difference, then by summation.
    "carbs_g": (1005, 1050),
    "sugars_g": (2000, 1063),
    # Total lipid, then total fat (NLEA).
    "fat_g": (1004, 1085),
    "sat_fat_g": (1258,),
    "fiber_g": (1079,),
    "sodium_mg": (1093,),
}
USDA_ENERGY_KJ = 1062


def from_usda(amounts: dict[int, float]) -> Nutrients:
    """Each nutrient from the first ID present; energy falls back to kilojoules ÷ 4.184."""
    values = {
        field: next((amounts[source] for source in sources if source in amounts), None)
        for field, sources in USDA_SOURCES.items()
    }
    if values["kcal"] is None and USDA_ENERGY_KJ in amounts:
        values["kcal"] = amounts[USDA_ENERGY_KJ] / KJ_PER_KCAL
    return Nutrients(**values)
