"""Writes one country's pack.sqlite (SPEC §3.10, PLAN §2.13). The app opens it read-only and
ignores packs with an unknown major schema version."""

import sqlite3
from contextlib import closing
from pathlib import Path

from gamba_pipeline.products import PackProduct
from gamba_pipeline.sqlite_writer import FTS_OPTIONS

SCHEMA_VERSION = "1.0"

SCHEMA = f"""
CREATE TABLE meta (key TEXT PRIMARY KEY NOT NULL, value TEXT NOT NULL);

CREATE TABLE product (
    id INTEGER PRIMARY KEY NOT NULL,
    gtin14 TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    brand TEXT,
    quantity TEXT,
    baseUnit TEXT NOT NULL,
    kcal REAL NOT NULL,
    proteinG REAL,
    carbsG REAL,
    sugarsG REAL,
    fatG REAL,
    satFatG REAL,
    fiberG REAL,
    sodiumMg REAL,
    servingLabel TEXT,
    servingAmount REAL,
    isComplete INTEGER NOT NULL,
    source TEXT NOT NULL,
    sourceRef TEXT NOT NULL,
    lastModified TEXT
);

CREATE TABLE productName (
    productId INTEGER NOT NULL REFERENCES product (id),
    lang TEXT NOT NULL,
    name TEXT NOT NULL,
    PRIMARY KEY (productId, lang)
) WITHOUT ROWID;

CREATE VIRTUAL TABLE productFts USING fts5(names, brand, content = '', {FTS_OPTIONS});
"""


def write(path: Path, products: list[PackProduct], meta: dict[str, str]) -> None:
    """Writes a fresh pack at `path`. Products are numbered in GTIN order, so the same inputs give
    the same file; the search index row for a product has its `id` as rowid."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    ordered = sorted(products, key=lambda product: product.gtin14)
    with closing(sqlite3.connect(path)) as db:
        db.executescript(SCHEMA)
        db.executemany(
            "INSERT INTO meta (key, value) VALUES (?, ?)",
            [("schemaVersion", SCHEMA_VERSION), *sorted(meta.items())],
        )
        db.executemany(
            f"INSERT INTO product VALUES ({', '.join('?' * 20)})",
            [
                (
                    index,
                    p.gtin14,
                    p.name,
                    p.brand,
                    p.quantity,
                    p.base_unit,
                    p.nutrients.kcal,
                    p.nutrients.protein_g,
                    p.nutrients.carbs_g,
                    p.nutrients.sugars_g,
                    p.nutrients.fat_g,
                    p.nutrients.sat_fat_g,
                    p.nutrients.fiber_g,
                    p.nutrients.sodium_mg,
                    p.serving.label if p.serving else None,
                    p.serving.grams if p.serving else None,
                    int(p.is_complete),
                    p.source,
                    p.source_ref,
                    p.last_modified,
                )
                for index, p in enumerate(ordered, start=1)
            ],
        )
        db.executemany(
            "INSERT INTO productName VALUES (?, ?, ?)",
            [
                (index, lang, name)
                for index, p in enumerate(ordered, start=1)
                for lang, name in sorted(p.names.items())
            ],
        )
        db.executemany(
            "INSERT INTO productFts (rowid, names, brand) VALUES (?, ?, ?)",
            [
                (index, "\n".join([p.name, *sorted(set(p.names.values()))]), p.brand or "")
                for index, p in enumerate(ordered, start=1)
            ],
        )
        db.commit()
        db.execute("VACUUM")
