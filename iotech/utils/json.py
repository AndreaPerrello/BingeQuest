def _set(a: dict, b: dict):
    return {**a, **b}


def _delete(a: dict, b: dict):
    return {k: v for k, v in a.items() if k not in b}


def _extract(a: dict, b: dict):
    return {k: v for k, v in a.items() if k in b}


def _replace(a: dict, b: dict):
    return _set(a, _extract(b, a))


def _insert(a: dict, b: dict):
    return _set(a, _delete(b, a))


__map__ = {
    'set': _set, 'delete': _delete,
    'replace': _replace, 'insert': _insert,
    'extract': _extract
}


def j_update(a: dict, b: dict, operation: str = None):
    """
    Applies a JSON update operation to two dictionaries, without editing the sources. Default operation is 'set'.
    :param a: Dictionary to update (with most priority).
    :param b: Dictionary of the updates to apply (lesser priority).
    :param operation:
        - set: Replace in A items from B, and add new values.
        - replace: Replace in A items from B, and ignores new values.
        - insert: Adds new values from B in A, but does not replace existing values.
        - delete: Delete from A items with keys in B.
        - extract: Extract from A values with keys in B.
    :return: Updated dictionary.
    """
    operation = operation or 'set'
    if operation not in __map__:
        raise ValueError(f"Operation '{operation}' is not valid.")
    return __map__[operation](a, b)
