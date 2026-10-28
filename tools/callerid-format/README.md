# 来电号码分段 / Incoming number grouping

这是现有 Asterisk 来电路由的可选部署工具，不是 Android APK 的自动安装功能。
修改手机服务配置，无需更新 APK；APK 版本号保持 1.1.1。

This optional tool extends an existing Asterisk incoming route. It updates the
phone's server configuration, not the Android APK or its deployment defaults.

适用范围：已配置 `[vsa-phone-local]`、入口 `2001` 的 Groundwire 优先来电路由。
工具支持从无分段、旧的大陆手机号分段规则升级，也支持重复部署脚本更新。
全新部署的空白 `gateway-test` 不会自动创建真实手机通话路由。

Scope: an existing Groundwire-priority `[vsa-phone-local]` incoming route on
extension `2001`. The installer accepts the unformatted route, the earlier China
mobile-only prefix, or an already installed hook. A fresh echo-only installation
does not gain cellular routes automatically. Other dialplans require an explicit
manual AGI hook; this tool refuses to guess or replace them.

## 部署 / Deployment

可直接下载 [Releases 中的完整部署包](https://github.com/1Fann/asterisk-assistant/releases/tag/callerid-format-v1.0.0)，解压后运行以下命令。部署包已包含经校验的号码库，无需再次下载依赖。

The [complete release bundle](https://github.com/1Fann/asterisk-assistant/releases/tag/callerid-format-v1.0.0) includes the verified number-formatting dependency. Extract it and run the command below; no dependency download is needed.

在项目根目录、手机已通过 ADB 连接且 Shell 已获 Root 的情况下运行：
From the repository root, with an ADB-connected phone and Root granted to Shell:

```powershell
./tools/callerid-format/deploy.ps1 -AdbPath 'C:/Android/platform-tools/adb.exe' -Serial 'YOUR_DEVICE_SERIAL'
```

需要 Python 3；若命令不是 `python`，通过 `-PythonPath` 指定。依赖仅在电脑首次
下载时联网，运行时在红米离线处理号码。不上传手机配置、账号密码或真实来电记录。

Python 3 is required; set `-PythonPath` if needed. The dependency download happens
on the computer; call-time processing stays offline on the phone. No phone
configuration, credentials or real caller logs are uploaded.

规则来源：Android `PhoneNumberUtils` 使用的 Google libphonenumber，借助 Python
移植版 `phonenumberslite` 9.0.42 在本机离线处理。iOS 开源库 libPhoneNumber-iOS
也采用 Google 数据；这里不声称与 Apple 原生电话的私有实现完全一致。

- https://android.googlesource.com/platform/frameworks/base/+/master/telephony/java/android/telephony/PhoneNumberUtils.java
- https://github.com/google/libphonenumber
- https://github.com/daviddrysdale/python-phonenumbers
- https://github.com/iziz/libPhoneNumber-iOS

只设置 `CALLERID(name)`。不改 `CALLERID(num)`、身份头、隐私标志、账号、密码或拨号路由。
数字顺序（包括前导零）必须全部保留，分隔符统一为空格。保留已有文字姓名。
受限号码、短号、星号井号服务串及无法识别的号码不强制分组。

Only the numeric display name is formatted. The dialable identity, privacy flags,
credentials and routing stay intact. Existing textual names are preserved. All
digits, including leading zeros, must survive; punctuation becomes spaces.
Restricted callers, short codes, service strings and unknown formats are left
alone. Parsing is offline, with a two-second execution limit and no caller logs.

`+` 国际号码按国家代码识别；无国际代码时默认中国大陆 `CN`。
国际拨号前缀按默认地区识别（CN 为 `00`），保留原来的前缀。
没有区号或国家代码时不能猜测真正的归属地。

International numbers are selected by country calling code. Numbers without one
use the explicit home region, default `CN`. IDD prefixes follow that region's
metadata. A bare foreign local number cannot identify its country unambiguously.

手机配置：`/usr/local/lib/asterisk-callerid/settings.json`，例如 `{"default_region":"CN"}`。
脚本：`/usr/local/lib/asterisk-callerid/callerid_format.py`。
依赖 wheel 在同目录，保留其 Apache-2.0 许可证和元数据，不安装到全局 Python 环境。

Dependency: `phonenumberslite-9.0.42-py2.py3-none-any.whl`

SHA-256: `7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e`

Stage the verified wheel and `callerid_format.py` in
`/tmp/callerid-format-upload` inside the assistant's chroot, then execute
`install_on_phone.py` there as root. It refuses changes during a call or when an
unexpected route / different previous backup is present. It saves the original private
configuration on the phone, enables the standard `res_agi.so` module persistently,
and its `res_speech.so` dependency, and reloads the dialplan without restarting the
server. This does not configure a speech engine or any cloud service.

For a formatter-only rollback, replace the AGI priority with
`exten => 2001,1,Set(GLOBAL(VSA_LAST_IN_STAGE)=groundwire-check)` and remove the
immediately following identical `same => n,Set(...)` priority, then reload the
dialplan. No account migration or phone reboot is needed.

Run `check_format.py` with the pinned wheel on `PYTHONPATH`, or place the wheel
next to the scripts. Checks use synthetic numbers and all available country
examples, test digit preservation, privacy and AGI behavior, and make no calls.

```text
python tools/callerid-format/download_dependency.py
python tools/callerid-format/check_format.py
```

## 验证 / Verification (2026-10-29)

- 6 local regression groups passed, including examples from all 245 supported
  regions and exact digit preservation.
- 9 isolated Asterisk Local-channel cases passed on the phone: mobile, fixed
  line, service number, international +/00 prefixes, short code, textual name,
  and restricted presentation. Each also checked the original caller number,
  presentation flag and successful AGI execution. No cellular or SIP endpoint
  call was placed by the tests.
- Installed script SHA-256:
  `89b1fab17ee618b952e5460e3515dd0806437cea8121937b8b6f15455866de41`.
- Production incoming hook and persistent module entries verified. The rest of
  the dialplan matches the private pre-upgrade backup. Temporary test contexts
  and upload files removed. A fresh user-observed international call has not
  been tested; examples are synthetic.
