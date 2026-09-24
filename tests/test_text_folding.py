import json
import os
import sqlite3
from pathlib import Path

import pytest

from gamba_pipeline.sqlite_writer import FTS_OPTIONS

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared" / "text_folding.json"
APP_COPY = Path("Packages/GambaKit/Tests/GambaCoreTests/Vectors/text_folding.json")
VECTORS = json.loads(SHARED.read_text(encoding="utf-8"))["vectors"]


@pytest.fixture(scope="module")
def tokenizer():
    db = sqlite3.connect(":memory:")
    db.execute(f"CREATE VIRTUAL TABLE t USING fts5(x, {FTS_OPTIONS})")
    db.execute("CREATE VIRTUAL TABLE v USING fts5vocab(t, 'instance')")
    yield db
    db.close()


@pytest.mark.parametrize("index", range(len(VECTORS)), ids=[v["input"] for v in VECTORS])
def test_the_index_folds_the_shared_vectors(tokenizer, index):
    vector = VECTORS[index]
    tokenizer.execute("INSERT INTO t (rowid, x) VALUES (?, ?)", (index + 1, vector["input"]))
    tokens = [
        term
        for (term,) in tokenizer.execute(
            "SELECT term FROM v WHERE doc = ? ORDER BY offset", (index + 1,)
        )
    ]
    assert tokens == vector["tokens"]


def test_the_vectors_match_the_app_repository():
    app_repo = Path(os.environ.get("GAMBA_APP_REPO", ROOT.parent / "Gamba"))
    app_vectors = app_repo / APP_COPY
    if not app_vectors.exists():
        pytest.skip(f"no app repository at {app_repo}; set GAMBA_APP_REPO")
    assert SHARED.read_bytes() == app_vectors.read_bytes(), "copy the app's text_folding.json here"
