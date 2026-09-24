from collections import Counter
from pathlib import Path

from gamba_pipeline.branded import read_products
from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.products import PackProduct
from gamba_pipeline.servings import Serving

BRANDED = Path(__file__).parent / "fixtures" / "usda" / "branded"


def test_reads_the_latest_us_record_for_each_gtin():
    stats = Counter()
    products = read_products(BRANDED, stats)
    assert list(products) == [
        "00036000291452",
        "00041000000010",
        "00041000000034",
        "00041000000041",
    ]
    assert stats == Counter(
        {
            "usda products": 7,
            "usda invalid barcode": 1,
            "usda without energy": 1,
            "usda duplicate barcode": 1,
        }
    )


def test_maps_names_brands_servings_and_nutrients():
    products = read_products(BRANDED, Counter())
    assert products["00036000291452"] == PackProduct(
        gtin14="00036000291452",
        name="CHEDDAR CHEESE",
        brand="TILLAMOOK",
        quantity="8 oz/226 g",
        base_unit="g",
        nutrients=Nutrients(
            kcal=402,
            protein_g=25,
            carbs_g=1.8,
            sugars_g=0.5,
            fat_g=33,
            sat_fat_g=19,
            fiber_g=0,
            sodium_mg=620,
        ),  # fmt: skip
        serving=Serving("serving", 28.0),
        source="usda",
        source_ref="1001",
        last_modified="2024-04-01",
    )
    juice = products["00041000000041"]
    assert (juice.name, juice.brand, juice.base_unit, juice.serving) == (
        "ORANGE JUICE",
        "Tropicana Products, Inc.",
        "ml",
        Serving("serving", 240.0),
    )
    assert products["00041000000034"].serving == Serving("1 CONTAINER", 170.0)
