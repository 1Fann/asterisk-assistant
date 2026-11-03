#!/system/bin/sh
# Local Redmi backup for the case where BOTH parts of an enabled root monitor exit.
BASE=/data/adb/interlink-guard
BB=/data/adb/magisk/busybox
[ ! -L "$BASE" ] && [ -f "$BASE/.interlink-owned" ] && [ -x "$BB" ] || exit 0
if [ "${1:-}" != --loop ]; then
    [ -f "$BASE/enabled" ] || exit 0
    "$BB" setsid "$BB" ash "$BASE/guard.sh" --loop </dev/null >/dev/null 2>&1 &
    exit 0
fi
umask 077
exec 9>"$BASE/guard.lock"
"$BB" flock -n 9 || exit 0
printf '%s\n' "$$" >"$BASE/guard.pid"
trap 'rm -f "$BASE/guard.pid"' EXIT
trap 'exit 0' TERM INT HUP

alive() {
    [ -f "$1" ] && [ ! -L "$1" ] && read -r pid rest <"$1" || return 1
    case "$pid" in ''|0|1|*[!0-9]*) return 1;; esac
    [ -r "/proc/$pid/cmdline" ] && "$BB" tr '\000' '\n' <"/proc/$pid/cmdline" | "$BB" grep -Fxq "$2"
}

repair() {
    name=$1; dir=$2; marker=$3; wanted=$4; package=$5
    [ -d "$dir" ] && [ ! -L "$dir" ] && [ -f "$dir/$marker" ] && [ ! -L "$dir/$marker" ] || return 0
    if [ "$wanted" != '-' ]; then [ -f "$dir/$wanted" ] && [ ! -L "$dir/$wanted" ] || return 0; fi
    case "$name" in
        asterisk|voice)
            [ ! -e "$dir/disabled" ] || return 0
            entry=$dir/health.sh; arg=loop
            alive "$dir/health-supervisor.pid" "$entry" || alive "$dir/health-loop.pid" "$entry" || missing=1;;
        sms)
            [ "$(cat "$dir/owner")" = sms-bridge-owned-v1 ] || return 0
            entry=$dir/run.sh; arg=''
            alive "$dir/supervisor.pid" "$entry" || alive "$dir/pid" me.capcom.smsgateway.modules.iphone.RootMonitorMain || missing=1;;
        bark)
            [ ! -e "$dir/update.rollback" ] || return 0
            entry=$dir/monitor-boot.sh; arg=''
            alive "$dir/boot.pid" "$entry" || alive "$dir/boot.pid" /data/adb/service.d/97-sms-push-assistant.sh || alive "$dir/loop.pid" "$dir/monitor.sh" || missing=1;;
        ddns)
            [ ! -e "$dir/disabled" ] && [ ! -e /data/adb/ddns-go.transaction ] || return 0
            entry=$dir/watchdog.sh; arg=''
            alive "$dir/watchdog.pid" "$entry" || alive "$dir/daemon.pid" "$dir/daemon.sh" || missing=1;;
    esac
    [ "${missing:-0}" = 1 ] || return 0
    [ -f "$entry" ] && [ ! -L "$entry" ] && [ "$("$BB" stat -c %u "$entry")" = 0 ] || return 0
    # Avoid racing a normal update or bringing up a removed Android package.
    if [ -f "$BASE/$name.retry" ]; then
        read -r last <"$BASE/$name.retry"
        [ $((now-last)) -ge 60 ] || return 0
    fi
    printf '%s\n' "$now" >"$BASE/$name.retry"
    "$BB" timeout -k 1 5 /system/bin/cmd package path "$package" 9>&- | "$BB" grep -q '^package:' || return 0
    [ -f "$BASE/enabled" ] || return 0
    if [ "$name" = ddns ]; then
        [ ! -e "$dir/disabled" ] && [ ! -e /data/adb/ddns-go.transaction ] || return 0
        "$BB" setsid "$BB" ash "$entry" </dev/null >/dev/null 2>&1 9>&- &
    else
        [ -f "$dir/$wanted" ] || return 0
        "$BB" setsid /system/bin/sh "$entry" $arg </dev/null >/dev/null 2>&1 9>&- &
    fi
    printf '%s\n' "$(date +%s)" >"$BASE/$name.last-repair"
}

# Per-boot retry timestamps are monotonic. Each original manager is responsible
# for APK identity, user preferences, call safety and its own singleton lock.
for app in asterisk voice sms bark ddns; do rm -f "$BASE/$app.retry"; done
next_policy=0
while [ -f "$BASE/enabled" ]; do
    read -r up rest </proc/uptime; now=${up%%.*}
    if [ "$(getprop sys.boot_completed)" = 1 ]; then
        # MIUI can reinstate the management app's background restriction on boot.
        # The DDNS engine itself runs under root. Preserve its explicit pause.
        if [ "$now" -ge "$next_policy" ] && [ -f /data/adb/ddns-go/.ddns-go-android-root ] && [ ! -e /data/adb/ddns-go/disabled ]; then
            next_policy=$((now+300))
            pkg=com.mcyao.ddnspanel
            if "$BB" timeout 5 cmd appops get "$pkg" RUN_ANY_IN_BACKGROUND 9>&- | "$BB" grep -Eq 'RUN_ANY_IN_BACKGROUND: (ignore|deny|errored)'; then
                "$BB" timeout 5 cmd appops set --uid "$pkg" RUN_ANY_IN_BACKGROUND allow 9>&-
                "$BB" timeout 5 cmd appops set "$pkg" RUN_ANY_IN_BACKGROUND allow 9>&-
            fi
        fi
        missing=0; repair asterisk /data/adb/asterisk-app .asterisk-app-owned health-enabled com.fann.asterisk
        missing=0; repair voice /data/adb/voice-sip-assistant .owned health-enabled com.fann.voicesiphelper
        missing=0; repair sms /data/adb/sms-bridge owner enabled me.capcom.smsgateway.iphone
        missing=0; repair bark /data/adb/sms-push-assistant .owned enabled com.mcyao.barkserver
        missing=0; repair ddns /data/adb/ddns-go .ddns-go-android-root - com.mcyao.ddnspanel
    fi
    sleep 10 9>&-
done
