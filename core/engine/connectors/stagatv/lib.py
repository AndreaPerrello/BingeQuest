import functools
import re
from typing import Optional, List, Generator

import bs4

from iotech.utils import dt
from ... import scraping, utils


class SeriesSeasonEpisode:
    files_dl_base_url = "https://stagatvfiles.com"
    files_base_url_pattern = r"https:\/\/stagatvfiles\.com\/videos\/file\/(?P<data_file>.*)\/.*"

    # noinspection PyTypeChecker
    def __init__(self, series_season, season_string: str, base_soup: bs4.BeautifulSoup):
        self._series_season = series_season
        self._season_string = season_string
        self._base_soup: bs4.BeautifulSoup = base_soup
        self._item_soup: bs4.BeautifulSoup = None

    @functools.cached_property
    def _full_number(self) -> str:
        return self._base_soup.find('div', {'class': 'epl-num'}).text

    @functools.cached_property
    def season_number(self) -> Optional[int]:
        match = re.match(r"Season (?P<number>.*[0-9])", self._season_string)
        if not match:
            return
        return int(match['number'].strip())

    @functools.cached_property
    def episode_number(self) -> Optional[int]:
        match = re.match(r"S.* EP(?P<number>.*[0-9])", self._full_number)
        if not match:
            return
        return int(match['number'].strip())

    @functools.cached_property
    def title(self) -> str:
        return f"{self.clean_title} ({self.details_string})"

    @functools.cached_property
    def clean_title(self) -> str:
        return self._series_season.full_title.split('(')[0].strip()

    @functools.cached_property
    def details_string(self) -> str:
        return f"S{self.season_number} E{str(self.episode_number).zfill(2)}"

    @functools.cached_property
    def url(self) -> str:
        return self._base_soup['href']


class Series:

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
        return self.full_title.split(f'(S')[0].strip()

    # Scraped properties

    def scrape(self):
        self._item_soup = bs4.BeautifulSoup(scraping.get(self._base_soup['href']).text)

    @property
    def image_url(self) -> Optional[str]:
        if not self._item_soup:
            return
        return self._item_soup.find('img', {'class': 'ts-post-image', 'alt': self.full_title})['src']

    @property
    def year(self) -> Optional[int]:
        if not self._item_soup:
            return
        date_time = self._item_soup.find('time', {'itemprop': 'dateCreated'})['datetime']
        return dt.datetime.from_iso(date_time).year

    @property
    def poster_url(self) -> Optional[str]:
        if not self._item_soup:
            return
        gallery_image = self._item_soup.find('div', {'class': 'gallery_img'})
        poster_url = '#'
        if gallery_image:
            poster_url = gallery_image.find('a')['href']
        return poster_url

    def get_seasons_episodes(self) -> List[SeriesSeasonEpisode]:
        if not self._item_soup:
            return []
        _list = list()
        box = self._item_soup.find('div', {'class': 'bixbox ts-ep-list'})
        spans = [s.text for s in box.find_all('span', {'class': 'ts-chl-collapsible'})]
        divs = [d.find('div', 'epsdlist') for d in box.find_all('div', {'class': 'ts-chl-collapsible-content'})]
        for season_string, episode_list in zip(spans, divs):
            for episode_li in episode_list.find_all('li'):
                episode = SeriesSeasonEpisode(self, season_string, episode_li.find('a'))
                _list.append(episode)
        return _list

    @classmethod
    def _yield_all_list_items(cls, query: str) -> List:
        # Scrape series list
        url = f"{cls._base_url_}/series-lists/"
        soup = bs4.BeautifulSoup(scraping.get(url, cloud=False).text)
        seasons_list = soup.find('div', {'class': 'soralist'})
        # Yield items which title matches the query
        return seasons_list.findAll(lambda t: t.name == 'li' and utils.check_in(query, t.text))

    @classmethod
    def get_uniques(cls, query: str) -> List:
        """
        :rtype List[SeriesSeason]
        :param query:
        :return:
        """
        _items = dict()
        # Scrape series list
        for item_li in cls._yield_all_list_items(query):
            item = cls(item_li.find('a'))
            _item_id = item.title
            if _item_id not in _items:
                _items[_item_id] = item
        return list(_items.values())

    @classmethod
    def get_all(cls, query: str) -> List:
        """
        :rtype List[SeriesSeason]
        :param query:
        :return:
        """
        return [cls(item_li.find('a')) for item_li in cls._yield_all_list_items(query)]
