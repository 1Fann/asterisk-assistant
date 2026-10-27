"""Run inside the guest; tests use a temporary configuration, never live accounts."""
import importlib.util
from pathlib import Path
import tempfile
import sys

runtime=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/opt/asterisk-app')
spec=importlib.util.spec_from_file_location('manager_api',runtime/'api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
api.os.chown=lambda *arguments:None  # Device checks separately verify the real UID/group/capabilities.
for name in ('api.py','selftest.py','fresh-config.py'):
    compile((runtime/name).read_text(encoding='utf-8'),name,'exec')
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);api.C=root/'config';api.S=root/'state';api.C.mkdir();api.S.mkdir()
    (api.S/'lan-ip').write_text('192.0.2.10')
    initial='''; preserve this comment
[transport-lan]
type=transport
bind=192.0.2.9:16060
[transport-loopback]
type=transport
bind=127.0.0.1:16060
'''+api.account_blocks('1001','test_only_password_123','client','192.0.2.9')
    (api.C/'pjsip.conf').write_text(initial)
    (api.C/'extensions.conf').write_text('[custom]\nexten => 999,1,Hangup()\n')
    (api.C/'rtp.conf').write_text('[general]\nrtpstart=22000\nrtpend=22019\n')
    api.cli=lambda command:''
    assert api.auth_records()['1001']['password']=='test_only_password_123'
    api.network()
    updated=(api.C/'pjsip.conf').read_text()
    assert 'bind=192.0.2.10:16060' in updated and 'media_address=192.0.2.10' in updated
    assert updated.count('[1001]')==2 and updated.startswith('; preserve this comment')
    api.save_account({'user':'1001','password':'test_only_changed_123','role':'client'})
    assert api.auth_records()['1001']['password']=='test_only_changed_123'
    assert (api.C/'extensions.conf').read_text()=='[custom]\nexten => 999,1,Hangup()\n'
    api.save_account({'user':'1002','password':'test_only_second_123','role':'client'})
    assert len(api.auth_records())==2 and '[custom]' in (api.C/'extensions.conf').read_text()
    api.delete_account({'user':'1002'})
    assert list(api.auth_records())==['1001']
    try:api.config_path({'file':'../../etc/passwd'})
    except ValueError:pass
    else:raise AssertionError('Path traversal allowed')
    try:api.set_ports({'lanPort':80,'localPort':16060,'rtpStart':22000,'rtpEnd':22019})
    except ValueError:pass
    else:raise AssertionError('Invalid port accepted')
print('Backend checks passed: syntax, duplicate sections, credential edits, network, preservation, deletion, path and port validation')
