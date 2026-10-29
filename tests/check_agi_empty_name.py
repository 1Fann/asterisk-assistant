"""Regression checks for Asterisk's empty-name AGI sentinel, using fake data."""
import io
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

RUNTIME = Path(__file__).resolve().parents[1] / 'assets/runtime'


class AgiNames(unittest.TestCase):
    def run_agi(self, name_reply, presentation='allowed_not_screened'):
        module = runpy.run_path(str(RUNTIME / 'callerid-format.py'))
        main = module['main']
        with tempfile.TemporaryDirectory() as directory:
            main.__globals__['BUNDLE'] = Path(directory)
            source = io.StringIO('agi_callerid: 13800138000\nagi_calleridname: unknown\n\n'
                                 + '200 result=1 (' + presentation + ')\n'
                                 + name_reply + '\n200 result=1\n')
            sink = io.StringIO()
            with patch('sys.stdin', source), patch('sys.stdout', sink):
                main()
            return sink.getvalue()

    def test_empty_name_sentinel_gets_formatted(self):
        for reply in ['200 result=1 ()', '200 result=0']:
            result = self.run_agi(reply)
            self.assertIn('GET FULL VARIABLE ${CALLERID(name)}\n', result)
            self.assertIn('SET VARIABLE CALLERID(name) "138 0013 8000"', result)

    def test_real_unknown_contact_name_is_preserved(self):
        self.assertNotIn('SET VARIABLE', self.run_agi('200 result=1 (unknown)'))

    def test_privacy_restriction_prevents_lookup_and_formatting(self):
        result = self.run_agi('200 result=1 ()', 'prohib_not_screened')
        self.assertNotIn('${CALLERID(name)}', result)
        self.assertNotIn('SET VARIABLE', result)

    def test_unexpected_agi_reply_fails_without_replacing_name(self):
        with self.assertRaises(RuntimeError):
            self.run_agi('510 Invalid command')


if __name__ == '__main__':
    unittest.main()
