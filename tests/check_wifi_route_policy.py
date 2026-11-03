"""Check kernel source lookup and default lease matching with documented addresses only."""
import importlib.util
from pathlib import Path

module = Path(__file__).resolve().parents[1] / "assets/runtime/wifi-rs.py"
spec = importlib.util.spec_from_file_location("wifi_rs", module)
wifi_rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wifi_rs)

source = "2001:db8:1::8"
lookup = f"2606:4700:4700::1111 from {source} via fe80::1 dev wlan0 table wlan0"
default = "default via fe80::1 dev wlan0 metric 1024"
def healthy(*routes, via=lookup):
    return wifi_rs.route_ready(source, via, routes)

assert healthy(default, via=lookup.replace(" from " + source, ""))
assert healthy(default + " expires 121sec")
assert not healthy(default + " expires 120sec")
assert not healthy(default, via=lookup.replace("dev wlan0", "dev rmnet0"))
assert not healthy(default, via=lookup.replace(source, "2001:db8:2::1"))
assert not healthy(default, via="")
assert not healthy(default.replace("fe80::1", "fe80::2"))
assert not healthy(default + " linkdown")
assert not healthy(default.replace("default", "default from 2001:db8:2::/64"))
assert healthy(default.replace("default", "default from 2001:db8:1::/64"))
assert not healthy(default, default.replace("default", "default from 2001:db8:1::/64") + " expires 60sec")
assert not healthy(default, default.replace("1024", "128") + " expires 60sec")
assert not healthy(default, default + " expires 5sec")
assert healthy(default, default.replace("fe80::1", "fe80::2") + " expires 5sec")
assert not healthy(default + " expires unknown")
print("PASS: 15 source, interface, next-hop, prefix, metric and lease checks")
