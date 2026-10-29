#!/system/bin/sh
set -eu
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
if [ "${ASTERISK_APP_NS:-0}" != 1 ]; then
  exec "$BB" unshare -m --propagation private /system/bin/sh -c 'export ASTERISK_APP_NS=1; exec /system/bin/sh /data/adb/asterisk-app/enter.sh "$@"' asterisk-app "$@"
fi
R=$BASE/rootfs
mkdir -p "$R/proc" "$R/dev/shm" "$R/run" "$R/tmp"
"$BB" mount -t proc -o nosuid,nodev,noexec,ro proc "$R/proc"
for dev in null zero random urandom; do
  [ -e "$R/dev/$dev" ] || touch "$R/dev/$dev"
  "$BB" mount -o bind "/dev/$dev" "$R/dev/$dev"
done
"$BB" mount -t tmpfs -o nosuid,nodev,mode=1777 tmpfs "$R/dev/shm"
"$BB" ln -sfn /proc/self/fd "$R/dev/fd"
"$BB" ln -sfn /proc/self/fd/0 "$R/dev/stdin"
"$BB" ln -sfn /proc/self/fd/1 "$R/dev/stdout"
"$BB" ln -sfn /proc/self/fd/2 "$R/dev/stderr"
chmod 1777 "$R/tmp"
exec "$BB" chroot "$R" /usr/bin/env -i PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin LANG=C.UTF-8 TZ=Asia/Shanghai "$@"
