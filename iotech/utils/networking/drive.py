import os

from . import configs

import logging
LOGGER = logging.getLogger()


def map_network_drive(network_path: str, drive: str, username: str = None, password: str = None, force: bool = False):
    """
    Map a network path to a drive.
    :param network_path: Path of the network to mount.
    :param drive: Drive to mount.
    :param username: (optional) Username of the network.
    :param password: (optional) Password of the network.
    :param force: (optional) Flag to force the unmount/re-mount of the drive.
    """
    try:
        import win32wnet
    except Exception:
        raise ModuleNotFoundError(f"Failed to map network '{network_path}' to drive '{drive}': pywin32 not found.")
    if os.path.exists(network_path):
        raise OSError(f"Network path '{network_path}' is already mapped.")
    if os.path.exists(drive) and not force:
        raise ValueError(f"Drive '{drive}' is already mapped.")
    if force:
        try:
            win32wnet.WNetCancelConnection2(drive, 1, 1)
        except Exception as e:
            raise RuntimeError(f"Failed to unmap drive '{drive}': {e}")
    net_resource = win32wnet.NETRESOURCE()
    net_resource.lpLocalName = drive
    net_resource.lpRemoteName = network_path
    win32wnet.WNetAddConnection2(net_resource, username, password, 0)


def configs_map_network_drive():
    """ Map the network path to drive, based on configurations. """
    network_path = configs.NETWORK_PATH.get()
    drive = configs.NETWORK_DRIVE.get()
    if network_path and drive:
        try:
            map_network_drive(
                network_path, drive,
                username=configs.NETWORK_USERNAME.get(),
                password=configs.NETWORK_PASSWORD.get(),
                force=configs.NETWORK_FORCE_MAP.get())
            LOGGER.info(f"Network path '{network_path}' mapped on drive '{drive}'")
        except Exception as e:
            LOGGER.error(e)
