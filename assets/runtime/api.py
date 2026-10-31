import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import runpy
import secrets
import subprocess
import sys
from types import SimpleNamespace

os.umask(0o077)
C=Path('/etc/asterisk')
S=Path('/etc/asterisk-app')
ALLOWED={'pjsip.conf','extensions.conf','rtp.conf','modules.conf','logger.conf'}

def cli(command):
    result=subprocess.run(['/usr/sbin/asterisk','-rx',command],capture_output=True,text=True,timeout=12)
    return result.stdout if result.returncode==0 else ''

def blocks(text):
    matches=list(re.finditer(r'(?m)^\[([^\]\r\n]+)\][^\r\n]*(?:\r?\n|$)',text))
    out=[]
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(text)
        body=text[m.end():end]
        fields={}
        for line in body.splitlines():
            if line.lstrip().startswith((';','#')) or '=' not in line: continue
            key,value=line.split('=',1)
            fields[key.strip()]=value.strip()
        out.append({'name':m.group(1),'header':m.group(0),'body':body,'fields':fields})
    return text[:matches[0].start()] if matches else text,out

def field(body,key,value):
    pattern=r'(?m)^([ \t]*'+re.escape(key)+r'\s*=\s*)[^\r\n]*'
    if re.search(pattern,body): return re.sub(pattern,lambda m:m.group(1)+str(value),body)
    return body.rstrip()+'\n'+key+'='+str(value)+'\n\n'

def write(path,text):
    temporary=path.with_name('.'+path.name+'.tmp')
    with temporary.open('w',encoding='utf-8') as stream:
        stream.write(text);stream.flush();os.fsync(stream.fileno())
    os.chmod(temporary,0o640)
    os.chown(temporary,0,3003)
    os.replace(temporary,path)
    (S/'selftest-passed').unlink(missing_ok=True)

def auth_records(text=None):
    _,sections=blocks(text if text is not None else (C/'pjsip.conf').read_text())
    result={}
    endpoints={s['name']:s for s in sections if s['fields'].get('type')=='endpoint'}
    for s in sections:
        f=s['fields']
        if f.get('type')=='auth' and f.get('username'):
            user=f['username']; ep=endpoints.get(user,{'fields':{}})['fields']
            result[user]={'user':user,'password':f.get('password',''),'authSection':s['name'],
                'role':'gateway' if ep.get('transport')=='transport-loopback' else 'client',
                'editable':s['name']=='auth-'+user and user in endpoints}
    return result

def ports():
    _,sections=blocks((C/'pjsip.conf').read_text())
    by_name={s['name']:s['fields'] for s in sections}
    def port(name,default):
        try:return int(by_name[name]['bind'].rsplit(':',1)[1])
        except (ValueError,KeyError):return default
    rtp=(C/'rtp.conf').read_text()
    def value(name,default):
        m=re.search(r'(?m)^\s*'+name+r'\s*=\s*(\d+)',rtp)
        return int(m.group(1)) if m else default
    return {'lanPort':port('transport-lan',16060),'localPort':port('transport-loopback',16060),
            'rtpStart':value('rtpstart',22000),'rtpEnd':value('rtpend',22019)}

def public_accounts():
    contacts=cli('pjsip show contacts')
    result=[]
    for user,record in sorted(auth_records().items()):
        registered=bool(re.search(r'Contact:\s+'+re.escape(user)+r'/',contacts))
        result.append({'user':user,'role':record['role'],'editable':record['editable'],
                       'registered':registered,'contactState':'已登记（未启用在线探测）' if registered else '未登记'})
    return result

def active_calls():
    text=cli('core show channels count')
    m=re.search(r'(\d+) active calls',text)
    return int(m.group(1)) if m else 0

def callerid_state(update=False, desired=None):
    import callerid
    state=SimpleNamespace(C=C,S=S,cli=cli,blocks=blocks,field=field,write=write)
    return callerid.prepare(state,desired) if update else callerid.describe(state)

