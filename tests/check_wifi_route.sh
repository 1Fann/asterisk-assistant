#!/system/bin/sh
# Exercise real check/selector code with isolated Android IP responses. The
# parser uses the host Python or the deployed PBX Python interpreter on Android.
set -eu
SOURCE_DIR=$(cd "$(dirname "$1")" && pwd)
TEST=$(mktemp -d "${TMPDIR:-/data/local/tmp}/pbx-route-check.XXXXXX")
trap 'rm -rf "$TEST"' EXIT
export TEST SOURCE_DIR PATH="$TEST/bin:$PATH" SHELL_PATH="$(command -v sh)"
REAL_BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
 [ ! -x "$candidate" ] || { REAL_BB=$candidate; break; }
done
export REAL_BB
mkdir -p "$TEST/bin" "$TEST/rootfs/etc/asterisk-app"
cat >"$TEST/prefix" <<'EOF'
BASE=$TEST
BB=bb
bb() {
 applet=$1; shift
 if [ "$applet" = chroot ]; then
  [ "$4" = /opt/asterisk-app/wifi-rs.py ] || exit 90
  if [ -n "${ROUTE_TEST_PYTHON:-}" ]; then
   "$ROUTE_TEST_PYTHON" -IB "$SOURCE_DIR/wifi-rs.py" "$5" "$6"
  else
   "$REAL_BB" chroot /data/adb/asterisk-app/rootfs /usr/bin/python3 -IB -c "$(cat "$SOURCE_DIR/wifi-rs.py")" "$5" "$6"
  fi
 elif [ -n "$REAL_BB" ]; then "$REAL_BB" "$applet" "$@"
 else command "$applet" "$@"; fi
}
sleep() { :; }
EOF
{ printf '#!%s\n' "$SHELL_PATH"; cat "$TEST/prefix"; sed -n '/^umask 077/,$p' "$1" | sed "s|/sys/class/net/wlan0/address|$TEST/mac|"; } >"$TEST/check.sh"
{ printf '#!%s\n' "$SHELL_PATH"; cat "$TEST/prefix"; sed -n '/^addresses=/,$p' "$SOURCE_DIR/ipv6.sh"; } >"$TEST/ipv6.sh"
cp "$SOURCE_DIR/wifi-worker-lib.sh" "$TEST/wifi-worker-lib.sh"
{ printf '#!%s\n' "$SHELL_PATH"; cat <<'EOF'
case "$*" in
 *'scope global') cat "$TEST/addresses";;
 *'scope link') cat "$TEST/link";;
 '-6 route help') echo 'uid NUMBER';;
 '-6 route get '*"from 2001:db8:1::8 uid 223") cat "$TEST/lookup";;
 '-6 route show table wlan0 default') cat "$TEST/routes";;
 *) exit 1;;
esac
EOF
} >"$TEST/bin/ip"
printf '#!%s\necho running\n' "$SHELL_PATH" >"$TEST/control.sh"
{ printf '#!%s\n' "$SHELL_PATH"; cat <<'EOF'
[ "$*" = '/usr/bin/python3 /opt/asterisk-app/wifi-rs.py fe80::8 02:00:00:00:00:01' ] || exit 91
printf 'RS\n' >>"$TEST/sent"
[ ! -f "$TEST/after_addr" ] || cp "$TEST/after_addr" "$TEST/addresses"
[ ! -f "$TEST/after_route" ] || cp "$TEST/after_route" "$TEST/routes"
[ ! -f "$TEST/stop_after" ] || touch "$TEST/disabled"
EOF
} >"$TEST/enter.sh"
if command -v chmod >/dev/null; then chmod 700 "$TEST/bin/ip" "$TEST/control.sh" "$TEST/ipv6.sh" "$TEST/enter.sh"; fi
touch "$TEST/.asterisk-app-owned" "$TEST/wifi-compat.enabled"
echo 'asterisk:x:223:3003:asterisk:/var/lib/asterisk:/bin/false' >"$TEST/rootfs/etc/passwd"
echo '02:00:00:00:00:01' >"$TEST/mac"
echo '3: wlan0 inet6 fe80::8/64 scope link' >"$TEST/link"
conf="$TEST/rootfs/etc/asterisk-app/public-ipv6.json";echo '{"enabled":true}' >"$conf"
address='3: wlan0 inet6 2001:db8:1::8/64 scope global'
lookup='2606:4700:4700::1111 from 2001:db8:1::8 via fe80::1 dev wlan0 table wlan0'
route='default via fe80::1 dev wlan0 proto ra expires 600sec'
echo "$lookup" >"$TEST/lookup";echo "$address" >"$TEST/addresses";echo "$route" >"$TEST/routes"
check() {
 rm -f "$TEST/sent" "$TEST/wifi-route.last-rs" "$TEST/wifi-route.last-verified-rs" "$TEST/wifi-route.status"
 "$SHELL_PATH" "$TEST/check.sh" check
 status=$(cat "$TEST/wifi-route.status" 2>/dev/null || true)
 [ "${status:-inactive}" = "$1" ] || { echo "expected $1, got $status" >&2; exit 1; }
 if [ "$2" = sent ]; then [ "$(cat "$TEST/sent")" = RS ]; [ -s "$TEST/wifi-route.last-rs" ]; else [ ! -e "$TEST/sent" ]; fi
 if [ "${3:-}" = verified ]; then [ -s "$TEST/wifi-route.last-verified-rs" ]; else [ ! -e "$TEST/wifi-route.last-verified-rs" ]; fi
}
check local-route-ready skip
printf '' >"$TEST/routes";check solicitation-unconfirmed sent
echo "$route" >"$TEST/after_route";check local-route-ready sent verified
printf '' >"$TEST/addresses";echo "$address" >"$TEST/after_addr";check local-route-ready sent verified
rm -f "$TEST/after_route" "$TEST/after_addr"
echo 'default from 2001:db8:2::/64 via fe80::1 dev wlan0 expires 600sec' >"$TEST/routes";check solicitation-unconfirmed sent
echo "$route" >"$TEST/routes";echo "${lookup%wlan0 table wlan0}rmnet0 table wlan0" >"$TEST/lookup";check solicitation-unconfirmed sent
echo "$lookup" >"$TEST/lookup";echo '3: wlan0 inet6 2001:db8:2::8/64 scope global' >>"$TEST/addresses";check ambiguous-source skip
printf '' >"$TEST/addresses";printf '' >"$TEST/link";check no-link-local skip
echo '3: wlan0 inet6 fe80::8/64 scope link' >"$TEST/link";touch "$TEST/stop_after";check awaiting-kernel-route sent
check inactive skip;rm -f "$TEST/disabled" "$TEST/stop_after"
echo '{"enabled":false}' >"$conf";check inactive skip
echo '{"enabled":true}' >"$conf";rm -f "$TEST/wifi-compat.enabled";check inactive skip
echo 'PASS: 12 local route checks including missing address, source policies, confirmed/unconfirmed RS, stop and opt-out'
