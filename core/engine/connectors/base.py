import abc
import urllib.parse
from typing import Optional, List, Any

from .. import security
from ..utils import new_tab

_lang_map = {'en': 'ENG', 'it': 'ITA'}


class SearchConnector:

    children: List = []

    def __init__(self, original_title: str, url: str = None, image_url: str = None, lang: str = None):
        self._original_title = urllib.parse.unquote(original_title)
        self._url = url
        self._image_url = image_url
        self._lang = lang

    def __lt__(self, other):
        return self.title < other.title

    def __eq__(self, other):
        return self.title == other.title

    @property
    def title(self) -> str:
        language = _lang_map.get(self._lang, _lang_map['en'])
        return f"{self._original_title} ({language})"

    @property
    def query_title(self) -> str:
        return self._original_title.lower()

    @property
    def url(self) -> str:
        return self._url

    @classmethod
    def uid(cls) -> str:
        return cls.__name__.lower()

    @property
    def link(self) -> str:
        return security.url_for('search', m=self.media_hash)

    @property
    def src(self) -> str:
        return self._image_url

    @classmethod
    def content_from_hash(cls, media_hash: str) -> (Optional[str], Optional[str]):
        try:
            data = security.decrypt_dict(media_hash)
            return data['content'], data['uid']
        except:
            return None, None

    @property
    def media_hash(self) -> str:
        return security.encrypt_dict(content=self.get_content(), uid=self.uid())

    def get_content(self) -> dict:
        return {'url': self.url}

    @classmethod
    async def execute(cls, content: Any) -> Any:
        return new_tab(content['url'])

    @classmethod
    @abc.abstractmethod
    def search(cls, query: str):
        """
        :rtype Optional[SearchResult]
        :param query:
        :return:
        """
        pass


class SearchResult:

    def __init__(self, main: List[SearchConnector] = None, secondary: List[SearchConnector] = None):
        main = main and {x.title: x for x in main} or dict()
        secondary = secondary and {x.title: x for x in secondary} or dict()
        self._reduce(main, secondary)

    def _reduce(self, main: dict, secondary: dict):
        self.main = main
        self.secondary = {k: v for k, v in secondary.items() if k not in main}

    def merge(self, x):
        """
        :type x: SearchResult
        """
        main = {**self.main, **x.main}
        secondary = {**self.secondary, **x.secondary}
        self._reduce(main, secondary)

    def sorted(self):
        return self.__class__(sorted(self.main.values()), sorted(self.secondary.values()))

