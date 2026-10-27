# Validation / 验证范围

Tested on one ARM64 MediaTek Redmi, Android17 port, BakaSU. Signed builds installed with prior data retained. Independent configurable monitors passed normal-state, immediate-check, monitor-off and manual-stop checks. With recent-task locks OFF, both helpers and gateway were force-stopped; independent root checks restored the foreground network owner, gateway privileged/audio readiness and server-confirmed SIP registration without keeping helper UI running. An external LAN SIP probe received401. Boot-entry duplicate suppression passed; actual reboot and prolonged deep sleep were not tested. No automated real cellular calls were placed.

The server and gateway monitors were separately paused to verify ownership: the gateway helper did not restart the Asterisk manager, and the server helper did not restart the gateway. Current default interval is5minutes, configurable1–1440. Policy tests cover interval input rejection and unknown/ringing/active-call deferral. Checks do not prove that an iPhone is foregrounded or actual two-way call audio works.

No phone accounts, passwords, device identifiers, logs, signing keys or Cloudflare data are included.

## Public IPv6 / DDNS (1.1.1)

After deployment, open Public IPv6 / DDNS, enable it and enter your own hostname. Your existing DDNS service continues to manage its AAAA record; Cloudflare must use DNS-only. Use the hostname without a port as the client domain, `sip:phone.example.com:port` as the UDP proxy, and retain existing credentials.

Managed client endpoints move to a non-temporary global Wi-Fi IPv6 address for signaling and media. Clients need IPv6 in this mode; use the hostname instead of the former IPv4 address. The local gateway remains on IPv4 loopback. Disabling public mode restores LAN client settings. With monitoring enabled, address changes trigger an idle-only restart; loss of IPv6 falls back to LAN until it returns.

The foreground service holds a Wi-Fi multicast reception lock for ROMs that filter IPv6 neighbor discovery while asleep. This consumes additional power and is released when public mode is disabled, the server stops or the process exits. Authentication/RTP echo self-tests support IPv6. No actual cellular calls are automated and router settings are not modified. Allow the configured SIP UDP and RTP ports along the path. The preset uses UDP without SIP TLS or media encryption; management and credentials remain local.

User validation confirmed hostname registration and echo over cellular Internet. Short screen-off cross-device SIP and ICMPv6 checks passed. Prolonged deep sleep, reboot and full dual-SIM public call coverage remain pending.
