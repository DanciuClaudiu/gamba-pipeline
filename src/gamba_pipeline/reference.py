"""Builds reference.sqlite: USDA generic foods and the exercise library (SPEC §3.10, §4.1, §10)."""

import json
from dataclasses import dataclass, field
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
    duplicates: list[GenericFood] = field(default_factory=list)


def select_foods(
    foundation: list[GenericFood], sr_legacy: list[GenericFood], report: ReferenceReport
) -> list[GenericFood]:
    """Valid foods. A name in both sources keeps the Foundation food, the newer analysis; a
    rejected Foundation food doesn't claim its name."""
    kept: list[GenericFood] = []
    names: set[str] = set()
    for food in [*foundation, *sr_legacy]:
        verdict = validate.check(food.nutrients)
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
