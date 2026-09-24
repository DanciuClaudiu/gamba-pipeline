"""Sanity checks on per-100 values (SPEC §10 step 4). Impossible rows are rejected; rows whose
energy doesn't match their macros are kept and flagged for the report (plan P12). Carbs just below
zero are set to 0 g and listed in the report."""

from dataclasses import astuple, dataclass, replace

from gamba_pipeline.nutrients import Nutrients

MAX_MACROS_G = 105.0
# Pure fats are 902 kcal per 100 g with USDA's 9.02 kcal/g factor (lard, tallow, fish oils).
MAX_KCAL = 905.0
# Package labels round per serving, so pure fats come out above 905: 130 kcal per 14 g tablespoon
# of oil is 929 kcal per 100 g. Packs allow up to this when the energy matches the macros.
MAX_LABEL_KCAL = 935.0
ENERGY_TOLERANCE_KCAL = 20.0
ENERGY_TOLERANCE_SHARE = 0.20
# USDA computes carbohydrate by difference (100 g minus water, protein, fat and ash), so a food
# without carbs can come out slightly negative: raw meat and fish at -0.06 to -0.71 g.
MIN_ADJUSTED_CARBS_G = -1.0


@dataclass(frozen=True)
class Verdict:
    rejected: str | None = None
    flagged: str | None = None


def check(nutrients: Nutrients, *, label_values: bool = False) -> Verdict:
    """`label_values` is for products whose values come from package labels (the packs): energy up
    to 935 kcal passes when it matches the macros."""
    n = nutrients
    if n.kcal is None:
        return Verdict(rejected="no energy value")
    if any(value is not None and value < 0 for value in astuple(n)):
        return Verdict(rejected="a negative value")
    macros = sum(value or 0 for value in (n.protein_g, n.carbs_g, n.fat_g))
    if macros > MAX_MACROS_G:
        return Verdict(rejected=f"protein + carbs + fat {macros:.1f} g over {MAX_MACROS_G:.0f} g")
    computed = None
    if n.protein_g is not None and n.carbs_g is not None and n.fat_g is not None:
        computed = 4 * n.protein_g + 4 * n.carbs_g + 9 * n.fat_g
    tolerance = max(ENERGY_TOLERANCE_KCAL, ENERGY_TOLERANCE_SHARE * n.kcal)
    matches = computed is not None and abs(n.kcal - computed) <= tolerance
    limit = MAX_LABEL_KCAL if label_values and matches else MAX_KCAL
    if n.kcal > limit:
        return Verdict(rejected=f"energy {n.kcal:.0f} kcal over {limit:.0f} kcal")
    if computed is not None and not matches:
        return Verdict(flagged=f"energy {n.kcal:.0f} kcal, macros give {computed:.0f} kcal")
    return Verdict()


def adjust(nutrients: Nutrients) -> tuple[Nutrients, str | None]:
    """Carbs from -1 g up to 0 g become 0 g, with a note for the report; anything else is kept."""
    carbs = nutrients.carbs_g
    if carbs is not None and MIN_ADJUSTED_CARBS_G <= carbs < 0:
        return replace(nutrients, carbs_g=0.0), f"carbs {carbs:.2f} g set to 0 g"
    return nutrients, None
