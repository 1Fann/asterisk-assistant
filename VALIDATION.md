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

## 2026-10-29 background recovery and Chinese UI / 后台恢复与汉化

- Production-signed APKs updated the existing Android 13 / Magisk installation; SIP, dialplan, DDNS and gateway configuration hashes were unchanged.
- Host checks: 26 health-policy cases per assistant; the gateway Gradle unit-test suite passed, including Chinese status/error distinctions and call-count privacy checks. Native audio libraries retain their previously pinned hashes.
- Explicit background setup was exercised in the actual APKs. The ROM rejects the symbolic AUTO_START shell operation; its framework exposes OP_AUTO_START=10008. The fix only uses that vendor operation when the actual MIUI operation appears in the ROM output. Error messages identify the setting instead of blaming Root.
- Screen-off fault injection force-stopped both assistants, the gateway and DDNS UI. Asterisk foreground ownership returned at the 11.1-second sample; complete gateway/Shizuku/audio/SIP readiness returned at 32.6 seconds. No activity was manually launched during recovery.
- A second screen-off run also force-stopped the Shizuku manager UI. All readiness checks passed at 33.3 seconds. Independent IPv6 SIP OPTIONS responses remained available throughout both sampled runs. Timings are measurements on this device, not a service guarantee.
- 用户随后确认：红米息屏且未手动打开软件，iPhone 蜂窝网络 / VPN 关闭时，600 回声、真实呼出双向声音、锁屏来电推送、号码分段和接听双向声音正常。
- No automatic real calls or audio recordings were made. Root and system consent are still required on a new phone; no router changes, account secrets or signing keys are included.

## 2026-10-31 — 1.2.2 reliability build

- Built with the existing production signing key; APK signature matched the expected application certificate. No repository push or public release performed.
- 26 host monitor-policy checks passed.
- Four isolated monitor checks passed using Voice SIP Assistant's `tests/check_monitor_runtime.sh`: nonblocking common-lock contention, duplicate-start exclusion, recreation of a killed monitor worker, and shutdown after disabling.
- `tests/check_boot_runtime.sh` passed three isolated cases: manual STOP is retained across boot; enabled/unlocked boot requests service start; disabling autostart cancels first-unlock waiting. Boot, package, network and service commands were mocked in a private temporary test directory; no real server or cellular call was started/stopped.
- Runtime publication is atomic. The BOOT and null-intent sticky-service path now checks the persisted manual-stop flag before starting.
- Real reboot, long screen-off operation and end-to-end iPhone calls remain separate acceptance work. Tests do not establish uninterrupted availability or bypass credential-encrypted storage.

## 2026-10-31 Redmi / MIUI 14 device verification

Installed same-signature updates on one Redmi Note 10 Pro running Android 13, MIUI 14 and Magisk. Existing application data and monitor settings were retained. The device currently has no secure lock-screen credential; no lock-screen setting was changed.

真实息屏测试中，分别结束五项套件的检测工作进程，均自动恢复：Voice SIP 15.3 秒、Asterisk 6.8 秒、Bark 11.2 秒、短信互联 11.1 秒、DDNS 28.6 秒。这里只结束检测工作进程，没有用结束真实通话或发送短信来测试。

整机重启一次，全程没有手动解锁或打开应用；约 67 秒后，所需前台服务和重启后的新检测记录齐备。随后确认网关 SIP 注册、Shizuku 连接、音频就绪、本机短信 HTTPS、Bark ping 及 DDNS 本机健康正常。DDNS 配置和原偏好摘要保持一致。

随后强制进入深度 Doze 75 秒，Voice SIP、Asterisk、短信互联和 Bark 的检测记录均在此期间更新，电话检查状态正常。已退出强制 Doze，恢复正常电源策略。

These are service-readiness tests, not new end-to-end cellular calls, actual SMS delivery, APNs delivery, or an overnight battery-powered suspend test. No automatic real calls or messages were sent. Unattended boot on this device does not establish Direct Boot support before first credential unlock on a password-protected device. Existing wake-lock preferences were preserved; no global battery policy was disabled.

