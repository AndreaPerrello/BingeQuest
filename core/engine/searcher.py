import concurrent.futures
from typing import Optional, Set

import cloudscraper

from .connectors.base import MovieConnector, SearchResult
from . import connectors


class SearchEngine:

    _map: Set[MovieConnector] = {
        connectors.AltaDefinizione,
        connectors.AnimeUnity,
        connectors.StagaTV,
        connectors.DailyFlix,
        # connectors.YouTube,
    }

    def __init__(self, app):
        self._app = app

    async def execute_search(self, query: str) -> SearchResult:
        result: SearchResult = SearchResult()
        if query:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(c.search, query) for c in self._map]
                for future in concurrent.futures.as_completed(futures):
                    search_result: SearchResult = future.result()
                    if search_result:
                        result.merge(search_result)
        return result

    @classmethod
    async def execute_from_hash(cls, media_hash: str) -> Optional[str]:
        content, media_type = MovieConnector.content_from_hash(media_hash)
        for c in cls._map:
            if c.__name__ == media_type:
                return await c.execute(content)

    @classmethod
    async def proxy_post(cls, url: str, **kwargs):
        return cloudscraper.create_scraper().post(url, **kwargs).json()
