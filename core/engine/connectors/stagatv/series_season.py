import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import bs4

from ..base import SearchConnector, SearchResult
from .lib import Series, SeriesSeasonEpisode
from ... import security, scraping


class StagaTV_SeriesSeason(SearchConnector):

    def __init__(self, poster_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._poster_url: str = poster_url

    def get_content(self) -> dict:
        return {'title': self._base_title, 'url': self.url, 'details': self._details, 'poster': self._poster_url}

    @classmethod
    async def execute_deferred(cls, url: str, data: dict, **kwargs) -> dict:
        response = scraping.post(url, data=data).json()
        if response:
            return dict(file_url=response['file'])

    @classmethod
    async def execute(cls, content: dict):
        kwargs = dict()
        url = content['url']
        soup = bs4.BeautifulSoup(scraping.get(url).text)
        file_url = soup.find('div', {'class': 'dl-item'}).find('a')['href']
        match = re.match(SeriesSeasonEpisode.files_base_url_pattern, file_url)
        if match:
            token = match['data_file']
            kwargs['data'] = {'token': token, 'api': '1'}
        else:
            kwargs['data'] = {}
            kwargs['error'] = 'Episode file not found'
        poster = content['poster']
        return await cls.render_player_deferred(
            title=content['title'], details=content['details'],
            url=file_url, player_poster_url=poster,
            player_src_base_url=SeriesSeasonEpisode.files_dl_base_url, **kwargs)

    @classmethod
    def _search_season_episodes(cls, series: Series):
        _list = list()
        series.scrape()
        episodes = series.get_seasons_episodes()
        # with ThreadPoolExecutor(max_workers=len(episodes)) as p:
        #     futures = [p.submit(e.scrape) for e in episodes]
        #     wait(futures)
        for episode in episodes:
            _list.append(cls(
                original_title=episode.title, details=episode.details_string,
                base_title=series.title, image_url=series.image_url,
                poster_url=series.poster_url, url=episode.url))
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
