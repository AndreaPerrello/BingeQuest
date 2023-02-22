from typing import Optional, Tuple, Union

import bs4
import cloudscraper

from ..utils import check_in
from ...utils import new_tab
from ..base import SearchConnector, SearchResult

scraper = cloudscraper.create_scraper()


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
            text = scraper.get(src).text
            soup = bs4.BeautifulSoup(text)
            return cls._find_in_soup(soup)
        return None, None

    @classmethod
    def _do_search(cls, query: str, title_only: bool) -> SearchResult:
        main_list = []
        secondary_list = []
        url = f"{cls._base_url_}/index.php?do=search"
        form = {'do': 'search', 'subaction': 'search', 'story': query}
        if title_only:
            form['titleonly'] = 3
        text = scraper.post(url, data=form).text
        soup = bs4.BeautifulSoup(text)
        for wrapper in soup.find_all('div', 'wrapperImage'):
            a = wrapper.find('a')
            image_url = a.find('img').attrs['src']
            url = a.attrs['href']
            title = wrapper.find('div', {'class': 'info'}).find('h2', {'class': 'titleFilm'}).find('a').text
            item = cls(title, url, image_url=image_url, lang='it')
            if check_in(query, title):
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
        soup = bs4.BeautifulSoup(scraper.get(original_url).text)
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
            return new_tab(p)
