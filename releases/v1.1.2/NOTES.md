## Asterisk 助手 1.1.2

- 来电号码分段正式内置 APK，包括经过固定 SHA-256 校验的完整号码库，无需电脑、ADB 或额外部署 ZIP。
- 默认开启；首次部署自动准备，覆盖升级后打开 App 并授予 Root，空闲时自动接管现有配置。
- 首页新增“来电号码分段”：可以开关功能，选择无国家区号时使用的默认地区（默认 CN）。
- 245 个国家／地区的号码数据，支持手机、固话、400／800 及国际号码；仅调整数字显示名称，保留真实号码、隐私和文字姓名。短号和无法识别的号码保留原样。
- 通话中或状态未知时推迟配置，空闲后自动重试；已有独立脚本原位接管，避免重复处理。
- 使用原签名覆盖升级，保留账号、密码、网络和拨号配置。新部署仍需要 Root，并仍是回声测试环境，不会自动创建蜂窝通话路由。

### 使用

安装 APK → 打开并授予 Root → 已部署的设备会自动准备；新设备先点“一键部署 Asterisk”。以后在首页“来电号码分段”调整开关和地区即可。无需下载之前的独立工具包。

## Asterisk Assistant 1.1.2

- Caller number formatting and the complete SHA-256-pinned metadata wheel are now bundled in the APK. No computer, ADB or separate deployment ZIP is needed.
- Enabled by default. New deployment prepares it automatically; upgrades take over existing settings when the app opens with Root and the server is idle.
- A new home-screen entry toggles the feature and selects the default region for numbers without country codes (CN by default).
- Metadata covers 245 regions. Only numeric display names are formatted; caller numbers, privacy and textual names are preserved. Short codes and unknown formats stay unchanged.
- Calls and unknown call state defer configuration until idle. Existing standalone hooks are taken over in place.
- The original signing identity is retained. Existing credentials, network and dialplan logic are preserved. Root is still required, and fresh deployment remains echo-only without automatic cellular routes.

Install the APK, open it and grant Root. Existing deployments are prepared automatically; new users first deploy Asterisk. Configure the switch and home region in the app. The old standalone tools are no longer required.
