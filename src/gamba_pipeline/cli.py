"""Command line: `uv run gamba-pipeline <command>`."""

import argparse
from datetime import date
from pathlib import Path

from gamba_pipeline import branded, inputs, off, packs, reference
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
    args = parser.parse_args(argv)

    pinned = inputs.load(ROOT / "inputs.toml")
    downloads = ROOT / "build" / "inputs"
    if args.command == "download":
        for item in pinned.values():
            print(f"{item.name}: {inputs.fetch(item, downloads)}")
        return 0
    if args.command == "packs":
        return _packs(args.countries.split(","), args.build_date, pinned, downloads)
    return _reference(args.build_date, pinned, downloads)


def _reference(build_date: str, pinned: dict[str, inputs.Input], downloads: Path) -> int:
    output = ROOT / "build" / "reference.sqlite"
    report = reference.build(
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
    print(f"{output}: {report.foods} foods, {report.exercises} exercises")
    print(f"size {report.size_bytes / 1_000_000:.1f} MB")
    print(
        f"rejected {len(report.rejected)}, duplicate names {len(report.duplicates)}, "
        f"flagged {len(report.flagged)}, adjusted {len(report.adjusted)}"
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
        report = packs.PackReport(code)
        meta = {"buildDate": build_date, "offExport": pinned["off"].release}
        usda_products = None
        if country.usda_branded:
            folder = inputs.unzip(inputs.fetch(pinned["branded"], downloads), downloads / "branded")
            usda_products = list(branded.read_products(folder, report.stats).values())
            meta["usdaBranded"] = pinned["branded"].release
        off_products = off.read_products(parquet, country, report.stats)
        output = ROOT / "build" / "packs" / country.pack_id / "pack.sqlite"
        packs.build(country, off_products, usda_products, output, meta, report)
        packs.write_report(report, ROOT / "build" / "packs" / f"{country.pack_id}.report.json")
        size = report.size_bytes / 1_000_000
        print(
            f"{country.pack_id}: {report.products} products, {size:.1f} MB, "
            f"rejected {len(report.rejected)}, flagged {len(report.flagged)}"
        )
    return 0
