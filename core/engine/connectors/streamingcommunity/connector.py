import functools
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from .utils import get_ratio
from ... import scraping, utils
from ..base import SearchConnector, SearchResult

import logging
LOGGER = logging.getLogger(__name__)


class _Series:

    def __init__(self, title, image_url: str, series_url: str, year: int):
        self.title = title
        self.image_url = image_url
        self.series_url = series_url
        self.year = year


class StreamingCommunity(SearchConnector):

    children = []

    _base_url_ = "https://streamingcommunity.blue"
    _base_titles_url_ = f"{_base_url_}/titles"

    @classmethod
    def _unpack(cls, query: str, record: dict):
        pseudo_title = ' '.join(x.title() for x in record['slug'].split('-'))
        if utils.check_in(query, pseudo_title):
            resource = f"{record['id']}-{record['slug']}"
            image_ratios = {image['sc_url']: get_ratio(image['sc_url']) for image in record['images']}
            image_url = min(image_ratios, key=image_ratios.get)
            series_url = f"{cls._base_titles_url_}/{resource}"
            series_soup = scraping.get_soup(series_url)
            original_title = series_soup.find('h1', {'class': 'title'}).text
            info = series_soup.find('div', {'class': 'info-span'})
            year = int(info.find('span', {'class': 'desc'}).text.split(' ')[0])
            return _Series(original_title, image_url, series_url, year)

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        """
        Search series-groups on StagaTV and return links to search a StagaTV_Series.
        """
        # Scrape series list
        url = f"{cls._base_url_}/search?q={urllib.parse.quote(query)}"
        soup = scraping.get_soup(url)
        search_result = soup.find('the-search-page')
        if not search_result:
            return
        records = json.loads(search_result['records-json'])
        item_list: List[StreamingCommunity] = list()
        partial = functools.partial(cls._unpack, query)
        with ThreadPoolExecutor(5) as p:
            for series in p.map(partial, records):
                if series:
                    item_list.append(cls(
                        original_title=series.title, url=series.series_url,
                        image_url=series.image_url, year=series.year, lang='it'
                    ))
        # Return results
        return SearchResult(item_list)

