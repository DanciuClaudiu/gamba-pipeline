"""USDA Branded Foods for the US pack (SPEC §10 step 3)."""

from collections import Counter, defaultdict
from pathlib import Path

import duckdb

from gamba_pipeline import barcodes, names
from gamba_pipeline.nutrients import USDA_SOURCES, from_usda
from gamba_pipeline.products import PackProduct
from gamba_pipeline.servings import label_serving

MARKETS = ("United States", "US")
BASE_UNITS = {"g": "g", "GRM": "g", "GM": "g", "ml": "ml", "MLT": "ml"}
NUTRIENT_IDS = sorted({source for sources in USDA_SOURCES.values() for source in sources} | {1062})


def _csv(folder: Path, name: str) -> str:
    path = str(folder / name).replace("'", "''")
    return f"read_csv('{path}', header = true, all_varchar = true)"


def read_products(folder: Path, stats: Counter) -> dict[str, PackProduct]:
    """The latest record for each US GTIN-14, by GTIN. USDA keeps every published version of a
    product; the one with the latest available date wins."""
    with duckdb.connect() as con:
        con.execute("SET enable_progress_bar = false")
        con.execute(
            f"""
            CREATE TEMP TABLE latest AS
            SELECT arg_max(fdc_id, (available_date, CAST(fdc_id AS BIGINT))) AS fdc_id
            FROM {_csv(folder, "branded_food.csv")}
            WHERE market_country IN {MARKETS}
            GROUP BY gtin_upc
            """
        )
        amounts: dict[int, dict[int, float]] = defaultdict(dict)
        cursor = con.execute(
            f"""
            SELECT CAST(n.fdc_id AS INTEGER), CAST(n.nutrient_id AS INTEGER),
                   TRY_CAST(n.amount AS DOUBLE)
            FROM {_csv(folder, "food_nutrient.csv")} n
            SEMI JOIN latest USING (fdc_id)
            WHERE n.nutrient_id IN ({", ".join(f"'{i}'" for i in NUTRIENT_IDS)})
            """
        )
        while rows := cursor.fetchmany(100_000):
            for fdc_id, nutrient_id, amount in rows:
                if amount is not None:
                    amounts[fdc_id][nutrient_id] = amount
        records = con.execute(
            f"""
            SELECT CAST(b.fdc_id AS INTEGER), b.gtin_upc, f.description, b.brand_name,
                   b.brand_owner, b.package_weight, b.serving_size_unit,
                   TRY_CAST(b.serving_size AS DOUBLE), b.household_serving_fulltext,
                   coalesce(nullif(b.modified_date, ''), b.available_date), b.available_date
            FROM latest
            JOIN {_csv(folder, "branded_food.csv")} b USING (fdc_id)
            JOIN {_csv(folder, "food.csv")} f USING (fdc_id)
            ORDER BY 1
            """
        ).fetchall()

    products: dict[str, tuple[str, PackProduct]] = {}
    for (
        fdc_id,
        gtin_upc,
        description,
        brand_name,
        brand_owner,
        package_weight,
        unit,
        size,
        household,
        modified,
        available,
    ) in records:
        stats["usda products"] += 1
        gtin14 = barcodes.normalize(gtin_upc or "")
        if gtin14 is None:
            stats["usda invalid barcode"] += 1
            continue
        nutrients = from_usda(amounts.get(fdc_id, {}))
        if nutrients.kcal is None:
            stats["usda without energy"] += 1
            continue
        base = BASE_UNITS.get(unit or "")
        product = PackProduct(
            gtin14=gtin14,
            name=names.clean(description),
            brand=names.clean(brand_name) or names.clean(brand_owner),
            quantity=names.clean(package_weight),
            base_unit=base or "g",
            nutrients=nutrients,
            serving=label_serving(household, size) if base else None,
            source="usda",
            source_ref=str(fdc_id),
            last_modified=modified or None,
        )
        current = products.get(gtin14)
        if current is not None:
            stats["usda duplicate barcode"] += 1
            if current[0] >= (available or ""):
                continue
        products[gtin14] = (available or "", product)
    return {gtin14: product for gtin14, (_, product) in sorted(products.items())}
