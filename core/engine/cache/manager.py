import hashlib

from iotech.utils.classes import Singleton

from .models import CacheEntries


@Singleton
class Cache:

    def get(self, cache_name: str, **kwargs):
        return CacheEntries.get(cache_name, self._make_hash(kwargs))

    def set(self, cache_name: str, value: dict, **kwargs):
        CacheEntries.set(cache_name, self._make_hash(kwargs), value)

    @staticmethod
    def _make_hash(dd: dict) -> str:
        unique_str = ''.join(["'%s':'%s';" % (key, val) for (key, val) in sorted(dd.items())])
        return hashlib.sha1(unique_str.encode()).hexdigest()
