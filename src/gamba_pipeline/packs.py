"""Builds one country's pack (SPEC §3.10, §10 steps 3–4)."""

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from gamba_pipeline import pack_writer, validate
from gamba_pipeline.countries import Country
from gamba_pipeline.products import PackProduct, finalize, merge

# Open Food Facts requires derived databases to stay under ODbL, with its contents under DbCL.
PACK_LICENSE = "ODbL-1.0; contents DbCL-1.0"
OFF_ATTRIBUTION = "Open Food Facts contributors, https://world.openfoodfacts.org"
USDA_ATTRIBUTION = "USDA FoodData Central, https://fdc.nal.usda.gov"


@dataclass
class PackReport:
    country: str
    stats: Counter = field(default_factory=Counter)
    rejected: list[tuple[str, str, str]] = field(default_factory=list)  # (source, ref, reason)
    flagged: list[tuple[str, str, str]] = field(default_factory=list)  # (gtin14, name, reason)
    products: int = 0
    size_bytes: int = 0


def _valid(products: list[PackProduct], report: PackReport) -> dict[str, PackProduct]:
    """Each source is validated before the merge, so a bad record can't displace a good one."""
    valid = {}
    for product in products:
        verdict = validate.check(product.nutrients, label_values=True)
        if verdict.rejected:
            report.stats[f"{product.source} rejected"] += 1
            report.rejected.append((product.source, product.source_ref, verdict.rejected))
        else:
            valid[product.gtin14] = product
    return valid


def select(
    country: Country,
    off_products: list[PackProduct],
    usda_products: list[PackProduct] | None,
    report: PackReport,
) -> list[PackProduct]:
    off = _valid(off_products, report)
    usda = _valid(usda_products or [], report)
    kept = []
    for gtin14 in sorted(off.keys() | usda.keys()):
        in_off, in_usda = gtin14 in off, gtin14 in usda
        merged = merge(off.get(gtin14), usda.get(gtin14))
        if in_off and in_usda:
            report.stats["in both"] += 1
            if merged.source == "usda":
                report.stats["usda nutrients kept"] += 1
        elif in_usda:
            report.stats["usda only"] += 1
        product = finalize(merged)
        if product is None:
            report.stats["no name or brand"] += 1
            continue
        if not merged.name:
            report.stats["named by brand"] += 1
        verdict = validate.check(product.nutrients, label_values=True)
        if verdict.flagged:
            report.flagged.append((product.gtin14, product.name, verdict.flagged))
        kept.append(product)
    return kept


def build(
    country: Country,
    off_products: list[PackProduct],
    usda_products: list[PackProduct] | None,
    output: Path,
    meta: dict[str, str],
    report: PackReport,
) -> PackReport:
    products = select(country, off_products, usda_products, report)
    attribution = OFF_ATTRIBUTION
    if country.usda_branded:
        attribution += f"; {USDA_ATTRIBUTION}"
    pack_meta = {**meta, "country": country.code, "license": PACK_LICENSE}
    pack_writer.write(output, products, {**pack_meta, "attribution": attribution})
    report.products = len(products)
    report.size_bytes = output.stat().st_size
    return report


def write_report(report: PackReport, path: Path) -> None:
    """The build's counts and every rejected and flagged row, for build/REPORT.md (M2.3)."""
    data = {
        "country": report.country,
        "products": report.products,
        "sizeBytes": report.size_bytes,
        "stats": dict(sorted(report.stats.items())),
        "rejected": [
            {"source": source, "ref": ref, "reason": reason}
            for source, ref, reason in report.rejected
        ],
        "flagged": [
            {"gtin14": gtin14, "name": name, "reason": reason}
            for gtin14, name, reason in report.flagged
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
