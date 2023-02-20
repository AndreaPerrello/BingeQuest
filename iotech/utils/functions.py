import asyncio
import functools
import importlib
import inspect
import json
import os
import sys
import time
import decimal
import contextvars

from typing import (
    Any, Union, List, Callable,
    Coroutine, Generator,
    AsyncGenerator, Awaitable)

from . import version

import logging
LOGGER = logging.getLogger(__name__)


def run_sync_iterable(iterable: Generator[Any, None, None]) -> AsyncGenerator[Any, None]:
    async def _gen_wrapper() -> AsyncGenerator[Any, None]:
        # Wrap the generator such that each iteration runs
        # in the executor. Then rationalise the raised
        # errors so that it ends.
        def _inner() -> Any:
            # https://bugs.python.org/issue26221
            # StopIteration errors are swallowed by the
            # run_in_exector method
            try:
                return next(iterable)
            except StopIteration:
                raise StopAsyncIteration()
        loop = asyncio.get_running_loop()
        while True:
            try:
                yield await loop.run_in_executor(None, contextvars.copy_context().run, _inner)
            except StopAsyncIteration:
                return
    return _gen_wrapper()


def run_sync(func: Callable[..., Any]) -> Callable[..., Coroutine[None, None, Any]]:
    """
    Ensure that the sync function is run within the event loop.

    If the *func* is not a coroutine it will be wrapped such that
    it runs in the default executor (use loop.set_default_executor
    to change). This ensures that synchronous functions do not
    block the event loop.
    """
    @functools.wraps(func)
    async def _wrapper(*args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, contextvars.copy_context().run, functools.partial(func, *args, **kwargs)
        )
        if inspect.isgenerator(result):
            return run_sync_iterable(result)
        else:
            return result
    return _wrapper


def is_coroutine_function(func: Any) -> bool:
    # Python < 3.8 does not correctly determine partially wrapped
    # coroutine functions are coroutine functions, hence the need for
    # this to exist. Code taken from CPython.
    if sys.version_info >= (3, 8):
        return asyncio.iscoroutinefunction(func)
    else:
        # Note that there is something special about the AsyncMock
        # such that it isn't determined as a coroutine function
        # without an explicit check.
        try:
            from mock import AsyncMock

            if isinstance(func, AsyncMock):
                return True
        except ImportError:
            # Not testing, no asynctest to import
            pass
        while inspect.ismethod(func):
            func = func.__func__
        while isinstance(func, functools.partial):
            func = func.func
        if not inspect.isfunction(func):
            return False
        result = bool(func.__code__.co_flags & inspect.CO_COROUTINE)
        return result or getattr(func, "_is_coroutine", None) is asyncio.coroutines._is_coroutine


def retry(target, ok_function, on_retry=None, on_wait=None,
          max_retries=1, back_off_factor=1, wait_time=None, **kwargs):
    """
    Retry a given target function for a number of max retries or when the ok_function returns True.
    :param target: Function to execute.
    :param ok_function: Function to check the result of the target function. If the return is True, the execution of
    the target function will be terminated.
    :param on_retry: Event before the retry of the target function.
    :param on_wait: Event before waiting the next retry attempt.
    :param max_retries: Maximum number of retries.
    :param back_off_factor: Back-off factor of the incremental wait time. Default behavior.
    :param wait_time: If set, it will be used as a fixed wait time instead of the incremental wait time.
    :param kwargs: Arguments of the target function.
    :return: Tuple (result, is_ok), where "result" is the return of the target function, and "is_ok" is True if
    the target function has been executed successfully.
    """
    result, is_ok, current_retry = None, False, 1
    should_retry = current_retry <= max_retries
    while should_retry:
        if on_retry is not None:
            on_retry(current_retry, max_retries, **kwargs)
        result = target(**kwargs)
        is_ok = ok_function(result)
        should_retry = not is_ok and current_retry <= max_retries
        if should_retry:
            if wait_time is None:
                wait_time = back_off_factor * (2 ** (current_retry - 1))
            if on_wait is not None:
                on_wait(wait_time, current_retry, max_retries, **kwargs)
            time.sleep(wait_time)
            current_retry += 1
    return result, is_ok


