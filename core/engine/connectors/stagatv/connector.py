import re
from typing import List

import bs4
import cloudscraper
import quart

from ... import security
from ..base import SearchConnector, SearchResult

scraper = cloudscraper.create_scraper()


class StagaTV_Series(SearchConnector):

    _base_url_ = "https://www.stagatv.com"
    _files_base_url_pattern_ = r"https:\/\/stagatvfiles\.com\/videos\/file\/(?P<data_file>.*)\/.*"
    _files_dl_base_url_ = "https://stagatvfiles.com"

    def __init__(self, title: str, url: str, image_url: str, poster_url: str, token: str):
        super().__init__(title, url, image_url)
        self._poster_url: str = poster_url
        self._token: str = token

    def get_content(self) -> dict:
        return {'url': self.url, 'poster_url': self._poster_url, 'token': self._token}

    @classmethod
    async def execute(cls, content: dict):
        source_url = content['url']
        source_data = {'token': content['token'], 'api': '1'}
        source_poster = content['poster_url']
        return await quart.render_template(
            'media/player/deferred.html', source_url=source_url, source_poster=source_poster,
            source_data=source_data, base_url=cls._files_dl_base_url_,
            mime_type="video/mp4")

    @classmethod
    def search(cls, query: str) -> SearchResult:
        episodes_list: List[StagaTV_Series] = list()
        # Scrape series list
        url = f"{cls._base_url_}/series-lists/"
        soup = bs4.BeautifulSoup(scraper.get(url).text)
        for li in soup.find('div', {'class': 'soralist'}).find_all('li'):
            link = li.find('a')
            series_full_title = link.text
            season_match = re.match(r".*\(S(?P<number>[0-9][1-2])\)", series_full_title)
            if not season_match:
                continue
            season_number = season_match['number']
            series_title = series_full_title.split(f'(S{season_number})')[0].strip()
            # Check if the query matches the series title
            if query.lower() == series_title.lower():
                series_url = link['href']
                series_soup = bs4.BeautifulSoup(scraper.get(series_url).text)
                img = series_soup.find('img', {'class': 'ts-post-image', 'alt': series_full_title})
                gallery_image = series_soup.find('div', {'class': 'gallery_img'})
                poster_url = '#'
                if gallery_image:
                    poster_url = gallery_image.find('a')['href']
                episode_links = [li.find('a') for li in series_soup.find('div', {'class': 'epsdlist'}).find_all('li')]
                for episode_link in episode_links:
                    episode_full_number = episode_link.find('div', {'class': 'epl-num'}).text
                    episode_match = re.match(r"S.* EP(?P<number>.*[0-9])", episode_full_number)
                    if not episode_match:
                        continue
                    episode_number = episode_match['number'].strip()
                    episode_title = f"{series_full_title} (E{episode_number})"
                    episode_cover = img['src']
                    episode_url = episode_link['href']
                    episode_soup = bs4.BeautifulSoup(scraper.get(episode_url).text)
                    episode_file_url = episode_soup.find('div', {'class': 'dl-item'}).find('a')['href']
                    match = re.match(cls._files_base_url_pattern_, episode_file_url)
                    if match:
                        token = match['data_file']
                        item = cls(episode_title, episode_file_url, episode_cover, poster_url, token=token)
                        episodes_list.append(item)
        # Return results
        return SearchResult(episodes_list)


class StagaTV(SearchConnector):

    children = [StagaTV_Series]

    _base_url_ = "https://www.stagatv.com"

    @property
    def link(self) -> str:
        return security.url_for('search', q=self.query_title, u=StagaTV_Series.uid())

    @classmethod
    def search(cls, query: str) -> SearchResult:
        """
        Search series-groups on StagaTV and return links to search a StagaTV_Series.
        """
        item_list: List[StagaTV] = list()
        # Scrape series list
        url = f"{cls._base_url_}/series-lists/"
        soup = bs4.BeautifulSoup(scraper.get(url).text)
        for li in soup.find('div', {'class': 'soralist'}).find_all('li'):
            link = li.find('a')
            full_title = link.text
            season_match = re.match(r".*\(S(?P<number>[0-9][1-2])\)", full_title)
            if not season_match:
                continue
            season_number = season_match['number']
            title = full_title.split(f'(S{season_number})')[0].strip()
            # Check if the query is contained in the series title
            if query in title.lower():
                item_soup = bs4.BeautifulSoup(scraper.get(link['href']).text)
                image_url = item_soup.find('img', {'class': 'ts-post-image', 'alt': full_title})['src']
                item_list.append(cls(title, image_url=image_url))
        # Return results
        return SearchResult(item_list)

