"""Writes reference.sqlite (SPEC §3.10, PLAN §2.5): generic foods with servings, the exercise
library, FTS5 search tables and a meta table. The app opens it read-only."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from gamba_pipeline.exercises import Exercise
from gamba_pipeline.usda import GenericFood

SCHEMA_VERSION = "1.0"
# The same search options as the regional packs (SPEC §3.10).
FTS_OPTIONS = "tokenize = 'unicode61 remove_diacritics 2', prefix = '2 3'"

SCHEMA = f"""
CREATE TABLE meta (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL);

CREATE TABLE food (
    fdcId INTEGER PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    source TEXT NOT NULL,
    kcal REAL NOT NULL,
    proteinG REAL,
    carbsG REAL,
    sugarsG REAL,
    fatG REAL,
    satFatG REAL,
    fiberG REAL,
    sodiumMg REAL
);

CREATE TABLE serving (
    fdcId INTEGER NOT NULL REFERENCES food (fdcId),
    sortIndex INTEGER NOT NULL,
    label TEXT NOT NULL,
    grams REAL NOT NULL,
    PRIMARY KEY (fdcId, sortIndex)
) WITHOUT ROWID;

CREATE VIRTUAL TABLE foodFts USING fts5(
    name, content = 'food', content_rowid = 'fdcId', {FTS_OPTIONS}
);

CREATE TABLE exercise (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    equipment TEXT,
    force TEXT,
    level TEXT,
    mechanic TEXT,
    primaryMuscles TEXT NOT NULL,
    secondaryMuscles TEXT NOT NULL,
    trackingType TEXT NOT NULL,
    imageRef TEXT
);

CREATE VIRTUAL TABLE exerciseFts USING fts5(id UNINDEXED, name, {FTS_OPTIONS});
"""


def write(
    path: Path, foods: list[GenericFood], exercises: list[Exercise], meta: dict[str, str]
) -> None:
    """Writes a fresh database at `path`, replacing any existing file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [("schemaVersion", SCHEMA_VERSION), *sorted(meta.items())],
        )
        db.executemany(
            "INSERT INTO food VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    food.fdc_id,
                    food.name,
                    food.category,
                    food.source,
                    food.nutrients.kcal,
                    food.nutrients.protein_g,
                    food.nutrients.carbs_g,
                    food.nutrients.sugars_g,
                    food.nutrients.fat_g,
                    food.nutrients.sat_fat_g,
                    food.nutrients.fiber_g,
                    food.nutrients.sodium_mg,
                )
                for food in foods
            ],
        )
        db.executemany(
            "INSERT INTO serving VALUES (?, ?, ?, ?)",
            [
                (food.fdc_id, index, serving.label, serving.grams)
                for food in foods
                for index, serving in enumerate(food.servings)
            ],
        )
        db.execute("INSERT INTO foodFts (foodFts) VALUES ('rebuild')")
        db.executemany(
            "INSERT INTO exercise VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    exercise.id,
                    exercise.name,
                    exercise.category,
                    exercise.equipment,
                    exercise.force,
                    exercise.level,
                    exercise.mechanic,
                    json.dumps(list(exercise.primary_muscles)),
                    json.dumps(list(exercise.secondary_muscles)),
                    exercise.tracking_type,
                    exercise.image_ref,
                )
                for exercise in exercises
            ],
        )
        db.executemany(
            "INSERT INTO exerciseFts (id, name) VALUES (?, ?)",
            [(exercise.id, exercise.name) for exercise in exercises],
        )
        db.commit()
        db.execute("VACUUM")
