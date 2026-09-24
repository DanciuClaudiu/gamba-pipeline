from pathlib import Path

import pytest

from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.servings import Serving
from gamba_pipeline.usda import read_foods

USDA = Path(__file__).parent / "fixtures" / "usda"


def by_id(foods):
    return {food.fdc_id: food for food in foods}


def test_reads_only_foundation_foods():
    foods = read_foods(USDA / "foundation", "foundation")
    assert [food.fdc_id for food in foods] == [100, 101, 103, 104]
    assert {food.source for food in foods} == {"foundation"}


def test_maps_names_categories_and_nutrients():
    foods = by_id(read_foods(USDA / "foundation", "foundation"))
    hummus = foods[100]
    assert hummus.name == "Hummus, commercial"
    assert hummus.category == "Legumes and Legume Products"
    assert hummus.nutrients == Nutrients(kcal=229, protein_g=7.35, carbs_g=14.9, fat_g=17.1)
    assert foods[103].nutrients.kcal == 39  # Atwater General only
    assert foods[103].nutrients.sat_fat_g is None  # an empty amount is missing
    assert foods[104].category is None


def test_turns_portions_into_servings():
    foundation = by_id(read_foods(USDA / "foundation", "foundation"))
    assert foundation[100].servings == (Serving("tablespoon", 14.8),)
    assert foundation[103].servings == (Serving("cup, chopped", 91.0),)
    sr_legacy = by_id(read_foods(USDA / "sr_legacy", "sr_legacy"))
    assert sr_legacy[200].servings == (
        Serving("tbsp", 14.2),
        Serving('pat (1" sq, 1/3" high)', 5.0),
    )
    assert sr_legacy[203].servings == (Serving("fl oz", 29.1),)


def test_reads_sr_legacy():
    butter = by_id(read_foods(USDA / "sr_legacy", "sr_legacy"))[200]
    assert butter.nutrients == Nutrients(
        kcal=717,
        protein_g=0.85,
        carbs_g=0.06,
        sugars_g=0.06,
        fat_g=81.11,
        sat_fat_g=51.37,
        fiber_g=0,
        sodium_mg=643,
    )
    assert butter.category == "Dairy and Egg Products"


def test_rejects_an_unknown_source():
    with pytest.raises(KeyError):
        read_foods(USDA / "sr_legacy", "branded")
