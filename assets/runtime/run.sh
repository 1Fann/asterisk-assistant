#!/bin/sh
set -eu
mkdir -p /run/asterisk
chown -R asterisk:asterisk /run/asterisk /var/log/asterisk /var/lib/asterisk /var/spool/asterisk
chown root:android_inet /etc/asterisk /etc/asterisk/*.conf
chmod 750 /etc/asterisk
exec /usr/bin/setpriv --reuid="$(id -u asterisk)" --regid=3003 --clear-groups --bounding-set=-all --inh-caps=-all --no-new-privs /usr/sbin/asterisk -f -C /etc/asterisk/asterisk.conf
