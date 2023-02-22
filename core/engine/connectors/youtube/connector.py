# import datetime
# import functools
# import re
# from typing import List
#
# import bs4
# import requests
# from youtubesearchpython import VideosSearch
# from googlesearch import search as g_search
#
# from core.engine.utils import multi_format_date
# from core.engine.connectors.imdb_movie import IMDBMovie
# from core.engine.connectors.movie import MovieConnector
#
#
# class _YTResult(dict):
#
#     _min_minutes_ = 60
#
#     def __init__(self, query: str, suffix: str, **kwargs):
#         self._query: str = query
#         self._suffix: str = suffix
#         self.title = None
#         self.year = None
#         self._image_url = None
#         super().__init__(**kwargs)
#
#     @property
#     def imdb_title(self) -> str:
#         original_title = self.original_title.lower()
#         split = original_title.split(self._suffix)
#         title = re.sub(r'[^a-zA-Z0-9\s]+', '', split[0]) if split else self._query
#         return title
#
#     @functools.cached_property
#     def url(self) -> str:
#         return self['link']
#
#     @property
#     def image_url(self) -> str:
#         return self._image_url or self.get('thumbnails', [])[-1].get('url')
#
#     @image_url.setter
#     def image_url(self, x):
#         self._image_url = x
#
#     @functools.cached_property
#     def duration(self) -> datetime.datetime:
#         return multi_format_date(self['duration'])
#
#     @functools.cached_property
#     def time_delta(self) -> datetime.timedelta:
#         return datetime.timedelta(
#             hours=self.duration.hour,
#             minutes=self.duration.minute,
#             seconds=self.duration.second)
#
#     @property
#     def original_title(self) -> str:
#         return self['title']
#
#     def is_invalid(self) -> bool:
#         return self.original_title is None or self.duration is None or \
#                self.time_delta < datetime.timedelta(minutes=self._min_minutes_)
#
#
# def guess_movie_year(string: str):
#     seq = [int(y) for y in re.findall(r'([1-2][0-9]{3})', string)]
#     if seq:
#         year = max(seq)
#         if year > 1920:
#             return year
#
#
# class YouTube(MovieConnector):
#     _search_suffixes_ = ["full movie", "film completo"]
#     _youtube_result_limit_ = 2
#     _max_google_query_len_ = 36
#
#     @classmethod
#     def search(cls, query: str) -> List[MovieConnector]:
#         if not query:
#             return []
#         search_results = []
#         for search_suffix in cls._search_suffixes_:
#             search_key = f"{query} {search_suffix}"
#             video_search = VideosSearch(search_key, limit=cls._youtube_result_limit_)
#             for video_data in video_search.result().get('result', []):
#                 yt_result = _YTResult(query, search_suffix, **video_data)
#                 if yt_result.is_invalid():
#                     continue
#                 imdb_kwargs = {}
#                 year = guess_movie_year(yt_result.original_title)
#                 if year:
#                     imdb_kwargs['year'] = yt_result.year = year
#                 imdb_title = yt_result.imdb_title
#                 imdb_movie = IMDBMovie.search(imdb_title, duration=yt_result.time_delta, **imdb_kwargs)
#                 if not imdb_movie and len(imdb_title) <= cls._max_google_query_len_:
#                     google_query = f"{imdb_title.strip()} movie"
#                     if year:
#                         google_query = f"{google_query} {year}"
#                     for google_link in g_search(google_query):
#                         if 'wikipedia' in google_link:
#                             soup = bs4.BeautifulSoup(requests.get(google_link).text)
#                             imdb_title = soup.find('h1', {'id': 'firstHeading'}).find('span').text
#                             if query in imdb_title:
#                                 imdb_movie = IMDBMovie.search(imdb_title, duration=yt_result.time_delta, **imdb_kwargs)
#                             break
#                 if imdb_movie:
#                     yt_result.title = imdb_movie.name
#                     yt_result.image_url = imdb_movie.image_url
#                 elif yt_result.year:
#                     yt_result.title = f"{query.title()} ({yt_result.year})"
#                 else:
#                     continue
#                 search_results.append(cls(yt_result.title, yt_result.url, yt_result.image_url))
#         return search_results
