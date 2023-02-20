import ipaddress
import socket
import sys
from typing import Iterable, List

import psutil


def ipv4s() -> Iterable[tuple]:
    """ Get the iterable of IPV4 addresses. """
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == socket.AF_INET:
                yield interface, snic.address


def basic_socket(udp: bool = False, proto: int = None, broadcast: bool = False) -> socket.socket:
    """
    Creates a basic socket.
    :param udp: (optional) Flag to set the UDP protocol.
    :param proto: (optional) Protocol to use.
    :param broadcast: (optional) Flag to enable broadcasting.
    :return: The socket.
    """
    proto = socket.IPPROTO_UDP if udp else proto
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, proto=proto)
    if sys.platform in ["linux", "linux2"]:
        if hasattr(socket, 'SO_REUSEPORT'):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    if broadcast:
        # Enable broadcasting mode
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    # Return the socket
    return s


def get_broadcast_ips() -> List[str]:
    """
    Get all the possible broadcast IPs of the current network interface.
    :return: List of possible IP string for the broadcasting.
    """
    ips = list()
    for _, host in ipv4s():
        s = basic_socket(udp=True)
        s.connect((host, 80))
        for mask in [8, 16, 24]:
            try:
                ip = s.getsockname()[0]
                ip_interface = ipaddress.IPv4Interface(f"{ip}/{mask}")
                ips.append(str(ip_interface.network.broadcast_address))
            except:
                pass
    return ips
