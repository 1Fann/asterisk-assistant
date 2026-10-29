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
 loop) exec "$BB" flock -n "$BASE/health-loop.lock" /system/bin/sh "$BASE/health.sh" --loop;;
 once) exec "$BB" flock -n "$BASE/health-check.lock" "$BB" flock /data/adb/call-service-health.lock /system/bin/sh "$BASE/health.sh" --check;;
 --loop|--check) ;;
 *) exit 2;;
esac
if [ "$1" = --check ]; then
 [ -f "$BASE/health-enabled" ] || exit 0
 [ "$(getprop sys.boot_completed)" = 1 ] || exit 0
 [ "$(cmd activity get-started-user-state 0 2>/dev/null)" = RUNNING_UNLOCKED ] || exit 0
 HELPER=$(pm path com.fann.asterisk 2>/dev/null | sed -n 's/^package://p' | head -n 1)
 [ -n "$HELPER" ] && [ -f "$HELPER" ] || exit 0
 # Validate protected hashes BEFORE loading APK code as root, including after reinstall/update.
 EXPECTED=$(cat "$BASE/health-helper.sha256" 2>/dev/null)
 [ -n "$EXPECTED" ] && [ "$("$BB" sha256sum "$HELPER" | "$BB" awk '{print $1}')" = "$EXPECTED" ] || exit 0
 exec "$BB" timeout 180 env CLASSPATH="$HELPER" app_process /system/bin --nice-name=asterisk_health_check com.fann.asterisk.HealthMain </dev/null >/dev/null 2>&1
fi
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
while [ -f "$BASE/health-enabled" ]; do
 renew_monitor_wake
 /system/bin/sh "$BASE/health.sh" once
 MINUTES=$(cat "$BASE/health-minutes" 2>/dev/null)
 case "$MINUTES" in ''|*[!0-9]*) MINUTES=5;; esac
 [ "$MINUTES" -ge 1 ] && [ "$MINUTES" -le 1440 ] || MINUTES=5
 LEFT=$((MINUTES * 60))
 while [ "$LEFT" -gt 0 ] && [ -f "$BASE/health-enabled" ]; do
  [ -f "$BASE/health-now" ] && { rm -f "$BASE/health-now"; break; }
  renew_monitor_wake
  sleep 5
  LEFT=$((LEFT - 5))
  # A cheap service-owner check detects task-cleaner damage without waiting a full interval.
  # Full recovery still applies the manual-OFF and active-call guards in HealthMain.
  if [ $((LEFT % 10)) -eq 0 ] && ! dumpsys activity services com.fann.asterisk 2>/dev/null | "$BB" grep -q 'isForeground=true'; then
   break
  fi
 done
done
