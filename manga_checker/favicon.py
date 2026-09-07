"""見開きマンガ本のドット絵ファビコン（32x32・透過PNG）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

SIZE = 32
BLUE = (28, 92, 214, 255)
DARK = (14, 48, 138, 255)
SPINE = (20, 64, 176, 255)
PAPER = (255, 252, 246, 255)
INK = (18, 18, 20, 255)


def _put(px, x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < SIZE and 0 <= y < SIZE:
        px[x, y] = color


def _hline(px, x0: int, x1: int, y: int, color) -> None:
    for x in range(min(x0, x1), max(x0, x1) + 1):
        _put(px, x, y, color)


def _vline(px, x: int, y0: int, y1: int, color) -> None:
    for y in range(min(y0, y1), max(y0, y1) + 1):
        _put(px, x, y, color)


def _frame(px, x0: int, y0: int, x1: int, y1: int, color) -> None:
    _hline(px, x0, x1, y0, color)
    _hline(px, x0, x1, y1, color)
    _vline(px, x0, y0, y1, color)
    _vline(px, x1, y0, y1, color)


def render_favicon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    px = img.load()

    top, bottom = 6, 25
    spine_l, spine_r = 15, 16

    for y in range(top + 1, bottom):
        t = (y - (top + 1)) / float((bottom - 1) - (top + 1) or 1)
        left_outer = int(round(5 - t * 3))
        right_outer = int(round(26 + t * 3))
        for x in range(left_outer, spine_l):
            _put(px, x, y, PAPER)
        for x in range(spine_r + 1, right_outer + 1):
            _put(px, x, y, PAPER)
        _put(px, spine_l, y, DARK)
        _put(px, spine_r, y, DARK)
        _put(px, left_outer, y, BLUE)
        _put(px, right_outer, y, BLUE)

    _hline(px, 5, 14, top, BLUE)
    _hline(px, 17, 26, top, BLUE)
    _put(px, spine_l, top, BLUE)
    _put(px, spine_r, top, BLUE)
    _hline(px, 2, 14, bottom, BLUE)
    _hline(px, 17, 29, bottom, BLUE)
    _put(px, spine_l, bottom, BLUE)
    _put(px, spine_r, bottom, BLUE)
    _put(px, 4, top, BLUE)
    _put(px, 27, top, BLUE)

    _frame(px, 6, 8, 13, 14, INK)
    _frame(px, 5, 16, 13, 23, INK)
    _frame(px, 18, 8, 25, 14, INK)
    _frame(px, 18, 16, 26, 23, INK)
    return img


def write_favicon(path: Path | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    dest = path or (root / "favicon.png")
    render_favicon().save(dest, format="PNG")
    return dest
