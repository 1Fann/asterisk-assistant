# Asterisk Assistant

[简体中文](README.md) · [Download APK](https://github.com/1Fann/asterisk-assistant/releases/latest) · [MIT License](LICENSE)

Deploy and manage an Asterisk SIP server on a rooted ARM64 Android phone. Native Android interface; Termux is not required.

## Features

- One-tap download, integrity verification, Ubuntu ARM64 setup and Asterisk installation.
- Start, stop, restart, service status and active call count.
- Add/delete SIP accounts, change passwords and view client connection details.
- SIP/RTP port settings, dialplan/configuration editor and previous-save backup restoration.
- Runtime logs, account authentication tests and RTP echo self-test.
- Boot startup and optional dedicated wake lock.
- Configuration migration and guarded cleanup of the supported legacy deployment.

## Requirements

- ARM64 phone, Android 12+, primary Android user (user 0).
- Root and BusyBox at `/data/adb/ksu/bin/busybox`. The current implementation targets KernelSU/BakaSU; other Root solutions are untested.
- Wi-Fi Internet access for the first installation. Allow at least 1 GB of free space for the runtime and packages.
- Tested on an MT6893 Redmi running BakaSU and an Android 17 port. Other devices have not been tested.

## Quick start

1. Download the APK from [Releases](https://github.com/1Fann/asterisk-assistant/releases/latest).
2. Allow notifications and grant Asterisk Assistant Root access in your Root manager.
3. Tap the one-tap deployment button and wait for installation to finish.
4. Open the accounts screen for locally generated passwords and connection settings.
5. Use UDP. Default accounts are `1001` for a SIP client and `2001` for the local phone gateway. Dial `600` for echo testing.

A fresh deployment uses Wi-Fi SIP UDP `16060`, loopback SIP UDP `16060` and RTP `22000–22019`. Check the App for actual values; these settings can be changed in the UI.

For Linphone, use the phone's Wi-Fi IP as the SIP domain, `sip:PHONE_IP:PORT` as the SIP proxy, and the username as the authentication ID. First test echo extension `600` on the same Wi-Fi network.

The initial dialplan provides LAN echo testing. Real cellular call routing is not created automatically, and router settings are not changed. The current App interface is Chinese; this repository provides both Chinese and English documentation.

## Legacy migration

For an existing `/data/adb/sip-pbx` deployment, deploy the new runtime first and then use the migration button. Existing SIP accounts, passwords, dialplan and ports are retained. Service restarts briefly during migration.

After self-test and client verification, use legacy cleanup. This removes the old runtime directory, `98-sip-pbx.sh` boot entry and `local.sip.pbx.network` helper app. Other apps are outside the cleanup scope.

## Runtime and data

- Runtime: `/data/adb/asterisk-app`.
- Boot entry: `/data/adb/service.d/97-asterisk-app.sh`. It waits for boot completion, the primary user's first unlock and Wi-Fi availability.
- Root performs installation and management. Asterisk runs as this App's ordinary Android UID with cleared supplementary groups and Linux capabilities, plus no-new-privileges.
- A foreground service maintains the UID's background networking state. Runtime mounts use a private mount namespace.
- Account configuration stays in the device's Root-private directory; it is not uploaded or printed to logs. Management windows block screenshots.
- Allow notifications and background operation in Android settings. The optional wake lock is off by default and increases power use when enabled.

See [SECURITY.md](SECURITY.md). Uninstalling the App does not automatically remove the runtime; stop the server before uninstalling.

## Build

Windows, PowerShell, JDK 21, Android SDK Platform 35 and Build Tools 36.0.0 are required. Gradle is not needed.

```powershell
./build.ps1 -SdkRoot 'C:\Android\Sdk' -JavaHome 'C:\Java\jdk-21'
```

Alternatively set `ANDROID_HOME` and `JAVA_HOME`, then run `./build.ps1`. Output is written to `out/`. The first build creates a signing key in the ignored `private/` directory. Retain your key for future in-place updates; never commit or publish it.

The `releases/` directory contains Base64-encoded, locally signed APK release inputs and SHA-256 metadata. After backend checks and Android compilation pass, Actions decodes and verifies the prepared APK and uploads it to Releases. The release signing key remains local; CI builds use disposable keys.

Backend checks: `python3 check-backend.py assets/runtime`. Release validation: `python3 tools/verify_release.py`. Device validation: [VALIDATION.md](VALIDATION.md).

## Upstream and licensing

Original management code is [MIT licensed](LICENSE). Ubuntu Base 24.04.5 ARM64 is verified against a pinned SHA-256. Asterisk is installed from Ubuntu's signed noble repositories, so package revisions follow those repositories.

Asterisk and Ubuntu components retain their upstream licenses and are downloaded at installation time, not bundled in the APK. See [NOTICE.md](NOTICE.md). This is not an official Asterisk or Canonical app.
