import copy

from diskcache import Cache as DiskCache

from iotech.utils.classes import Singleton

from ..engine.security import encrypt_dict, decrypt_dict
cache = DiskCache('.mycache', statistics=True)


@Singleton
class Cache:

    def _do_get(self, cache_name: str, cache_id: int):
        cached_value = cache.get(f"{cache_name}:{cache_id}")
        if cached_value:
            return decrypt_dict(cached_value)

    def _do_set(self, cache_name: str, cache_id: int, value: dict):
        cache.set(f"{cache_name}:{cache_id}", encrypt_dict(**value), tag=cache_name)

    def get(self, cache_name: str, **kwargs):
        return self._do_get(cache_name, self._make_hash(kwargs))

    def set(self, cache_name: str, value: dict, **kwargs):
        self._do_set(cache_name, self._make_hash(kwargs), value)

    def _make_hash(self, o):
        if isinstance(o, (set, tuple, list)):
            return tuple([self._make_hash(e) for e in o])
        elif not isinstance(o, dict):
            return hash(o)
        new_o = copy.deepcopy(o)
        for k, v in new_o.items():
            new_o[k] = self._make_hash(v)
        return hash(tuple(frozenset(sorted(new_o.items()))))
