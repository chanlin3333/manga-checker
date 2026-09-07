import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from manga_checker.favicon import render_favicon, write_favicon


class FaviconTests(unittest.TestCase):
    def test_is_32px_book_icon(self) -> None:
        img = render_favicon()
        self.assertEqual(img.size, (32, 32))
        self.assertEqual(img.mode, "RGBA")
        px = img.load()
        self.assertEqual(px[0, 0][3], 0)
        self.assertEqual(px[31, 0][3], 0)
        self.assertEqual(px[0, 31][3], 0)
        self.assertEqual(px[31, 31][3], 0)
        opaque = [px[x, y] for y in range(32) for x in range(32) if px[x, y][3] > 64]
        self.assertGreater(len(opaque), 80)
        self.assertTrue(any(c[2] > c[0] + 15 for c in opaque))

    def test_write_png(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon-3.png"
            write_favicon(path)
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 50)
