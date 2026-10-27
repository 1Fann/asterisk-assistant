# Security / 安全说明

The App requires a trusted Root grant to manage its runtime. Asterisk itself runs under the App's normal Android UID with no Linux capabilities and no-new-privileges. Keep that Root grant limited to builds you trust.

App 需要 Root 来管理运行环境。Asterisk 进程本身使用 App 的普通 Android UID，清空 Linux capabilities 并启用 no-new-privileges。

Passwords are generated locally and kept in the device's Root-private configuration. Do not attach `pjsip.conf`, the runtime directory, signing keys or credentials to public issues. Logs filter common authentication markers, but review diagnostic material before sharing it.

密码在本机生成并保存在手机 Root 私有目录。请勿在公开 Issue 上传 `pjsip.conf`、运行目录、签名私钥或账号密码。分享诊断信息前应检查其中内容。

The initial setup is a Wi-Fi LAN echo test. It does not enable public Internet access or cellular dialing. Validate any changes to SIP exposure and dialplan before use.

初始配置用于 Wi-Fi 局域网回声测试，不自动开通公网访问或蜂窝拨号。
