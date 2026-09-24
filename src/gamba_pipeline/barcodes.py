"""Barcodes as GTIN-14 (SPEC §3.6), the same rules as the app's `GambaCore.GTIN`. Both repositories
test against the same vectors, `shared/barcodes.json` (plan P18)."""

SYMBOLOGIES = frozenset({"ean13", "ean8", "upcA", "upcE"})


def normalize(raw: str, symbology: str | None = None) -> str | None:
    """`raw` as a GTIN-14, or None when it isn't a valid EAN-13, EAN-8, UPC-A, UPC-E or GTIN-14.
    Open Food Facts codes are typed codes (no symbology): an 8-digit code is read as EAN-8 when its
    check digit fits, otherwise as UPC-E."""
    code = raw.strip()
    if not code or not code.isascii() or not code.isdigit():
        return None
    match symbology, len(code):
        case "upcE", 8:
            expanded = expand_upce(code)
            return _padded(expanded) if expanded else None
        case ("ean8", 8) | ("ean13", 12 | 13) | ("upcA", 12 | 13) | (None, 12 | 13 | 14):
            return _padded(code) if has_valid_check_digit(code) else None
        case None, 8:
            if has_valid_check_digit(code):
                return _padded(code)
            expanded = expand_upce(code)
            return _padded(expanded) if expanded else None
        case _:
            return None


def expand_upce(code: str) -> str | None:
    """The 12-digit UPC-A for an 8-digit UPC-E (number system 0 or 1), or None when the check digit
    doesn't match."""
    d = list(code)
    if len(d) != 8 or d[0] not in "01":
        return None
    match d[6]:
        case "0" | "1" | "2":
            parts = [d[0], d[1], d[2], d[6], "0000", d[3], d[4], d[5]]
        case "3":
            parts = [d[0], d[1], d[2], d[3], "00000", d[4], d[5]]
        case "4":
            parts = [d[0], d[1], d[2], d[3], d[4], "00000", d[5]]
        case _:
            parts = [d[0], d[1], d[2], d[3], d[4], d[5], "0000", d[6]]
    upc_a = "".join(parts) + d[7]
    return upc_a if has_valid_check_digit(upc_a) else None


def has_valid_check_digit(code: str) -> bool:
    if len(code) < 2 or not code.isascii() or not code.isdigit():
        return False
    return check_digit(code[:-1]) == int(code[-1])


def check_digit(body: str) -> int:
    """GS1 mod 10: weights 3 and 1 alternate, starting with 3 at the rightmost digit."""
    total = sum(
        int(digit) * (3 if index % 2 == 0 else 1) for index, digit in enumerate(reversed(body))
    )
    return (10 - total % 10) % 10


def _padded(code: str) -> str:
    return code.rjust(14, "0")
