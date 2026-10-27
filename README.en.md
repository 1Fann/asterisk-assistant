# Asterisk Assistant

[中文](README.md) · [Download APK](https://github.com/1Fann/asterisk-assistant/releases/latest) · [MIT](LICENSE)

Version **1.1.1**. A community Android app that deploys and manages Ubuntu's Asterisk packages on a rooted ARM64 phone. Asterisk core source is unchanged. Termux is not required.

Features include deployment, start/stop/restart, SIP accounts/passwords, connection state, ports, configuration/backups, logs, authentication/RTP echo self-tests, legacy migration/cleanup, boot startup and an optional wake lock.

## Independent recovery

Opt-in root monitoring has a1–1440 minute interval (default5), immediate check and last result. It checks the native server, foreground network owner, IPv4 SIP responses and Wi-Fi address changes. It never repairs Shizuku or the gateway; [Voice SIP Assistant](https://github.com/1Fann/voice-sip-assistant) owns those. A shared lock serializes both monitors. Manual server Stop is respected. Calls/unknown call state or absent Wi-Fi defer recovery. Clearing UI tasks does not stop the root loop; it resumes after first unlock following boot. Deep sleep can delay a check. Rare owner recovery may open the management activity. Disable monitoring and stop the server before uninstalling.

## Use

Android12+, ARM64, Root,1GB free space and `/data/adb/ksu/bin/busybox` are required. Grant Root and notifications, deploy, and read locally generated account credentials in the app. Fresh defaults: client1001, gateway2001, SIP UDP16060, RTP22000–22019 and echo600. Migrated deployments retain their settings. Fresh deployment does not enable cellular calling routes. No router changes or cloud credential upload. Runtime: `/data/adb/asterisk-app`; native Asterisk runs under the app's ordinary UID.

## Build and signing

On Windows with JDK21, Android SDK35 and Build Tools36.0.0, run `./build.ps1 -SdkRoot C:/Android/Sdk -JavaHome C:/Java/jdk-21`. Keys are generated locally under ignored `private/`. Public release APKs retain the maintainer's existing signing identity; CI uses a disposable key to verify compilation. Self-signed builds must update certificate pins (`RootBridge.CERT` or `Root.DUALSIM_CERT`, including the latter's paired gateway identity). A different certificate cannot update an existing installation. No private signing keys or device configuration are published.

See [validation](VALIDATION.md) and [third-party notices](NOTICE.md). The management code is MIT; Asterisk and Ubuntu retain their own licenses. Releases provide the locally signed APK and SHA256SUMS.

## Public IPv6 / DDNS (1.1.1)

After deployment, open Public IPv6 / DDNS, enable it and enter your own hostname. Your existing DDNS service continues to manage its AAAA record; Cloudflare must use DNS-only. Use the hostname without a port as the client domain, `sip:phone.example.com:port` as the UDP proxy, and retain existing credentials.

Managed client endpoints move to a non-temporary global Wi-Fi IPv6 address for signaling and media. Clients need IPv6 in this mode; use the hostname instead of the former IPv4 address. The local gateway remains on IPv4 loopback. Disabling public mode restores LAN client settings. With monitoring enabled, address changes trigger an idle-only restart; loss of IPv6 falls back to LAN until it returns.

The foreground service holds a Wi-Fi multicast reception lock for ROMs that filter IPv6 neighbor discovery while asleep. This consumes additional power and is released when public mode is disabled, the server stops or the process exits. Authentication/RTP echo self-tests support IPv6. No actual cellular calls are automated and router settings are not modified. Allow the configured SIP UDP and RTP ports along the path. The preset uses UDP without SIP TLS or media encryption; management and credentials remain local.

User validation confirmed hostname registration and echo over cellular Internet. Short screen-off cross-device SIP and ICMPv6 checks passed. Prolonged deep sleep, reboot and full dual-SIM public call coverage remain pending.
