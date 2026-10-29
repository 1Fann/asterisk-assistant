import json
import os
from pathlib import Path
import secrets

os.umask(0o077)
base = Path('/etc/asterisk-app')
base.mkdir(exist_ok=True)
credential_file = base / 'accounts.json'
lan = Path('/etc/asterisk-app/lan-ip').read_text().strip()
if credential_file.exists():
    credentials = json.loads(credential_file.read_text())
else:
    credentials = {user: secrets.token_hex(16) for user in ('1001', '2001')}
    credential_file.write_text(json.dumps(credentials))
config = Path('/etc/asterisk')
backup = Path('/etc/asterisk-app/package-defaults')
backup.mkdir(exist_ok=True)

def write(name, content):
    target = config / name
    original = backup / name
    if target.exists() and not original.exists():
        original.write_bytes(target.read_bytes())
    target.write_text(content.strip() + '\n')
    os.chmod(target, 0o640)

write('asterisk.conf', '''
[directories]
astetcdir => /etc/asterisk
astmoddir => /usr/lib/aarch64-linux-gnu/asterisk/modules
astvarlibdir => /var/lib/asterisk
astdbdir => /var/lib/asterisk
astkeydir => /var/lib/asterisk
astdatadir => /usr/share/asterisk
astagidir => /usr/share/asterisk/agi-bin
astspooldir => /var/spool/asterisk
astrundir => /run/asterisk
astlogdir => /var/log/asterisk
[options]
verbose = 0
debug = 0
documentation_language = en_US
''')
write('modules.conf', '''
[modules]
autoload=no
load=res_sorcery_config.so
load=res_sorcery_memory.so
load=res_sorcery_astdb.so
load=res_sorcery_realtime.so
load=res_pjproject.so
load=res_pjsip.so
load=res_pjsip_authenticator_digest.so
load=res_pjsip_endpoint_identifier_user.so
load=res_pjsip_registrar.so
load=res_pjsip_session.so
load=res_pjsip_caller_id.so
load=res_pjsip_sdp_rtp.so
load=res_pjsip_outbound_authenticator_digest.so
load=res_pjsip_pubsub.so
load=res_pjsip_notify.so
load=res_pjsip_dtmf_info.so
load=chan_pjsip.so
load=res_rtp_asterisk.so
load=res_timing_timerfd.so
load=codec_ulaw.so
load=codec_alaw.so
load=codec_g722.so
load=bridge_simple.so
load=bridge_native_rtp.so
load=bridge_softmix.so
load=pbx_config.so
load=app_echo.so
load=app_dial.so
load=app_stack.so
load=res_pjsip_header_funcs.so
''')
write('rtp.conf', '''
[general]
rtpstart=22000
rtpend=22019
icesupport=no
''')
write('http.conf', '[general]\nenabled=no')
write('manager.conf', '[general]\nenabled=no')
write('cdr.conf', '[general]\nenable=no')
write('cel.conf', '[general]\nenable=no')
write('logger.conf', '''
[general]
dateformat=%F %T
[logfiles]
console => warning,error
messages => warning,error
''')
write('extensions.conf', '''
[general]
static=yes
writeprotect=yes
clearglobalvars=no
[iphone-test]
exten => 600,1,Answer()
 same => n,Wait(1)
 same => n,Echo()
 same => n,Hangup()
[gateway-test]
; Cellular routes are intentionally not configured during the LAN test.
''')
pjsip = f'''
[global]
type=global
user_agent=Redmi-LAN-PBX
endpoint_identifier_order=username

[transport-lan]
type=transport
protocol=udp
bind={lan}:16060

[transport-loopback]
type=transport
protocol=udp
bind=127.0.0.1:16060
'''
for user, transport, address, context in (
    ('1001', 'transport-lan', lan, 'iphone-test'),
    ('2001', 'transport-loopback', '127.0.0.1', 'gateway-test'),
):
    pjsip += f'''

[{user}]
type=endpoint
transport={transport}
context={context}
disallow=all
allow=ulaw,alaw,g722
auth=auth-{user}
aors={user}
direct_media=no
rtp_symmetric=yes
force_rport=yes
rewrite_contact=yes
media_address={address}
bind_rtp_to_media_address=yes
rtp_timeout=60
rtp_timeout_hold=300
allow_subscribe=no
dtmf_mode=rfc4733

[auth-{user}]
type=auth
auth_type=userpass
username={user}
password={credentials[user]}

[{user}]
type=aor
max_contacts=1
remove_existing=yes
minimum_expiration=60
default_expiration=300
maximum_expiration=3600
'''
write('pjsip.conf', pjsip)
print('configuration_ready=yes; accounts=1001,2001; echo_extension=600')

credential_file.unlink(missing_ok=True)