## 2026-10-31 — 1.2.3 speed regression checks

- Same production signing identity retained; local build, APK signature verification and 26 host monitor-policy checks passed.
- The shared `tests/check_fast_monitor_runtime.sh` harness in the Voice assistant repository ran transformed copies under /data/local/tmp/voice-speed-test-20261031, with mocked status/check commands and isolated locks, PID files and wake files. 9 checks passed for this monitor.
- Verified: no per-second dumpsys; first killed worker recreated within the 3-second test threshold; a surviving check retains repair exclusion without retaining the loop lock; supervisor lock does not leak to its child; cached process loss triggers a check within 3 seconds; explicit temporary dependency failure retries within 4.5 seconds; upgrade waits for a live check and then replaces both monitor owners; disabling monitoring stops both owners. Asterisk also covers engine-PID loss with a live service owner.
- These are isolated scheduling/lock checks. Actual gateway/SIP readiness, reboot and screen-off service fault injection are measured separately; no production service or real call was touched by this test harness.

## 2026-10-31 recovery-speed follow-up

The second pass removes fixed first-failure waits, adds inexpensive cached-process checks, and keeps backoff for repeated failures. Full network checks retain their configured cadence. These measurements replace neither the original baseline above nor its stated limitations.

| Component | Checker replacement (s) | Actual local service ready after process kill (s) |
|---|---:|---:|
| voice | 0.3 | 13.16 |
| asterisk | 0.2 | 11.77 |
| sms | 1.9 | 2.69 |
| bark | 1.4 | 1.48 |
| ddns | 2.1 | 1.41 |

Phone readiness required SIP registration plus the gateway’s connected Shizuku and ready audio flags; PBX readiness required the engine and gateway registration. SMS, Bark and DDNS required successful local HTTP(S) responses, with the configured Host header retained for SMS. No real call, SMS or push notification was generated. Measurements include polling overhead and are not upper bounds for network faults or repeated failures.

In the final unattended reboot, Android reported boot completion at 36.8 seconds; all five service checks were simultaneously ready by 69.39 seconds. These timings include the operating-system restart and polling overhead; the initial 67-second baseline above used foreground-service presence and fresh monitor records, so it is not the same measurement.

The unattended reboot phase measurements and final installed artifact hashes are recorded in `D:/CodeX/HELP/reliability-20261031/speed-verification.json`. No unlock input or app-launch request was sent by that test. The device had no secure screen-lock credential before testing; no lock-screen setting was changed.

## 2026-10-31 — 1.2.4 runtime staging cache

- START/BOOT verify the APK signing identity on every request, then reuse a successfully staged package only when its positive package-update timestamp matches and one Root check validates the complete private hash manifest against actual host scripts, the boot hook, the monitor APK digest, and installed rootfs copies. Root ownership and host script execution permissions are checked. The existing awake preference is still synchronized on cache hits.
- The cache is invalidated before staging and recorded only after all deployment work and integrity checks succeed. UPDATE/DEPLOY and other explicit actions retain full staging. Creating rootfs after a host-only deployment invalidates the cache; a damaged installed rootfs is left uncached so the normal DEPLOY repair remains available. Manual-stop, call guards, rootfs launch and networking code were not changed.
- 15 host cache-policy checks and 13 isolated filesystem checks passed, covering a cache hit, changed/unknown package timestamps, malformed manifests, missing ownership marker, wrong owner, missing/corrupt scripts, changed boot hook or APK digest, host-to-rootfs transitions, missing/corrupt rootfs copies and successful validation after repair. The Windows fixture executes the production validation shell; only root ownership reporting and the absent sha256sum utility are supplied by the fixture, using SHA-256 of real temporary file bytes. No phone or production service was touched by these checks.
- Existing 26 monitor-policy checks passed. APK construction and signature verification use the existing signing identity. Actual on-device latency and Android shell utility compatibility are separate acceptance checks; no recovery-time improvement is claimed from host tests.

