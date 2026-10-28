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

## Bundled number-formatting dependency / 内置号码格式依赖

From 1.1.2 the Android APK bundles the complete `phonenumberslite` 9.0.42 wheel,
a Python port of Google's libphonenumber under Apache-2.0. It retains its upstream
license, copyright and package metadata. Its SHA-256 is
`7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e`.
The app verifies it before staging, and the server coordinator verifies it before
installation. It is installed beside the formatter, outside global Python
packages. Original management and integration code remains MIT; that license
does not replace the dependency's license.

1.1.2 起 APK 内置 Apache-2.0 授权的完整 `phonenumberslite` 9.0.42 wheel，保留
许可证、版权及包元数据。App 和服务端部署前均校验固定 SHA-256。依赖安装在
格式化脚本旁，不修改全局 Python 包；本项目 MIT 许可证不替代上游许可证。

- [Google libphonenumber](https://github.com/google/libphonenumber)
- [Python port and license](https://github.com/daviddrysdale/python-phonenumbers)
