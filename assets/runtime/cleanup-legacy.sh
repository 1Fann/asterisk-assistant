#!/system/bin/sh
set -eu
BASE=/data/adb/asterisk-app
OLD=/data/adb/sip-pbx
BB=/data/adb/ksu/bin/busybox
[ -f "$BASE/.asterisk-app-owned" ] && [ -f "$BASE/migration-verified" ] || { echo migration_not_verified; exit 1; }
[ "$("$BASE/control.sh" state)" = running ] || exit 1
[ -f "$BASE/rootfs/etc/asterisk-app/selftest-passed" ] || { echo selftest_required; exit 1; }
if [ -d "$OLD" ]; then
  [ -f "$OLD/control.sh" ] && [ -d "$OLD/rootfs/etc/asterisk" ] || exit 1
  touch "$OLD/disabled"
  "$BB" flock "$OLD/supervisor.lock" true
  "$OLD/control.sh" stop >/dev/null
  [ "$(readlink -f "$OLD")" = /data/adb/sip-pbx ] || exit 1
  rm -rf /data/adb/sip-pbx
fi
rm -f /data/adb/service.d/98-sip-pbx.sh
if cmd package list packages local.sip.pbx.network | "$BB" grep -q '^package:local.sip.pbx.network$'; then pm uninstall local.sip.pbx.network >/dev/null; fi
rm -rf "$BASE/migration" "$BASE/rootfs/etc/asterisk-app/import-check"
touch "$BASE/legacy-cleaned"
echo legacy_cleanup_complete
