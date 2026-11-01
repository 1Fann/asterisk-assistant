"""Exercise production worker loops with isolated scheduler/process failures.

No phone, network, kernel lock or real server is touched. Android BusyBox's
deadline/locking implementation still needs separate on-device acceptance.
"""
import argparse, os, subprocess, tempfile
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('--shell',required=True)
shell=Path(parser.parse_args().shell).resolve()
repo=Path(__file__).resolve().parents[1]
(repo/'out').mkdir(exist_ok=True)
env={**os.environ,'PATH':str(shell.parent)+os.pathsep+os.environ.get('PATH','')}
def posix(p):
    s=Path(p).resolve().as_posix()
    return '/'+s[0].lower()+s[2:] if os.name=='nt' else s

with tempfile.TemporaryDirectory(prefix='wifi-workers-',dir=repo/'out') as temp:
    base=Path(temp)
    route=(repo/'assets/runtime/wifi-route.sh').read_text(encoding='utf-8')
    # Keep the production loop, replace Android command dispatch and sleep only.
    body=route[route.index('umask 077'):]
    fixture='''
BASE="'''+posix(base)+'''"
BB=bb
count=0
bb() {
 [ "$1 $2 $3 $4" = 'timeout -k 2 20' ] || exit 81
 count=$((count+1))
 # Model a checker that reaches its deadline each time. The next iteration
 # must still execute rather than leaving the singleton owner stuck/exited.
 return 124
}
sleep() { [ "$count" -lt 3 ] || rm -f "$BASE/wifi-compat.enabled"; }
'''+body+'''
'''
    # Production loop exits 0, so record each deadline dispatch in the fixture.
    fixture=fixture.replace('count=$((count+1))','count=$((count+1)); printf x >> "$BASE/checks"')
    (base/'wifi-worker-lib.sh').write_text('wifi_process() { WIFI_TICKS=100; return 0; }\n',encoding='utf-8')
    (base/'wifi-compat.enabled').touch();(base/'loop.sh').write_text(fixture,encoding='utf-8',newline='\n')
    subprocess.run([str(shell),str(base/'loop.sh'),'--loop'],env=env,check=True,timeout=10)
    assert (base/'checks').read_text()=='xxx'

    compat=(repo/'assets/runtime/wifi-compat.sh').read_text(encoding='utf-8')
    body=compat[compat.index('case "${1:-loop}"'):]
    prefix='''
BASE="'''+posix(base)+'''"
BB=bb
ticks=0
bb() {
 if [ "$1" = setsid ]; then
  # A singleton worker that disappears after the first iteration.
  if [ ! -f "$BASE/route-live" ]; then touch "$BASE/route-live"; printf x >> "$BASE/launches"; fi
  return 0
 fi
 exit 82
}
wifi_route_alive() { [ -f "$BASE/route-live" ]; }
getprop() { printf '0\\n'; }
sleep() {
 wait
 [ "$1" = 1 ] || exit 83
 ticks=$((ticks+1))
 [ "$ticks" -ne 1 ] || rm -f "$BASE/route-live"
 [ "$ticks" -lt 3 ] || rm -f "$BASE/wifi-compat.enabled"
}
'''
    (base/'wifi-compat.enabled').touch();(base/'compat.sh').write_text(prefix+body,encoding='utf-8',newline='\n')
    subprocess.run([str(shell),str(base/'compat.sh'),'--loop'],env=env,check=True,timeout=10)
    assert (base/'launches').read_text()=='xx'
    (base/'launches').unlink();(base/'disabled').touch();(base/'wifi-compat.enabled').touch()
    subprocess.run([str(shell),str(base/'compat.sh'),'--loop'],env=env,check=True,timeout=10)
    assert not (base/'launches').exists()
    (base/'disabled').unlink()
    subprocess.run([str(shell),str(base/'compat.sh'),'--loop'],env=env,check=True,timeout=10)
    assert not (base/'launches').exists()
print('PASS: timed-out checks continue; lost workers recover; live workers remain; stop and compatibility opt-out prevent relaunch')
