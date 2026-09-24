"""How many products each country would get in a pack, for the pack threshold (SPEC §3.10, Q5)."""

from collections import defaultdict
from pathlib import Path

import duckdb

from gamba_pipeline import barcodes, nutrients


def count_products(parquet: Path) -> dict[str, int]:
    """Distinct GTINs with energy, a valid barcode and a name or brand, by Open Food Facts country
    tag, most first. Validation isn't applied, so a pack ends up slightly smaller."""
    energy = ", ".join(f"'{name}'" for name in nutrients.OFF_NAMES[:3])
    path = str(parquet).replace("'", "''")
    gtins: dict[str, set[str]] = defaultdict(set)
    with duckdb.connect() as con:
        con.execute("SET enable_progress_bar = false")
        cursor = con.execute(
            f"""
            SELECT code, countries_tags
            FROM read_parquet('{path}')
            WHERE len(list_filter(
                      nutriments, n -> n.name IN ({energy}) AND n."100g" IS NOT NULL)) > 0
              AND (len(list_filter(product_name, x -> trim(coalesce(x.text, '')) <> '')) > 0
                   OR trim(coalesce(brands, '')) <> '')
            """
        )
        while rows := cursor.fetchmany(50_000):
            for code, tags in rows:
                gtin14 = barcodes.normalize(code or "")
                if gtin14:
                    for tag in tags or []:
                        gtins[tag].add(gtin14)
    return dict(
        sorted(
            ((tag, len(codes)) for tag, codes in gtins.items()),
            key=lambda item: (-item[1], item[0]),
        )
    )
