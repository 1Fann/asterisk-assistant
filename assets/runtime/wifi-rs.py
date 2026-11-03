"""Solicit an IPv6 router advertisement on the PBX Wi-Fi interface."""
import ipaddress
import re
import socket
import struct
import sys


def field(words, key, default=None):
    if key not in words:
        return default
    return words[words.index(key) + 1]


def route_ready(source, lookup, defaults):
    """Verify the selected WLAN next hop against the applicable default's lease."""
    try:
        address = ipaddress.IPv6Address(source)
        path = lookup.split()
        # Some ip versions omit the source in their printed reply. The caller
        # explicitly supplied it to the kernel; reject any contradictory reply.
        if field(path, "dev") != "wlan0" or ipaddress.IPv6Address(field(path, "from", source)) != address:
            return False
        gateway = field(path, "via")
        if gateway is None:
            return False
        selected = []
        for line in defaults:
            words = line.split()
            if not words or words[0] != "default" or field(words, "dev") != "wlan0":
                continue
            if "linkdown" in words or field(words, "via") != gateway:
                continue
            prefix = ipaddress.IPv6Network(field(words, "from", "::/0"), strict=False)
            if address not in prefix:
                continue
            lifetime = field(words, "expires")
            healthy = lifetime is None or int(lifetime[:-3] if lifetime.endswith("sec") else lifetime) > 120
            selected.append((prefix.prefixlen, -int(field(words, "metric", "0")), healthy))
        if not selected:
            return False
        # Equal-ranked defaults cannot be disambiguated by the next hop. Require
        # all of these candidates to be healthy instead of trusting any long lease.
        best = max(entry[:2] for entry in selected)
        return all(healthy for length, metric, healthy in selected if (length, metric) == best)
    except (ValueError, IndexError, TypeError):
        return False


def solicit(source, mac):
    if not ipaddress.IPv6Address(source).is_link_local or not re.fullmatch(r"(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", mac):
        raise ValueError("Expected Wi-Fi link-local and hardware addresses")
    index = socket.if_nametoindex("wlan0")
    # ICMPv6 type 133 and Source Link-Layer Address option, checksum filled by Linux.
    packet = struct.pack("!BBHI", 133, 0, 0, 0) + bytes([1, 1]) + bytes.fromhex(mac.replace(":", ""))
    with socket.socket(socket.AF_INET6, socket.SOCK_RAW, socket.IPPROTO_ICMPV6) as sock:
        sock.settimeout(3)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, b"wlan0\0")
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_IF, index)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, 255)
        sock.bind((source, 0, 0, index))
        sock.sendto(packet, ("ff02::2", 0, 0, index))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "route-check":
        sys.exit(0 if route_ready(sys.argv[2], sys.stdin.readline(), sys.stdin) else 1)
    solicit(*sys.argv[1:])