## 2026-10-31 phone recovery follow-up

The configured Redmi remained plugged in with its existing CPU and high-performance Wi-Fi locks active. Phone process observation now uses a one-second lightweight path; full checks retain their configured real-time intervals.

Three independent gateway process-exit measurements reached foreground + takeover + Shizuku connected + audio-ready + SIP-ready in [2.48, 2.62, 2.53] seconds. Three PBX engine process-exit measurements reached running + gateway registration in [6.0, 5.17, 5.22] seconds. Each fault was preceded by an idle cellular/PBX call check. No real call, SMS or notification was generated.

The final unattended reboot reported all services ready after 67.31 seconds, with no unlock input or activity/service launch by the observer. Measurements and artifact hashes: `D:/CodeX/HELP/reliability-20261031/phone-speed-verification.json`. These are single-device observations with polling overhead, not upper bounds.

After correcting the cold-start pending-request lifetime check, a further gateway process-exit test after reboot reached stable readiness in 2.47 seconds and retained the same idle privileged process. The final installed APK hashes were checked byte-for-byte against the local builds.

## 2026-10-31 — 1.2.5 bounded engine recovery

The new path is restricted to the monitor's observed loss of a cached engine PID. Root checks that the PID remains absent (alive, reused or unknown IDs fail closed), monitoring and prior background authorization remain enabled, the service is not manually stopped, Wi-Fi is present and the manager is already foreground. APK signing and the complete existing runtime manifest are still verified before the final live call guard and repeated authorization/PID checks. It requests the same native launch under a start/stop lock; full background, configuration, IPv4/public-IPv6 SIP validation still follows. It does not restart or modify the gateway. Ordinary startup and uncertain cases retain ManagerService staging.

STOP writes its marker before waiting for launch serialization; recover rechecks it after network preparation and never clears it. BusyBox ash retains FD 9 and uses nonblocking flock -n with at most twenty one-second contention waits; waiting children close FD 9. Neither the unsupported Magisk flock -w nor its timeout helper is used for acquisition: device checking showed that timeout's timer child could retain the lock briefly after its parent exited. All detached native/supervisor/Wi-Fi children close inherited lock descriptors. After native launch, SYNC_RUNTIME only synchronizes the existing manager's CPU/Wi-Fi locks; it never stages, starts/restarts an engine or clears STOP. It rechecks current state after synchronization and releases locks if a manual stop won. The existing three-second startup budget polls process identity instead of sleeping blindly. The network preparation cache hashes full PJSIP configuration, IPv4/IPv6 state, optional public-IPv6 settings, the actual rootfs api.py and cache implementation. It records only an unchanged successful preparation; changed inputs, missing files and failure cannot become a hit.

Offline validation: 26 monitor-policy, 26 staging-policy and 38 restricted-recovery checks passed. Fourteen staged-filesystem integrity checks (including corruption of the new network-cache script), 15 new real-file network-cache cases and 13 isolated production-control cases passed. The control fixture mocks Android/native commands and flock dispatch; it proves branch decisions, stop-during-preparation cancellation and bounded contention retries, not Android lock timing. No device, real server or call was operated by these tests. The one-second monitoring interval and final readiness criteria remain unchanged. Actual recovery latency, Android shell behavior and reboot acceptance require separate device testing; this build alone does not establish the three-second target.

Follow-up diagnosis: the existing public-IPv6 network generator appended separator newlines on every invocation, changing the configuration digest despite unchanged settings and preventing the new cache from being populated. Generated-tail whitespace is now idempotent; eight production-function checks cover repeated preparation, IPv4/IPv6 changes, disabling IPv6, comments, unrelated sections and unchanged ports. The health record adds fixed gate labels, a runtime-validation result and elapsed milliseconds to distinguish a rejected fast path from slow native initialization. It records no IP addresses, accounts, tokens or configuration contents. A failed deployment with old runtime assets was excluded from recovery measurements; APK installation alone is insufficient acceptance without updated asset hashes, foreground ownership and a fresh checker record.

