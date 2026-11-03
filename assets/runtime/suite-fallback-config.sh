#!/system/bin/sh
# Called by the signed APK with Magisk BusyBox ash. No companion is enabled here.
set -eu
umask 077
BB=/data/adb/magisk/busybox
BASE=/data/adb/interlink-guard
BOOT=/data/adb/service.d
HOOK=$BOOT/95-interlink-guard.sh
LOCK=/data/adb/.interlink-guard-config.lock
action=${1:-status}
conflict() { echo conflict; exit 0; }
regular() { [ ! -L "$1" ] && [ -f "$1" ] && [ "$("$BB" stat -c '%u:%h' "$1")" = 0:1 ]; }
exists() { [ -e "$1" ] || [ -L "$1" ]; }
boot_text() { printf '#!/system/bin/sh\n# interlink-resilience-owned\n/system/bin/sh /data/adb/interlink-guard/guard.sh\n'; }
ownership() {
    [ ! -L "$BOOT" ] && [ -d "$BOOT" ] || conflict
    if exists "$BASE"; then
        [ ! -L "$BASE" ] && [ -d "$BASE" ] && [ "$("$BB" stat -c '%u:%a' "$BASE")" = 0:700 ] && regular "$BASE/.interlink-owned" || conflict
        for f in guard.sh guard.pid enabled guard.lock ddns.last-repair; do
            if exists "$BASE/$f"; then regular "$BASE/$f" || conflict; fi
        done
    fi
    if exists "$HOOK"; then
        regular "$HOOK" && boot_text | "$BB" cmp -s - "$HOOK" || conflict
        [ -d "$BASE" ] || conflict
    fi
}
running() {
    [ -f "$BASE/guard.pid" ] && read -r pid rest <"$BASE/guard.pid" || return 1
    case "$pid" in ''|0|1|*[!0-9]*) return 1;; esac
    [ -r "/proc/$pid/cmdline" ] && [ "$("$BB" tr '\000' '\n' <"/proc/$pid/cmdline")" = "$(printf '%s\nash\n%s/guard.sh\n--loop' "$BB" "$BASE")" ]
}
status() {
    if [ ! -e "$BASE/enabled" ]; then echo off
    elif [ ! -f "$HOOK" ] || [ ! -x "$BASE/guard.sh" ]; then echo needs_repair
    elif running; then echo running
    else echo waiting; fi
}
[ -x "$BB" ] && [ "$(id -u)" = 0 ] || { echo no_magisk; exit 0; }
ownership
case "$action" in status) status; exit 0;; enable|disable) ;; *) exit 2;; esac
if exists "$LOCK"; then regular "$LOCK" || conflict; fi
exec 8>>"$LOCK"
"$BB" flock -n 8 || { echo busy; exit 0; }
ownership
if [ "$action" = disable ]; then
    # Removing the enabled marker first also makes the existing boot hook inert.
    [ ! -d "$BASE" ] || rm -f "$BASE/enabled"
    [ ! -f "$HOOK" ] || rm -f "$HOOK"
    echo off; exit 0
fi
worker=${2:?missing bundled worker}
digest=${3:?missing digest}
[ "${#digest}" -eq 64 ] && [ "$(printf %s "$worker" | "$BB" sha256sum | "$BB" cut -d ' ' -f 1)" = "$digest" ] || exit 2
if [ ! -d "$BASE" ]; then
    temp=$("$BB" mktemp -d /data/adb/.interlink-guard.XXXXXXXX)
    chmod 700 "$temp"; : >"$temp/.interlink-owned"
    mv "$temp" "$BASE"
fi
tmp=''; trap '[ -z "$tmp" ] || rm -f "$tmp"' EXIT
changed=0
if [ ! -x "$BASE/guard.sh" ] || [ "$("$BB" sha256sum "$BASE/guard.sh" | "$BB" cut -d ' ' -f 1)" != "$digest" ]; then
    tmp=$("$BB" mktemp "$BASE/.worker.XXXXXXXX"); printf %s "$worker" >"$tmp"; chmod 700 "$tmp"; mv -f "$tmp" "$BASE/guard.sh"; tmp=''; changed=1
fi
if [ ! -f "$HOOK" ]; then
    tmp=$("$BB" mktemp "$BOOT/.interlink-boot.XXXXXXXX"); boot_text >"$tmp"; chmod 700 "$tmp"; mv -f "$tmp" "$HOOK"; tmp=''
fi
touch "$BASE/enabled"
if running; then
    if [ "$changed" = 1 ]; then echo updated; else echo running; fi
else
    /system/bin/sh "$BASE/guard.sh" 8>&-
    echo started
fi
