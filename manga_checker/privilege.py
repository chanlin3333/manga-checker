"""検索結果の『該当商品カード』だけを見て特典を判定する。"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from manga_checker.product_cards import extract_product_card_texts
from manga_checker.title_match import titles_match

_STRONG_PRIVILEGE = [
    re.compile(r"特典あり"),
    re.compile(r"購入特典"),
    re.compile(r"店舗特典"),
    re.compile(r"有償特典"),
    re.compile(r"限定特典"),
    re.compile(r"メロン限定版"),
    re.compile(r"メロンブックス限定"),
    re.compile(r"メロンブックス特典"),
    re.compile(r"アニメイト特典"),
    re.compile(r"ゲーマーズ特典"),
    re.compile(r"ゲーマーズ限定"),
    re.compile(r"とらのあな特典"),
    re.compile(r"とらのあな限定"),
    re.compile(r"喜久屋特典"),
    re.compile(r"特典付"),
    re.compile(r"特典付き"),
    re.compile(r"【特典"),
    re.compile(r"特典（"),
    re.compile(r"特典\("),
    re.compile(r"特典ペーパー"),
    re.compile(r"イラストペーパー"),
    re.compile(r"イラストカード"),
    re.compile(r"リーフレット"),
    re.compile(r"描き下ろし"),
    re.compile(r"ブロマイド"),
    re.compile(r"G特典"),
    re.compile(r"icon_present", re.IGNORECASE),
    re.compile(r"icon_tokuten", re.IGNORECASE),
    re.compile(r"アクリルスタンド"),
    re.compile(r"メロン限定"),
]

_NEGATIONS = [
    re.compile(r"特典なし"),
    re.compile(r"特典無し"),
    re.compile(r"特典配布終了"),
    re.compile(r"【特典なし】"),
    re.compile(r"特典は終了"),
    re.compile(r"特典終了"),
    re.compile(r"特典はございません"),
    re.compile(r"特典はありません"),
    re.compile(r"特典情報はありません"),
    re.compile(r"特典はお付けできません"),
]

_ENDED_PRIVILEGE = re.compile(
    r"特典.{0,12}(なし|無し|終了|ございません|ありません|お付けできません)|"
    r"(なし|無し|終了).{0,8}特典|"
    r"配布終了"
)

_NO_HIT_PHRASES = (
    "該当する商品はございません",
    "見つかりませんでした",
    "検索結果はありません",
    "該当する商品は見つかりませんでした",
    "お探しの商品は見つかりません",
)
_ZERO_HIT = re.compile(
    r"(検索結果|該当|ヒット)[^\d]{0,12}0\s*件|(?<![\d０-９])0\s*件(?!\d)|件数[：:\s]*0(?:件)?"
)

_MELON_CONCRETE = (
    "メロン限定版",
    "メロンブックス限定",
    "メロンブックス特典",
    "メロン限定",
    "描き下ろしイラストカード",
    "イラストカード",
    "描き下ろし",
    "リーフレット",
    "アクリルスタンド",
    "有償特典",
    "特典ペーパー",
    "特典付き",
    "特典付",
    "購入特典",
    "店舗特典",
    "特典（",
    "【特典",
)

_KINO_YES = re.compile(r"特典|限定|ペーパー|イラストカード")
_KINO_CHROME = re.compile(
    r"(header|footer|global.?nav|gnav|utility|member|login|topicpath|"
    r"breadcrumb|sidemenu|side_nav)",
    re.I,
)

STATUS_YES = "特典あり"
STATUS_NO = "通常/なし"
STATUS_UNKNOWN = "未確認"


def evaluate_privilege(
    html: str,
    *,
    title_for_match: str,
    isbn: str = "",
    author: str = "",
    source_url: str = "",
    store_id: str = "",
    http_ok: bool = True,
) -> tuple[str, str]:
    """ページ全体は見ない。商品一覧の該当カードだけを判定する。"""
    if not http_ok:
        return STATUS_UNKNOWN, "ページを取得できませんでした。"

    if store_id == "kinokuniya" or "kinokuniya.co.jp" in (source_url or ""):
        return _evaluate_kinokuniya(
            html, title_for_match=title_for_match, isbn=isbn, author=author
        )
    if store_id == "melonbooks" or "melonbooks.co.jp" in (source_url or ""):
        if "detail.php" in (source_url or ""):
            from manga_checker.melon import evaluate_melon_detail

            return evaluate_melon_detail(html)
        return (
            STATUS_UNKNOWN,
            "検索一覧では判定せず、一致する商品詳細ページの確認が必要です。",
        )

    markup = html or ""
    if "<" not in markup:
        markup = f'<ul class="item_list"><li class="item">{markup}</li></ul>'

    if _looks_like_no_hit(markup, title_for_match, isbn):
        return STATUS_UNKNOWN, "検索ヒットが見つかりませんでした。"

    cards = extract_product_card_texts(markup, title_for_match, isbn, author=author)
    if not cards:
        return STATUS_NO, "該当作品の商品カードが見つかりませんでした。"

    hits: list[str] = []
    negated = False
    for card in cards:
        if _privilege_ended(card):
            negated = True
            continue
        if _is_negated(card):
            negated = True
            continue
        hits.extend(privilege_keywords_in(card))
    hits = list(dict.fromkeys(hits))
    if hits:
        return STATUS_YES, "商品カードで検出: " + " / ".join(hits[:4])
    if negated:
        return STATUS_NO, "該当商品に特典なし／配布終了の記載があります。"
    return STATUS_NO, "該当商品カードに特典表記はありません。"


def card_has_privilege(text: str) -> list[str]:
    return privilege_keywords_in(text)


def privilege_keywords_in(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in _STRONG_PRIVILEGE:
        match = pattern.search(text)
        if match:
            token = match.group(0)
            if token not in hits:
                hits.append(token)
    return hits


def _evaluate_melonbooks(
    html: str, *, title_for_match: str, isbn: str, author: str = ""
) -> tuple[str, str]:
    markup = html or ""
    if "<" not in markup:
        markup = f'<ul class="item_list"><li class="item">{markup}</li></ul>'
    if _looks_like_no_hit(markup, title_for_match, isbn):
        return STATUS_UNKNOWN, "検索ヒットが見つかりませんでした。"

    cards = extract_product_card_texts(
        markup, title_for_match, isbn, author=author, plain=True
    )
    if not cards:
        return STATUS_NO, "該当作品の商品カードが見つかりませんでした。"

    hits: list[str] = []
    for card in cards:
        if _privilege_ended(card):
            continue
        hits.extend(_melon_concrete_hits(card))
    hits = list(dict.fromkeys(hits))
    if hits:
        return STATUS_YES, "商品カードテキストで検出: " + " / ".join(hits[:4])
    return STATUS_NO, "該当商品カードに特典文言はありません。"


def _evaluate_kinokuniya(
    html: str, *, title_for_match: str, isbn: str, author: str = ""
) -> tuple[str, str]:
    markup = html or ""
    if _looks_like_no_hit(markup, title_for_match, isbn):
        return STATUS_UNKNOWN, "検索ヒットが見つかりませんでした。"

    titles = _kinokuniya_product_titles(markup, title_for_match, isbn, author=author)
    if not titles:
        return STATUS_NO, "該当商品のタイトル見出しが見つかりませんでした。"

    hits: list[str] = []
    for heading in titles:
        for match in _KINO_YES.finditer(heading):
            token = match.group(0)
            if token not in hits:
                hits.append(token)
    if hits:
        return STATUS_YES, "商品タイトルで検出: " + " / ".join(hits[:4])
    return STATUS_NO, "商品タイトルに特典表記はありません。"


def _kinokuniya_product_titles(
    html: str, title: str, isbn: str, author: str = ""
) -> list[str]:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup.find_all(("header", "footer", "nav", "aside")):
        tag.decompose()
    for tag in soup.find_all(class_=_KINO_CHROME):
        tag.decompose()
    for tag in soup.find_all(id=_KINO_CHROME):
        tag.decompose()

    headings: list[str] = []
    seen: set[str] = set()
    for el in soup.select("h1, h2, h3"):
        text = el.get_text(" ", strip=True)
        if not text or text in seen:
            continue
        if titles_match(title, text, isbn, author=author):
            seen.add(text)
            headings.append(text)
    return headings


def _melon_concrete_hits(text: str) -> list[str]:
    hits: list[str] = []
    for word in _MELON_CONCRETE:
        if word in text and word not in hits:
            hits.append(word)
    return hits


def _privilege_ended(text: str) -> bool:
    return bool(_ENDED_PRIVILEGE.search(text or ""))


def _looks_like_no_hit(html: str, title: str, isbn: str) -> bool:
    text = re.sub(r"\s+", " ", html or "")
    has_marker = any(marker in text for marker in _NO_HIT_PHRASES) or bool(_ZERO_HIT.search(text))
    has_work = (title and title in text) or (isbn and isbn in text)
    return has_marker and not has_work


def _is_negated(text: str) -> bool:
    return any(pattern.search(text) for pattern in _NEGATIONS)
