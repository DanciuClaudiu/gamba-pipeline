import json
from pathlib import Path

import pytest

from gamba_pipeline import branded, inputs, off, packs, reference, report, spotcheck
from gamba_pipeline.countries import COUNTRIES
from gamba_pipeline.survey import count_products

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
BRANDED = FIXTURES / "usda" / "branded"


@pytest.fixture
def build(off_parquet, tmp_path) -> Path:
    """A build folder from the fixtures: reference, the RO and US packs, survey and spot checks."""
    build = tmp_path / "build"
    result = reference.build(
        foundation_dir=FIXTURES / "usda" / "foundation",
        sr_legacy_dir=FIXTURES / "usda" / "sr_legacy",
        exercises_json=FIXTURES / "exercises.json",
        overrides_json=FIXTURES / "overrides.json",
        output=build / "reference.sqlite",
        meta={"buildDate": "2026-09-24"},
    )
    reference.write_report(result, build / "reference.report.json")
    results = {}
    for code in ("ro", "us"):
        country = COUNTRIES[code]
        pack_report = packs.PackReport(code)
        usda = None
        if country.usda_branded:
            usda = list(branded.read_products(BRANDED, pack_report.stats).values())
        off_products = off.read_products(off_parquet, country, pack_report.stats)
        pack = build / "packs" / country.pack_id / "pack.sqlite"
        packs.build(country, off_products, usda, pack, {"buildDate": "2026-09-24"}, pack_report)
        packs.write_report(pack_report, build / "packs" / f"{country.pack_id}.report.json")
        checks = spotcheck.refresh(pack, country, off_parquet, BRANDED)
        results[country.pack_id] = [spotcheck.as_json(r) for r in spotcheck.run(pack, checks)]
    (build / "spotchecks.json").write_text(json.dumps(results), encoding="utf-8")
    (build / "survey.json").write_text(json.dumps(count_products(off_parquet)), encoding="utf-8")
    return build


def test_reason_groups():
    assert report.reason_group("energy 929 kcal over 905 kcal") == "energy over the limit"
    assert report.reason_group("protein + carbs + fat 120.0 g over 105 g") == (
        "protein + carbs + fat over 105 g"
    )
    assert report.reason_group("a negative value") == "a negative value"


def test_country_names():
    assert report.country_name("en:united-kingdom") == "United Kingdom"
    assert report.country_name("en:czech-republic") == "Czech Republic"


def test_writes_the_report(build):
    text = report.write(build, "2026-09-24", inputs.load(ROOT / "inputs.toml")).read_text()
    lines = text.splitlines()
    assert (
        "Built 2026-09-24 with `uv run gamba-pipeline` from the inputs pinned in `inputs.toml`."
        in lines
    )
    assert "| Foods | 7 (Foundation 4, SR Legacy 3) |" in lines
    assert "| Exercises | 6 (bodyweightReps 2, weightReps 2, assisted 1, duration 1) |" in lines
    assert any(line.startswith("| food-ro | 4 | 4 | ") and "not packaged" in line for line in lines)
    assert any(line.startswith("| food-us | 6 | 6 | ") for line in lines)
    assert "| food-ro | 9 | 1 | 1 | 1 |" in lines  # read, without energy, invalid, duplicate
    assert "| food-us | 12 | 1 | 1 | 1 |" in lines
    assert "| protein + carbs + fat over 105 g | 1 | 0 |" in lines
    assert "| food-us | 3 | 2 | 1 |" in lines  # in both, USDA nutrients kept, USDA only
    assert "| food-ro | 3 | 3 | 3 | 3 | 3 |" in lines  # spot checks
    assert "| 5,000 | 0 | 0 | 0.0 MB |" in lines


def test_writes_the_complete_lists(build):
    report.write(build, "2026-09-24", inputs.load(ROOT / "inputs.toml"))
    lists = build / "report"
    assert (lists / "food-ro-rejected.csv").read_text().splitlines() == [
        "source,ref,reason",
        "off,5940000000059,protein + carbs + fat 120.0 g over 105 g",
    ]
    assert (lists / "food-ro-flagged.csv").read_text().splitlines() == [
        "gtin14,name,reason",
        '05940000000066,Vin alb demisec,"energy 80 kcal, macros give 10 kcal"',
    ]
    assert len((lists / "reference-rejected.csv").read_text().splitlines()) == 3
