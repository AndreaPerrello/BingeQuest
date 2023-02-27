import functools
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Set

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
        # connectors.MainDailyFlix,
        connectors.StreamingCommunity,
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

    def _internal_search(self, q: str, c: SearchConnector):
        return c.search(q)

    @classmethod
    def _all_connectors(cls, uid: str = None) -> Set[SearchConnector]:
        return {c for c in cls._connectors_map(not uid) if not uid or c.uid() == uid}

    @classmethod
    def _get_connector_from_uid(cls, uid: str) -> SearchConnector:
        for c in cls._connectors_map(not uid):
            if c.uid() == uid:
                return c

    async def do_search(self, query: str, uid: str = None) -> SearchResult:
        result: SearchResult = SearchResult()
        if query:
            _map = self._all_connectors(uid)
            partial = functools.partial(self._internal_search, query)
            with ThreadPoolExecutor(max_workers=len(_map)) as p:
                for r in p.map(partial, _map):
                    result.merge(r)
        return result.sorted()

    @classmethod
    async def execute_from_media_hash(cls, media_hash: str) -> Optional[str]:
        content, media_type = SearchConnector.content_from_hash(media_hash)
        for c in cls._connectors_map(no_children=False):
            if c.uid() == media_type:
                return await c.execute(content)

    @classmethod
    async def defer(cls, uid: str, **kwargs) -> dict:
        cache_name = 'proxy_post'
        cache_value = Cache().get(cache_name, **kwargs)
        if not cache_value:
            connector = cls._get_connector_from_uid(uid)
            if not connector:
                raise ValueError('Could not parse the request.')
            cache_value = await connector.execute_deferred(**kwargs)
            if cache_value:
                Cache().set(cache_name, cache_value, **kwargs)
        return cache_value
