from ...configurator import Config

NETWORK_DRIVE = Config(str, "NETWORK", "drive", None)
NETWORK_PATH = Config(str, "NETWORK", "path", None)
NETWORK_USERNAME = Config(str, "NETWORK", "username", None)
NETWORK_PASSWORD = Config(str, "NETWORK", "password", None)
NETWORK_FORCE_MAP = Config(bool, "NETWORK", "force_map", False)
