import unittest

from manga_checker.dates import format_release_date, iter_months, prefer_pubdate
from manga_checker.official import OfficialHit, OfficialIndex, lookup_status
from manga_checker.privilege import STATUS_NO, STATUS_YES


class DateFormatTests(unittest.TestCase):
    def test_full_date_with_weekday(self) -> None:
        self.assertEqual(format_release_date("20260927"), "2026/09/27 (日)")
        self.assertEqual(format_release_date("2026-09-27"), "2026/09/27 (日)")

    def test_year_month_only(self) -> None:
        self.assertEqual(format_release_date("2026.9"), "2026/09")

    def test_iter_months_four_from_september(self) -> None:
        self.assertEqual(
            iter_months(2026, 9, 4),
            [(2026, 9), (2026, 10), (2026, 11), (2026, 12)],
        )

    def test_iter_months_wraps_year(self) -> None:
        self.assertEqual(
            iter_months(2026, 11, 4),
            [(2026, 11), (2026, 12), (2027, 1), (2027, 2)],
        )

    def test_prefer_full_openbd_date(self) -> None:
        self.assertEqual(prefer_pubdate("2026.9", "20260927"), "20260927")

    def test_openbd_onix_date_is_preferred(self) -> None:
        from manga_checker.openbd import _record_pubdates

        record = {
            "summary": {"pubdate": "2026.9"},
            "onix": {
                "PublishingDetail": {
                    "PublishingDate": {"PublishingDateRole": "01", "Date": "20260927"}
                }
            },
        }
        self.assertIn("20260927", _record_pubdates(record))
    def test_openbd_publication_date_alias(self) -> None:
        from manga_checker.retail_dates import collect_onix_pubdates

        record = {
            "onix": {
                "PublishingDetail": {
                    "PublicationDate": {"Date": "20260827"}
                }
            }
        }
        self.assertIn("20260827", collect_onix_pubdates(record))
        self.assertEqual(format_release_date("20260827"), "2026/08/27 (木)")

    def test_retail_html_release_date(self) -> None:
        from manga_checker.retail_dates import parse_retail_pubdate

        html = """
        <script type="application/ld+json">
        {"@type":"Book","datePublished":"2026-08-27"}
        </script>
        <th>発売日</th><td>2026年08月27日</td>
        """
        self.assertEqual(parse_retail_pubdate(html), "2026-08-27")


class KikuyaLookupTests(unittest.TestCase):
    def test_hit_uses_search_fallback_url(self) -> None:
        index = OfficialIndex()
        index.loaded = True
        index.entries["kikuya"] = [
            OfficialHit(
                "kikuya",
                "『初凪ヒメリウム』喜久屋書店限定特典",
                "https://kikuyashoten.myshopify.com/products/example",
                ["喜久屋特典"],
            )
        ]
        fallback = "https://kikuyashoten.myshopify.com/search?q=test"
        status, _, url = lookup_status(index, "kikuya", "初凪ヒメリウム", "", fallback)
        self.assertEqual(status, STATUS_YES)
        self.assertEqual(url, fallback)

    def test_miss_uses_inventory_search(self) -> None:
        index = OfficialIndex()
        index.loaded = True
        fallback = "https://kikuyashoten.myshopify.com/search?q=test"
        status, _, url = lookup_status(index, "kikuya", "存在しない作品", "", fallback)
        self.assertEqual(status, STATUS_NO)
        self.assertEqual(url, fallback)
