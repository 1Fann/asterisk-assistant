"""Reject private local files and credential-shaped strings before publication."""
from pathlib import Path
import re,subprocess
root=Path(__file__).resolve().parents[1]
files=list(filter(None,subprocess.check_output(['git','ls-files','-z'],cwd=root).decode().split('\0')))
bad=[]
pattern=re.compile(rb'ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',re.I)
for name in files:
    p=Path(name)
    if any(x in {'private','out','.work','__pycache__'} for x in p.parts) or p.name=='local.properties' or p.suffix in {'.jks','.keystore','.password','.apk'}:
        bad.append(name);continue
    if name.startswith('releases/') or p.suffix in {'.jar','.png','.jpg'}:continue
    if pattern.search((root/p).read_bytes()):bad.append(name)
assert not bad,'Private material detected in: '+', '.join(bad)
print('Public-file audit passed: '+str(len(files))+' tracked files')
