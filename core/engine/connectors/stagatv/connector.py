from ... import security
from ..base import SearchConnector, SearchResult
from .episode import StagaTV_Episode
from . import lib


class StagaTV(SearchConnector):

    # FIXME: 'Peaky-Blinders' like seasons may be packed into a single result
    # FIXME: 'Breaking-Bad' like season are returned with the season name in the main result

    children = [StagaTV_Episode]

    _base_url_ = "https://www.stagatv.com"

    @property
    def link(self) -> str:
        return security.url_for('search', q=self.query_title, u=StagaTV_Episode.uid())

    @classmethod
    def search(cls, query: str) -> SearchResult:
        _list = list()
        for series_season in lib.SeriesSeason.get_all(query):
            _list.append(cls(original_title=series_season.title, image_url=series_season.image_url))
        # Return results
        return SearchResult(_list)

