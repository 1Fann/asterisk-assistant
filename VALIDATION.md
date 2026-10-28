# Validation / 验证范围

Tested on one ARM64 MediaTek Redmi, Android17 port, BakaSU. Signed builds installed with prior data retained. Independent configurable monitors passed normal-state, immediate-check, monitor-off and manual-stop checks. With recent-task locks OFF, both helpers and gateway were force-stopped; independent root checks restored the foreground network owner, gateway privileged/audio readiness and server-confirmed SIP registration without keeping helper UI running. An external LAN SIP probe received401. Boot-entry duplicate suppression passed; actual reboot and prolonged deep sleep were not tested. No automated real cellular calls were placed.

The server and gateway monitors were separately paused to verify ownership: the gateway helper did not restart the Asterisk manager, and the server helper did not restart the gateway. Current default interval is5minutes, configurable1–1440. Policy tests cover interval input rejection and unknown/ringing/active-call deferral. Checks do not prove that an iPhone is foregrounded or actual two-way call audio works.

No phone accounts, passwords, device identifiers, logs, signing keys or Cloudflare data are included.

## Optional incoming number grouping (2026-10-29)

The existing phone's server-side formatter passed six local regression groups,
including examples across all 245 supported regions and exact digit preservation.
Nine isolated Asterisk Local-channel cases passed on the phone, checking mobile,
fixed-line, service, international +/00, short-code, textual-name and restricted
caller handling. They also checked unchanged caller numbers and presentation
flags, plus successful AGI execution. No real SIP endpoint or cellular calls were
placed by these tests. Temporary test contexts were removed; the rest of the
incoming dialplan was verified unchanged. The user confirmed spaced display with
the previous China mobile-only rule. New international live incoming calls have
not been user-tested, and exact iOS native formatting is not claimed.

六组本地回归检查及手机端九项隔离验证通过。用户已确认旧大陆手机号规则能显示
空格；新版国际号码的真实来电尚未实测。仅发布可选服务端脚本、部署工具和文档，
APK 保持 1.1.1，未声称 APK 自动包含或启用这项扩展。

## Public IPv6 / DDNS (1.1.1)

After deployment, open Public IPv6 / DDNS, enable it and enter your own hostname. Your existing DDNS service continues to manage its AAAA record; Cloudflare must use DNS-only. Use the hostname without a port as the client domain, `sip:phone.example.com:port` as the UDP proxy, and retain existing credentials.

Managed client endpoints move to a non-temporary global Wi-Fi IPv6 address for signaling and media. Clients need IPv6 in this mode; use the hostname instead of the former IPv4 address. The local gateway remains on IPv4 loopback. Disabling public mode restores LAN client settings. With monitoring enabled, address changes trigger an idle-only restart; loss of IPv6 falls back to LAN until it returns.

The foreground service holds a Wi-Fi multicast reception lock for ROMs that filter IPv6 neighbor discovery while asleep. This consumes additional power and is released when public mode is disabled, the server stops or the process exits. Authentication/RTP echo self-tests support IPv6. No actual cellular calls are automated and router settings are not modified. Allow the configured SIP UDP and RTP ports along the path. The preset uses UDP without SIP TLS or media encryption; management and credentials remain local.

User validation confirmed hostname registration and echo over cellular Internet. Short screen-off cross-device SIP and ICMPv6 checks passed. Prolonged deep sleep, reboot and full dual-SIM public call coverage remain pending.

## Built-in APK integration 1.1.2 (2026-10-29)

Seven isolated runtime integration groups passed: fresh enabled defaults,
credential/client/dialplan preservation, idempotent setup, switch/default-region
settings, busy/unknown-call deferral, legacy hook takeover, migration deferral,
invalid configuration and dependency corruption handling. The six number-format
regression groups continue to pass across 245 metadata regions.

The production-signed 1.1.2 APK was installed over 1.1.1 on the phone. Opening the
app staged the bundled scripts and wheel and created enabled/CN configuration
automatically. Private credential fingerprints and existing pjsip.conf,
extensions.conf and rtp.conf fingerprints matched before/after upgrade. Gateway
registration remained present. Actual AGI execution verified disabling formatting,
changing the default region to US, then restoring enabled/CN. All nine isolated
Asterisk cases passed with the new APK's installed formatter; no cellular calls
were initiated. New-install bootstrap is tested in fixtures rather than by
clearing the user's working deployment. The device's lock screen prevented a
visual walkthrough; the home entry is compiled and the app/API is verified.

1.1.2 原签名覆盖升级、App 自动接管、账号及原拨号配置保留、开关与默认地区设置
和九项手机端隔离验证均通过。新安装流程使用隔离配置验证，没有清空用户现有部署。
未自动拨打真实电话；此次尚未重新实测完整手机通话，也未完成锁屏后的界面逐项点验。
