"""出版社の表示優先順。"""

from __future__ import annotations

import re

from manga_checker.volume import normalize_text

PUBLISHER_ORDER = [
    "集英社",
    "講談社",
    "小学館",
    "KADOKAWA",
    "秋田書店",
    "芳文社",
    "スクウェア・エニックス",
    "白泉社",
    "竹書房",
    "双葉社",
    "少年画報社",
    "徳間書店",
    "一迅社",
    "マッグガーデン",
    "コアミックス",
    "TOブックス",
    "アルファポリス",
    "オーバーラップ",
    "フロンティアワークス",
    "ホビージャパン",
    "ブシロードワークス",
    "マイクロマガジン社",
    "イマジカインフォス",
]
PRIORITY_PUBLISHERS = PUBLISHER_ORDER
OTHER_PUBLISHER_LABEL = "その他"

_KADOKAWA_ALIASES = ("KADOKAWA", "ＫＡＤＯＫＡＷＡ", "角川")
_SQEX_ALIASES = ("スクウェア・エニックス", "スクウェアエニックス", "SQUARE ENIX")
_ORDER_INDEX = {name: i for i, name in enumerate(PUBLISHER_ORDER)}
_ORDER_SET = frozenset(PUBLISHER_ORDER)


def canonical_publisher(publisher: str) -> str:
    text = normalize_text(publisher)
    head = re.split(r"[／/]", text)[0].strip()
    compact = head.replace(" ", "").replace("・", "")
    if any(alias in head or alias.replace("・", "") in compact for alias in _KADOKAWA_ALIASES):
        return "KADOKAWA"
    if any(alias.replace("・", "") in compact or alias in head for alias in _SQEX_ALIASES):
        return "スクウェア・エニックス"
    for name in sorted(PUBLISHER_ORDER, key=len, reverse=True):
        if name in head or name.replace("・", "") in compact:
            return name
    return head or "出版社未登録"


def publisher_group_label(publisher: str) -> str:
    canon = canonical_publisher(publisher)
    if canon in _ORDER_SET:
        return canon
    return OTHER_PUBLISHER_LABEL


def publisher_sort_key(publisher: str, pubdate: str, title: str) -> tuple:
    canon = canonical_publisher(publisher)
    if canon in _ORDER_INDEX:
        tier = _ORDER_INDEX[canon]
    else:
        tier = len(PUBLISHER_ORDER)
    date_key = re.sub(r"\D", "", pubdate or "").ljust(8, "0")
    return (tier, date_key, title)
