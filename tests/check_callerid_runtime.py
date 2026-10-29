"""Isolated App deployment/configuration checks; no device or real calls."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
RUNTIME=ROOT/'assets/runtime'
sys.path.insert(0,str(RUNTIME))
import callerid
spec=importlib.util.spec_from_file_location('fixture_api',RUNTIME/'api.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
api.os.chown=lambda *args:None


class AppFormatting(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        api.C=self.root/'config';api.S=self.root/'state';api.C.mkdir();api.S.mkdir()
        callerid.BUNDLE=self.root/'bundle';callerid.RUNTIME=RUNTIME
        api.cli=lambda cmd:''
        (api.C/'pjsip.conf').write_text('''; preserve authentication and client settings
[2001]
type=endpoint
transport=transport-loopback
context=gateway-test
trust_id_inbound=yes
[auth-2001]
type=auth
password=synthetic-secret
[1001]
type=endpoint
transport=transport-lan
context=clients
''')
        (api.C/'extensions.conf').write_text('[gateway-test]\nexten => 2001,1,Hangup()\n[clients]\nexten => 600,1,Echo()\n')
        (api.C/'modules.conf').write_text('[modules]\nautoload=no\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_fresh_default_and_preservation(self):
        original=(api.C/'extensions.conf').read_text()
        result=callerid.prepare(api)
        self.assertTrue(result['enabled']);self.assertFalse(result['pending'])
        self.assertEqual(result['defaultRegion'],'CN')
        text=(api.C/'pjsip.conf').read_text()
        self.assertIn('password=synthetic-secret',text)
        self.assertIn('transport=transport-lan\ncontext=clients',text)
        self.assertIn(original.strip(),(api.C/'extensions.conf').read_text())
        self.assertIn('Goto(gateway-test,${EXTEN},1)',(api.C/'extensions.conf').read_text())
        self.assertTrue((callerid.BUNDLE/callerid.WHEEL).is_file())
        self.assertIn('load=func_callerid.so',(api.C/'modules.conf').read_text())
        self.assertIn('load=res_pjsip_caller_id.so',(api.C/'modules.conf').read_text())

    def test_live_missing_identity_module_is_loaded_before_success(self):
        loaded={'res_agi.so'}
        def command(cmd):
            if cmd=='core show uptime':return 'up'
            if cmd=='core show channels count':return '0 active calls'
            if cmd.startswith('module load '):loaded.add(cmd.split()[-1]);return ''
            if cmd.startswith('module show like '):return 'Running' if cmd.split()[-1] in loaded else ''
            return ''
        api.cli=command
        self.assertFalse(callerid.prepare(api)['pending'])
        self.assertIn('res_pjsip_caller_id.so',loaded)

    def test_idempotent_and_ui_settings(self):
        callerid.prepare(api)
        before={p.name:p.read_bytes() for p in api.C.iterdir()}
        callerid.prepare(api)
        self.assertEqual(before,{p.name:p.read_bytes() for p in api.C.iterdir()})
        result=callerid.prepare(api,{'enabled':False,'defaultRegion':'gb'})
        self.assertFalse(result['enabled']);self.assertEqual(result['defaultRegion'],'GB')
        public=json.loads((callerid.BUNDLE/'settings.json').read_text())
        self.assertEqual(public,{'enabled':False,'default_region':'GB'})
        self.assertEqual(before,{p.name:p.read_bytes() for p in api.C.iterdir()})

    def test_busy_or_unknown_calls_defer_without_writes(self):
        for summary in ['1 active calls','unknown']:
            api.cli=lambda cmd: 'up' if cmd=='core show uptime' else summary
            result=callerid.prepare(api)
            self.assertTrue(result['pending']);self.assertFalse(callerid.BUNDLE.exists())
            with self.assertRaises(ValueError):callerid.prepare(api,{'enabled':True,'defaultRegion':'CN'})

    def test_existing_standalone_hook_is_taken_over(self):
        legacy='[gateway-test]\nexten => 2001,1,'+callerid.HOOK+'\n same => n,Hangup()\n'
        (api.C/'extensions.conf').write_text(legacy)
        callerid.BUNDLE.mkdir()
        (callerid.BUNDLE/'settings.json').write_text('{"default_region":"HK"}')
        original=(api.C/'pjsip.conf').read_bytes()
        result=callerid.prepare(api)
        self.assertEqual((api.C/'extensions.conf').read_text(),legacy)
        self.assertEqual((api.C/'pjsip.conf').read_bytes(),original)
        self.assertEqual(result['defaultRegion'],'HK')

    def test_invalid_settings_and_context_rejected(self):
        for data in [{'enabled':True,'defaultRegion':'ZZ'},{'enabled':'false','defaultRegion':'CN'},
                     {'enabled':True,'defaultRegion':'CN; bad'}]:
            with self.assertRaises(ValueError):callerid.prepare(api,data)
        p=api.C/'pjsip.conf';p.write_text(p.read_text().replace('context=gateway-test','context=missing'))
        with self.assertRaises(ValueError):callerid.prepare(api)
        self.assertFalse(callerid.BUNDLE.exists())

    def test_migration_defers(self):
        (api.S/'callerid-defer').touch()
        self.assertTrue(callerid.prepare(api)['pending'])
        self.assertFalse(callerid.BUNDLE.exists())

    def test_corrupt_dependency_refused(self):
        fixture=self.root/'bad-runtime';fixture.mkdir()
        (fixture/callerid.WHEEL).write_bytes(b'wrong')
        callerid.RUNTIME=fixture
        with self.assertRaises(ValueError):callerid.prepare(api)
        self.assertFalse(callerid.BUNDLE.exists())


if __name__=='__main__':unittest.main()
