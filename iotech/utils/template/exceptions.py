class TemplateError(Exception):
    """Raised when a Template error occurs."""

    def __init__(self, message="An unspecified Template error has occurred"):
        super().__init__(message)


class TemplateConversionError(TemplateError):

    def __init__(self, name: str, direction: str, func_name: str, data: object, kwargs: dict, reason: str):
        super().__init__(f"Conversion error of template '{name}/{direction}' in function "
                         f"'{func_name}' with data '{data} ({kwargs})'. Reason: {reason}")
