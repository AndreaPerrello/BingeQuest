import functools
import importlib
import os
from http import HTTPStatus
from typing import Union, Tuple

import pluggy
import quart
import uvicorn
import werkzeug.exceptions

from ..startup import is_production
from ...utils import networking
from ..interface import ServiceInterface
from .. import configs as service_configs
from .app import PintApp, QuartApp
from . import spec, ext, configs

import logging
LOGGER = logging.getLogger(__name__)


class WebService(ServiceInterface):

    # noinspection PyTypeChecker
    def __init__(self, views_module, app_cls=QuartApp, **app_kwargs):
        super().__init__()
        self._views_module = views_module
        app = app_cls(service_configs.SERVICE_NAME.get(), **app_kwargs)
        app.config.from_object(configs.WebServiceAppConfig())
        self._app: Union[QuartApp, PintApp] = app
        self._pluggy = pluggy.PluginManager('default')
        self._server: uvicorn.Server = None
        if not hasattr(self, '_event_loop'):
            raise Exception("Main class must implement asyncio _event_loop.")

    # Properties

    @functools.cached_property
    def listener(self) -> Tuple[str, int]:
        return configs.WEBSERVICE_HOST.get(), configs.WEBSERVICE_PORT.get()

    @property
    def app(self) -> quart.Quart:
        return self._app

    @functools.cached_property
    def base_url(self):
        return configs.WEBSERVICE_ENDPOINT()

    # Interface methods

    def interface_init(self):
        # Check if app host-port is in use
        if networking.ping(*self.listener):
            raise Exception(f"Cannot start the web-service on: {self.listener}.")
        # Configure the app
        self._configure_app()
        # Initialize the server
        log_level = logging.WARNING if is_production() else None
        kwargs = dict(app=self._app, host=self.listener[0], port=self.listener[1], log_level=log_level)
        self._server: uvicorn.Server = uvicorn.Server(uvicorn.Config(**kwargs))

    def __repr__(self):
        return f"Web-server running at: {configs.WEBSERVICE_ENDPOINT()}"

    def interface_run(self):
        # Run the server
        LOGGER.info(f"{self}")
        self._server.run()

    def interface_stop(self):
        # # Stop the server, if any
        if self._server:
            self._server.force_exit = True
            self._server.should_exit = True

    # Internal procedures
    async def _initialize_db(self):
        """ Initialize the database. """
        def _wrapped():
            LOGGER.info(f"Connecting database: {ext.db.engine.url}..")
            ext.db.create_all()
            LOGGER.info(f"Database configured.")
        if isinstance(self._app, quart.Quart):
            async with self._app.app_context():
                _wrapped()
        else:
            _wrapped()

    def _configure_app(self):
        """ Configure the web-app. """
        # Add views hook specs
        self._pluggy.add_hookspecs(spec)
        # Scrape views modules
        views_at = self._views_module.__name__.split('.')
        views_path = os.path.join(*views_at)
        # noinspection PyTypeChecker
        modules = ['.'.join(views_at + [name, 'views'])
                   for name in os.listdir(views_path)
                   if not name.endswith('.py') and not name.startswith('__')]
        # Import and register each view
        for name in sorted(modules, reverse=True):
            module = importlib.import_module(name)
            self._pluggy.register(module)
        # Configure extensions
        # Database extension
        if ext.db.is_configured:
            ext.db.init_app(self._app)
            event_loop = getattr(self, '_event_loop')
            event_loop.create_task(self._initialize_db())
        # Mail extension
        if ext.mail.is_configured:
            ext.mail.init_app(self._app)
        # CORS extension
        if ext.cors.is_configured:
            self._app = ext.cors.init_app(
                self._app, allow_origin=configs.WEBSERVICE_ALLOW_ORIGINS.get(),
                allow_credentials=configs.WEBSERVICE_ALLOW_CREDENTIALS.get())
        # Load blueprints
        self._pluggy.hook.load_blueprints(core=self)

    # Methods

    async def emit(self, event: str, data: Union[str, dict] = None):
        """
        Send a websocket event with optional data.
        :param event: The websocket event route/topic to send data on.
        :param data: (optional) Mapping or string of data to send.
        """
        if hasattr(self._app, 'emit'):
            await self._app.emit(event=event, data=data or '')

    # Response methods

    def _response_success(self, status_code: Union[int, HTTPStatus], data=None, location: str = None):
        data = data or ''
        if location:
            location_uri = f"{self.base_url}{location}"
            return data, status_code, {"Location": location_uri}
        return data, status_code

    @staticmethod
    def _response_error(status_code: Union[int, HTTPStatus], desc: str):
        return {"message": desc}, status_code

    def _response_bad_request(self, desc):
        return self._response_error(HTTPStatus.BAD_REQUEST, desc)

    def response_missing_payload(self):
        """ Return an API response of missing payload. """
        return self._response_bad_request("Missing request payload.")

    def response_error(self, e: Union[BaseException, str], status_code: Union[int, HTTPStatus] = None):
        """
        Return a response of error.
        :param e: Exception to return the error from.
        :param status_code: (optional) Status code of the error. Automatically set to BAD_REQUEST if is the error is
        an instance of KeyError.
        """
        if isinstance(e, werkzeug.exceptions.BadRequestKeyError):
            return self.response_error(KeyError(', '.join(e.args)))
        if isinstance(e, KeyError):
            return self._response_bad_request(f"Missing key(s) {e} in request arguments or payload.")
        status_code = status_code or HTTPStatus.INTERNAL_SERVER_ERROR
        return self._response_error(status_code, str(e))

    def response_ok(self, data: Union[str, dict, object] = None, *args, **kwargs):
        """
        Return a response with ok status.
        :param data: (optional) Data of the response, in the form of a string, dictionary or object to marshal; object
        auto-marshalling requires the parameter model to be not null.
        """
        return self._response_success(HTTPStatus.OK, data)

    def response_created(self, location: str = None):
        """
        Return a response of created resource.
        :param location: (optional) Location of the created resource to put in the response headers.
        """
        return self._response_success(HTTPStatus.CREATED, location=location)

    def response_no_content(self):
        """ Return a response of no content. """
        return self._response_success(HTTPStatus.NO_CONTENT)

