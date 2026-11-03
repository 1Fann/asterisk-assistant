# 配套服务备用守护 / Companion monitor fallback

在 Asterisk 助手的「后台运行 → 配套服务备用守护」中点「启用 / 修复」。此功能需要 Magisk 和已授权的 Root。启动脚本和守护程序都来自本次安装的 Asterisk APK。已经按相同方式部署过的手机可以沿用原有守护，无需再次配置各个助手。

备用守护每 10 秒检查已经启用的电话、短信、Bark 和 DDNS 守护。如果某一组件的两层守护都退出了，就调用该组件自己的启动入口。失败后的再次尝试至少间隔 60 秒。原有组件负责判断签名、用户开关和当前通话状态。启用此功能时也会定期检查已启用的 DDNS 管理应用是否被系统限制后台运行。

点「关闭备用守护」会停止这个附加检查并移除它的开机入口。各个应用的监护仍由各自的开关控制。在之前的红米实测中，DDNS 的两层守护同时退出后约 10.92 秒恢复，原 DDNS 引擎保持运行。这是单次测量。

## English

Open the Asterisk assistant's background settings, select **配套服务备用守护** (companion monitor fallback), then **启用 / 修复** (enable or repair). This requires Magisk and root access. The installed APK supplies both the monitor and its boot entry. The setup recognizes an existing compatible installation and retains the companion applications' settings.

Every ten seconds it checks the supervisors of already enabled phone, SMS, Bark and DDNS services. If both supervisors for one component are absent, it requests recovery through that component's own startup entry. Subsequent attempts are spaced by at least sixty seconds. The respective component retains responsibility for package checks, manual stops and active calls. While enabled, the fallback periodically checks for a background restriction on the active DDNS management app.

**关闭备用守护** (disable fallback) stops the additional checks and removes their boot entry. In one Redmi test the two DDNS supervisors recovered in 10.92 seconds and the existing DDNS engine continued running.
