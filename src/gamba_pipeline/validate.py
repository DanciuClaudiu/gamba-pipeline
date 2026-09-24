"""Sanity checks on per-100 values (SPEC §10 step 4). Impossible rows are rejected; rows whose
energy doesn't match their macros are kept and flagged for the report (plan P12)."""

from dataclasses import astuple, dataclass

from gamba_pipeline.nutrients import Nutrients

MAX_MACROS_G = 105.0
# Pure fats are 902 kcal per 100 g with USDA's 9.02 kcal/g factor (lard, tallow, fish oils).
MAX_KCAL = 905.0
ENERGY_TOLERANCE_KCAL = 20.0
ENERGY_TOLERANCE_SHARE = 0.20


@dataclass(frozen=True)
class Verdict:
    rejected: str | None = None
    flagged: str | None = None


def check(nutrients: Nutrients) -> Verdict:
    n = nutrients
    if n.kcal is None:
        return Verdict(rejected="no energy value")
    if any(value is not None and value < 0 for value in astuple(n)):
        return Verdict(rejected="a negative value")
    macros = sum(value or 0 for value in (n.protein_g, n.carbs_g, n.fat_g))
    if macros > MAX_MACROS_G:
        return Verdict(rejected=f"protein + carbs + fat {macros:.1f} g over {MAX_MACROS_G:.0f} g")
    if n.kcal > MAX_KCAL:
        return Verdict(rejected=f"energy {n.kcal:.0f} kcal over {MAX_KCAL:.0f} kcal")
    if n.protein_g is None or n.carbs_g is None or n.fat_g is None:
        return Verdict()
    computed = 4 * n.protein_g + 4 * n.carbs_g + 9 * n.fat_g
    if abs(n.kcal - computed) > max(ENERGY_TOLERANCE_KCAL, ENERGY_TOLERANCE_SHARE * n.kcal):
        return Verdict(flagged=f"energy {n.kcal:.0f} kcal, macros give {computed:.0f} kcal")
    return Verdict()