A same-context, read-only device probe then isolated the remaining fast-path rejection to manifest parsing before any shell verification: Android's preferences XML serialization appended four spaces after the manifest's terminal newline. New manifests omit that newline. Loading accepts only terminal whitespace-only lines and CRLF; interior empty lines, padded entries, invalid hashes/paths and duplicates remain invalid. The exact four-space device case is covered by the policy tests, and the complete ownership, execution-permission and actual-file SHA-256 checks are unchanged.

The check and upgrade deadlines now wrap all flock acquisition. Nested Android-query deadlines close inherited lock descriptors, while the actual checker retains both its application and shared repair locks. This addresses the observed Magisk BusyBox timer-child behavior without relaxing exclusion. All four isolated Magisk BusyBox cases in `tests/check_check_lock_runtime.sh` passed on the device for the preceding candidate: immediate release after success or validation failure, exclusion during a live check, upgrade waiting and disabled-upgrade release.

A combined worker/engine fault exposed a separate race in that candidate: the engine died during the replacement worker's initial full check, before the worker sampled its PID, and service readiness took 66.86 seconds. The worker now observes a live engine identity before and after full checks, including its first check, and retains a confirmed death across lock contention. An unobserved or reused PID is not fast-start evidence. Missing-engine retries are bounded, and manual stop, monitoring/authorization settings and the live call guard remain authoritative. During backoff, a newly verified live engine re-arms observation; its next death does not inherit the previous fault's retry budget. A rejected repair lock is distinguished from an attempted recovery, so a confirmed loss can retry when the lock is free. Thirteen deterministic production-loop cases exercise these boundaries with a simulated process table and clock. Root subprocesses also wait on actual exit notification under their original deadline; five host checks cover immediate and later exits, error, timeout and caller interruption. The one-second lightweight process check and final service readiness criteria remain unchanged.

An earlier update handoff held the per-app check lock while waiting for *both* singleton owner locks to become free. A concurrent replacement legitimately held the worker lock, starving business checks for over 90 seconds. Handoff now snapshots exact shell arguments, PID and kernel start ticks, lets an existing check finish, and holds its lock only while signaling the original owners. Replacement observation takes place outside the check lock and accepts an independently started owner. An observed replacement pair is reported as complete; an unconfirmed handoff issues a final idempotent supervisor launch and reports deferred. Two additional isolated device fixture cases cover continued check admission and concurrent replacement during this handoff. Final on-device acceptance is recorded separately.

All six isolated lock and handoff cases passed with the final 1.2.5 runtime on the Redmi Note 10 Pro using its installed Magisk BusyBox.

<!-- recovery-target-20261031:start -->
## 2026-10-31 恢复目标实机复测

红米 Note 10 Pro / MIUI 14，接电、息屏、ADB 连接，沿用现有唤醒设置。每次终止单个进程前均确认蜂窝与 PBX 空闲。

- 守护工作进程（Asterisk PBX）：0.58, 0.64 s（范围 0.58–0.64 s）。
- Asterisk PBX业务进程退出至本地就绪：3.53, 3.58 s（范围 3.53–3.58 s）。整机重启后该项首次观测就绪：54.08 s。

电话单次设备请求补测（独立故障试验，未并入或替代原多次请求样本）：

- Asterisk PBX：首次观测本地就绪 3.26 秒；分别再稳定观测 3.20 秒。

每次采样仅往返设备一次，并行检查网关与 PBX；目标进程身份前后一致，仍要求网关前台、状态应答及五项就绪标志、PBX 进程和命名空间身份、与配置匹配的动态注册记录，并至少持续抽样 3 秒。计时包含实际设备观测开销。

