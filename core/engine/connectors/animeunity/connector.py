import base64
import json
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from ... import scraping
from ..base import SearchConnector, SearchResult
from .classes import Anime, Episode, Related


class AnimeUnity(SearchConnector):

    # TODO: extract anime episodes and put in seasons and episode selector
    # TODO: get the download URL and put in deferred player

    base_url = "https://www.animeunity.tv"

    @staticmethod
    def _format_search_results(json_string):
        forbidden_chars = [{'old': '\n', 'new': '\u2424'}, {'old': '\/', 'new': '/'}, {'old': '\'', 'new': '%27'}]
        for char in forbidden_chars:
            json_string = str.replace(json_string, char['old'], char['new'])
        res_obj = json.loads(json_string)
        if not isinstance(res_obj, type([])):
            res_obj = [res_obj]
        anime_list: List[Anime] = []
        for anime_ob in res_obj:
            anime = Anime(anime_ob['id'], anime_ob['title'], anime_ob['type'], anime_ob['episodes_length'])
            anime.status = anime_ob['status']
            anime.year = anime_ob['date']
            anime.slug = anime_ob['slug']
            anime.title_eng = anime_ob['title_eng']
            anime.cover_image = anime_ob['imageurl_cover']
            anime.thumbnail = anime_ob['imageurl']
            anime.episodes = []
            for ep in anime_ob['episodes']:
                episode = Episode(ep['id'], ep['number'], ep['created_at'], ep['link'])
                anime.episodes.append(episode)
            if 'related' in anime_ob:
                anime.related = []
                for rel in anime_ob['related']:
                    anime.related.append(Related(rel['id'], rel['type'], rel['title'], rel['slug']))
            anime_list.append(anime)
        anime_list.sort(key=lambda a: a.year)
        return anime_list

    @classmethod
    def _do_search(cls, title: str = "false", type_="false", year="false", order="false",
                   status="false", genres="false", offset=0) -> List[Anime]:
        payload = {"title": title, "type": type_, "year": year,
                   "order": order, "status": status, "genres": genres,
                   "offset": offset}
        page = scraping.get(f"{cls.base_url}/archivio", params=payload)
        soup = BeautifulSoup(page.content, 'html.parser')
        archive = soup.find('archivio')
        if not archive or 'records' not in archive.attrs:
            return []
        return cls._format_search_results(archive.attrs['records'])

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        anime_list = cls._do_search(title=query, order="Popolarità")
        _list = list()
        for anime in anime_list:
            # image_base64 = base64.b64encode(requests.get(anime.cover_image).content)
            # ext = anime.thumbnail.split('.')[-1]
            # image_url = f'data:image/{ext};base64, {image_base64.decode()}'
            image_url = anime.thumbnail
            item = cls(
                original_title=anime.main_title, url=anime.url,
                image_url=image_url, lang='it'
            )
            _list.append(item)
        return SearchResult(_list)

