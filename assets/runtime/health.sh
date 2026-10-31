#!/system/bin/sh
# asterisk-app-owned: independent root monitor; no credentials or call audio logged.
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
umask 077
[ -f "$BASE/.asterisk-app-owned" ] && [ -x "$BB" ] || exit 1
# Android mksh marks numbered descriptors close-on-exec. Use flock's command form.
case "${1:-loop}" in
 loop) exec "$BB" flock -n "$BASE/health-supervisor.lock" /system/bin/sh "$BASE/health.sh" --supervise;;
 # A timeout timer must be created before any repair lock is acquired.
 once) exec "$BB" timeout 180 "$BB" flock -n "$BASE/health-check.lock" "$BB" flock -n /data/adb/call-service-health.lock /system/bin/sh "$BASE/health.sh" --check "${2:-}";;
 upgrade) exec "$BB" timeout 200 "$BB" flock -n "$BASE/health-upgrade.lock" /system/bin/sh "$BASE/health.sh" --handoff;;
 --supervise|--loop|--check|--handoff|--retire) ;;
 *) exit 2;;
esac
owner_key() {
 # Match the exact three shell arguments and the kernel start tick, not just a
 # numeric pidfile. Never signal a flock wrapper, checker, engine or PID reuse.
 local pid mode cmd stat rest
 pid=$1; mode=$2
 case "$pid" in ''|0|1|*[!0-9]*) return 1;; esac
 [ -r "/proc/$pid/stat" ] && IFS= read -r stat < "/proc/$pid/stat" || return 1
 rest=${stat##*) }; set -- $rest
 [ "$#" -ge 20 ] || return 1
 cmd=$(tr '\000' '\n' < "/proc/$pid/cmdline" 2>/dev/null) || return 1
 [ "$cmd" = "/system/bin/sh
$BASE/health.sh
$mode" ] || return 1
 printf '%s:%s\n' "$pid" "${20}"
}
recorded_owner() {
 local pid
 [ -r "$BASE/$1.pid" ] && IFS= read -r pid < "$BASE/$1.pid" && owner_key "$pid" "$2"
}
signal_owner() {
 local key mode sig pid
 key=$1; mode=$2; sig=$3
 [ -n "$key" ] || return 0
 pid=${key%%:*}
 if [ "$(owner_key "$pid" "$mode")" = "$key" ]; then kill "-$sig" "$pid" 2>/dev/null || :; fi
}
if [ "$1" = --retire ]; then
 [ -f "$BASE/health-enabled" ] || exit 0
 # The only handoff section under the check lock: signal the original two
 # shell owners individually and return. No waiting, restarting or sleeping.
 signal_owner "${2:-}" --supervise TERM
 signal_owner "${3:-}" --loop TERM
 exit 0
fi
if [ "$1" = --handoff ]; then
 [ -f "$BASE/health-enabled" ] || exit 0
 OLD_SUP=$(recorded_owner health-supervisor --supervise)
 OLD_LOOP=$(recorded_owner health-loop --loop)
 # Preserve a live check; release its lock before waiting on any other owner.
 "$BB" flock "$BASE/health-check.lock" /system/bin/sh "$BASE/health.sh" --retire "$OLD_SUP" "$OLD_LOOP" || exit 1
 ATTEMPT=0
 while [ -f "$BASE/health-enabled" ] && [ "$ATTEMPT" -lt 20 ]; do
  SUP=$(recorded_owner health-supervisor --supervise)
  WORKER=$(recorded_owner health-loop --loop)
  if [ -n "$SUP" ] && [ "$SUP" != "$OLD_SUP" ] && [ -n "$WORKER" ] && [ "$WORKER" != "$OLD_LOOP" ]; then exit 0; fi
  if [ "$ATTEMPT" -eq 8 ]; then
   # A shell can defer TERM while waiting on a child. Only its snapshotted
   # process identity may be retired; an independent check remains protected.
   signal_owner "$OLD_SUP" --supervise KILL
   signal_owner "$OLD_LOOP" --loop KILL
  fi
  if [ -z "$SUP" ] || [ "$SUP" = "$OLD_SUP" ]; then
   "$BB" setsid /system/bin/sh "$BASE/health.sh" loop </dev/null >/dev/null 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
  fi
  ATTEMPT=$((ATTEMPT + 1))
  sleep 0.25 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
 done
 if [ -f "$BASE/health-enabled" ]; then
  # Final idempotent launch in case ownership changed at the deadline; do not
  # report a completed handoff without observing the replacement owners.
  "$BB" setsid /system/bin/sh "$BASE/health.sh" loop </dev/null >/dev/null 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
  exit 75
 fi
 exit 0
fi
if [ "$1" = --supervise ]; then
 printf '%s\n' "$$" > "$BASE/health-supervisor.pid"
 trap 'rm -f "$BASE/health-supervisor.pid"' EXIT
 trap 'exit 0' TERM INT
 # Restart the first failed worker immediately; back off only repeated short failures.
 FAILURES=0
 while [ -f "$BASE/health-enabled" ]; do
  read STARTED _ < /proc/uptime; STARTED=${STARTED%%.*}
  # Do not let a child keep the supervisor's singleton lock after its owner dies.
  "$BB" flock -n "$BASE/health-loop.lock" /system/bin/sh "$BASE/health.sh" --loop 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
  [ -f "$BASE/health-enabled" ] || break
  read ENDED _ < /proc/uptime; ENDED=${ENDED%%.*}
  [ $((ENDED - STARTED)) -lt 30 ] || FAILURES=0
  case "$FAILURES" in 0) DELAY=0;; 1) DELAY=1;; 2) DELAY=2;; 3) DELAY=5;; *) DELAY=10;; esac
  [ "$FAILURES" -ge 4 ] || FAILURES=$((FAILURES + 1))
  while [ "$DELAY" -gt 0 ] && [ -f "$BASE/health-enabled" ]; do
   sleep 1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-; DELAY=$((DELAY - 1))
  done
 done
 exit 0
