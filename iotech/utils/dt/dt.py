""" Time and dates conversion and management utility wrapper. Based on date-time and date-util. """
import os

import pytz
import datetime as py_datetime
import dateutil.parser

from . import configs

timezone: py_datetime.tzinfo = configs.get_timezone()


class datetime(py_datetime.datetime):

    @classmethod
    def from_dt(cls, d: py_datetime.datetime):
        d = d.astimezone(timezone)
        return cls(d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond, tzinfo=d.tzinfo)

    def strftime(self, fmt) -> str:
        if os.name == 'nt':
            fmt = fmt.replace('%-', '%#')
        return super().strftime(fmt)

    def to_ms(self) -> int:
        """ Convert to milliseconds. """
        return int(self.timestamp() * 1000)

    @classmethod
    def from_iso(cls, date_string: str):
        """
        Get a datetime from ISO timestamp string.
        :param date_string:
        """
        try:
            date_time = cls.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f%z')
        except:
            date_time = cls.strptime(date_string, '%Y-%m-%dT%H:%M:%S%z')
        return cls.from_dt(date_time)

    def to_iso(self) -> str:
        return self.timestamp_to_iso(self.timestamp())

    @classmethod
    def from_timestamp(cls, timestamp: str):
        """
        Generate a datetime from a timestamp.
        :param timestamp:
        """
        return cls.from_dt(dateutil.parser.parse(timestamp))

    @classmethod
    def is_datetime(cls, string: str) -> bool:
        """
        Check if a string can be converted in a datetime object.
        :param string:
        """
        try:
            cls.from_timestamp(string)
            return True
        except Exception:
            return False

    @classmethod
    def get_now(cls):
        """ Get the current datetime. """
        return cls.from_dt(cls.now(timezone))

    @classmethod
    def get_now_iso_timestamp(cls) -> str:
        """ Get the current timestamp in ISO format. """
        return cls.timestamp_to_iso(cls.get_now().timestamp())

    @classmethod
    def timestamp_to_iso(cls, timestamp: float) -> str:
        """
        Convert a timestamp to ISO format.
        :param timestamp:
        """
        return cls.fromtimestamp(timestamp, tz=timezone).isoformat()

    def timedelta(self, **kwargs):
        """
        Get the datetime with delta applied.
        :param kwargs: Arguments of datetime.timedelta object.
        :return: Datetime with given applied timedelta.
        """
        return self.from_dt(self + py_datetime.timedelta(**kwargs))

    @classmethod
    def new(cls, date_time=None, **kwargs):
        """
        Create a new datetime or time from key-value arguments.
        :param date_time: (optional) Datetime from which to create the new datetime.
        :param kwargs:
        """
        tz = kwargs.pop('tz', False)
        kwargs.update({
            'year': date_time and date_time.year or kwargs.get('year', 2000),
            'month': date_time and date_time.month or kwargs.get('month', 1),
            'day': date_time and date_time.day or kwargs.get('day', 1),
            'tzinfo': date_time and date_time.tzinfo or tz and timezone or pytz.utc
        })
        return cls.from_dt(py_datetime.datetime(**kwargs))

    @classmethod
    def new_time(cls, **kwargs):
        return py_datetime.time(**kwargs)
