import abc
import base64
import json
import urllib.parse
from typing import Optional, List

import cryptography.fernet

from iotech.configurator import Config

FERNET_KEY = Config(str, 'FERNET', 'key')
key = FERNET_KEY.get().encode('utf-8')
fernet = cryptography.fernet.Fernet(key)


class MovieConnector:

    def __init__(self, title: str, url: str, relative_url: str):
        self.title = urllib.parse.unquote(title)
        self.url = url
        self.relative_url = relative_url

    @property
    def image_url(self) -> str:
        return f"{self.relative_url}"

    @classmethod
    def content_from_hash(cls, media_hash: str) -> (Optional[str], Optional[str]):
        try:
            b64_hash = media_hash.encode('ascii')
            encrypted_data = base64.urlsafe_b64decode(b64_hash)
            dumped_data = fernet.decrypt(encrypted_data).decode()
            data = json.loads(dumped_data)
            return data['url'], data['type']
        except:
            return None, None

    @property
    def media_hash(self) -> str:
        dumped_data = json.dumps(dict(url=self.url, type=self.__class__.__name__))
        encrypted_data = fernet.encrypt(dumped_data.encode())
        b64_hash = base64.urlsafe_b64encode(encrypted_data)
        return b64_hash.decode('ascii')

    @classmethod
    def get_link(cls, original_url: str) -> str:
        return original_url

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

    def __init__(self, main: List[MovieConnector] = None, secondary: List[MovieConnector] = None):
        main = main and {x.title: x for x in main} or dict()
        secondary = secondary and {x.title: x for x in secondary} or dict()
        secondary = {k: v for k, v in secondary.items() if k not in main}
        self.main = main
        self.secondary = secondary

    def merge(self, x):
        """
        :type x: SearchResult
        """
        self.main = {**self.main, **x.main}
        self.secondary = {**self.secondary, **x.secondary}