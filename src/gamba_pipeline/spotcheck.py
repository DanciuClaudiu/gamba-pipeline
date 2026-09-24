"""Spot checks (M2 acceptance): each country's most-scanned products must be found by barcode and
by name, with the per-100 values of their source record.

The expected values are read from the raw inputs by the SQL below, not by the pipeline's own
readers, and committed in spotchecks/<country>.json; `refresh` rewrites them after a new export."""

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

from gamba_pipeline import barcodes
from gamba_pipeline.countries import Country

FIELDS = ("kcal", "proteinG", "carbsG", "sugarsG", "fatG", "satFatG", "fiberG", "sodiumMg")
PER_COUNTRY = 20


@dataclass(frozen=True)
class SpotCheck:
    gtin14: str
    name: str
    query: str  # what a person would type to find it
    source: str
    source_ref: str
    expected: dict[str, float | None]


@dataclass(frozen=True)
class SpotResult:
    check: SpotCheck
    by_barcode: bool
    name_rank: int | None  # position among the name search's results
    mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.by_barcode and self.name_rank is not None and not self.mismatches


def as_json(result: SpotResult) -> dict:
    return {
        "gtin14": result.check.gtin14,
        "name": result.check.name,
        "byBarcode": result.by_barcode,
        "nameRank": result.name_rank,
        "mismatches": list(result.mismatches),
        "passed": result.passed,
    }


