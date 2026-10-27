"""Decode and verify the reviewed, production-signed release input."""
import base64, hashlib, io, json, re, sys, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
if (root/'AndroidManifest.xml').exists():
    version=ET.parse(root/'AndroidManifest.xml').getroot().attrib['{http://schemas.android.com/apk/res/android}versionName']
else:
    version=re.search(r'versionName\s*=\s*"([^"]+)"',(root/'app/build.gradle.kts').read_text()).group(1)
assert re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:-[a-z0-9.]+)?',version)
directory=root/'releases'/('v'+version)
m=json.loads((directory/'manifest.json').read_text())
assert m['version']==version and m['encoding']=='base64'
assert re.fullmatch(r'[A-Za-z0-9._-]+\.apk',m['name'])
parts=m.get('parts',[m.get('input')])
assert parts and len(set(parts))==len(parts)
assert all(isinstance(p,str) and re.fullmatch(re.escape(m['name'])+r'\.b64(?:\.[0-9]+)?',p) for p in parts)
binary=base64.b64decode(''.join((directory/p).read_text().strip() for p in parts),validate=True)
digest=hashlib.sha256(binary).hexdigest()
assert len(binary)==m['size'] and digest==m['sha256'],'APK checksum mismatch'
assert (directory/'SHA256SUMS').read_text().strip()==digest+'  '+m['name']
with zipfile.ZipFile(io.BytesIO(binary)) as z:
    assert z.testzip() is None
    assert {'classes.dex','AndroidManifest.xml'}<=set(z.namelist())
    assert not any(n.endswith(('.jks','.keystore','.password')) or n.startswith('private/') for n in z.namelist())
    for p in (root/'assets/runtime').glob('*'):
        if p.is_file():
            assert z.read('assets/runtime/'+p.name).replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n'),'Packaged runtime differs: '+p.name
    native=root/'third_party/upstream-native.json'
    if native.exists():
        for name,sha in json.loads(native.read_text())['libraries'].items():
            assert hashlib.sha256(z.read('lib/arm64-v8a/'+name)).hexdigest()==sha,'Native library mismatch'
output=Path(sys.argv[1]) if len(sys.argv)>1 else root/'.work/release'
output.mkdir(parents=True,exist_ok=True)
(output/m['name']).write_bytes(binary)
(output/'SHA256SUMS').write_text(digest+'  '+m['name']+'\n')
print('Verified signed APK: '+m['name'])
