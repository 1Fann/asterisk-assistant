"""Production identity-cache and upgrade-loop checks with an isolated proc table."""
import argparse, os, subprocess, tempfile
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--shell',required=True)
shell=Path(parser.parse_args().shell).resolve();repo=Path(__file__).resolve().parents[1]
(repo/'out').mkdir(exist_ok=True)
env={**os.environ,'PATH':str(shell.parent)+os.pathsep+os.environ.get('PATH','')}
def posix(p):
 s=Path(p).resolve().as_posix();return '/'+s[0].lower()+s[2:] if os.name=='nt' else s
with tempfile.TemporaryDirectory(prefix='wifi-identity-',dir=repo/'out') as tmp:
 base=Path(tmp);b=posix(base)
 lib=(repo/'assets/runtime/wifi-worker-lib.sh').read_text(encoding='utf-8').replace('/proc/',b+'/proc/')
 (base/'lib.sh').write_text(lib,encoding='utf-8',newline='\n')
 for pid in (101,102,201,202,777): (base/'proc'/str(pid)).mkdir(parents=True)
 def stat(pid,ticks,parent=1):
  return f'{pid} (sh) '+' '.join(['S',str(parent)]+['0']*17+[str(ticks)])+'\n'
 (base/'proc/101/stat').write_text(stat(101,100),newline="\n");(base/'proc/101/cmdline').write_bytes(('/system/bin/sh\0'+b+'/wifi-route.sh\0--loop\0').encode())
 (base/'wifi-route.pid').write_text('101 100\n',newline='\n')
 script=f'''BASE='{b}'
BB=bb
bb() {{ printf x >> "$BASE/argv-reads"; shift; tr "$@"; }}
kill() {{ [ "$1" = -0 ] && [ "$2" = 101 ]; }}
. "$BASE/lib.sh"
wifi_route_alive || exit 1
wifi_route_alive || exit 2
printf '%s' '{stat(101,200)}' > "$BASE/proc/101/stat"
if wifi_route_alive; then exit 3; fi
printf '101 200\\n' > "$BASE/wifi-route.pid"
printf 'unrelated\\000' > "$BASE/proc/101/cmdline"
if wifi_route_alive; then exit 4; fi
printf '/system/bin/sh\\000%s/wifi-route.sh\\000--loop\\000' "$BASE" > "$BASE/proc/101/cmdline"
wifi_route_alive || exit 5
wifi_route_alive || exit 6
printf '101 200 extra\\n' > "$BASE/wifi-route.pid"
if wifi_route_alive; then exit 7; fi
rm "$BASE/wifi-route.pid"
if wifi_route_alive; then exit 8; fi
'''
 (base/'identity.sh').write_text(script,encoding='utf-8',newline='\n')
 subprocess.run([str(shell),str(base/'identity.sh')],env=env,check=True,timeout=10)
 assert (base/'argv-reads').read_text()=='xxx', 'healthy ticks must not re-run argv commands'

 # Execute the production handoff algorithm against old-loop/sleep identities.
 for pid,parent in ((201,101),(202,102),(777,999)):
  (base/f'proc/{pid}/cmdline').write_bytes(b'sleep\0'+(b'30' if pid==201 else b'15')+b'\0')
 (base/'wifi-compat.enabled').touch()
 prefix=f'''BASE='{b}'
BB=bb
pidof() {{ case "$1" in sh) echo '101 102 999';; sleep) echo '201 202 777';; esac; }}
wifi_process() {{
 case "$1" in
  101) WIFI_TICKS=10; WIFI_PPID=1;; 102) WIFI_TICKS=20; WIFI_PPID=1;;
  201) WIFI_TICKS=30; WIFI_PPID=101;;
  202) if [ -f "$BASE/reused" ]; then WIFI_TICKS=999; WIFI_PPID=999; else WIFI_TICKS=40; WIFI_PPID=102; fi;;
  777) WIFI_TICKS=50; WIFI_PPID=999;; *) return 1;;
 esac
}}
wifi_owner() {{ case "$1:$2:$3" in 101:route:10|102:compat:20) return 0;; *) return 1;; esac; }}
kill() {{
 printf '%s %s\\n' "$1" "$2" >> "$BASE/signals"
 [ "$1:$2" != '-TERM:102' ] || touch "$BASE/reused"
 return 0
}}
sleep() {{ :; }}
bb() {{ if [ "$1" = tr ]; then shift; tr "$@"; elif [ "$1" = setsid ]; then printf x >> "$BASE/restarted"; else exit 90; fi; }}
'''
 upgrade=(repo/'assets/runtime/wifi-upgrade.sh').read_text(encoding='utf-8')
 upgrade=upgrade[upgrade.index('OWNERS='):].replace('/proc/',b+'/proc/')
 (base/'handoff.sh').write_text(prefix+upgrade+'\nwait\n',encoding='utf-8',newline='\n')
 subprocess.run([str(shell),str(base/'handoff.sh')],env=env,check=True,timeout=10)
 signals=(base/'signals').read_text().splitlines()
 assert set(signals)=={'-TERM 101','-TERM 102','-TERM 201','-KILL 101','-KILL 102'},signals
 assert (base/'restarted').read_text()=='x'
print('PASS: cached identities, PID reuse, malformed/stale records, exact old-worker retirement, old sleep release and replacement exclusion')
