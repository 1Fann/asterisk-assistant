#!/system/bin/sh
# asterisk-assistant-owned: Android 13 screen-off Wi-Fi compatibility.
# Retain Wi-Fi receive performance only while the owned PBX is running.
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
[ -x "$BB" ] && [ -f "$BASE/.asterisk-app-owned" ] || exit 1
case "${1:-loop}" in
 loop) exec "$BB" flock -n "$BASE/wifi-compat.lock" /system/bin/sh "$0" --loop;;
 --loop) ;;
 *) exit 2;;
esac
umask 077
HELD=0
release() {
 if [ "$HELD" = 1 ]; then cmd wifi force-hi-perf-mode disabled >/dev/null 2>&1; fi
 rm -f "$BASE/wifi-compat.active" "$BASE/wifi-compat.pid"
}
trap release EXIT
trap 'exit 0' HUP INT TERM
printf '%s\n' "$$" > "$BASE/wifi-compat.pid"
while [ -f "$BASE/wifi-compat.enabled" ]; do
 WANT=0
 if [ "$(getprop sys.boot_completed)" = 1 ] && [ ! -f "$BASE/disabled" ] &&
    [ "$(/system/bin/sh "$BASE/control.sh" state 2>/dev/null)" = running ] &&
    "$BB" grep -q '"enabled"[[:space:]]*:[[:space:]]*true' "$BASE/rootfs/etc/asterisk-app/public-ipv6.json" 2>/dev/null &&
    ip -6 -o addr show dev wlan0 scope global 2>/dev/null | "$BB" grep -q 'inet6 '; then
  WANT=1
 fi
 if [ "$WANT" = 1 ]; then
  # Reapply after Wi-Fi reconnects; this setting is not persistent across reboot.
  if cmd wifi force-hi-perf-mode enabled >/dev/null 2>&1; then
   HELD=1; touch "$BASE/wifi-compat.active"
  fi
 elif [ "$HELD" = 1 ]; then
  cmd wifi force-hi-perf-mode disabled >/dev/null 2>&1
  HELD=0; rm -f "$BASE/wifi-compat.active"
 fi
 sleep 15
done
