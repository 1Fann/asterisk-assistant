#!/system/bin/sh
# Retire only snapshotted Wi-Fi loops during APK asset replacement; never PBX.
BASE=/data/adb/asterisk-app
for BB in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do [ ! -x "$BB" ] || break; done
[ -x "$BB" ] && [ -f "$BASE/.asterisk-app-owned" ] || exit 1
case "${1:-}" in
 --worker) ;;
 *) exec "$BB" timeout -k 2 40 "$BB" flock -n "$BASE/wifi-upgrade.lock" /system/bin/sh "$0" --worker;;
esac
. "$BASE/wifi-worker-lib.sh"
OWNERS=
for pid in $(pidof sh); do
 wifi_process "$pid" || continue
 ticks=$WIFI_TICKS
 for role in compat route; do
  if wifi_owner "$pid" "$role" "$ticks"; then OWNERS="$OWNERS $pid:$ticks:$role"; break; fi
 done
done
SLEEPS=
collect_sleeps() {
 local child child_ticks cmd
 for child in $(pidof sleep); do
  wifi_process "$child" && [ "$WIFI_PPID" = "$pid" ] || continue
  child_ticks=$WIFI_TICKS
  cmd=$("$BB" tr '\000' ' ' <"/proc/$child/cmdline" 2>/dev/null)
  case "$cmd" in 'sleep 1 '|'sleep 15 '|'sleep 30 '|'/system/bin/sleep 1 '|'/system/bin/sleep 15 '|'/system/bin/sleep 30 ')
   SLEEPS="$SLEEPS $child:$child_ticks";;
  esac
 done
}
for key in $OWNERS; do
 pid=${key%%:*}; rest=${key#*:}; ticks=${rest%%:*}; role=${rest#*:}
 wifi_owner "$pid" "$role" "$ticks" || continue
 # Snapshot direct sleeps before TERM, then again if the shell deferred TERM.
 # Do not freeze a process: an interrupted updater must never leave it stopped.
 collect_sleeps
 if wifi_owner "$pid" "$role" "$ticks"; then
  kill -TERM "$pid" 2>/dev/null || :
  if wifi_owner "$pid" "$role" "$ticks"; then collect_sleeps; fi
 fi
 done
for key in $SLEEPS; do
 child=${key%%:*}; child_ticks=${key#*:}
 # An orphaned child is still ours only while its original start tick matches.
 wifi_process "$child" && [ "$WIFI_TICKS" = "$child_ticks" ] || continue
 cmd=$("$BB" tr '\000' ' ' <"/proc/$child/cmdline" 2>/dev/null)
 case "$cmd" in 'sleep 1 '|'sleep 15 '|'sleep 30 '|'/system/bin/sleep 1 '|'/system/bin/sleep 15 '|'/system/bin/sleep 30 ') kill -TERM "$child" 2>/dev/null || :;; esac
done
sleep 0.25 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
for key in $OWNERS; do
 pid=${key%%:*}; rest=${key#*:}; ticks=${rest%%:*}; role=${rest#*:}
 if wifi_owner "$pid" "$role" "$ticks"; then kill -KILL "$pid" 2>/dev/null || :; fi
done
if [ -f "$BASE/wifi-compat.enabled" ] && [ ! -f "$BASE/disabled" ]; then
 "$BB" setsid /system/bin/sh "$BASE/wifi-compat.sh" loop </dev/null >/dev/null 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
fi