def load(path: Path) -> list[SpotCheck]:
    return [SpotCheck(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def save(path: Path, checks: list[SpotCheck]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps([asdict(check) for check in checks], ensure_ascii=False, indent=1)
    path.write_text(text + "\n", encoding="utf-8")


def match_query(query: str) -> str:
    """An FTS5 query for every word as a prefix ("coca cola" → '"coca"* "cola"*')."""
    words = [word.replace('"', "") for word in query.split() if re.search(r"\w", word)]
    return " ".join(f'"{word}"*' for word in words)


def close(actual: float | None, expected: float | None) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return abs(actual - expected) <= 0.01 + 0.001 * abs(expected)


def run(pack: Path, checks: list[SpotCheck]) -> list[SpotResult]:
    results = []
    with sqlite3.connect(f"file:{pack}?mode=ro", uri=True) as db:
        for check in checks:
            row = db.execute(
                f"SELECT id, {', '.join(FIELDS)} FROM product WHERE gtin14 = ?", (check.gtin14,)
            ).fetchone()
            if row is None:
                results.append(SpotResult(check, False, None, ()))
                continue
            product_id, *values = row
            ids = db.execute(
                "SELECT rowid FROM productFts WHERE productFts MATCH ? ORDER BY rank",
                (match_query(check.query),),
            ).fetchall()
            rank = next((i for i, (rowid,) in enumerate(ids, start=1) if rowid == product_id), None)
            mismatches = tuple(
                f"{field} {value} ≠ {check.expected[field]}"
                for field, value in zip(FIELDS, values, strict=True)
                if not close(value, check.expected[field])
            )
            results.append(SpotResult(check, True, rank, mismatches))
    return results


def refresh(pack: Path, country: Country, parquet: Path, branded: Path | None) -> list[SpotCheck]:
    """The country's most-scanned products in the pack, with expected values read from their
    source records."""
    with sqlite3.connect(f"file:{pack}?mode=ro", uri=True) as db:
        in_pack = {
            row[0]: row[1:]
            for row in db.execute("SELECT gtin14, name, source, sourceRef FROM product")
        }
    chosen: list[tuple[str, str, str, str]] = []
    for code in _most_scanned(parquet, country):
        gtin14 = barcodes.normalize(code)
        if gtin14 in in_pack and gtin14 not in {c[0] for c in chosen}:
            chosen.append((gtin14, *in_pack[gtin14]))
        if len(chosen) == PER_COUNTRY:
            break
    off_values = _off_values(parquet, [ref for _, _, source, ref in chosen if source == "off"])
    usda_refs = [ref for _, _, source, ref in chosen if source == "usda"]
    usda_values = _usda_values(branded, usda_refs) if branded and usda_refs else {}
    return [
        SpotCheck(
            gtin14=gtin14,
            name=name,
            query=" ".join(re.findall(r"[^\W_]+", name)[:3]).lower(),
            source=source,
            source_ref=ref,
            expected=(off_values if source == "off" else usda_values)[ref],
        )
        for gtin14, name, source, ref in chosen
    ]


def _most_scanned(parquet: Path, country: Country) -> list[str]:
    """Codes by Open Food Facts' scan ranking in the country: its top-N-<country>-scans-<year>
    tags for the latest year, smallest N first, then by scans."""
    path = str(parquet).replace("'", "''")
    pattern = f"^top-([0-9]+)-{country.code}-scans-([0-9]{{4}})$"
    with duckdb.connect() as con:
        con.execute("SET enable_progress_bar = false")
        rows = con.execute(
            f"""
            WITH ranked AS (
                SELECT code, unique_scans_n,
                       CAST(regexp_extract(tag, ?, 1) AS INTEGER) AS tier,
                       CAST(regexp_extract(tag, ?, 2) AS INTEGER) AS year
                FROM (
                    SELECT code, unique_scans_n, unnest(popularity_tags) AS tag
                    FROM read_parquet('{path}')
                    WHERE list_contains(countries_tags, ?)
                )
                WHERE regexp_matches(tag, ?)
            )
            SELECT code FROM ranked
            WHERE year = (SELECT max(year) FROM ranked)
            GROUP BY code, unique_scans_n
            ORDER BY min(tier), unique_scans_n DESC NULLS LAST, code
            LIMIT 500
            """,
            [pattern, pattern, country.off_tag, pattern],
        ).fetchall()
    return [code for (code,) in rows if code]


def _off_values(parquet: Path, codes: list[str]) -> dict[str, dict[str, float | None]]:
    """Per-100 values straight from the export: kcal, else kJ ÷ 4.184; sodium, else salt ÷ 2.5."""
    if not codes:
        return {}
    path = str(parquet).replace("'", "''")

    def value(name: str) -> str:
        return f"max(CAST(n.\"100g\" AS DOUBLE)) FILTER (WHERE n.name = '{name}')"

    with duckdb.connect() as con:
        con.execute("SET enable_progress_bar = false")
        rows = con.execute(
            f"""
            WITH n AS (
                SELECT code, unnest(nutriments) AS n FROM read_parquet('{path}')
                WHERE code IN (SELECT unnest(?))
            ), v AS (
                SELECT code,
                       coalesce({value("energy-kcal")}, {value("energy-kj")} / 4.184,
                                {value("energy")} / 4.184) AS kcal,
                       {value("proteins")} AS protein, {value("carbohydrates")} AS carbs,
                       {value("sugars")} AS sugars, {value("fat")} AS fat,
                       {value("saturated-fat")} AS sat_fat, {value("fiber")} AS fiber,
                       coalesce({value("sodium")}, {value("salt")} / 2.5) * 1000 AS sodium
                FROM n GROUP BY code
            )
            SELECT code, round(kcal, 3), round(protein, 3), round(carbs, 3), round(sugars, 3),
                   round(fat, 3), round(sat_fat, 3), round(fiber, 3), round(sodium, 3)
            FROM v
            """,
            [codes],
        ).fetchall()
    return {row[0]: dict(zip(FIELDS, row[1:], strict=True)) for row in rows}


def _usda_values(folder: Path, fdc_ids: list[str]) -> dict[str, dict[str, float | None]]:
    """Per-100 values straight from USDA Branded, by FDC ID."""
    path = str(folder / "food_nutrient.csv").replace("'", "''")

    def value(*ids: int) -> str:
        return (
            "coalesce("
            + ", ".join(
                f"max(TRY_CAST(amount AS DOUBLE)) FILTER (WHERE nutrient_id = '{i}')" for i in ids
            )
            + ")"
        )

    with duckdb.connect() as con:
        con.execute("SET enable_progress_bar = false")
        rows = con.execute(
            f"""
            SELECT fdc_id, {value(1008, 2048, 2047)}, {value(1003)}, {value(1005, 1050)},
                   {value(2000, 1063)}, {value(1004, 1085)}, {value(1258)}, {value(1079)},
                   {value(1093)}
            FROM read_csv('{path}', header = true, all_varchar = true)
            WHERE fdc_id IN (SELECT unnest(?))
            GROUP BY fdc_id
            """,
            [fdc_ids],
        ).fetchall()
    return {row[0]: dict(zip(FIELDS, row[1:], strict=True)) for row in rows}
