"""Exercise the real Magisk control script with temporary directories and fake Android/Magisk."""
import argparse
import base64
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--shell", required=True)
shell = Path(parser.parse_args().shell).resolve()
repo = Path(__file__).resolve().parents[1]
source = repo / "assets/compat/redmi-wifi-control.sh"
bundle = repo / "assets/compat/redmi-wifi-module.zip"
module = "interlink_wifi_awake"
name = "ZZInterlinkWifiAwake.apk"
apk = Path("system/product/overlay") / name

def posix(path):
    path = Path(path).resolve().as_posix()
    return "/" + path[0].lower() + path[2:] if os.name == "nt" else path

(repo/"out").mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=repo/"out") as temp:
    base = Path(temp)
    script = base / "check.sh"
    live = base / "modules" / module
    next_dir = base / "modules_update" / module
    live.parent.mkdir()
    next_dir.parent.mkdir()
    other = live.parent / "other"
    other.mkdir()
    (other / "disable").write_text("untouched")
    template = base / "bundle"
    with zipfile.ZipFile(bundle) as z:
        z.extractall(template)
    mounted = base / name
    payload = base64.b64encode(bundle.read_bytes()).decode()
    mocks = '''
BB=bb
bb(){
 local op=$1;shift
 case "$op" in
  timeout) shift; "$@";;
  base64) "$TEST_PY" -c 'import base64,sys;sys.stdout.buffer.write(base64.b64decode(sys.stdin.buffer.read(),validate=True))';;
  sha256sum) "$TEST_PY" -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest(),sys.argv[1])' "$1";;
  *) command "$op" "$@";;
 esac
}
getprop(){ case "$1" in ro.product.device) echo "$TEST_DEVICE";; ro.build.version.sdk) echo "$TEST_SDK";; esac; }
pm(){ case "$2" in com.android.wifi.resources) [ "$HAS_TARGET" = yes ] && echo package:/target.apk;;
     local.interlink.redmi.wifiawake) [ ! -e "$MOUNTED" ] || echo "package:$MOUNTED";; esac; }
cmd(){ echo "$LOOKUP"; }
dumpsys(){ echo "mSuspendOptimizationsEnabled $SUSPEND"; }
magisk(){
 case "$1" in
 -V) echo "$MAGISK_VERSION";;
 --install-module)
  [ ! -f "$BASE/block-install" ] || return 1
  echo called >>"$BASE/install-count"; mkdir -p "$next" "$live"
  cp -R "$BASE/bundle/." "$next/"; cp "$next/module.prop" "$live/"; touch "$live/update";;
 esac
}
'''
    text = source.read_text().replace("BASE=/data/adb", "BASE=" + shlex.quote(posix(base)))
    text = text.replace("BB=$BASE/magisk/busybox", mocks)
    text = text.replace("package:/product/overlay/ZZInterlinkWifiAwake.apk|package:/system/product/overlay/ZZInterlinkWifiAwake.apk", '"package:$MOUNTED"')
    script.write_text(text, newline="\n")
    env = dict(os.environ, PATH=str(shell.parent)+os.pathsep+os.environ["PATH"],
               TEST_DEVICE="chopin", TEST_SDK="33", HAS_TARGET="yes", LOOKUP="true",
               MAGISK_VERSION="27000", SUSPEND="true", MOUNTED=posix(mounted), TEST_PY=sys.executable.replace("\\","/"))
    checked = 0
    def check(action, wanted, data=payload, **extra):
        global checked
        result = subprocess.run([str(shell),posix(script),action,data], env={**env, **extra},
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15)
        assert result.returncode == 0 and result.stdout.strip() == wanted, (action,wanted,result.stdout,result.stderr)
        assert (other / "disable").read_text() == "untouched"
        checked += 1
    check("enable","unsupported",TEST_DEVICE="another")
    check("enable","unsupported",TEST_SDK="34")
    check("enable","no-target",HAS_TARGET="no")
    check("enable","no-magisk",MAGISK_VERSION="")
    check("status","absent")
    check("enable","bad-asset",base64.b64encode(b"wrong").decode())
    (base/"block-install").touch()
    check("enable","install-failed")
    (base/"block-install").unlink()
    check("enable","pending-enable")
    check("enable","pending-enable")
    assert (base/"install-count").read_text().splitlines()==["called"]
    check("disable","disabled")
    assert all((d/"disable").is_file() for d in (live,next_dir))
    (next_dir/"disable").unlink()
    check("status","mixed")
    check("disable","disabled")
    check("enable","pending-enable")
    shutil.rmtree(live);next_dir.rename(live)
    shutil.copyfile(template/apk,mounted)
    check("status","not-effective")
    check("status","not-effective",LOOKUP="false")
    check("enable","active",LOOKUP="false",SUSPEND="false")
    check("disable","pending-disable")
    mounted.unlink()
    check("disable","disabled")
    (live/"remove").touch()
    check("enable","removing")
    (live/"remove").unlink()
    (live/"service.sh").write_text("foreign hook")
    check("enable","conflict")
    (live/"service.sh").unlink()
    (live/apk).write_text("unknown overlay")
    check("disable","conflict")
    assert (live/"disable").is_file()
    if os.name != "nt":
        shutil.rmtree(live);live.symlink_to(other, target_is_directory=True)
        check("disable","conflict")
    print("PASS:",checked,"module state/action cases; unrelated module preserved")
