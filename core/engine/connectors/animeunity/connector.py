from typing import List, Optional

import cloudscraper
from bs4 import BeautifulSoup

from ..base import SearchConnector, SearchResult
from .obj_manipulator import format_search_results
from .json_parser import decode_json
from .classes import Anime


class AnimeUnity(SearchConnector):

    base_url = "https://www.animeunity.tv"

    @classmethod
    def _do_search(cls, title: str = "false", type_="false", year="false", order="false",
                   status="false", genres="false", offset=0) -> List[Anime]:
        scraper = cloudscraper.create_scraper()
        payload = {"title": title, "type": type_, "year": year,
                   "order": order, "status": status, "genres": genres,
                   "offset": offset}
        page = scraper.get(f"{cls.base_url}/archivio", params=payload)
        soup = BeautifulSoup(page.content, 'html.parser')
        archive = soup.find('archivio')
        if not archive or 'records' not in archive:
            return []
        return format_search_results(decode_json(archive['records']))

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        anime_list = cls._do_search(title=query, order="Popolarità")
        return SearchResult([cls(anime.main_title, anime.url, anime.thumbnail) for anime in anime_list])

