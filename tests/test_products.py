import pytest

from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.products import PackProduct, base_unit, finalize, merge
from gamba_pipeline.servings import Serving

CHEDDAR_OFF = Nutrients(kcal=400, protein_g=25, carbs_g=1.8, fat_g=33, sodium_mg=600)
CHEDDAR_USDA = Nutrients(
    kcal=402, protein_g=25, carbs_g=1.8, sugars_g=0.5, fat_g=33, sat_fat_g=19, fiber_g=0,
    sodium_mg=620,
)  # fmt: skip


def product(**changes) -> PackProduct:
    fields = {
        "gtin14": "00036000291452",
        "name": "Medium Cheddar Cheese",
        "brand": "Tillamook",
        "quantity": "8 oz",
        "base_unit": "g",
        "nutrients": CHEDDAR_OFF,
        "serving": Serving("1 oz", 28.0),
        "source": "off",
        "source_ref": "036000291452",
        "last_modified": "2025-06-01",
    }
    return PackProduct(**{**fields, **changes})


def usda_product(**changes) -> PackProduct:
    fields = {
        "name": "CHEDDAR CHEESE",
        "brand": "TILLAMOOK",
        "quantity": "8 oz/226 g",
        "nutrients": CHEDDAR_USDA,
        "serving": Serving("serving", 28.0),
        "source": "usda",
        "source_ref": "1001",
        "last_modified": "2024-04-01",
    }
    return product(**{**fields, **changes})


@pytest.mark.parametrize(
    ("unit", "quantity", "base"),
    [
        ("ml", None, "ml"),
        ("g", "330 ml", "g"),
        (None, "330 ml", "ml"),
        (None, "2 L", "ml"),
        (None, "6 x 1.5l", "ml"),
        (None, "12 FL OZ", "ml"),
        (None, "1 lb", "g"),
        (None, "500g", "g"),
        (None, None, "g"),
    ],
)
def test_base_unit(unit, quantity, base):
    assert base_unit(unit, quantity) == base


def test_complete_means_energy_and_the_three_macros():
    assert product().is_complete
    assert not product(nutrients=Nutrients(kcal=400, protein_g=25, fat_g=33)).is_complete


def test_merge_takes_nutrients_from_the_more_complete_record_and_names_from_open_food_facts():
    assert merge(product(), usda_product()) == product(
        nutrients=CHEDDAR_USDA,
        serving=Serving("serving", 28.0),
        source="usda",
        source_ref="1001",
        last_modified="2024-04-01",
    )


def test_merge_keeps_open_food_facts_on_a_tie():
    assert merge(product(), usda_product(nutrients=CHEDDAR_OFF)) == product()


def test_merge_uses_usda_names_only_when_open_food_facts_has_none():
    merged = merge(product(name=None, quantity=None), usda_product())
    assert (merged.name, merged.brand, merged.quantity) == (
        "CHEDDAR CHEESE",
        "Tillamook",
        "8 oz/226 g",
    )


def test_merge_with_one_side_missing():
    assert merge(product(), None) == product()
    assert merge(None, usda_product()) == usda_product()


def test_finalize_names_a_product_by_its_brand():
    assert finalize(product()) == product()
    assert finalize(product(name=None, brand="Napolact")) == product(
        name="Napolact", brand="Napolact"
    )
    assert finalize(product(name=None, brand=None)) is None
