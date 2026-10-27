import hashlib
import re
import secrets
import select
import socket
import struct
import time
accounts={}
def md5(value):
    return hashlib.md5(value.encode()).hexdigest()

class Client:
    def __init__(self, user, host, target_port):
        self.user, self.host = user, host
        self.ipv6 = ':' in host
        self.uri_host = '['+host+']' if self.ipv6 else host
        self.target_port = target_port
        self.sock = socket.socket(socket.AF_INET6 if self.ipv6 else socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, 0))
        self.port = self.sock.getsockname()[1]
        self.callid = secrets.token_hex(12) + '@pbx-test'
        self.tag = secrets.token_hex(8)
        self.seq = 0

    def send(self, method, uri, auth='', body='', to=None, seq=None, extra=''):
        if seq is None:
            self.seq += 1
            seq = self.seq
        packet = (f'{method} {uri} SIP/2.0\r\n'
                  f'Via: SIP/2.0/UDP {self.uri_host}:{self.port};branch=z9hG4bK{secrets.token_hex(8)};rport\r\n'
                  f'Max-Forwards: 70\r\n'
                  f'From: <sip:{self.user}@{self.uri_host}>;tag={self.tag}\r\n'
                  f'To: {to or f"<sip:{self.user}@{self.uri_host}>"}\r\n'
                  f'Call-ID: {self.callid}\r\n'
                  f'CSeq: {seq} {method}\r\n'
                  f'Contact: <sip:{self.user}@{self.uri_host}:{self.port}>\r\n'
                  f'{auth}{extra}'
                  f'{"Content-Type: application/sdp" + chr(13) + chr(10) if body else ""}'
                  f'Content-Length: {len(body.encode())}\r\n\r\n{body}')
        self.last_packet = packet.encode()
        self.sock.sendto(self.last_packet, (self.host, self.target_port))

    def response(self, method, timeout=6):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            ready, _, _ = select.select([self.sock], [], [], min(0.5, max(0, end-time.monotonic())))
            if not ready:
                self.sock.sendto(self.last_packet, (self.host, self.target_port))
                continue
            text = self.sock.recv(65535).decode(errors='replace')
            if not text.startswith('SIP/2.0') or not re.search(rf'CSeq: \d+ {method}\r', text, re.I):
                continue
            if int(text.split()[1]) >= 200:
                return text
        raise RuntimeError(f'{method} response timeout')

    def auth(self, challenge, method, uri, password):
        header = re.search(r'WWW-Authenticate: Digest (.+)\r', challenge, re.I).group(1)
        fields = dict(re.findall(r'(\w+)="([^"]*)"', header))
        realm, nonce = fields['realm'], fields['nonce']
        a1, a2 = md5(f'{self.user}:{realm}:{password}'), md5(f'{method}:{uri}')
        value = f'username="{self.user}", realm="{realm}", nonce="{nonce}", uri="{uri}"'
        if 'auth' in fields.get('qop', ''):
            cnonce = secrets.token_hex(8)
            digest = md5(f'{a1}:{nonce}:00000001:{cnonce}:auth:{a2}')
            value += f', qop=auth, nc=00000001, cnonce="{cnonce}"'
        else:
            digest = md5(f'{a1}:{nonce}:{a2}')
        return f'Authorization: Digest {value}, response="{digest}", algorithm=MD5\r\n'

    def register(self, password, expires=120):
        uri = f'sip:{self.uri_host}:{self.target_port}'
        extra = f'Expires: {expires}\r\n'
        self.send('REGISTER', uri, extra=extra)
        response = self.response('REGISTER')
        assert response.split()[1] == '401', 'Missing authentication challenge'
        self.send('REGISTER', uri, self.auth(response, 'REGISTER', uri, password), extra=extra)
        return self.response('REGISTER').split()[1]

    def echo(self):
        rtp = socket.socket(socket.AF_INET6 if self.ipv6 else socket.AF_INET, socket.SOCK_DGRAM)
        rtp.bind((self.host, 0))
        uri = f'sip:600@{self.uri_host}:{self.target_port}'
        family='IP6' if self.ipv6 else 'IP4'
        sdp = (f'v=0\r\no=test 1 1 IN {family} {self.host}\r\ns=RTP self-test\r\n'
               f'c=IN {family} {self.host}\r\nt=0 0\r\nm=audio {rtp.getsockname()[1]} RTP/AVP 0\r\n'
               'a=rtpmap:0 PCMU/8000\r\na=sendrecv\r\n')
        to = f'<sip:600@{self.uri_host}>'
        self.send('INVITE', uri, body=sdp, to=to)
        response = self.response('INVITE')
        if response.split()[1] == '401':
            self.send('ACK', uri, to=re.search(r'^To: (.+)\r', response, re.M|re.I).group(1), seq=self.seq)
            self.send('INVITE', uri, self.auth(response, 'INVITE', uri, accounts[self.user]), body=sdp, to=to)
            response = self.response('INVITE')
        assert response.split()[1] == '200', 'Echo INVITE failed'
        to = re.search(r'^To: (.+)\r', response, re.M|re.I).group(1)
        remote_uri = re.search(r'^Contact: <([^>]+)>', response, re.M|re.I).group(1)
        self.send('ACK', remote_uri, to=to, seq=self.seq)
        address = re.search(r'^c=IN '+family+r' (\S+)', response, re.M).group(1)
        port = int(re.search(r'^m=audio (\d+)', response, re.M).group(1))
        payload = bytes(range(160))
        returned = 0
        time.sleep(1.1)
        for index in range(80):
            packet = struct.pack('!BBHII', 0x80, 0, index, index*160, 123456) + payload
            rtp.sendto(packet, (address, port))
            ready, _, _ = select.select([rtp], [], [], 0.02)
            if ready:
                result = rtp.recv(4096)
                if result[12:] == payload:
                    returned += 1
        self.send('BYE', remote_uri, to=to)
        assert self.response('BYE').split()[1] == '200', 'Call cleanup failed'
        rtp.close()
        assert returned >= 10, f'Insufficient returned RTP packets: {returned}'
        return returned


def run(credentials,lan,lan_port,local_port):
    global accounts
    accounts=credentials
    tested=[]
    echoed=0
    for user,host,port in [('1001',lan,lan_port),('2001','127.0.0.1',local_port)]:
        if user not in credentials:
            continue
        client=Client(user,host,port)
        uri=f'sip:600@{client.uri_host}:{port}'
        target=f'<sip:600@{client.uri_host}>'
        client.send('OPTIONS',uri,to=target)
        challenge=client.response('OPTIONS')
        assert challenge.split()[1]=='401','Expected authentication challenge'
        client.send('OPTIONS',uri,client.auth(challenge,'OPTIONS',uri,credentials[user]),to=target)
        status=client.response('OPTIONS').split()[1]
        assert status in ('200','404'),'Authentication failed'
        tested.append(user)
        if user=='1001' and status=='200':
            echoed=client.echo()
        client.sock.close()
    assert tested,'No test accounts'
    return {'testedAccounts':tested,'echoPackets':echoed}
