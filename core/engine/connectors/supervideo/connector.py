import abc
from typing import Optional, Tuple, Union, List

from ... import utils, scraping
from ..base import SearchConnector, SearchResult


class SuperVideo(SearchConnector):

    _base_url_ = 'https://cb01.taxi'

    @property
    def src(self):
        return f"{self._base_url_}{self._image_url}"

    @classmethod
    async def execute(cls, content: dict):
        soup = scraping.get_soup(content['url'])
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
            return cls.new_tab(p)

    @classmethod
    def _find_in_soup(cls, soup, trusted: str = 'supervideo.tv') -> (list, str):
        tags = ["a", "li"]
        k = "data-target"
        partials = soup.findAll(lambda tag: tag.name in tags and tag.get(k) and trusted in tag.get(k))
        if partials:
            return partials, k
        k = "data-link"
        partials = soup.findAll(lambda tag: tag.name in tags and tag.get(k) and trusted in tag.get(k))
        return partials, k

    @classmethod
    def _find_in_frame(cls, soup, trusted: str) -> Tuple[Optional[Union[list, str]], Optional[str]]:
        iframes = soup.findAll(lambda tag: tag.name == "iframe" and trusted in tag['src'])
        if iframes:
            src = iframes[0].attrs['src']
            if src.startswith('/'):
                return f"{cls._base_url_}{src}", None
            return cls._find_in_soup(scraping.get_soup(src))
        return None, None

    @classmethod
    @abc.abstractmethod
    def _scrape_item(cls, wrapper) -> Optional[SearchConnector]:
        return

    @classmethod
    @abc.abstractmethod
    def _get_wrappers(cls, soup) -> List:
        return list()

    @classmethod
    def _do_search(cls, query: str, title_only: bool) -> SearchResult:
        main_list = []
        secondary_list = []
        url = f"{cls._base_url_}/index.php?do=search"
        form = {'do': 'search', 'subaction': 'search', 'story': query}
        if title_only:
            form['titleonly'] = 3
        soup = scraping.post_soup(url, data=form)
        for wrapper in cls._get_wrappers(soup):
            item = cls._scrape_item(wrapper)
            if item:
                if utils.check_in(query, item.title):
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
