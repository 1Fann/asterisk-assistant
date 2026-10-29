# Asterisk-Assistant-1.2.1

修复清后台后的恢复与后台权限提示；保留原账号配置。

修复中文名称乱码，新增自适应服务器图标。

已确认的故障是系统限制后台运行 / 小米自启动关闭，以及状态检查仅看到旧注册状态。不是单纯检查间隔过长。

首次打开助手时显示“后台运行准备”。点击“检查 / 允许后台运行”并明确确认后，助手仅为自己及受信任的配套网关解除后台限制、加入电池优化白名单，并在可识别的小米系统允许自启动。电话、麦克风、通知及 Shizuku 权限仍需用户自行允许。遇到不支持的系统设置时说明具体失败项，不再统一提示 Root 失败。

自动检查开启时，每约 10 秒轻量检查服务是否退出；完整检查仍按用户配置的 1–1440 分钟执行。授权后台设置后，检查任务可修复被重新施加的后台限制。Asterisk 与网关的恢复仍分属各自助手，共用恢复锁；通话中或无法确认通话状态时不重启，尊重应用内手动停止。清理最近任务无需加锁，但被杀进程恢复期间仍可能暂时无法接听，不承诺零中断。

专用唤醒锁继续由 Asterisk 的原有开关控制。开启时，Root 检查任务持有可续期、到期自动释放的唤醒锁，防止界面被清理后检查立即休眠；关闭时释放。DDNS 的独立守护和唤醒选项保持原状。

The reproduced failure involved Android background restrictions, disabled MIUI autostart, and a readiness check accepting stale registration without a foreground service. Shortening the full-check interval alone was insufficient.

The assistants now show a background-access setup prompt. After explicit confirmation, Root changes are limited to the assistant and its trusted paired gateway: background execution, battery-optimization exemption, and recognized MIUI autostart. Phone, microphone, notification, and Shizuku consent remain separate. Unsupported settings identify the failed step instead of incorrectly reporting missing Root.

When monitoring is enabled, an approximately 10-second lightweight check detects a missing foreground service. Full checks retain the configured 1–1440-minute interval. Consented background settings may be repaired if restrictions return. Server and gateway recovery retain separate ownership, a shared repair lock, active-call guards and manual-OFF behavior. Recovery is not uninterrupted availability.

The existing Asterisk dedicated-wake option now also controls a renewable, bounded root-monitor wake lease. Disabling it releases the lease. DDNS keeps its separate existing daemon and wake option.

## 2026-10-29 background recovery and Chinese UI / 后台恢复与汉化

- Production-signed APKs updated the existing Android 13 / Magisk installation; SIP, dialplan, DDNS and gateway configuration hashes were unchanged.
- Host checks: 26 health-policy cases per assistant; the gateway Gradle unit-test suite passed, including Chinese status/error distinctions and call-count privacy checks. Native audio libraries retain their previously pinned hashes.
- Explicit background setup was exercised in the actual APKs. The ROM rejects the symbolic AUTO_START shell operation; its framework exposes OP_AUTO_START=10008. The fix only uses that vendor operation when the actual MIUI operation appears in the ROM output. Error messages identify the setting instead of blaming Root.
- Screen-off fault injection force-stopped both assistants, the gateway and DDNS UI. Asterisk foreground ownership returned at the 11.1-second sample; complete gateway/Shizuku/audio/SIP readiness returned at 32.6 seconds. No activity was manually launched during recovery.
- A second screen-off run also force-stopped the Shizuku manager UI. All readiness checks passed at 33.3 seconds. Independent IPv6 SIP OPTIONS responses remained available throughout both sampled runs. Timings are measurements on this device, not a service guarantee.
- 用户随后确认：红米息屏且未手动打开软件，iPhone 蜂窝网络 / VPN 关闭时，600 回声、真实呼出双向声音、锁屏来电推送、号码分段和接听双向声音正常。
- No automatic real calls or audio recordings were made. Root and system consent are still required on a new phone; no router changes, account secrets or signing keys are included.

Upgrade in place with the existing production signature. / 使用原发布签名覆盖升级。
