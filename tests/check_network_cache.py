"""Exercise the production network-cache shell with temporary files; no device access."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


def native(name):
    if os.name == "nt" and re.match(r"^/[a-zA-Z]/", name):
        return Path(name[1] + ":" + name[2:])
    return Path(name)


if len(sys.argv) > 1 and sys.argv[1] == "--sha":
    try:
        if len(sys.argv) == 2:
            print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest() + "  -")
        for name in sys.argv[2:]:
            print(hashlib.sha256(native(name).read_bytes()).hexdigest() + "  " + name)
    except OSError:
        sys.exit(1)
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--shell", required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
output = repo / "out"
output.mkdir(exist_ok=True)
shell_dir = Path(args.shell).resolve().parent


def posix(path):
    value = Path(path).as_posix()
    return "/" + value[0].lower() + value[2:] if re.match(r"^[A-Za-z]:/", value) else value


with tempfile.TemporaryDirectory(prefix="network-cache-", dir=output) as temporary:
    base = Path(temporary).resolve()
    assert base.parent == output.resolve()
    rootfs = base / "rootfs"
    for relative in ("etc/asterisk", "etc/asterisk-app", "opt/asterisk-app"):
        (rootfs / relative).mkdir(parents=True)
    paths = {
        "pjsip": rootfs / "etc/asterisk/pjsip.conf",
        "ipv4": rootfs / "etc/asterisk-app/lan-ip",
        "ipv6": rootfs / "etc/asterisk-app/lan-ipv6",
        "public": rootfs / "etc/asterisk-app/public-ipv6.json",
        "api": rootfs / "opt/asterisk-app/api.py",
        "script": base / "network-cache.sh",
    }
    for key in ("pjsip", "ipv4", "ipv6", "api"):
        paths[key].write_text("fixture-" + key + "\n", encoding="utf-8")
    paths["script"].write_bytes((repo / "assets/runtime/network-cache.sh").read_bytes())
    python = shlex.quote(Path(sys.executable).as_posix())
    helper = shlex.quote(Path(__file__).resolve().as_posix())
    bb = base / "bb"
    bb.write_text("#!" + Path(args.shell).as_posix() + "\ncase \"$1\" in\n"
                  + "sha256sum) shift; exec " + python + " " + helper + " --sha \"$@\";;\n"
                  + "awk) shift; exec " + shlex.quote(posix(shell_dir / "awk.exe") if os.name == "nt" else "awk") + " \"$@\";;\nesac\nexit 20\n", encoding="utf-8", newline="\n")
    bb.chmod(0o700)
    enter = base / "enter.sh"
    enter.write_text("#!" + Path(args.shell).as_posix() + "\nprintf 'prepared\\n' >> \"$BASE/calls\"\n"
                     + "[ \"${FAIL_NETWORK:-0}\" != 1 ] || exit 1\n"
                     + "if [ \"${CHANGE_NETWORK:-0}\" = 1 ]; then printf 'changed\\n' >> \"$R/etc/asterisk/pjsip.conf\"; fi\n", encoding="utf-8", newline="\n")
    enter.chmod(0o700)
    wrapper = base / "check.sh"
    wrapper.write_text("set -eu\nBASE=" + shlex.quote(posix(base)) + "\nR=" + shlex.quote(posix(rootfs))
                       + "\nBB=" + shlex.quote(posix(bb)) + "\nexport BASE R\n. \"$BASE/network-cache.sh\"\nprepare_network\n", encoding="utf-8", newline="\n")
    env = os.environ.copy()
    env["PATH"] = str(shell_dir) + os.pathsep + env.get("PATH", "")
    total = 0

    def calls():
        return len((base / "calls").read_text().splitlines()) if (base / "calls").exists() else 0

    def check(label, expected_delta, success=True, extra=None):
        global total
        before = calls()
        result = subprocess.run([args.shell, str(wrapper)], capture_output=True, text=True, env={**env, **(extra or {})})
        assert (result.returncode == 0) == success, (label, result.returncode, result.stderr)
        assert calls() - before == expected_delta, label
        print("PASS:", label)
        total += 1

    check("first successful unchanged preparation records a cache", 1)
    check("unchanged configuration skips only network preparation", 0)
    for key in ("ipv4", "ipv6", "pjsip", "api"):
        paths[key].write_text("new-" + key + "\n", encoding="utf-8")
        check(key + " change reruns preparation", 1)
    paths["public"].write_text('{"enabled":true}\n', encoding="utf-8")
    check("new public IPv6 settings invalidate cache", 1)
    paths["public"].write_text('{"enabled":false}\n', encoding="utf-8")
    check("changed public IPv6 settings invalidate cache", 1)
    paths["public"].unlink()
    check("removed public settings invalidate cache", 1)
    paths["script"].write_text(paths["script"].read_text() + "\n# new cache logic\n", encoding="utf-8", newline="\n")
    check("cache implementation change reruns preparation", 1)
    marker = base / "network-prepared.sha256"
    marker.write_text("corrupt\n", encoding="utf-8")
    check("malformed cache cannot skip preparation", 1)
    paths["ipv4"].write_text("failed-update\n", encoding="utf-8")
    check("failed network preparation is not cached", 1, False, {"FAIL_NETWORK": "1"})
    assert not marker.exists()
    check("changed preparation output is left uncached", 1, extra={"CHANGE_NETWORK": "1"})
    assert not marker.exists()
    check("later unchanged successful preparation can cache", 1)
    paths["pjsip"].unlink()
    check("missing required configuration fails closed", 0, False)
    print(f"PASS: {total} isolated network preparation checks")
