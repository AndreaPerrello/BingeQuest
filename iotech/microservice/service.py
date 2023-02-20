import asyncio
import inspect
from typing import Callable, Coroutine, Awaitable, Union, Optional

from apscheduler.events import JobExecutionEvent
from apscheduler.job import Job
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .base import BaseService
from ..utils import timing, functions

import logging
LOGGER = logging.getLogger(__name__)
logging.getLogger("apscheduler.scheduler").setLevel(logging.ERROR)
logging.getLogger("apscheduler.executors").setLevel(logging.ERROR)
logging.getLogger("apscheduler.executors.default").setLevel(logging.ERROR)


class MicroService(BaseService):
    """
    Framework for a self-managed base-service based on asyncio.
    Based on an "init-start-stop" stages design with asynchronous and scheduled functions.
    Handles the basic lifecycle of the service and its execution, without need of further development.
    The class allows to just define custom public behaviours on the three stages (initialization, start and stop);
    It also provides interfaces to:
        - Implement optional internal behaviours (to create new frameworks that manage and hide internal processes);
        - Schedule both synchronous and asynchronous jobs;
        - Shutdown (both gracefully or abortively) the service without breaking the workflow;
        - Control the state of the service.
    Can be integrated with add-ons to integrate new functions (e.g. APIService to expose REST APIs).
    """

    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__()
        #  Async-io loop
        self._event_loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        # Scheduler
        self._scheduler: AsyncIOScheduler = None
        # Stop objects
        self._loop_stop_event: asyncio.Event = None

    # Loop

    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        return self._event_loop

    def _after_init(self):
        # Schedule the run of interfaces
        for interface in self._get_interfaces():
            # Add interface run job
            self.add_job(interface.interface_run, args=(self,))

    def _scheduler_listener(self, event: JobExecutionEvent):
        if hasattr(event, 'exception') and event.exception is not None:
            if isinstance(event.exception, KeyboardInterrupt):
                return self.stop()
            elif isinstance(event.exception, RuntimeError):
                return self.stop(str(event.exception))
            LOGGER.error(event.exception)

    def _init(self):
        super()._init()
        # Create the scheduler with an in-memory job store for protected internal jobs
        self._scheduler = AsyncIOScheduler(event_loop=self._event_loop)
        self._scheduler.add_listener(self._scheduler_listener)
        self._scheduler.add_jobstore(MemoryJobStore(), '_internal')
        # Create stop events and lock
        self._loop_stop_event = asyncio.Event()

    def _execute_on_init(self):
        result_or_coro = self.on_init()
        if inspect.iscoroutine(result_or_coro):
            self._event_loop.create_task(result_or_coro)

    def _start(self):
        # Start scheduler
        self._scheduler.start()

        async def _loop_stop_signal():
            """ Asynchronous stop request waiter event for the asyncio loop. """
            await self._loop_stop_event.wait()
        try:
            # Run the loop until stop waiter completes
            self._event_loop.run_until_complete(_loop_stop_signal())
        except KeyboardInterrupt:
            LOGGER.warning("Keyboard Interrupt received, exiting..")
            self.on_interrupt()
        except RuntimeError as e:
            LOGGER.error(e)

    def _stop(self):
        # Internally signal the stop event to complete the event loop, needed when exception are
        # raised from inside a task of the event loop
        if self._loop_stop_event:
            self._loop_stop_event.set()
        # Super call
        super()._stop()

    def _after_stop(self):
        if self._event_loop:
            # Stop the event loop
            self._event_loop.stop()
        if self._scheduler:
            # Remove all jobs
            self._scheduler.remove_all_jobs()
            # Shut down the scheduler
            try:
                self._scheduler.shutdown()
            except:
                pass

    def on_interrupt(self):
        pass

    # Scheduler

    def add_job(self, func: Union[Callable, Coroutine, Awaitable], *args,
                force: bool = False, **kwargs) -> Optional[Job]:
        """
        Add a function or job to execute, in the internal service scheduler, in the event loop or in a executor.
        - If a scheduled job is provided, it will be executed in the service scheduler.
        - If a coroutine is provided, it will be executed as a task in the event loop.
        - If a callable is provided, it will be executed in a executor by the event loop.
        The request proxies to the BaseScheduler 'add_job' method of APScheduler and supports both
        synchronous and asynchronous jobs with asyncio.
        Extends the functionality of the basic APScheduler supporting milliseconds intervals and one shot jobs.
        :param func: Callable of the task to schedule as a job.
        :param force: (optional) Flag to force the execution of the job until is completed.
        :param args: APScheduler default positional arguments. If no trigger type is specified,
        a one shot job is scheduled.
        :param kwargs: APScheduler default key-value arguments. If the trigger type 'interval' and kwarg 'milliseconds'
        is used, the job is scheduled with milliseconds interval.
        :return: The created Job, if scheduled, None elsewhere.
        """
        func = functions.ensure_async(func)
        delay = kwargs.pop('delay', None)
        if delay:
            async def _add_delayed():
                await asyncio.sleep(delay)
                self.add_job(func, **kwargs)
            self._event_loop.create_task(_add_delayed())
            return

        # Get args and kwargs
        _args = kwargs.pop('args', tuple())
        _kwargs = kwargs.pop('kwargs', dict())
        # Allow the job to run no matter how late it is
        kwargs['misfire_grace_time'] = None
        # Check if the job has a trigger
        trigger = kwargs.get('trigger', args and args[0] or None)
        # If no trigger, create a task in the loop for the function
        if trigger is None:
            # If is not a coroutine
            if force:
                # Run the coroutine until complete
                self._event_loop.run_until_complete(func())
            else:
                # Create the task and return
                # noinspection PyTypeChecker
                self._event_loop.create_task(func(*_args, **_kwargs))
            return
        elif trigger == 'interval':
            # Check if is milliseconds interval
            milliseconds = kwargs.pop('milliseconds', None)
            if milliseconds is not None:
                # Create the periodic sub job to execute
                sub_job: timing.PeriodicJob = timing.PeriodicJob.from_task_period(func, milliseconds / 1000)
                # Set the needed number of seconds for the sub job to complete
                kwargs['seconds'] = sub_job.seconds
                # Replace the job function with the sub job run function
                func = sub_job.start
        # Add the job store, if not exists
        job_store = kwargs.get('jobstore')
        if job_store:
            try:
                self._scheduler.add_jobstore(MemoryJobStore(), job_store)
            except ValueError:
                pass
        # Add the job to the scheduler
        return self._scheduler.add_job(func, *args, args=_args, kwargs=_kwargs, **kwargs)