class _SchemaItem:

    def __init__(self, id: str, schema: dict, cls):
        self._id: str = id
        self._schema: dict = schema
        self._cls = cls

    @property
    def id(self) -> str:
        return self._id

    @property
    def schema(self) -> dict:
        return self._schema

    @property
    def cls(self):
        return self._cls


def scrape_schema_items(directory: str, schema_name: str, script_name: str) -> List[_SchemaItem]:
    """
    Get schema items by scraping a given directory.
    Eventual pre-existent commands with same names will be overwritten.
    :param directory: Directory to scrape.
    :param schema_name: Name of the schema (JSON file) to load.
    :param script_name: Name of the script to load.
    """
    # Check if the directory exists
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory path '{directory}' not found.")
    # Errors list
    items: List[_SchemaItem] = list()
    # For each item in the directory
    for item_id in os.listdir(directory):
        item_directory = os.path.join(directory, item_id)
        # Ignore if the found item is not a directory or is a protected directory
        if not os.path.isdir(item_directory) or item_id.startswith("_"):
            continue
        # Find the the schema and the script of the item
        schema_path = os.path.join(item_directory, f"{schema_name}.json")
        script_path = os.path.join(item_directory, f"{script_name}.py")
        # If the command files does not exist, continue
        if not os.path.exists(script_path) or not os.path.exists(schema_path):
            continue
        # Open the command schema file
        with open(schema_path) as f:
            # Get the schema
            schema = json.loads(f.read())
        # Get the item class name
        item_class_name = schema.pop("class_name")
        # Get the module
        module_root: str = directory.replace("\\", ".").replace("/", ".")
        module = None
        while module_root:
            try:
                module_name = ".".join([module_root, item_id, script_name])
                module = importlib.import_module(module_name)
                break
            except:
                module_root = ".".join(module_root.split(".")[1:])
        # Check if the module is valid
        if module is None:
            LOGGER.warning(ModuleNotFoundError(f"Error while loading '{item_id}': could not find any valid module."))
            continue
        # Get the item class
        if not hasattr(module, item_class_name):
            LOGGER.warning(AttributeError(f"Module '{module}' has not class named '{item_class_name}'."))
            continue
        items.append(_SchemaItem(item_id, schema, getattr(module, item_class_name)))
    return items


def lcm(x: Union[int, float], y: Union[int, float]) -> int:
    """
    Get the lower common multiplier of two numbers. Supports both integer and floats.
    :param x: First number to get LCM.
    :param y: Second number to get the LCM.
    :return: The integer LCM of the two numbers.
    """
    max_digits = 3
    n = 1
    if isinstance(x, float) or isinstance(y, float):
        xd, yd = round(decimal.Decimal(x), ndigits=max_digits), round(decimal.Decimal(y), ndigits=max_digits)
        n = 10**max(abs(xd.as_tuple().exponent), abs(yd.as_tuple().exponent))
    x = int(x*n)
    y = int(y*n)
    greater = max(x,y)
    while True:
        if not greater % x and not greater % y:
            result = greater
            break
        greater += 1
    f_result = result / n
    if int(f_result) != f_result:
        return lcm(f_result, 1)
    return int(f_result)


def async_queue(event_loop: asyncio.AbstractEventLoop) -> asyncio.Queue:
    """ Create a cross-version compatible asyncio Queue. """
    queue_kwargs = dict(loop=event_loop) if version.lt(3, 10) else dict()
    return asyncio.Queue(**queue_kwargs)


def decode(obj: Union[str, bytes], encoding: str = 'utf-8'):
    """
    Decode an object based on an encoding type.
    :param obj: Object to decode.
    :param encoding: The encoding to use, default is UTF-8.
    :return: A dictionary, if the object contains an encoded JSON, else a string of the decoded object.
    """
    if isinstance(obj, bytes):
        string = obj.decode(encoding)
    elif isinstance(obj, str):
        string = obj
    else:
        raise ValueError("Data must be of type str, bytes or MQTTMessage.")
    if any(string.startswith(x) for x in ['[', '{']):
        return json.loads(string)
    return string


def ensure_async(func: Callable[..., Any]) -> Callable[..., Awaitable[Any]]:
    """ Ensure that the returned function is async (can be called to create a coroutine). """
    if is_coroutine_function(func):
        return func
    return run_sync(func)
