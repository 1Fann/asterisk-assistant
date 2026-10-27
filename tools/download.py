"""Retrieve only public, SHA-256-pinned upstream artifacts."""
import hashlib, urllib.request
from pathlib import Path
def retrieve(url,sha,destination):
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    if not destination.exists():
        temporary=destination.with_name(destination.name+'.part')
        request=urllib.request.Request(url,headers={'User-Agent':'voice-sip-gateway-source-builder'})
        with urllib.request.urlopen(request,timeout=90) as response,temporary.open('wb') as out:
            while chunk:=response.read(1024*1024): out.write(chunk)
        assert hashlib.sha256(temporary.read_bytes()).hexdigest()==sha,'Upstream artifact checksum mismatch'
        temporary.replace(destination)
    assert hashlib.sha256(destination.read_bytes()).hexdigest()==sha,'Cached artifact checksum mismatch'
    return destination
