"""Command line: `uv run gamba-pipeline <command>`."""

import argparse
from pathlib import Path

from gamba_pipeline import inputs

ROOT = Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gamba-pipeline", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download", help="download and verify every pinned input")
    args = parser.parse_args(argv)

    pinned = inputs.load(ROOT / "inputs.toml")
    downloads = ROOT / "build" / "inputs"
    if args.command == "download":
        for item in pinned.values():
            print(f"{item.name}: {inputs.fetch(item, downloads)}")
    return 0
