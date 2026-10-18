"""build/REPORT.md (M2.3): what the build produced, what it left out and why, the spot checks and
the pack threshold (Q5). The complete rejected and flagged lists go to build/report/*.csv, which
are rebuilt every time and not committed."""

import csv
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from gamba_pipeline.countries import COUNTRIES, THRESHOLD, Country
from gamba_pipeline.inputs import Input, sha256_of

THRESHOLDS = (1_000, 2_000, 5_000, 10_000, 20_000)
NOT_COUNTRIES = frozenset({"en:world"})
EXAMPLES = 2


def reason_group(reason: str) -> str:
    """ "energy 929 kcal over 905 kcal" → "energy over the limit"."""
    if reason.startswith("protein + carbs + fat"):
        return "protein + carbs + fat over 105 g"
    if reason.startswith("energy") and " over " in reason:
        return "energy over the limit"
    if reason.startswith("energy"):
        return "energy doesn't match the macros"
    return reason


def country_name(tag: str) -> str:
    """ "en:united-kingdom" → "United Kingdom"."""
    return tag.split(":", 1)[-1].replace("-", " ").title()


def megabytes(size: int) -> str:
    return f"{size / 1_000_000:.1f} MB"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _table(header: list[str], rows: list[list]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return lines


def write(build: Path, build_date: str, pinned: dict[str, Input]) -> Path:
    """Writes build/REPORT.md and build/report/*.csv from the build's outputs."""
    lists = build / "report"
    lines = [
        "# Pipeline report",
        "",
        f"Built {build_date} with `uv run gamba-pipeline` from the inputs pinned in `inputs.toml`.",
        "Complete lists of rejected and flagged rows: `build/report/*.csv` (local, not committed).",
        "",
        "## Inputs",
        "",
        *_table(
            ["Input", "Release", "SHA-256"],
            [[name, item.release, f"`{item.sha256[:16]}…`"] for name, item in pinned.items()],
        ),
    ]
    lines += _reference_section(build, lists)
    lines += _packs_section(build, lists)
    lines += _spotcheck_section(build)
    lines += _threshold_section(build)
    path = build / "REPORT.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _reference_section(build: Path, lists: Path) -> list[str]:
    data = _read_json(build / "reference.report.json")
    database = build / "reference.sqlite"
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
        sources = dict(db.execute("SELECT source, count(*) FROM food GROUP BY 1"))
        tracking = db.execute(
            "SELECT trackingType, count(*) FROM exercise GROUP BY 1 ORDER BY 2 DESC, 1"
        ).fetchall()
    _write_csv(
        lists / "reference-rejected.csv",
        ["fdcId", "name", "source", "reason"],
        [[f["fdcId"], f["name"], f["source"], f["reason"]] for f in data["rejected"]],
    )
    _write_csv(
        lists / "reference-flagged.csv",
        ["fdcId", "name", "source", "reason"],
        [[f["fdcId"], f["name"], f["source"], f["reason"]] for f in data["flagged"]],
    )
    by_type = ", ".join(f"{kind} {count:,}" for kind, count in tracking)
    return [
        "",
        "## Reference database",
        "",
        *_table(
            ["", ""],
            [
                [
                    "Foods",
                    f"{data['foods']:,} (Foundation {sources.get('foundation', 0):,}, "
                    f"SR Legacy {sources.get('sr_legacy', 0):,})",
                ],
                ["Rejected", f"{len(data['rejected']):,}"],
                ["Duplicate names (kept Foundation)", f"{len(data['duplicates']):,}"],
                ["Flagged", f"{len(data['flagged']):,}"],
                ["Carbs set to 0 g", f"{len(data['adjusted']):,}"],
                ["Exercises", f"{data['exercises']:,} ({by_type})"],
                ["Size", megabytes(data["sizeBytes"])],
                ["SHA-256", f"`{sha256_of(database)}`"],
            ],
        ),  # fmt: skip
    ]


def _packs_section(build: Path, lists: Path) -> list[str]:
    packs = sorted((build / "packs").glob("food-*.report.json"))
    rows, read, reasons, examples, merges = [], [], {}, [], []
    for path in packs:
        data = _read_json(path)
        pack_id = path.name.removesuffix(".report.json")
        database = build / "packs" / pack_id / "pack.sqlite"
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as db:
            complete = db.execute("SELECT count(*) FROM product WHERE isComplete").fetchone()[0]
        archive = build / "packages" / f"{pack_id}.aar"
        stats = data["stats"]
        rows.append(
            [
                pack_id,
                data["products"],
                complete,
                data["sizeBytes"],
                archive.stat().st_size if archive.exists() else None,
                len(data["rejected"]),
                len(data["flagged"]),
                stats.get("named by brand", 0),
                stats.get("no name or brand", 0),
            ]
        )
        read.append(
            [
                pack_id,
                *(
                    f"{stats.get(f'off {key}', 0) + stats.get(f'usda {key}', 0):,}"
                    for key in (
                        "products",
                        "without energy",
                        "invalid barcode",
                        "duplicate barcode",
                    )
                ),
            ]
        )
        for item in data["rejected"]:
            group = reason_group(item["reason"])
            reasons.setdefault(group, {}).setdefault(pack_id, 0)
            reasons[group][pack_id] += 1
        examples += [
            [pack_id, f"`{f['gtin14']}`", f["name"], f["reason"]]
            for f in data["flagged"][:EXAMPLES]
        ]
        if "in both" in stats:
            merges.append(
                [
                    pack_id,
                    f"{stats['in both']:,}",
                    f"{stats.get('usda nutrients kept', 0):,}",
                    f"{stats.get('usda only', 0):,}",
                ]
            )
        _write_csv(
            lists / f"{pack_id}-rejected.csv",
            ["source", "ref", "reason"],
            [[r["source"], r["ref"], r["reason"]] for r in data["rejected"]],
        )
        _write_csv(
            lists / f"{pack_id}-flagged.csv",
            ["gtin14", "name", "reason"],
            [[f["gtin14"], f["name"], f["reason"]] for f in data["flagged"]],
        )
    pack_ids = [path.name.removesuffix(".report.json") for path in packs]
    groups = sorted(reasons)
    lines = [
        "",
        "## Packs",
        "",
        *_table(
            [
                "Pack",
                "Products",
                "Complete",
                "Size",
                "Download",
                "Rejected",
                "Flagged",
                "Named by brand",
                "Left out (no name or brand)",
            ],
            [_pack_row(row) for row in [*rows, _total(rows)]],
        ),  # fmt: skip
        "",
        "### What was read",
        "",
        "Products read from Open Food Facts (and USDA Branded for the US), and those left out "
        "before validation.",
        "",
        *_table(["Pack", "Read", "Without energy", "Invalid barcode", "Duplicate barcode"], read),
        "",
        "### Why rows were rejected",
        "",
        *_table(
            ["Pack", *groups],
            [
                [pack_id, *(f"{reasons[group].get(pack_id, 0):,}" for group in groups)]
                for pack_id in pack_ids
            ],
        ),
    ]
    if merges:
        lines += [
            "",
            "### USDA Branded merge",
            "",
            *_table(["Pack", "In both", "USDA nutrients kept", "USDA only"], merges),
        ]
    lines += [
        "",
        "### Flagged rows",
        "",
        "Energy that doesn't match 4P + 4C + 9F by more than max(20 kcal, 20%). Kept and never "
        f"fixed (P12). The first {EXAMPLES} per pack:",
        "",
        *_table(["Pack", "GTIN-14", "Name", "Why"], examples),
    ]
    return lines


def _total(rows: list[list]) -> list:
    """The Packs table's last row: every column added up, the download only when every pack is
    packaged."""
    columns = [[row[i] for row in rows] for i in range(1, 9)]
    download = columns[3]
    return [
        "Total",
        *(sum(column) for column in columns[:3]),
        sum(download) if download and None not in download else None,
        *(sum(column) for column in columns[4:]),
    ]


def _pack_row(row: list) -> list[str]:
    pack_id, products, complete, size, download, *counts = row
    return [
        pack_id,
        f"{products:,}",
        f"{complete:,}",
        megabytes(size),
        megabytes(download) if download is not None else "not packaged",
        *(f"{count:,}" for count in counts),
    ]


def _spotcheck_section(build: Path) -> list[str]:
    path = build / "spotchecks.json"
    if not path.exists():
        return ["", "## Spot checks", "", "Not run."]
    results = _read_json(path)
    rows, failures = [], []
    for pack_id, items in sorted(results.items()):
        rows.append(
            [
                pack_id,
                len(items),
                sum(item["byBarcode"] for item in items),
                sum(item["nameRank"] is not None for item in items),
                sum(not item["mismatches"] for item in items if item["byBarcode"]),
                sum(item["passed"] for item in items),
            ]
        )
        failures += [
            [pack_id, f"`{item['gtin14']}`", item["name"], "; ".join(item["mismatches"])]
            for item in items
            if not item["passed"]
        ]
    lines = [
        "",
        "## Spot checks",
        "",
        "The most-scanned products in each country (`spotchecks/<country>.json`), looked up by "
        "barcode and by name, with the per-100 values of their source record.",
        "",
        *_table(["Pack", "Products", "By barcode", "By name", "Values", "Passed"], rows),
    ]
    if failures:
        lines += ["", *_table(["Pack", "GTIN-14", "Name", "Problem"], failures)]
    return lines


def _threshold_section(build: Path) -> list[str]:
    survey = {
        tag: count
        for tag, count in _read_json(build / "survey.json").items()
        if tag not in NOT_COUNTRIES
    }
    built = {
        path.name.removesuffix(".report.json"): _read_json(path)
        for path in (build / "packs").glob("food-*.report.json")
    }
    pack_bytes = sum(data["sizeBytes"] for data in built.values())
    per_product = pack_bytes / max(1, sum(data["products"] for data in built.values()))
    archives = [build / "packages" / f"{pack_id}.aar" for pack_id in built]
    downloads = ""
    if archives and all(archive.exists() for archive in archives):
        share = sum(archive.stat().st_size for archive in archives) / pack_bytes
        downloads = f" Downloads are about {share:.0%} of the size."
    rows = []
    for threshold in THRESHOLDS:
        counts = [count for count in survey.values() if count >= threshold]
        rows.append(
            [
                f"{threshold:,}",
                len(counts),
                f"{sum(counts):,}",
                megabytes(int(sum(counts) * per_product)),
            ]
        )
    over = sum(count >= THRESHOLD for count in survey.values())
    countries = [
        COUNTRIES[code] for pack_id in built if (code := pack_id.removeprefix("food-")) in COUNTRIES
    ]
    missing, under = threshold_changes(survey, countries, THRESHOLD)
    lines = [
        "",
        "## Pack threshold (Q5)",
        "",
        "Products per country with energy, a valid barcode and a name or brand, before "
        f"validation. Sizes are estimated at {per_product:.0f} bytes per product, the average of "
        f"the packs built above.{downloads}",
        "",
        *_table(["At least", "Countries", "Products", "Estimated size"], rows),
        "",
        f"**Threshold:** {THRESHOLD:,} products (Q5): {over} "
        f"{'country' if over == 1 else 'countries'} over it.",
        "",
    ]
    if missing:
        lines += [
            "Over the threshold without a pack (add them to `countries.py`, with their languages):",
            "",
            *_table(
                ["Country", "Open Food Facts tag", "Products"],
                [[country_name(tag), f"`{tag}`", f"{count:,}"] for tag, count in missing],
            ),
        ]
    else:
        lines.append("Over the threshold without a pack: none.")
    if under:
        listed = ", ".join(f"{pack_id} ({count:,})" for pack_id, count in under)
        lines += ["", f"Packs under the threshold, kept: {listed}."]
    return lines


def threshold_changes(
    survey: dict[str, int], countries: Iterable[Country], threshold: int
) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """Open Food Facts tags over the threshold that none of `countries` has, most products first;
    and the packs of `countries` under it, by ID, with their count (0 when the survey lacks it)."""
    countries = list(countries)
    tags = {country.off_tag for country in countries}
    missing = sorted(
        (
            (tag, count)
            for tag, count in survey.items()
            if count >= threshold and tag not in tags and tag not in NOT_COUNTRIES
        ),
        key=lambda item: (-item[1], item[0]),
    )
    under = sorted(
        (country.pack_id, survey.get(country.off_tag, 0))
        for country in countries
        if survey.get(country.off_tag, 0) < threshold
    )
    return missing, under
