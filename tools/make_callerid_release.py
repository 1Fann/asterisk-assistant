"""Build a self-contained optional extension release, preserving the signed APK."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT/'releases/callerid-format-v1.0.0'
META = json.loads((RELEASE/'manifest.json').read_text())
OUT = ROOT/'.work/callerid-release'
TOOLS = ROOT/'tools/callerid-format'


def archive_file(archive, name, data):
    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data)


def build():
    assert re.fullmatch(r'callerid-format-v[0-9]+\.[0-9]+\.[0-9]+', META['tag'])
    assert all(re.fullmatch(r'[A-Za-z0-9._-]+\.zip', META[k]) for k in ['tools_name', 'source_name'])
    OUT.mkdir(parents=True, exist_ok=True)
    # The existing verifier checks the reviewed production-signed APK payload.
    subprocess.run([sys.executable, str(ROOT/'tools/verify_release.py'), str(OUT)], check=True)
    apk = OUT/('Asterisk-Assistant-' + META['apk_version'] + '.apk')
    assert apk.is_file()
    spec = importlib.util.spec_from_file_location('callerid_dependency', TOOLS/'download_dependency.py')
    dependency = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dependency)
    wheel = dependency.retrieve()
    prefix = 'asterisk-callerid-format-' + META['version'] + '/'
    with zipfile.ZipFile(OUT/META['tools_name'], 'w') as archive:
        for source in sorted(TOOLS.iterdir()):
            if source.is_file() and source.suffix in {'.py', '.ps1', '.md'}:
                archive_file(archive, prefix+'tools/callerid-format/'+source.name, source.read_bytes())
        archive_file(archive, prefix+'tools/callerid-format/'+wheel.name, wheel.read_bytes())
        for name in ['LICENSE', 'NOTICE.md']:
            archive_file(archive, prefix+name, (ROOT/name).read_bytes())
        archive_file(archive, prefix+'README.md', (RELEASE/'NOTES.md').read_bytes())
    # Keep the source package aligned with the workflow's checked-out commit.
    files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    source_prefix = 'asterisk-assistant-' + META['tag'] + '/'
    with zipfile.ZipFile(OUT/META['source_name'], 'w') as archive:
        for name in sorted(filter(None, files)):
            if name.startswith('releases/'):
                continue
            assert not any(p in {'private', '.work', 'out', '.git', '__pycache__'} for p in Path(name).parts)
            assert not name.endswith(('.jks', '.keystore', '.password', '.apk', '.b64'))
            archive_file(archive, source_prefix+name, (ROOT/name).read_bytes())
    assets = [apk, OUT/META['tools_name'], OUT/META['source_name']]
    (OUT/'SHA256SUMS').write_text(''.join(
        hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name + '\n' for path in assets))
    for path in assets:
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
    with zipfile.ZipFile(OUT/META['tools_name']) as archive:
        binary = archive.read(prefix+'tools/callerid-format/'+wheel.name)
        assert hashlib.sha256(binary).hexdigest() == dependency.SHA256
    print('Prepared ' + META['tag'] + ': unchanged signed APK, offline tools, source and checksums')


if __name__ == '__main__':
    build()
