"""Small databases built from tests/fixtures, for the app's FoodDatabase tests: reference.sqlite
and the RO and US packs (`uv run gamba-pipeline fixtures <folder>`)."""

from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from gamba_pipeline import branded, off, packs, reference
from gamba_pipeline.countries import COUNTRIES

FIXTURES = Path(__file__).resolve().parents[2] / "tests" / "fixtures"
# The export's types for the columns the pipeline reads (the real file has 111 columns).
OFF_COLUMNS = {
    "code": "VARCHAR",
    "lang": "VARCHAR",
    "countries_tags": "VARCHAR[]",
    "product_name": 'STRUCT(lang VARCHAR, "text" VARCHAR)[]',
    "brands": "VARCHAR",
    "quantity": "VARCHAR",
    "product_quantity_unit": "VARCHAR",
    "serving_size": "VARCHAR",
    "serving_quantity": "VARCHAR",
    "last_modified_t": "BIGINT",
    "nutriments": 'STRUCT("name" VARCHAR, "100g" FLOAT)[]',
    "unique_scans_n": "INTEGER",
    "popularity_tags": "VARCHAR[]",
}
BUILD_DATE = "2026-09-24"


def off_parquet(source: Path, parquet: Path) -> Path:
    """The JSON fixture as Parquet, typed like the Open Food Facts export."""
    columns = ", ".join(f"'{name}': '{kind}'" for name, kind in OFF_COLUMNS.items())
    with duckdb.connect() as con:
        con.execute(
            f"COPY (SELECT * FROM read_json('{source}', format = 'array', "
            f"columns = {{{columns}}})) TO '{parquet}' (FORMAT parquet)"
        )
    return parquet


def build(output: Path) -> list[Path]:
    """Builds reference.sqlite, food-ro/pack.sqlite and food-us/pack.sqlite in `output`."""
    reference.build(
        foundation_dir=FIXTURES / "usda" / "foundation",
        sr_legacy_dir=FIXTURES / "usda" / "sr_legacy",
        exercises_json=FIXTURES / "exercises.json",
        overrides_json=FIXTURES / "overrides.json",
        output=output / "reference.sqlite",
        meta={"buildDate": BUILD_DATE},
    )
    written = [output / "reference.sqlite"]
    with TemporaryDirectory() as temporary:
        parquet = off_parquet(FIXTURES / "off" / "products.json", Path(temporary) / "food.parquet")
        for code in ("ro", "us"):
            country = COUNTRIES[code]
            usda = None
            if country.usda_branded:
                usda = list(
                    branded.read_products(FIXTURES / "usda" / "branded", Counter()).values()
                )
            pack = output / country.pack_id / "pack.sqlite"
            report = packs.PackReport(code)
            off_products = off.read_products(parquet, country, report.stats)
            packs.build(country, off_products, usda, pack, {"buildDate": BUILD_DATE}, report)
            written.append(pack)
    return written
