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
enabled() {
 [ -f "$BASE/wifi-compat.enabled" ] && [ ! -f "$BASE/disabled" ] &&
 "$BB" grep -q '"enabled"[[:space:]]*:[[:space:]]*true' "$BASE/rootfs/etc/asterisk-app/public-ipv6.json" &&
 [ "$("$BASE/control.sh" state)" = running ]
}
record() {
 local current
 current=
 [ ! -r "$BASE/wifi-route.status" ] || IFS= read -r current <"$BASE/wifi-route.status"
 [ "$current" = "$1" ] || { printf '%s\n' "$1" >"$BASE/wifi-route.status.new.$$" && mv -f "$BASE/wifi-route.status.new.$$" "$BASE/wifi-route.status"; }
}
check_route() {
 local address lookup table defaults
 address=$("$BASE/ipv6.sh" route-source) || return 2
 [ "$address" != ambiguous ] || return 3
 [ -n "$address" ] || return 1
 # RTM_GETROUTE is a local kernel lookup; no packet is sent to this address.
 lookup=$(ip -6 route get 2606:4700:4700::1111 from "$address" $UID_SELECTOR 2>/dev/null) || return 1
 lookup=${lookup%%'
'*}
 table=$(printf '%s\n' "$lookup" | "$BB" awk '{for(i=1;i<NF;i++)if($i=="table"){print $(i+1);exit}}')
 case "$table" in *[!a-zA-Z0-9_.-]*) return 2;; esac
 defaults=$(ip -6 route show table "${table:-main}" default 2>/dev/null) || return 2
 printf '%s\n%s\n' "$lookup" "$defaults" | "$BB" chroot "$BASE/rootfs" /usr/bin/python3 -IB /opt/asterisk-app/wifi-rs.py route-check "$address"
}
enabled || exit 0
UID_SELECTOR=
if ip -6 route help 2>&1 | "$BB" grep -qw uid; then
 engine_uid=$("$BB" awk -F: '$1=="asterisk" {print $3; exit}' "$BASE/rootfs/etc/passwd")
 case "$engine_uid" in ''|*[!0-9]*) record unknown-source; exit 0;; esac
 UID_SELECTOR="uid $engine_uid"
fi
check_route; result=$?
case "$result" in
 0) record local-route-ready; exit 0;;
 1) ;;
 3) record ambiguous-source; exit 0;;
 *) record route-check-unavailable; exit 0;;
esac
source=$(ip -6 -o addr show dev wlan0 scope link | "$BB" awk '$3=="inet6" && !/ tentative| dadfailed| deprecated/ {split($4,a,"/");print a[1];exit}')
[ -n "$source" ] && IFS= read -r mac </sys/class/net/wlan0/address || { record no-link-local; exit 0; }
enabled || exit 0
# The kernel installs the gateway and lifetime supplied by the router's RA.
"$BASE/enter.sh" /usr/bin/python3 /opt/asterisk-app/wifi-rs.py "$source" "$mac" || { record solicitation-failed; exit 0; }
date +%s > "$BASE/wifi-route.last-rs"
record awaiting-kernel-route
for delay in 1 2 3; do
 sleep "$delay" 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
 enabled || exit 0
 if check_route; then
  date +%s > "$BASE/wifi-route.last-verified-rs"
  record local-route-ready
  exit 0
 fi
done
record solicitation-unconfirmed
