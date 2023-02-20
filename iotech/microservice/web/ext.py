import importlib
from typing import Callable

from . import configs, exceptions

import logging
LOGGER = logging.getLogger(__name__)

__protected__ = ['_ext_name', '_module_name', '_class_name', '_check_function', '_error']


class AppExt:

    def __init__(self, name: str, module_name: str, class_name: str,
                 check_func: Callable = None, lazy: bool = False, kwargs=None, exc_cls=None):
        self._ext_name: str = name
        self._module_name: str = module_name
        self._class_name: str = class_name
        self._check_func: Callable = check_func
        self._lazy: bool = lazy
        self._kwargs = kwargs or dict()
        # noinspection PyTypeChecker
        self._instance_cls: type = None
        self._instance: object = None
        self._exc_cls = exc_cls or exceptions.WebServiceExtensionNotConfigured
        if self._check_func is None or self._check_func():
            try:
                ext_module = importlib.import_module(self._module_name)
                self._instance_cls = getattr(ext_module, self._class_name)
                if not self._lazy:
                    self._instance = self._instance_cls(**self._kwargs)
            except ModuleNotFoundError:
                self._exc = exceptions.WebServiceExtensionModuleNotFound(self._module_name)
            except AttributeError:
                self._exc = exceptions.WebServiceExtensionModuleClassNotFound(self._module_name, self._class_name)

    def __repr__(self):
        return f"{self._ext_name}"

    def __call__(self, *args, **kwargs):
        return self._instance(*args, **kwargs)

    def __getattr__(self, item):
        if item in __protected__:
            return super().__getattribute__(item)
        if self._instance is None:
            raise self._exc_cls(module_name=self._module_name)
        return getattr(self._instance, item)

    def init_app(self, app, *args, **kwargs):
        if not self._lazy:
            self._instance.init_app(app, *args, **kwargs)
            self._instance.app = app
        else:
            self._instance = self._instance_cls(app, *args, **kwargs)
            return self._instance

    @property
    def is_configured(self) -> bool:
        return self._instance_cls is not None and self._lazy or self._instance is not None


# Quart-Flask SQLAlchemy
db = AppExt(
    'db', 'flask_sqlalchemy', 'SQLAlchemy',
    check_func=configs.WEBSERVICE_HAS_DATABASE,
    exc_cls=exceptions.WebServiceMissingDBConfiguration
)
# Quart-Flask Mail
mail = AppExt('mail', 'flask_mail', 'Mail')
# Quart-Cors
cors = AppExt('cors', 'quart_cors', 'cors', lazy=True)
