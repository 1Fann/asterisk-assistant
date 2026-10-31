# Asterisk Assistant 1.2.6

修复长时间息屏后公网 SIP 注册可能一直连接中的问题。实机发现 Wi-Fi 的 IPv6 默认路由过期后，Asterisk 仍在运行，外部注册请求也能到达，但无法向公网回复；解锁手机后网络恢复。

本版本在现有息屏兼容模式中加入路由自动续期。服务运行且公网 IPv6 已启用时，每 30 秒检查 Wi-Fi 默认路由；路由缺失或剩余有效期不超过 120 秒时，向路由器请求 IPv6 路由通告，由系统获取新的路由和有效期。手动停止服务、关闭公网 IPv6 或关闭息屏兼容后，不发送续期请求。

原签名 APK 已在红米 Note 10 Pro / MIUI 14 上覆盖安装。手机连续息屏约 84 分钟，更新后被动观察 32 分钟，自动续期成功、两条公网推送线路注册成功，用户确认 Groundwire 连接成功。本轮验证连接及注册，未拨打实际电话。更新使用原签名，保留已有部署和账号配置；首次安装或换机仍需配置和授权。

Fixes public SIP registration getting stuck after prolonged screen-off operation. On the tested device, the Wi-Fi IPv6 default route expired while Asterisk remained running. Public registration requests arrived, but the server could not reply until network routing recovered.

The existing screen-off compatibility mode now checks the Wi-Fi default route every 30 seconds while the server and public IPv6 mode are enabled. A missing route or a remaining lifetime of at most 120 seconds triggers an IPv6 Router Solicitation. The kernel installs the gateway and lifetime advertised by the router. Manual server stop, disabling public IPv6, or opting out of screen-off compatibility suppresses solicitations.

The production-signed APK was installed on a Redmi Note 10 Pro running MIUI 14. The phone stayed screen-off for approximately 84 minutes, including 32 minutes of passive post-update observation. Automatic renewal succeeded, both public push-service lines registered, and the user confirmed Groundwire connected. This validates connection and registration on the tested device; no real call was placed. The update retains the existing signing identity, deployment and account configuration. First-time installation still requires configuration and authorization. See VALIDATION.md for measurement details.
