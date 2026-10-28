"""Download and hash-check the public, pinned optional formatting dependency."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

VERSION = '9.0.42'
WHEEL = 'phonenumberslite-9.0.42-py2.py3-none-any.whl'
SHA256 = '7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e'
ROOT = Path(__file__).resolve().parents[2]
DESTINATION = ROOT/'.work/callerid-format'/WHEEL


def retrieve():
    if DESTINATION.exists():
        if hashlib.sha256(DESTINATION.read_bytes()).hexdigest() != SHA256:
            raise RuntimeError('Cached dependency checksum mismatch')
        return DESTINATION
    request = urllib.request.Request(
        'https://pypi.org/pypi/phonenumberslite/' + VERSION + '/json',
        headers={'User-Agent': 'asterisk-assistant-callerid-format'})
    with urllib.request.urlopen(request, timeout=30) as response:
        metadata = json.load(response)
    artifact = next(x for x in metadata['urls'] if x['filename'] == WHEEL)
    if artifact['digests']['sha256'] != SHA256 or not artifact['url'].startswith('https://files.pythonhosted.org/'):
        raise RuntimeError('Unexpected dependency metadata')
    with urllib.request.urlopen(artifact['url'], timeout=30) as response:
        binary = response.read(2*1024*1024)
    if hashlib.sha256(binary).hexdigest() != SHA256:
        raise RuntimeError('Downloaded dependency checksum mismatch')
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    temporary = DESTINATION.with_suffix('.part')
    temporary.write_bytes(binary)
    temporary.replace(DESTINATION)
    return DESTINATION


if __name__ == '__main__':
    dependency = retrieve()
    sys.path.insert(0, str(dependency))
    import phonenumbers
    assert phonenumbers.__version__ == VERSION
    print('Verified phonenumberslite ' + VERSION + ' (' + str(len(phonenumbers.SUPPORTED_REGIONS)) + ' regions)')