先前候选的实测记录（按管理 APK 的 SHA-256 区分，以下未计入最终版本样本）：

- `8b8c022d5fdc`，Asterisk PBX守护：0.41 s。
- `8b8c022d5fdc`，Asterisk PBX业务：66.86 s。
- `299413aa4f8b`，Asterisk PBX守护：0.64 s。
- `299413aa4f8b`，Asterisk PBX业务：未达到稳定就绪（观察 89.97 s）。

重启各时间均从同一次重启请求起算。全部六项首次齐备 61.97 s，稳定确认 66.12 s；无安全锁屏凭据，观察者未输入解锁、未主动启动界面或服务。强制深度休眠 77.66 s，4 次抽查六项服务与五个工作进程均正常，结束后已解除强制状态。

数值为本机含探测开销的首次观测，不是普适上限。守护与业务分别连续抽样确认至少 1 秒和 3 秒。电话就绪检查含网关状态及匹配的 PBX 注册记录；本次未拨打真实电话、发送短信或通知，也未验证外网送达或双向通话音频。
<!-- recovery-target-20261031:end -->


## 1.2.6 — Screen-off IPv6 default-route renewal / 息屏 IPv6 路由续期

On the test Android 13 / MIUI 14 phone, Asterisk stayed running while the WLAN IPv6 default route expired during prolonged screen-off operation. LAN registration succeeded, but public SIPIS REGISTER requests arrived without SIP replies. A kernel route lookup from the PBX Wi-Fi address returned network unreachable. A single ICMPv6 Router Solicitation restored a router-advertised default with a 1800-second lifetime while the screen remained off.

The APK now bundles a singleton route check under the existing Wi-Fi compatibility option. While the owned server and public IPv6 mode are enabled, it checks the Wi-Fi default route every 30 seconds. A missing route or a remaining lifetime of at most 120 seconds triggers a standards-based solicitation on wlan0. The kernel installs the router-advertised route. A valid permanent route or a longer-lived route needs no solicitation. Manual server stop, public-mode disable and compatibility opt-out suppress requests.

在真实 Android Shell 上，用隔离目录及模拟网络命令验证了路由正常、缺失、120 秒边界、其他接口、多路由器、手动停止、公网停用及兼容模式关闭。原签名 APK 1.2.6 已覆盖安装，运行文件逐字节匹配 APK，Asterisk 进程号和账号／拨号配置校验值保持一致。红米持续息屏期间，实际任务在路由到期前自行请求续期，内核有效期恢复至约 1800 秒，并已观察到公网 SIPIS 注册成功的 200 回复。此轮未自动拨打电话。

2026-11-01 最终确认：手机连续息屏约 84.5 分钟，其中更新后的被动观察持续 32 分钟，抽样未发现 Wi-Fi 默认路由缺失。自动续期成功，两条公网 SIPIS 线路均注册成功；用户随后在保持红米息屏的情况下确认 Groundwire 连接成功。本轮验证连接及注册，未测试实际通话或双向音频。

Final confirmation on 2026-11-01: the phone stayed continuously screen-off for approximately 84.5 minutes. During 32 minutes of passive post-update observation, every sample retained a Wi-Fi default route and an automatic renewal succeeded. Both public SIPIS lines registered successfully, and the user subsequently confirmed Groundwire connected while the Android phone remained screen-off. These are single-device connection and registration observations; no actual call or two-way audio was tested.


## 2026-11-01 reliability follow-up 1.2.7


补齐 IPv6 自动续期任务自身的恢复。Wi-Fi 兼容循环定期补齐续期任务，独立健康守护也会补齐 Wi-Fi 兼容任务。任务仍由单实例锁保护；服务器手动停止或关闭兼容选项后，不主动恢复已停用的任务。

单次路由检查增加 20 秒时限和额外 2 秒强制退出期限，原始套接字增加 3 秒时限，避免一次卡住阻塞以后的续期。原有的路由有效期判断、账号配置和签名身份保留。

