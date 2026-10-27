# Asterisk 助手

[English](README.en.md) · [下载 APK](https://github.com/1Fann/asterisk-assistant/releases/latest) · [MIT 许可证](LICENSE)

在已 Root 的 ARM64 Android 手机上，一键部署并可视化管理 Asterisk SIP 服务器。原生 Android 界面，无需 Termux。

## 功能

- 一键下载并校验 Ubuntu ARM64 运行环境，安装 Asterisk。
- 启动、停止、重启，查看运行状态和通话数。
- 添加、删除 SIP 账号，修改密码，查看客户端连接信息。
- 修改 SIP / RTP 端口，编辑拨号规则与配置文件，恢复上次保存前的备份。
- 查看运行日志，执行账号认证和 RTP 回声自检。
- 开机自启，以及可选的专用唤醒锁。
- 迁移受支持的旧部署，校验成功后清理旧目录、开机脚本和旧辅助 App。

## 使用要求

- ARM64 手机，Android 12 或更高版本，主用户（用户 0）。
- Root，并具备 `/data/adb/ksu/bin/busybox`；当前适配 KernelSU / BakaSU 环境，其他 Root 方案未验证。
- 首次部署需要 Wi-Fi 联网下载 Ubuntu Base 和软件包，建议至少预留 1 GB 空间。
- 已在 MT6893 红米、BakaSU、移植 Android 17 上验证；其他设备尚未实测。

## 快速开始

1. 从 [Releases](https://github.com/1Fann/asterisk-assistant/releases/latest) 下载并安装 APK。
2. 允许通知，在 Root 管理器中为“Asterisk 助手”授权。
3. 点击“一键部署 Asterisk”，等待下载安装完成。
4. 打开“SIP 账号与连接方式”，查看本机随机生成的账号密码和连接参数。
5. SIP 客户端使用 UDP；客户端账号默认 `1001`，手机网关账号默认 `2001`，回声测试号码为 `600`。

新部署默认端口：Wi-Fi SIP UDP `16060`，本机 SIP UDP `16060`，RTP `22000–22019`。以 App 显示为准，均可在界面中修改。

使用 Linphone 时，“SIP 域名”填手机 Wi-Fi IP，“SIP 代理”填 `sip:手机IP:端口`，认证 ID 与用户名一致。先在同一 Wi-Fi 下拨 `600` 验证回声。

初始配置用于局域网回声测试，不自动创建真实蜂窝通话路由，也不修改路由器设置。

## 迁移旧部署

针对旧的 `/data/adb/sip-pbx` 部署：先部署新运行环境，再点击“迁移现有账号与配置”。App 保留原 SIP 账号、密码、拨号规则和端口，迁移期间会短暂重启服务。

迁移后完成自检并确认客户端连接正常，再点击“清理旧部署”。清理范围为旧服务器目录、`98-sip-pbx.sh` 开机脚本和 `local.sip.pbx.network` 辅助 App。其他应用不在清理范围内。

## 后台与数据

- 运行目录：`/data/adb/asterisk-app`。
- 开机入口：`/data/adb/service.d/97-asterisk-app.sh`；等待系统完成启动、主用户首次解锁及 Wi-Fi 就绪。
- Root 用于部署和管理；Asterisk 进程使用本 App 的普通 Android UID，清空附加组与 Linux capabilities，并启用 no-new-privileges。
- 前台服务维护该 UID 的后台网络状态，运行环境挂载位于私有命名空间。
- 账号配置保存在手机 Root 私有目录，不上传云端，密码不输出到日志；管理窗口禁止截图。
- 请允许 App 的通知和后台运行。专用唤醒锁默认关闭，开启后会增加耗电。

更多安全说明见 [SECURITY.md](SECURITY.md)。卸载 App 不会自动删除运行目录，卸载前请先停止服务器。

## 构建

需要 Windows、PowerShell、JDK 21、Android SDK Platform 35 和 Build Tools 36.0.0，无需 Gradle。

```powershell
./build.ps1 -SdkRoot 'C:\Android\Sdk' -JavaHome 'C:\Java\jdk-21'
```

也可设置 `ANDROID_HOME` 和 `JAVA_HOME` 后运行 `./build.ps1`。APK 输出到 `out/`，首次构建会在 `private/` 生成本地签名密钥。请保留该密钥以便后续覆盖升级，切勿提交或公开它。

仓库的 `releases/` 保存已签名 APK 的 Base64 发布输入及 SHA-256；Actions 在源码检查和 Android 构建通过后，将其还原、校验并上传到 Releases。正式签名私钥始终留在本地，CI 构建使用临时密钥。

后端检查：`python3 check-backend.py assets/runtime`。发布校验：`python3 tools/verify_release.py`。设备验证记录见 [VALIDATION.md](VALIDATION.md)。

## 上游与许可证

原创管理代码采用 [MIT 许可证](LICENSE)。Ubuntu Base 24.04.5 ARM64 下载使用固定 SHA-256 校验，Asterisk 从 Ubuntu noble 签名软件源安装，具体软件包修订版本随软件源更新。

Asterisk 和 Ubuntu 组件保留各自许可证，运行环境不包含在 APK 内。详见 [NOTICE.md](NOTICE.md)。本项目并非 Asterisk 或 Canonical 官方 App。
