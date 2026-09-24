from gamba_pipeline.survey import count_products


def test_counts_pack_products_by_country(off_parquet):
    assert count_products(off_parquet) == {
        "en:romania": 5,
        "en:united-states": 5,
        "en:united-kingdom": 2,
    }
