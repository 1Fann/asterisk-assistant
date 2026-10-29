# Asterisk Assistant

**Latest: 1.2.1** — [新手机部署与权限说明 / New-phone setup](NEW-PHONE-SETUP.md)

Bundled AGI missing-name formatting fix, portable root-provider support, IPv6 Wi-Fi receive locks and optional Android 11–13 screen-off compatibility.

[中文](README.md) · [Download APK](https://github.com/1Fann/asterisk-assistant/releases/latest) · [MIT](LICENSE)

Version **1.2.1**. A community Android app that deploys and manages Ubuntu's Asterisk packages on a rooted ARM64 phone. Asterisk core source is unchanged. Termux is not required.

1.2.0 fixes skipped number grouping when AGI represents a missing caller name as `unknown`, while preserving real contact names and caller privacy.

Features include deployment, start/stop/restart, SIP accounts/passwords, connection state, ports, configuration/backups, logs, authentication/RTP echo self-tests, legacy migration/cleanup, boot startup and an optional wake lock.

## Update 1.2.1

Also fixes the corrupted launcher label and adds an adaptive server icon.

The reproduced failure involved Android background restrictions, disabled MIUI autostart, and a readiness check accepting stale registration without a foreground service. Shortening the full-check interval alone was insufficient.

The assistants now show a background-access setup prompt. After explicit confirmation, Root changes are limited to the assistant and its trusted paired gateway: background execution, battery-optimization exemption, and recognized MIUI autostart. Phone, microphone, notification, and Shizuku consent remain separate. Unsupported settings identify the failed step instead of incorrectly reporting missing Root.

When monitoring is enabled, an approximately 10-second lightweight check detects a missing foreground service. Full checks retain the configured 1–1440-minute interval. Consented background settings may be repaired if restrictions return. Server and gateway recovery retain separate ownership, a shared repair lock, active-call guards and manual-OFF behavior. Recovery is not uninterrupted availability.

The existing Asterisk dedicated-wake option now also controls a renewable, bounded root-monitor wake lease. Disabling it releases the lease. DDNS keeps its separate existing daemon and wake option.

## Independent recovery

Opt-in root monitoring has a1–1440 minute interval (default5), immediate check and last result. It checks the native server, foreground network owner, IPv4 SIP responses and Wi-Fi address changes. It never repairs Shizuku or the gateway; [Voice SIP Assistant](https://github.com/1Fann/voice-sip-assistant) owns those. A shared lock serializes both monitors. Manual server Stop is respected. Calls/unknown call state or absent Wi-Fi defer recovery. Clearing UI tasks does not stop the root loop; it resumes after first unlock following boot. Deep sleep can delay a check. Rare owner recovery may open the management activity. Disable monitoring and stop the server before uninstalling.

## Use

Android12+, ARM64, Root,1GB free space and a supported root-manager BusyBox are required (Magisk, KernelSU/BakaSU or APatch path discovery). Grant Root and notifications, deploy, and read locally generated account credentials in the app. Fresh defaults: client1001, gateway2001, SIP UDP16060, RTP22000–22019 and echo600. Migrated deployments retain their settings. Fresh deployment does not enable cellular calling routes. No router changes or cloud credential upload. Runtime: `/data/adb/asterisk-app`; native Asterisk runs under the app's ordinary UID.

## Built-in incoming number grouping (1.1.2)

The APK now includes the formatter and complete pinned lightweight libphonenumber
metadata for 245 regions. New deployment prepares it automatically. On upgrade,
open the app and grant Root; existing configurations are taken over while idle.
No computer ADB or separate deployment ZIP is required.

Open **Incoming number grouping / 来电号码分段** on the home screen to toggle the
feature and choose the default region (CN by default). International country
codes are recognized automatically. Bare numbers use the selected region.
Formatting remains offline; only numeric display names change. Caller numbers,
privacy and textual names remain intact. Short codes, service strings and
unknown formats are preserved. Calls or unknown call state defer configuration;
idle status refresh retries automatically. Settings changes require idle state.

Fresh deployment remains echo-only and does not create cellular calling routes.
Authenticated loopback gateway contexts are wrapped without changing their
original priorities; existing standalone hooks are taken over in place to avoid
double execution. Exact Apple native UI parity is not claimed. The [standalone
deployment tools](tools/callerid-format/README.md) remain as a legacy fallback.

## Build and signing

On Windows with JDK21, Android SDK35 and Build Tools36.0.0, run `./build.ps1 -SdkRoot C:/Android/Sdk -JavaHome C:/Java/jdk-21`. Keys are generated locally under ignored `private/`. Public release APKs retain the maintainer's existing signing identity; CI uses a disposable key to verify compilation. Self-signed builds must update certificate pins (`RootBridge.CERT` or `Root.DUALSIM_CERT`, including the latter's paired gateway identity). A different certificate cannot update an existing installation. No private signing keys or device configuration are published.

See [validation](VALIDATION.md) and [third-party notices](NOTICE.md). The management code is MIT; Asterisk and Ubuntu retain their own licenses. Releases provide the locally signed APK and SHA256SUMS.

## Public IPv6 / DDNS (1.1.1)

After deployment, open Public IPv6 / DDNS, enable it and enter your own hostname. Your existing DDNS service continues to manage its AAAA record; Cloudflare must use DNS-only. Use the hostname without a port as the client domain, `sip:phone.example.com:port` as the UDP proxy, and retain existing credentials.

Managed client endpoints move to a non-temporary global Wi-Fi IPv6 address for signaling and media. Clients need IPv6 in this mode; use the hostname instead of the former IPv4 address. The local gateway remains on IPv4 loopback. Disabling public mode restores LAN client settings. With monitoring enabled, address changes trigger an idle-only restart; loss of IPv6 falls back to LAN until it returns.

The foreground service holds a Wi-Fi multicast reception lock for ROMs that filter IPv6 neighbor discovery while asleep. This consumes additional power and is released when public mode is disabled, the server stops or the process exits. Authentication/RTP echo self-tests support IPv6. No actual cellular calls are automated and router settings are not modified. Allow the configured SIP UDP and RTP ports along the path. The preset uses UDP without SIP TLS or media encryption; management and credentials remain local.

User validation confirmed hostname registration and echo over cellular Internet. Short screen-off cross-device SIP and ICMPv6 checks passed. Prolonged deep sleep, reboot and full dual-SIM public call coverage remain pending.
