import pytest

from gamba_pipeline.servings import Serving, dedupe, label_serving, usda_serving


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


@pytest.mark.parametrize(
    ("text", "amount", "serving"),
    [
        ("1 pot (150 g)", 150.0, Serving("1 pot", 150.0)),
        ("0.5 cup (64 g)", 64.0, Serving("0.5 cup", 64.0)),
        ("half a can (207g)", 207.0, Serving("half a can", 207.0)),
        ("2 FRIED LINKS", 40.0, Serving("2 FRIED LINKS", 40.0)),
        ("30 g", 30.0, Serving("serving", 30.0)),
        ("250ml", 250.0, Serving("serving", 250.0)),
        ("112.00000000000001g", 112.00000000000001, Serving("serving", 112.0)),
        ("1 ONZ", 28.0, Serving("serving", 28.0)),  # USDA's code for ounce
        ("8 OZA", 240.0, Serving("serving", 240.0)),  # and for fluid ounce
        ("Amount per serving", 240.0, Serving("serving", 240.0)),
        (None, 45.0, Serving("serving", 45.0)),
    ],
)
def test_label_servings(text, amount, serving):
    assert label_serving(text, amount) == serving


def test_a_label_serving_needs_an_amount():
    assert label_serving("1 pot (150 g)", None) is None
    assert label_serving("1 pot (150 g)", 0.0) is None
