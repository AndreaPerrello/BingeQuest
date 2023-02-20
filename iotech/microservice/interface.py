import abc


class _BaseService(object):

    def _after_init(self):
        """ Internal after initialization event. """

    def _before_start(self):
        """ Internal start event. """

    def _stop(self):
        """ Internal stop event. """

    async def on_init(self):
        """ On initialization event of the service. """

    def on_start(self):
        """ On start event of the service. """
        pass

    def on_stop(self):
        """ On stop event of the service. """
        pass


class ServiceInterface(abc.ABC, _BaseService):

    @staticmethod
    @abc.abstractmethod
    def interface_init(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def interface_run(self):
        pass

    @staticmethod
    @abc.abstractmethod
    def interface_stop(self):
        pass
