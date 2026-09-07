"""ドット絵の本（表紙に「1」）ファビコン（32x32・透過PNG）。"""

from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image

SIZE = 32
ICON_NAME = "icon-3.png"
_SOURCE = Path(__file__).resolve().parent.parent / "assets" / "favicon-source.png"


def _color_delta(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _punch_background(img: Image.Image, max_delta: int) -> None:
    px = img.load()
    width, height = img.size
    corner = px[0, 0]

    def is_bg(x: int, y: int) -> bool:
        pixel = px[x, y]
        if pixel[3] == 0:
            return True
        return _color_delta(pixel, corner) <= max_delta

    seen: set[tuple[int, int]] = set()
    queue: deque[tuple[int, int]] = deque(
        ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
    )
    while queue:
        x, y = queue.popleft()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        if not is_bg(x, y):
            continue
        px[x, y] = (0, 0, 0, 0)
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))


def _clear_light_halo(img: Image.Image) -> None:
    px = img.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = px[x, y]
            if a < 40:
                px[x, y] = (0, 0, 0, 0)
            elif a and min(r, g, b) >= 238 and _color_delta((r, g, b), (r, r, r)) <= 12:
                px[x, y] = (0, 0, 0, 0)


def render_favicon() -> Image.Image:
    src = Image.open(_SOURCE).convert("RGBA")
    _punch_background(src, max_delta=24)
    bbox = src.getbbox()
    if bbox is None:
        return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cropped = src.crop(bbox)
    pad = max(2, side // 40) if (side := max(cropped.size)) else 2
    canvas = Image.new("RGBA", (side + pad * 2, side + pad * 2), (0, 0, 0, 0))
    ox = (canvas.width - cropped.width) // 2
    oy = (canvas.height - cropped.height) // 2
    canvas.paste(cropped, (ox, oy), cropped)
    fitted = canvas.resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    _clear_light_halo(fitted)
    return fitted


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
