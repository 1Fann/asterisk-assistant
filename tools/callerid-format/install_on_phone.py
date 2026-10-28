"""Run inside the assistant's chroot after staging the two public files in /tmp.

This targets the existing Groundwire incoming route, with no account changes.
"""
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys

sys.path.insert(0, '/opt/asterisk-app')
import api

WHEEL = 'phonenumberslite-9.0.42-py2.py3-none-any.whl'
SHA256 = '7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e'
UPLOAD = Path('/tmp/callerid-format-upload')
BUNDLE = Path('/usr/local/lib/asterisk-callerid')
CONFIG = Path('/etc/asterisk')
STATE = Path('/etc/asterisk-app')

if api.active_calls():
    raise SystemExit('Active call; nothing changed')
if not api.cli('core show uptime'):
    raise SystemExit('Asterisk is not responding; nothing changed')
if hashlib.sha256((UPLOAD/WHEEL).read_bytes()).hexdigest() != SHA256:
    raise SystemExit('Dependency checksum mismatch; nothing changed')
compile((UPLOAD/'callerid_format.py').read_text(), 'callerid_format.py', 'exec')
extension_path = CONFIG/'extensions.conf'
module_path = CONFIG/'modules.conf'
original = extension_path.read_text()
modules = module_path.read_text()
context_match = re.search(r'(?ms)^\[vsa-phone-local\]\s*\n(.*?)(?=^\[|\Z)', original)
if not context_match:
    raise SystemExit('Supported incoming route is not configured; nothing changed')
context = context_match.group(0)
hook = 'exten => 2001,1,AGI(/usr/local/lib/asterisk-callerid/callerid_format.py)'
already_hooked = hook in context
new_prefix = ('; Offline libphonenumber display formatting; the dialable identity stays intact.\n'
              + hook + '\n'
              ' same => n,Set(GLOBAL(VSA_LAST_IN_STAGE)=groundwire-check)')
if already_hooked:
    updated = original
elif 'exten => 2001,1,Set(VSA_FMT_NUM=${CALLERID(num)})' in context:
    start = original.index('exten => 2001,1,Set(VSA_FMT_NUM=${CALLERID(num)})', context_match.start())
    end_marker = ' same => n(fmt-ready),Set(GLOBAL(VSA_LAST_IN_STAGE)=groundwire-check)'
    end = original.index(end_marker, start) + len(end_marker)
    old_prefix = original[start:end]
    if 'Dial(' in old_prefix or len(old_prefix.splitlines()) > 15 or end > context_match.end():
        raise SystemExit('Unexpected incoming prefix; nothing changed')
    updated = original[:start] + new_prefix + original[end:]
else:
    basic = 'exten => 2001,1,Set(GLOBAL(VSA_LAST_IN_STAGE)=groundwire-check)'
    if basic not in context:
        raise SystemExit('Unsupported incoming route; nothing changed')
    start = original.index(basic, context_match.start())
    updated = original[:start] + new_prefix + original[start+len(basic):]
module_updated = modules
for module in ['res_speech.so', 'res_agi.so']:
    if not re.search(r'(?m)^\s*load\s*=\s*' + re.escape(module) + r'\s*$', module_updated):
        module_updated = module_updated.rstrip() + '\nload=' + module + '\n'
for name, data in [('before-international-callerid-extensions.conf', original),
                   ('before-international-callerid-modules.conf', modules)]:
    backup = STATE/name
    if backup.exists():
        if not already_hooked and backup.read_text() != data:
            raise SystemExit('Different previous backup exists; review before replacing it')
    else:
        api.write(backup, data)
BUNDLE.mkdir(parents=True, exist_ok=True)
os.chmod(BUNDLE, 0o755)
for name in [WHEEL, 'callerid_format.py']:
    target = BUNDLE/name
    shutil.copyfile(UPLOAD/name, target)
    os.chmod(target, 0o755 if name.endswith('.py') else 0o644)
    os.chown(target, 0, 0)
if not (BUNDLE/'settings.json').exists():
    (BUNDLE/'settings.json').write_text('{"default_region":"CN"}\n')
    os.chmod(BUNDLE/'settings.json', 0o644)
    os.chown(BUNDLE/'settings.json', 0, 0)
try:
    # AGI links to Asterisk's speech abstraction; no speech engine is configured.
    api.cli('module load res_speech.so')
    api.cli('module load res_agi.so')
    if not re.search(r'(?m)^res_agi\.so\s+.*Running', api.cli('module show like res_agi.so')):
        raise RuntimeError('AGI module is not running')
    if module_updated != modules:
        api.write(module_path, module_updated)
    if updated != original:
        api.write(extension_path, updated)
    api.cli('dialplan reload')
    plan = api.cli('dialplan show 2001@vsa-phone-local')
    if 'AGI(/usr/local/lib/asterisk-callerid/callerid_format.py)' not in plan:
        raise RuntimeError('Incoming formatter is not in the loaded dialplan')
    print('Installed offline international caller display formatting; backup saved')
    print('No SIP credentials, endpoints, caller number, or privacy rules changed')
except Exception:
    if extension_path.read_text() != original:
        api.write(extension_path, original)
    if module_path.read_text() != modules:
        api.write(module_path, modules)
    api.cli('dialplan reload')
    raise
