from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
from typing import List, Optional

import bs4

from ... import utils, scraping
from ..base import SearchConnector, SearchResult

import logging
LOGGER = logging.getLogger(__name__)


class MainDailyFlix(SearchConnector):

    # TODO: Manage WatchDailyFlix for TV series

    _base_url_ = "https://main.dailyflix.stream"

    @classmethod
    async def execute(cls, content: dict):
        return utils.new_tab(content['url'])

    @classmethod
    def _scrape_tr(cls, tr):
        td = tr.find('td')
        if not td:
            return
        link = td.find('a')
        if not link:
            return
        title = link.text
        url = link['href']
        soup = bs4.BeautifulSoup(scraping.get(url).text)
        breadcrumbs = [a.text for a in soup.findAll(
            lambda tag: tag.name == 'a' and 'rel' in tag.attrs and 'tag' in tag.attrs['rel'])]
        if 'TV' in breadcrumbs:
            return
        year = int(breadcrumbs[2].replace('#', ''))
        iframe = soup.find('iframe')
        if not iframe:
            return
        file_url = iframe['src'].split('<')[0].strip()
        posters = soup.findAll(
            lambda tag: tag.name == 'img' and 'aria-label' in tag.attrs
                        and tag.attrs['aria-label'].startswith('Poster'))
        if posters:
            image_url = posters[0]['src']
        else:
            image_url = None
        return cls(original_title=title, url=file_url, image_url=image_url, year=year)

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        main_items: List[MainDailyFlix] = list()
        secondary_items: List[MainDailyFlix] = list()
        # Scrape items list
        url = f"{cls._base_url_}/?s={urllib.parse.quote(query)}"
        soup = bs4.BeautifulSoup(scraping.get(url).text)
        table = soup.find('table', {'class': 'table'})
        if not table:
            return
        # Multiprocess table items
        trs = table.find_all('tr')
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(cls._scrape_tr, tr) for tr in trs]
            for future in as_completed(futures):
                item = future.result()
                if item:
                    if utils.check_in(query, item.title):
                        main_items.append(item)
                    else:
                        secondary_items.append(item)
        # Return results
        return SearchResult(main_items, secondary_items)

