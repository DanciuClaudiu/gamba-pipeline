from collections import Counter

from gamba_pipeline.countries import COUNTRIES
from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.off import read_products
from gamba_pipeline.products import PackProduct
from gamba_pipeline.servings import Serving


def by_gtin(products):
    return {product.gtin14: product for product in products}


def test_reads_a_country_s_products_with_energy_and_a_valid_barcode(off_parquet):
    stats = Counter()
    products = read_products(off_parquet, COUNTRIES["ro"], stats)
    assert [product.gtin14 for product in products] == [
        "05449000000996",
        "05940000000011",
        "05940000000028",
        "05940000000035",
        "05940000000059",
        "05940000000066",
    ]
    assert stats == Counter(
        {
            "off products": 9,
            "off duplicate barcode": 1,
            "off invalid barcode": 1,
            "off without energy": 1,
        }
    )


def test_maps_names_nutrients_servings_and_dates(off_parquet):
    products = by_gtin(read_products(off_parquet, COUNTRIES["ro"], Counter()))
    assert products["05940000000011"] == PackProduct(
        gtin14="05940000000011",
        name="Brânză de vaci 5%",
        names={"en": "Cottage cheese 5%"},
        brand="Covalact",
        quantity="200 g",
        base_unit="g",
        nutrients=Nutrients(kcal=97.992, protein_g=12.5, carbs_g=3.4, fat_g=5.0, sodium_mg=100.0),
        serving=Serving("1 porție", 100.0),
        source="off",
        source_ref="5940000000011",
        last_modified="2025-09-01",
    )
    coke = products["05449000000996"]
    assert (coke.name, coke.names, coke.brand, coke.base_unit, coke.serving) == (
        "Coca-Cola",
        {"ro": "Coca-Cola Original"},
        "Coca-Cola",
        "ml",
        Serving("1 can", 330.0),
    )
    assert coke.nutrients.carbs_g == 10.6
    assert products["05940000000028"].name is None  # named by brand later
    assert products["05940000000028"].base_unit == "ml"  # "1 l"


def test_names_follow_the_country(off_parquet):
    coke = by_gtin(read_products(off_parquet, COUNTRIES["gb"], Counter()))["05449000000996"]
    assert coke.names == {}  # English only, and the English name is the main name
    beanz = by_gtin(read_products(off_parquet, COUNTRIES["gb"], Counter()))["05000000000012"]
    assert beanz.name == "Beanz in a rich tomato sauce"  # no "main" entry: the product's language
    assert beanz.nutrients.sodium_mg == 240.0
