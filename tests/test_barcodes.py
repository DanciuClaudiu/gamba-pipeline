import json
import os
from pathlib import Path

import pytest

from gamba_pipeline import barcodes

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared" / "barcodes.json"
APP_COPY = Path("Packages/GambaKit/Tests/GambaCoreTests/Vectors/barcodes.json")
VECTORS = json.loads(SHARED.read_text(encoding="utf-8"))["vectors"]


@pytest.mark.parametrize(
    "vector", VECTORS, ids=lambda v: f"{v['input']!r} as {v['symbology'] or 'typed'}"
)
def test_normalizes_the_shared_vectors(vector):
    assert barcodes.normalize(vector["input"], vector["symbology"]) == vector["gtin14"]


def test_the_vectors_match_the_app_repository():
    app_repo = Path(os.environ.get("GAMBA_APP_REPO", ROOT.parent / "Gamba"))
    app_vectors = app_repo / APP_COPY
    if not app_vectors.exists():
        pytest.skip(f"no app repository at {app_repo}; set GAMBA_APP_REPO")
    assert SHARED.read_bytes() == app_vectors.read_bytes(), "copy the app's barcodes.json here"


def test_check_digits_and_upc_e():
    assert barcodes.check_digit("400638133393") == 1
    assert barcodes.check_digit("9638507") == 4
    assert barcodes.expand_upce("04252614") == "042100005264"
    assert barcodes.expand_upce("04252615") is None
