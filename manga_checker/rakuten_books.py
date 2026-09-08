"""楽天ブックス書籍検索API (BooksBook/Search) から新刊・予約のコミックを取得する。"""

from __future__ import annotations

import re
import time
import unicodedata

import requests

from manga_checker.config import rakuten_access_key, rakuten_affiliate_id, rakuten_application_id
from manga_checker.dates import date_in_month, month_bounds, prefer_pubdate
from manga_checker.http import make_session
from manga_checker.models import Comic
from manga_checker.publishers import PUBLISHER_ORDER, publisher_sort_key
from manga_checker.volume import is_volume_one, normalize_text

BOOKS_BOOK_SEARCH = "https://openapi.rakuten.co.jp/services/api/BooksBook/Search/20170404"
COMIC_GENRE_ID = "001001"
RAKUTEN_MAX_PAGES = 100
RAKUTEN_HITS_PER_PAGE = 30
# ジャンル走査が100ページ上限で月の先頭まで届かないときの分割キー
RAKUTEN_SPLIT_PUBLISHERS = tuple(
    dict.fromkeys(
        [
            *PUBLISHER_ORDER,
            "ＫＡＤＯＫＡＷＡ",
            "新潮社",
            "幻冬舎コミックス",
            "リブレ",
            "大洋図書",
        ]
    )
)
_SALES_YM = re.compile(r"(?P<y>\d{4})\s*年\s*(?P<m>\d{1,2})\s*月")
_SALES_YMD = re.compile(r"(?P<y>\d{4})\s*年\s*(?P<m>\d{1,2})\s*月\s*(?P<d>\d{1,2})\s*日")
_SALES_ISO = re.compile(r"(?P<y>\d{4})[-/.](?P<m>\d{1,2})(?:[-/.](?P<d>\d{1,2}))?")


def rakuten_configured() -> bool:
    return bool(rakuten_application_id() and rakuten_access_key())


def fetch_rakuten_volume_ones(
    year: int,
    month: int,
    session: requests.Session | None = None,
    delay_sec: float = 1.0,
    max_items: int = 0,
) -> list[Comic]:
    """対象月のコミックを取り切るまで走査し、第1巻を出版社順に分別する。"""
    by_month = fetch_rakuten_volume_ones_by_month(
        [(year, month)], session=session, delay_sec=delay_sec, max_items=max_items
    )
    return by_month.get((year, month), [])


