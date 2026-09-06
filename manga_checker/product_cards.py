"""検索結果HTMLから、該当作品の商品カードだけを取り出す。"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, NavigableString, Tag

from manga_checker.title_match import titles_match

_NOISE_TAGS = ("script", "style", "nav", "header", "footer", "aside", "noscript")
_NOISE_CLASS = re.compile(
    r"(side|sidebar|recommend|pickup|osusume|slider|swiper|"
    r"checkbox|topicpath|breadcrumb|ranking|modal|popup)",
    re.I,
)
_LIST_CONTAINER = re.compile(r"(item_list|product.?list|search.?list|result.?list|list_wrap)", re.I)
_CARD_CLASS = re.compile(
    r"(item|product|goods|card|entry|search_result|item_box|product_box)",
    re.I,
)
_PRIVILEGE_CLASS = re.compile(
    r"(icon_present|present_icon|g.?tokuten|tokuten|privilege|limited|"
    r"gentei|icon.?bonus|icon.?gift|leaflet|acrylic)",
    re.I,
)
_PRIVILEGE_SRC = re.compile(
    r"(present|tokuten|privilege|gentei|limited|gift|leaflet|acrylic)",
    re.I,
)
_CARD_SELECTORS = (
    "li.item",
    "div.item",
    "div.product",
    "article.product",
    "li.product",
    "[class*='item_box']",
    "[class*='search_item']",
    "[class*='itemlist']",
    "[class*='product_item']",
)
_ICON_SELECTORS = (
    ".icon_tokuten",
    "[class*='icon_tokuten']",
    "[class*='icon_gentei']",
    ".icon_present",
    "[class*='icon_present']",
)


def extract_product_card_texts(
    html: str, title: str, isbn: str = "", *, author: str = "", plain: bool = False
) -> list[str]:
    soup = BeautifulSoup(html or "", "html.parser")
    _strip_noise(soup)
    cards: list[str] = []
    seen: set[int] = set()

    for node in _candidate_nodes(soup, title, isbn, include_icons=not plain):
        ident = id(node)
        if ident in seen:
            continue
        seen.add(ident)
        text = card_plain_text(node) if plain else visible_card_text(node)
        if 8 < len(text) < 12000 and titles_match(title, text, isbn, author=author):
            cards.append(text)
    return cards


def card_plain_text(el: Tag) -> str:
    parts = [el.get_text(" ", strip=True)]
    for node in el.find_all(True):
        for attr in ("alt", "title", "aria-label"):
            value = node.get(attr)
            if value:
                parts.append(str(value))
    return " ".join(parts)


def visible_card_text(el: Tag) -> str:
    parts = [el.get_text(" ", strip=True)]
    nodes = [el, *el.find_all(True)]
    for node in nodes:
        for attr in (
            "alt",
            "title",
            "aria-label",
            "data-original-title",
            "data-tooltip",
            "data-content",
        ):
            value = node.get(attr)
            if value:
                parts.append(str(value))
        classes = " ".join(node.get("class") or [])
        node_id = str(node.get("id") or "")
        blob = f"{classes} {node_id}"
        if _PRIVILEGE_CLASS.search(blob):
            if re.search(r"icon_present|present_icon|g.?tokuten", blob, re.I):
                parts.append("G特典")
            if re.search(r"icon_tokuten|tokuten|privilege|leaflet|acrylic", blob, re.I):
                parts.append("特典")
                parts.append("icon_tokuten")
                parts.append("特典あり")
            if re.search(r"gentei|limited|メロン限定", blob, re.I):
                parts.append("メロン限定版")
        for attr in ("src", "data-src", "data-original"):
            src = str(node.get(attr) or "")
            if src and _PRIVILEGE_SRC.search(src):
                parts.append("特典あり")
                if re.search(r"present", src, re.I):
                    parts.append("G特典")
    return " ".join(parts)


def _strip_noise(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(_NOISE_TAGS):
        tag.decompose()
    for tag in soup.find_all(class_=_NOISE_CLASS):
        tag.decompose()
    for tag in soup.find_all(id=_NOISE_CLASS):
        tag.decompose()


def _candidate_nodes(
    soup: BeautifulSoup, title: str, isbn: str, *, include_icons: bool = True
) -> list[Tag]:
    found: list[Tag] = []
    for selector in _CARD_SELECTORS:
        for el in soup.select(selector):
            classes = " ".join(el.get("class") or []).lower()
            if "list" in classes and "item" not in classes:
                continue
            found.append(el)
    if include_icons:
        for icon in soup.select(",".join(_ICON_SELECTORS)):
            card = _nearest_card(icon)
            if card is not None:
                found.append(card)
    for node in _title_nodes(soup, title, isbn):
        card = _nearest_card(node)
        if card is not None:
            found.append(card)
    return found


def _title_nodes(soup: BeautifulSoup, title: str, isbn: str) -> list[Tag | NavigableString]:
    needles = [n for n in (title, isbn) if n and len(n) >= 2]
    found: list[Tag | NavigableString] = []
    for needle in needles:
        pattern = re.compile(re.escape(needle))
        found.extend(soup.find_all(string=pattern))
    return found


def _nearest_card(node: Tag | NavigableString) -> Tag | None:
    el = node.parent if isinstance(node, NavigableString) else node
    best: Tag | None = None
    for _ in range(16):
        if el is None or not isinstance(el, Tag):
            break
        if el.name in {"body", "html"}:
            break
        classes = " ".join(el.get("class") or [])
        el_id = str(el.get("id") or "")
        if _LIST_CONTAINER.search(classes) or _LIST_CONTAINER.search(el_id):
            break
        if _NOISE_CLASS.search(classes) or _NOISE_CLASS.search(el_id):
            el = el.parent
            continue
        if el.name in {"li", "article"}:
            return el
        if el.name in {"div", "section"} and _CARD_CLASS.search(classes) and "list" not in classes.lower():
            best = el
        el = el.parent
    return best
