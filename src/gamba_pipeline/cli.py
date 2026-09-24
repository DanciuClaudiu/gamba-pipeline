"""Command line: `uv run gamba-pipeline <command>`."""

import argparse
from datetime import date
from pathlib import Path

from gamba_pipeline import inputs, reference

ROOT = Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamba-pipeline", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download", help="download and verify every pinned input")
    build_reference = commands.add_parser("reference", help="build build/reference.sqlite")
    build_reference.add_argument("--build-date", default=date.today().isoformat())
    args = parser.parse_args(argv)

    pinned = inputs.load(ROOT / "inputs.toml")
    downloads = ROOT / "build" / "inputs"
    if args.command == "download":
        for item in pinned.values():
            print(f"{item.name}: {inputs.fetch(item, downloads)}")
        return 0

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
            "buildDate": args.build_date,
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
