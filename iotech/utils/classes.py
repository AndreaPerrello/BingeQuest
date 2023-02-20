import enum


class Singleton:

    def __init__(self, _cls):
        """
        Decorator class to implement the "singleton" design pattern.
        :param _cls: Class to apply the singleton pattern to.
        """
        self._cls = _cls
        self._instance = None

    def __call__(self, *args, **kwds):
        if self._instance is None:
            self._instance = self._cls(*args, **kwds)
        return self._instance


class Status(enum.Enum):
    UNKNOWN = -1
    UNINITIALIZED = 0
    INITIALIZED = 1
    STARTED = 2
    STOPPING = 3
    STOPPED = 4

    def __eq__(self, other):
        return self.value.__eq__(other.value)

    def __gt__(self, other):
        return self.value.__gt__(other.value)

    def __lt__(self, other):
        return self.value.__lt__(other.value)

    def __le__(self, other):
        return self.value.__le__(other.value)

    def __ge__(self, other):
        return self.value.__ge__(other.value)

    @property
    def is_initialized(self) -> bool:
        """ Check if the status is (at least) initialized. """
        return self >= self.INITIALIZED

    @property
    def is_running(self) -> bool:
        """ Check if the status is running (started and not stopped). """
        return self.STARTED <= self < self.STOPPED

    @property
    def is_stopping(self) -> bool:
        """ Check if the status is stopping. """
        return self == self.STOPPING

    @property
    def is_stopped(self) -> bool:
        """ Check if the status is stopped. """
        return self == self.STOPPED
