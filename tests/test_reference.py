import json
import sqlite3
from pathlib import Path

from gamba_pipeline import reference

FIXTURES = Path(__file__).parent / "fixtures"


def build(tmp_path):
    return reference.build(
        foundation_dir=FIXTURES / "usda" / "foundation",
        sr_legacy_dir=FIXTURES / "usda" / "sr_legacy",
        exercises_json=FIXTURES / "exercises.json",
        overrides_json=FIXTURES / "overrides.json",
        output=tmp_path / "reference.sqlite",
        meta={"buildDate": "2026-09-23", "usdaFoundation": "2026-04-30"},
    )


def test_builds_the_golden_fixture(tmp_path):
    report = build(tmp_path)
    with sqlite3.connect(tmp_path / "reference.sqlite") as db:
        foods = db.execute("SELECT fdcId, name, source, kcal FROM food ORDER BY fdcId").fetchall()
        servings = db.execute("SELECT fdcId, label, grams FROM serving ORDER BY 1, 2").fetchall()
        exercises = [name for (name,) in db.execute("SELECT name FROM exercise ORDER BY name")]
        meta = dict(db.execute("SELECT key, value FROM meta"))
    assert foods == [
        (100, "Hummus, commercial", "foundation", 229.0),
        (101, "Crème fraîche", "foundation", 393.0),
        (103, "Broccoli, raw", "foundation", 39.0),
        (105, "Chicken, breast, meat and skin, raw", "foundation", 132.8),
        (200, "Butter, salted", "sr_legacy", 717.0),
        (202, "Lard", "sr_legacy", 902.0),
        (203, "Alcoholic beverage, rice (sake)", "sr_legacy", 134.0),
    ]
    assert servings == [
        (100, "tablespoon", 14.8),
        (103, "cup, chopped", 91.0),
        (200, 'pat (1" sq, 1/3" high)', 5.0),
        (200, "tbsp", 14.2),
        (203, "fl oz", 29.1),
    ]
    assert exercises == [
        "Back Flyes - With Bands",
        "Band Assisted Pull-Up",
        "Barbell Squat to a Bench",
        "Chest Push (Multiple Response)",
        "Plank",
        "Pull-Ups",
    ]
    assert meta == {
        "schemaVersion": "1.0",
        "buildDate": "2026-09-23",
        "usdaFoundation": "2026-04-30",
    }
    assert (report.foods, report.exercises) == (7, 6)
    assert report.size_bytes > 0


def test_stores_adjusted_carbs(tmp_path):
    report = build(tmp_path)
    with sqlite3.connect(tmp_path / "reference.sqlite") as db:
        assert db.execute("SELECT carbsG FROM food WHERE fdcId = 105").fetchone() == (0.0,)
    assert [(food.fdc_id, note) for food, note in report.adjusted] == [
        (105, "carbs -0.43 g set to 0 g"),
    ]


def test_reports_rejected_duplicate_and_flagged_foods(tmp_path):
    report = build(tmp_path)
    assert [(food.name, reason) for food, reason in report.rejected] == [
        ("Mystery powder", "no energy value"),
        ("Impossible bar", "protein + carbs + fat 120.0 g over 105 g"),
    ]
    assert [(food.fdc_id, food.name) for food in report.duplicates] == [(201, "Broccoli, raw")]
    assert [(food.name, reason) for food, reason in report.flagged] == [
        ("Alcoholic beverage, rice (sake)", "energy 134 kcal, macros give 22 kcal"),
    ]


def test_writes_the_report(tmp_path):
    report = build(tmp_path)
    reference.write_report(report, tmp_path / "reference.report.json")
    data = json.loads((tmp_path / "reference.report.json").read_text(encoding="utf-8"))
    assert (data["foods"], data["exercises"]) == (7, 6)
    assert data["rejected"][0] == {
        "fdcId": 104,
        "name": "Mystery powder",
        "source": "foundation",
        "reason": "no energy value",
    }
    assert data["duplicates"] == [{"fdcId": 201, "name": "Broccoli, raw", "source": "sr_legacy"}]
    assert data["adjusted"] == [
        {
            "fdcId": 105,
            "name": "Chicken, breast, meat and skin, raw",
            "source": "foundation",
            "note": "carbs -0.43 g set to 0 g",
        }
    ]