def fetch_rakuten_volume_ones_by_month(
    months: list[tuple[int, int]],
    session: requests.Session | None = None,
    delay_sec: float = 1.0,
    max_items: int = 0,
) -> dict[tuple[int, int], list[Comic]]:
    """発売日降順のジャンル走査を行い、第1巻を各月（初日〜末日）へ振り分ける。

    Books API に発売日範囲パラメータはない。100ページ上限で対象月の先頭（1日）まで
    遡れない月は、件数が残っていても未完了とみなし、在庫走査と出版社分割で取り切る。
    「発売済みだからスキップ」はしない。
    """
    del max_items
    if not months:
        return {}
    if not rakuten_configured():
        raise RuntimeError("楽天アプリIDまたはaccessKeyが未設定です")
    session = session or make_session()
    start = min(months)
    end = max(months)
    first_day, _ = month_bounds(*start)
    _, last_day = month_bounds(*end)
    print(
        f"楽天ブックス: コミックジャンル {COMIC_GENRE_ID} を発売日の新しい順で走査します。"
        f"（対象 {first_day.isoformat()} 00:00:00 〜 {last_day.isoformat()} 23:59:59。"
        f"1ページ最大{RAKUTEN_HITS_PER_PAGE}件 / 最大{RAKUTEN_MAX_PAGES}ページ。"
        f"各月の初日より前の発売日に達するまでページ送り）"
    )
    buckets: dict[tuple[int, int], list[Comic]] = {key: [] for key in months}
    try:
        scanned, reached_older, hit_page_cap, reached_past = _paginate_window(
            session,
            months,
            delay_sec,
            extra={"booksGenreId": COMIC_GENRE_ID},
            max_pages=RAKUTEN_MAX_PAGES,
        )
        _extend_buckets(buckets, scanned)
        incomplete = _incomplete_months(months, reached_older, hit_page_cap, reached_past)
        if incomplete:
            miss_start, miss_end = min(incomplete), max(incomplete)
            print(
                f"楽天ブックス: {RAKUTEN_MAX_PAGES}ページ上限のため "
                f"{miss_start[0]}年{miss_start[1]}月〜{miss_end[0]}年{miss_end[1]}月 "
                "の月初まで届いていません（既存件数があっても補完します）。"
                "予約を除く在庫商品（availability=1）を走査します。"
            )
            try:
                extra_buckets, reached_older, hit_page_cap, reached_past = _paginate_window(
                    session,
                    incomplete,
                    delay_sec,
                    extra={"booksGenreId": COMIC_GENRE_ID, "availability": "1"},
                    max_pages=RAKUTEN_MAX_PAGES,
                )
            except Exception as exc:
                print(f"楽天ブックス: 在庫走査をスキップします（{exc}）。")
            else:
                _extend_buckets(buckets, extra_buckets)
                incomplete = _incomplete_months(
                    incomplete, reached_older, hit_page_cap, reached_past
                )
        if incomplete:
            miss_start, miss_end = min(incomplete), max(incomplete)
            print(
                f"楽天ブックス: 在庫走査でも "
                f"{miss_start[0]}年{miss_start[1]}月〜{miss_end[0]}年{miss_end[1]}月 "
                "の月初まで未到達のため、出版社別にページ送りして全件を集めます。"
            )
            for publisher in RAKUTEN_SPLIT_PUBLISHERS:
                try:
                    extra_buckets, _, _, _ = _paginate_window(
                        session,
                        incomplete,
                        delay_sec,
                        extra={"booksGenreId": COMIC_GENRE_ID, "publisherName": publisher},
                        max_pages=RAKUTEN_MAX_PAGES,
                    )
                except Exception as exc:
                    print(f"楽天ブックス: 出版社「{publisher}」の走査をスキップします（{exc}）。")
                    continue
                _extend_buckets(buckets, extra_buckets)
    except Exception as exc:
        print(
            f"楽天ブックス: 走査を中断しました（{exc}）。"
            f"取得済み {sum(len(v) for v in buckets.values())} 件は月別に残します。"
        )
    result: dict[tuple[int, int], list[Comic]] = {}
    for year, month in months:
        volume_ones = [
            comic
            for comic in buckets.get((year, month), [])
            if is_volume_one(comic.title, comic.volume)
        ]
        volume_ones = _dedupe_comics(volume_ones)
        volume_ones.sort(
            key=lambda c: publisher_sort_key(c.publisher, c.pubdate, c.display_title)
        )
        result[(year, month)] = volume_ones
        first, last = month_bounds(year, month)
        print(
            f"楽天ブックス: {year}年{month}月（{first.isoformat()}〜{last.isoformat()}） "
            f"{len(buckets.get((year, month), []))}件 → 第1巻 {len(volume_ones)}件"
        )
    return result


def parse_rakuten_item(item: dict) -> Comic | None:
    title = normalize_text(str(item.get("title") or ""))
    if not title:
        return None
    isbn = re.sub(r"[^0-9X]", "", str(item.get("isbn") or "").upper())
    sales = str(item.get("salesDate") or "")
    cover = _cover_url(item)
    return Comic(
        title=title,
        author=normalize_text(str(item.get("author") or "").replace("／", " / ")),
        publisher=normalize_text(str(item.get("publisherName") or "")),
        pubdate=normalize_sales_date(sales),
        isbn=isbn,
        source="rakuten",
        series=normalize_text(str(item.get("seriesName") or "")),
        cover_url=cover,
        cover_source="rakuten" if cover else "",
        rakuten_item_url=str(item.get("affiliateUrl") or item.get("itemUrl") or ""),
        title_kana=normalize_text(str(item.get("titleKana") or "")),
        author_kana=normalize_text(str(item.get("authorKana") or "")),
    )


def sales_in_month(sales_date: str, year: int, month: int) -> bool:
    """年と月の部分一致で判定する。解析できない表記は破棄しない。"""
    text = _normalize_sales_text(sales_date)
    if not text:
        return True
    if _year_month_mentioned(text, year, month):
        return True
    parsed = sales_year_month(text)
    if parsed is None:
        return True
    return parsed == (year, month)


def sales_year_month(sales_date: str) -> tuple[int, int] | None:
    text = _normalize_sales_text(sales_date)
    if not text:
        return None
    for pattern in (_SALES_YM, _SALES_ISO):
        match = pattern.search(text)
        if not match:
            continue
        year, month = int(match.group("y")), int(match.group("m"))
        if 1 <= month <= 12:
            return year, month
    digits = re.sub(r"\D", "", text)
    if len(digits) >= 6:
        year, month = int(digits[:4]), int(digits[4:6])
        if 1 <= month <= 12:
            return year, month
    return None


def _usable_year_month(sales_date: str) -> tuple[int, int] | None:
    """3099年などのプレースホルダ発売日は走査終了判定・月振り分けに使わない。"""
    ym = sales_year_month(sales_date)
    if ym is None:
        return None
    year, _month = ym
    if year < 1990 or year >= 2100:
        return None
    return ym


