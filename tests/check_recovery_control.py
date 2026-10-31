"""Run actual control.sh branches in an isolated filesystem with mock Android/native commands."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time


def native(path):
    return Path(path[1] + ":" + path[2:]) if os.name == "nt" and re.match(r"^/[a-zA-Z]/", path) else Path(path)


if len(sys.argv) > 1 and sys.argv[1] == "--sha":
    try:
        if len(sys.argv) == 2:
            print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest() + "  -")
        for name in sys.argv[2:]:
            print(hashlib.sha256(native(name).read_bytes()).hexdigest() + "  " + name)
    except OSError:
        sys.exit(1)
    sys.exit(0)
if len(sys.argv) > 1 and sys.argv[1] == "--sleep":
    time.sleep(0 if os.environ.get("FAST_LOCK_TEST") == "1" and sys.argv[2] == "1" else float(sys.argv[2]))
    sys.exit(0)

parser = argparse.ArgumentParser()
parser.add_argument("--shell", required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
output = repo / "out"
output.mkdir(exist_ok=True)
shell = Path(args.shell).resolve()


def posix(path):
    value = Path(path).as_posix()
    return "/" + value[0].lower() + value[2:] if re.match(r"^[A-Za-z]:/", value) else value


with tempfile.TemporaryDirectory(prefix="recovery-control-", dir=output) as temporary:
    base = Path(temporary).resolve()
    assert base.parent == output.resolve()
    rootfs = base / "rootfs"
    for relative in ("rootfs/run/asterisk", "rootfs/etc/asterisk-app", "rootfs/etc/asterisk", "rootfs/opt/asterisk-app", "proc/99999999", "bin"):
        (base / relative).mkdir(parents=True)
    env = os.environ.copy()
    env["PATH"] = str(base / "bin") + os.pathsep + str(shell.parent) + os.pathsep + env.get("PATH", "")
    env["TEST_BASE"] = posix(base)
    python, helper = shlex.quote(Path(sys.executable).as_posix()), shlex.quote(Path(__file__).resolve().as_posix())

    def script(path, body):
        path.write_text("#!" + shell.as_posix() + "\n" + body, encoding="utf-8", newline="\n")
        path.chmod(0o700)

    bb = base / "bb"
    script(bb, "case \"$1\" in\n"
           "timeout) shift 2; exec \"$@\";;\n"
           "flock) shift; [ \"$1\" = -n ] && [ \"$2\" = 9 ] || exit 20; printf 'lock\\n' >> \"$TEST_BASE/events\"; n=$(cat \"$TEST_BASE/lock-attempts\" 2>/dev/null || echo 0); printf '%s\\n' $((n+1)) > \"$TEST_BASE/lock-attempts\"; [ \"$n\" -ge \"${LOCK_BUSY_ATTEMPTS:-0}\" ]; exit $?;;\n"
           "ash) shift; exec " + shlex.quote(posix(shell)) + " \"$@\";;\n"
           "setsid) shift; exec \"$@\";;\n"
           "sha256sum) shift; exec " + python + " " + helper + " --sha \"$@\";;\n"
           "awk|grep) task=$1; shift; exec \"$task\" \"$@\";;\nesac\nexit 20\n")
    script(base / "bin/cmd", "printf 'package:com.fann.asterisk uid:10001\\n'\n")
    script(base / "bin/ip", "[ \"${NO_WIFI:-0}\" = 1 ] || printf '1: wlan0 inet 192.0.2.1/24 scope global wlan0\\n'\n")
    script(base / "bin/chmod", ":\n")
    script(base / "bin/chown", ":\n")
    script(base / "bin/readlink", "cat \"$1\"\n")
    script(base / "bin/sleep", "exec " + python + " " + helper + " --sleep \"$@\"\n")
    script(base / "ipv6.sh", "printf '2001:db8::1\\n'\n")
    script(base / "supervisor.sh", ":\n")
    script(base / "enter.sh", "if [ \"$1\" = /usr/bin/python3 ]; then\n"
           " printf 'network\\n' >> \"$TEST_BASE/events\"\n"
           " [ \"${STOP_DURING_NETWORK:-0}\" != 1 ] || touch \"$TEST_BASE/disabled\"\n"
           " [ \"${FAIL_NETWORK:-0}\" != 1 ] || exit 1\n"
           "else\n"
           " printf 'engine\\n' >> \"$TEST_BASE/events\"\n"
           " printf '99999999\\n' > \"$TEST_BASE/rootfs/run/asterisk/asterisk.pid\"\n"
           " printf '%s\\n' \"$TEST_BASE/rootfs\" > \"$TEST_BASE/proc/99999999/root\"\n"
           " printf '/usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf' > \"$TEST_BASE/proc/99999999/cmdline\"\nfi\n")
    source = (repo / "assets/runtime/control.sh").read_text()
    source = re.sub(r"BB=\nfor candidate.*?\[ -n \"\$BB\" \] \|\| \{ echo busybox_missing; exit 20; \}", "BB=" + shlex.quote(posix(bb)), source, count=1, flags=re.S)
    source = source.replace("BASE=/data/adb/asterisk-app", "BASE=" + shlex.quote(posix(base))).replace("/system/bin/sh", shlex.quote(posix(shell))).replace("/proc/", posix(base / "proc") + "/")
    (base / "control.sh").write_text(source, encoding="utf-8", newline="\n")
    (base / "control.sh").chmod(0o700)
    (base / "network-cache.sh").write_bytes((repo / "assets/runtime/network-cache.sh").read_bytes())
    for name, value in {"etc/asterisk-app/android-uid": "10001", "etc/asterisk/pjsip.conf": "fixture", "opt/asterisk-app/api.py": "fixture"}.items():
        (rootfs / name).write_text(value, encoding="utf-8")
    total = 0

    def reset():
        for relative in ("installed", "health-enabled", "background-authorized"):
            (base / relative).touch()
        for relative in ("disabled", "network-prepared.sha256", "events", "lock-attempts", "rootfs/run/asterisk/asterisk.pid", "proc/99999999/root", "proc/99999999/cmdline"):
            (base / relative).unlink(missing_ok=True)
        (rootfs / "etc/asterisk-app/android-uid").write_text("10001", encoding="utf-8")

    def run(label, action="recover", success=False, engine=False, extra=None):
        global total
        result = subprocess.run([str(shell), str(base / "control.sh"), action], env={**env, **(extra or {})}, capture_output=True, text=True, timeout=8)
        events = (base / "events").read_text().splitlines() if (base / "events").exists() else []
        assert (result.returncode == 0) == success, (label, result.returncode, result.stdout, result.stderr)
        assert ("engine" in events) == engine, (label, events)
        assert events and events[0] == "lock", label
        print("PASS:", label)
        total += 1

    for marker in ("installed", "health-enabled", "background-authorized"):
        reset(); (base / marker).unlink()
        run("missing " + marker + " blocks automatic launch")
    reset(); (base / "disabled").touch()
    run("manual stop blocks automatic recovery")
    assert (base / "disabled").exists()
    reset(); (rootfs / "etc/asterisk-app/android-uid").write_text("10002", encoding="utf-8")
    run("UID mismatch blocks launch")
    reset(); run("missing Wi-Fi blocks launch", extra={"NO_WIFI": "1"})
    reset(); run("network preparation failure blocks launch", extra={"FAIL_NETWORK": "1"})
    reset(); run("manual stop during preparation cancels recovery", extra={"STOP_DURING_NETWORK": "1"})
    assert (base / "disabled").exists()
    reset(); run("authorized recovery launches verified mock engine", success=True, engine=True)
    reset(); (base / "disabled").touch()
    run("explicit user start can clear manual stop", action="start", success=True, engine=True)
    assert not (base / "disabled").exists()
    reset(); run("manual stop records intent even without an engine", action="stop", success=True)
    assert (base / "disabled").exists()
    reset(); run("brief lock contention retries then launches once", success=True, engine=True, extra={"LOCK_BUSY_ATTEMPTS": "2", "FAST_LOCK_TEST": "1"})
    assert (base / "lock-attempts").read_text().strip() == "3"
    assert (base / "events").read_text().splitlines().count("engine") == 1
    reset(); run("persistent lock contention stops after twenty waits", extra={"LOCK_BUSY_ATTEMPTS": "99", "FAST_LOCK_TEST": "1"})
    assert (base / "lock-attempts").read_text().strip() == "21"
    print(f"PASS: {total} isolated control recovery cases (flock invocation is mocked, not timing-tested)")
