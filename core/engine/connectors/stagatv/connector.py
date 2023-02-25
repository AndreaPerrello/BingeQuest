from ... import security
from ..base import SearchConnector, SearchResult
from .series_season import StagaTV_Series
from .lib import Series


class StagaTV(SearchConnector):

    children = [StagaTV_Series]

    @property
    def link(self) -> str:
        return security.url_for('search', q=self.query_title, u=StagaTV_Series.uid())

    @classmethod
    def search(cls, query: str) -> SearchResult:
        _list = list()
        for series in Series.get_uniques(query):  # type: Series
            series.scrape()
            item = cls(original_title=series.title, image_url=series.image_url, year=series.year)
            _list.append(item)
        # Return results
        return SearchResult(_list)
