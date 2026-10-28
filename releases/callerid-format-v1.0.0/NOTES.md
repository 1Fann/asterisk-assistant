## 来电号码分段扩展 1.0.0

将之前仅支持大陆手机号的来电显示分段扩展到 Google libphonenumber 245 个国家／地区的号码数据，包括固话、400／800、港澳台及国际号码。仅格式化数字形式的显示名称，真实主叫号码、回拨号码、隐私标志和文字姓名保持不变。

### 下载哪个文件

- **Asterisk-CallerID-Format-1.0.0.zip**：本次新增功能的部署包，包含格式化脚本、Windows ADB 部署工具、中英文说明和已校验的完整号码库依赖。解压后按 `tools/callerid-format/README.md` 操作。需要电脑 Python 3、ADB 及手机 Shell Root，适用于已经配置的 Groundwire 优先来电路由。
- **Asterisk-Assistant-1.1.1.apk**：沿用原签名的管理 App，内容和之前的 1.1.1 完全一致。安装 APK 不会自动启用号码分段扩展；已经安装 1.1.1 的用户无需重装。
- **asterisk-assistant-callerid-format-1.0.0-source.zip**：本次发布对应的完整仓库源码，不含手机私人配置或签名密钥。
- **SHA256SUMS**：以上三个附件的校验值。

号码库随部署包提供，解压后的脚本部署不需要再次下载依赖。手机运行时离线处理。无国家区号时默认中国大陆；短号、服务串和无法识别的号码保持原样。不承诺与 iPhone 原生电话的排版完全一致。全新回声测试环境不会自动创建蜂窝通话路由。

六组回归检查、245 个地区的号码样例检查和手机端九项隔离验证通过。国际号码真实来电尚未逐一实测；内部测试不会拨打真实蜂窝电话。

## Incoming number formatting extension 1.0.0

This release adds offline numeric caller display-name grouping using Google
libphonenumber metadata for 245 regions. It covers mobile, fixed-line, service
and international formats while preserving caller numbers, privacy and names.

- **Asterisk-CallerID-Format-1.0.0.zip** is the new deployment bundle, including
  bilingual instructions, the Windows ADB deployment tool and the complete
  SHA-256-verified formatting dependency. Extract and follow
  `tools/callerid-format/README.md`. Computer Python 3, ADB and phone Shell Root
  are required. An existing Groundwire-priority incoming route is required.
- **Asterisk-Assistant-1.1.1.apk** is the unchanged, originally signed manager.
  Installing it does not enable the extension. Existing users need not reinstall.
- **asterisk-assistant-callerid-format-1.0.0-source.zip** contains the source for
  this release, without private device configuration or signing material.
- **SHA256SUMS** covers all three files above.

The tools bundle includes its dependency, so deployment does not download it
again. Call-time processing stays offline. Bare numbers default to CN; short
codes, service strings and unknown formats stay unchanged. Exact Apple native
formatting parity is not claimed. Fresh echo-only setups do not gain cellular
routes automatically. Six regression groups and nine isolated on-phone cases
passed; international live calls have not been exhaustively tested.
