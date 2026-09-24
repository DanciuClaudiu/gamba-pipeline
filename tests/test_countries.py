from gamba_pipeline.countries import COUNTRIES


def test_the_m2_countries_and_their_name_languages():
    assert {code: country.name_languages for code, country in COUNTRIES.items()} == {
        "gb": ("en",),
        "ro": ("ro", "en"),
        "us": ("en",),
    }


def test_pack_ids_and_open_food_facts_tags():
    assert COUNTRIES["ro"].pack_id == "food-ro"
    assert COUNTRIES["gb"].off_tag == "en:united-kingdom"
    assert COUNTRIES["us"].off_tag == "en:united-states"
    assert [code for code, country in COUNTRIES.items() if country.usda_branded] == ["us"]
