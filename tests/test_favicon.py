import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from manga_checker.favicon import render_favicon, write_favicon


class FaviconTests(unittest.TestCase):
    def test_is_32px_speech_bubble_with_one(self) -> None:
        img = render_favicon()
        self.assertEqual(img.size, (32, 32))
        self.assertEqual(img.mode, "RGBA")
        px = img.load()
        self.assertEqual(px[0, 0], (0, 0, 0, 0))
        self.assertEqual(px[31, 0], (0, 0, 0, 0))
        self.assertEqual(px[31, 31], (0, 0, 0, 0))
        colors = {px[x, y][:3] for y in range(32) for x in range(32) if px[x, y][3]}
        self.assertIn((0, 0, 0), colors)
        self.assertIn((255, 255, 255), colors)
        self.assertTrue(any(px[x, y][3] == 0 for y in range(32) for x in range(32)))
        digit_black = sum(
            1
            for y in range(6, 20)
            for x in range(12, 20)
            if px[x, y][:3] == (0, 0, 0) and px[x, y][3] == 255
        )
        self.assertGreater(digit_black, 20)

    def test_write_png(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "icon-1.png"
            write_favicon(path)
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 50)
