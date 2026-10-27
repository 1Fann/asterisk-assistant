# Asterisk 助手 / Asterisk Assistant

[English](README.en.md) · [下载 APK](https://github.com/1Fann/asterisk-assistant/releases/latest) · [MIT](LICENSE)

在已 Root 的 ARM64 Android 手机上，一键部署并可视化管理 Asterisk SIP 服务器。当前版本 **1.1.0**。这是社区原创管理 App，使用 Ubuntu 软件源的 Asterisk，未修改服务器核心源码。无需 Termux。

- 一键下载安装经校验的运行环境；启动、停止、重启。
- SIP 账号、密码、连接状态、端口、拨号配置和备份管理。
- 日志、认证与 RTP 回声自检、旧部署迁移清理。
- 开机启动、可选唤醒锁、独立服务器定时检查与异常恢复。

## 检查与恢复

可独立开启、关闭，间隔1–1440分钟（默认5），支持立即检查和上次结果。Root 检查任务独立于界面，清理后台后仍能检查；开机首次解锁后恢复。通话中或无法确认通话状态时跳过恢复，Wi-Fi 未就绪时等待。关闭检查不会停止现有服务。深度休眠可能延后检查；清理至下次检查之间可能短暂不可用。

本助手只恢复服务器进程、前台网络服务、SIP 响应及 Wi-Fi 地址变化。网关与 Shizuku 由 [Voice SIP 助手](https://github.com/1Fann/voice-sip-assistant) 独立管理。手动点击“停止”后，服务器监护不会把它拉起。必要时恢复后台服务可能打开管理页面。两个监护任务共用锁，避免同时修复。

## 使用

1. 安装 APK，允许通知并授予 Root。需要 Android12+、ARM64、约1GB空间，以及 `/data/adb/ksu/bin/busybox`；当前已在 BakaSU/联发科红米上测试。
2. 点击“一键部署 Asterisk”。初始客户端账号1001、网关账号2001，密码由本机随机生成。
3. 从“账号与连接方式”读取本机连接参数。初始 SIP UDP16060、RTP22000–22019，可在界面修改；迁移安装以界面实际值为准。
4. SIP 客户端拨600验证回声。初始安装不会自动添加真实蜂窝呼出路由。
5. 按需开启自动检查并保存间隔。卸载前关闭检查、停止服务器。

Root 数据位于 `/data/adb/asterisk-app`，服务器使用普通 App UID 运行。账号只保存在本机，不上传云端；不修改路由器。

## 自行构建与签名

Windows、JDK21、Android SDK35、Build Tools36.0.0：

```powershell
./build.ps1 -SdkRoot C:/Android/Sdk -JavaHome C:/Java/jdk-21
```

构建脚本在本机 `private/` 生成签名文件。公开发布 APK 使用维护者的既有签名，可覆盖升级已安装版本；CI 使用临时签名，只验证构建。自行签名需要同步修改代码中的证书指纹：Asterisk 的 `RootBridge.CERT`；Voice SIP 助手的 `Root.DUALSIM_CERT`（其自身及配套网关信任指纹）。不同签名不能直接覆盖安装。私钥、密码和手机配置不在仓库中。

## 验证与许可证

见 [VALIDATION.md](VALIDATION.md)、[第三方说明](NOTICE.md)。管理代码 MIT；Asterisk、Ubuntu 保留各自许可证。Release 附件包含本地签名 APK 和 SHA256SUMS，签名私钥不上传 CI。
