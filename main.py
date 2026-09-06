"""今月発売のコミック第1巻と、主要書店の特典有無を一覧化する。"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from manga_checker.catalog import fetch_months_volume_ones
from manga_checker.dates import iter_months
from manga_checker.http import configure_ssl, make_session
from manga_checker.models import ComicReport
from manga_checker.official import OfficialIndex
from manga_checker.publishers import publisher_sort_key
from manga_checker.report import write_csv, write_html
from manga_checker.stores import check_stores


def parse_args() -> argparse.Namespace:
    today = date.today()
    parser = argparse.ArgumentParser(
        description="当月から数ヶ月分のコミック第1巻を集め、書店特典の確認用一覧を作ります。"
    )
    parser.add_argument("--year", type=int, default=today.year, help="開始年（省略時は今年）")
    parser.add_argument("--month", type=int, default=today.month, help="開始月 1-12（省略時は今月）")
    parser.add_argument(
        "--months",
        type=int,
        default=4,
        help="開始月から何ヶ月分を取得するか（省略時は当月含む4ヶ月）",
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="書店の検索ページを実際に取得してキーワード判定する（時間がかかります）",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="各月の HTML/CSV に出力する件数。楽天APIの取得件数は制限しません。0 で全件出力",
    )
    parser.add_argument(
        "--csv-in",
        type=Path,
        default=None,
        help="追加タイトルのCSV（title,volume,author,publisher,pubdate,isbn）",
    )
    parser.add_argument("--out-dir", type=Path, default=Path("output"), help="出力フォルダ")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="SSL証明書の検証をスキップする（CERTIFICATE_VERIFY_FAILED 向け）",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 1 <= args.month <= 12:
        raise SystemExit("month は 1〜12 で指定してください。")
    if args.months < 1:
        raise SystemExit("months は 1 以上で指定してください。")

    configure_ssl(insecure=True if args.insecure else None)
    if args.insecure:
        print("SSL検証を無効化しています（--insecure）。")

    windows = iter_months(args.year, args.month, args.months)
    labels = "、".join(f"{year}年{month}月" for year, month in windows)
    print(f"書誌を取得しています… {labels}（楽天APIは1回の走査で期間内を振り分けます。--limit は月ごとの出力件数です）")

    session = make_session()
    catalog = OfficialIndex()
    catalog.load(session)

    comics_by_month = fetch_months_volume_ones(windows, extra_csv=args.csv_in, session=session)

    month_panels: list[tuple[int, int, list[ComicReport]]] = []
    all_reports: list[ComicReport] = []
    for year, month in windows:
        print()
        print(f"===== {year}年{month}月 =====")
        comics = list(comics_by_month.get((year, month), []))
        comics.sort(
            key=lambda c: publisher_sort_key(c.publisher, c.pubdate, c.display_title)
        )
        if args.limit and args.limit > 0:
            comics = comics[: args.limit]
            print(f"--limit {args.limit} により {year}年{month}月の出力を {len(comics)} 件に絞りました。")
        else:
            print(f"{year}年{month}月の第1巻を全件処理します: {len(comics)} 件")

        reports: list[ComicReport] = []
        for i, comic in enumerate(comics, start=1):
            print(f"[{i}/{len(comics)}] {comic.display_title}")
            reports.append(
                ComicReport(
                    comic=comic,
                    checks=check_stores(
                        comic,
                        fetch=args.fetch,
                        session=session,
                        catalog=catalog,
                    ),
                    period_year=year,
                    period_month=month,
                )
            )
        month_panels.append((year, month, reports))
        all_reports.extend(reports)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if len(windows) == 1:
        year, month = windows[0]
        heading = f"{year}年{month}月 コミック第1巻 書店特典チェック"
    else:
        heading = "コミック第1巻 書店特典チェック"
    csv_path = args.out_dir / "volume1_privileges.csv"
    html_path = args.out_dir / "volume1_privileges.html"
    write_csv(all_reports, csv_path)
    write_html(all_reports, html_path, heading, month_panels=month_panels)
    print()
    print("完了しました。")
    print(f"  CSV : {csv_path.resolve()}")
    print(f"  HTML: {html_path.resolve()}")
    print("HTMLをブラウザで開くと、月タブと各書店の検索リンクから特典を確認できます。")


if __name__ == "__main__":
    main()
