"""Exercise AGI in isolated Local channels, without SIP or cellular calls."""
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, '/opt/asterisk-app')
import api

p = Path('/etc/asterisk/extensions.conf')
original = p.read_text()
context = 'vsa-display-format-selftest'
if '[' + context + ']' in original or api.active_calls():
    raise SystemExit('Test context already exists or a call is active')
load_cli = '0 modules loaded' in api.cli('module show like res_clioriginate.so')
if load_cli:
    api.cli('module load res_clioriginate.so')
if 'No such command' in api.cli('core show help channel originate'):
    raise SystemExit('Internal channel test command unavailable')
cases = [
    ('13800138000', '13800138000', 'allowed_not_screened', '138 0013 8000'),
    ('01012345678', '01012345678', 'allowed_not_screened', '010 1234 5678'),
    ('4008001234', '4008001234', 'allowed_not_screened', '400 800 1234'),
    ('+442079460018', '+442079460018', 'allowed_not_screened', '+44 20 7946 0018'),
    ('008613800138000', '008613800138000', 'allowed_not_screened', '00 86 138 0013 8000'),
    ('+12025550123', '+12025550123', 'allowed_not_screened', '+1 202 555 0123'),
    ('10010', '10010', 'allowed_not_screened', '10010'),
    ('13800138000', 'Alice', 'allowed_not_screened', 'Alice'),
    ('13800138000', '13800138000', 'prohib_not_screened', '13800138000'),
]
text = '\n[' + context + ']\n'
for index, (number, name, privacy, expected) in enumerate(cases):
    text += f'''exten => test{index},1,Set(CALLERID(num)={number})
 same => n,Set(CALLERID(name)={name})
 same => n,Set(CALLERID(num-pres)={privacy})
 same => n,AGI(/usr/local/lib/asterisk-callerid/callerid_format.py)
 same => n,GotoIf($["${{CALLERID(name)}}"="{expected}"]?numcheck:failedname)
 same => n(numcheck),GotoIf($["${{CALLERID(num)}}"="{number}"]?privacycheck:failednumber)
 same => n(privacycheck),GotoIf($["${{CALLERID(num-pres)}}"="{privacy}"]?statuscheck:failedprivacy)
 same => n(statuscheck),GotoIf($["${{AGISTATUS}}"="SUCCESS"]?passed:failedstatus)
 same => n(passed),Set(GLOBAL(VSA_FORMAT_SELFTEST)=PASS)
 same => n,Hangup()
 same => n(failedname),Set(GLOBAL(VSA_FORMAT_SELFTEST)=FAILNAME)
 same => n,Hangup()
 same => n(failednumber),Set(GLOBAL(VSA_FORMAT_SELFTEST)=FAILNUMBER)
 same => n,Hangup()
 same => n(failedprivacy),Set(GLOBAL(VSA_FORMAT_SELFTEST)=FAILPRIVACY)
 same => n,Hangup()
 same => n(failedstatus),Set(GLOBAL(VSA_FORMAT_SELFTEST)=FAILSTATUS)
 same => n,Hangup()
'''
try:
    api.write(p, original.rstrip() + '\n' + text)
    api.cli('dialplan reload')
    for index in range(len(cases)):
        api.cli('dialplan set global VSA_FORMAT_SELFTEST PENDING')
        start = time.monotonic()
        api.cli(f'channel originate Local/test{index}@{context}/n application Wait 1')
        result = 'PENDING'
        for _ in range(30):
            globals_ = api.cli('dialplan show globals')
            match = re.search(r'VSA_FORMAT_SELFTEST\s*=\s*(PASS|FAIL[A-Z]*|PENDING)', globals_)
            result = match.group(1) if match else 'MISSING'
            if result != 'PENDING':
                break
            time.sleep(0.1)
        elapsed = time.monotonic()-start
        print(f'internal-case-{index+1}: {result}; {elapsed:.3f}s', flush=True)
        if result != 'PASS':
            raise SystemExit('Internal AGI verification failed')
finally:
    # Do not overwrite any concurrent configuration edits.
    current = p.read_text()
    api.write(p, current.split('\n['+context+']\n',1)[0].rstrip()+'\n')
    api.cli('dialplan reload')
    api.cli('dialplan set global VSA_FORMAT_SELFTEST DONE')
    if load_cli:
        api.cli('module unload res_clioriginate.so')
print('All 9 internal cases passed; temporary context removed; no real calls made')
