"""Run as root on Linux, against an isolated directory and an inert worker."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile


def main():
    assert os.getuid() == 0, 'Run in an isolated Linux root context or with sudo'
    source = Path(__file__).resolve().parents[1] / 'assets/runtime/suite-fallback-config.sh'
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        base = root / 'interlink-guard'
        boot = root / 'service.d'
        boot.mkdir()
        bb = root / 'magisk/busybox'
        bb.parent.mkdir()
        bb.write_text('#!/bin/sh\nexec "$@"\n')
        bb.chmod(0o700)
        script = root / 'config.sh'
        script.write_text(source.read_text().replace('/data/adb/', tmp+'/').replace('/system/bin/sh','/bin/sh'))
        worker = '#!/bin/sh\nexit 0\n'
        digest = hashlib.sha256(worker.encode()).hexdigest()
        def run(action, *args):
            return subprocess.check_output(['/bin/sh', str(script), action, *args],text=True).strip()
        assert run('status') == 'off' and not base.exists()
        assert run('enable',worker,digest) == 'started'
        assert (base/'guard.sh').read_text() == worker and (base/'enabled').is_file()
        stamp = (base/'guard.sh').stat().st_mtime_ns
        assert run('enable',worker,digest) == 'started' and (base/'guard.sh').stat().st_mtime_ns == stamp
        assert run('disable') == 'off' and run('disable') == 'off'
        hook = boot / '95-interlink-guard.sh'
        assert not hook.exists() and not (base/'enabled').exists()
        hook.write_text('foreign installation\n')
        assert run('enable',worker,digest) == 'conflict' and hook.read_text() == 'foreign installation\n'
        hook.unlink(); hook.symlink_to(base/'guard.sh')
        assert run('disable') == 'conflict' and hook.is_symlink()
        hook.unlink()
        try: run('enable',worker,'0'*64)
        except subprocess.CalledProcessError: pass
        else: raise AssertionError('Accepted incorrect payload digest')
        assert not (base/'enabled').exists()
        print('Companion monitor install, idempotence, disable, conflict and digest checks passed')


if __name__ == '__main__': main()
