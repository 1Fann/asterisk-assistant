#!/system/bin/sh
# Run on Android with: sh check_wifi_route.sh /path/to/wifi-route.sh
# Uses a private fixture, mocked network commands and a stub solicitation sender.
set -eu
TEST=$(mktemp -d /data/local/tmp/pbx-route-check.XXXXXX)
trap 'rm -f "$TEST/bin/ip" "$TEST/control.sh" "$TEST/enter.sh" "$TEST/check.sh" "$TEST/mac" "$TEST/routes" "$TEST/seen" "$TEST/.asterisk-app-owned" "$TEST/disabled" "$TEST/wifi-compat.enabled" "$TEST/wifi-route.last-rs" "$TEST/rootfs/etc/asterisk-app/public-ipv6.json"; rmdir "$TEST/bin" "$TEST/rootfs/etc/asterisk-app" "$TEST/rootfs/etc" "$TEST/rootfs" "$TEST"' EXIT
mkdir -p "$TEST/bin" "$TEST/rootfs/etc/asterisk-app"
sed "s|^BASE=/data/adb/asterisk-app|BASE=$TEST|;s|/sys/class/net/wlan0/address|$TEST/mac|" "$1" >"$TEST/check.sh"
export TEST PATH="$TEST/bin:$PATH"
cat >"$TEST/bin/ip" <<'EOF'
#!/system/bin/sh
case "$*" in
 *'scope global') echo '3: wlan0 inet6 2001:db8::1/64 scope global';;
 *'scope link') echo '3: wlan0 inet6 fe80::1/64 scope link';;
 *'route show'*) cat "$TEST/routes";;
 *) exit 1;;
esac
EOF
printf '#!/system/bin/sh\necho running\n' >"$TEST/control.sh"
printf '#!/system/bin/sh\nprintf "%%s\\n" "$*" >"$TEST/seen"\n' >"$TEST/enter.sh"
chmod 700 "$TEST/bin/ip" "$TEST/control.sh" "$TEST/enter.sh"
touch "$TEST/.asterisk-app-owned" "$TEST/wifi-compat.enabled"
echo '02:00:00:00:00:01' >"$TEST/mac"
conf="$TEST/rootfs/etc/asterisk-app/public-ipv6.json";echo '{"enabled":true}' >"$conf"
check() {
 rm -f "$TEST/seen";printf '%s\n' "$2" >"$TEST/routes";sh "$TEST/check.sh" check
 if [ "$1" = send ]; then grep -q '^/usr/bin/python3 /opt/asterisk-app/wifi-rs.py fe80::1 02:00:00:00:00:01$' "$TEST/seen"; else [ ! -e "$TEST/seen" ]; fi
}
check skip 'default via fe80::abcd dev wlan0 proto ra expires 121sec pref medium'
check send 'default via fe80::abcd dev wlan0 proto ra expires 120sec pref medium'
check send ''
check send 'default via fe80::abcd dev ccmni0 proto ra expires 1700sec'
check skip 'default via fe80::abcd dev wlan0 proto static'
check skip 'default via fe80::abcd dev wlan0 proto ra expires 1sec
default via fe80::def0 dev wlan0 proto ra expires 300sec'
touch "$TEST/disabled";check skip '';rm -f "$TEST/disabled"
echo '{"enabled":false}' >"$conf";check skip ''
echo '{"enabled":true}' >"$conf";rm -f "$TEST/wifi-compat.enabled";check skip ''
echo 'PASS: healthy, missing and expiring Wi-Fi routes, other interfaces, multiple gateways, manual stop, disabled public mode and compatibility opt-out'
