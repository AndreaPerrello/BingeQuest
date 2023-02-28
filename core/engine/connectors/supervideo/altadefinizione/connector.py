from typing import Optional, List

from ..connector import SuperVideo
from ...base import SearchConnector
from .... import scraping


class AltaDefinizione(SuperVideo):

    _base_url_ = 'https://altadefinizione.navy'

    @classmethod
    def _get_wrappers(cls, soup) -> List:
        return soup.find_all('div', 'wrapperImage')

    @staticmethod
    def _extract_item_details(item_soup):
        details = {}
        for li in item_soup.find('ul', {'id': 'details'}).find_all('li'):
            label = li.find('label')
            key = label.text.split(':')[0].strip()
            span = li.find('span')
            if span:
                if span['id'] == 'staring':
                    value = [a.text for a in span.find_all('a')]
                else:
                    value = span.attrs['data-value']
            else:
                a = li.find('a')
                if a:
                    value = a.text
                else:
                    value = int(li.text.split('\n')[-1])
            details[key] = value
        return details

    @classmethod
    def _scrape_item(cls, wrapper) -> Optional[SearchConnector]:
        a = wrapper.find('a')
        image_url = a.find('img').attrs['src']
        item_url = a.attrs['href']
        title = wrapper.find('div', {'class': 'info'}).find('h2', {'class': 'titleFilm'}).find('a').text
        item_soup = scraping.get_soup(item_url)
        details = cls._extract_item_details(item_soup)
        year = details['Anno']
        return cls(original_title=title, url=item_url, image_url=image_url, year=year, lang='it')
