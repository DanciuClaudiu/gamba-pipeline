"""The countries that get a pack (SPEC §3.10): every country with at least `THRESHOLD` products in
the survey (Q5, recommended in M9.3). A country that crosses it later is listed by the report and
added here by hand, with its languages; a pack whose country falls under it stays."""

from dataclasses import dataclass

THRESHOLD = 5_000


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


# National official languages (Q34), without those in which fewer than 0.1% of the country's
# products have a name (export 3dc10b5): Irish (0.03%), Māori (0.01%), Romansh, Nynorsk (0.03%),
# Tamil, Tamazight, Welsh (0.03%), Scottish Gaelic (0.01%) and nine of South Africa's (Zulu 0.02%,
# the rest none). Regional languages (Catalan, Frisian) aren't official nationally; nor is Arabic
# in Israel since 2018.
COUNTRIES = {
    country.code: country
    for country in (
        Country("ar", "en:argentina", ("es",)),
        Country("at", "en:austria", ("de",)),
        Country("au", "en:australia", ("en",)),
        Country("be", "en:belgium", ("nl", "fr", "de")),
        Country("bg", "en:bulgaria", ("bg",)),
        Country("br", "en:brazil", ("pt",)),
        Country("ca", "en:canada", ("en", "fr")),
        Country("ch", "en:switzerland", ("de", "fr", "it")),
        Country("cz", "en:czech-republic", ("cs",)),
        Country("de", "en:germany", ("de",)),
        Country("dk", "en:denmark", ("da",)),
        Country("ee", "en:estonia", ("et",)),
        Country("es", "en:spain", ("es",)),
        Country("fi", "en:finland", ("fi", "sv")),
        Country("fr", "en:france", ("fr",)),
        Country("gb", "en:united-kingdom", ("en",)),
        Country("gr", "en:greece", ("el",)),
        Country("hr", "en:croatia", ("hr",)),
        Country("hu", "en:hungary", ("hu",)),
        Country("ie", "en:ireland", ("en",)),
        Country("il", "en:israel", ("he",)),
        Country("in", "en:india", ("hi", "en")),
        Country("it", "en:italy", ("it",)),
        Country("jp", "en:japan", ("ja",)),
        Country("lt", "en:lithuania", ("lt",)),
        Country("lu", "en:luxembourg", ("lb", "fr", "de")),
        Country("ma", "en:morocco", ("ar",)),
        Country("mx", "en:mexico", ("es",)),
        Country("nl", "en:netherlands", ("nl",)),
        Country("no", "en:norway", ("nb",)),  # Open Food Facts' "no" names count as "nb" (names)
        Country("nz", "en:new-zealand", ("en",)),
        Country("pl", "en:poland", ("pl",)),
        Country("pt", "en:portugal", ("pt",)),
        Country("ro", "en:romania", ("ro",)),
        Country("ru", "en:russia", ("ru",)),
        Country("sa", "en:saudi-arabia", ("ar",)),
        Country("se", "en:sweden", ("sv",)),
        Country("sg", "en:singapore", ("en", "zh", "ms")),
        Country("sk", "en:slovakia", ("sk",)),
        Country("th", "en:thailand", ("th",)),
        Country("tr", "en:turkey", ("tr",)),
        Country("ua", "en:ukraine", ("uk",)),
        Country("us", "en:united-states", ("en",), usda_branded=True),
        Country("za", "en:south-africa", ("en", "af")),
    )
}