def _first_usable_year_month(items: list[dict]) -> tuple[int, int] | None:
    for item in items:
        ym = _usable_year_month(str(item.get("salesDate") or ""))
        if ym:
            return ym
    return None


def normalize_sales_date(sales_date: str) -> str:
    text = _normalize_sales_text(sales_date)
    match = _SALES_YMD.search(text)
    if match:
        return (
            f"{int(match.group('y')):04d}-"
            f"{int(match.group('m')):02d}-"
            f"{int(match.group('d')):02d}"
        )
    iso = _SALES_ISO.search(text)
    if iso and iso.group("d"):
        return (
            f"{int(iso.group('y')):04d}-"
            f"{int(iso.group('m')):02d}-"
            f"{int(iso.group('d')):02d}"
        )
    ym = sales_year_month(text)
    if ym:
        return f"{ym[0]:04d}-{ym[1]:02d}"
    return prefer_pubdate(sales_date)


def _normalize_sales_text(sales_date: str) -> str:
    return unicodedata.normalize("NFKC", sales_date or "").strip()


def _year_month_mentioned(text: str, year: int, month: int) -> bool:
    compact = re.sub(r"\s+", "", text)
    y = f"{year:04d}"
    m2 = f"{month:02d}"
    m1 = str(month)
    needles = (
        f"{y}年{m2}月",
        f"{y}年{m1}月",
        f"{y}-{m2}",
        f"{y}/{m2}",
        f"{y}.{m2}",
    )
    return any(needle in compact for needle in needles)


def _dedupe_comics(comics: list[Comic]) -> list[Comic]:
    seen: set[str] = set()
    unique: list[Comic] = []
    for comic in comics:
        key = comic.isbn or comic.display_title
        if key in seen:
            continue
        seen.add(key)
        unique.append(comic)
    return unique


def _paginate_month(
    session: requests.Session,
    year: int,
    month: int,
    delay_sec: float,
    extra: dict[str, str],
    stop_on_older: bool = True,
    max_pages: int = 100,
    collected: list[Comic] | None = None,
    max_items: int = 0,
    stop_if=None,
) -> list[Comic]:
    """発売日の新しい順に走査し、対象月の書誌を返す。"""
    del collected, max_items, stop_if
    buckets, *_ = _paginate_window(
        session,
        [(year, month)],
        delay_sec,
        extra,
        stop_on_older=stop_on_older,
        max_pages=max_pages,
    )
    return buckets.get((year, month), [])


def _extend_buckets(
    dest: dict[tuple[int, int], list[Comic]],
    src: dict[tuple[int, int], list[Comic]],
) -> None:
    for key, comics in src.items():
        dest.setdefault(key, []).extend(comics)


def _incomplete_months(
    months: list[tuple[int, int]],
    reached_older: bool,
    hit_page_cap: bool,
    reached_past: set[tuple[int, int]],
) -> list[tuple[int, int]]:
    """ページ上限で月初より前まで辿れなかった月。空でも『揃った』とはみなさない。"""
    if reached_older or not hit_page_cap:
        return []
    return [key for key in months if key not in reached_past]


def _paginate_window(
    session: requests.Session,
    months: list[tuple[int, int]],
    delay_sec: float,
    extra: dict[str, str],
    stop_on_older: bool = True,
    max_pages: int = 100,
) -> tuple[dict[tuple[int, int], list[Comic]], bool, bool, set[tuple[int, int]]]:
    """発売日降順を、次ページがなくなるか上限まで走査し、対象月へ振り分ける。

    Returns:
        buckets, reached_older, hit_page_cap, reached_past
        reached_past: その月より古い発売日のページを既に見た月（= その月は降順で取り切った）
    """
    month_set = set(months)
    start_bound = min(months)
    end_bound = max(months)
    buckets: dict[tuple[int, int], list[Comic]] = {key: [] for key in months}
    consecutive_empty = 0
    reached_older = False
    reached_past: set[tuple[int, int]] = set()
    last_page = 0
    api_page_count = max_pages
    for page in range(1, max_pages + 1):
        payload = _request(session, {**extra, "page": str(page)})
        items = _items(payload)
        api_page_count = _page_count(payload, cap=max_pages)
        last_page = page
        if delay_sec:
            time.sleep(max(delay_sec, 1.0))
        if not items:
            consecutive_empty += 1
            print(
                f"楽天ブックス取得中: ページ {page}/{api_page_count} "
                f"(0件, 空ページ継続 {consecutive_empty})"
            )
            if consecutive_empty >= 3 or page >= api_page_count:
                break
            continue
        consecutive_empty = 0
        sample = str(items[0].get("salesDate") or "")
        first_ym = _first_usable_year_month(items)
        if first_ym:
            for ym in month_set:
                if first_ym < ym:
                    reached_past.add(ym)
        stop_after_page = False
        if stop_on_older and first_ym and first_ym < start_bound:
            reached_older = True
            reached_past.update(month_set)
            stop_after_page = True
            print(
                f"楽天ブックス取得中: ページ {page}/{api_page_count} "
                f"(先頭salesDate={sample} が対象期間より前のため、当ページ取り込み後に走査終了)"
            )
        added_by_month: dict[tuple[int, int], int] = {key: 0 for key in months}
        for item in items:
            target = _bucket_for_item(item, months, month_set)
            if target is None:
                continue
            comic = parse_rakuten_item(item)
            if not comic:
                continue
            buckets[target].append(comic)
            added_by_month[target] += 1
        added_total = sum(added_by_month.values())
        counts = " ".join(
            f"{year}/{month:02d}+{added_by_month[(year, month)]}" for year, month in months
        )
        print(
            f"楽天ブックス取得中: ページ {page}/{api_page_count} "
            f"({len(items)}件, 期間内+{added_total} [{counts}]"
            f", 先頭salesDate={sample})"
        )
        if stop_after_page:
            break
        if page >= api_page_count:
            if first_ym and first_ym > end_bound:
                print("  ※ pageCount 上限に達しましたが、まだ対象期間より新しい発売日です。")
            break
    hit_page_cap = last_page >= max_pages and api_page_count >= max_pages and not reached_older
    return buckets, reached_older, hit_page_cap, reached_past


