#!/system/bin/sh
set -eu
umask 077
BASE=/data/adb/asterisk-app
BB=/data/adb/ksu/bin/busybox
R=$BASE/rootfs
phase() { printf '{"phase":"%s","percent":%s}\n' "$1" "$2" > "$BASE/progress.json"; echo "PHASE:$1"; }
trap 'phase failed 0' EXIT
phase verify 30
ACTUAL=$(sha256sum "$1" | "$BB" awk '{print $1}')
[ "$ACTUAL" = a91d5a93010193712d346d761372b7c9db6dfcf093893161c64ca107f05914f2 ] || { echo archive_checksum_mismatch; exit 1; }
mkdir -p "$R"
chmod 755 "$R"
if [ ! -f "$BASE/.rootfs-extracted" ]; then
  phase extract 40
  "$BB" tar -xzf "$1" -C "$R"
  touch "$BASE/.rootfs-extracted"
fi
mkdir -p "$R/opt/asterisk-app" "$R/etc/asterisk-app"
chmod 700 "$R/etc/asterisk-app"
printf '%s\n' "$2" > "$R/etc/asterisk-app/android-uid"
cp "$BASE/guest-install.sh" "$R/opt/asterisk-app/guest-install.sh"
cp "$BASE/"*.py "$BASE/"*.whl "$BASE/run.sh" "$R/opt/asterisk-app/"
phase packages 50
"$BASE/enter.sh" /bin/sh /opt/asterisk-app/guest-install.sh > "$BASE/install.log" 2>&1
IP=$(ip -4 -o addr show wlan0 | "$BB" awk '{split($4,a,"/"); print a[1]; exit}')
[ -n "$IP" ] || { echo wifi_not_ready; exit 1; }
printf '%s\n' "$IP" > "$R/etc/asterisk-app/lan-ip"
phase configure 90
"$BASE/enter.sh" /usr/bin/python3 /opt/asterisk-app/api.py initialize
touch "$BASE/installed"
printf '1\n' > "$BASE/autostart"
phase ready 100
trap - EXIT
