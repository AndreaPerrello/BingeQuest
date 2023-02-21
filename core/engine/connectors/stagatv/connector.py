import re
from typing import List

import bs4
import cloudscraper
import quart

from ..base import MovieConnector, SearchResult

scraper = cloudscraper.create_scraper()


class StagaTV(MovieConnector):

    _base_url_ = "https://www.stagatv.com"
    _files_base_url_pattern_ = r"https:\/\/stagatvfiles\.com\/videos\/file\/(?P<data_file>.*)\/.*"
    _files_dl_base_url_ = "https://stagatvfiles.com"

    def __init__(self, title: str, url: str, image_relative_url: str, token: str):
        super().__init__(title, url, image_relative_url)
        self._token: str = token

    def get_content(self) -> dict:
        return {'url': self.url, 'token': self._token}

    @classmethod
    async def execute(cls, content: dict):
        source_url = content['url']
        source_data = {'token': content['token'], 'api': '1'}
        return await quart.render_template(
            'movie/player_deferred.html', source_url=source_url,
            source_data=source_data, base_url=cls._files_dl_base_url_,
            mime_type="video/mp4")

    @classmethod
    def search(cls, query: str) -> SearchResult:
        episodes_list: List[StagaTV] = list()
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
            # Check if the query is contained in the series title
            if query in series_title.lower():
                series_url = link['href']
                series_soup = bs4.BeautifulSoup(scraper.get(series_url).text)
                img = series_soup.find('img', {'class': 'ts-post-image', 'alt': series_full_title})
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
                        episodes_list.append(cls(episode_title, episode_file_url, episode_cover, token=token))
        # Return results
        return SearchResult(episodes_list)

