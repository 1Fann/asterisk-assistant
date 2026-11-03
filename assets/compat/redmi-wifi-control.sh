#!/system/bin/sh
# Executed from the verified app's assets under an exclusive per-module lock.
set -eu
umask 077
BASE=/data/adb
BB=$BASE/magisk/busybox
ID=interlink_wifi_awake
TARGET=com.android.wifi.resources
OVERLAY=local.interlink.redmi.wifiawake
APK=system/product/overlay/ZZInterlinkWifiAwake.apk
MODULE_SHA=2e6c42e2c62807ba47ebacd4d0ac700d1f2a7d72cb46bb755a2d3c91fd0d4d80
RRO_SHA=a46d25a9f2641e9e3e1e2aa480ea07c55d98a9966b8eba9b18d1b3483c19f5d0
PROP_SHA=91c50778a615189073811212ffb722efd10418a71e38c687dd0458effeae8fc7
CUSTOM_SHA=49dd3c5ce1f00674e0889a86eb05a2b5848c6743414f1e438a0134d0be29f04a
live=$BASE/modules/$ID
next=$BASE/modules_update/$ID
finish() { printf '%s\n' "$1"; exit 0; }
digest() { [ -f "$1" ] && [ ! -L "$1" ] && [ "$("$BB" sha256sum "$1" | "$BB" cut -d' ' -f1)" = "$2" ]; }
owned() {
 dir=$1
 [ ! -L "$dir" ] || return 1
 [ -e "$dir" ] || return 0
 [ -d "$dir" ] && digest "$dir/module.prop" "$PROP_SHA" || return 1
 # Magisk may generate top-level partition aliases, including dangling aliases
 # for unused partitions. Never follow one for payload or marker verification.
 "$BB" find "$dir" -mindepth 1 | while IFS= read -r path; do
  case "${path#"$dir"/}" in
   system|system/product|system/product/overlay) [ -d "$path" ] && [ ! -L "$path" ] || exit 1;;
   module.prop|"$APK"|disable|remove|update) [ -f "$path" ] && [ ! -L "$path" ] || exit 1;;
   customize.sh) digest "$path" "$CUSTOM_SHA" || exit 1;;
   product|vendor|system_ext)
    part=${path##*/}
    [ -L "$path" ] || exit 1
    case "$("$BB" readlink "$path")" in "system/$part"|"./system/$part"|"$dir/system/$part"|"$live/system/$part") ;; *) exit 1;; esac;;
   *) exit 1;;
  esac
 done || return 1
 if digest "$dir/$APK" "$RRO_SHA"; then return 0; fi
 # On a first installation Magisk may leave a live metadata stub beside
 # the full pending tree. Its pending payload was verified before this call.
 [ "$dir" = "$live" ] && [ -f "$dir/update" ] && [ ! -e "$dir/$APK" ] && [ -d "$next" ]
}
verify_trees() {
 for parent in "$BASE" "$BASE/modules" "$BASE/modules_update"; do [ ! -L "$parent" ] || finish conflict; done
 owned "$next" && owned "$live" || finish conflict
}
state() {
 verify_trees
 if [ -f "$live/remove" ] || [ -f "$next/remove" ]; then finish removing; fi
 path=$(pm path "$OVERLAY" 2>/dev/null || :)
 case "$path" in
  "") loaded=0;;
  package:/product/overlay/ZZInterlinkWifiAwake.apk|package:/system/product/overlay/ZZInterlinkWifiAwake.apk)
   digest "${path#package:}" "$RRO_SHA" || finish conflict
   loaded=1;;
  *) finish conflict;;
 esac
 if [ ! -d "$live" ] && [ ! -d "$next" ]; then [ "$loaded" = 0 ] || finish conflict; finish absent; fi
 if [ -d "$live" ] && [ -d "$next" ]; then
  if [ -f "$live/disable" ] && [ ! -f "$next/disable" ]; then finish mixed; fi
  if [ ! -f "$live/disable" ] && [ -f "$next/disable" ]; then finish mixed; fi
 fi
 if [ -f "$live/disable" ] || [ -f "$next/disable" ]; then
  [ "$loaded" = 0 ] && finish disabled
  finish pending-disable
 fi
 [ -d "$next" ] && finish pending-enable
 [ "$loaded" = 1 ] || finish pending-enable
 [ "$(resource)" = false ] || finish not-effective
 # Check the running Wi-Fi framework as well as the resource resolver.
 if "$BB" timeout 8 dumpsys wifi 2>/dev/null | "$BB" awk '/^[[:space:]]*mSuspendOptimizationsEnabled[[:space:]]+(true|false)[[:space:]]*$/{seen=1;if($2!="false")bad=1} END{exit !(seen&&!bad)}'; then
  finish active
 fi
 finish not-effective
}
resource() { cmd overlay lookup --user 0 "$TARGET" "$TARGET:bool/config_wifiSuspendOptimizationsEnabled" 2>/dev/null || :; }
[ "$(getprop ro.product.device)" = chopin ] && [ "$(getprop ro.build.version.sdk)" = 33 ] || finish unsupported
case "$(magisk -V 2>/dev/null || :)" in ''|*[!0-9]*) finish no-magisk;; esac
[ -n "$(pm path "$TARGET" 2>/dev/null || :)" ] || finish no-target
action=${1:-status}
current=$(state)
case "$action" in
 status) finish "$current";;
 enable|disable) ;;
 *) finish conflict;;
esac
case "$current" in conflict|removing) finish "$current";; esac
if [ "$action" = enable ] && [ "$current" = absent ]; then
 case "$(resource)" in true|false) ;; *) finish no-target;; esac
 temp=$("$BB" mktemp -d "$BASE/.interlink-wifi.XXXXXX") || finish install-failed
 trap 'rm -f "$temp/module.zip"; rmdir "$temp"' EXIT
 printf '%s' "${2:-}" | "$BB" base64 -d >"$temp/module.zip" || finish bad-asset
 digest "$temp/module.zip" "$MODULE_SHA" || finish bad-asset
 # This installer can execute customize.sh; only the exact bundled ZIP is eligible.
 magisk --install-module "$temp/module.zip" >/dev/null 2>&1 || finish install-failed
 [ -d "$next" ] || [ -d "$live" ] || finish install-failed
 state
fi
for dir in "$live" "$next"; do
 [ -d "$dir" ] || continue
 if [ "$action" = disable ]; then
  [ -f "$dir/disable" ] || (set -C; : >"$dir/disable")
 elif [ -f "$dir/disable" ]; then
  rm -f "$dir/disable"
 fi
done
state
