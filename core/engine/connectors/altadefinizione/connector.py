from typing import List, Optional, Tuple, Union

import bs4
import cloudscraper

from ...utils import new_tab
from ..base import MovieConnector, SearchResult

scraper = cloudscraper.create_scraper()


class AltaDefinizione(MovieConnector):

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
    def _do_search(cls, query: str, title_only: bool) -> List[MovieConnector]:
        url = f"{cls._base_url_}/index.php?do=search"
        form = {'do': 'search', 'subaction': 'search', 'story': query}
        if title_only:
            form['titleonly'] = 3
        text = scraper.post(url, data=form).text
        soup = bs4.BeautifulSoup(text)
        movie_list = []
        for wrapper in soup.find_all('div', 'wrapperImage'):
            a = wrapper.find('a')
            image = a.find('img').attrs['src']
            url = a.attrs['href']
            title = wrapper.find('div', {'class': 'info'}).find('h2', {'class': 'titleFilm'}).find('a').text
            movie_list.append(cls(title, url, image))
        return movie_list

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        main_results = cls._do_search(query, title_only=True)
        secondary_results = cls._do_search(query, title_only=False)
        return SearchResult(main_results, secondary_results)

    @property
    def image_url(self):
        return f"{self._base_url_}{self.relative_url}"

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
