import abc
import urllib.parse
import webbrowser
from typing import Optional, List, Any, Dict

from quart import render_template, url_for

from .. import security

_lang_map = {'en': 'ENG', 'it': 'ITA'}


class SearchConnector:
    children: List = []

    def __init__(
            self,
            original_title: str,
            base_title: str = None,
            details: str = None,
            url: str = None,
            image_url: str = None,
            lang: str = None,
            year: int = None,
            *args,
            **kwargs
    ):
        self._original_title = urllib.parse.unquote(original_title)
        self._base_title: str = base_title
        self._details: str = details
        self._url: str = url
        self._image_url: str = image_url
        self._lang: str = lang
        self._year: int = year

    def __lt__(self, other):
        return self.title < other.title

    def __eq__(self, other):
        return self.title == other.title

    @property
    def title(self) -> str:
        title = self._original_title
        if self._year:
            title = f"{title} [{self._year}]"
        language = _lang_map.get(self._lang, _lang_map['en'])
        language_string = f"({language})"
        if language_string in title:
            return title
        return f"{title} {language_string}"

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
        return self._image_url if self._image_url else '/assets/images/blank-poster.jpg'

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

    # Methods

    def get_content(self) -> dict:
        return {'url': self.url}

    @classmethod
    async def render_player_deferred(
            cls, player_poster_url: str = None,
            player_src_base_url: str = '', mime_type: str = None, ajax_method: str = None, **kwargs):
        """
        Render a deferred media-player (video-player with deferred loading function).
        :param player_poster_url: (optional) URL of the player poster to render after defer loading.
        :param player_src_base_url: (optional) Base source url to prepend to the deferred result file.
        :param mime_type: (optional) Mime-type of the deferred resource; default is 'video/mp4'.
        :param kwargs: (optional) Key-value arguments to pass to the deferred function.
        """
        mime_type = mime_type or 'video/mp4'
        player_poster_url = player_poster_url or '#'
        player_src_base_url = player_src_base_url or ''
        if not kwargs.get('error'):
            kwargs['ajax_url'] = url_for('deferred_execute')
            kwargs['ajax_method'] = ajax_method or 'post'
            kwargs['encrypted_ajax_data'] = security.encrypt_dict(u=cls.uid(), **kwargs)
        return await render_template(
            'media/player/deferred.html',
            player_poster=player_poster_url,
            player_src_base_url=player_src_base_url,
            mime_type=mime_type, **kwargs)

    @classmethod
    def new_tab(cls, url):
        webbrowser.open_new_tab(url)
        return "<script>history.back()</script>"

    @classmethod
    async def execute_deferred(cls, **kwargs) -> Optional[Dict]:
        return dict()

    @classmethod
    async def execute(cls, content: Any) -> Any:
        return cls.new_tab(content['url'])

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

    def merge(self, result):
        """
        :type result: SearchResult
        """
        if result:
            main = {**self.main, **result.main}
            secondary = {**self.secondary, **result.secondary}
            self._reduce(main, secondary)

    def sorted(self):
        return self.__class__(sorted(self.main.values()), sorted(self.secondary.values()))

    @property
    def is_empty(self) -> bool:
        return not self.main and not self.secondary
