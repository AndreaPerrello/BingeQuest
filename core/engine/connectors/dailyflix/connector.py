import urllib.parse
from typing import List, Optional

import bs4
import cloudscraper

from ...utils import new_tab
from ..base import MovieConnector, SearchResult

scraper = cloudscraper.create_scraper()


class DailyFlix(MovieConnector):

    _base_url_ = "https://main.dailyflix.stream"

    @classmethod
    async def execute(cls, content: dict):
        return new_tab(content['url'])

    @classmethod
    def search(cls, query: str) -> Optional[SearchResult]:
        movies_list: List[DailyFlix] = list()
        # Scrape movie list
        url = f"{cls._base_url_}/?s={urllib.parse.quote(query)}"
        soup = bs4.BeautifulSoup(scraper.get(url).text)
        table = soup.find('table', {'class': 'table'})
        if not table:
            return
        for td in table.find_all('td'):
            link = td.find('a')
            if not link:
                continue
            movie_title = link.text
            movie_url = link['href']
            movie_soup = bs4.BeautifulSoup(scraper.get(movie_url).text)
            movie_file_frame = movie_soup.find('iframe')
            if not movie_file_frame:
                continue
            movie_file_url = movie_file_frame['src']
            poster = movie_soup.find('div', {'class': 'poster_parent'})
            if not poster:
                continue
            poster_style = poster['style']
            movie_image_url = poster_style.strip().split(',')[1].strip().replace('url(', '').replace(')', '')
            movies_list.append(cls(movie_title, movie_file_url, movie_image_url))
        # Return results
        return SearchResult(movies_list)

