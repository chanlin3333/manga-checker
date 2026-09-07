"""雲（8弁）枠に「1」のファビコン（32x32・透過PNG）。"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

SIZE = 32
BLACK = (0, 0, 0, 255)
WHITE = (255, 255, 255, 255)
ICON_NAME = "icon-2.png"
_SOURCE = Path(__file__).resolve().parent.parent / "assets" / "favicon-source.png"


def _punch_outer_white(img: Image.Image) -> None:
    px = img.load()
    width, height = img.size

    def is_outer_fill(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
        if a == 0:
            return True
        return r >= 230 and g >= 230 and b >= 230

    seen: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque()
    for start in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)):
        queue.append(start)
    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        if not is_outer_fill(x, y):
            continue
        px[x, y] = (0, 0, 0, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))


def _snap(img: Image.Image) -> Image.Image:
    px = img.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = px[x, y]
            if a < 64:
                px[x, y] = (0, 0, 0, 0)
            elif r + g + b < 400:
                px[x, y] = BLACK
            else:
                px[x, y] = WHITE
    return img


def render_favicon() -> Image.Image:
    src = Image.open(_SOURCE).convert("RGBA")
    _punch_outer_white(src)
    bbox = src.getbbox()
    if bbox is None:
        return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cropped = src.crop(bbox)
    side = max(cropped.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    ox = (side - cropped.width) // 2
    oy = (side - cropped.height) // 2
    square.paste(cropped, (ox, oy), cropped)
    fitted = square.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    return _snap(fitted)


def write_favicon(path: Path | None = None) -> Path:
    root = Path(__file__).resolve().parent.parent
    png = render_favicon()
    dest = path or (root / ICON_NAME)
    png.save(dest, format="PNG")
    if path is None:
        png.save(root / "favicon.png", format="PNG")
        png.save(root / "favicon.ico", format="ICO", sizes=[(32, 32)])
    elif dest.suffix.lower() == ".ico":
        png.save(dest, format="ICO", sizes=[(32, 32)])
    return dest