本地隔离测试覆盖任务丢失后的重新拉起、检查超时后的后续检查；这些测试模拟 Android 命令和时钟，不代表实机时延保证。实机故障注入和长时间息屏复测须在部署后单独记录。

Adds recovery for the IPv6 renewal worker itself. The Wi-Fi compatibility loop periodically ensures that the singleton renewal worker exists, and the independent health monitor also restores missing Wi-Fi compatibility workers. Manual stop and compatibility opt-out remain authoritative.

Each route check has a 20-second deadline with a further 2-second kill grace. The raw socket has a 3-second timeout, preventing a stuck attempt from blocking later renewal cycles. Existing route decisions, account configuration and production signing identity are retained.

Local isolated regressions cover a lost renewal worker and repeated check deadlines. They mock Android commands and scheduling; actual device recovery latency and prolonged screen-off acceptance require separate deployment testing.


1.2.7 follow-up: one-second route-worker identity polling and exact Wi-Fi-only upgrade handoff are covered by `tests/check_wifi_identity.py`. Cached live ticks issue no argv subprocesses. PID reuse and unrelated sleeps are excluded. Existing process-observation regressions remain applicable. Device timing must be measured after the old loops have handed off to the new APK.

### 2026-11-01 最终 APK 续期任务退出实机验收 / Renewal-worker device acceptance

最终 1.2.7 APK 的 SHA-256 为 `c9f744453f2dd87bfc296630699d66a4a31c67f38cc3c985ac54e79a90ababc0`。安装后，四个 Wi-Fi 运行脚本已与 APK 核对一致，新续期任务记录包含 PID 与进程启动时间。对已经运行新版代码的续期任务分别执行三次受控 KILL，首次观测到替代任务恢复的时间为 **0.625、1.250、1.157 秒**；三次均通过后续稳定确认，Asterisk PBX 进程号均未变化。

这是单台设备、包含实际观察开销的三次任务恢复测量，不是恢复时间上限，也不代表全部故障均可在一秒内恢复。本项仅验证续期任务退出后的重新拉起与稳定存活，不替代实际路由续期、真实通话、主业务恢复或整机重启验收。升级前旧循环及其 sleep 子进程的观测不计入上述新版样本。

The final 1.2.7 APK has SHA-256 `c9f744453f2dd87bfc296630699d66a4a31c67f38cc3c985ac54e79a90ababc0`. After installation, all four Wi-Fi runtime scripts matched the APK, and the new renewal-worker record contained its PID and process start ticks. Three controlled KILL trials against workers already running the new code first observed replacement workers after **0.625, 1.250 and 1.157 seconds**. Every replacement passed subsequent stability observation, and the Asterisk PBX PID remained unchanged.

These are three single-device measurements including observation overhead, not upper bounds or a one-second guarantee for every failure. This acceptance covers replacement and stable survival of the renewal worker. It does not substitute for route-renewal, real-call, business-process recovery or whole-device reboot tests. Observations of pre-update loops and their sleep children are excluded from these new-runtime samples.

### 2026-11-01 最终 APK 业务退出及整机重启验收 / Business-process and reboot acceptance

最终 1.2.7 部署后，单次受控终止 PBX 业务进程，首次观测本地就绪为 **2.97 秒**，随后连续稳定确认至少 3 秒。同轮电话网关业务进程退出测试为 2.59 秒，并单独通过至少 3 秒稳定确认。这里的就绪检查包含网关状态应答和本地就绪标志、PBX 运行状态及匹配的网关注册记录。

随后进行一次整机重启，所有时间均从发出重启请求起算，包含系统启动：系统启动完成 **37.53 秒**，用户自动解锁 **37.84 秒**，PBX 网关注册 **54.66 秒**，电话网关完整本地就绪 **62.00 秒**，全套服务首次齐备 **62.06 秒**，在 **66.08 秒**完成持续 4.02 秒的稳定确认。观察者没有输入解锁指令，也没有主动启动 Activity 或服务；该红米设备 `deviceSecure=false`，因此这不是设置安全锁屏密码后首次解锁之前的恢复验证。

