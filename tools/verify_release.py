"""Validate and decode the prepared public APK without any signing credentials."""
import base64
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

root=Path(__file__).resolve().parents[1]
version=ET.parse(root/'AndroidManifest.xml').getroot().attrib['{http://schemas.android.com/apk/res/android}versionName']
assert re.fullmatch(r'\d+\.\d+\.\d+',version),'Invalid version'
directory=root/'releases'/('v'+version)
manifest=json.loads((directory/'manifest.json').read_text())
assert manifest['version']==version and manifest['encoding']=='base64'
assert re.fullmatch(r'[A-Za-z0-9._-]+\.apk',manifest['name'])
assert manifest['input']==manifest['name']+'.b64'
binary=base64.b64decode((directory/manifest['input']).read_text().strip(),validate=True)
digest=hashlib.sha256(binary).hexdigest()
assert len(binary)==manifest['size'] and digest==manifest['sha256'],'APK checksum mismatch'
assert (directory/'SHA256SUMS').read_text().strip()==digest+'  '+manifest['name']
output=Path(sys.argv[1]) if len(sys.argv)>1 else root/'.work/release'
output.mkdir(parents=True,exist_ok=True)
apk=output/manifest['name'];apk.write_bytes(binary)
with zipfile.ZipFile(apk) as archive:
    assert archive.testzip() is None
    assert 'classes.dex' in archive.namelist() and 'AndroidManifest.xml' in archive.namelist()
    for source in (root/'assets/runtime').iterdir():
        if source.is_file():
            assert archive.read('assets/runtime/'+source.name).replace(b'\r\n',b'\n')==source.read_bytes().replace(b'\r\n',b'\n'),'Packaged runtime differs: '+source.name
    assert not any(n.endswith(('.jks','.keystore','.password')) or n.startswith('private/') for n in archive.namelist())
(output/'SHA256SUMS').write_text(digest+'  '+manifest['name']+'\n')
print('Prepared signed APK verified: '+manifest['name'])