def status():
    try:cid=callerid_state(True)
    except Exception as error:
        cid=callerid_state();cid.update(pending=True,warning=str(error) if isinstance(error,ValueError) else '号码分段准备失败，请刷新重试')
    uptime=cli('core show uptime')
    version=subprocess.run(['/usr/sbin/asterisk','-V'],capture_output=True,text=True,timeout=8).stdout.strip()
    return {'ok':True,'installed':True,'running':bool(uptime),'version':version,
            'ip':(S/'lan-ip').read_text().strip(),'accounts':public_accounts(),'activeCalls':active_calls(),
            'ports':ports(),'uptime':uptime.strip(),'legacyFound':len(sys.argv)>2 and sys.argv[2]=='1',
            'autostart':len(sys.argv)>3 and sys.argv[3]=='1',
            'legacyCleaned':len(sys.argv)>4 and sys.argv[4]=='1',
            'migrationPending':(S/'import-check/pjsip.conf').exists(),
            'selfTestPassed':(S/'selftest-passed').exists(),
            'publicIpv6':public_ipv6(), 'ipv6':read_ipv6(), 'callerId':cid}

def public_ipv6():
    path=S/'public-ipv6.json'
    return json.loads(path.read_text()) if path.exists() else {'enabled':False,'domain':''}

def read_ipv6():
    path=S/'lan-ipv6'
    value=path.read_text().strip() if path.exists() else ''
    try:
        address=ipaddress.IPv6Address(value)
        return str(address) if address in ipaddress.IPv6Network('2000::/3') else ''
    except ValueError:return ''

