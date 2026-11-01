#!/system/bin/sh
# Keep the router-advertised return path for public SIP available during sleep.
BASE=/data/adb/asterisk-app
for BB in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
 [ ! -x "$BB" ] || break
done
[ -x "$BB" ] && [ -f "$BASE/.asterisk-app-owned" ] || exit 1
umask 077
. "$BASE/wifi-worker-lib.sh"
case "${1:-loop}" in
 loop) exec "$BB" flock -n "$BASE/wifi-route.lock" /system/bin/sh "$0" --loop;;
 --loop)
  wifi_process "$$" || exit 1
  OWNER="$$ $WIFI_TICKS"
  printf '%s\n' "$OWNER" >"$BASE/wifi-route.pid.new.$$"
  mv -f "$BASE/wifi-route.pid.new.$$" "$BASE/wifi-route.pid"
  release_route() {
   local current
   [ -r "$BASE/wifi-route.pid" ] && IFS= read -r current <"$BASE/wifi-route.pid" || return 0
   [ "$current" != "$OWNER" ] || rm -f "$BASE/wifi-route.pid"
  }
  trap release_route EXIT
  trap 'exit 0' TERM INT HUP
  while [ -f "$BASE/wifi-compat.enabled" ]; do
   # A blocked network/namespace command must not stop later renewal attempts.
   "$BB" timeout -k 2 20 /system/bin/sh "$0" check 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
   sleep 30 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
  done
  exit 0;;
 check) ;;
 *) exit 2;;
esac
[ -f "$BASE/wifi-compat.enabled" ] && [ ! -f "$BASE/disabled" ] || exit 0
"$BB" grep -q '"enabled"[[:space:]]*:[[:space:]]*true' "$BASE/rootfs/etc/asterisk-app/public-ipv6.json" || exit 0
[ "$("$BASE/control.sh" state)" = running ] || exit 0
ip -6 -o addr show dev wlan0 scope global | "$BB" grep -q 'inet6 [23]' || exit 0
routes=$(ip -6 route show table wlan0 default 2>/dev/null) || routes=$(ip -6 route show table all 2>/dev/null) || exit 0
# A permanent default or one with more than two minutes remaining needs no traffic.
if printf '%s\n' "$routes" | "$BB" awk '
 $1=="default" && / dev wlan0( |$)/ && !/ linkdown( |$)/ {
   expiry=-1
   for(i=1;i<NF;i++)if($i=="expires")expiry=$(i+1)+0
   if(expiry<0 || expiry>120)healthy=1
 }
 END {exit !healthy}'; then exit 0; fi
source=$(ip -6 -o addr show dev wlan0 scope link | "$BB" awk '$3=="inet6" && !/ tentative| dadfailed| deprecated/ {split($4,a,"/");print a[1];exit}')
[ -n "$source" ] && IFS= read -r mac </sys/class/net/wlan0/address || exit 0
# The kernel installs the gateway and lifetime supplied by the router's RA.
if "$BASE/enter.sh" /usr/bin/python3 /opt/asterisk-app/wifi-rs.py "$source" "$mac"; then
 date +%s > "$BASE/wifi-route.last-rs"
fi
