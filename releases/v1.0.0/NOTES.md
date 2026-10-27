# Asterisk 助手 v1.0.0 / Asterisk Assistant v1.0.0

- Android 原生管理界面，一键部署 Asterisk。
- SIP 账号、密码、端口、配置文件与日志管理。
- 启停、开机自启、可选专用唤醒锁及 SIP / RTP 回声自检。
- 支持迁移指定旧部署，校验后删除旧目录、开机脚本和辅助 App。

- Native Android management UI and one-tap Asterisk deployment.
- SIP accounts/passwords, SIP/RTP ports, configuration editor and logs.
- Start/stop/restart, boot startup, optional wake lock and SIP/RTP self-test.
- Migration and verified cleanup of the supported legacy deployment.

Requires an ARM64 phone, Android 12+, Root and KernelSU/BakaSU BusyBox at `/data/adb/ksu/bin/busybox`. Tested on MT6893 Redmi with BakaSU and an Android 17 port. First deployment requires Wi-Fi and downloads Ubuntu Base plus packages; allow at least 1 GB of free space.

需要 ARM64、Android 12+、Root 以及指定路径下的 KernelSU/BakaSU BusyBox。已在 MT6893 红米、BakaSU、移植 Android 17 上验证。首次部署需要联网下载运行环境和软件包，建议预留至少 1 GB 空间。

Fresh install: UDP 16060, RTP 22000–22019, echo 600. Migration preserves existing credentials, dialplan and ports. The supplied APK has the same signing identity as the installed v1.0.0 build. No signing key or phone configuration is published.

新部署默认 SIP UDP 16060、RTP 22000–22019，回声号码 600。迁移保留原账号和端口；APK 沿用已安装版本的签名，仓库不包含签名私钥或手机配置。

Account authentication, RTP echo and LAN/background access were tested. The boot entry was invoked successfully; a full phone reboot and real cellular call were not tested in this release.

已测试账号认证、RTP 回声及局域网后台访问。开机入口已调用验证，本次未做整机重启或真实蜂窝通话测试。
