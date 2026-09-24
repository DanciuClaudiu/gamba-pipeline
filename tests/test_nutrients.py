import pytest

from gamba_pipeline.nutrients import Nutrients, from_usda


def test_reads_all_eight_nutrients():
    butter = from_usda(
        {
            1008: 717,
            1003: 0.85,
            1005: 0.06,
            2000: 0.06,
            1004: 81.11,
            1258: 51.37,
            1079: 0,
            1093: 643,
        }
    )
    assert butter == Nutrients(
        kcal=717,
        protein_g=0.85,
        carbs_g=0.06,
        sugars_g=0.06,
        fat_g=81.11,
        sat_fat_g=51.37,
        fiber_g=0,
        sodium_mg=643,
    )


@pytest.mark.parametrize(
    ("amounts", "kcal"),
    [
        ({1008: 393, 2048: 380, 2047: 390}, 393),  # Energy
        ({2048: 229, 2047: 240}, 229),  # Atwater Specific Factors
        ({2047: 39}, 39),  # Atwater General Factors
    ],
)
def test_energy_falls_back_to_the_atwater_variants(amounts, kcal):
    assert from_usda(amounts).kcal == kcal


def test_energy_falls_back_to_kilojoules():
    assert from_usda({1062: 418.4}).kcal == pytest.approx(100)


def test_fat_carbs_and_sugars_have_fallbacks():
    food = from_usda({1085: 12.0, 1050: 30.0, 1063: 4.0})
    assert (food.fat_g, food.carbs_g, food.sugars_g) == (12.0, 30.0, 4.0)


def test_missing_stays_missing():
    assert from_usda({1003: 10.0}) == Nutrients(protein_g=10.0)
