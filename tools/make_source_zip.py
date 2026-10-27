"""Create a source-only archive; include pinned native sources for the gateway."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
from download import retrieve
root=Path(__file__).resolve().parents[1]
out=root/'.work/release';out.mkdir(parents=True,exist_ok=True)
manifest=next(p for p in (root/'releases').glob('*/manifest.json') if (p.parent.name==('v'+json.loads(p.read_text())['version'])) and json.loads(p.read_text())['name']==next(out.glob('*.apk')).name)
version=json.loads(manifest.read_text())['version']
target=out/(root.name+'-'+version+'-source.zip')
files=subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')
assert any(p=='LICENSE' for p in files)
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for name in sorted(filter(None,files)):
        if name.startswith('releases/'):continue
        assert not any(p in {'private','.work','out','.git'} for p in Path(name).parts)
        assert not name.endswith(('.jks','.keystore','.password','.apk','.b64'))
        z.write(root/name,root.name+'/'+name)
    native=root/'third_party/upstream-native.json'
    if native.exists():
        for item in json.loads(native.read_text())['native_source_archives']:
            archive=retrieve(item['url'],item['sha256'],root/'.work/native-sources'/item['name'])
            z.write(archive,root.name+'/third_party/native-sources/'+item['name'])
digest=hashlib.sha256(target.read_bytes()).hexdigest()
with (out/'SHA256SUMS').open('a') as f:f.write(digest+'  '+target.name+'\n')
print('Created corresponding source archive: '+target.name)
