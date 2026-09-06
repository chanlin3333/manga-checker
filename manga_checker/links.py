"""Amazon / 楽天ブックスへの直通URL。"""

from __future__ import annotations

from urllib.parse import quote, urlencode

from manga_checker.config import affiliate_settings, rakuten_affiliate_id
from manga_checker.covers import isbn13_to_isbn10


def isbn13(isbn: str) -> str:
    return "".join(ch for ch in isbn if ch.isdigit())


def isbn_search_query(isbn: str) -> str:
    """書店検索用。13桁ISBNを優先し、なければ10桁。"""
    compact = "".join(ch for ch in (isbn or "") if ch.isdigit() or ch in "Xx").upper()
    digits = "".join(ch for ch in compact if ch.isdigit())
    if len(digits) >= 13:
        return digits[:13]
    if len(compact) == 10:
        return compact
    return ""


def amazon_url(isbn: str = "", title: str = "") -> str:
    digits = "".join(ch for ch in isbn if ch.isdigit() or ch in "Xx")
    if len(digits) == 13 and digits.startswith("978"):
        isbn10 = isbn13_to_isbn10(digits)
        url = f"https://www.amazon.co.jp/dp/{isbn10}" if isbn10 else (
            "https://www.amazon.co.jp/s?k=" + quote(digits)
        )
    elif len(digits) == 13:
        url = "https://www.amazon.co.jp/s?k=" + quote(digits)
    elif len(digits) == 10:
        url = f"https://www.amazon.co.jp/dp/{digits.upper()}"
    elif title:
        url = "https://www.amazon.co.jp/s?k=" + quote(title)
    else:
        url = "https://www.amazon.co.jp/"
    tag = affiliate_settings().get("amazon_tag") or ""
    if tag and "amazon.co.jp" in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}tag={quote(tag)}"
    return url


def rakuten_url(isbn: str = "", title: str = "") -> str:
    digits = isbn13(isbn)
    if len(digits) == 13:
        url = "https://books.rakuten.co.jp/search?" + urlencode({"sitem": digits, "g": "001"})
    elif title:
        url = "https://books.rakuten.co.jp/search?" + urlencode({"sitem": title, "g": "001"})
    else:
        url = "https://books.rakuten.co.jp/"
    aid = rakuten_affiliate_id()
    if aid and url.startswith("https://books.rakuten.co.jp/"):
        url = "https://hb.afl.rakuten.co.jp/hgc/" + quote(aid, safe="") + "/?pc=" + quote(url, safe="")
    return url
