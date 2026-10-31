#!/system/bin/sh
# Isolated regression for Magisk BusyBox timeout children retaining flock files.
# SOURCE is transformed into a private temp directory; no real APK/service is used.
set -eu
SOURCE=$1
BB=/data/adb/magisk/busybox
[ -x "$BB" ] || exit 2
TEST_ROOT=/data/local/tmp/pbx-check-lock-test-20261031
mkdir -p "$TEST_ROOT"
CASE=$("$BB" mktemp -d "$TEST_ROOT/case.XXXXXX")
case "$CASE" in /data/local/tmp/pbx-check-lock-test-20261031/case.*) ;; *) exit 2;; esac
export TEST_CASE="$CASE"
cleanup() {
 rm -f "$CASE/health-enabled"
 touch "$CASE/release" "$CASE/release-owners"
 # Only our mock worker, with its exact private path, may be terminated.
 pid=$(cat "$CASE/mock.pid" 2>/dev/null || :)
 case "$pid" in ''|*[!0-9]*) ;; *)
  if [ -r "/proc/$pid/cmdline" ] && tr '\000' ' ' < "/proc/$pid/cmdline" | "$BB" grep -qF "$CASE/bin/app_process"; then kill -TERM "$pid" 2>/dev/null || :; fi;;
 esac
 rm -rf "$CASE"
}
trap cleanup EXIT
trap 'exit 1' TERM INT
mkdir "$CASE/bin"
printf '#!/system/bin/sh\necho 1\n' > "$CASE/bin/getprop"
printf '#!/system/bin/sh\necho RUNNING_UNLOCKED\n' > "$CASE/bin/cmd"
printf '#!/system/bin/sh\necho "package:$TEST_CASE/mock.apk"\n' > "$CASE/bin/pm"
cat > "$CASE/bin/app_process" <<'EOF'
#!/system/bin/sh
echo $$ > "$TEST_CASE/mock.pid"
touch "$TEST_CASE/entered"
while [ -f "$TEST_CASE/block" ] && [ ! -f "$TEST_CASE/release" ]; do
 sleep 0.1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
done
EOF
chmod 700 "$CASE/bin/"*
PATH="$CASE/bin:$PATH"; export PATH
printf mock > "$CASE/mock.apk"
"$BB" sha256sum "$CASE/mock.apk" | "$BB" awk '{print $1}' > "$CASE/health-helper.sha256"
cp "$CASE/health-helper.sha256" "$CASE/mock-valid.sha256"
"$BB" sed -e "s|^BASE=.*|BASE=$CASE|" \
 -e "s|/data/adb/call-service-health.lock|$CASE/shared.lock|g" \
 -e "s|/sys/power/wake_|$CASE/wake_|g" \
 -e '/^ OLD_LOOP=\$(recorded_owner health-loop --loop)$/a\ touch "$TEST_CASE/snapshotted"' "$SOURCE" > "$CASE/body.sh"
cat > "$CASE/health.sh" <<'EOF'
#!/system/bin/sh
# Isolated shell-owner stand-ins with production argv, PID files and singleton locks.
if [ "${TEST_STUB_OWNER:-0}" = 1 ]; then
 case "$1" in --supervise) name=health-supervisor;; --loop) name=health-loop;; *) exit 2;; esac
 echo $$ > "$TEST_CASE/$name.pid"
 trap 'touch "$TEST_CASE/term.$$"' TERM
 while [ ! -f "$TEST_CASE/release.$$" ] && [ ! -f "$TEST_CASE/release-owners" ]; do
  sleep 0.05 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
 done
 exit 0
