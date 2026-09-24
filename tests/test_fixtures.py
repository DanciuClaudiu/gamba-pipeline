import sqlite3

from gamba_pipeline import fixtures


def count(path, table):
    with sqlite3.connect(path) as db:
        return db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_builds_the_app_test_databases(tmp_path):
    written = fixtures.build(tmp_path)
    assert [path.relative_to(tmp_path).as_posix() for path in written] == [
        "reference.sqlite",
        "food-ro/pack.sqlite",
        "food-us/pack.sqlite",
    ]
    assert count(written[0], "food") == 7
    assert count(written[1], "product") == 4
    assert count(written[2], "product") == 6


def test_the_same_fixtures_give_the_same_files(tmp_path):
    first = [path.read_bytes() for path in fixtures.build(tmp_path / "a")]
    assert first == [path.read_bytes() for path in fixtures.build(tmp_path / "b")]
