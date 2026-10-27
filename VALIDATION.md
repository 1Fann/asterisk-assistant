# Validation / 验证范围

Tested on one ARM64 MediaTek Redmi, Android17 port, BakaSU. Signed builds installed with prior data retained. Independent configurable monitors passed normal-state, immediate-check, monitor-off and manual-stop checks. With recent-task locks OFF, both helpers and gateway were force-stopped; independent root checks restored the foreground network owner, gateway privileged/audio readiness and server-confirmed SIP registration without keeping helper UI running. An external LAN SIP probe received401. Boot-entry duplicate suppression passed; actual reboot and prolonged deep sleep were not tested. No automated real cellular calls were placed.

The server and gateway monitors were separately paused to verify ownership: the gateway helper did not restart the Asterisk manager, and the server helper did not restart the gateway. Current default interval is5minutes, configurable1–1440. Policy tests cover interval input rejection and unknown/ringing/active-call deferral. Checks do not prove that an iPhone is foregrounded or actual two-way call audio works.

No phone accounts, passwords, device identifiers, logs, signing keys or Cloudflare data are included.
