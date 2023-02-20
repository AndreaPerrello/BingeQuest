class ConfiguratorError(Exception):
    """Raised when an Configurator error occurs."""

    def __init__(self, message="An unspecified Configurator error has occurred"):
        super().__init__(message)


class ConfigFileDoesNotExists(ConfiguratorError):

    def __init__(self, config_file_path):
        super().__init__(f"Config file '{config_file_path}' does not exist")


class ValueTypeNotAllowed(ConfiguratorError):

    def __init__(self, option, data_type):
        super().__init__(f"Value of '{option}' must be None or type '{data_type}'")


class SetValueError(ConfiguratorError):

    def __init__(self, value, reason):
        super().__init__(f"Could not set the value '{value}'. Reason: {reason}")


