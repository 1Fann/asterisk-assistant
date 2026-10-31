"""Solicit an IPv6 router advertisement on the PBX Wi-Fi interface."""
import ipaddress
import re
import socket
import struct
import sys


def solicit(source, mac):
    if not ipaddress.IPv6Address(source).is_link_local or not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac):
        raise ValueError("Expected Wi-Fi link-local and hardware addresses")
    index = socket.if_nametoindex("wlan0")
    # ICMPv6 type 133 and Source Link-Layer Address option, checksum filled by Linux.
    packet = struct.pack("!BBHI", 133, 0, 0, 0) + bytes([1, 1]) + bytes.fromhex(mac.replace(":", ""))
    with socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, b"wlan0\0")
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, index)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)
        sock.bind((source, 0, 0, index))
        sock.sendto(packet, ("ff02::2", 0, 0, index))


if __name__ == "__main__":
    solicit(*sys.argv[1:])
