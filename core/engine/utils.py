import datetime
import webbrowser


def multi_format_date(string: str):
    if not string:
        return
    try:
        return datetime.datetime.strptime(string, "%H:%M:%S")
    except:
        try:
            return datetime.datetime.strptime(string, "%M:%S")
        except:
            pass


def history_back() -> str:
    return "<script>history.back()</script>"


def new_tab(url: str) -> str:
    webbrowser.open_new_tab(url)
    return history_back()


def _parse(s: str):
    return s.lower().replace('-', ' ')


def check_in(query: str, title: str) -> bool:
    return _parse(query) in _parse(title)


def check_equal(query: str, title: str) -> bool:
    return _parse(query) == _parse(title)
