"""App-owned offline display-name formatter deployment; never edits credentials."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys

VERSION = '1.1.2'
WHEEL = 'phonenumberslite-9.0.42-py2.py3-none-any.whl'
WHEEL_SHA = '7ae0a97b12e9f0749e7bed2c9c3da4df43648ea5ba021de86b36088d98a0915e'
BUNDLE = Path('/usr/local/lib/asterisk-callerid')
RUNTIME = Path(__file__).resolve().parent
BEGIN = '; BEGIN APP CALLERID FORMAT'
END = '; END APP CALLERID FORMAT'
HOOK = 'AGI(/usr/local/lib/asterisk-callerid/callerid_format.py)'


def settings(api):
    path = api.S/'callerid-format.json'
    legacy = BUNDLE/'settings.json'
    value = json.loads(path.read_text()) if path.exists() else (
        json.loads(legacy.read_text()) if legacy.exists() else {})
    return {'enabled': value.get('enabled', True),
            'default_region': value.get('default_region', 'CN'),
            'routes': value.get('routes', {}), 'version': value.get('version', '')}


def describe(api, pending=False):
    value = settings(api)
    installed = (BUNDLE/WHEEL).is_file() and (BUNDLE/'callerid_format.py').is_file()
    return {'enabled': bool(value['enabled']), 'defaultRegion': value['default_region'],
            'installed': installed, 'pending': pending or value['version'] != VERSION,
            'version': VERSION, 'regions': 245}


def public_file(path, binary, mode):
    if path.exists() and path.read_bytes() == binary:
        return
    tmp = path.with_name('.'+path.name+'.tmp')
    with tmp.open('wb') as stream:
        stream.write(binary); stream.flush(); os.fsync(stream.fileno())
    os.chmod(tmp, mode); os.chown(tmp, 0, 0); os.replace(tmp, path)


def validate_region(region):
    if not isinstance(region, str) or not re.fullmatch(r'[A-Za-z]{2}', region):
        raise ValueError('默认地区须为两位代码，例如 CN、HK、US')
    sys.path.insert(0, str(RUNTIME/WHEEL))
    import phonenumbers
    if region.upper() not in phonenumbers.SUPPORTED_REGIONS:
        raise ValueError('号码库不支持这个地区代码')
    return region.upper()


def plan(api, config):
    """Wrap authenticated loopback gateway contexts; original priorities survive."""
    original = (api.C/'extensions.conf').read_text()
    pjsip = (api.C/'pjsip.conf').read_text()
    prefix, sections = api.blocks(pjsip)
    routes = dict(config['routes'])
    contexts = {s['name']: s['body'] for s in api.blocks(original)[1]}
    for section in sections:
        fields = section['fields']
        if fields.get('type') != 'endpoint' or fields.get('transport') != 'transport-loopback':
            continue
        context = fields.get('context', '')
        if context in routes.values():
            continue
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,79}', context) or context not in contexts:
            raise ValueError('网关来电上下文无效，未自动修改拨号规则')
        # Take over the previous standalone hook in place without double execution.
        if HOOK in contexts[context]:
            continue
        wrapper = 'app-callerid-'+hashlib.sha256(context.encode()).hexdigest()[:12]
        if wrapper in contexts and wrapper not in routes.values():
            raise ValueError('发现重名自定义上下文，未覆盖')
        routes[context] = wrapper
        section['body'] = api.field(section['body'], 'context', wrapper)
    block = '\n'+BEGIN+'\n'
    for original_context, wrapper in sorted(routes.items()):
        if not re.fullmatch(r'[A-Za-z0-9_.-]{1,79}', original_context) or not re.fullmatch(r'app-callerid-[a-f0-9]{12}', wrapper):
            raise ValueError('号码分段路由配置无效')
        block += ('['+wrapper+']\nexten => _.,1,'+HOOK+'\n'
                  ' same => n,Goto('+original_context+',${EXTEN},1)\n')
    block += END+'\n'
    existing = re.search(r'(?ms)^'+re.escape(BEGIN)+r'\n.*?^'+re.escape(END)+r'\n?', original)
    if existing:
        updated = original[:existing.start()] + block.lstrip('\n') + original[existing.end():]
    elif routes:
        updated = original.rstrip()+'\n'+block
    else:
        updated = original
    return updated, prefix+''.join(s['header']+s['body'] for s in sections), routes


def prepare(api, desired=None):
    config = settings(api)
    if desired is not None:
        if not isinstance(desired.get('enabled'), bool):
            raise ValueError('号码分段开关无效')
        config['enabled'] = desired['enabled']
        config['default_region'] = validate_region(desired.get('defaultRegion', 'CN'))
    if (api.S/'callerid-defer').exists():
        if desired is not None: raise ValueError('正在迁移，请稍后设置')
        return describe(api, True)
    running = bool(api.cli('core show uptime'))
    if running:
        calls = re.search(r'(\d+) active calls', api.cli('core show channels count'))
        if not calls or int(calls.group(1)):
            if desired is not None: raise ValueError('通话中或状态尚未确认，请稍后设置')
            return describe(api, True)
    else:
        pid = Path('/run/asterisk/asterisk.pid')
        if pid.exists() and Path('/proc/'+pid.read_text().strip()+'/comm').exists():
            if desired is not None: raise ValueError('服务器响应异常，请稍后设置')
            return describe(api, True)
    binary = (RUNTIME/WHEEL).read_bytes()
    if hashlib.sha256(binary).hexdigest() != WHEEL_SHA:
        raise ValueError('内置号码库校验失败，请重新安装官方签名 APK')
    script = (RUNTIME/'callerid-format.py').read_bytes()
    compile(script, 'callerid-format.py', 'exec')
    # Plan and validate all changes before writing any server configuration.
    ext, pjsip, routes = plan(api, config)
    modules = (api.C/'modules.conf').read_text()
    new_modules = modules
    for name in ['res_speech.so', 'res_agi.so', 'func_callerid.so']:
        if not re.search(r'(?m)^\s*load\s*=\s*'+re.escape(name)+r'\s*$', new_modules):
            new_modules = new_modules.rstrip()+'\nload='+name+'\n'
    BUNDLE.mkdir(parents=True, exist_ok=True); os.chmod(BUNDLE, 0o755)
    public_file(BUNDLE/WHEEL, binary, 0o644)
    public_file(BUNDLE/'callerid_format.py', script, 0o755)
    public_settings = {k: config[k] for k in ('enabled', 'default_region')}
    public_file(BUNDLE/'settings.json', (json.dumps(public_settings)+'\n').encode(), 0o644)
    if running:
        for name in ['res_speech.so', 'res_agi.so', 'func_callerid.so']:
            if 'Running' not in api.cli('module show like '+name): api.cli('module load '+name)
        if 'Running' not in api.cli('module show like res_agi.so'):
            raise ValueError('号码分段模块加载失败，请重启服务器后重试')
    changed = []
    for name, content in [('modules.conf', new_modules), ('extensions.conf', ext), ('pjsip.conf', pjsip)]:
        path = api.C/name
        if path.read_text() != content:
            backup = api.S/('before-app-callerid-'+name)
            if not backup.exists(): api.write(backup, path.read_text())
            api.write(path, content); changed.append(name)
    config.update(routes=routes, version=VERSION)
    state = json.dumps(config, sort_keys=True)+'\n'
    if not (api.S/'callerid-format.json').exists() or (api.S/'callerid-format.json').read_text() != state:
        api.write(api.S/'callerid-format.json', state)
    if running:
        if 'extensions.conf' in changed: api.cli('dialplan reload')
        if 'pjsip.conf' in changed: api.cli('module reload res_pjsip.so')
    return describe(api)
