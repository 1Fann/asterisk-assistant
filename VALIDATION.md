# 本机验证 / Local validation

2026-10-27，ARM64 Redmi / Android 17 / BakaSU。

- 签名 APK 编译、签名验证、手机安装通过。
- 实际从 App 点击一键部署，下载并校验官方 Ubuntu Base，完成 Asterisk 软件包安装和启动。
- 独立端口部署测试通过，随后迁移原账号和配置。
- 原 SIP 密码映射、拨号规则及 RTP 配置比较一致；没有输出密码。
- 两个既有账号认证通过，RTP 回声测试收到 61 个匹配包。
- Windows 通过 Wi-Fi 收到正确的 SIP 认证挑战；App 返回桌面、前台服务保持运行时再次通过。
- 账号列表、端口设置界面读取正常。
- 后端测试覆盖重复节名解析、修改密码、保留原拨号配置、账号增删、Wi-Fi 地址更新、文件路径和端口校验。
- Asterisk 使用本 App 的普通 Android UID，CapEff=0，NoNewPrivs=1。
- 开机脚本已实际调用并成功启动 App 前台服务；本次没有重启手机验证完整开机过程。
- 旧服务器目录、旧开机脚本和旧网络辅助 App 已删除。DDNS 和 GSM2SIP 保留。

APK SHA-256:

`6f25a857596f2ae0297ff203548f0ba5954ff557afc880191d4dca04acd85d1a`

No real cellular call was placed. Existing cellular routing was not changed. This validation concerns installation, migration, SIP authentication, LAN access and RTP echo.
