# Asterisk Assistant 1.2.9

在「后台运行」中新增两个可分别启停的选项。

- **红米息屏 Wi-Fi 模块**仅适用于 Redmi Note 10 Pro（chopin）、Android 13、Magisk 及其兼容的 Wi-Fi 资源包。点「安装／启用」后自行重启，再打开面板查看是否生效。点「停用」后也需自行重启。它会改变整机的 Wi-Fi 息屏策略，拔电或停用 PBX 后仍然生效，可能增加耗电。助手识别已有的同版模块和等待重启的变更，有冲突时会提示。升级助手不会自动安装这个模块。
- **配套服务备用守护**面向已启用的电话、短信、Bark 与 DDNS 守护。每 10 秒检查一次，在某组件的两层守护都退出时，请求该组件自行恢复。已按相同方式部署的手机可沿用现有守护；关闭该选项会移除这项附加检查和开机入口。详见[后台恢复说明](https://github.com/1Fann/asterisk-assistant/blob/v1.2.9/docs/BACKGROUND-RECOVERY.md)。

修复网络变化引发的自动重启可能遗留“用户已停止”标记的问题。启动、停止和自动恢复共用一把锁，自动恢复检查授权、软件身份、Wi-Fi 与通话状态，并保留恢复期间收到的手动停止意图。

Wi-Fi 失去全部可选全球地址时，现在可以从链路本地地址请求 IPv6 路由通告。助手使用本机内核路由查询核对 PBX 源地址、接口、网关、源前缀和有效期，支持时也使用 PBX 账户的 UID。发送请求后分次核对地址与路由，独立记录发送和恢复。界面区分本机 SIP、等待可确定的公网地址和本机 IPv6 监听状态。iPhone 端公网可达性需从外部网络验证。

APK 沿用原签名，保留现有部署和账号。21 个本地模块状态与操作样例通过，覆盖首次安装、重复启用、等待重启、关闭、错误摘要与同名冲突。红米覆盖安装正式 APK 后，已在应用面板验证「已生效 → 已设置停用 → 已生效」，并重新启用现有备用守护。外部电话、短信端到端效果和整夜自然息屏需按实际设备另行验收。

Two independent options are available under Background.

- **Redmi screen-off Wi-Fi module** supports Redmi Note 10 Pro (chopin), Android 13, Magisk and the compatible Wi-Fi resources package. Select Install/enable, reboot at a convenient time, then reopen the panel to verify activation. Disable also takes effect after a reboot. The setting applies device-wide, including when unplugged or after the PBX stops, and can increase power use. The assistant recognizes this exact module and pending changes, and reports conflicts. Installation is opt-in.
- **Companion monitor fallback** checks already enabled phone, SMS, Bark and DDNS supervisors every ten seconds. If both supervisors of a component have exited, it requests recovery through that component's own entry point. Existing matching deployments can be adopted. Disabling this option stops the extra monitor and removes its boot entry. See [background recovery](https://github.com/1Fann/asterisk-assistant/blob/v1.2.9/docs/BACKGROUND-RECOVERY.md).

Network-driven automatic restarts no longer leave a manual-stop marker. Start, stop and automatic recovery use the same lock. Recovery verifies authorization, package identity, Wi-Fi and idle calls, and preserves any manual stop requested during recovery.

The Wi-Fi worker can solicit an IPv6 router advertisement from link-local when all eligible global addresses have expired. A local kernel lookup checks the PBX source, interface, gateway, source prefix and lease, and uses the PBX UID when supported. Sending and observing a usable route are recorded separately. Local SIP, pending address selection and the local IPv6 SIP listener have separate status. External iPhone reachability requires an outside-network check.

The APK retains the production signing identity, account settings and deployment. Twenty-one local module scenarios passed, covering installation, repeated enable, pending reboot, disabling, digest mismatch and conflicting ownership. The management script also recognized the matching module already active on the tested Redmi. End-to-end phone/SMS service and overnight natural screen-off behavior require separate device acceptance.

On the Redmi, the signed upgrade and its two settings panels were verified on the device. The module panel reported active, pending disable and active again without rebooting during the test. The existing companion fallback remained operational.
