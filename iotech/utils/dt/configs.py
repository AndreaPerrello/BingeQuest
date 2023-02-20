import datetime

import pytz

from ...configurator import Config

TZ_STRING = Config(str, "SERVICE", "timezone", None)


def get_timezone() -> datetime.tzinfo:
    string = TZ_STRING.get()
    return pytz.timezone(string) if string is not None else pytz.utc
