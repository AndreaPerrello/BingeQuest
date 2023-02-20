import concurrent.futures
from typing import Optional

from .movie import MovieConnector, SearchResult
from . import connectors


class SearchEngine:

    _map = {
        connectors.AltaDefinizione,
        connectors.AnimeUnity,
        # connectors.YouTube,
    }

    def __init__(self, app):
        self._app = app

    async def search(self, query: str) -> SearchResult:
        result: SearchResult = SearchResult()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(c.search, query) for c in self._map]
            for future in concurrent.futures.as_completed(futures):
                search_result: SearchResult = future.result()
                if search_result:
                    result.merge(search_result)
        return result

    @classmethod
    def get_link(cls, media_hash: str) -> Optional[str]:
        original_url, media_type = MovieConnector.content_from_hash(media_hash)
        for c in cls._map:
            if c.__name__ == media_type:
                return c.get_link(original_url)
