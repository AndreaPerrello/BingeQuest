from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Set

import cloudscraper

from .connectors.base import SearchConnector, SearchResult
from .cache import Cache
from . import connectors

import logging
LOGGER = logging.getLogger(__name__)


class SearchEngine:

    _base_map: Set[SearchConnector] = {
        connectors.AltaDefinizione,
        connectors.AnimeUnity,
        connectors.StagaTV,
        connectors.DailyFlix,
        # connectors.YouTube,
    }

    def __init__(self, app):
        self._app = app

    @classmethod
    def _connectors_map(cls, no_children: bool = True):
        def _recursive(parents):
            if not parents:
                return []
            children = []
            if not no_children:
                for i in parents:
                    children += i.children
            return parents + _recursive(children)
        return _recursive(list(cls._base_map))

    def _internal_search(self, c: SearchConnector, *args, **kwargs):
        return c.search(*args, **kwargs)

    async def do_search(self, query: str, uid: str = None) -> SearchResult:
        result: SearchResult = SearchResult()
        if query:
            _map = {c for c in self._connectors_map(not uid) if not uid or c.uid() == uid}
            with ThreadPoolExecutor(max_workers=len(_map)) as executor:
                futures = [executor.submit(self._internal_search, c, query) for c in _map]
                for future in as_completed(futures):
                    search_result: SearchResult = future.result()
                    if search_result:
                        result.merge(search_result)
        return result.sorted()

    @classmethod
    async def execute_from_media_hash(cls, media_hash: str) -> Optional[str]:
        content, media_type = SearchConnector.content_from_hash(media_hash)
        for c in cls._connectors_map(no_children=False):
            if c.uid() == media_type:
                return await c.execute(content)

    @classmethod
    async def proxy_post(cls, url: str, **kwargs) -> dict:
        cache_name = 'proxy_post'
        cache_value = Cache().get(cache_name, url=url, **kwargs)
        if not cache_value:
            cache_value = cloudscraper.create_scraper().post(url, **kwargs).json()
            Cache().set(cache_name, cache_value, url=url, **kwargs)
        return cache_value