以上为单台设备各一次故障／重启实测，时间是包含查询延迟的首次成功观测，不是固定上限或通用保证。仅核验本地接口及状态，不证明公网可达、实际呼叫接通或双向通话音频。重启记录：调查工作区 `reliability-20261031/private/full-retest-20261101-084900/reboot.json`。

After deploying the final 1.2.7 APK, one controlled PBX business-process kill first reached local readiness in **2.97 seconds**, followed by at least three seconds of stable observation. The separate gateway business-process trial reached readiness in 2.59 seconds and likewise passed at least three seconds of stability observation. Readiness includes the gateway status acknowledgement and local ready flags, the running PBX and a matching gateway registration.

One subsequent whole-device reboot measured every stage from the reboot request, including operating-system startup: boot completed at **37.53 seconds**, the user unlocked automatically at **37.84 seconds**, the PBX gateway registered at **54.66 seconds**, full local gateway readiness appeared at **62.00 seconds**, and all services were first ready at **62.06 seconds**. Stability was confirmed at **66.08 seconds**, after 4.02 seconds of continuous readiness. The observer issued no unlock, Activity-start or service-start commands. The Redmi device reported `deviceSecure=false`; this does not validate recovery before the first credential unlock on a securely locked device.

These are one trial per fault/reboot on one device. Times are first successful observations including query latency, not fixed upper bounds or general guarantees. Checks cover local interfaces and state, not public-network reachability, a completed real call or two-way call audio. Reboot evidence is in the investigation workspace at `reliability-20261031/private/full-retest-20261101-084900/reboot.json`.

## 2026-11-04 1.2.8 自动重启与 IPv6 路由核验 / Restart and route validation

1.2.8（versionCode 17）正式 APK 为 497989 字节，SHA-256 为 `ffaeccad04b930ddc734c2b3f464e106eecfd54b2aeb67c9f35cf05e7d0bd95b`。使用 Android 构建工具确认签名与 1.2.7 一致。APK 内 24 个运行文件（含二进制号码库）均与本地源码原始字节一致。

- 27 个隔离控制脚本场景通过，包括自动重启失败、并发手动停用、正在通话／通话状态未知，以及恢复途中撤销授权。26 项通话和恢复策略检查、13 个进程观察场景、8 项网络配置检查通过。
- 15 项路由选择测试覆盖源地址、正确的接口和下一跳、更专用前缀、优先级及 120 秒有效期边界。12 个脚本场景运行真实的地址选择器、路由管理脚本和 Python 判定逻辑，模拟 Android 网络、服务和时钟。测试区分了只剩链路本地地址、多个稳定地址、错误接口／源前缀、请求后恢复、通告未生效和手动停用。原有工作进程时限、身份与旧版本交接测试通过。
- 诊断文件位于手机的 `/data/adb/asterisk-app/`。`wifi-route.status` 记录最近的本地路由判断。`wifi-route.last-rs` 是最近成功发出请求的时间，`wifi-route.last-verified-rs` 是请求后的有界复查实际观察到可用内核路由的时间。稍后才恢复的路由可在下一轮显示为 `local-route-ready`。这些文件不能证明观察到的路由一定由本次请求产生，也不证明公网或 iPhone 可达。
- 若原 PBX 地址已失效，存在多个合格稳定地址时报告 `ambiguous-source`，保留现有“只有一个候选才改选”规则。使用独立 DDNS 的设备仍需核对其地址选择与 PBX 实际监听地址。此处的实测是本地隔离测试；1.2.8 的真机长期自然息屏、重启和外部连接应另行记录。

