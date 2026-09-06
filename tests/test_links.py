import unittest

from manga_checker.links import amazon_url, rakuten_url


class LinkTests(unittest.TestCase):
    def tearDown(self) -> None:
        from manga_checker import config

        config._CACHE = None

    def test_isbn_search_query_prefers_13_digits(self) -> None:
        from manga_checker.links import isbn_search_query

        self.assertEqual(isbn_search_query("978-4-08-885231-7"), "9784088852317")
        self.assertEqual(isbn_search_query(""), "")
        from manga_checker import config

        config._CACHE = {"amazon_tag": "", "rakuten_affiliate_id": ""}
        url = rakuten_url("9784000000000", "タイトル")
        self.assertIn("books.rakuten.co.jp/search", url)
        self.assertIn("9784000000000", url)

    def test_amazon_tag_appended(self) -> None:
        from manga_checker import config

        config._CACHE = {"amazon_tag": "mytag-22", "rakuten_affiliate_id": ""}
        url = amazon_url("9784065338339", "テスト")
        self.assertIn("tag=mytag-22", url)
