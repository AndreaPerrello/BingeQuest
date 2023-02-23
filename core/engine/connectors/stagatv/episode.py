import quart

from ..base import SearchConnector, SearchResult
from . import lib


class StagaTV_Episode(SearchConnector):

    def __init__(self, poster_url: str, token: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            source_data=source_data, base_url=lib.SeriesEpisode.files_dl_base_url,
            mime_type="video/mp4")

    @classmethod
    def search(cls, query: str) -> SearchResult:
        _list = list()
        for series_season in lib.SeriesSeason.get_all(query):
            for episode in series_season.get_episodes():
                episode.scrape()
                item = cls(original_title=episode.title, url=episode.file_url,
                           image_url=series_season.image_url,
                           poster_url=series_season.poster_url, token=episode.token)
                _list.append(item)
        # Return results
        return SearchResult(_list)
