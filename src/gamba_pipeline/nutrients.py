"""The eight tracked nutrients (SPEC §3.7), per 100 g. A missing value stays None, never 0."""

from dataclasses import astuple, dataclass

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


# Open Food Facts nutriment names. Their per-100 values are in grams, except energy-kcal (kcal) and
# energy-kj and energy (kJ).
OFF_NAMES = (
    "energy-kcal", "energy-kj", "energy", "proteins", "carbohydrates", "sugars", "fat",
    "saturated-fat", "fiber", "sodium", "salt",
)  # fmt: skip
SALT_PER_SODIUM = 2.5


def from_off(per_100: dict[str, float | None]) -> Nutrients:
    """Nutrients from Open Food Facts per-100 values. Energy prefers kcal, then kJ ÷ 4.184; sodium
    comes from salt ÷ 2.5 when missing. Values are rounded to 3 decimals, which removes the float32
    noise in the Parquet export (10.600000381 → 10.6)."""

    def value(name: str) -> float | None:
        return per_100.get(name)

    kcal = value("energy-kcal")
    if kcal is None:
        kj = value("energy-kj") if value("energy-kj") is not None else value("energy")
        kcal = kj / KJ_PER_KCAL if kj is not None else None
    sodium_g = value("sodium")
    if sodium_g is None and value("salt") is not None:
        sodium_g = value("salt") / SALT_PER_SODIUM
    return Nutrients(
        kcal=_rounded(kcal),
        protein_g=_rounded(value("proteins")),
        carbs_g=_rounded(value("carbohydrates")),
        sugars_g=_rounded(value("sugars")),
        fat_g=_rounded(value("fat")),
        sat_fat_g=_rounded(value("saturated-fat")),
        fiber_g=_rounded(value("fiber")),
        sodium_mg=_rounded(sodium_g * 1000 if sodium_g is not None else None),
    )


def _rounded(value: float | None) -> float | None:
    return round(value, 3) if value is not None else None


def count(nutrients: Nutrients) -> int:
    """How many of the eight nutrients are present; the US merge keeps the higher count."""
    return sum(value is not None for value in astuple(nutrients))
