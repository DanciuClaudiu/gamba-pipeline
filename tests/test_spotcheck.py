from collections import Counter
from dataclasses import replace
from pathlib import Path

from gamba_pipeline import branded, off, packs, spotcheck
from gamba_pipeline.countries import COUNTRIES
from gamba_pipeline.spotcheck import close, match_query

BRANDED = Path(__file__).parent / "fixtures" / "usda" / "branded"
CHEDDAR = {
    "kcal": 402.0, "proteinG": 25.0, "carbsG": 1.8, "sugarsG": 0.5, "fatG": 33.0,
    "satFatG": 19.0, "fiberG": 0.0, "sodiumMg": 620.0,
}  # fmt: skip


def build_pack(off_parquet, tmp_path, code) -> Path:
    country = COUNTRIES[code]
    usda = None
    if country.usda_branded:
        usda = list(branded.read_products(BRANDED, Counter()).values())
    output = tmp_path / country.pack_id / "pack.sqlite"
    off_products = off.read_products(off_parquet, country, Counter())
    meta = {"buildDate": "2026-09-24"}
    packs.build(country, off_products, usda, output, meta, packs.PackReport(code))
    return output


def test_match_query_makes_every_word_a_prefix():
    assert match_query("coca cola") == '"coca"* "cola"*'
    assert match_query('lapte "zuzu" & 1,5%') == '"lapte"* "zuzu"* "1,5%"*'


def test_close():
    assert close(97.992, 97.992)
    assert close(620.4, 620.0)  # within 0.01 + 0.1%
    assert not close(621.0, 620.0)
    assert close(None, None)
    assert not close(0.0, None)


def test_refresh_picks_the_country_s_most_scanned_products_in_the_pack(off_parquet, tmp_path):
    pack = build_pack(off_parquet, tmp_path, "ro")
    checks = spotcheck.refresh(pack, COUNTRIES["ro"], off_parquet, None)
    # The impossible bar is top 10 but not in the pack; the wine's tier is from 2024.
    assert [(check.gtin14, check.query) for check in checks] == [
        ("05940000000011", "brânză de vaci"),
        ("05449000000996", "coca cola"),
        ("05940000000028", "napolact"),
    ]
    assert checks[0].expected == {
        "kcal": 97.992, "proteinG": 12.5, "carbsG": 3.4, "sugarsG": None, "fatG": 5.0,
        "satFatG": None, "fiberG": None, "sodiumMg": 100.0,
    }  # fmt: skip


def test_refresh_reads_usda_values_for_usda_records(off_parquet, tmp_path):
    pack = build_pack(off_parquet, tmp_path, "us")
    checks = spotcheck.refresh(pack, COUNTRIES["us"], off_parquet, BRANDED)
    assert [(check.gtin14, check.source, check.source_ref) for check in checks] == [
        ("05449000000996", "off", "5449000000996"),
        ("00036000291452", "usda", "1001"),
        ("00041000000034", "usda", "1008"),
    ]
    assert checks[1].expected == CHEDDAR


def test_run_checks_the_barcode_the_name_and_every_value(off_parquet, tmp_path):
    pack = build_pack(off_parquet, tmp_path, "ro")
    checks = spotcheck.refresh(pack, COUNTRIES["ro"], off_parquet, None)
    assert all(result.passed for result in spotcheck.run(pack, checks))
    wrong = replace(checks[0], expected={**checks[0].expected, "kcal": 120.0})
    missing = replace(checks[1], gtin14="00000000000000")
    unfindable = replace(checks[2], query="nothing like it")
    results = spotcheck.run(pack, [wrong, missing, unfindable])
    assert results[0].mismatches == ("kcal 97.992 ≠ 120.0",)
    assert not results[1].by_barcode
    assert results[2].name_rank is None
    assert not any(result.passed for result in results)


def test_saves_and_loads_checks(off_parquet, tmp_path):
    pack = build_pack(off_parquet, tmp_path, "ro")
    checks = spotcheck.refresh(pack, COUNTRIES["ro"], off_parquet, None)
    spotcheck.save(tmp_path / "ro.json", checks)
    assert spotcheck.load(tmp_path / "ro.json") == checks
