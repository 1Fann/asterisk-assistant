#!/system/bin/sh
set -eu
umask 077
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
ARCHIVE=${1:?archive}
APP_UID=${2:?uid}
[ -f "$BASE/.asterisk-app-owned" ] || { echo 'unmanaged_directory'; exit 1; }
REAL_UID=$(cmd package list packages -U com.fann.asterisk | "$BB" awk '$1=="package:com.fann.asterisk" {split($2,a,":"); print a[2]}')
[ "$APP_UID" = "$REAL_UID" ] || { echo uid_mismatch; exit 1; }
case "$ARCHIVE" in /data/user/0/com.fann.asterisk/files/ubuntu-base.tar.gz|/data/data/com.fann.asterisk/files/ubuntu-base.tar.gz) ;; *) echo invalid_archive_path; exit 1;; esac
exec "$BB" flock -n "$BASE/install.lock" /system/bin/sh "$BASE/install-worker.sh" "$ARCHIVE" "$APP_UID"
