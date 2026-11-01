# Sourced by owned Wi-Fi workers. Normal liveness ticks use shell builtins only.
wifi_process() {
 local pid stat rest
 pid=$1
 case "$pid" in ''|0|1|*[!0-9]*) return 1;; esac
 [ -r "/proc/$pid/stat" ] && IFS= read -r stat <"/proc/$pid/stat" || return 1
 rest=${stat##*) }; set -- $rest
 [ "$#" -ge 20 ] && [ "$1" != Z ] && [ "$1" != X ] || return 1
 WIFI_PPID=$2; WIFI_TICKS=${20}
 case "$WIFI_TICKS" in ''|*[!0-9]*) return 1;; esac
 kill -0 "$pid" 2>/dev/null
}
wifi_owner() {
 local pid role expected cmd
 pid=$1; role=$2; expected=$3
 case "$role" in route|compat) ;; *) return 1;; esac
 wifi_process "$pid" && [ "$WIFI_TICKS" = "$expected" ] || return 1
 cmd=$("$BB" tr '\000' '\n' <"/proc/$pid/cmdline" 2>/dev/null) || return 1
 [ "$cmd" = "/system/bin/sh
$BASE/wifi-$role.sh
--loop" ]
}
wifi_route_alive() {
 local pid ticks extra
 [ -r "$BASE/wifi-route.pid" ] && read -r pid ticks extra <"$BASE/wifi-route.pid" || return 1
 [ -z "$extra" ] && wifi_process "$pid" && [ "$WIFI_TICKS" = "$ticks" ] || return 1
 if [ "${ROUTE_OWNER:-}" != "$pid:$ticks" ]; then
  wifi_owner "$pid" route "$ticks" || return 1
  ROUTE_OWNER=$pid:$ticks
 fi
 return 0
}
