"""Pinned inputs (inputs.toml): downloaded once, verified by SHA-256, unzipped once."""

import hashlib
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path


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
