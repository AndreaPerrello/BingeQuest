import re

import bs4
import cloudscraper

from ..base import MovieConnector, SearchResult

scraper = cloudscraper.create_scraper()


class StagaTV(MovieConnector):

    _base_url_ = "https://www.stagatv.com"
    _files_base_url_ = "https://stagatvfiles.com/videos/file/{data_file}/{file_name}"

    @classmethod
    def search(cls, query: str) -> SearchResult:
        results = []
        url = f"{cls._base_url_}/series-lists/"
        soup = bs4.BeautifulSoup(scraper.get(url).text)
        for li in soup.find('div', {'class': 'soralist'}).find_all('li'):
            link = li.find('a')
            series_full_title = link.text
            match = re.match(r".*\(S(?P<number>[0-9][1-2])\)", series_full_title)
            if not match:
                continue
            season_number = match['number']
            series_title = series_full_title.split(f'(S{season_number})')[0].strip()
            if query in series_title.lower():
                series_url = link['href']
                series_soup = bs4.BeautifulSoup(scraper.get(series_url).text)
                img = series_soup.find('img', {'class': 'ts-post-image', 'alt': series_full_title})
                episode_links = [li.find('a') for li in series_soup.find('div', {'class': 'epsdlist'}).find_all('li')]
                # FIXME
                episode = episode_links[0]
                episode_url = episode['href']
                episode_soup = bs4.BeautifulSoup(scraper.get(episode_url).text)
                episode_file_url = episode_soup.find('div', {'class': 'dl-item'}).find('a')['href']
                episode_file_soup = bs4.BeautifulSoup(scraper.get(episode_file_url).text)
                # file_name = episode_file_soup.find('h1').text.strip()
                # data_file = episode_file_soup.find('button', {'id': 'om_dl'})['data-file']
                # file_url = cls._files_base_url_.format(file_name=file_name, data_file=data_file)
                # TODO: The file download button must be clicked
                results.append(cls(series_full_title, episode_file_url, img['src']))
        return SearchResult(results)

