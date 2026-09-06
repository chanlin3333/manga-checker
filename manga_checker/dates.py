"""発売日の正規化と表示用フォーマット。"""

from __future__ import annotations

import re
from datetime import date, datetime

_WEEKDAYS = "月火水木金土日"


def prefer_pubdate(*candidates: str) -> str:
    """年月日まで分かる値を優先する。"""
    best = ""
    best_score = -1
    for raw in candidates:
        value = (raw or "").strip()
        if not value:
            continue
        score = len(_digits(value))
        if score > best_score:
            best = value
            best_score = score
    return best


def format_release_date(raw: str) -> str:
    """「2026/09/27 (日)」形式。日が無い場合は年月のみ。"""
    value = (raw or "").strip()
    if not value:
        return "日付未登録"
    parsed = parse_release_date(value)
    if parsed:
        w = _WEEKDAYS[parsed.weekday()]
        return f"{parsed:%Y/%m/%d} ({w})"
    match = re.search(r"(\d{4})\D+(\d{1,2})(?:\D+(\d{1,2}))?", value)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        if match.group(3):
            try:
                parsed = date(year, month, int(match.group(3)))
            except ValueError:
                parsed = None
            if parsed:
                w = _WEEKDAYS[parsed.weekday()]
                return f"{parsed:%Y/%m/%d} ({w})"
        if 1 <= month <= 12:
            return f"{year:04d}/{month:02d}"
    digits = _digits(value)
    if len(digits) >= 6:
        return f"{digits[:4]}/{digits[4:6]}"
    return value


def _digits(raw: str) -> str:
    return re.sub(r"\D", "", raw)


def has_full_day(raw: str) -> bool:
    return parse_release_date(raw) is not None


def parse_release_date(raw: str) -> date | None:
    value = (raw or "").strip()
    if not value:
        return None
    digits = _digits(value)
    if len(digits) >= 8:
        try:
            return datetime.strptime(digits[:8], "%Y%m%d").date()
        except ValueError:
            pass
    match = re.search(r"(\d{4})[./年-](\d{1,2})[./月-](\d{1,2})", value)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            return None
    return None


def iter_months(year: int, month: int, count: int = 4) -> list[tuple[int, int]]:
    """year/month から連続する count ヶ月（年またぎ可）。"""
    if count < 1:
        raise ValueError("count は 1 以上にしてください。")
    if not 1 <= month <= 12:
        raise ValueError("month は 1〜12 です。")
    y, m = year, month
    months: list[tuple[int, int]] = []
    for _ in range(count):
        months.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return months