def set_public_ipv6(data):
    if active_calls():raise ValueError('当前存在通话，请挂断后修改网络设置')
    enabled=data.get('enabled');domain=data.get('domain','').strip().lower().rstrip('.')
    if not isinstance(enabled,bool):raise ValueError('网络开关无效')
    if domain and (len(domain)>253 or not all(re.fullmatch(r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?',p) for p in domain.split('.'))):
        raise ValueError('请填写完整域名，不含 sip:、端口或路径')
    if enabled and (not domain or '.' not in domain):raise ValueError('请填写 DDNS 完整域名')
    if enabled and not read_ipv6():raise ValueError('Wi-Fi 暂无唯一可用的非临时公网 IPv6')
    backup=S/'before-public-ipv6.conf'
    if not backup.exists():write(backup,(C/'pjsip.conf').read_text())
    write(S/'public-ipv6.json',json.dumps({'enabled':enabled,'domain':domain}))
    network()
    return {'ok':True,'message':'IPv6 / DDNS 设置已保存，需重启服务生效'}

def network():
    ip=(S/'lan-ip').read_text().strip()
    text=(C/'pjsip.conf').read_text(); prefix,sections=blocks(text)
    old_ip=None
    for s in sections:
        if s['name']=='transport-lan':
            bind=s['fields'].get('bind','')
            if ':' in bind:
                old_ip,port=bind.rsplit(':',1)
                s['body']=field(s['body'],'bind',ip+':'+port)
    if old_ip:
        for s in sections:
            if s['fields'].get('media_address')==old_ip:
                s['body']=field(s['body'],'media_address',ip)
    public=public_ipv6();ipv6=read_ipv6();enabled=public['enabled'] and bool(ipv6)
    # Managed public clients use IPv6 for both signaling and RTP; the local gateway stays IPv4.
    if public['enabled'] or any(s['name']=='transport-public-ipv6' for s in sections):
        port=ports()['lanPort']
        sections=[s for s in sections if s['name']!='transport-public-ipv6']
        for s in sections:
            f=s['fields']
            if f.get('type')=='endpoint' and f.get('transport') in ('transport-lan','transport-public-ipv6'):
                for key,value in {'transport':'transport-public-ipv6' if enabled else 'transport-lan',
                    'media_address':ipv6 if enabled else ip,'bind_rtp_to_media_address':'yes',
                    'rtp_ipv6':'yes' if enabled else 'no'}.items():s['body']=field(s['body'],key,value)
        if enabled:
            # blocks() retains separator newlines in the previous section body.
            # Replacing this generated tail must not append another separator on
            # every recovery, otherwise unchanged network preparation never stabilizes.
            if sections:sections[-1]['body']=sections[-1]['body'].rstrip('\r\n')+'\n'
            else:prefix=prefix.rstrip('\r\n')+'\n' if prefix else ''
            sections.append({'header':'\n[transport-public-ipv6]\n','body':f'type=transport\nprotocol=udp\nbind=[{ipv6}]:{port}\n'})
    updated=prefix+''.join(s['header']+s['body'] for s in sections)
    if updated!=text:write(C/'pjsip.conf',updated)
    return {'ok':True}

def reload_config():
    output=cli('module reload res_pjsip.so')
    if 'reloaded successfully' not in output:raise ValueError('配置已保存，需启动或重启服务后生效')

def account_blocks(user,password,role,ip):
    gateway=role=='gateway'; transport='transport-loopback' if gateway else 'transport-lan'
    context='app-gateway' if gateway else 'app-users'; address='127.0.0.1' if gateway else ip
    ipv6=read_ipv6() if public_ipv6()['enabled'] and not gateway else ''
    if ipv6:transport='transport-public-ipv6';address=ipv6
    return f'''
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
rtp_ipv6={'yes' if ipv6 else 'no'}
allow_subscribe=no
dtmf_mode=rfc4733

[auth-{user}]
type=auth
auth_type=userpass
username={user}
password={password}

[{user}]
type=aor
max_contacts=1
remove_existing=yes
default_expiration=300
minimum_expiration=60
maximum_expiration=3600
'''

def save_account(data):
    user=data.get('user',''); password=data.get('password',''); role=data.get('role','client')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,32}',user):raise ValueError('账号只支持字母、数字、下划线和短横线')
    if role not in ('client','gateway'):raise ValueError('账号类型无效')
    records=auth_records(); old=records.get(user)
    if old and not old['editable']:raise ValueError('此账号使用自定义配置，请使用高级编辑')
    if not password and old:password=old['password']
    if not re.fullmatch(r'[A-Za-z0-9_-]{16,64}',password):raise ValueError('密码需16–64位字母、数字、下划线或短横线')
    text=(C/'pjsip.conf').read_text(); prefix,sections=blocks(text)
    if old and old['role']==role:
        for s in sections:
            if s['name']==old['authSection'] and s['fields'].get('type')=='auth':s['body']=field(s['body'],'password',password)
        updated=prefix+''.join(s['header']+s['body'] for s in sections)
    else:
        if active_calls():raise ValueError('当前存在通话，请挂断后修改账号类型')
        updated=prefix+''.join(s['header']+s['body'] for s in sections if s['name'] not in (user,'auth-'+user))
        updated+=account_blocks(user,password,role,(S/'lan-ip').read_text().strip())
        ext=(C/'extensions.conf').read_text()
        if '[app-users]' not in ext:ext+='\n[app-users]\nexten => 600,1,Answer()\n same => n,Wait(1)\n same => n,Echo()\n same => n,Hangup()\n\n[app-gateway]\n'
        write(C/'extensions.conf',ext);cli('dialplan reload')
    write(C/'pjsip.conf',updated)
    if cli('core show uptime'):reload_config()
    return {'ok':True,'message':'账号已保存'}

def delete_account(data):
    if active_calls():raise ValueError('当前存在通话，请挂断后删除账号')
    user=data.get('user',''); record=auth_records().get(user)
    if not record or not record['editable']:raise ValueError('账号不存在或使用自定义配置')
    prefix,sections=blocks((C/'pjsip.conf').read_text())
    write(C/'pjsip.conf',prefix+''.join(s['header']+s['body'] for s in sections if s['name'] not in (user,record['authSection'])))
    if cli('core show uptime'):reload_config()
    return {'ok':True,'message':'账号已删除'}

def config_path(data):
    name=data.get('file','')
    if name not in ALLOWED:raise ValueError('不允许编辑该文件')
    return C/name

def set_ports(data):
    if active_calls():raise ValueError('当前存在通话，请挂断后更改端口')
    lan=int(data['lanPort']);local=int(data['localPort']);start=int(data['rtpStart']);end=int(data['rtpEnd'])
    if not all(1024<=p<=65535 for p in (lan,local,start,end)) or end<=start or end-start>10000:raise ValueError('端口范围无效')
    text=(C/'pjsip.conf').read_text();prefix,sections=blocks(text)
    for s in sections:
        if s['name']=='transport-lan':s['body']=field(s['body'],'bind',(S/'lan-ip').read_text().strip()+':'+str(lan))
        if s['name']=='transport-loopback':s['body']=field(s['body'],'bind','127.0.0.1:'+str(local))
    write(C/'pjsip.conf',prefix+''.join(s['header']+s['body'] for s in sections))
    rtp=(C/'rtp.conf').read_text();rtp=field(field(rtp,'rtpstart',start),'rtpend',end);write(C/'rtp.conf',rtp)
    return {'ok':True,'message':'端口已保存，正在重启'}

def migration_verify():
    original=(S/'import-check/pjsip.conf').read_text()
    auth_before={u:r['password'] for u,r in auth_records(original).items()}
    auth_after={u:r['password'] for u,r in auth_records().items()}
    preserved=auth_before==auth_after and bool(auth_before)
    dialplan=(S/'import-check/extensions.conf').read_bytes()==(C/'extensions.conf').read_bytes()
    rtp=(S/'import-check/rtp.conf').read_bytes()==(C/'rtp.conf').read_bytes()
    if not (preserved and dialplan and rtp):raise ValueError('迁移校验失败，旧部署尚未删除')
    return {'ok':True,'accountsPreserved':preserved,'dialplanPreserved':dialplan,'rtpPreserved':rtp}

def main(action,data):
    if action=='initialize':
        if not (S/'initialized').exists():
            runpy.run_path('/opt/asterisk-app/fresh-config.py',run_name='__main__')
            (S/'initialized').touch()
        callerid_state(True)
        return {'ok':True}
    if action=='status':return status()
    if action=='logs':
        path=Path('/var/log/asterisk/messages')
        lines=path.read_text(errors='replace').splitlines()[-200:] if path.exists() else []
        lines=[line for line in lines if not re.search(r'password|authorization|secret|nonce|digest|credential',line,re.I)]
        return {'ok':True,'content':'\n'.join(lines[-80:]) or '暂无运行日志'}
    if action=='accounts':return {'ok':True,'accounts':public_accounts()}
    if action=='credentials':
        record=auth_records().get(data.get('user',''))
        if not record:raise ValueError('账号不存在')
        return {'ok':True,'user':record['user'],'password':record['password'],'role':record['role']}
    if action=='save_account':return save_account(data)
    if action=='delete_account':return delete_account(data)
    if action=='set_ports':return set_ports(data)
    if action=='set_public_ipv6':return set_public_ipv6(data)
    if action=='set_callerid':
        result=callerid_state(True,data)
        return {'ok':True,'callerId':result,'message':'号码分段设置已保存并生效'}
    if action=='network':return network()
    if action=='read_file':return {'ok':True,'content':config_path(data).read_text()}
    if action=='save_file':
        if active_calls():raise ValueError('当前存在通话，请稍后保存配置')
        path=config_path(data); content=data.get('content','')
        if len(content.encode())>262144 or '\x00' in content:raise ValueError('配置内容无效或过大')
        backup=S/('backup-'+path.name);backup.write_bytes(path.read_bytes())
        write(path,content)
        return {'ok':True,'message':'配置已保存，请重启服务应用'}
    if action=='restore_file':
        if active_calls():raise ValueError('当前存在通话，请稍后恢复配置')
        path=config_path(data); backup=S/('backup-'+path.name)
        if not backup.exists():raise ValueError('没有上次保存前的备份')
        write(path,backup.read_text());return {'ok':True,'message':'已恢复，请重启服务'}
    if action=='migration_verify':return migration_verify()
    if action=='selftest':
        import selftest
        p=ports(); credentials={u:r['password'] for u,r in auth_records().items()}
        host=read_ipv6() if public_ipv6()['enabled'] else ''
        result=selftest.run(credentials,host or (S/'lan-ip').read_text().strip(),p['lanPort'],p['localPort'])
        (S/'selftest-passed').touch()
        return {'ok':True,**result}
    raise ValueError('未知操作')

if __name__=='__main__':
    try:
        action=sys.argv[1] if len(sys.argv)>1 else 'status'
        data=json.loads(sys.stdin.read() or '{}') if action in {'credentials','save_account','delete_account','read_file','save_file','restore_file','set_ports','set_public_ipv6','set_callerid'} else {}
        result=main(action,data)
        print(json.dumps(result,ensure_ascii=False))
    except Exception as error:
        message=str(error) if isinstance(error,ValueError) else '操作失败：'+type(error).__name__
        print(json.dumps({'ok':False,'error':message},ensure_ascii=False))
        sys.exit(1)
