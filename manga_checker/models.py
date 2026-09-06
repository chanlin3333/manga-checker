from __future__ import annotations

from dataclasses import dataclass, field

from manga_checker.search_title import bare_search_title


@dataclass
class Comic:
    title: str
    volume: str = ""
    author: str = ""
    publisher: str = ""
    pubdate: str = ""
    isbn: str = ""
    source: str = ""
    ndl_url: str = ""
    series: str = ""
    cover_url: str = ""
    cover_source: str = ""
    rakuten_item_url: str = ""
    title_kana: str = ""
    author_kana: str = ""

    @property
    def display_title(self) -> str:
        if self.volume and self.volume not in self.title:
            return f"{self.title} {self.volume}".strip()
        return self.title

    @property
    def search_query(self) -> str:
        return bare_search_title(self.title, self.volume)


@dataclass
class StoreCheck:
    store_id: str
    store_name: str
    status: str
    detail: str
    url: str


@dataclass
class ComicReport:
    comic: Comic
    checks: list[StoreCheck] = field(default_factory=list)
    period_year: int = 0
    period_month: int = 0
