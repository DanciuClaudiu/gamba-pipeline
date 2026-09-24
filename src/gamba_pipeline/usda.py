"""Generic foods from USDA FoodData Central's Foundation Foods and SR Legacy CSV downloads
(SPEC §10 step 2)."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import duckdb

from gamba_pipeline.nutrients import Nutrients, from_usda
from gamba_pipeline.servings import Serving, dedupe, usda_serving

# The Foundation download also contains lab samples and acquisitions; only these rows are foods.
DATA_TYPES = {"foundation": "foundation_food", "sr_legacy": "sr_legacy_food"}


@dataclass(frozen=True)
class GenericFood:
    fdc_id: int
    name: str
    category: str | None
    source: str
    nutrients: Nutrients
    servings: tuple[Serving, ...]


def _csv(folder: Path, name: str) -> str:
    path = str(folder / name).replace("'", "''")
    return f"read_csv('{path}', header = true, all_varchar = true)"


def read_foods(folder: Path, source: str) -> list[GenericFood]:
    """The source's foods with their nutrients and servings, sorted by FDC ID."""
    data_type = DATA_TYPES[source]
    with duckdb.connect() as con:
        foods = con.execute(
            f"""
            SELECT CAST(f.fdc_id AS INTEGER), trim(f.description), c.description
            FROM {_csv(folder, "food.csv")} f
            LEFT JOIN {_csv(folder, "food_category.csv")} c ON c.id = f.food_category_id
            WHERE f.data_type = ?
            ORDER BY 1
            """,
            [data_type],
        ).fetchall()
        ids = {row[0] for row in foods}

        amounts: dict[int, dict[int, float]] = defaultdict(dict)
        for fdc_id, nutrient_id, amount in con.execute(
            f"""
            SELECT CAST(fdc_id AS INTEGER), CAST(nutrient_id AS INTEGER), TRY_CAST(amount AS DOUBLE)
            FROM {_csv(folder, "food_nutrient.csv")}
            """
        ).fetchall():
            if fdc_id in ids and amount is not None:  # an empty amount is missing, not 0
                amounts[fdc_id][nutrient_id] = amount

        portions: dict[int, list[Serving]] = defaultdict(list)
        for fdc_id, amount, unit, modifier, grams in con.execute(
            f"""
            SELECT CAST(p.fdc_id AS INTEGER), TRY_CAST(p.amount AS DOUBLE), u.name, p.modifier,
                   TRY_CAST(p.gram_weight AS DOUBLE)
            FROM {_csv(folder, "food_portion.csv")} p
            LEFT JOIN {_csv(folder, "measure_unit.csv")} u ON u.id = p.measure_unit_id
            ORDER BY 1, TRY_CAST(p.seq_num AS INTEGER) NULLS LAST, CAST(p.id AS INTEGER)
            """
        ).fetchall():
            serving = usda_serving(amount, unit, modifier, grams)
            if serving and fdc_id in ids:
                portions[fdc_id].append(serving)

    return [
        GenericFood(
            fdc_id=fdc_id,
            name=name,
            category=category,
            source=source,
            nutrients=from_usda(amounts[fdc_id]),
            servings=tuple(dedupe(portions[fdc_id])),
        )
        for fdc_id, name, category in foods
    ]
