import gzip
from pathlib import Path

from gamba_pipeline import inputs, release

ROOT = Path(__file__).resolve().parents[1]


def one_pack(build: Path) -> Path:
    pack = build / "packs" / "food-ro" / "pack.sqlite"
    pack.parent.mkdir(parents=True)
    pack.write_bytes(b"SQLite format 3\0" * 100)
    return pack


def test_release_gzips_each_pack_reproducibly(tmp_path):
    pack = one_pack(tmp_path)
    pinned = inputs.load(ROOT / "inputs.toml")
    first = release.write(tmp_path, "2026-11-01", pinned)
    copy = (tmp_path / "release" / "food-ro.sqlite.gz").read_bytes()
    release.write(tmp_path, "2026-11-01", pinned)
    assert [path.name for path in first] == ["food-ro.sqlite.gz", "NOTES.md"]
    assert gzip.decompress(copy) == pack.read_bytes()
    assert (tmp_path / "release" / "food-ro.sqlite.gz").read_bytes() == copy


def test_release_notes_credit_open_food_facts(tmp_path):
    one_pack(tmp_path)
    release.write(tmp_path, "2026-11-01", inputs.load(ROOT / "inputs.toml"))
    notes = (tmp_path / "release" / "NOTES.md").read_text(encoding="utf-8")
    assert "built 2026-11-01 from Open Food Facts export `3dc10b5`" in notes
    assert "Branded Foods 2026-04-30: 1 pack." in notes
    assert "© Open Food Facts contributors" in notes and "odbl/1-0" in notes
    assert "dbcl/1-0" in notes and "https://fdc.nal.usda.gov" in notes
