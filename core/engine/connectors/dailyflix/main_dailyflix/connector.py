from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.parse
from typing import List, Optional

import bs4

from .... import utils, scraping
from ...base import SearchConnector, SearchResult

import logging

LOGGER = logging.getLogger(__name__)


class MainDailyFlix(SearchConnector):

    _base_url_ = "https://main.dailyflix.stream"
    _base_storage_url_ = "https://filemoon.sx/"

    # @classmethod
    # async def execute_deferred(cls, url: str) -> dict:
    #     file_code = url.split('/')[-1]
    #     download_page_url = f"{cls._base_storage_url_}download/{file_code}"
    #     captcha_response = scraping.solve_captcha(download_page_url)
    #     data = {'g-recaptcha-response': captcha_response, 'b': 'download', 'file_code': file_code, 'adb': 0}
    #     result = scraping.post(download_page_url, data=data)
    #     soup = bs4.BeautifulSoup(result.text)
    #     remote_file_url = soup.find('a', {'class': 'button'})['href']
    #     file_url = quart.url_for('proxy', method='get', url=remote_file_url, referer=cls._base_storage_url_)
    #     file_url = url
    #     return dict(file_url=file_url)

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
        url = link['href']
        soup = bs4.BeautifulSoup(scraping.get(url).text)
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
        return cls(original_title=title, url=file_url, image_url=image_url, **kwargs)

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

