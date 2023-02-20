import datetime
import json

import aniso8601
from PyMovieDb import IMDB

imdb = IMDB()


class IMDBMovie(dict):

    @property
    def name(self) -> str:
        return self['name']

    @property
    def image_url(self) -> str:
        return self['poster']

    @property
    def duration(self):
        try:
            return aniso8601.parse_duration(self.get('duration'))
        except:
            pass

    @classmethod
    def single_search(cls, key: str, year: int = None, duration: datetime.timedelta = None):
        imdb_result_string = imdb.get_by_name(key, year=year)
        if imdb_result_string:
            result = cls(**json.loads(imdb_result_string))
            if result.get('status') is None:
                expected = result.duration
                if expected:
                    _delta_minutes_ = 10
                    duration_threshold = datetime.timedelta(minutes=_delta_minutes_)
                    if max(expected, duration) - min(expected, duration) < duration_threshold:
                        return result

    @classmethod
    def multi_search(cls, key: str, year: int = None, duration: datetime.timedelta = None):
        split = [x for x in key.split(' ') if x]
        for i in range(len(split)):
            sub_key = ' '.join(split[i:])
            result = cls.single_search(sub_key, year=year, duration=duration)
            if result:
                return result

    @classmethod
    def search(cls, key: str, year: int = None, duration: datetime.timedelta = None):
        result = cls.single_search(key, year=year, duration=duration)
        if result:
            return result
