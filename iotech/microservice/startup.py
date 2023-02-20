import argparse
import functools
import importlib
import importlib.util
import uuid
import os
import enum
import inspect
import warnings
from typing import Union, Iterable, Callable, Type

from ..microservice import BaseService
from ..configurator import Config
from . import configs

import logging
import logging.config
LOGGER = logging.getLogger(__name__)
warnings.filterwarnings("ignore")


class Environment(enum.Enum):
    PRODUCTION = "production"
    DEVELOP = "develop"


# PARAMETERS
DEFAULT_ENVIRONMENT_TYPE = Environment.PRODUCTION.value

# CONFIGURATIONS
ENVIRONMENT_TYPE = Config(str, "ENVIRONMENT", "type", DEFAULT_ENVIRONMENT_TYPE)
MODULE_NAME = Config(str, "MODULE", "name")


# FUNCTIONS
def is_environment(env: Environment) -> bool:
    """
    Check the MicroService environment.
    :param env: Environment of the running MicroService to match.
    :return: True if the running MicroService environment is the same of the one give, False elsewhere.
    """
    return ENVIRONMENT_TYPE.get() == env.value


def is_production() -> bool:
    """ Check if the MicroService environment is Production. """
    return is_environment(Environment.PRODUCTION)


# Create microservice app
def create_app(config_dir: str, app_file: str,
               starter: Union[Iterable[str], Callable, BaseService, Type[BaseService]],
               environment: str = None, *args, **kwargs):
    """
    Gracefully configure and create a MicroService using configurations and a static or dynamic starter.
    :param config_dir: Name of the directory to set as configurations directory.
    :param app_file: Configuration file to use inside the configuration directory.
    :param starter: Iterable of string to load the module from a path. Alternatively, it can be a function
    that returns an equivalent iterable of strings.
    The iterable must the in the following form:
        - Module name: Name of the module directory which contains the main script.
        - Script name: Name of the Python script which contains the MicroService class or object.
        - Class or Object name: Name of the MicroService class or object inside the script.
        - (optional): Name of the service to run, used to override or setup the related Configurator variable.
        If no service name is configured or provided, this method will raise an exception.
    :param environment: (optional) String of the environment type. Anything different from 'production' is intended
    as a non-production environment.
    :param args: Positional arguments of the MicroService class constructor.
    :param kwargs: Key-value arguments of the MicroService class constructor.
    """
    # Parameters
    is_function: bool = inspect.isfunction(starter) or isinstance(starter, functools.partial)
    is_microservice_type: bool = hasattr(starter, '__mro__') and BaseService in inspect.getmro(starter)
    is_microservice: bool = isinstance(starter, BaseService)
    is_iterable: bool = any([isinstance(starter, x) for x in [list, tuple]])
    # Check if is valid input for the run
    if all(not x for x in [is_microservice, is_microservice_type, is_function, is_iterable]):
        raise ValueError("The starter must be a MicroService class or instance, a starter callable or an iterable.")

    # Initialize the configurator
    service_name = configs.SERVICE_NAME.get_or_set(default=uuid.uuid4().hex)
    Config.init(config_dir, app_file)
    # Get/set service name
    configs.SERVICE_NAME.get_or_set(default=service_name)
    # Override or get environment type from configurations
    environment = environment or ENVIRONMENT_TYPE.get(nocache=True)
    ENVIRONMENT_TYPE.set(environment)
    # Log service and environment
    LOGGER.info(f"Service: {service_name} (Environment: {environment})")
    # Initialize the configurator
    Config.init(config_dir, app_file)

    # Logging configurations
    try:
        import yaml
        # Load from file
        with open(os.path.join(config_dir, "log.yaml"), 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        LOGGER.info("Loaded logging configuration from log.yaml")
    except FileNotFoundError:
        # Set default
        log_format = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
                      '-35s %(lineno) -5d: %(message)s')
        logging.basicConfig(level=logging.INFO, format=log_format)
        LOGGER.info("Loaded standard logging configuration")

    # The starter is already a service instance
    if is_microservice:
        app = starter
    # The starter is a service class
    elif is_microservice_type:
        app = starter(*args, **kwargs)
    # Get the app from starter
    else:
        # Dynamic import modules
        module_args = starter if is_iterable else starter()
        if len(module_args) == 3:
            module_name, script_name, attribute_name = module_args
        else:
            module_name, script_name, attribute_name, service_name = module_args
            configs.SERVICE_NAME.set(service_name)
        # Get the app from dynamic import of the module, script and attribute
        object_or_cls = getattr(importlib.import_module(f"{module_name}.{script_name}"), attribute_name)
        app = object_or_cls(*args, **kwargs) if inspect.isclass(object_or_cls) else object_or_cls
    # Return the created app
    return app


def run_app(app: BaseService, _raise: bool = None):
    """
    Run a MicroService app with exception handling.
    :param app: The MicroService app to run.
    :param _raise: (optional) Flag to raise runtime exceptions; default is True if not in production environment.
    """
    # Set the raise flag
    _raise = _raise or not is_production()
    try:
        # Start the application
        return app.start()
    except Exception as e:
        # Abort the system upon exception
        app.abort(str(e))
        # Check to raise the exception
        if _raise:
            raise e


def cmd_create_app(starter: Union[Iterable[str], Callable, BaseService], *args, **kwargs) -> BaseService:
    """
    Create a MicroService using command line arguments.
    :param starter: MicroService instance or child class to create the app from; can also be an iterable of module,
     script and class-name or variable to call, or a callable which returns an iterable of the same form.
    :param args: Positional arguments to instantiate the MicroService;
        only used if a MicroService instance is not provided.
    :param kwargs: Key-value arguments to instantiate the MicroService;
        only used if a MicroService instance is not provided.
    :return: The instance of the created MicroService.
    """
    # Instance cmd arguments parser
    parser = argparse.ArgumentParser()
    # Configuration files directory
    parser.add_argument('-c', '--config_dir', default="config",
                        metavar='configuration_directory', type=str,
                        help='Configuration directory to use; if not specified, '
                             'default config directory will be used')
    # Configuration file
    parser.add_argument('-f', '--file_app', default="application.ini",
                        metavar='configuration_file', type=str,
                        help='Configuration file to use; if not specified, '
                             'default configs will be used')
    # Environment
    parser.add_argument('-e', '--environment', required=False, default=None,
                        type=str, help='Environment (production/develop)')

    # Parse cmd arguments
    cmd_args = parser.parse_args()
    config_dir = cmd_args.config_dir
    app_file = cmd_args.file_app
    environment = cmd_args.environment

    # Create the app with cmd arguments
    # noinspection PyTypeChecker
    return create_app(config_dir, app_file, starter=starter, environment=environment, *args, **kwargs)


def cmd_run(starter: Union[Iterable[str], Callable, BaseService, Type[BaseService]],
            _raise: bool = None, *args, **kwargs):
    """
    Create and run a MicroService using command line arguments without returning the created app.
    :param starter: MicroService instance or child class to create the app from; can also be an iterable of module,
     script and class-name or variable to call, or a callable which returns an iterable of the same form.
    :param _raise: (optional) Flag to raise runtime exceptions; default is True if not in production environment.
    :param args: Positional arguments to instantiate the MicroService;
        only used if a MicroService instance is not provided.
    :param kwargs: Key-value arguments to instantiate the MicroService;
        only used if a MicroService instance is not provided.
    """
    # Run the app
    # noinspection PyTypeChecker
    run_app(cmd_create_app(starter, *args, **kwargs), _raise=_raise)
