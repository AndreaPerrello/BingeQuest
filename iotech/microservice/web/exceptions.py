from . import configs


class WebServiceExtensionError(Exception):

    def __init__(self, message="An unspecified Core API Extension error has occurred"):
        super().__init__(message)


class WebServiceExtensionNotConfigured(WebServiceExtensionError):

    def __init__(self, module_name: str):
        super().__init__(f"API Extension '{module_name}' is not configured")


class WebServiceMissingDBConfiguration(WebServiceExtensionError):

    def __init__(self, *args, **kwargs):
        super().__init__(f"Missing configuration {configs.WEBSERVICE_DB_FILE_DIR}")


class WebServiceExtensionModuleNotFound(WebServiceExtensionError):
    def __init__(self, module_name: str):
        Exception(f"Module '{module_name}' not found")


class WebServiceExtensionModuleClassNotFound(WebServiceExtensionError):

    def __init__(self, module_name: str, class_name: str):
        super().__init__(f"Class '{class_name}' not found in module '{module_name}'")
