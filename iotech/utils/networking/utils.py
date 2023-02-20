import os
import socket


def is_docker() -> bool:
    """
    Check whether the software is running in a Docker environment.
    :return: True if the software is running in Docker, False elsewhere.
    """
    is_env = os.path.exists('/.dockerenv')
    path = '/proc/self/cgroup'
    return is_env or os.path.isfile(path) and any('docker' in line for line in open(path))


def ping(host: str, port: int) -> bool:
    """
    Ping an address by host and port.
    :param host: The host of the target to ping.
    :param port: The port of the host to ping.
    :return: True if the ping is successful, False elsewhere.
    """
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect_ex((host, port)) == 0
