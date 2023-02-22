def _parse(s: str):
    return s.lower().replace('-', ' ')


def check_in(query: str, title: str) -> bool:
    return _parse(query) in _parse(title)


def check_equal(query: str, title: str) -> bool:
    return _parse(query) == _parse(title)
