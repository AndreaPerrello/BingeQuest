from typing import Optional, Tuple, Union

import bs4

from ... import utils, scraping
from ..base import SearchConnector, SearchResult


class AltaDefinizione(SearchConnector):

    _base_url_ = 'https://altadefinizione.navy'

    @classmethod
    def _find_in_soup(cls, soup: bs4.BeautifulSoup, trusted: str = 'supervideo.tv') -> (list, str):
        tags = ["a", "li"]
        k = "data-target"
        partials = soup.findAll(lambda tag: tag.name in tags and tag.get(k) and trusted in tag.get(k))
        if partials:
            return partials, k
        k = "data-link"
        partials = soup.findAll(lambda tag: tag.name in tags and tag.get(k) and trusted in tag.get(k))
        return partials, k

    @classmethod
    def _find_in_frame(cls, soup: bs4.BeautifulSoup, trusted: str) -> Tuple[Optional[Union[list, str]], Optional[str]]:
        iframes = soup.findAll(lambda tag: tag.name == "iframe" and trusted in tag['src'])
        if iframes:
            src = iframes[0].attrs['src']
            if src.startswith('/'):
                return f"{cls._base_url_}{src}", None
            soup = bs4.BeautifulSoup(scraping.get(src).text)
            return cls._find_in_soup(soup)
        return None, None

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
    def _do_search(cls, query: str, title_only: bool) -> SearchResult:
        main_list = []
        secondary_list = []
        url = f"{cls._base_url_}/index.php?do=search"
        form = {'do': 'search', 'subaction': 'search', 'story': query}
        if title_only:
            form['titleonly'] = 3
        soup = bs4.BeautifulSoup(scraping.post(url, data=form).text)
        for wrapper in soup.find_all('div', 'wrapperImage'):
            a = wrapper.find('a')
            image_url = a.find('img').attrs['src']
            item_url = a.attrs['href']
            title = wrapper.find('div', {'class': 'info'}).find('h2', {'class': 'titleFilm'}).find('a').text
            item_soup = bs4.BeautifulSoup(scraping.get(item_url).text)
            details = cls._extract_item_details(item_soup)
            item = cls(original_title=title, url=item_url, image_url=image_url, year=details['Anno'], lang='it')
            if utils.check_in(query, title):
                main_list.append(item)
            else:
                secondary_list.append(item)
        return SearchResult(main_list, secondary_list)

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        result = cls._do_search(query, title_only=True)
        no_title_result = cls._do_search(query, title_only=False)
        result.merge(no_title_result)
        return result

    @property
    def src(self):
        return f"{self._base_url_}{self._image_url}"

    @classmethod
    async def execute(cls, content: dict):
        original_url = content['url']
        soup = bs4.BeautifulSoup(scraping.get(original_url).text)
        partials, key = cls._find_in_soup(soup)
        for frame_name in ['guardahd', 'altaqualita/player']:
            if partials:
                break
            partials, key = cls._find_in_frame(soup, frame_name)
        if partials:
            if key:
                p = partials[0].attrs[key]
                if p.startswith('//'):
                    p = f"https:{p}"
            else:
                p = partials
            return utils.new_tab(p)
