from dataclasses import replace

from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.validate import Verdict, adjust, check


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


def test_sets_carbs_just_below_zero_to_zero():
    chicken = Nutrients(kcal=132.8, protein_g=21.4, carbs_g=-0.43, fat_g=4.78)
    assert adjust(chicken) == (replace(chicken, carbs_g=0.0), "carbs -0.43 g set to 0 g")


def test_leaves_other_values_alone():
    assert adjust(Nutrients(kcal=100, carbs_g=-1.5)) == (Nutrients(kcal=100, carbs_g=-1.5), None)
    assert adjust(Nutrients(kcal=100, fat_g=-0.2)) == (Nutrients(kcal=100, fat_g=-0.2), None)
    butter = Nutrients(kcal=717, carbs_g=0.06)
    assert adjust(butter) == (butter, None)


def test_label_values_allow_rounded_fats_up_to_935_kcal():
    oil = Nutrients(kcal=929, protein_g=0, carbs_g=0, fat_g=100)
    assert check(oil, label_values=True) == Verdict()
    assert check(oil).rejected == "energy 929 kcal over 905 kcal"


def test_label_values_still_reject_energy_that_does_not_match_the_macros():
    sauce = Nutrients(kcal=933, protein_g=1, carbs_g=5, fat_g=20)
    assert check(sauce, label_values=True).rejected == "energy 933 kcal over 905 kcal"
    too_much = Nutrients(kcal=940, protein_g=0, carbs_g=0, fat_g=100)
    assert check(too_much, label_values=True).rejected == "energy 940 kcal over 935 kcal"
