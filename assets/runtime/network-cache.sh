#!/system/bin/sh
# Sourced by control.sh; reuse only the exact previously successful preparation.
network_fingerprint() {
 NC_FILES=$("$BB" sha256sum "$R/etc/asterisk/pjsip.conf" "$R/etc/asterisk-app/lan-ip" "$R/etc/asterisk-app/lan-ipv6" "$R/opt/asterisk-app/api.py" "$BASE/network-cache.sh") || return 1
 if [ -f "$R/etc/asterisk-app/public-ipv6.json" ]; then
  NC_PUBLIC=$("$BB" sha256sum "$R/etc/asterisk-app/public-ipv6.json") || return 1
 else
  NC_PUBLIC=public_ipv6_absent
 fi
 printf '%s\n%s\n' "$NC_FILES" "$NC_PUBLIC" | "$BB" sha256sum | "$BB" awk '{print $1}'
}
prepare_network() {
 NC_BEFORE=$(network_fingerprint) || return 1
 NC_SAVED=$(cat "$BASE/network-prepared.sha256" 2>/dev/null || :)
 if [ -n "$NC_BEFORE" ] && [ "$NC_BEFORE" = "$NC_SAVED" ]; then return 0; fi
 # Invalidate before executing code so a failed update cannot become a cache hit.
 rm -f "$BASE/network-prepared.sha256"
 "$BASE/enter.sh" /usr/bin/python3 /opt/asterisk-app/api.py network >/dev/null || return 1
 NC_AFTER=$(network_fingerprint) || return 1
 [ -n "$NC_AFTER" ] || return 1
 # If preparation or a concurrent editor changed inputs, use the prepared files
 # this time but leave caching to a later unchanged successful preparation.
 [ "$NC_AFTER" = "$NC_BEFORE" ] || return 0
 (umask 077; printf '%s\n' "$NC_AFTER" > "$BASE/network-prepared.sha256.tmp.$$") || return 1
 mv -f "$BASE/network-prepared.sha256.tmp.$$" "$BASE/network-prepared.sha256"
}
