import unittest
import xml.etree.ElementTree as ET

from manga_checker.catalog import _parse_ndl_item


SAMPLE = """
<item xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:dcndl="http://ndl.go.jp/dcndl/terms/"
      xmlns:dcterms="http://purl.org/dc/terms/"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <title>リベンジアクト</title>
  <link>https://ndlsearch.ndl.go.jp/books/example</link>
  <dc:title>リベンジアクト</dc:title>
  <dc:creator>作者</dc:creator>
  <dcndl:volume>第1巻</dcndl:volume>
  <dc:publisher>出版社</dc:publisher>
  <dcterms:issued>2026.9</dcterms:issued>
  <dc:identifier xsi:type="dcndl:ISBN">978-4-0000-0000-0</dc:identifier>
</item>
"""


class CatalogParseTests(unittest.TestCase):
    def test_parse_ndl_item(self) -> None:
        item = ET.fromstring(SAMPLE)
        comic = _parse_ndl_item(item)
        self.assertIsNotNone(comic)
        assert comic is not None
        self.assertEqual(comic.title, "リベンジアクト")
        self.assertEqual(comic.volume, "第1巻")
        self.assertEqual(comic.isbn, "9784000000000")
        self.assertEqual(comic.publisher, "出版社")


if __name__ == "__main__":
    unittest.main()
