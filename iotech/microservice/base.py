import abc
import inspect
import threading
from typing import List

from .interface import ServiceInterface, _BaseService
from .classes import ShutdownAlert
from ..utils import classes

import logging
LOGGER = logging.getLogger(__name__)


class BaseService(abc.ABC, _BaseService):

    # noinspection PyTypeChecker
    def __init__(self):
        super().__init__()
        # Status
        self._status: classes.Status = None
        # Shutdown alert channel
        self._shutdown_alert: ShutdownAlert = None
        # Stop lock
        self._stop_lock: threading.Lock = None

    # Properties

    @property
    def status(self) -> classes.Status:
        return self._status

    @classmethod
    def _get_interfaces(cls):
        """
        :rtype: List[ServiceInterface]
        """
        return [c for c in inspect.getmro(cls)[0].__bases__
                if ServiceInterface in inspect.getmro(c)]

    def _init(self):
        """ Initialization procedure of the service. """
        LOGGER.info(f"Initializing service..")
        # Set status as uninitialized
        self._status: classes.Status = classes.Status.UNINITIALIZED
        # Create the shutdown alert channel
        self._shutdown_alert: ShutdownAlert = ShutdownAlert()
        # Create the stop lock
        self._stop_lock = threading.Lock()
        # Initialize service interfaces
        for interface in self._get_interfaces():
            interface.interface_init(self)

    def _execute_on_init(self):
        # On initialization event
        self.on_init()

    @classmethod
    def run(cls):
        from . import startup
        startup.cmd_run(cls)

    def _run(self):
        """ Internal run procedure of the service. Called only if no interface is defined for the service. """

    def _start(self):
        """ Internal start procedure. """
        interfaces = self._get_interfaces()
        if interfaces:
            if len(interfaces) > 1:
                raise Exception(f"Cannot run with multiple interfaces: {', '.join(i.__name__ for i in interfaces)}.")
            # Start with the service interface run procedure
            interfaces[0].interface_run(self)
        else:
            # Start with the internal service run procedure
            self._run()

    def start(self, initialize: bool = True):
        """ Start the service. Can be optionally initialized, then starts the scheduler and an async-io loop. """
        # Call procedure for the initialization
        if initialize:
            # Internal initialization the module
            self._init()
            # On initialization event
            self._execute_on_init()
            # After initialization event
            self._after_init()
            # Set status initialized
            self._status = classes.Status.INITIALIZED
        # Loop run
        if not self.should_stop:
            # Internal start of the module
            self._before_start()
            # On start event
            self.on_start()
            # Set status started
            self._status = classes.Status.STARTED
            LOGGER.info("Service: started")
            # Start the service
            self._start()
        # Execute the stop procedure
        self._execute_stop()

    def _stop(self):
        """ Internal stop procedure. """
        # Stop service interfaces
        for interface in self._get_interfaces():
            interface.interface_stop(self)

    def _after_stop(self):
        """ Procedure after the stop of the service. """
        pass

    def _execute_stop(self):
        """ Execute the stop procedure of the service. """
        # Acquire priority to stop the service
        with self._stop_lock:
            # Return if already required to stop
            if self._status.is_stopping or self.status.is_stopped:
                return
            # Set status stopping
            self._status = classes.Status.STOPPING
            # Internal stop of the module
            self._stop()
            # On stop event
            self.on_stop()
            # Set the status stopped
            self._status = classes.Status.STOPPED
            LOGGER.info("Service: stopped")
        # After stop event
        self._after_stop()

    def stop(self, message: str = None, logger=LOGGER.critical, *_args, **_kwargs):
        """
        Signals to stop the service. Restarts currently not implemented due to asyncio conflicts when required from
        an event loop task.
        :param message: (optional) Message to logger at the stop of the service.
        :param logger: (optional) Logger to use for the logger message. If none is give, the default logger with
        critical level will be used.
        """
        # Check logging
        if message:
            logger(message)
        # Ignore if the service has no status or is already stopping
        if self.status and not self.should_stop:
            # Execute the stop procedure
            return self._execute_stop()

    def restart(self):
        """ Restart the service. """
        return self.stop(restart=True)

    @property
    def should_stop(self) -> bool:
        """ Check if the service stop request has been received and should stop the execution. """
        return self._status.is_stopping

    def _shutdown(self, message: str = None, logger=LOGGER.info, **kwargs):
        """
        Thread-safe shutdown the execution of the service.
        :param message: (optional) Message to log at shutdown. If not specified, a generic message will be used.
        :param logger: (optional) Logging function to use to log the message. If not specified,
        the default logger with info level will be used.
        """
        if message is None and self._shutdown_alert is not None:
            message = self._shutdown_alert.message
        if message is not None:
            if isinstance(message, Exception):
                logger = LOGGER.critical
                message = f"Uncaught exception abort: {message}"
        # If the shutdown came from a thread, signal the shutdown alert
        if threading.current_thread() != threading.main_thread() and self._shutdown_alert is not None:
            return self._shutdown_alert.signal(message)
        # Return the stop signal
        return self.stop(message, logger, **kwargs)

    def abort(self, message: str = None):
        """
        Abort the service execution, shutting down with critical level.
        :param message: Abort message to logger.
        """
        return self._shutdown(message, LOGGER.critical, wait=False)

    def default_shutdown(self):
        """
        Default shutdown of the plugin execution.
        """
        return self._shutdown("Default shutdown")
