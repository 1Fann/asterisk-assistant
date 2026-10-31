"""Exercise the production worker loop across deterministic process/check races.

Only the engine process table, full check, Android queries and clock are fake.
No native engine, real lock, device or call is involved.
"""
import argparse
import os
from pathlib import Path
import shlex
import subprocess
import tempfile


def posix(path):
    value = Path(path).resolve().as_posix()
    return "/" + value[0].lower() + value[2:] if os.name == "nt" else value


parser = argparse.ArgumentParser()
parser.add_argument("--shell", required=True)
shell = Path(parser.parse_args().shell).resolve()
repo = Path(__file__).resolve().parents[1]
source = (repo / "assets/runtime/health.sh").read_text(encoding="utf-8")
output = repo / "out"
output.mkdir(exist_ok=True)
env = os.environ.copy()
env["PATH"] = str(shell.parent) + os.pathsep + env.get("PATH", "")
old, new = "88991", "88992"

mock = r"""
TICK=0
COUNT=0
kill() { [ "$1" = -0 ] && [ -f "$BASE/live.$2" ]; }
pidof() { :; }
sleep() {
 TICK=$((TICK + 1))
 if [ "$MODE:$TICK" = between:4 ]; then rm -f "$BASE/live.88991"; fi
 if [ "$MODE:$TICK" = rearm:20 ]; then touch "$BASE/live.88992"; printf '%s\n' 88992 > "$BASE/rootfs/run/asterisk/asterisk.pid"; fi
 if [ "$MODE:$TICK" = rearm:22 ]; then rm "$BASE/live.88992"; fi
 if [ "$MODE:$TICK" = latebusy:85 ]; then rm -f "$BASE/lock-busy"; fi
}
fixture_check() {
 COUNT=$((COUNT + 1))
 printf '%s|%s\n' "$TICK" "$1" >> "$BASE/events"
 case "$MODE:$COUNT" in
  first:1|busy:1|blocked:1|scheduled:2|reused:1|rearm:1|latebusy:1) rm -f "$BASE/live.88991";;
  stop:1) rm -f "$BASE/live.88991"; touch "$BASE/disabled";;
  off:1) rm -f "$BASE/live.88991" "$BASE/health-enabled";;
  nopermission:1) rm -f "$BASE/live.88991" "$BASE/background-authorized";;
  replaced:1) rm -f "$BASE/live.88991"; touch "$BASE/live.88992"
    printf '%s\n' 88992 > "$BASE/rootfs/run/asterisk/asterisk.pid";;
  busy:2) return 1;;
  latebusy:8) touch "$BASE/lock-busy"; return 1;;
 esac
 [ "$COUNT" -lt "$LIMIT" ] || rm -f "$BASE/health-enabled"
 return 0
}
"""

pairs = {
    "first": [(0, ""), (0, old)],  # Engine loss inside a replacement worker's first check.
    "scheduled": [(0, ""), (60, ""), (60, old)],
    "between": [(0, ""), (4, old)],
    "busy": [(0, ""), (0, old), (1, old)],
    "stale": [(0, ""), (3, ""), (6, "")],  # Never treat stale pidfile alone as evidence.
    "reused": [(0, ""), (3, "")],  # PID was live but its process did not match Asterisk.
    "blocked": [(0, ""), (0, old), (3, old), (6, old), (9, old), (12, old), (15, old), (75, old)],
    "rearm": [(0, ""), (0, old), (3, old), (6, old), (9, old), (12, old), (15, old), (22, new)],
    "latebusy": [(0, ""), (0, old), (3, old), (6, old), (9, old), (12, old), (15, old), (75, old), (85, old)],
    "stop": [(0, ""), (60, "")],
    "off": [(0, "")],
    "nopermission": [(0, ""), (60, "")],
    "replaced": [(0, ""), (60, "")],  # A currently live replacement cancels the old event.
}
for mode, expected in pairs.items():
    with tempfile.TemporaryDirectory(prefix="pbx-observation-", dir=output) as work:
        base = Path(work)
        root = posix(base)
        pidfile = base / "rootfs/run/asterisk/asterisk.pid"
        pidfile.parent.mkdir(parents=True)
        pidfile.write_text(old + "\n", encoding="ascii", newline="\n")
        for marker in (".asterisk-app-owned", "health-enabled", "installed", "background-authorized"):
            (base / marker).touch()
        if mode != "stale":
            (base / ("live." + old)).touch()
        (base / "health-minutes").write_text("1\n", encoding="ascii", newline="\n")
        bb = base / "bb"
        bb.write_text("#!" + posix(shell) + "\ncase \"$1\" in\n"
                      "timeout) echo isForeground=true;;\ngrep) shift; exec grep \"$@\";;\n"
                      'flock) [ ! -e "$TEST_LOCK" ];;\n'
                      "*) exit 20;;\nesac\n", encoding="utf-8", newline="\n")
        bb.chmod(0o700)
        transformed = source.replace("BASE=/data/adb/asterisk-app", "BASE=" + shlex.quote(root))
        transformed = transformed.replace(
            "/data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox",
            shlex.quote(posix(bb))).replace("/sys/power/wake_", root + "/wake_")
        original = '/system/bin/sh "$BASE/health.sh" once "$RECOVERY_PID"'
        assert transformed.count(original) == 1 and transformed.count("live_engine_pid() {") == 1
        transformed = transformed.replace(original, 'fixture_check "$RECOVERY_PID"')
        transformed = transformed.replace("live_engine_pid() {", mock + "\nlive_engine_pid() {")
        assert transformed.count("engine_identity() {") == 1
        transformed = transformed.replace("engine_identity() {", 'engine_identity() { [ "$MODE" != reused ]; return $?;')
        script = base / "health.sh"
        script.write_text(transformed, encoding="utf-8", newline="\n")
        case_env = dict(env, MODE=mode, LIMIT=str(len(expected)), TEST_LOCK=posix(base / "lock-busy"))
        subprocess.run([str(shell), posix(script), "--loop"], env=case_env, check=True, timeout=30)
        got = [(int(t), pid) for t, pid in (line.split("|") for line in (base / "events").read_text().splitlines())]
        assert got == expected, (mode, expected, got)
        print("PASS:", mode)
print("PASS:", len(pairs), "production-loop process-observation cases")