fi
if [ "$1" = --check ]; then
 [ -f "$BASE/health-enabled" ] || exit 0
 [ "$(getprop sys.boot_completed)" = 1 ] || exit 0
 [ "$("$BB" timeout 10 cmd activity get-started-user-state 0 2>/dev/null 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- | tr -d '\r')" = RUNNING_UNLOCKED ] || exit 0
 HELPER=$("$BB" timeout 10 pm path com.fann.asterisk 2>/dev/null 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- | sed -n 's/^package://p' | head -n 1)
 [ -n "$HELPER" ] && [ -f "$HELPER" ] || exit 0
 # Validate protected hashes BEFORE loading APK code as root, including after reinstall/update.
 EXPECTED=$(cat "$BASE/health-helper.sha256" 2>/dev/null)
 [ -n "$EXPECTED" ] && [ "$("$BB" sha256sum "$HELPER" | "$BB" awk '{print $1}')" = "$EXPECTED" ] || exit 0
 # Keep both locks across the Java body and reserve exit 1 for a rejected
 # nonblocking flock. An actual process failure must use ordinary backoff.
 env CLASSPATH="$HELPER" app_process /system/bin --nice-name=asterisk_health_check com.fann.asterisk.HealthMain "${2:-}" </dev/null >/dev/null 2>&1
 BODY_RESULT=$?; [ "$BODY_RESULT" -ne 1 ] || exit 70; exit "$BODY_RESULT"
