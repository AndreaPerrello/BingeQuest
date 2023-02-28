from typing import Optional, List

from ..connector import SuperVideo
from ...base import SearchConnector


class Cb01(SuperVideo):

    _base_url_ = 'https://cb01.taxi'

    @classmethod
    def _get_wrappers(cls, soup) -> List:
        return soup.find_all('div', {'class': 'mp-post'})

    @classmethod
    def _scrape_item(cls, wrapper) -> Optional[SearchConnector]:
        a = wrapper.find('a')
        image = a.find('img')
        image_url = image.attrs['src']
        item_url = a.attrs['href']
        original_title = image['alt']
        split = original_title.split('(')
        title = split[0]
        year = split[1].replace(')', '')
        return cls(original_title=title, url=item_url, image_url=image_url, year=year, lang='it')