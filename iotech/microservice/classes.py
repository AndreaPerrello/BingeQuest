class ShutdownAlert:

    def __init__(self):
        self._should = False
        self._message = None

    def reset(self):
        self._should = False
        self._message = None

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    @property
    def should(self):
        return self._should

    def signal(self, message=None):
        self._should = True
        self._message = message


