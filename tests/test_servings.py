import pytest

from gamba_pipeline.servings import Serving, dedupe, usda_serving


def test_foundation_portions_are_per_one_unit():
    assert usda_serving(2.0, "tablespoon", None, 29.6) == Serving("tablespoon", 14.8)


def test_foundation_modifiers_follow_the_unit():
    assert usda_serving(1.0, "cup", "chopped", 91.0) == Serving("cup, chopped", 91.0)


def test_sr_legacy_describes_the_portion_in_the_modifier():
    assert usda_serving(1.0, "undetermined", "can (12 fl oz)", 355.0) == Serving(
        "can (12 fl oz)", 355.0
    )
    assert usda_serving(0.5, "undetermined", "cup", 120.0) == Serving("cup", 240.0)


@pytest.mark.parametrize(
    ("amount", "unit", "modifier", "grams"),
    [
        (3.0, "undetermined", "oz", 85.0),  # the app converts weights itself
        (1.0, "lb", None, 453.6),
        (1.0, "paired raw w", None, 60.0),  # USDA lab pairing
        (1.0, "undetermined", None, 30.0),  # nothing to call it
        (1.0, "cup", None, 0.0),
        (0.0, "cup", None, 30.0),
        (None, "cup", None, 30.0),
    ],
)
def test_skips_what_isnt_a_usable_serving(amount, unit, modifier, grams):
    assert usda_serving(amount, unit, modifier, grams) is None


def test_keeps_the_first_serving_for_each_label():
    servings = [Serving("cup", 91.0), Serving("slice", 20.0), Serving("Cup", 88.0)]
    assert dedupe(servings) == [Serving("cup", 91.0), Serving("slice", 20.0)]
