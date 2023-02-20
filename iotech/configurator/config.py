import configparser
import distutils.util
import os
from typing import List, Dict

import expandvars

from ..utils import version
from . import exceptions

if version.lt(3, 10):
    from collections import Generator
else:
    from collections.abc import Generator

import logging
LOGGER = logging.getLogger(__name__)

_UNSET = object()


class _ConfigInterpolation(configparser.BasicInterpolation):

    def before_get(self, parser, section, option, value, defaults):
        return expandvars.expandvars(value)


class _ConfigParser(configparser.ConfigParser):

    def __init__(self):
        super().__init__(interpolation=_ConfigInterpolation())


class Config:
    parser = _ConfigParser()
    directory = None
    file_names = None
    _local_values = dict()

    def __init__(self, data_type, section: str, option: str = None, fallback=_UNSET):
        self._data_type = data_type
        self._is_none: bool = False
        self._section: str = section
        self._option: str = option
        self._fallback: object = fallback
        self._gen_value = _UNSET

    def __repr__(self):
        return f"'{self._option}' in section {self._section}"

    @staticmethod
    def init(directory, *file_names, ignore_error=False):
        # Set the directory of the configuration files to use
        Config.directory = directory
        # Load the configuration files
        Config.load(*file_names, ignore_error=ignore_error)

    @staticmethod
    def path(target):
        if isinstance(target, Config):
            yield os.path.join(Config.directory, target.get())
        yield os.path.join(Config.directory, target)

    @staticmethod
    def dir(target=""):
        return os.path.join(Config.directory, target)

    @staticmethod
    def load(*file_names, encoding=None, ignore_error=False):
        # If configuration should only be reloaded
        if not file_names:
            file_names = Config.file_names
        # Set file names
        Config.file_names = file_names
        # Build the real path of each configuration file
        config_file_paths = [os.path.join(Config.directory, file_name) for file_name in file_names]
        # Check if the file exists
        valid_file_paths = []
        for config_file_path in config_file_paths:
            if not os.path.isfile(config_file_path):
                if not ignore_error:
                    raise exceptions.ConfigFileDoesNotExists(config_file_path)
            else:
                valid_file_paths.append(config_file_path)
        # Parse and read the configurations
        Config.parser.read(valid_file_paths, encoding)

    def get(self, option=None, fallback=None, nocache: bool = False, **kwargs):
        fallback = fallback or self._fallback
        if self._is_none:
            return None if fallback is _UNSET else fallback
        option = option or self._option
        if fallback is _UNSET:
            value = Config.parser.get(self._section, option)
        else:
            if isinstance(fallback, Config):
                fallback = fallback.get()
            _args = (self._section, option)
            v = Config.parser.get(*_args, fallback=fallback)
            if nocache:
                value = v
            else:
                value = self._local_values.get(_args, v)
            if value == '':
                value = self._fallback
        # Check the value
        if value is None:
            return None
        if isinstance(value, Generator):
            if self._gen_value is _UNSET:
                self._gen_value = next(value)
            return self._gen_value
        # Check data type
        if isinstance(self._data_type, type):
            if self._data_type == bool:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return bool(distutils.util.strtobool(value))
            elif self._data_type == str and kwargs:
                value = str(value).format(**kwargs)
        elif isinstance(self._data_type, tuple):
            if isinstance(value, str):
                value = [str(x).strip() for x in value.split(",")]
            collection, data_type = self._data_type
            if collection == list:
                return [data_type(v) for v in value]
        # Return the casted value
        return self._data_type(value)

    def set(self, value):
        if value is not None:
            if not isinstance(value, self._data_type):
                raise exceptions.ValueTypeNotAllowed(self._option, type(self._data_type).__name__)
            self._is_none = False
            value = self._data_type(value)
        else:
            self._is_none = True
            return
        if self._section not in Config.parser.sections():
            Config.parser.add_section(self._section)
        try:
            Config.parser.set(self._section, self._option, str(value))
            self._local_values[(self._section, self._option)] = str(value)
        except Exception as e:
            raise exceptions.SetValueError(value, str(e))

    def get_or_set(self, default):
        self.set(self.get(fallback=default))

    @staticmethod
    def update(data):
        for section, data in data.items():
            if section not in Config.parser.sections():
                Config.parser.add_section(section)
            for option, value in data:
                Config.parser.set(section, option, value)

    @staticmethod
    def save(filename: str = None):
        if not filename:
            if len(Config.file_names) == 1:
                filename = Config.file_names[0]
            else:
                raise ValueError("Must provide a filename to save if configuration files are zero or multiple.")
        with open(Config.dir(filename), 'w') as f:
            Config.parser.write(f)

    @staticmethod
    def data(sections: List[str] = None):
        sections = sections or Config.parser.sections()
        return {s: Config.parser.items(s) for s in sections}

    @classmethod
    def from_dict(cls, section: str, options: dict) -> Dict[str, str]:
        data = {option_head: dict() for option_head in options}
        for option_head, option_tails in options.items():
            for _type, option_tail in option_tails:
                option = '_'.join([option_head, option_tail])
                if Config.parser.has_option(section, option):
                    data[option_head][option_tail] = Config(_type, section, option).get()
        return data
