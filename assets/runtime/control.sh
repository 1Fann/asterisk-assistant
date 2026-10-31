#!/system/bin/sh
set -eu
BASE=/data/adb/asterisk-app
BB=
for candidate in /data/adb/magisk/busybox /data/adb/ksu/bin/busybox /data/adb/ap/bin/busybox; do
  if [ -x "$candidate" ]; then BB=$candidate; break; fi
done
[ -n "$BB" ] || { echo busybox_missing; exit 20; }
R=$BASE/rootfs
# Serialize native launch/stop. STOP publishes its intent before waiting so an
# automatic recovery still preparing its network cannot undo a manual stop.
case "${1:-status}" in
 start|recover|stop)
  [ "$1" != stop ] || touch "$BASE/disabled"
  # mksh closes numbered descriptors on exec; BusyBox ash retains our lock FD.
  exec "$BB" ash "$0" --acquire "$1"
  ;;
 --acquire)
  case "${2:-}" in start|recover|stop) ;; *) exit 2;; esac
  exec 9>"$BASE/start-stop.lock"
  # Magisk's flock has no -w. Its timeout helper can retain inherited locks, so
  # retry only nonblocking acquisition; sleeping descendants cannot retain FD 9.
  LOCK_WAIT=0
  until "$BB" flock -n 9; do
   [ "$LOCK_WAIT" -lt 20 ] || { echo control_busy; exit 1; }
   LOCK_WAIT=$((LOCK_WAIT + 1))
   sleep 1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-
  done
  set -- "--locked-$2"
  ;;
esac
automatic_allowed() {
 [ -f "$BASE/health-enabled" ] && [ -f "$BASE/background-authorized" ] && [ ! -f "$BASE/disabled" ]
}
running() {
  [ -r "$R/run/asterisk/asterisk.pid" ] || return 1
  PBX_PID=$(cat "$R/run/asterisk/asterisk.pid" 2>/dev/null) || return 1
  case "$PBX_PID" in ''|*[!0-9]*) return 1;; esac
  [ -r "/proc/$PBX_PID/cmdline" ] || return 1
  [ "$(readlink /proc/$PBX_PID/root 2>/dev/null)" = "$R" ] || return 1
  tr '\000' ' ' < "/proc/$PBX_PID/cmdline" | "$BB" grep -q '/usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf'
}
case "${1:-status}" in
  ipv6) exec /system/bin/sh "$BASE/ipv6.sh";;
  network-state)
    /system/bin/sh "$BASE/ipv6.sh" > "$R/etc/asterisk-app/lan-ipv6.tmp"
    chmod 640 "$R/etc/asterisk-app/lan-ipv6.tmp"
    chown 0:3003 "$R/etc/asterisk-app/lan-ipv6.tmp"
    mv "$R/etc/asterisk-app/lan-ipv6.tmp" "$R/etc/asterisk-app/lan-ipv6"
    ;;
  state) if running; then echo running; else echo stopped; fi;;
  --locked-start|--locked-recover)
    AUTOMATIC=0; [ "$1" != --locked-recover ] || AUTOMATIC=1
    if [ "$AUTOMATIC" = 1 ]; then automatic_allowed || { echo recovery_paused; exit 1; }; fi
    [ -f "$BASE/installed" ] || { echo not_installed; exit 1; }
    REAL_UID=$(cmd package list packages -U com.fann.asterisk 2>/dev/null | "$BB" awk '$1=="package:com.fann.asterisk" {split($2,a,":"); print a[2]}')
    [ -n "$REAL_UID" ] && [ "$REAL_UID" = "$(cat "$R/etc/asterisk-app/android-uid")" ] || { echo uid_mismatch; exit 1; }
    if [ "$AUTOMATIC" = 0 ]; then rm -f "$BASE/disabled"; fi
    if ! running; then
      IP=$(ip -4 -o addr show wlan0 | "$BB" awk '{split($4,a,"/"); print a[1]; exit}')
      [ -n "$IP" ] || { echo wifi_not_ready; exit 1; }
      printf '%s\n' "$IP" > "$R/etc/asterisk-app/lan-ip"
      "$BASE/control.sh" network-state
      . "$BASE/network-cache.sh"
      prepare_network
      if [ "$AUTOMATIC" = 1 ]; then automatic_allowed || { echo recovery_paused; exit 1; }; fi
      "$BB" setsid "$BASE/enter.sh" /bin/sh /opt/asterisk-app/run.sh </dev/null >"$BASE/console.log" 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
      # Preserve the three-second launch allowance, returning as soon as its
      # verified process exists. HealthMain still checks actual SIP responses.
      n=0
      while ! running && [ "$n" -lt 12 ]; do
        sleep 0.25 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-; n=$((n+1))
      done
      running || { echo start_failed; exit 1; }
    fi
    "$BB" setsid /system/bin/sh "$BASE/supervisor.sh" </dev/null >"$BASE/supervisor.log" 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
    if [ -f "$BASE/wifi-compat.enabled" ]; then
      "$BB" setsid /system/bin/sh "$BASE/wifi-compat.sh" loop </dev/null >/dev/null 2>&1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&- &
    fi
    echo running
    ;;
  --locked-stop)
    touch "$BASE/disabled"
    if running; then
      kill -TERM "$PBX_PID"
      n=0
      while running && [ "$n" -lt 15 ]; do sleep 1 3>&- 4>&- 5>&- 6>&- 7>&- 8>&- 9>&-; n=$((n+1)); done
      if running; then echo stop_timeout; exit 1; fi
    fi
    echo stopped
    ;;
  restart) "$BASE/control.sh" stop; "$BASE/control.sh" start;;
  cli) shift; exec "$BASE/enter.sh" /usr/sbin/asterisk -rx "$*";;
  api)
    shift
    case "${1:-status}" in status|logs|accounts|credentials|save_account|delete_account|read_file|save_file|restore_file|set_ports|set_public_ipv6|set_callerid|network|initialize|migration_verify|selftest) ;; *) echo invalid_action; exit 1;; esac
    LEGACY=0; [ -d /data/adb/sip-pbx ] && LEGACY=1
    AUTO=$(cat "$BASE/autostart" 2>/dev/null || echo 0)
    CLEANED=0; [ -f "$BASE/legacy-cleaned" ] && CLEANED=1
    exec "$BASE/enter.sh" /usr/bin/python3 /opt/asterisk-app/api.py "${1:-status}" "$LEGACY" "$AUTO" "$CLEANED"
    ;;
  autostart)
    case "${2:-}" in 0|1) printf '%s\n' "$2" > "$BASE/autostart";; *) exit 1;; esac
    echo updated
    ;;
  status)
    if [ -f "$BASE/installed" ]; then exec "$BASE/control.sh" api status; fi
    LEGACY=false; [ -d /data/adb/sip-pbx ] && LEGACY=true
    PROGRESS='{}'; [ -f "$BASE/progress.json" ] && PROGRESS=$(cat "$BASE/progress.json")
    printf '{"ok":true,"installed":false,"running":false,"legacyFound":%s,"progress":%s}\n' "$LEGACY" "$PROGRESS"
    ;;
  *) echo invalid_action; exit 2;;
esac
