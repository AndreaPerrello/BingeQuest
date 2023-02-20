from typing import List, Optional

import bs4
import cloudscraper

from ..movie import MovieConnector, SearchResult

scraper = cloudscraper.create_scraper()


class AltaDefinizione(MovieConnector):

    base_url = 'https://altadefinizione.navy'

    @property
    def image_url(self):
        return f"{self.base_url}{self.relative_url}"

    @classmethod
    def get_link(cls, original_url: str):
        text = scraper.get(original_url).text
        soup = bs4.BeautifulSoup(text)
        partials, key = cls._find_in_soup(soup)
        if not partials:
            partials, key = cls._find_in_frame(soup, 'guardahd')
        if not partials:
            partials, key = cls._find_in_frame(soup, 'altaqualita/player')
        if partials:
            if key:
                p = partials[0].attrs[key]
                if p.startswith('//'):
                    return f"https:{p}"
                return p
            return partials

    @classmethod
    def _find_in_soup(cls, soup: bs4.BeautifulSoup, trusted: str = 'supervideo.tv'):
        tags = ["a", "li"]
        k = "data-target"
        partials = soup.findAll(lambda tag: tag.name in tags and tag.get(k) and trusted in tag.get(k))
        if partials:
            return partials, k
        k = "data-link"
        partials = soup.findAll(lambda tag: tag.name in tags and tag.get(k) and trusted in tag.get(k))
        return partials, k

    @classmethod
    def _find_in_frame(cls, soup: bs4.BeautifulSoup, trusted: str):
        iframes = soup.findAll(lambda tag: tag.name == "iframe" and trusted in tag['src'])
        if iframes:
            src = iframes[0].attrs['src']
            if src.startswith('/'):
                return f"{cls.base_url}{src}", None
            text = scraper.get(src).text
            soup = bs4.BeautifulSoup(text)
            return cls._find_in_soup(soup)
        return [], None

    @classmethod
    def _do_search(cls, query: str, title_only: bool) -> List[MovieConnector]:
        if not query:
            return list()
        url = f"{cls.base_url}/index.php?do=search"
        form = {'do': 'search', 'subaction': 'search', 'story': query}
        if title_only:
            form['titleonly'] = 3
        text = scraper.post(url, data=form).text
        soup = bs4.BeautifulSoup(text)
        movies = []
        for wrapper in soup.find_all('div', 'wrapperImage'):
            a = wrapper.find('a')
            image = a.find('img').attrs['src']
            url = a.attrs['href']
            title = wrapper.find('div', {'class': 'info'}).find('h2', {'class': 'titleFilm'}).find('a').text
            movies.append(cls(title, url, image))
        return movies

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        main_results = cls._do_search(query, title_only=True)
        secondary_results = cls._do_search(query, title_only=False)
        return SearchResult(main_results, secondary_results)
