#!/system/bin/sh
# Isolated boot-policy regression; all Android commands below are mocked.
set -eu
SOURCE=$1
BB=/data/adb/magisk/busybox
TEST_ROOT=/data/local/tmp/voice-reliability-test-20261031
mkdir -p "$TEST_ROOT"
CASE=$("$BB" mktemp -d "$TEST_ROOT/boot.XXXXXX")
case "$CASE" in /data/local/tmp/voice-reliability-test-20261031/boot.*) ;; *) exit 2;; esac
trap 'rm -rf "$CASE"' EXIT
export BOOT_TEST_CASE="$CASE"
mkdir "$CASE/bin"
printf '#!/system/bin/sh\necho 1\n' > "$CASE/bin/getprop"
cat > "$CASE/bin/cmd" <<'EOF'
#!/system/bin/sh
if [ -f "$BOOT_TEST_CASE/locked" ]; then echo RUNNING_LOCKED; else echo RUNNING_UNLOCKED; fi
EOF
printf '#!/system/bin/sh\necho "2: wlan0 inet 192.0.2.1/24"\n' > "$CASE/bin/ip"
cat > "$CASE/bin/am" <<'EOF'
#!/system/bin/sh
touch "$BOOT_TEST_CASE/start-requested"
EOF
chmod 700 "$CASE/bin/"*
PATH="$CASE/bin:$PATH"
export PATH
"$BB" sed "s|^BASE=.*|BASE=$CASE|" "$SOURCE" > "$CASE/boot.sh"
touch "$CASE/installed" "$CASE/disabled"
echo 1 > "$CASE/autostart"
"$BB" timeout 12 /system/bin/sh "$CASE/boot.sh" --worker
[ ! -f "$CASE/start-requested" ] || { echo 'FAIL: manual STOP overridden at boot'; exit 1; }
echo 'PASS: manual STOP survives boot'
rm "$CASE/disabled"
"$BB" timeout 12 /system/bin/sh "$CASE/boot.sh" --worker
[ -f "$CASE/start-requested" ]
echo 'PASS: enabled unlocked boot requests the service'
rm "$CASE/start-requested"
touch "$CASE/locked"
(sleep 1; echo 0 > "$CASE/autostart") &
"$BB" timeout 12 /system/bin/sh "$CASE/boot.sh" --worker
[ ! -f "$CASE/start-requested" ]
echo 'PASS: disabling autostart cancels waiting for first unlock'
