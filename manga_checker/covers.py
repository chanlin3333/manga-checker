"""ISBN から書影URLを組み立てる。"""

from __future__ import annotations


def amazon_cover_url(isbn: str) -> str:
    digits = "".join(ch for ch in isbn if ch.isdigit() or ch in "Xx")
    if len(digits) == 13 and digits.startswith("978"):
        isbn10 = isbn13_to_isbn10(digits)
        if isbn10:
            return f"https://images-na.ssl-images-amazon.com/images/P/{isbn10}.09.LZZZZZZZ.jpg"
    if len(digits) == 10:
        return f"https://images-na.ssl-images-amazon.com/images/P/{digits.upper()}.09.LZZZZZZZ.jpg"
    if len(digits) == 13:
        return f"https://images-na.ssl-images-amazon.com/images/P/{digits}.09.LZZZZZZZ.jpg"
    return ""


def openbd_cover_fallback(isbn: str) -> str:
    digits = "".join(ch for ch in isbn if ch.isdigit())
    if len(digits) == 13:
        return f"https://cover.openbd.jp/{digits}.jpg"
    return ""


def isbn13_to_isbn10(isbn13: str) -> str:
    core = isbn13[3:12]
    if len(core) != 9 or not core.isdigit():
        return ""
    total = sum(int(ch) * (10 - i) for i, ch in enumerate(core))
    remainder = total % 11
    check = 11 - remainder
    if check == 10:
        check_ch = "X"
    elif check == 11:
        check_ch = "0"
    else:
        check_ch = str(check)
    return core + check_ch
