"""Reject private local files and credential-shaped strings before publication."""
from pathlib import Path
import hashlib,re,subprocess
root=Path(__file__).resolve().parents[1]
files=list(filter(None,subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')))
bad=[]
pattern=re.compile(rb'ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',re.I)
for name in files:
    p=Path(name)
    if any(x in {'private','out','.work','__pycache__'} for x in p.parts) or p.name=='local.properties' or p.suffix in {'.jks','.keystore','.password','.apk'}:
        bad.append(name);continue
    if name.startswith('releases/') or p.suffix in {'.jar','.png','.jpg'}:continue
    if p.suffix=='.whl':
        if name!='assets/runtime/phonenumberslite-9.0.42-py2.py3-none-any.whl' or hashlib.sha256((root/p).read_bytes()).hexdigest()!='7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e':bad.append(name)
        continue
    if pattern.search((root/p).read_bytes()):bad.append(name)
assert not bad,'Private material detected in: '+', '.join(bad)
print('Public-file audit passed: '+str(len(files))+' tracked files')
