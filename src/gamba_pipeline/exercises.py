"""The exercise library (SPEC §4.1): free-exercise-db limited to five categories, names in Apple's
title case with reviewed overrides (Q35), and a tracking type for each exercise."""

import re
from dataclasses import dataclass

INCLUDED_CATEGORIES = frozenset(
    {"strength", "powerlifting", "olympic weightlifting", "strongman", "plyometrics"}
)
TRACKING_TYPES = frozenset({"weightReps", "bodyweightReps", "assisted", "duration"})
# Articles, conjunctions and short prepositions stay lowercase inside a name. "Over", "Up" and
# "Down" are left out: in "Bent Over Barbell Row" they're part of the movement's name.
SMALL_WORDS = frozenset(
    {
        "a", "an", "and", "as", "at", "but", "by", "for", "from", "in", "into",
        "nor", "of", "off", "on", "or", "the", "to", "via", "vs", "with",
    }
)  # fmt: skip
# Done without external weight: reps, with optional added weight.
BODYWEIGHT_EQUIPMENT = frozenset({None, "body only", "bands", "exercise ball", "foam roll"})
OVERRIDE_FIELDS = frozenset({"name", "trackingType"})


@dataclass(frozen=True)
class Exercise:
    id: str
    name: str
    category: str
    equipment: str | None
    force: str | None
    level: str | None
    mechanic: str | None
    primary_muscles: tuple[str, ...]
    secondary_muscles: tuple[str, ...]
    tracking_type: str
    image_ref: str | None


def title_case(name: str) -> str:
    """Apple title case. Small words are lowercase unless they start or end a segment; every other
    word starts with a capital. " - " starts a new segment, as in "Back Flyes - With Bands"."""
    return " - ".join(_title_case_segment(segment) for segment in name.split(" - "))


def _title_case_segment(segment: str) -> str:
    words = segment.split(" ")
    cased = []
    for index, word in enumerate(words):
        inner = 0 < index < len(words) - 1
        if inner and word.strip("()").lower() in SMALL_WORDS:
            cased.append(word.lower())
        else:
            cased.append(_capitalize_first_letter(word))
    return " ".join(cased)


def _capitalize_first_letter(word: str) -> str:
    for index, character in enumerate(word):
        if character.isalpha():
            return word[:index] + character.upper() + word[index + 1 :]
    return word


def tracking_type(raw: dict) -> str:
    """Rules first; the overrides file corrects the exceptions (SPEC §4.1)."""
    if raw.get("force") == "static":
        return "duration"
    if re.search(r"\bassisted\b", raw["name"], re.IGNORECASE):
        return "assisted"
    if raw.get("equipment") in BODYWEIGHT_EQUIPMENT:
        return "bodyweightReps"
    return "weightReps"


def build(raw_exercises: list[dict], overrides: dict[str, dict]) -> list[Exercise]:
    """The included exercises, sorted by name. Fails on an override for an unknown exercise, an
    unknown field or an unknown tracking type, so a typo can't slip through."""
    _check_overrides(overrides, known={raw["id"] for raw in raw_exercises})
    exercises = []
    for raw in raw_exercises:
        if raw["category"] not in INCLUDED_CATEGORIES:
            continue
        override = overrides.get(raw["id"], {})
        images = raw.get("images") or []
        exercises.append(
            Exercise(
                id=raw["id"],
                name=override.get("name") or title_case(raw["name"].strip()),
                category=raw["category"],
                equipment=raw.get("equipment"),
                force=raw.get("force"),
                level=raw.get("level"),
                mechanic=raw.get("mechanic"),
                primary_muscles=tuple(raw.get("primaryMuscles") or ()),
                secondary_muscles=tuple(raw.get("secondaryMuscles") or ()),
                tracking_type=override.get("trackingType") or tracking_type(raw),
                image_ref=images[0] if images else None,
            )
        )
    return sorted(exercises, key=lambda exercise: exercise.name.lower())


def _check_overrides(overrides: dict[str, dict], known: set[str]) -> None:
    unknown = sorted(set(overrides) - known)
    if unknown:
        raise ValueError(f"overrides for unknown exercises: {unknown}")
    for exercise_id, override in overrides.items():
        extra = sorted(set(override) - OVERRIDE_FIELDS)
        if extra:
            raise ValueError(f"{exercise_id}: unknown fields {extra}")
        if "trackingType" in override and override["trackingType"] not in TRACKING_TYPES:
            raise ValueError(f"{exercise_id}: unknown tracking type {override['trackingType']!r}")