def _bucket_for_item(
    item: dict,
    months: list[tuple[int, int]],
    month_set: set[tuple[int, int]],
) -> tuple[int, int] | None:
    sales = str(item.get("salesDate") or "")
    parsed = sales_year_month(sales)
    if parsed is not None and _usable_year_month(sales) is None:
        return None
    ym = _usable_year_month(sales)
    if ym is not None:
        if ym not in month_set:
            return None
        in_month = date_in_month(sales, ym[0], ym[1])
        if in_month is False:
            return None
        return ym
    for year, month in months:
        if sales_in_month(sales, year, month):
            return (year, month)
    return None


def _page_count(payload: dict, cap: int = RAKUTEN_MAX_PAGES) -> int:
    raw = payload.get("pageCount")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return cap
    if value <= 0:
        return cap
    return min(value, cap)


def _search_params(extra: dict[str, str]) -> dict[str, str]:
    params = {
        "applicationId": rakuten_application_id(),
        "accessKey": rakuten_access_key(),
        "format": "json",
        "formatVersion": "2",
        "hits": str(RAKUTEN_HITS_PER_PAGE),
        "sort": "-releaseDate",
        "outOfStockFlag": "1",
        "availability": extra.get("availability", "0"),
    }
    affiliate = rakuten_affiliate_id()
    if affiliate:
        params["affiliateId"] = affiliate
    for key, value in extra.items():
        if key == "availability" and value == "0":
            continue
        params[key] = value
    return params


def _request(session: requests.Session, extra: dict[str, str]) -> dict:
    params = _search_params(extra)
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            response = session.get(BOOKS_BOOK_SEARCH, params=params, timeout=30)
            if response.status_code == 429:
                time.sleep(4 + attempt * 2)
                continue
            if response.status_code >= 500:
                last_error = RuntimeError(f"楽天API HTTP {response.status_code}: {response.text[:300]}")
                time.sleep(3 + attempt * 3)
                continue
            if response.status_code >= 400:
                try:
                    detail = response.json()
                    message = detail.get("error_description") or detail.get("error") or response.text
                except ValueError:
                    message = response.text
                raise RuntimeError(f"楽天API HTTP {response.status_code}: {message}")
            payload = response.json()
            if not isinstance(payload, dict):
                raise RuntimeError("楽天APIの応答形式が不正です")
            if payload.get("error"):
                raise RuntimeError(str(payload.get("error_description") or payload.get("error")))
            return payload
        except requests.RequestException as exc:
            last_error = exc
            time.sleep(2)
    raise RuntimeError(f"楽天APIへの接続に失敗しました: {last_error}")


def _items(payload: dict) -> list[dict]:
    rows = payload.get("Items") or payload.get("items") or []
    items: list[dict] = []
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("Item"), dict):
            items.append(row["Item"])
        elif isinstance(row, dict):
            items.append(row)
    return items


def _cover_url(item: dict) -> str:
    for key in ("largeImageUrl", "mediumImageUrl", "smallImageUrl"):
        url = str(item.get(key) or "").strip()
        if not url:
            continue
        lowered = url.lower()
        if "noimage" in lowered or "nowprinting" in lowered or "now_printing" in lowered:
            continue
        return url
    return ""
