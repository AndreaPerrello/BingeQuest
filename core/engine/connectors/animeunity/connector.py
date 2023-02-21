from typing import List, Optional

import cloudscraper
from bs4 import BeautifulSoup
from pathlib import Path

from ..base import MovieConnector, SearchResult
from .obj_manipulator import get_formatted_search_results
from .classes import Anime
from . import json_parser

file_log = False
base_path = Path('./doc/templates')
defined_anime_types = ['TV', 'OVA', 'ONA', 'Movie', 'Special']


class AnimeUnity(MovieConnector):

    base_url = "https://www.animeunity.tv"

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        results = cls._search(title=query, order="Popolarità")
        return SearchResult([cls(anime.main_title, anime.url, anime.thumbnail) for anime in results])

    @classmethod
    def _search(cls, title="false", type_="false", year="false", order="false",
                status="false", genres="false", offset=0) -> List[Anime]:
        scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
        payload = {"title": title, "type": type_, "year": year,
                   "order": order, "status": status, "genres": genres,
                   "offset": offset}
        page = scraper.get(f"{cls.base_url}/archivio", params=payload)
        soup = BeautifulSoup(page.content, 'html.parser')
        anime_json = soup.find('archivio')['records']
        search_obj = get_formatted_search_results(json_parser.decode_json(anime_json))
        return search_obj

    @classmethod
    def anime_page_scraper(cls, url):
        scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
        page = scraper.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        anime_info = soup.find('video-player')
        anime_json = anime_info['anime']
        anime_obj = get_formatted_search_results(json_parser.decode_json(anime_json))
        return anime_obj[0]

    @classmethod
    def season_scraper(cls, anime, config=None):
        if config['season'] is not None:
            if not isinstance(anime, Anime):
                anime = anime[0]
            anime = cls.anime_page_scraper(anime.get_anime_url())
            anime_list = []
            if ('ALL' in config['season']) or (anime.type in config['season']):
                anime_list.append(anime)
            for rel in anime.related:
                if rel.a_id == anime.a_id:
                    continue
                if ('ALL' in config['season']) or (rel.type in config['season']):
                    anime_elem = cls.anime_page_scraper(rel.get_anime_url())
                    anime_list.append(anime_elem)
            return anime_list