fi
live_engine_pid() {
 local p
 [ -r "$BASE/rootfs/run/asterisk/asterisk.pid" ] || return 1
 IFS= read -r p < "$BASE/rootfs/run/asterisk/asterisk.pid" || [ -n "$p" ] || return 1
 case "$p" in ''|0|1|*[!0-9]*) return 1;; esac
 kill -0 "$p" 2>/dev/null && printf '%s\n' "$p"
}
engine_identity() {
 # A stale pidfile can name a reused PID. Verify the same native identity as
 # control.sh before caching death evidence, outside the one-second tick.
 [ "$(readlink "/proc/$1/root" 2>/dev/null)" = "$BASE/rootfs" ] &&
 tr '\000' ' ' < "/proc/$1/cmdline" 2>/dev/null | "$BB" grep -q '/usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf'
}
confirmed_engine_pid() {
 local p
 p=$(live_engine_pid) && engine_identity "$p" && printf '%s\n' "$p"
}
expects_engine() {
 [ -f "$BASE/health-enabled" ] && [ -f "$BASE/installed" ] &&
 [ -f "$BASE/background-authorized" ] && [ ! -f "$BASE/disabled" ]
}
# Arm the observation before publishing a replacement worker as live.
LAST_LIVE=$(confirmed_engine_pid)
printf '%s\n' "$$" > "$BASE/health-loop.pid"
release_monitor_wake() { printf '%s\n' asterisk_monitor > /sys/power/wake_unlock 2>/dev/null || :; }
renew_monitor_wake() {
 if [ -f "$BASE/health-awake" ] && [ ! -f "$BASE/disabled" ]; then
  # Bounded lease survives an app task cleanup, but expires if this monitor dies.
  printf '%s\n' 'asterisk_monitor 240000000000' > /sys/power/wake_lock 2>/dev/null || :
 else
  release_monitor_wake
 fi
}
trap 'release_monitor_wake; rm -f "$BASE/health-loop.pid"' EXIT
trap 'exit 0' TERM INT
TRANSIENT_RETRIES=0
MISSING_RETRIES=0
RECOVERY_PID=
while [ -f "$BASE/health-enabled" ]; do
 renew_monitor_wake
 # A full check can overlap native death. Refresh the live observation before
 # entering it, retaining the last confirmed observation across lock contention.
 BEFORE=$(confirmed_engine_pid)
 if [ -n "$BEFORE" ]; then LAST_LIVE=$BEFORE; RECOVERY_PID=
 elif ! expects_engine; then LAST_LIVE=; RECOVERY_PID=
 elif [ -n "$LAST_LIVE" ] && ! kill -0 "$LAST_LIVE" 2>/dev/null; then RECOVERY_PID=$LAST_LIVE
 else RECOVERY_PID=; fi
 REQUESTED_PID=$RECOVERY_PID
 /system/bin/sh "$BASE/health.sh" once "$RECOVERY_PID" 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
 CHECK_RESULT=$?
 RECOVERY_PID=
 WAITING_LOCK=0
 REJECTED_PID=
 MINUTES=$(cat "$BASE/health-minutes" 2>/dev/null)
 case "$MINUTES" in ''|*[!0-9]*) MINUTES=5;; esac
 [ "$MINUTES" -ge 1 ] && [ "$MINUTES" -le 1440 ] || MINUTES=5
 LEFT=$((MINUTES * 60))
 # The shared repair lock is nonblocking; retry contention without waiting for
 # the full user-selected interval. Active-call decisions remain in HealthMain.
 if [ "$CHECK_RESULT" -eq 75 ]; then
  TRANSIENT_RETRIES=$((TRANSIENT_RETRIES + 1))
  if [ "$TRANSIENT_RETRIES" -le 6 ]; then LEFT=3; elif [ "$LEFT" -gt 60 ]; then LEFT=60; fi
 else
  TRANSIENT_RETRIES=0
  [ "$CHECK_RESULT" -eq 0 ] || LEFT=3
 fi
 OWNER_PID=$(pidof com.fann.asterisk 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-)
 OWNER_PID=${OWNER_PID%% *}
 ENGINE_PID=$(live_engine_pid)
 if [ -n "$ENGINE_PID" ] && engine_identity "$ENGINE_PID"; then LAST_LIVE=$ENGINE_PID; MISSING_RETRIES=0
 elif ! expects_engine; then LAST_LIVE=; MISSING_RETRIES=0
 else
  # The authorized engine is missing. With no live observation, retry only the
  # ordinary check. A new, proven death during this check gets one immediate handoff;
  # a still-missing engine backs off even if the call guard paused recovery.
  if [ "$CHECK_RESULT" -eq 1 ] && [ -n "$REQUESTED_PID" ]; then
   # The check never ran. This lock collision is not a failed recovery attempt.
   WAITING_LOCK=1; LEFT=60
  elif [ -n "$LAST_LIVE" ] && ! kill -0 "$LAST_LIVE" 2>/dev/null && [ "$LAST_LIVE" != "$REQUESTED_PID" ]; then
   [ "$MISSING_RETRIES" -ge 7 ] || MISSING_RETRIES=$((MISSING_RETRIES + 1))
   LEFT=0
  else
   [ "$MISSING_RETRIES" -ge 7 ] || MISSING_RETRIES=$((MISSING_RETRIES + 1))
   if [ "$MISSING_RETRIES" -le 6 ]; then [ "$LEFT" -le 3 ] || LEFT=3
   else LEFT=60; fi
  fi
 fi
 TICKS=0
 while [ "$LEFT" -gt 0 ] && [ -f "$BASE/health-enabled" ]; do
  [ -f "$BASE/health-now" ] && { rm -f "$BASE/health-now"; break; }
  [ $((TICKS % 5)) -ne 0 ] || renew_monitor_wake
  sleep 1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
  LEFT=$((LEFT - 1)); TICKS=$((TICKS + 1))
  # Only while an authorized engine is missing: re-arm a replacement during
  # backoff, so its next death cannot inherit the previous failure's debt.
  if [ "$MISSING_RETRIES" -gt 0 ] || [ "$WAITING_LOCK" -eq 1 ]; then
   if ! expects_engine; then LAST_LIVE=; MISSING_RETRIES=0; WAITING_LOCK=0
   else
    CANDIDATE=$(live_engine_pid)
    if [ -z "$CANDIDATE" ]; then REJECTED_PID=
    elif [ "$CANDIDATE" != "$REJECTED_PID" ]; then
     if engine_identity "$CANDIDATE"; then
      LAST_LIVE=$CANDIDATE; ENGINE_PID=$CANDIDATE
      MISSING_RETRIES=0; TRANSIENT_RETRIES=0; WAITING_LOCK=0
     else REJECTED_PID=$CANDIDATE; fi
    fi
    if [ "$WAITING_LOCK" -eq 1 ] && "$BB" flock -n "$BASE/health-check.lock" "$BB" flock -n /data/adb/call-service-health.lock true; then break; fi
   fi
  fi
  case "$OWNER_PID" in ''|*[!0-9]*) ;; *) kill -0 "$OWNER_PID" 2>/dev/null || break;; esac
  case "$ENGINE_PID" in ''|*[!0-9]*) ;; *) if ! kill -0 "$ENGINE_PID" 2>/dev/null; then RECOVERY_PID=$ENGINE_PID; break; fi;; esac
  # Only the cached PID is checked each second; Binder checks remain infrequent.
  if [ $((TICKS % 10)) -eq 0 ] && ! "$BB" timeout 8 dumpsys activity services com.fann.asterisk 2>/dev/null 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- | "$BB" grep -q 'isForeground=true' 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-; then
   break
  fi
 done
done
