"""Products from the Open Food Facts Parquet export (SPEC §10 step 3)."""

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from gamba_pipeline import barcodes, names, nutrients
from gamba_pipeline.countries import Country
from gamba_pipeline.products import PackProduct, base_unit
from gamba_pipeline.servings import label_serving

BATCH = 20_000


def _query(parquet: Path) -> str:
    values = ",\n".join(
        f"list_filter(nutriments, n -> n.name = '{name}')[1].\"100g\""
        for name in nutrients.OFF_NAMES
    )
    path = str(parquet).replace("'", "''")
    return f"""
        SELECT code, lang, product_name, brands, quantity, product_quantity_unit, serving_size,
               TRY_CAST(serving_quantity AS DOUBLE), last_modified_t,
               {values}
        FROM read_parquet('{path}')
        WHERE list_contains(countries_tags, ?)
        """


def read_products(parquet: Path, country: Country, stats: Counter) -> list[PackProduct]:
    """The country's products with energy and a valid barcode, one per GTIN-14 (the one with more
    nutrients, then the most recently edited). `stats` counts what was left out."""
    kept: dict[str, PackProduct] = {}
    with duckdb.connect() as con:
        con.execute("SET enable_progress_bar = false")
        cursor = con.execute(_query(parquet), [country.off_tag])
        while rows := cursor.fetchmany(BATCH):
            for row in rows:
                stats["off products"] += 1
                product = _product(row, country)
                if product is None:
                    continue
                if product.nutrients.kcal is None:
                    stats["off without energy"] += 1
                    continue
                if product.gtin14 == "":
                    stats["off invalid barcode"] += 1
                    continue
                current = kept.get(product.gtin14)
                if current is not None:
                    stats["off duplicate barcode"] += 1
                    if _rank(current) >= _rank(product):
                        continue
                kept[product.gtin14] = product
    return [kept[gtin] for gtin in sorted(kept)]


def _rank(product: PackProduct) -> tuple[int, str]:
    return nutrients.count(product.nutrients), product.last_modified or ""


def _product(row: tuple, country: Country) -> PackProduct | None:
    code, lang, product_name, brands, quantity, quantity_unit, serving_size, serving_quantity = row[
        :8
    ]
    modified_t = row[8]
    per_100 = dict(zip(nutrients.OFF_NAMES, row[9:], strict=True))
    main, others = names.pick(
        {entry["lang"]: entry["text"] for entry in reversed(product_name or [])},
        lang,
        country.name_languages,
    )
    return PackProduct(
        gtin14=barcodes.normalize(code or "") or "",
        name=main,
        names=others,
        brand=names.first_brand(brands),
        quantity=names.clean(quantity),
        base_unit=base_unit(quantity_unit, quantity),
        nutrients=nutrients.from_off(per_100),
        serving=label_serving(serving_size, serving_quantity),
        source="off",
        source_ref=code,
        last_modified=datetime.fromtimestamp(modified_t, UTC).date().isoformat()
        if modified_t
        else None,
    )
