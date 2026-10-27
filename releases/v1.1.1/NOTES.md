# Asterisk Assistant 1.1.1

## 中文

新增可视化公网 IPv6 / DDNS 设置。保留账号、密码和本机网关，支持非临时 Wi-Fi IPv6 监听、媒体地址及地址变化恢复。加入 Wi-Fi 组播接收锁，以兼容部分 ROM 的息屏 IPv6 寻址；开启公网模式后增加耗电，关闭或停止服务后释放。自检与监护增加 IPv6 响应验证。

下载 Asterisk-Assistant-1.1.1.apk，可覆盖升级相同签名的旧版。源码和 SHA256SUMS 一并提供；不含手机账号、Token 或签名私钥。公网模式需要客户端及沿途网络支持 IPv6。当前 UDP 预设未配置 TLS/SRTP，验证范围见 README。

## English

Visual public IPv6/DDNS configuration, stable Wi-Fi IPv6 signaling/media, idle address-change recovery, and IPv6 authentication/RTP echo and health checks. Credentials and loopback gateway settings are preserved. An opt-in-public-mode multicast reception lock handles screen-off IPv6 discovery on affected ROMs; it increases power use and is released on stop/disable.

The production-signed APK updates matching-signature installations. Source and checksums are attached. No device credentials, API tokens or signing keys. IPv6 reachability is required end to end; the UDP preset does not configure TLS/SRTP. See README for validation limits.
