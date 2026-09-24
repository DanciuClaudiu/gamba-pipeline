from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.validate import Verdict, check


def test_accepts_a_consistent_food():
    butter = Nutrients(kcal=717, protein_g=0.85, carbs_g=0.06, fat_g=81.11)
    assert check(butter) == Verdict()


def test_accepts_pure_fat_at_902_kcal():
    assert check(Nutrients(kcal=902, protein_g=0, carbs_g=0, fat_g=100)) == Verdict()


def test_rejects_a_food_without_energy():
    assert check(Nutrients(protein_g=10)).rejected == "no energy value"


def test_rejects_negative_values():
    assert check(Nutrients(kcal=100, sodium_mg=-1)).rejected == "a negative value"


def test_rejects_more_than_105_g_of_macros():
    verdict = check(Nutrients(kcal=500, protein_g=60, carbs_g=50, fat_g=10))
    assert verdict.rejected == "protein + carbs + fat 120.0 g over 105 g"


def test_rejects_more_than_905_kcal():
    assert check(Nutrients(kcal=950)).rejected == "energy 950 kcal over 905 kcal"


def test_flags_energy_that_does_not_match_the_macros():
    sake = Nutrients(kcal=134, protein_g=0.5, carbs_g=5, fat_g=0)
    assert check(sake) == Verdict(flagged="energy 134 kcal, macros give 22 kcal")


def test_allows_20_kcal_or_20_percent_of_difference():
    assert check(Nutrients(kcal=60, protein_g=10, carbs_g=0, fat_g=0)) == Verdict()  # 20 kcal off
    assert check(Nutrients(kcal=500, protein_g=0, carbs_g=100, fat_g=0)) == Verdict()  # 20% off


def test_does_not_compare_energy_when_a_macro_is_missing():
    assert check(Nutrients(kcal=300, protein_g=1)) == Verdict()
