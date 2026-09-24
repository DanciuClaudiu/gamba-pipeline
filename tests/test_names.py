from gamba_pipeline.names import clean, first_brand, pick


def test_keeps_the_country_languages_that_differ_from_the_main_name():
    names = {
        "main": "Coca-Cola",
        "en": "Coca-Cola",
        "ro": "Coca-Cola Original",
        "de": "Coca-Cola Classic",
    }
    assert pick(names, "en", ("ro", "en")) == ("Coca-Cola", {"ro": "Coca-Cola Original"})


def test_the_main_name_falls_back_to_the_product_language_then_the_country_languages():
    assert pick({"en": "Beanz", "fr": "Haricots"}, "en", ("en",)) == ("Beanz", {})
    assert pick({"fr": "Haricots", "ro": "Fasole"}, "de", ("ro", "en")) == ("Fasole", {})
    assert pick({"fr": "Haricots"}, None, ("en",)) == ("Haricots", {})


def test_blank_names_are_missing():
    assert pick({"main": "  ", "en": ""}, "en", ("en",)) == (None, {})


def test_collapses_whitespace():
    assert clean("  Brânză   de vaci\n") == "Brânză de vaci"
    assert clean(" ") is None
    assert clean(None) is None


def test_first_brand():
    assert first_brand("Coca-Cola, The Coca-Cola Company") == "Coca-Cola"
    assert first_brand("Wal-Mart Stores,  Progressive Balloons  Inc.") == "Wal-Mart Stores"
    assert first_brand(" , Heinz") == "Heinz"
    assert first_brand(None) is None
