"""Production network transformation with synthetic files; no device or native service."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
repo = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("network_api", repo / "assets/runtime/api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
passed = 0


def require(condition, label):
    global passed
    assert condition, label
    print("PASS:", label)
    passed += 1


with tempfile.TemporaryDirectory(prefix="api-network-", dir=repo / "out") as directory:
    fixture = Path(directory).resolve()
    assert fixture.parent == (repo / "out").resolve()
    api.C, api.S = fixture / "asterisk", fixture / "state"
    api.C.mkdir(); api.S.mkdir()
    (api.S / "lan-ip").write_text("192.0.2.1")
    (api.S / "lan-ipv6").write_text("2001:db8::1")
    public = api.S / "public-ipv6.json"
    public.write_text(json.dumps({"enabled": True, "domain": "example.invalid"}))
    (api.C / "rtp.conf").write_text("rtpstart=22000\nrtpend=22019\n")
    config = api.C / "pjsip.conf"
    config.write_text("; fixture header\n[transport-lan]\ntype=transport\nprotocol=udp\nbind=192.0.2.1:16060\n\n"
                      "[client]\ntype=endpoint\ntransport=transport-lan\nmedia_address=192.0.2.1\n"
                      "; preserve this comment\n\n[custom]\ntype=aor\ncontact=sip:fixture@example.invalid\n")
    writes = []
    # Only OS ownership publication is mocked; network() and its parser are production code.
    def write(path, value):
        writes.append(path.name)
        path.write_text(value)
    api.write = write

    api.network(); first = config.read_text(); count = len(writes)
    api.network(); second = config.read_text()
    api.network(); third = config.read_text()
    require(first == second == third and len(writes) == count, "unchanged IPv6 preparation does not rewrite configuration")
    require(third.count("[transport-public-ipv6]") == 1, "generated IPv6 transport remains unique")
    require("bind=[2001:db8::1]:16060" in third and "rtp_ipv6=yes" in third, "IPv6 signaling and media settings are retained")
    require("; preserve this comment" in third and "contact=sip:fixture@example.invalid" in third, "comments and unrelated endpoint content survive")
    (api.S / "lan-ipv6").write_text("2001:db8::2")
    api.network(); updated = config.read_text(); api.network()
    require(updated == config.read_text() and "bind=[2001:db8::2]:16060" in updated, "IPv6 changes apply once then stabilize")
    public.write_text(json.dumps({"enabled": False, "domain": "example.invalid"}))
    api.network(); disabled = config.read_text(); api.network()
    require(disabled == config.read_text() and "[transport-public-ipv6]" not in disabled and "rtp_ipv6=no" in disabled, "disabling public IPv6 applies once and removes generated transport")
    (api.S / "lan-ip").write_text("192.0.2.2")
    api.network(); changed4 = config.read_text(); api.network()
    require(changed4 == config.read_text() and "bind=192.0.2.2:16060" in changed4 and "media_address=192.0.2.2" in changed4, "IPv4 changes apply once then stabilize")
    require(api.ports()["lanPort"] == 16060 and api.ports()["rtpStart"] == 22000, "network normalization does not alter ports")
    print(f"PASS: {passed} production network transformation checks")
