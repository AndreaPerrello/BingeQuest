import distutils.util
import math
from typing import Any, List

import jinja2


class BaseRenderEnv(jinja2.Environment):

    def __init__(self):
        """
        Basic rendering environment based on Jinja.
        Can be extended with filters by applying it on the global render env.
        """
        super().__init__(undefined=jinja2.StrictUndefined)
        self.filters['split'] = self.split
        self.filters['split_get'] = self.split_get
        self.filters['join'] = self.join
        self.filters['lower'] = self.lower

    @staticmethod
    def join(strings: List[str], with_: str):
        return with_.join(strings)

    @staticmethod
    def split(string: str, sep: str):
        return string.split(sep)

    def split_get(self, string: str, sep: str, index: int = 0):
        return self.split(string, sep)[index]

    @staticmethod
    def lower(string: str):
        return string.lower()


# Global rendering environment
env = BaseRenderEnv()


def safe_coerce_to(obj: Any, data_type: str, raise_: bool = True) -> Any:
    if not any(isinstance(obj, x) for x in [str, int, float, bool]):
        if raise_:
            raise ValueError(f"Coercion of object '{obj}' is not safe.")
    if data_type in ['str', 'string']:
        return str(obj)
    elif data_type in ['int', 'integer']:
        try:
            return int(obj)
        except ValueError:
            pass
    elif data_type in ['float', 'numeric']:
        try:
            return float(obj)
        except ValueError:
            pass
    elif data_type in ['bool', 'boolean']:
        try:
            if isinstance(obj, bool):
                return obj
            return bool(distutils.util.strtobool(obj))
        except (ValueError, AttributeError):
            pass
    if raise_:
        raise ValueError(f"Coercion of object '{obj}' to '{data_type}' failed.")


def coerce_string(string: str) -> Any:
    # Try to cast to integer number
    try:
        return int(string)
    except ValueError:
        pass
    # Try to cast to float number
    try:
        return float(string)
    except ValueError:
        pass
    try:
        return bool(distutils.util.strtobool(string))
    except ValueError:
        pass
    # Return the plain string
    return string


def _render_object(string: str, **kwargs):
    """
    Render a string from the global render environment with optional key-value formatting arguments.
    :param string: String to render/format.
    :param kwargs: Key-value arguments to render/format the string.
    :return: Rendered/formatted string.
    """
    return coerce_string(env.from_string(str(string)).render(**kwargs))


# noinspection PyTypeChecker
def is_null(x: object) -> bool:
    """
    Safe check if an object is None or NaN. String objects are always not null.
    :param x: Object to check.
    :return: True if the object is null, False elsewhere.
    """
    if isinstance(x, str):
        return False
    return any([x is None, str(x).isnumeric() and math.isnan(x)])


def safe_render(string: str, _fallback=None, _skip_null: bool = True, **kwargs):
    """
    Safely render a string using formatting key-value arguments, with a fallback option.
    :param string: The string to format.
    :param _fallback: (optional) Fallback value if the format fails.
    :param _skip_null: (optional) Skip null values in the formatting arguments.
    :param kwargs: Key-value arguments to format the string.
    :return: Formatted string.
    """
    if not isinstance(string, str):
        return string
    if string is None:
        return _fallback
    if _skip_null:
        kwargs = {k: str(v) for k, v in kwargs.items() if not is_null(v)}
    try:
        return _render_object(string, **kwargs)
    except:
        return _fallback


def render_dict(data: dict, formatting: dict) -> dict:
    """
    Render a dictionary with formatting arguments from another dictionary of data.
    :param data: Dictionary of data to render/format.
    :param formatting: Dictionary of data to use to render/format the main dictionary.
    :return: Original dictionary with rendered/formatted values.
    """
    properties = dict()
    for k, v in data.items():
        if isinstance(v, dict):
            properties[k] = render_dict(v, formatting)
        else:
            properties[k] = safe_render(v, **formatting)
    return {k: v for k, v in properties.items() if v != 'None' and v is not None}


def from_template(template_path: str, _env: BaseRenderEnv = None, **kwargs):
    _env = _env or BaseRenderEnv
    with open(template_path) as f:
        return _env.from_string(f.read()).render(**kwargs)
