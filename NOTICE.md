# Third-party components / 第三方组件

The original Android management code and deployment scripts in this repository are available under the MIT License in [LICENSE](LICENSE).

本仓库原创的 Android 管理代码及部署脚本采用 [MIT 许可证](LICENSE)。

Asterisk and Ubuntu Base are separate upstream projects. Their executables and root filesystem are **not bundled in the APK**. The App downloads the verified Ubuntu Base archive from Canonical and installs packages from Ubuntu's signed repositories on the device. Those components retain their upstream licenses and copyright notices; the repository's MIT License does not replace them.

Asterisk 和 Ubuntu Base 为独立上游项目，其可执行文件及根文件系统不包含在 APK 内。App 在手机上下载经校验的 Ubuntu Base，再从 Ubuntu 签名软件源安装软件包；这些组件保留其各自的许可证和版权声明。

- [Asterisk source and licensing](https://github.com/asterisk/asterisk)
- [Ubuntu Base](https://cdimage.ubuntu.com/ubuntu-base/releases/24.04/release/)
- Installed package copyright files: `/usr/share/doc/<package>/copyright` inside the runtime.

This is a community Android management tool, not an official Asterisk or Canonical app. No endorsement is implied.

本项目为社区 Android 管理工具，并非 Asterisk 或 Canonical 官方 App。

## Optional number-formatting dependency / 可选号码格式依赖

The optional `tools/callerid-format` extension downloads `phonenumberslite`
9.0.42, the Python port of Google's libphonenumber, under Apache-2.0. Its fixed
SHA-256 is recorded in the downloader and deployment guide. The complete wheel
retains its upstream license, copyright and package metadata. It is installed
beside the server-side formatter, outside global Python packages, and is not
bundled in the Android APK. This repository's MIT license does not replace it.

可选扩展下载 Apache-2.0 授权的 `phonenumberslite` 9.0.42，固定校验值见下载脚本
及部署说明。完整 wheel 保留上游许可证、版权及包元数据，不安装到全局 Python
环境，也不包含在 APK 内。仓库 MIT 许可证不替代上游许可证。

- [Google libphonenumber](https://github.com/google/libphonenumber)
- [Python port and license](https://github.com/daviddrysdale/python-phonenumbers)
