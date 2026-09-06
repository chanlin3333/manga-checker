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


def format_year_month(year: int, month: int) -> str:
    """タブ・説明文用の「2026年10月」形式（月はゼロ埋めしない）。"""
    return f"{year}年{month}月"


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    """年月に delta ヶ月を加算する（負数可、年またぎ可）。"""
    if not 1 <= month <= 12:
        raise ValueError("month は 1〜12 です。")
    index = year * 12 + (month - 1) + delta
    y, m0 = divmod(index, 12)
    return y, m0 + 1


def iter_months(year: int, month: int, count: int = 4) -> list[tuple[int, int]]:
    """year/month から連続する count ヶ月（年またぎ可）。"""
    if count < 1:
        raise ValueError("count は 1 以上にしてください。")
    if not 1 <= month <= 12:
        raise ValueError("month は 1〜12 です。")
    return [add_months(year, month, i) for i in range(count)]


def iter_month_offsets(
    year: int | None = None,
    month: int | None = None,
    *,
    before: int = 3,
    after: int = 3,
    today: date | None = None,
) -> list[tuple[int, int]]:
    """基準月の before ヶ月前から after ヶ月後まで（既定は -3〜+3 の7ヶ月）。"""
    if before < 0 or after < 0:
        raise ValueError("before / after は 0 以上にしてください。")
    today = today or date.today()
    y = today.year if year is None else year
    m = today.month if month is None else month
    if not 1 <= m <= 12:
        raise ValueError("month は 1〜12 です。")
    return [add_months(y, m, offset) for offset in range(-before, after + 1)]
