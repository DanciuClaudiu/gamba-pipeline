import sqlite3

import pytest

from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.pack_writer import write
from gamba_pipeline.products import PackProduct
from gamba_pipeline.servings import Serving

BRANZA = PackProduct(
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
COKE = PackProduct(
    gtin14="05449000000996",
    name="Coca-Cola",
    brand="Coca-Cola",
    quantity="330 ml",
    base_unit="ml",
    nutrients=Nutrients(kcal=42.0),
    serving=None,
    source="off",
    source_ref="5449000000996",
    last_modified=None,
)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "food-ro" / "pack.sqlite"
    write(path, [BRANZA, COKE], {"buildDate": "2026-09-24", "country": "ro"})
    connection = sqlite3.connect(path)
    yield connection
    connection.close()


def test_writes_meta(db):
    assert dict(db.execute("SELECT key, value FROM meta")) == {
        "schemaVersion": "1.0",
        "buildDate": "2026-09-24",
        "country": "ro",
    }


def test_numbers_products_in_gtin_order(db):
    assert db.execute("SELECT id, gtin14 FROM product ORDER BY id").fetchall() == [
        (1, "05449000000996"),
        (2, "05940000000011"),
    ]


def test_writes_every_field(db):
    assert db.execute("SELECT * FROM product WHERE id = 2").fetchone() == (
        2, "05940000000011", "Brânză de vaci 5%", "Covalact", "200 g", "g",
        97.992, 12.5, 3.4, None, 5.0, None, None, 100.0,
        "1 porție", 100.0, 1, "off", "5940000000011", "2025-09-01",
    )  # fmt: skip
    assert db.execute("SELECT servingLabel, isComplete FROM product WHERE id = 1").fetchone() == (
        None,
        0,
    )


def test_writes_names_by_language(db):
    assert db.execute("SELECT * FROM productName").fetchall() == [(2, "en", "Cottage cheese 5%")]


def search(db, query):
    return [
        name
        for (name,) in db.execute(
            "SELECT p.name FROM productFts f JOIN product p ON p.id = f.rowid "
            "WHERE productFts MATCH ? ORDER BY rank",
            (query,),
        )
    ]


def test_search_folds_diacritics_and_matches_prefixes_names_and_brands(db):
    assert search(db, '"branza"*') == ["Brânză de vaci 5%"]
    assert search(db, '"br"*') == ["Brânză de vaci 5%"]  # 2-character prefix
    assert search(db, '"cottage"*') == ["Brânză de vaci 5%"]  # the English name
    assert search(db, '"cova"*') == ["Brânză de vaci 5%"]  # the brand
    assert search(db, 'brand : "coca"*') == ["Coca-Cola"]
