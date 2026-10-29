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

## 2026-10-29 portability release / 新手机部署修复

The APKs package the migration fixes. The original signing identities were compared against APKs pulled from the connected phone before each upgrade; all four updated in place. SIP, DDNS and gateway account configuration hashes were unchanged. The temporary KSU BusyBox alias was removed; Magisk-backed IPv6 selection, both independent monitors and Asterisk authenticated echo self-test (61 returned packets) still passed. The temporary Wi-Fi boot hook was removed by the APK-owned runtime.

电话权限向导在实机完成授权后，网关自行恢复 Shizuku CONNECTED、audioReady、SIP ready。绑定超时重试日志已在实机观察到；未自动批准系统权限。号码库及空姓名修复已由 APK 部署，AGI 四项回归测试和部署八项检查通过。完整网关 JVM 测试通过，包括权限缺失、返回空数据、绑定超时、晚到回调及停止时取消重试。

An APK install is not a silent private-account restore or a cross-ROM audio guarantee. Fresh installation still requires user-approved Root/Shizuku/system permissions and local account setup. No private credentials, signing keys or permission databases are included in this release. The original cellular audio implementation is unchanged.

## Final manual call validation / 最终实际通话验证

2026-10-29: after disabling the iPhone VPN, the user confirmed SIP echo, two-way cellular audio, Groundwire lock-screen incoming push and caller-number grouping. The failed media attempt advertised the VPN address `198.18.0.1` and delivered no client RTP. Packet diagnostics recorded only addresses and counters, not audio. No real cellular calls were initiated automatically.

用户确认关闭 iPhone VPN 后，回声、普通号码双向声音、锁屏推送和号码分段均正常。网关原生音频实现未改动；新手机流程通过隔离配置与现有手机原签名升级验证，没有清空用户手机做出厂重置测试。
