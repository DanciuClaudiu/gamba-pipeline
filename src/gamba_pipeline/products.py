"""A pack product (SPEC §3.10) and the rules that shape it: base unit, the US merge of Open Food
Facts with USDA Branded, and the name fallback."""

import re
from dataclasses import dataclass, field, replace

from gamba_pipeline import nutrients as nutrient_rules
from gamba_pipeline.nutrients import Nutrients
from gamba_pipeline.servings import Serving

VOLUME = re.compile(r"\d\s*(?:ml|cl|dl|l|fl\.?\s?oz)\b", re.IGNORECASE)


@dataclass(frozen=True)
class PackProduct:
    gtin14: str
    name: str | None  # the main name; None until `finalize` falls back to the brand
    brand: str | None
    quantity: str | None  # as printed on the package ("500 g")
    base_unit: str  # "g" or "ml"; the nutrients are per 100 of it
    nutrients: Nutrients
    serving: Serving | None
    source: str  # "off" or "usda": where the nutrients came from
    source_ref: str  # the GTIN for Open Food Facts, the FDC ID for USDA
    last_modified: str | None  # YYYY-MM-DD
    names: dict[str, str] = field(default_factory=dict)  # by language, when different from `name`

    @property
    def is_complete(self) -> bool:
        """Energy, protein, carbs and fat all present (SPEC §3.6)."""
        n = self.nutrients
        return None not in (n.kcal, n.protein_g, n.carbs_g, n.fat_g)


def base_unit(quantity_unit: str | None, quantity: str | None) -> str:
    """ml for products sold by volume, otherwise g. Open Food Facts' own unit wins; without one,
    the printed quantity decides ("330 ml", "2 l", "12 fl oz")."""
    if quantity_unit in ("g", "ml"):
        return quantity_unit
    return "ml" if quantity and VOLUME.search(quantity) else "g"


def merge(off: PackProduct | None, usda: PackProduct | None) -> PackProduct:
    """The US pack's record for one GTIN (SPEC §10 step 3, Claudiu 24 September 2026): nutrients,
    base unit and serving from the record with more nutrients, Open Food Facts on a tie; names and
    brand from Open Food Facts whenever it has them."""
    if off is None or usda is None:
        result = off or usda
        assert result is not None
        return result
    winner = (
        usda if nutrient_rules.count(usda.nutrients) > nutrient_rules.count(off.nutrients) else off
    )
    return replace(
        winner,
        name=off.name or usda.name,
        names=off.names if off.name else usda.names,
        brand=off.brand or usda.brand,
        quantity=off.quantity or usda.quantity,
    )


def finalize(product: PackProduct) -> PackProduct | None:
    """A product without a name is named by its brand, and left out without either (Claudiu,
    24 September 2026)."""
    if product.name:
        return product
    if product.brand:
        return replace(product, name=product.brand)
    return None
