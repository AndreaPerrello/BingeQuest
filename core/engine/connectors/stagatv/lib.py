import functools
import re
from typing import Optional, List

import bs4

from ... import scraping, utils


class SeriesEpisode:
    files_dl_base_url = "https://stagatvfiles.com"
    _files_base_url_pattern_ = r"https:\/\/stagatvfiles\.com\/videos\/file\/(?P<data_file>.*)\/.*"

    # noinspection PyTypeChecker
    def __init__(self, series_season, base_soup: bs4.BeautifulSoup):
        self._series_season = series_season
        self._base_soup: bs4.BeautifulSoup = base_soup
        self._item_soup: bs4.BeautifulSoup = None

    @functools.cached_property
    def _full_number(self) -> str:
        return self._base_soup.find('div', {'class': 'epl-num'}).text

    @functools.cached_property
    def number(self) -> Optional[int]:
        episode_match = re.match(r"S.* EP(?P<number>.*[0-9])", self._full_number)
        if not episode_match:
            return
        return int(episode_match['number'].strip())

    @functools.cached_property
    def title(self) -> str:
        return f"{self._series_season.full_title} (E{self.number})"

    @functools.cached_property
    def url(self) -> str:
        return self._base_soup['href']

    def scrape(self):
        self._item_soup = bs4.BeautifulSoup(scraping.get(self.url).text)

    @property
    def file_url(self) -> Optional[str]:
        if not self._item_soup:
            return
        return self._item_soup.find('div', {'class': 'dl-item'}).find('a')['href']

    @property
    def token(self) -> Optional[str]:
        file_url = self.file_url
        if not file_url:
            return
        match = re.match(self._files_base_url_pattern_, file_url)
        if match:
            return match['data_file']


class SeriesSeason:

    _base_url_ = "https://www.stagatv.com"

    # noinspection PyTypeChecker
    def __init__(self, base_soup: bs4.BeautifulSoup):
        self._base_soup: bs4.BeautifulSoup = base_soup
        self._item_soup: bs4.BeautifulSoup = None

    @functools.cached_property
    def full_title(self) -> str:
        return self._base_soup.text

    @functools.cached_property
    def season_number(self) -> int:
        season_match = re.match(r".*\(S(?P<number>[0-9][1-2])\)", self.full_title)
        if season_match:
            return int(season_match['number'])

    @functools.cached_property
    def title(self) -> str:
        return self.full_title.split(f'(S{self.season_number})')[0].strip()

    def scrape(self):
        self._item_soup = bs4.BeautifulSoup(scraping.get(self._base_soup['href']).text)

    @property
    def image_url(self) -> Optional[str]:
        if not self._item_soup:
            return
        return self._item_soup.find('img', {'class': 'ts-post-image', 'alt': self.full_title})['src']

    @property
    def poster_url(self) -> Optional[str]:
        if not self._item_soup:
            return
        gallery_image = self._item_soup.find('div', {'class': 'gallery_img'})
        poster_url = '#'
        if gallery_image:
            poster_url = gallery_image.find('a')['href']
        return poster_url

    def get_episodes(self) -> List[SeriesEpisode]:
        if not self._item_soup:
            return []
        _list = list()
        for episode_li in self._item_soup.find('div', {'class': 'epsdlist'}).find_all('li'):
            episode = SeriesEpisode(self, episode_li.find('a'))
            _list.append(episode)
        return _list

    @classmethod
    def get_all(cls, query: str):
        """
        :rtype List[SeriesSeason]
        :param query:
        :return:
        """
        _list = list()
        # Scrape series list
        url = f"{cls._base_url_}/series-lists/"
        soup = bs4.BeautifulSoup(scraping.get(url).text)
        for item_li in soup.find('div', {'class': 'soralist'}).find_all('li'):
            series_season = cls(item_li.find('a'))
            # Check if the query matches the series title
            if utils.check_in(query, series_season.title):
                series_season.scrape()
                _list.append(series_season)
        return _list