The 1.2.8 release APK (versionCode 17) is 497989 bytes with SHA-256 `ffaeccad04b930ddc734c2b3f464e106eecfd54b2aeb67c9f35cf05e7d0bd95b`. Android build tools verified the same signer as 1.2.7. All 24 packaged runtime files, including the binary number-formatting dependency, matched the local source bytes.

- 27 isolated control-script scenarios passed, covering failed automatic restart, concurrent manual stop, active/unknown calls and revoked authorization. The 26 call/recovery policy checks, 13 process-observation scenarios and eight network-configuration checks also passed.
- Fifteen route-policy checks cover the source, actual interface and next hop, more-specific prefixes, route metrics and the 120-second lease boundary. Twelve shell scenarios run the production selector, worker and Python decision code against simulated Android network responses, service state and timing. They distinguish a link-local-only interface, ambiguous addresses, wrong interface/source prefix, recovery after solicitation, unconfirmed sends and manual stop. Existing worker timeout, identity and upgrade-handoff checks passed.
- In the device's `/data/adb/asterisk-app/`, `wifi-route.status` holds the most recent local route assessment. `wifi-route.last-rs` timestamps a successful send. `wifi-route.last-verified-rs` timestamps an acceptable kernel route inspected in the bounded post-send window. Later recovery may be reported by the next regular check. These observations establish neither causation by that solicitation nor public/iPhone reachability.
- If the old PBX address expired and multiple stable candidates remain, `ambiguous-source` preserves the existing selection policy. Sites using a separate DDNS selector should compare its choice with the PBX listener. These are local isolated measurements. Long natural screen-off periods, device reboots and external access on 1.2.8 require separate device acceptance.

## 2026-11-04 1.2.9 内置模块与备用守护 / Bundled module and companion fallback

正式 APK 1.2.9（code 18）共 514698 字节，SHA-256 为 `4ee4be3cb432f587177337fe566c84aa0c87c44a11cbee0c127bdc2a26fefa1a`。Android 构建工具验证签名与上一公开版本相同。包内 26 个运行文件及两个模块资产逐字节匹配源文件；发布输入已通过解码及校验。1.2.8 是本地候选，前节记录的控制和路由修复沿用至此版本。

21 个隔离模块管理场景使用正式控制脚本和临时目录中的模拟 Android / Magisk，验证型号、SDK、目标资源、包摘要、安装失败、待重启、重复启用、启停一致性、资源未生效以及同名文件冲突。无关模块的标记始终保留。在红米的独立检查中，当前脚本识别已安装同版覆盖和 Wi-Fi 框架生效状态；已部署备用守护连续两次启用仍使用相同 PID。红米已覆盖安装 1.2.9 正式 APK，核对安装字节与签名后，从应用面板完成「已生效 → 已设置停用 → 已生效」及备用守护重复启用检查。此版本尚未另行进行整夜息屏或真实通话测试。[备用守护验收](docs/BACKGROUND-RECOVERY.md)

The production 1.2.9 APK (code 18) is 514698 bytes, SHA-256 `4ee4be3cb432f587177337fe566c84aa0c87c44a11cbee0c127bdc2a26fefa1a`. Android build tools verified the same signer as the previous public version. The 26 runtime files and two compatibility assets matched their source bytes. Release input decoding and verification passed. The preceding section covers the local 1.2.8 candidate whose control and route fixes are included here.

Twenty-one isolated module-management scenarios exercised the production controller using temporary directories and simulated Android/Magisk responses. They cover device and SDK gates, resources, payload hashes, install failure, pending reboot, repeated enable, consistent markers, ineffective resources and identity conflicts. Another module's marker remained intact. An independent Redmi check identified the matching installed overlay and effective Wi-Fi framework state. Repeated enable of the existing fallback preserved its PID. The complete signed APK was installed on the Redmi and its hash verified. The app UI transitioned active → pending disable → active and enabled the existing fallback. This build has not had a separate overnight or actual call trial. [Companion fallback validation](docs/BACKGROUND-RECOVERY.md)
