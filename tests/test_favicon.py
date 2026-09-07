import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from manga_checker.favicon import render_favicon, write_favicon


class FaviconTests(unittest.TestCase):
    def test_is_32px_cloud_one_icon(self) -> None:
        img = render_favicon()
        self.assertEqual(img.size, (32, 32))
        self.assertEqual(img.mode, "RGBA")
        px = img.load()
        self.assertEqual(px[0, 0][3], 0)
        self.assertEqual(px[31, 0][3], 0)
        self.assertEqual(px[0, 31][3], 0)
        self.assertEqual(px[31, 31][3], 0)
        colors = {px[x, y][:3] for y in range(32) for x in range(32) if px[x, y][3]}
        self.assertIn((0, 0, 0), colors)
        self.assertIn((255, 255, 255), colors)
        center_black = sum(
            1
            for y in range(10, 22)
            for x in range(12, 20)
            if px[x, y][:3] == (0, 0, 0) and px[x, y][3] == 255
        )
        self.assertGreater(center_black, 10)

    def test_write_png(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon-2.png"
            write_favicon(path)
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 50)
