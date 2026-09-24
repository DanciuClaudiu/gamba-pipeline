"""Builds reference.sqlite: USDA generic foods and the exercise library (SPEC §3.10, §4.1, §10)."""

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

from gamba_pipeline import exercises as exercise_library
from gamba_pipeline import sqlite_writer, usda, validate
from gamba_pipeline.usda import GenericFood


@dataclass
class ReferenceReport:
    foods: int = 0
    exercises: int = 0
    size_bytes: int = 0
    rejected: list[tuple[GenericFood, str]] = field(default_factory=list)
    flagged: list[tuple[GenericFood, str]] = field(default_factory=list)
    adjusted: list[tuple[GenericFood, str]] = field(default_factory=list)
    duplicates: list[GenericFood] = field(default_factory=list)


def select_foods(
    foundation: list[GenericFood], sr_legacy: list[GenericFood], report: ReferenceReport
) -> list[GenericFood]:
    """Valid foods. A name in both sources keeps the Foundation food, the newer analysis; a
    rejected Foundation food doesn't claim its name."""
    kept: list[GenericFood] = []
    names: set[str] = set()
    for original in [*foundation, *sr_legacy]:
        nutrients, adjustment = validate.adjust(original.nutrients)
        food = replace(original, nutrients=nutrients)
        verdict = validate.check(nutrients)
        if verdict.rejected:
            report.rejected.append((food, verdict.rejected))
            continue
        key = food.name.lower()
        if key in names:
            report.duplicates.append(food)
            continue
        names.add(key)
        if verdict.flagged:
            report.flagged.append((food, verdict.flagged))
        if adjustment:
            report.adjusted.append((food, adjustment))
        kept.append(food)
    return kept


def build(
    *,
    foundation_dir: Path,
    sr_legacy_dir: Path,
    exercises_json: Path,
    overrides_json: Path,
    output: Path,
    meta: dict[str, str],
) -> ReferenceReport:
    report = ReferenceReport()
    foods = select_foods(
        usda.read_foods(foundation_dir, "foundation"),
        usda.read_foods(sr_legacy_dir, "sr_legacy"),
        report,
    )
    exercises = exercise_library.build(
        json.loads(exercises_json.read_text(encoding="utf-8")),
        json.loads(overrides_json.read_text(encoding="utf-8")),
    )
    sqlite_writer.write(output, foods, exercises, meta)
    report.foods = len(foods)
    report.exercises = len(exercises)
    report.size_bytes = output.stat().st_size
    return report


def write_report(report: ReferenceReport, path: Path) -> None:
    """The build's counts and every rejected, duplicate, flagged and adjusted food, for
    build/REPORT.md."""

    def food(item: GenericFood, **extra: str) -> dict:
        return {"fdcId": item.fdc_id, "name": item.name, "source": item.source, **extra}

    data = {
        "foods": report.foods,
        "exercises": report.exercises,
        "sizeBytes": report.size_bytes,
        "rejected": [food(item, reason=reason) for item, reason in report.rejected],
        "duplicates": [food(item) for item in report.duplicates],
        "flagged": [food(item, reason=reason) for item, reason in report.flagged],
        "adjusted": [food(item, note=note) for item, note in report.adjusted],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
