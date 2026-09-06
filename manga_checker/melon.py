"""メロンブックスの検索結果 → 商品詳細ページの特典判定。"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from manga_checker.privilege import STATUS_NO, STATUS_UNKNOWN, STATUS_YES
from manga_checker.title_match import listing_matches_work

_DETAIL_HREF = re.compile(r"detail\.php", re.I)
_PRODUCT_ID = re.compile(r"product_id=(\d+)", re.I)
_DETAIL_HITS = (
    "特典情報",
    "メロンブックス特典",
    "メロンブックス限定版",
    "メロン限定版",
    "描き下ろしイラストカード",
    "イラストカード",
    "描き下ろし",
    "リーフレット",
)
_NONE = re.compile(r"特典は?[な無]し|特典はありません|特典情報はありません")


def first_melon_detail_url(
    html: str,
    page_url: str,
    title: str = "",
    isbn: str = "",
    author: str = "",
    allow_first: bool = False,
) -> str:
    """検索結果から作品に一致する detail.php?product_id= を返す。"""
    soup = BeautifulSoup(html or "", "html.parser")
    base = page_url or "https://www.melonbooks.co.jp/"
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for tag in soup.find_all("a", href=True):
        abs_url = _melon_detail_url(str(tag.get("href") or ""), base)
        if not abs_url or abs_url in seen:
            continue
        seen.add(abs_url)
        parent = tag.find_parent(["li", "div", "article", "td", "section"]) or tag
        blob = " ".join(
            part for part in (tag.get_text(" ", strip=True), parent.get_text(" ", strip=True)) if part
        )
        score = 2 if listing_matches_work(title, blob, isbn, author=author) else 0
        ranked.append((score, abs_url))
    matching = [url for score, url in ranked if score]
    if matching:
        return matching[0]
    if allow_first and ranked:
        return ranked[0][1]
    return ""


def evaluate_melon_detail(html: str) -> tuple[str, str]:
    if not html:
        return STATUS_UNKNOWN, "詳細ページを取得できませんでした。"
    soup = BeautifulSoup(html, "html.parser")
    blocks: list[str] = []
    for node in soup.select(
        ".privilege, .privilege_box, [class*='privilege'], [id*='privilege'], "
        ".tokuten_box, [class*='tokuten'], [id*='tokuten']"
    ):
        text = node.get_text(" ", strip=True)
        if text:
            blocks.append(text)
    heading = soup.find(string=re.compile(r"特典情報|店舗特典|購入特典"))
    if heading:
        parent = heading.find_parent(["div", "section", "table", "dl", "li", "td"]) or heading.parent
        if parent:
            text = parent.get_text(" ", strip=True)
            if text:
                blocks.append(text)
    combined = " ".join(blocks)
    scope = combined or soup.get_text(" ", strip=True)
    if combined and _NONE.search(combined) and not any(
        word in combined for word in _DETAIL_HITS if word not in {"特典情報"}
    ):
        return STATUS_NO, "詳細ページに特典情報はありません。"
    for word in _DETAIL_HITS:
        if word in scope:
            snippet = _snippet(scope, word)
            return STATUS_YES, f"詳細ページで検出: {snippet}"
    if combined and "特典" in combined and not _NONE.search(combined):
        return STATUS_YES, "詳細ページの特典情報エリアを検出"
    return STATUS_NO, "詳細ページに特典情報はありません。"


def _melon_detail_url(href: str, base: str) -> str:
    if not href:
        return ""
    if not _DETAIL_HREF.search(href) and not _PRODUCT_ID.search(href):
        return ""
    abs_url = urljoin(base, href).split("#")[0]
    parsed = urlparse(abs_url)
    product_id = ""
    match = _PRODUCT_ID.search(abs_url)
    if match:
        product_id = match.group(1)
    else:
        product_id = (parse_qs(parsed.query).get("product_id") or [""])[0]
    if not product_id:
        return ""
    return f"https://www.melonbooks.co.jp/detail/detail.php?product_id={product_id}"


def _snippet(text: str, word: str, radius: int = 40) -> str:
    idx = text.find(word)
    if idx < 0:
        return word
    start = max(0, idx - 8)
    end = min(len(text), idx + len(word) + radius)
    return re.sub(r"\s+", " ", text[start:end]).strip()
