import json
import sqlite3

import pytest

from gamba_pipeline.exercises import Exercise
from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.servings import Serving
from gamba_pipeline.sqlite_writer import write
from gamba_pipeline.usda import GenericFood

FOODS = [
    GenericFood(
        101,
        "Crème fraîche",
        "Dairy and Egg Products",
        "foundation",
        Nutrients(kcal=393, protein_g=2.4, carbs_g=3, fat_g=40, sodium_mg=40),
        (Serving("tablespoon", 15.0),),
    ),
    GenericFood(201, "Broccoli, raw", None, "sr_legacy", Nutrients(kcal=34), ()),
]
EXERCISES = [
    Exercise(
        id="Plank",
        name="Plank",
        category="strength",
        equipment="body only",
        force="static",
        level="beginner",
        mechanic="isolation",
        primary_muscles=("abdominals",),
        secondary_muscles=(),
        tracking_type="duration",
        image_ref="Plank/0.jpg",
    )
]


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "reference.sqlite"
    write(path, FOODS, EXERCISES, {"buildDate": "2026-09-23"})
    connection = sqlite3.connect(path)
    yield connection
    connection.close()


def test_writes_meta(db):
    assert dict(db.execute("SELECT key, value FROM meta")) == {
        "schemaVersion": "1.0",
        "buildDate": "2026-09-23",
    }


def test_writes_foods_with_missing_values_as_null(db):
    rows = db.execute("SELECT * FROM food ORDER BY fdcId").fetchall()
    assert rows == [
        (101, "Crème fraîche", "Dairy and Egg Products", "foundation",
         393.0, 2.4, 3.0, None, 40.0, None, None, 40.0),
        (201, "Broccoli, raw", None, "sr_legacy",
         34.0, None, None, None, None, None, None, None),
    ]  # fmt: skip


def test_writes_servings_in_order(db):
    assert db.execute("SELECT * FROM serving").fetchall() == [(101, 0, "tablespoon", 15.0)]


def test_writes_exercises(db):
    row = db.execute("SELECT * FROM exercise").fetchone()
    assert row[:7] == ("Plank", "Plank", "strength", "body only", "static", "beginner", "isolation")
    assert json.loads(row[7]) == ["abdominals"]
    assert json.loads(row[8]) == []
    assert row[9:] == ("duration", "Plank/0.jpg")


def food_search(db, query):
    return [
        name
        for (name,) in db.execute(
            "SELECT f.name FROM foodFts s JOIN food f ON f.fdcId = s.rowid "
            "WHERE foodFts MATCH ? ORDER BY rank",
            (query,),
        )
    ]


def test_food_search_ignores_diacritics_and_matches_prefixes(db):
    assert food_search(db, '"creme"*') == ["Crème fraîche"]
    assert food_search(db, '"cr"*') == ["Crème fraîche"]  # 2-character prefix
    assert food_search(db, '"bro"*') == ["Broccoli, raw"]  # 3-character prefix


def test_exercise_search(db):
    rows = db.execute(
        "SELECT e.name FROM exerciseFts s JOIN exercise e ON e.id = s.id WHERE exerciseFts MATCH ?",
        ('"pla"*',),
    ).fetchall()
    assert rows == [("Plank",)]


def test_replaces_an_existing_file(tmp_path):
    path = tmp_path / "reference.sqlite"
    write(path, FOODS, EXERCISES, {})
    write(path, FOODS[:1], [], {})
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT count(*) FROM food").fetchone() == (1,)
