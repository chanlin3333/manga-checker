"""プロジェクト直下に icon-1.png / favicon.png / favicon.ico を書き出す。"""

from manga_checker.favicon import write_favicon

if __name__ == "__main__":
    out = write_favicon()
    print(f"wrote {out}")
