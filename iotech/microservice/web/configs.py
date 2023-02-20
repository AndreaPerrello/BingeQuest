import os
import uuid

from ...configurator import Config


WEBSERVICE_DB_FILE_DIR = Config(str, "WEBSERVICE", "db_file_dir", None)
WEBSERVICE_HOST = Config(str, "WEBSERVICE", "host", "0.0.0.0")
WEBSERVICE_SSL = Config(bool, "WEBSERVICE", "ssl", False)
WEBSERVICE_SERVER_HOST = Config(str, "WEBSERVICE", "server_host", None)
WEBSERVICE_PORT = Config(int, "WEBSERVICE", "port", 5000)
WEBSERVICE_ALLOW_ORIGINS = Config((list, str), 'WEBSERVICE', 'allow_origins', None)
WEBSERVICE_ALLOW_CREDENTIALS = Config(bool, 'WEBSERVICE', 'allow_credentials', False)


def WEBSERVICE_DB_URI() -> str:
    db_file_dir = WEBSERVICE_DB_FILE_DIR.get()
    if db_file_dir is None:
        db_uri = Config(str, "WEBSERVICE", "db_uri", None).get()
    else:
        db_uri = f"sqlite:///{os.path.abspath(os.path.join(db_file_dir, 'repository.db'))}"
    return db_uri


def WEBSERVICE_HAS_DATABASE() -> bool:
    return WEBSERVICE_DB_URI() is not None


def WEBSERVICE_ENDPOINT() -> str:
    protocol = "https" if WEBSERVICE_SSL.get() else "http"
    default_host = "localhost" if WEBSERVICE_HOST.get() == "0.0.0.0" else WEBSERVICE_HOST.get()
    host = WEBSERVICE_SERVER_HOST.get(fallback=default_host)
    base_endpoint = f"{protocol}://{host}"
    return f"{base_endpoint}:{WEBSERVICE_PORT.get()}"


class WebServiceAppConfig:
    ERROR_404_HELP = False
    SECRET_KEY = uuid.uuid4().hex

    def __init__(self):
        if WEBSERVICE_HAS_DATABASE():
            self.SQLALCHEMY_DATABASE_URI = WEBSERVICE_DB_URI()
            self.SQLALCHEMY_TRACK_MODIFICATIONS = False
            self.RAPIDOC_CONFIG = {"allow-try": True, "theme": "light",
                                   "show-header": False, "show-components": True}
