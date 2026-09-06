"""タイトル・巻次から『第1巻』相当かを判定する。"""

from __future__ import annotations

import re
import unicodedata

# 全角数字・括弧などを半角へ揃える
_VOLUME_FIELD_ONE = re.compile(r"^(第)?0*1(巻|冊)?$")
_OTHER_VOLUME_FIELD = re.compile(r"^(第)?\d+(巻|冊)?$")

# 11巻・21巻を除外しつつ、スペース混じり・末尾の 1 / （1） / 1巻 / 第1巻 を拾う
_VOLUME_ONE_PATTERN = re.compile(
    r"(?<![0-9０-９])(?:第\s*[1１]\s*巻|[1１]\s*巻|[(（]\s*[1１]\s*[)）]|[ \u3000][1１](?=[ \u3000:：\(\)（）~〜-]|$))(?![0-9０-９])"
)
_VOLUME_ONE_EXTRA = [
    re.compile(r"(?<!\d)vol\.?\s*0*1(?!\d)", re.IGNORECASE),
    re.compile(r"(?<!\d)volume\s*0*1(?!\d)", re.IGNORECASE),
]


def normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "")
    return re.sub(r"\s+", " ", text).strip()


def is_volume_one(title: str, volume: str = "") -> bool:
    """第1巻らしい書誌なら True。

    単なる数字の『1』（例: 『1日10分で〜』）は対象外。
    『(1)』『第1巻』『1巻』および半角・全角スペースで区切られた末尾の『 1』を拾う。
    """
    title_n = normalize_text(title)
    volume_n = normalize_text(volume)

    if volume_n:
        if _VOLUME_FIELD_ONE.fullmatch(volume_n):
            return True
        if _OTHER_VOLUME_FIELD.fullmatch(volume_n):
            return False

    for haystack in _search_texts(title, volume):
        if _VOLUME_ONE_PATTERN.search(haystack):
            return True
        if any(pattern.search(haystack) for pattern in _VOLUME_ONE_EXTRA):
            return True
    return False


def _search_texts(title: str, volume: str) -> list[str]:
    """スペース種別を潰す前の原文と、正規化後の両方を見る。"""
    raw_title = title or ""
    raw_volume = volume or ""
    texts = [
        raw_title,
        f"{raw_title} {raw_volume}".strip(),
        unicodedata.normalize("NFKC", raw_title),
        normalize_text(f"{raw_title} {raw_volume}"),
    ]
    seen: set[str] = set()
    unique: list[str] = []
    for text in texts:
        if text and text not in seen:
            seen.add(text)
            unique.append(text)
    return unique
