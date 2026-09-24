"""The countries that get a pack (SPEC §3.10). M2 builds three; M9 adds every country with enough
products."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Country:
    code: str  # ISO 3166-1 alpha-2, lowercase; the pack is food-<code>
    off_tag: str  # the Open Food Facts countries_tags entry
    languages: tuple[str, ...]  # official languages (Q34)
    usda_branded: bool = False  # merge USDA Branded Foods (SPEC §10 step 3)

    @property
    def pack_id(self) -> str:
        return f"food-{self.code}"

    @property
    def name_languages(self) -> tuple[str, ...]:
        """The official languages plus English, each once (Q34)."""
        return tuple(dict.fromkeys((*self.languages, "en")))


COUNTRIES = {
    country.code: country
    for country in (
        # Welsh and Scottish Gaelic names are too rare to index (44 and 11 of 194,241 products).
        Country("gb", "en:united-kingdom", ("en",)),
        Country("ro", "en:romania", ("ro",)),
        Country("us", "en:united-states", ("en",), usda_branded=True),
    )
}
