import re

from gamba_pipeline.countries import COUNTRIES, THRESHOLD


def test_every_country_over_the_threshold():
    assert len(COUNTRIES) == 44
    assert THRESHOLD == 5_000
    assert all(re.fullmatch(r"[a-z]{2}", code) for code in COUNTRIES)
    assert len({country.off_tag for country in COUNTRIES.values()}) == 44


def test_the_m2_countries_and_their_name_languages():
    assert {code: COUNTRIES[code].name_languages for code in ("gb", "ro", "us")} == {
        "gb": ("en",),
        "ro": ("ro", "en"),
        "us": ("en",),
    }


def test_countries_with_several_languages():
    several = {
        code: country.name_languages
        for code, country in COUNTRIES.items()
        if len(country.name_languages) > 2
    }
    assert several == {
        "be": ("nl", "fr", "de", "en"),
        "ch": ("de", "fr", "it", "en"),
        "fi": ("fi", "sv", "en"),
        "lu": ("lb", "fr", "de", "en"),
        "sg": ("en", "zh", "ms"),
    }
    assert COUNTRIES["ca"].name_languages == ("en", "fr")
    assert COUNTRIES["no"].name_languages == ("nb", "en")


def test_pack_ids_and_open_food_facts_tags():
    assert COUNTRIES["ro"].pack_id == "food-ro"
    assert COUNTRIES["in"].pack_id == "food-in"
    assert COUNTRIES["gb"].off_tag == "en:united-kingdom"
    assert COUNTRIES["us"].off_tag == "en:united-states"
    assert COUNTRIES["cz"].off_tag == "en:czech-republic"
    assert [code for code, country in COUNTRIES.items() if country.usda_branded] == ["us"]
