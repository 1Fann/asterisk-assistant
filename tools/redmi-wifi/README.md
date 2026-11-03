# 红米 Wi-Fi 资源覆盖 / Redmi Wi-Fi resource overlay

本目录包含内置 Magisk 模块的安装脚本、模块描述和静态 RRO 源码。覆盖仅把 `com.android.wifi.resources` 的 `WifiCustomization` 组中的 `config_wifiSuspendOptimizationsEnabled` 设为 false。RRO 无应用代码、权限或服务。Magisk 在重启后加载或停用它；助手的“红米息屏 Wi-Fi 模块”面板显示运行状态。其他设备继续使用原有通用 Wi-Fi 兼容和路由续期。

The bundled Magisk module is `assets/compat/redmi-wifi-module.zip` (SHA-256 `2e6c42e2c62807ba47ebacd4d0ac700d1f2a7d72cb46bb755a2d3c91fd0d4d80`). Its three entries are the module description, installer script, and signed code-free overlay APK (`a46d25a9f2641e9e3e1e2aa480ea07c55d98a9966b8eba9b18d1b3483c19f5d0`). The XML here defines its package, target, and single resource override. Android build tools can compile and link these resources against SDK 33 or newer; use your own signing credentials for independent builds. The assistant only manages the reviewed payload matching its pins.
