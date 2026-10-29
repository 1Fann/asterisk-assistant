#!/system/bin/sh
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
[ -f "$BASE/installed" ] || exit 0
[ "$(cat "$BASE/autostart" 2>/dev/null)" = 1 ] || [ -f "$BASE/health-enabled" ] || exit 0
if [ "${1:-}" != --worker ]; then
  "$BB" setsid "$BB" flock -n "$BASE/boot.lock" /system/bin/sh "$0" --worker </dev/null >"$BASE/boot.log" 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
  exit 0
fi
while [ "$(getprop sys.boot_completed)" != 1 ]; do sleep 5; done
while [ "$(cmd activity get-started-user-state 0 2>/dev/null | tr -d '\r')" != RUNNING_UNLOCKED ]; do sleep 5; done
if [ -f "$BASE/health-enabled" ]; then
 "$BB" setsid /system/bin/sh "$BASE/health.sh" loop </dev/null >/dev/null 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
fi
while ! ip -4 -o addr show wlan0 | "$BB" grep -q 'inet '; do sleep 5; done
n=0
while [ "$n" -lt 6 ] && [ "$(cat "$BASE/autostart" 2>/dev/null)" = 1 ]; do
  if am start-foreground-service -n com.fann.asterisk/.ManagerService --es action BOOT </dev/null >/dev/null 2>&1; then echo foreground_start_requested; exit 0; fi
  n=$((n+1)); sleep 10
done
