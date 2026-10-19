"""Pinned inputs (inputs.toml): downloaded once, verified by SHA-256, unzipped once. The monthly
run moves the Open Food Facts pin to the newest export (`latest_off`); the others move by hand."""

import hashlib
import json
import tomllib
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Any

HEADER = "# Every input is pinned by release and SHA-256; a mismatch stops the build."
OFF_DATASET = "openfoodfacts/product-database"
OFF_FILE = "food.parquet"


class ChecksumMismatch(Exception):
    """A downloaded file doesn't match its pinned SHA-256."""


@dataclass(frozen=True)
class Input:
    name: str
    url: str
    release: str
    sha256: str
    file: str


def load(path: Path) -> dict[str, Input]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return {name: Input(name=name, **fields) for name, fields in data.items()}


def save(path: Path, pins: dict[str, Input]) -> None:
    """Writes `pins` in inputs.toml's layout: the header, then one section per input."""
    lines = [HEADER]
    for name, item in pins.items():
        lines += ["", f"[{name}]"]
        lines += [f'{field.name} = "{getattr(item, field.name)}"' for field in fields(Input)[1:]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def latest_off(current: Input, get_json: Callable[[str], Any] = _get_json) -> Input:
    """The pin of the Open Food Facts export at the dataset's newest revision on Hugging Face.
    Hugging Face's LFS object ID for a file is its SHA-256."""
    api = f"https://huggingface.co/api/datasets/{OFF_DATASET}"
    revision = get_json(api)["sha"]
    for entry in get_json(f"{api}/tree/{revision}"):
        if entry["path"] == OFF_FILE:
            return replace(
                current,
                url=f"https://huggingface.co/datasets/{OFF_DATASET}/resolve/{revision}/{OFF_FILE}",
                release=revision,
                sha256=entry["lfs"]["oid"],
            )
    raise FileNotFoundError(f"no {OFF_FILE} in {OFF_DATASET} at {revision}")


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(item: Input, directory: Path) -> Path:
    """The verified local copy of `item`, downloading it first if needed."""
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / item.file
    if not target.exists() or sha256_of(target) != item.sha256:
        partial = target.with_name(target.name + ".partial")
        urllib.request.urlretrieve(item.url, partial)
        partial.replace(target)
    actual = sha256_of(target)
    if actual != item.sha256:
        raise ChecksumMismatch(f"{item.name}: expected {item.sha256}, got {actual}")
    return target


def unzip(archive: Path, destination: Path) -> Path:
    """Extracts `archive` once and returns the folder that holds `food.csv`."""
    if not destination.exists():
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(destination)
    folders = sorted({path.parent for path in destination.rglob("food.csv")})
    if len(folders) != 1:
        raise FileNotFoundError(f"expected one food.csv under {destination}, found {len(folders)}")
    return folders[0]
