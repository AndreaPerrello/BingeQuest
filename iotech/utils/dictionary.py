import json
import collections


def clean(dd: dict):
    """
    Clean a dictionary, by converting all the nested json strings into dictionaries.
    :param dd: Dictionary to clean.
    :return: Dictionary of cleansed data.
    """
    for k in dd.keys():
        try:
            v = json.loads(dd[k].replace("'", "\""))
            if isinstance(v, dict): dd[k] = v
        except:
            pass


def deep_update(source: dict, overrides: dict=None) -> dict:
    """
    Deep update a nested dictionary. Works like the classic update, but with nested dictionaries of varying depth
    and does not update in-place.
    If one of the arguments is null, it will be treated as an empty dictionary.
    :param source: Source dictionary to update.
    :param overrides: (optional) Dictionary to override to the source.
    :return: Dictionary of values of the second dictionary overridden or added to the first.
    """
    deep = source.copy()
    overrides = overrides or dict()
    for key, value in overrides.items():
        if isinstance(value, collections.Mapping) and value:
            deep[key] = deep_update(deep.get(key, {}), value)
        else:
            deep[key] = overrides[key]
    return deep
