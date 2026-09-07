"""吹き出しに「1」のファビコン（32x32・透過PNG）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 32
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)

# 太めのサンセリフ「1」（8x14）
_DIGIT_ONE = (
    "00111000",
    "01111000",
    "11111000",
    "00111000",
    "00111000",
    "00111000",
    "00111000",
    "00111000",
    "00111000",
    "00111000",
    "00111000",
    "00111000",
    "11111110",
    "11111110",
)


def render_favicon() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.polygon(((4, 21), (13, 21), (2, 30)), fill=BLACK)
    draw.rounded_rectangle((1, 1, 30, 24), radius=8, fill=BLACK)
    draw.polygon(((7, 20), (12, 20), (5, 26)), fill=WHITE)
    draw.rounded_rectangle((5, 5, 26, 20), radius=5, fill=WHITE)

    ox, oy = 12, 6
    px = img.load()
    for row, bits in enumerate(_DIGIT_ONE):
        for col, bit in enumerate(bits):
            if bit == "1":
                px[ox + col, oy + row] = BLACK
    return img


def write_favicon(path: Path | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    dest = path or (root / "favicon.png")
    render_favicon().save(dest, format="PNG")
    return dest
