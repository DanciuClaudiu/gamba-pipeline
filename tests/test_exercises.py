import json
from pathlib import Path

import pytest

from gamba_pipeline.exercises import build, title_case, tracking_type

FIXTURES = Path(__file__).parent / "fixtures"
RAW = json.loads((FIXTURES / "exercises.json").read_text())
OVERRIDES = json.loads((FIXTURES / "overrides.json").read_text())


@pytest.mark.parametrize(
    ("raw", "cased"),
    [
        ("Barbell Squat To A Bench", "Barbell Squat to a Bench"),
        ("Around The Worlds", "Around the Worlds"),
        ("Back Flyes - With Bands", "Back Flyes - With Bands"),
        ("Isometric Neck Exercise - Front And Back", "Isometric Neck Exercise - Front and Back"),
        ("Chest Push (multiple response)", "Chest Push (Multiple Response)"),
        ("Front Cone Hops (or hurdle hops)", "Front Cone Hops (or Hurdle Hops)"),
        ("Close-Grip Push-Up off of a Dumbbell", "Close-Grip Push-Up off of a Dumbbell"),
        ("Bent Over Barbell Row", "Bent Over Barbell Row"),
        ("3/4 Sit-Up", "3/4 Sit-Up"),
        ("Landmine 180's", "Landmine 180's"),
    ],
)
def test_title_case(raw, cased):
    assert title_case(raw) == cased


@pytest.mark.parametrize(
    ("exercise_id", "expected"),
    [
        ("Plank", "duration"),
        ("Band_Assisted_Pull-Up", "assisted"),
        ("Pullups", "bodyweightReps"),
        ("Back_Flyes_-_With_Bands", "bodyweightReps"),
        ("Barbell_Squat_To_A_Bench", "weightReps"),
        ("Chest_Push_multiple_response", "weightReps"),
    ],
)
def test_tracking_type_rules(exercise_id, expected):
    raw = next(raw for raw in RAW if raw["id"] == exercise_id)
    assert tracking_type(raw) == expected


def test_builds_the_included_categories_sorted_by_name():
    names = [exercise.name for exercise in build(RAW, OVERRIDES)]
    assert names == [
        "Back Flyes - With Bands",
        "Band Assisted Pull-Up",
        "Barbell Squat to a Bench",
        "Chest Push (Multiple Response)",
        "Plank",
        "Pull-Ups",
    ]


def test_keeps_ids_muscles_and_the_first_image():
    squat = next(e for e in build(RAW, OVERRIDES) if e.id == "Barbell_Squat_To_A_Bench")
    assert squat.primary_muscles == ("quadriceps",)
    assert squat.secondary_muscles == ("glutes", "hamstrings")
    assert squat.image_ref == "Barbell_Squat_To_A_Bench/0.jpg"
    assert squat.tracking_type == "weightReps"


def test_overrides_can_set_the_tracking_type():
    exercises = build(RAW, {"Plank": {"trackingType": "bodyweightReps"}})
    assert next(e for e in exercises if e.id == "Plank").tracking_type == "bodyweightReps"


def test_rejects_overrides_for_unknown_exercises():
    with pytest.raises(ValueError, match="unknown exercises"):
        build(RAW, {"Not_An_Exercise": {"name": "X"}})


def test_rejects_unknown_tracking_types_and_fields():
    with pytest.raises(ValueError, match="tracking type"):
        build(RAW, {"Plank": {"trackingType": "timed"}})
    with pytest.raises(ValueError, match="unknown fields"):
        build(RAW, {"Plank": {"title": "Plank"}})


def test_the_real_overrides_file_matches_the_real_library():
    root = Path(__file__).resolve().parents[1]
    real = root / "build" / "inputs" / "exercises.json"
    if not real.exists():
        pytest.skip("run `uv run gamba-pipeline download` first")
    overrides = json.loads((root / "overrides" / "exercise_overrides.json").read_text())
    build(json.loads(real.read_text()), overrides)  # raises on a stale or mistyped override
