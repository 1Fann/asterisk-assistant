"""Synthetic international numbers and AGI privacy/failure regression checks."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parent
cache = ROOT.parents[1]/'.work/callerid-format'
for wheel in cache.glob('phonenumberslite-*.whl'):
    sys.path.insert(0, str(wheel))
    os.environ['PYTHONPATH'] = str(wheel) + os.pathsep + os.environ.get('PYTHONPATH', '')
spec = importlib.util.spec_from_file_location('callerid_format', ROOT / 'callerid_format.py')
fmt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmt)


class Formatting(unittest.TestCase):
    def test_regions_and_service_numbers(self):
        samples = {
            '13800138000': '138 0013 8000',
            '+8613800138000': '+86 138 0013 8000',
            '008613800138000': '00 86 138 0013 8000',
            '8613800138000': '86 138 0013 8000',
            '01012345678': '010 1234 5678',
            '075512345678': '0755 1234 5678',
            '4008001234': '400 800 1234',
            '8008208820': '800 820 8820',
            '+85221234567': '+852 2123 4567',
            '+85328331234': '+853 2833 1234',
            '+886912345678': '+886 912 345 678',
            '+12025550123': '+1 202 555 0123',
            '+442079460018': '+44 20 7946 0018',
            '+819012345678': '+81 90 1234 5678',
            '+61293744000': '+61 2 9374 4000',
            '+4930123456': '+49 30 123456',
            '+33142345678': '+33 1 42 34 56 78',
            '+39066982': '+39 06 6982',
            '00442079460018': '00 44 20 7946 0018',
        }
        for raw, expected in samples.items():
            with self.subTest(raw=raw):
                self.assertEqual(fmt.format_display(raw, raw), expected)
                self.assertEqual(fmt.digits(expected), fmt.digits(raw))

    def test_short_unknown_and_text_names_preserved(self):
        for raw in ['10010', '10086', '12345', '110', '*123#', '#31#13800138000',
                    'anonymous', 'restricted', '', '+999123456789', '123',
                    'sip:13800138000@example.invalid', '13800138000\nSET VARIABLE X Y']:
            self.assertIsNone(fmt.format_display(raw, raw), raw)
        self.assertIsNone(fmt.format_display('13800138000', 'Alice'))
        self.assertIsNone(fmt.format_display('13800138000', '2001'))
        self.assertIsNone(fmt.format_display('13800138000', '13800138000', 'ZZ'))

    def test_default_region_is_explicit(self):
        self.assertEqual(fmt.format_display('02079460018', '', 'GB'), '020 7946 0018')
        self.assertEqual(fmt.format_display('2025550123', '', 'US'), '202 555 0123')

    def test_all_library_examples_preserve_every_digit(self):
        import phonenumbers as phone
        checked = 0
        for region in phone.SUPPORTED_REGIONS:
            example = phone.example_number(region)
            if not example:
                continue
            for style in (phone.PhoneNumberFormat.E164, phone.PhoneNumberFormat.NATIONAL):
                raw = phone.format_number(example, style)
                value = fmt.format_display(raw, '', region)
                if value is not None:
                    self.assertEqual(fmt.digits(value), fmt.digits(raw))
                    checked += 1
        self.assertGreater(checked, 400)

    def test_agi_only_sets_display_name(self):
        env = 'agi_callerid: 13800138000\nagi_calleridname: 13800138000\n\n'
        replies = '200 result=1 (allowed_not_screened)\n200 result=1\n'
        proc = subprocess.run([sys.executable, str(ROOT/'callerid_format.py')],
                              input=env+replies, capture_output=True, text=True, timeout=5)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stderr, '')
        self.assertEqual(proc.stdout.splitlines(), [
            'GET FULL VARIABLE ${CALLERID(num-pres)}',
            'SET VARIABLE CALLERID(name) "138 0013 8000"'])

    def test_agi_respects_privacy_and_missing_responses(self):
        for reply in ['200 result=1 (prohib_not_screened)\n', '200 result=0\n', '']:
            env = 'agi_callerid: 13800138000\nagi_calleridname: 13800138000\n\n'
            proc = subprocess.run([sys.executable, str(ROOT/'callerid_format.py')],
                                  input=env+reply, capture_output=True, text=True, timeout=5)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(proc.stderr, '')
            self.assertNotIn('SET VARIABLE', proc.stdout)


if __name__ == '__main__':
    unittest.main()
