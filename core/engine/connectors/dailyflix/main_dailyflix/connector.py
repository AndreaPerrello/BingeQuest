from concurrent.futures import ThreadPoolExecutor
import urllib.parse
from typing import List, Optional

from .... import utils, scraping
from ...base import SearchConnector, SearchResult

import logging

LOGGER = logging.getLogger(__name__)


class MainDailyFlix(SearchConnector):

    _base_url_ = "https://main.dailyflix.stream"
    _base_storage_url_ = "https://filemoon.sx/"
    _untrusted_source_url = 'https://playhydrax.com'

    @classmethod
    async def execute(cls, content: dict):
        return cls.new_tab(content['url'])

    @classmethod
    def _scrape_tr(cls, tr):
        td = tr.find('td')
        if not td:
            return
        link = td.find('a')
        if not link:
            return
        title = link.text
        soup = scraping.get_soup(link['href'])
        iframe = soup.find('iframe')
        if not iframe:
            return
        file_url = iframe['src'].split('<')[0].strip()
        if file_url.startswith(cls._untrusted_source_url):
            return
        breadcrumbs = [a.text for a in soup.findAll(
            lambda tag: tag.name == 'a' and 'rel' in tag.attrs and 'tag' in tag.attrs['rel'])]
        if 'TV' in breadcrumbs:
            return
        kwargs = dict()
        for b in breadcrumbs:
            try:
                kwargs['year'] = int(b.replace('#', ''))
            except:
                pass
        posters = soup.findAll(
            lambda tag: tag.name == 'img' and 'aria-label' in tag.attrs
                        and tag.attrs['aria-label'].startswith('Poster'))
        if posters:
            image_url = posters[0]['src']
        else:
            image_url = None
        return cls(original_title=title, url=file_url, image_url=image_url, **kwargs)

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        main_items: List[MainDailyFlix] = list()
        secondary_items: List[MainDailyFlix] = list()
        # Scrape items list
        soup = scraping.get_soup(f"{cls._base_url_}/?s={urllib.parse.quote(query)}")
        table = soup.find('table', {'class': 'table'})
        if not table:
            return
        # Multiprocess table items
        trs = table.find_all('tr')
        with ThreadPoolExecutor(max_workers=10) as p:
            for item in p.map(cls._scrape_tr, trs):
                if item:
                    if utils.check_in(query, item.title):
                        main_items.append(item)
                    else:
                        secondary_items.append(item)
        # Return results
        return SearchResult(main_items, secondary_items)

