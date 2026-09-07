"""プロジェクト直下に favicon.png を書き出す。"""

from pathlib import Path

from manga_checker.favicon import write_favicon

if __name__ == "__main__":
    out = write_favicon(Path(__file__).resolve().parent / "favicon.png")
    print(f"wrote {out}")
