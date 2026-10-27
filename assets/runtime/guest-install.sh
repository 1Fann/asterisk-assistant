#!/bin/sh
set -eu
export DEBIAN_FRONTEND=noninteractive
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
printf 'APT::Sandbox::User "root";\n' > /etc/apt/apt.conf.d/99android
printf 'nameserver 223.5.5.5\nnameserver 1.1.1.1\n' > /etc/resolv.conf
cat > /etc/apt/sources.list.d/ubuntu.sources <<'EOF'
Types: deb
URIs: http://ports.ubuntu.com/ubuntu-ports
Suites: noble noble-updates noble-security
Components: main universe
Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg
EOF
dpkg --configure -a
apt-get update -o Acquire::Retries=3
apt-get install -y --no-install-recommends asterisk ca-certificates openssl python3 util-linux
getent group android_inet >/dev/null || groupadd -g 3003 android_inet
PBX_UID=$(cat /etc/asterisk-app/android-uid)
case "$PBX_UID" in ''|*[!0-9]*) exit 1;; esac
[ "$PBX_UID" -ge 10000 ] && [ "$PBX_UID" -lt 20000 ]
if [ "$(id -u asterisk)" != "$PBX_UID" ]; then usermod -u "$PBX_UID" asterisk; fi
apt-get clean