fi
EOF
cat "$CASE/body.sh" >> "$CASE/health.sh"
touch "$CASE/.asterisk-app-owned" "$CASE/health-enabled"
free_lock() { "$BB" flock -n "$CASE/$1" true || { echo "FAIL: $1 remains held after completion"; exit 1; }; }
busy_lock() {
 if "$BB" flock -n "$CASE/$1" true; then echo "FAIL: $1 released during active check"; exit 1; fi
}
# Successful app_process exit must not wait for 10/180-second timer children.
/system/bin/sh "$CASE/health.sh" once
[ -f "$CASE/entered" ]
free_lock health-check.lock; free_lock shared.lock
echo 'PASS: complete check releases both locks immediately'
# An early APK-validation return exercises both nested query deadlines too.
printf invalid > "$CASE/health-helper.sha256"
rm "$CASE/entered"
/system/bin/sh "$CASE/health.sh" once
[ ! -f "$CASE/entered" ]
free_lock health-check.lock; free_lock shared.lock
cp "$CASE/mock-valid.sha256" "$CASE/health-helper.sha256"
echo 'PASS: early validation failure releases query and check locks immediately'
# The actual check must continue holding both locks; upgrade waits behind it.
touch "$CASE/block"
/system/bin/sh "$CASE/health.sh" once & check=$!
n=0
while [ ! -f "$CASE/entered" ] && [ "$n" -lt 50 ]; do sleep 0.1; n=$((n+1)); done
[ -f "$CASE/entered" ]
busy_lock health-check.lock; busy_lock shared.lock
if /system/bin/sh "$CASE/health.sh" once; then echo 'FAIL: overlapping check accepted'; exit 1; fi
/system/bin/sh "$CASE/health.sh" upgrade & upgrade=$!
sleep 0.2
busy_lock health-upgrade.lock
busy_lock health-check.lock; busy_lock shared.lock
rm "$CASE/health-enabled"
touch "$CASE/release"
wait "$check"; wait "$upgrade"
free_lock health-check.lock; free_lock shared.lock; free_lock health-upgrade.lock
echo 'PASS: live check holds locks, upgrade waits, all release without timer delay'
/system/bin/sh "$CASE/health.sh" upgrade
free_lock health-upgrade.lock; free_lock health-check.lock
echo 'PASS: disabled upgrade releases its locks immediately'
# A boot/owner restart can win the worker lock while upgrade waits for a real
# check. Keep the original supervisor retiring to prove business checks remain
# admitted during handoff, then accept the independently replaced worker.
wait_file() { n=0; while [ ! -e "$1" ] && [ "$n" -lt 100 ]; do sleep 0.05; n=$((n+1)); done; [ -e "$1" ]; }
touch "$CASE/health-enabled" "$CASE/block"
rm -f "$CASE/release" "$CASE/entered" "$CASE/snapshotted"
TEST_STUB_OWNER=1 "$BB" flock -n "$CASE/health-supervisor.lock" /system/bin/sh "$CASE/health.sh" --supervise & old_sup_job=$!
TEST_STUB_OWNER=1 "$BB" flock -n "$CASE/health-loop.lock" /system/bin/sh "$CASE/health.sh" --loop & old_loop_job=$!
wait_file "$CASE/health-supervisor.pid"; wait_file "$CASE/health-loop.pid"
old_sup=$(cat "$CASE/health-supervisor.pid"); old_loop=$(cat "$CASE/health-loop.pid")
/system/bin/sh "$CASE/health.sh" once & active=$!
wait_file "$CASE/entered"
/system/bin/sh "$CASE/health.sh" upgrade & handoff=$!
wait_file "$CASE/snapshotted"
touch "$CASE/release.$old_loop"; wait "$old_loop_job"
rm "$CASE/health-loop.pid"
TEST_STUB_OWNER=1 "$BB" flock -n "$CASE/health-loop.lock" /system/bin/sh "$CASE/health.sh" --loop & new_loop_job=$!
wait_file "$CASE/health-loop.pid"; new_loop=$(cat "$CASE/health-loop.pid")
[ "$new_loop" != "$old_loop" ]
touch "$CASE/release"; wait "$active"
wait_file "$CASE/term.$old_sup"
free_lock health-check.lock; free_lock shared.lock
/system/bin/sh "$CASE/health.sh" once
[ ! -e "$CASE/term.$new_loop" ]
echo 'PASS: upgrade does not hold the check lock while a supervised owner retires'
touch "$CASE/release.$old_sup"; wait "$old_sup_job"
wait "$handoff"
kill -0 "$new_loop" && [ ! -e "$CASE/term.$new_loop" ]
new_sup=$(cat "$CASE/health-supervisor.pid")
[ "$old_sup" != "$new_sup" ] && kill -0 "$new_sup"
free_lock health-upgrade.lock
echo 'PASS: concurrent replacement is preserved, missing supervisor starts, handoff finishes'
rm -f "$CASE/health-enabled"; touch "$CASE/release-owners"; wait "$new_loop_job"
# Let our real supervisor finish its short worker contention backoff before cleanup.
n=0; while kill -0 "$new_sup" 2>/dev/null && [ "$n" -lt 60 ]; do sleep 0.05; n=$((n+1)); done
! kill -0 "$new_sup" 2>/dev/null
