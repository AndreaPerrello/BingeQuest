import math
import time
import threading
from typing import Callable, Union

from .functions import lcm

import logging
LOGGER = logging.getLogger(__name__)


class PeriodicJob:
    _allowed_seconds = list(range(1, 61))

    # noinspection PyTypeChecker
    def __init__(self, task_function: Callable, period: float, times: int = None):
        """
        Periodic job for execution of a task with almost-exact period a given number of times.
        :param task_function: Task function for the job to execute.
        :param period: Period of the task execution (in seconds)
        :param times: (optional) Number of time to execute.
        If omitted, the job will be executed forever until stopped.

        Example:

        def task(job: PeriodicJob):
            if job.execution == 2:
                job.stop()

        PeriodicJob(task, 0.25, 4).start()
        """
        super().__init__()
        self._task_function: Callable = task_function
        self._period: float = period
        self._times: int = times
        self._should_stop: bool = False
        self._execution: int = None
        self._t0: float = None
        self._lock: threading.Lock = threading.Lock()

    @classmethod
    def from_task_period(cls, task_function: Callable, period: float):
        values = [lcm(period, seconds) for seconds in cls._allowed_seconds]
        k = min(range(len(values)), key=values.__getitem__)
        times = int(values[k] / period)
        return cls(task_function, period, times)

    @property
    def _finished(self) -> bool:
        """ Check if the task should finish running. """
        return self._should_stop or (self._times is None or self._execution > self._times)

    def start(self):
        """ Start a thread on the run function. """
        threading.Thread(target=self.run).start()

    def run(self):
        # Thread-safe lock
        with self._lock:
            # Reset executions
            self._execution = 1
            # Set starting time
            self._t0 = time.time()
            # Run until finished
            while not self._finished:
                # Execute task
                self._task_function(self)
                # Increase executions
                self._execution += 1
                # Temporized sleep
                delta = self._t0 + self._period * (self._execution - 1) - time.time()
                if delta > 0: time.sleep(delta)

    @property
    def execution(self) -> int:
        """ Get the current execution number. """
        return self._execution

    @property
    def times(self) -> float:
        """ Number of times the job should execute before stopping itself. If none, returns Inf. """
        return self._times if self._times is not None else math.inf

    @property
    def seconds(self) -> Union[float, int]:
        """ Number of seconds needed to complete the job. """
        if self._times is None:
            return math.inf
        return int(math.ceil(self._times * self._period))

    def stop(self):
        """ Stop the execution of the job prematurely. """
        self._should_stop = True
