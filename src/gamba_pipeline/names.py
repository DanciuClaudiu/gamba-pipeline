"""Product names and brands for the packs (SPEC §3.10, Q34)."""


def clean(text: str | None) -> str | None:
    """Whitespace collapsed; None when nothing is left."""
    cleaned = " ".join((text or "").split())
    return cleaned or None


def pick(
    names: dict[str, str], main_language: str | None, languages: tuple[str, ...]
) -> tuple[str | None, dict[str, str]]:
    """The product's main name, and its names in `languages` that differ from it.

    Open Food Facts lists names by language, with "main" for the product's main language. Without
    a "main" entry, the name in the product's language is used, then the first of `languages`, then
    any name."""
    cleaned = {lang: text for lang, raw in names.items() if (text := clean(raw))}
    main = (
        cleaned.get("main")
        or (cleaned.get(main_language) if main_language else None)
        or next((cleaned[lang] for lang in languages if lang in cleaned), None)
        or next(iter(cleaned.values()), None)
    )
    others = {
        lang: cleaned[lang] for lang in languages if lang in cleaned and cleaned[lang] != main
    }
    return main, others


def first_brand(brands: str | None) -> str | None:
    """The first of Open Food Facts' comma-separated brands ("Pringles, Kellogg's" → "Pringles")."""
    return next((brand for part in (brands or "").split(",") if (brand := clean(part))), None)
