from iotech.microservice import MicroService
from iotech.microservice.web import WebService

from . import views
from .engine import SearchEngine

import logging

LOGGER = logging.getLogger(__name__)


class Controller(WebService, MicroService):
    """
    Controller of the Core operations. Manages the API application execution and the bus messages
    (service calls and command invocations on the plugin devices, device data updates, ecc..).
    """

    # noinspection PyTypeChecker
    def __init__(self):
        kwargs = dict(static_url_path='', static_folder='web', template_folder='web/templates')
        MicroService.__init__(self)
        WebService.__init__(self, views, **kwargs)
        self._engine = SearchEngine(self.app)

    @property
    def engine(self) -> SearchEngine:
        return self._engine
