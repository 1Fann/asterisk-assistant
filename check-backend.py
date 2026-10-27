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
    # Enabling IPv6 preserves credentials, the local gateway and the dialplan.
    (api.S/'lan-ipv6').write_text('2001:db8::10')
    # Documentation prefix is not globally routable, so use a synthetic global address in the fixture.
    (api.S/'lan-ipv6').write_text('2606:4700:1234::10')
    before=api.auth_records()['1001']['password'];dialplan=(api.C/'extensions.conf').read_bytes()
    api.save_account({'user':'2001','password':'test_only_gateway_123','role':'gateway'})
    api.set_public_ipv6({'enabled':True,'domain':'phone.example.com'})
    text=(api.C/'pjsip.conf').read_text();_,parts=api.blocks(text)
    endpoints={s['name']:s['fields'] for s in parts if s['fields'].get('type')=='endpoint'}
    assert endpoints['1001']['transport']=='transport-public-ipv6'
    assert endpoints['1001']['media_address']=='2606:4700:1234::10'
    assert endpoints['2001']['transport']=='transport-loopback'
    assert api.auth_records()['1001']['password']==before
    # save_account may create default app contexts; network changes must preserve their bytes.
    dialplan=(api.C/'extensions.conf').read_bytes()
    api.network();assert (api.C/'pjsip.conf').read_text().count('[transport-public-ipv6]')==1
    assert (api.C/'extensions.conf').read_bytes()==dialplan
    (api.S/'lan-ipv6').write_text('2606:4700:5678::20');api.network()
    assert 'bind=[2606:4700:5678::20]:16060' in (api.C/'pjsip.conf').read_text()
    (api.S/'lan-ipv6').write_text('');api.network()
    assert '[transport-public-ipv6]' not in (api.C/'pjsip.conf').read_text()
    assert 'media_address=192.0.2.10' in (api.C/'pjsip.conf').read_text()
    (api.S/'lan-ipv6').write_text('2606:4700:5678::20');api.network()
    api.set_ports({'lanPort':17060,'localPort':16060,'rtpStart':22000,'rtpEnd':22019});api.network()
    assert 'bind=[2606:4700:5678::20]:17060' in (api.C/'pjsip.conf').read_text()
    api.set_public_ipv6({'enabled':False,'domain':'phone.example.com'})
    assert '[transport-public-ipv6]' not in (api.C/'pjsip.conf').read_text()
    assert api.auth_records()['1001']['password']==before
    for data in ({'enabled':True,'domain':'sip:phone.example.com:15060'},{'enabled':'false','domain':'phone.example.com'}):
        try:api.set_public_ipv6(data)
        except ValueError:pass
        else:raise AssertionError('Invalid public network setting accepted')
print('Backend checks passed: syntax, duplicate sections, credential edits, network, preservation, deletion, path and port validation')
