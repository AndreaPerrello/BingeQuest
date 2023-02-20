import os
import importlib
import pathlib
from typing import List, Callable

from . import exceptions

import logging
LOGGER = logging.getLogger(__name__)


class TemplateManager:

    def __init__(self):
        self._templates: dict = dict()

    def init(self, templates_dir: str, **directions: List[str]):
        """
        Initialize the template directory and the related directions and functions.
        :param templates_dir: Directory containing the templates folders.
        :param directions: Dictionary of allowed directions for the conversion; each direction contains a list of
        allowed function names that can be called for the conversion in the related direction.
        """
        pathlib.Path(templates_dir).mkdir(parents=True, exist_ok=True)
        for template_name in os.listdir(templates_dir):
            template_directory = os.path.join(templates_dir, template_name)
            if not os.path.isdir(template_directory):
                continue
            self._templates[template_name] = dict()
            for direction_name, functions in directions.items():
                template_direction_file = os.path.join(template_directory, direction_name)
                template_direction_file_path = ".".join([template_direction_file, "py"])
                if not os.path.exists(template_direction_file_path):
                    raise FileNotFoundError(f"No template '{template_direction_file_path}' found")
                self._templates[template_name][direction_name] = dict()
                module_name = template_direction_file.replace(os.path.sep, ".")
                module = importlib.import_module(module_name)
                for function_name in functions:
                    function = getattr(module, function_name, None)
                    if function is not None:
                        self._templates[template_name][direction_name][function_name] = function
                        LOGGER.info(f"Loaded template '{template_name}' ({direction_name}.{function_name})")

    def _get_function(self, template_name: str, direction: str, function_name: str) -> Callable:
        """
        Get a templating function filtering by template, direction and function name.
        :param template_name: Name of the template.
        :param direction: Direction of the function in the template, which is the sub file in the template directory.
        :param function_name: Name of the function related to the direction script.
        :return: The callable function if exists, else None.
        """
        return self._templates.get(template_name, {}).get(direction, {}).get(function_name)

    def convert(self, template_name: str, direction: str, function_name: str, data, **kwargs) -> object:
        """
        Convert data on a template with given direction and function.
        :param template_name: Name of the template.
        :param direction: Direction for the conversion.
        :param function_name: Name of the function in the given direction.
        :param data: Data to convert.
        :param kwargs: Optional key-value arguments for the conversion function.
        :return: The result of the templating function.
        """
        func = self._get_function(template_name, direction, function_name)
        if func is not None:
            try:
                return func(data=data, **kwargs)
            except Exception as e:
                raise exceptions.TemplateConversionError(
                    template_name, direction, function_name, data, kwargs, str(e))
