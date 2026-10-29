#!/system/bin/sh
# Select a single, non-temporary global-unicast Wi-Fi address; never fall back to privacy addresses.
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
addresses=$(ip -6 -o addr show dev wlan0 scope global 2>/dev/null | "$BB" awk '
 /(^|[[:space:]])(temporary|tentative|deprecated|dadfailed)([[:space:]]|$)/ {next}
 /preferred_lft 0sec/ {next}
 $3=="inet6" {split($4,a,"/");if(a[1] ~ /^[23][0-9a-fA-F]*:/)print a[1]}
' | "$BB" sort -u)
previous=$(cat "$BASE/rootfs/etc/asterisk-app/lan-ipv6" 2>/dev/null)
if [ -n "$previous" ] && printf '%s\n' "$addresses" | "$BB" grep -qxF "$previous"; then
 printf '%s\n' "$previous"
elif [ "$(printf '%s\n' "$addresses" | "$BB" grep -c :)" = 1 ]; then
 printf '%s\n' "$addresses"
fi
