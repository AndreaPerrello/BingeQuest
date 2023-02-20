import sys
import operator


def _check_version(op, major: int, minor: int, micro: int) -> bool:
    info = sys.version_info
    return op((info.major, info.minor, info.micro), (major, minor, micro))


def lt(major: int, minor: int = 0, micro=0):
    return _check_version(operator.lt, major, minor, micro)


def le(major: int, minor: int = 0, micro=0):
    return _check_version(operator.le, major, minor, micro)


def gt(major: int, minor: int = 0, micro=0):
    return _check_version(operator.gt, major, minor, micro)


def ge(major: int, minor: int = 0, micro=0):
    return _check_version(operator.ge, major, minor, micro)
