import json
import urllib.parse
from typing import List, Optional

import bs4

from .utils import get_ratio
from ... import scraping, utils
from ..base import SearchConnector, SearchResult


class StreamingCommunity(SearchConnector):

    children = []

    _base_url_ = "https://streamingcommunity.blue"
    _base_titles_url_ = f"{_base_url_}/titles"

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        """
        Search series-groups on StagaTV and return links to search a StagaTV_Series.
        """
        # Scrape series list
        url = f"{cls._base_url_}/search?q={urllib.parse.quote(query)}"
        soup = bs4.BeautifulSoup(scraping.get(url).text)
        search_result = soup.find('the-search-page')
        if not search_result:
            return
        records = json.loads(search_result['records-json'])
        item_list: List[StreamingCommunity] = list()
        for record in records:
            pseudo_title = ' '.join(x.title() for x in record['slug'].split('-'))
            if utils.check_in(query, pseudo_title):
                resource = f"{record['id']}-{record['slug']}"
                image_ratios = {image['sc_url']: get_ratio(image['sc_url']) for image in record['images']}
                image_url = min(image_ratios, key=image_ratios.get)
                series_url = f"{cls._base_titles_url_}/{resource}"
                series_soup = bs4.BeautifulSoup(scraping.get(series_url).text)
                original_title = series_soup.find('h1', {'class': 'title'}).text
                info = series_soup.find('div', {'class': 'info-span'})
                year = int(info.find('span', {'class': 'desc'}).text.split(' ')[0])
                item = cls(original_title=original_title, url=series_url,
                           image_url=image_url, year=year, lang='it')
                item_list.append(item)
        # Return results
        return SearchResult(item_list)

