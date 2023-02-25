from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from typing import List

from ..base import SearchConnector, SearchResult
from .lib import Series, SeriesSeasonEpisode
from ... import security, scraping


class StagaTV_SeriesSeason(SearchConnector):

    def __init__(self, poster_url: str, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._poster_url: str = poster_url
        self._token: str = token

    def get_content(self) -> dict:
        return {'title': self._base_title, 'url': self.url, 'details': self._details,
                'poster_url': self._poster_url, 'token': self._token}

    @classmethod
    async def execute_deferred(cls, url: str, data: dict, **kwargs) -> dict:
        response = scraping.post(url, data=data).json()
        if response:
            return dict(file_url=response['file'])

    @classmethod
    async def execute(cls, content: dict):
        url = content['url']
        data = {'token': content['token'], 'api': '1'}
        poster = content['poster_url']
        return await cls.render_player_deferred(
            title=content['title'], details=content['details'],
            url=url, data=data, player_poster_url=poster,
            player_src_base_url=SeriesSeasonEpisode.files_dl_base_url)

    @classmethod
    def _search_season_episodes(cls, series: Series):
        _list = list()
        series.scrape()
        episodes = series.get_seasons_episodes()
        with ThreadPoolExecutor(max_workers=len(episodes)) as executor:
            futures = [executor.submit(e.scrape) for e in episodes]
            wait(futures)
        for episode in episodes:
            _list.append(cls(
                original_title=episode.title, details=episode.details_string,
                base_title=series.title, url=episode.file_url,
                image_url=series.image_url, poster_url=series.poster_url,
                token=episode.token))
        return _list

    @classmethod
    def search(cls, query: str) -> SearchResult:
        _list = list()
        series_list = Series.get_all(query)
        with ThreadPoolExecutor(max_workers=len(series_list)) as executor:
            futures = [executor.submit(cls._search_season_episodes, s) for s in series_list]
            for future in as_completed(futures):
                search_result: List[cls] = future.result()
                _list += search_result
        # Return results
        return SearchResult(_list)


class StagaTV_Series(SearchConnector):

    children = [StagaTV_SeriesSeason]

    @property
    def link(self) -> str:
        return security.url_for('search', q=self.query_title, u=StagaTV_SeriesSeason.uid())

    @classmethod
    def search(cls, query: str) -> SearchResult:
        _list = list()
        for series in Series.get_all(query):  # type: Series
            series.scrape()
            item = cls(original_title=series.full_title, image_url=series.image_url)
            _list.append(item)
        # Return results
        return SearchResult(_list)
