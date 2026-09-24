import hashlib
import zipfile
from pathlib import Path

import pytest

from gamba_pipeline import inputs

ROOT = Path(__file__).resolve().parents[1]


def pinned(tmp_path: Path, content: bytes, sha256: str | None = None) -> inputs.Input:
    source = tmp_path / "source.bin"
    source.write_bytes(content)
    return inputs.Input(
        name="demo",
        url=source.as_uri(),
        release="1",
        sha256=sha256 or hashlib.sha256(content).hexdigest(),
        file="demo.bin",
    )


def test_every_pinned_input_has_a_checksum():
    pins = inputs.load(ROOT / "inputs.toml")
    assert set(pins) == {"foundation", "sr_legacy", "exercises"}
    for item in pins.values():
        assert len(item.sha256) == 64
        assert item.url.startswith("https://")


def test_fetch_downloads_and_verifies(tmp_path):
    path = inputs.fetch(pinned(tmp_path, b"gamba"), tmp_path / "downloads")
    assert path.read_bytes() == b"gamba"
    assert inputs.sha256_of(path) == hashlib.sha256(b"gamba").hexdigest()


def test_fetch_reuses_a_verified_copy(tmp_path):
    item = pinned(tmp_path, b"gamba")
    first = inputs.fetch(item, tmp_path / "downloads")
    (tmp_path / "source.bin").unlink()  # a second download would now fail
    assert inputs.fetch(item, tmp_path / "downloads") == first


def test_fetch_stops_on_a_checksum_mismatch(tmp_path):
    with pytest.raises(inputs.ChecksumMismatch):
        inputs.fetch(pinned(tmp_path, b"gamba", sha256="0" * 64), tmp_path / "downloads")


def test_unzip_returns_the_folder_with_the_csv_files(tmp_path):
    archive = tmp_path / "data.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("Release_2026/food.csv", "fdc_id\n")
    folder = inputs.unzip(archive, tmp_path / "data")
    assert (folder / "food.csv").exists()
    assert folder.name == "Release_2026"
