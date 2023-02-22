from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
from typing import List, Optional

import bs4
import cloudscraper

from ..utils import check_in
from ...utils import new_tab
from ..base import SearchConnector, SearchResult

import logging
LOGGER = logging.getLogger(__name__)

scraper = cloudscraper.create_scraper()


class DailyFlix(SearchConnector):

    _base_url_ = "https://main.dailyflix.stream"

    @classmethod
    async def execute(cls, content: dict):
        return new_tab(content['url'])

    @classmethod
    def _scrape_td(cls, td):
        link = td.find('a')
        if not link:
            return
        title = link.text
        url = link['href']
        soup = bs4.BeautifulSoup(scraper.get(url).text)
        file_frame = soup.find('iframe')
        if not file_frame:
            return
        file_url = file_frame['src'].split('<')[0].strip()
        poster = soup.find('div', {'class': 'poster_parent'})
        if not poster:
            return
        poster_style = poster['style']
        image_url = poster_style.strip().split(',')[1].strip().replace('url(', '').replace(')', '')
        return cls(title, url=file_url, image_url=image_url)

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        main_items: List[DailyFlix] = list()
        secondary_items: List[DailyFlix] = list()
        # Scrape items list
        url = f"{cls._base_url_}/?s={urllib.parse.quote(query)}"
        soup = bs4.BeautifulSoup(scraper.get(url).text)
        table = soup.find('table', {'class': 'table'})
        if not table:
            return
        # Multiprocess table items
        tds = table.find_all('td')
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(cls._scrape_td, td) for td in tds]
            for future in as_completed(futures):
                item = future.result()
                if item:
                    if check_in(query, item.title):
                        main_items.append(item)
                    else:
                        secondary_items.append(item)
        # Return results
        return SearchResult(main_items, secondary_items)

