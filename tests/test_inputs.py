import hashlib
import zipfile
from dataclasses import replace
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
    assert set(pins) == {"foundation", "sr_legacy", "exercises", "off", "branded"}
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


def test_save_writes_inputs_toml_as_it_is(tmp_path):
    original = (ROOT / "inputs.toml").read_text(encoding="utf-8")
    inputs.save(tmp_path / "inputs.toml", inputs.load(ROOT / "inputs.toml"))
    assert (tmp_path / "inputs.toml").read_text(encoding="utf-8") == original


def test_latest_off_pins_the_newest_revision():
    api = "https://huggingface.co/api/datasets/openfoodfacts/product-database"
    responses = {
        api: {"sha": "e7f6e1c9"},
        f"{api}/tree/e7f6e1c9": [
            {"path": "beauty.parquet", "lfs": {"oid": "a" * 64}},
            {"path": "food.parquet", "lfs": {"oid": "b" * 64}},
        ],
    }
    current = inputs.load(ROOT / "inputs.toml")["off"]
    assert inputs.latest_off(current, responses.__getitem__) == replace(
        current,
        url="https://huggingface.co/datasets/openfoodfacts/product-database/resolve/e7f6e1c9/food.parquet",
        release="e7f6e1c9",
        sha256="b" * 64,
    )


def test_latest_off_needs_food_parquet():
    api = "https://huggingface.co/api/datasets/openfoodfacts/product-database"
    responses = {api: {"sha": "e7f6e1c9"}, f"{api}/tree/e7f6e1c9": []}
    current = inputs.load(ROOT / "inputs.toml")["off"]
    with pytest.raises(FileNotFoundError, match="e7f6e1c9"):
        inputs.latest_off(current, responses.__getitem__)


def test_pin_latest_saves_the_new_pin(tmp_path, monkeypatch, capsys):
    from gamba_pipeline import cli

    (tmp_path / "inputs.toml").write_bytes((ROOT / "inputs.toml").read_bytes())
    pins = inputs.load(ROOT / "inputs.toml")
    newer = replace(pins["off"], release="e7f6e1c9" + "0" * 32, sha256="b" * 64)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(inputs, "latest_off", lambda current: newer)
    assert cli.main(["pin-latest"]) == 0
    assert inputs.load(tmp_path / "inputs.toml") == {**pins, "off": newer}
    assert capsys.readouterr().out == "off: 3dc10b5 → e7f6e1c\n"
    assert cli.main(["pin-latest"]) == 0
    assert capsys.readouterr().out == "off: e7f6e1c (unchanged)\n"
