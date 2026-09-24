from pathlib import Path

import duckdb
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
# The export's types for the columns the pipeline reads (the real file has 111 columns).
OFF_COLUMNS = {
    "code": "VARCHAR",
    "lang": "VARCHAR",
    "countries_tags": "VARCHAR[]",
    "product_name": 'STRUCT(lang VARCHAR, "text" VARCHAR)[]',
    "brands": "VARCHAR",
    "quantity": "VARCHAR",
    "product_quantity_unit": "VARCHAR",
    "serving_size": "VARCHAR",
    "serving_quantity": "VARCHAR",
    "last_modified_t": "BIGINT",
    "nutriments": 'STRUCT("name" VARCHAR, "100g" FLOAT)[]',
}


@pytest.fixture(scope="session")
def off_parquet(tmp_path_factory) -> Path:
    """tests/fixtures/off/products.json as Parquet, typed like the Open Food Facts export."""
    path = tmp_path_factory.mktemp("off") / "food.parquet"
    source = FIXTURES / "off" / "products.json"
    columns = ", ".join(f"'{name}': '{kind}'" for name, kind in OFF_COLUMNS.items())
    with duckdb.connect() as con:
        con.execute(
            f"COPY (SELECT * FROM read_json('{source}', format = 'array', "
            f"columns = {{{columns}}})) TO '{path}' (FORMAT parquet)"
        )
    return path
