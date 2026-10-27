#!/system/bin/sh
set -eu
BASE=/data/adb/asterisk-app
BB=/data/adb/ksu/bin/busybox
if [ "${1:-}" != --locked ]; then exec "$BB" flock -n "$BASE/supervisor.lock" /system/bin/sh "$BASE/supervisor.sh" --locked; fi
while [ ! -f "$BASE/disabled" ]; do
  IP=$(ip -4 -o addr show wlan0 2>/dev/null | "$BB" awk '{split($4,a,"/"); print a[1]; exit}')
  OLD=$(cat "$BASE/rootfs/etc/asterisk-app/lan-ip" 2>/dev/null || true)
  if [ -n "$IP" ]; then
    if [ "$IP" != "$OLD" ]; then "$BASE/control.sh" stop || true; rm -f "$BASE/disabled"; fi
    if [ "$("$BASE/control.sh" state)" != running ]; then "$BASE/control.sh" start || true; fi
  fi
  sleep 30
done
