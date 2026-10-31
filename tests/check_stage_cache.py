"""Run the production cache-validation shell against isolated, disposable files.

Usage: python tests/check_stage_cache.py --java D:/Java/jdk-21/bin --shell path/to/sh.exe
On Windows, only stat ownership and the unavailable sha256sum utility are provided
by this fixture; SHA-256 still reads the real fixture bytes. No device is touched.
"""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


def native(path):
    if os.name == "nt" and re.match(r"^/[a-zA-Z]/", path):
        return Path(path[1] + ":" + path[2:])
    return Path(path)


if len(sys.argv) > 1 and sys.argv[1] == "--stat":
    for name in sys.argv[4:]:
        native(name).stat()
        sys.stdout.buffer.write(b"1000\n" if os.environ.get("TEST_FOREIGN_OWNER") else b"0\n")
    sys.exit(0)
if len(sys.argv) > 1 and sys.argv[1] == "--sha":
    for line in sys.stdin:
        expected, name = line.rstrip("\n").split("  ", 1)
        try:
            actual = hashlib.sha256(native(name).read_bytes()).hexdigest()
        except OSError:
            sys.exit(1)
        if actual != expected:
            sys.exit(1)
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--java", required=True)
parser.add_argument("--shell", required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
out = repo / "out"
out.mkdir(exist_ok=True)
names = ["control.sh", "run.sh", "enter.sh", "api.py", "health.sh", "network-cache.sh", "97-asterisk-app.sh", "health-helper.sha256", "phonenumberslite-9.0.42-py2.py3-none-any.whl"]


def posix(path):
    text = path.as_posix()
    return "/" + text[0].lower() + text[2:] if re.match(r"^[A-Za-z]:/", text) else text


with tempfile.TemporaryDirectory(prefix="stage-cache-", dir=out) as temporary:
    fixture = Path(temporary)
    base, hook = fixture / "runtime", fixture / "service.d" / "97-asterisk-app.sh"
    base.mkdir()
    hook.parent.mkdir()
    (base / ".asterisk-app-owned").touch()
    for name in names:
        (base / name).write_bytes(("#!/bin/sh\n# fixture:" + name + "\n").encode())
        (base / name).chmod(0o700)
    hook.write_bytes((base / hook.name).read_bytes())
    hook.chmod(0o700)
    classes = fixture / "classes"
    classes.mkdir()
    subprocess.run([str(Path(args.java) / "javac"), "--release", "8", "-d", str(classes), str(repo / "src/com/fann/asterisk/RuntimeStageCache.java"), str(repo / "tests/RuntimeStageCacheChecks.java")], check=True)
    subprocess.run([str(Path(args.java) / "java"), "-cp", str(classes), "com.fann.asterisk.RuntimeStageCacheChecks", posix(base), posix(hook), str(fixture)], check=True)
    wrapper = fixture / "check.sh"
    if os.name == "nt":
        python = shlex.quote(Path(sys.executable).as_posix())
        helper = shlex.quote(Path(__file__).resolve().as_posix())
        prefix = f'stat() {{ {python} {helper} --stat "$@"; }}\nsha256sum() {{ {python} {helper} --sha "$@"; }}\n'
    else:
        prefix = ""
    wrapper.write_text(prefix + '. "$1"\n', encoding="utf-8", newline="\n")
    count = 0

    def check(label, expect=True, rootfs=False, foreign=False):
        global count
        env = os.environ.copy()
        if foreign:
            env["TEST_FOREIGN_OWNER"] = "1"
        result = subprocess.run([args.shell, str(wrapper), posix(fixture / ("rootfs.sh" if rootfs else "host.sh"))], capture_output=True, text=True, env=env)
        valid = result.returncode == 0 and result.stdout.strip() == "valid"
        if valid != expect:
            subprocess.run([args.shell, "-x", str(wrapper), posix(fixture / ("rootfs.sh" if rootfs else "host.sh"))], env=env)
        assert valid == expect, (label, result.returncode, result.stdout, result.stderr)
        print("PASS:", label)
        count += 1

    check("unchanged files hit cache")
    check("non-root ownership invalidates cache", False, foreign=True)
    owned = base / ".asterisk-app-owned"
    owned.unlink()
    check("missing ownership marker invalidates cache", False)
    owned.touch()
    target = base / "control.sh"
    original = target.read_bytes()
    target.unlink()
    check("missing runtime script invalidates cache", False)
    target.write_bytes(original + b"corrupt")
    target.chmod(0o700)
    check("corrupt runtime script invalidates cache", False)
    target.write_bytes(original)
    network_cache = base / "network-cache.sh"
    cache_bytes = network_cache.read_bytes()
    network_cache.write_bytes(cache_bytes + b"corrupt")
    check("corrupt network cache code invalidates runtime", False)
    network_cache.write_bytes(cache_bytes)
    original_hook = hook.read_bytes()
    hook.write_bytes(original_hook + b"corrupt")
    check("corrupt boot hook invalidates cache", False)
    hook.write_bytes(original_hook)
    helper_hash = base / "health-helper.sha256"
    helper_bytes = helper_hash.read_bytes()
    helper_hash.write_bytes(b"wrong apk hash\n")
    check("altered helper APK digest invalidates cache", False)
    helper_hash.write_bytes(helper_bytes)
    (base / "installed").touch()
    check("installed marker without rootfs invalidates cache", False)
    (base / "installed").unlink()
    rootfs = base / "rootfs/opt/asterisk-app"
    rootfs.mkdir(parents=True)
    for name in names:
        if name.endswith((".py", ".whl")) or name == "run.sh":
            (rootfs / name).write_bytes((base / name).read_bytes())
    check("new rootfs invalidates host-only cache", False)
    check("complete rootfs hits cache", rootfs=True)
    (rootfs / "api.py").write_bytes(b"corrupt")
    check("corrupt rootfs copy invalidates cache", False, rootfs=True)
    (rootfs / "api.py").write_bytes((base / "api.py").read_bytes())
    (rootfs / "run.sh").unlink()
    check("missing rootfs copy invalidates cache", False, rootfs=True)
    (rootfs / "run.sh").write_bytes((base / "run.sh").read_bytes())
    check("repaired rootfs hits cache again", rootfs=True)
    print(f"PASS: {count} runtime filesystem cache checks")
