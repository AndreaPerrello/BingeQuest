import quart

from .events import QuartEventBroker
from . import configs as web_configs

import logging
LOGGER = logging.getLogger(__name__)


class _QuartBaseAppInterface:

    # noinspection PyTypeChecker
    def __init__(self, **kwargs):
        assert isinstance(self, quart.Quart)
        broker_kwargs = dict()
        if 'keepalive' in kwargs:
            broker_kwargs['keepalive'] = kwargs['keepalive']
        if 'token_expire_seconds' in kwargs:
            broker_kwargs['token_expire_seconds'] = kwargs['token_expire_seconds']
        self.config["SECRET_KEY"] = web_configs.WebServiceAppConfig.SECRET_KEY
        self._events = self.extensions["events"] = QuartEventBroker(self, auth=False, **broker_kwargs)

    async def emit(self, event: str, data):
        if self._events:
            await self._events.put(event=event, data=data)

    def on_auth(self):
        """ On-authentication event of the WebSocket broker. """

    def on_verify(self):
        """ On-verify event of the WebSocket broker. """

    def on_send(self, data):
        """ On-send event of the WebSocket broker. """


class QuartApp(quart.Quart, _QuartBaseAppInterface):

    def __init__(self, *args, **kwargs):
        quart.Quart.__init__(self, *args, **kwargs)
        _QuartBaseAppInterface.__init__(self)
