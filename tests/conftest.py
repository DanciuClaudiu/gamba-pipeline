from pathlib import Path

import pytest

from gamba_pipeline import fixtures


@pytest.fixture(scope="session")
def off_parquet(tmp_path_factory) -> Path:
    """tests/fixtures/off/products.json as Parquet, typed like the Open Food Facts export."""
    path = tmp_path_factory.mktemp("off") / "food.parquet"
    return fixtures.off_parquet(fixtures.FIXTURES / "off" / "products.json", path)
