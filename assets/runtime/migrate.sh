#!/system/bin/sh
set -eu
umask 077
BASE=/data/adb/asterisk-app
rm -f "$BASE/rootfs/etc/asterisk-app/selftest-passed" "$BASE/migration-verified"
OLD=/data/adb/sip-pbx
BB=/data/adb/ksu/bin/busybox
R=$BASE/rootfs
touch "$R/etc/asterisk-app/callerid-defer"
trap 'rm -f "$R/etc/asterisk-app/callerid-defer"' EXIT
[ -f "$BASE/installed" ] && [ -f "$BASE/.asterisk-app-owned" ] || exit 1
[ -d "$OLD/rootfs/etc/asterisk" ] || { echo no_legacy_config; exit 1; }
CALLS=$("$OLD/control.sh" cli core show channels count 2>/dev/null | "$BB" awk '/ active calls/{print $1;exit}')
[ "${CALLS:-0}" = 0 ] || { echo active_calls; exit 1; }
mkdir -p "$BASE/migration"
if [ ! -f "$BASE/migration/pending" ]; then
  cp -a "$R/etc/asterisk" "$BASE/migration/fresh-config"
  touch "$BASE/migration/pending"
fi
touch "$OLD/disabled"
"$BB" flock "$OLD/supervisor.lock" true
"$OLD/control.sh" stop >/dev/null
"$BASE/control.sh" stop >/dev/null
cp -a "$OLD/rootfs/etc/asterisk/." "$R/etc/asterisk/"
mkdir -p "$R/etc/asterisk-app/import-check"
for name in pjsip.conf extensions.conf rtp.conf; do cp "$OLD/rootfs/etc/asterisk/$name" "$R/etc/asterisk-app/import-check/$name"; done
if [ -f "$OLD/rootfs/var/lib/asterisk/astdb.sqlite3" ]; then cp "$OLD/rootfs/var/lib/asterisk/astdb.sqlite3" "$R/var/lib/asterisk/astdb.sqlite3"; fi
if ! "$BASE/control.sh" start >/dev/null; then
  "$BASE/control.sh" stop >/dev/null || true
  rm -f "$OLD/disabled"
  /system/bin/sh /data/adb/service.d/98-sip-pbx.sh
  echo migration_start_failed_legacy_restored
  exit 1
fi
if ! "$BASE/control.sh" api migration_verify; then
  "$BASE/control.sh" stop >/dev/null || true
  rm -f "$OLD/disabled"
  /system/bin/sh /data/adb/service.d/98-sip-pbx.sh
  exit 1
fi
touch "$BASE/migration-verified"
