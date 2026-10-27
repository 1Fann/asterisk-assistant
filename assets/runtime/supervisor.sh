#!/system/bin/sh
# Compatibility launcher: configurable server checks are owned by Asterisk Assistant.
BASE=/data/adb/asterisk-app
[ -f "$BASE/health-enabled" ] || exit 0
exec /system/bin/sh "$BASE/health.sh" loop
