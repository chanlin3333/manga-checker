import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from manga_checker.favicon import render_favicon, write_favicon


class FaviconTests(unittest.TestCase):
    def test_is_32px_transparent_png_without_letters(self) -> None:
        img = render_favicon()
        self.assertEqual(img.size, (32, 32))
        self.assertEqual(img.mode, "RGBA")
        px = img.load()
        self.assertEqual(px[0, 0], (0, 0, 0, 0))
        self.assertEqual(px[31, 0], (0, 0, 0, 0))
        self.assertEqual(px[0, 31], (0, 0, 0, 0))
        self.assertEqual(px[31, 31], (0, 0, 0, 0))
        colors = {px[x, y] for y in range(32) for x in range(32) if px[x, y][3]}
        self.assertTrue(any(c[2] > c[0] and c[3] == 255 for c in colors))
        opaque = [(x, y) for y in range(32) for x in range(32) if px[x, y][3]]
        self.assertGreater(len(opaque), 80)

    def test_write_png(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "favicon.png"
            write_favicon(path)
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 50)
