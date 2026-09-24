"""Command line: `uv run gamba-pipeline <command>`. A full build runs download, reference, packs,
package, survey, spotcheck and report, in that order."""

import argparse
import json
from datetime import date
from pathlib import Path

from gamba_pipeline import (
    branded,
    fixtures,
    inputs,
    off,
    package,
    packs,
    reference,
    report,
    spotcheck,
    survey,
)
from gamba_pipeline.countries import COUNTRIES

ROOT = Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamba-pipeline", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download", help="download and verify every pinned input")
    build_reference = commands.add_parser("reference", help="build build/reference.sqlite")
    build_reference.add_argument("--build-date", default=date.today().isoformat())
    build_packs = commands.add_parser("packs", help="build build/packs/food-<country>/pack.sqlite")
    build_packs.add_argument("--countries", default=",".join(COUNTRIES))
    build_packs.add_argument("--build-date", default=date.today().isoformat())
    commands.add_parser("package", help="build build/packages/food-<country>.aar with ba-package")
    commands.add_parser("survey", help="count each country's pack products (build/survey.json)")
    check = commands.add_parser("spotcheck", help="check the packs against spotchecks/*.json")
    check.add_argument(
        "--refresh", action="store_true", help="choose the products and read their values again"
    )
    make_fixtures = commands.add_parser(
        "fixtures", help="build small test databases for the app's FoodDatabase tests"
    )
    make_fixtures.add_argument("output", type=Path)
    build_report = commands.add_parser("report", help="write build/REPORT.md")
    build_report.add_argument("--build-date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    if args.command == "fixtures":
        for path in fixtures.build(args.output):
            print(path)
        return 0

    pinned = inputs.load(ROOT / "inputs.toml")
    downloads = ROOT / "build" / "inputs"
    match args.command:
        case "download":
            for item in pinned.values():
                print(f"{item.name}: {inputs.fetch(item, downloads)}")
            return 0
        case "reference":
            return _reference(args.build_date, pinned, downloads)
        case "packs":
            return _packs(args.countries.split(","), args.build_date, pinned, downloads)
        case "package":
            return _package()
        case "survey":
            counts = survey.count_products(inputs.fetch(pinned["off"], downloads))
            path = ROOT / "build" / "survey.json"
            path.write_text(json.dumps(counts, indent=1) + "\n", encoding="utf-8")
            print(f"{path}: {len(counts)} country tags")
            return 0
        case "spotcheck":
            return _spotcheck(args.refresh, pinned, downloads)
        case _:
            path = report.write(ROOT / "build", args.build_date, pinned)
            print(path)
            return 0


def _reference(build_date: str, pinned: dict[str, inputs.Input], downloads: Path) -> int:
    output = ROOT / "build" / "reference.sqlite"
    result = reference.build(
        foundation_dir=inputs.unzip(
            inputs.fetch(pinned["foundation"], downloads), downloads / "foundation"
        ),
        sr_legacy_dir=inputs.unzip(
            inputs.fetch(pinned["sr_legacy"], downloads), downloads / "sr_legacy"
        ),
        exercises_json=inputs.fetch(pinned["exercises"], downloads),
        overrides_json=ROOT / "overrides" / "exercise_overrides.json",
        output=output,
        meta={
            "buildDate": build_date,
            "usdaFoundation": pinned["foundation"].release,
            "usdaSrLegacy": pinned["sr_legacy"].release,
            "freeExerciseDb": pinned["exercises"].release,
        },
    )
    reference.write_report(result, ROOT / "build" / "reference.report.json")
    print(f"{output}: {result.foods} foods, {result.exercises} exercises")
    print(f"size {result.size_bytes / 1_000_000:.1f} MB")
    print(
        f"rejected {len(result.rejected)}, duplicate names {len(result.duplicates)}, "
        f"flagged {len(result.flagged)}, adjusted {len(result.adjusted)}"
    )
    return 0


def _packs(
    codes: list[str], build_date: str, pinned: dict[str, inputs.Input], downloads: Path
) -> int:
    unknown = sorted(set(codes) - set(COUNTRIES))
    if unknown:
        raise SystemExit(f"no pack rules for {unknown}; known: {sorted(COUNTRIES)}")
    parquet = inputs.fetch(pinned["off"], downloads)
    for code in codes:
        country = COUNTRIES[code]
        result = packs.PackReport(code)
        meta = {"buildDate": build_date, "offExport": pinned["off"].release}
        usda_products = None
        if country.usda_branded:
            folder = inputs.unzip(inputs.fetch(pinned["branded"], downloads), downloads / "branded")
            usda_products = list(branded.read_products(folder, result.stats).values())
            meta["usdaBranded"] = pinned["branded"].release
        off_products = off.read_products(parquet, country, result.stats)
        output = ROOT / "build" / "packs" / country.pack_id / "pack.sqlite"
        packs.build(country, off_products, usda_products, output, meta, result)
        packs.write_report(result, ROOT / "build" / "packs" / f"{country.pack_id}.report.json")
        size = result.size_bytes / 1_000_000
        print(
            f"{country.pack_id}: {result.products} products, {size:.1f} MB, "
            f"rejected {len(result.rejected)}, flagged {len(result.flagged)}"
        )
    return 0


def _package() -> int:
    packs_dir = ROOT / "build" / "packs"
    for pack in sorted(path.parent.name for path in packs_dir.glob("food-*/pack.sqlite")):
        archive = package.package(packs_dir, pack, ROOT / "build" / "packages")
        print(f"{archive}: {archive.stat().st_size / 1_000_000:.1f} MB")
    return 0


def _spotcheck(refresh: bool, pinned: dict[str, inputs.Input], downloads: Path) -> int:
    results = {}
    for code, country in COUNTRIES.items():
        pack = ROOT / "build" / "packs" / country.pack_id / "pack.sqlite"
        checks_path = ROOT / "spotchecks" / f"{code}.json"
        if refresh:
            branded_dir = None
            if country.usda_branded:
                branded_zip = inputs.fetch(pinned["branded"], downloads)
                branded_dir = inputs.unzip(branded_zip, downloads / "branded")
            parquet = inputs.fetch(pinned["off"], downloads)
            spotcheck.save(checks_path, spotcheck.refresh(pack, country, parquet, branded_dir))
        checked = spotcheck.run(pack, spotcheck.load(checks_path))
        results[country.pack_id] = [spotcheck.as_json(result) for result in checked]
        passed = sum(result.passed for result in checked)
        print(f"{country.pack_id}: {passed} of {len(checked)} passed")
        for result in checked:
            if not result.passed:
                print(f"  {result.check.gtin14} {result.check.name}: {result.mismatches}")
    path = ROOT / "build" / "spotchecks.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0 if all(item["passed"] for items in results.values() for item in items) else 1
