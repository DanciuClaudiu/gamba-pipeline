import json
import sqlite3
from collections import Counter
from pathlib import Path

from gamba_pipeline import branded as usda_branded
from gamba_pipeline import off, packs
from gamba_pipeline.countries import COUNTRIES

BRANDED = Path(__file__).parent / "fixtures" / "usda" / "branded"


def build(off_parquet, tmp_path, code):
    country = COUNTRIES[code]
    report = packs.PackReport(code)
    off_products = off.read_products(off_parquet, country, report.stats)
    usda = None
    if country.usda_branded:
        usda = list(usda_branded.read_products(BRANDED, report.stats).values())
    output = tmp_path / country.pack_id / "pack.sqlite"
    packs.build(country, off_products, usda, output, {"buildDate": "2026-09-24"}, report)
    return report, sqlite3.connect(output)


def test_builds_the_romanian_pack(off_parquet, tmp_path):
    report, db = build(off_parquet, tmp_path, "ro")
    assert db.execute("SELECT gtin14, name, brand, kcal FROM product ORDER BY id").fetchall() == [
        ("05449000000996", "Coca-Cola", "Coca-Cola", 42.0),
        ("05940000000011", "Brânză de vaci 5%", "Covalact", 97.992),
        ("05940000000028", "Napolact", "Napolact", 60.0),
        ("05940000000066", "Vin alb demisec", "Jidvei", 80.0),
    ]
    assert dict(db.execute("SELECT key, value FROM meta")) == {
        "schemaVersion": "1.0",
        "buildDate": "2026-09-24",
        "country": "ro",
    }
    assert report.stats == Counter(
        {
            "off products": 9,
            "off duplicate barcode": 1,
            "off invalid barcode": 1,
            "off without energy": 1,
            "off rejected": 1,
            "no name or brand": 1,
            "named by brand": 1,
        }
    )
    assert report.rejected == [
        ("off", "5940000000059", "protein + carbs + fat 120.0 g over 105 g"),
    ]
    assert report.flagged == [
        ("05940000000066", "Vin alb demisec", "energy 80 kcal, macros give 10 kcal"),
    ]
    assert (report.products, report.size_bytes > 0) == (4, True)


def test_builds_the_us_pack_with_usda_branded(off_parquet, tmp_path):
    report, db = build(off_parquet, tmp_path, "us")
    products = "SELECT gtin14, name, brand, kcal, source FROM product ORDER BY id"
    assert db.execute(products).fetchall() == [
        ("00036000291452", "Medium Cheddar Cheese", "Tillamook", 402.0, "usda"),
        ("00041000000010", "Creamy Peanut Butter", "Jif", 594.0, "off"),
        ("00041000000027", "Pure Vegetable Oil", "Crisco", 929.0, "off"),
        ("00041000000034", "GREEK YOGURT, VANILLA", "Kroger", 88.0, "usda"),
        ("00041000000041", "ORANGE JUICE", "Tropicana Products, Inc.", 45.0, "usda"),
        ("05449000000996", "Coca-Cola", "Coca-Cola", 42.0, "off"),
    ]
    servings = "SELECT gtin14, servingLabel, servingAmount, sourceRef FROM product ORDER BY id"
    assert db.execute(servings).fetchall() == [
        ("00036000291452", "serving", 28.0, "1001"),
        ("00041000000010", "2 tbsp", 32.0, "041000000010"),
        ("00041000000027", "1 tbsp", 14.0, "041000000027"),
        ("00041000000034", "1 CONTAINER", 170.0, "1008"),
        ("00041000000041", "serving", 240.0, "1004"),
        ("05449000000996", "1 can", 330.0, "5449000000996"),
    ]
    assert report.stats["in both"] == 3
    assert report.stats["usda nutrients kept"] == 2
    assert report.stats["usda only"] == 1
    assert report.rejected == []


def test_the_same_inputs_give_the_same_file(off_parquet, tmp_path):
    build(off_parquet, tmp_path / "a", "ro")
    build(off_parquet, tmp_path / "b", "ro")
    first = (tmp_path / "a" / "food-ro" / "pack.sqlite").read_bytes()
    assert first == (tmp_path / "b" / "food-ro" / "pack.sqlite").read_bytes()


def test_writes_the_report(off_parquet, tmp_path):
    report, _ = build(off_parquet, tmp_path, "ro")
    packs.write_report(report, tmp_path / "food-ro.report.json")
    data = json.loads((tmp_path / "food-ro.report.json").read_text(encoding="utf-8"))
    assert (data["country"], data["products"], data["stats"]["named by brand"]) == ("ro", 4, 1)
    assert data["rejected"] == [
        {
            "source": "off",
            "ref": "5940000000059",
            "reason": "protein + carbs + fat 120.0 g over 105 g",
        }
    ]
    assert data["flagged"] == [
        {
            "gtin14": "05940000000066",
            "name": "Vin alb demisec",
            "reason": "energy 80 kcal, macros give 10 kcal",
        }
    ]
