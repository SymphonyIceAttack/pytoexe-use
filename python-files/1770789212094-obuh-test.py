#!/usr/bin/env python3
import sys, os, json, time, socket, struct, random, re, threading
from datetime import datetime
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings; warnings.filterwarnings("ignore")
import requests

# PyInstaller compatibility fix - MUST be at the top before importing webview
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    basedir = sys._MEIPASS
    os.environ['WEBVIEW2_BROWSER'] = 'edge'  # Force WebView2 on Windows
else:
    basedir = os.path.dirname(__file__)

# Import webview AFTER path fixes
import webview

class Config:
    API_MCSRVSTAT="https://api.mcsrvstat.us/3/"
    API_MCSTATUS="https://api.mcstatus.io/v2/status/java/"
    MCSCANS_SERVERS="https://api.mcscans.fi/public/v1/servers"
    MCSCANS_SERVER="https://api.mcscans.fi/public/v1/server/"
    API_DNS_GOOGLE="https://dns.google/resolve"
    API_DNS_CF="https://cloudflare-dns.com/dns-query"
    API_IPAPI="http://ip-api.com/json/"
    API_GEOJS="https://get.geojs.io/v1/ip/geo/"
    API_SHODAN="https://internetdb.shodan.io/"
    API_HACKERTARGET="https://api.hackertarget.com/"

class IPV:
    BAD=[(0,16777215),(167772160,184549375),(1681915904,1686110207),(2130706432,2147483647),(2851995648,2852061183),(2886729728,2887778303),(3232235520,3232301055),(3221225472,3221225727),(3221225984,3221226239),(3227017984,3227018239),(3323068416,3323199487),(3325256704,3325256959),(3405803776,4294967295)]
    @staticmethod
    def to_int(ip):
        try:p=ip.split('.');return(int(p[0])<<24)+(int(p[1])<<16)+(int(p[2])<<8)+int(p[3])
        except:return 0
    @staticmethod
    def ok(ip):
        if not ip or not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',str(ip)):return False
        n=IPV.to_int(str(ip))
        if n==0:return False
        for s,e in IPV.BAD:
            if s<=n<=e:return False
        return True

class DNS:
    def __init__(self,sess):self.s=sess
    def resolve(self,host):
        r={'hostname':host,'ipv4':[],'methods':[],'srv':[],'cname':[]}
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',host):
            if IPV.ok(host):r['ipv4'].append(host);r['methods'].append('Direct IP')
            return r
        self._g(host,r,'Google DoH');self._c(host,r);self._srv(host,r)
        for pfx in['mc.','play.','server.','hub.']:self._g(f"{pfx}{host}",r,f'DoH ({pfx}{host})')
        r['ipv4']=list(dict.fromkeys(r['ipv4']));return r
    def _g(self,host,r,label='Google DoH'):
        try:
            resp=self.s.get(Config.API_DNS_GOOGLE,params={'name':host,'type':'A'},timeout=8)
            if resp.status_code==200:
                for a in resp.json().get('Answer',[]):
                    if a.get('type')==1:
                        ip=a['data']
                        if IPV.ok(ip) and ip not in r['ipv4']:r['ipv4'].append(ip);(r['methods'].append(label) if label not in r['methods'] else None)
                    elif a.get('type')==5:
                        cn=a.get('data','').rstrip('.');
                        if cn and cn not in r['cname']:r['cname'].append(cn)
        except:pass
    def _c(self,host,r):
        try:
            resp=self.s.get(Config.API_DNS_CF,params={'name':host,'type':'A'},headers={'Accept':'application/dns-json'},timeout=8)
            if resp.status_code==200:
                for a in resp.json().get('Answer',[]):
                    if a.get('type')==1:
                        ip=a['data']
                        if IPV.ok(ip) and ip not in r['ipv4']:r['ipv4'].append(ip);(r['methods'].append('Cloudflare DoH') if 'Cloudflare DoH' not in r['methods'] else None)
        except:pass
    def _srv(self,host,r):
        try:
            resp=self.s.get(Config.API_DNS_GOOGLE,params={'name':f'_minecraft._tcp.{host}','type':'SRV'},timeout=8)
            if resp.status_code==200:
                for a in resp.json().get('Answer',[]):
                    if a.get('type')==33:
                        sd=a.get('data','');r['srv'].append(sd);parts=sd.split()
                        if len(parts)>=4:
                            sh=parts[3].rstrip('.');self._g(sh,r,f'SRV ({sh})')
                        if 'SRV Record' not in r['methods']:r['methods'].append('SRV Record')
        except:pass

class SubScan:
    WORDS=['mc','play','server','hub','lobby','game','pvp','survival','creative','skyblock','prison','factions','bedwars','skywars','uhc','kitpvp','practice','duels','build','spawn','world','earth','towny','rpg','vanilla','modded','proxy','bungee','velocity','waterfall','node','node1','node2','us','eu','asia','au','uk','de','fr','br','www','mail','ftp','ssh','vpn','api','cdn','dns','ns1','ns2','admin','forum','community','discord','ts','ts3','wiki','blog','shop','store','donate','tebex','buycraft','map','dynmap','bluemap','dev','test','staging','beta','backup','panel','control','portal','login','auth','old','new','v1','v2','v3','app','web','static','files','download','media','status','stats','monitor','logs','db','mysql','redis','cache','dashboard','git']
    @staticmethod
    def scan(domain,dns_r):
        found=[]
        def chk(sub):
            try:
                full=f"{sub}.{domain}";r=dns_r.resolve(full)
                if r['ipv4']:return{'subdomain':full,'ip':r['ipv4'][0]}
            except:pass
            return None
        with ThreadPoolExecutor(max_workers=60) as ex:
            futs={ex.submit(chk,w):w for w in SubScan.WORDS}
            for f in as_completed(futs):
                try:
                    v=f.result()
                    if v:found.append(v)
                except:pass
        return{'domain':domain,'checked':len(SubScan.WORDS),'found':found,'count':len(found)}

class MCPing:
    @staticmethod
    def ping(host,port=25565,timeout=5):
        r={'host':host,'port':port,'online':False}
        try:
            ip=host
            try:
                resp=requests.get(Config.API_DNS_GOOGLE,params={'name':host,'type':'A'},timeout=5)
                if resp.status_code==200:
                    for a in resp.json().get('Answer',[]):
                        if a.get('type')==1 and IPV.ok(a['data']):ip=a['data'];r['resolved_ip']=ip;break
            except:pass
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM);sock.settimeout(timeout);sock.connect((ip,port))
            data=b'\x00'+MCPing._vi(47);enc=host.encode('utf-8');data+=MCPing._vi(len(enc))+enc+struct.pack('>H',port)+MCPing._vi(1)
            sock.send(MCPing._vi(len(data))+data);sock.send(b'\x01\x00');resp=MCPing._read(sock);sock.close()
            if resp:
                try:
                    sd=json.loads(resp);r['online']=True;r['version']=sd.get('version',{});r['players']=sd.get('players',{})
                    desc=sd.get('description','')
                    if isinstance(desc,dict):
                        t=desc.get('text','');ex=desc.get('extra',[])
                        if ex:t=''.join(e.get('text','') for e in ex if isinstance(e,dict))
                        r['motd']=t
                    elif isinstance(desc,str):r['motd']=desc
                except:r['online']=True
        except socket.timeout:r['error']='Timed out'
        except ConnectionRefusedError:r['error']='Refused'
        except OSError as e:r['error']=str(e)
        except Exception as e:r['error']=str(e)
        return r
    @staticmethod
    def _vi(v):
        r=b''
        while True:
            t=v&0x7F;v>>=7
            if v:t|=0x80
            r+=bytes([t])
            if not v:break
        return r
    @staticmethod
    def _rvi(s):
        r=n=0
        while True:
            b=s.recv(1)
            if not b:return-1
            v=b[0];r|=(v&0x7F)<<(7*n);n+=1
            if n>5:return-1
            if not(v&0x80):break
        return r
    @staticmethod
    def _read(s):
        try:
            MCPing._rvi(s);MCPing._rvi(s);sl=MCPing._rvi(s)
            if sl<0 or sl>1048576:return None
            d=b''
            while len(d)<sl:
                c=s.recv(min(4096,sl-len(d)))
                if not c:break
                d+=c
            return d.decode('utf-8')
        except:return None

class Ports:
    SVC={21:'FTP',22:'SSH',23:'Telnet',25:'SMTP',53:'DNS',80:'HTTP',110:'POP3',143:'IMAP',443:'HTTPS',445:'SMB',993:'IMAPS',995:'POP3S',1433:'MSSQL',1521:'Oracle',2082:'cPanel',2083:'cPanel-SSL',2086:'WHM',2087:'WHM-SSL',2222:'DirectAdmin',3306:'MySQL',3389:'RDP',5432:'PostgreSQL',5900:'VNC',6379:'Redis',8080:'HTTP-Alt',8443:'HTTPS-Alt',8888:'Plesk',8880:'HTTP-Alt3',9090:'Cockpit',9200:'Elasticsearch',27017:'MongoDB',27015:'Source-Game',25565:'Minecraft',25566:'MC-2',25567:'MC-3',25568:'MC-4',25569:'MC-5',25570:'MC-6',25571:'MC-7',25572:'MC-8',25575:'RCON',19132:'Bedrock',19133:'Bedrock-2'}
    @staticmethod
    def scan(ip):
        if not IPV.ok(ip):return{'ip':ip,'error':'Invalid public IP','open':[],'total_open':0}
        op=[]
        def chk(p):
            try:s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(1.5);r=s.connect_ex((ip,p));s.close();return r==0
            except:return False
        with ThreadPoolExecutor(max_workers=60) as ex:
            futs={ex.submit(chk,p):p for p in Ports.SVC}
            for f in as_completed(futs):
                p=futs[f]
                try:
                    if f.result():op.append(p)
                except:pass
        return{'ip':ip,'scanned':len(Ports.SVC),'open':sorted(op),'total_open':len(op),'services':{str(p):Ports.SVC.get(p,'?') for p in sorted(op)}}

class Geo:
    HOSTS={'OVH':['ovh','soyoustart','kimsufi'],'Hetzner':['hetzner'],'DigitalOcean':['digitalocean'],'Linode/Akamai':['linode','akamai'],'Vultr':['vultr','choopa','constant company'],'AWS':['amazon','aws','ec2'],'Google Cloud':['google cloud','google llc'],'Azure':['microsoft','azure'],'Cloudflare':['cloudflare'],'Shockbyte':['shockbyte'],'Apex Hosting':['apex hosting','apex minecraft'],'BisectHosting':['bisect'],'MCProHosting':['mcpro'],'PebbleHost':['pebblehost'],'Contabo':['contabo'],'Scaleway':['scaleway','online s.a.s'],'Leaseweb':['leaseweb'],'NFOrce':['nforce'],'ColoCrossing':['colocrossing'],'Psychz':['psychz'],'Hostinger':['hostinger'],'GoDaddy':['godaddy'],'Namecheap':['namecheap'],'Ionos/1&1':['ionos','1and1','1&1'],'DediPath':['dedipath'],'DataPacket':['datapacket'],'Nocix':['nocix'],'QuadraNet':['quadranet'],'ServerMania':['servermania'],'ReliableSite':['reliablesite'],'Limestone':['limestone'],'PhoenixNAP':['phoenixnap'],'Rackspace':['rackspace'],'Oracle Cloud':['oracle'],'Alibaba Cloud':['alibaba'],'UpCloud':['upcloud'],'Kamatera':['kamatera'],'Packet/Equinix':['packet','equinix'],'BuyVM':['buyvm','frantech'],'RamNode':['ramnode'],'HostHatch':['hosthatch'],'Time4VPS':['time4vps'],'AlphaVPS':['alphavps'],'GCore':['gcore','g-core']}
    VPS_IND=['vps','cloud','dedicated','server','hosting','data center','datacenter','colocation','virtual','instance']
    def __init__(self,sess):self.s=sess
    def locate(self,ip):
        if not IPV.ok(ip):return{'ip':ip,'error':'Invalid public IP'}
        try:
            r=self.s.get(f"{Config.API_IPAPI}{ip}?fields=66846719",timeout=8)
            if r.status_code==200:
                d=r.json()
                if d.get('status')=='success':return{'ip':ip,'country':d.get('country'),'country_code':d.get('countryCode'),'region':d.get('regionName'),'city':d.get('city'),'zip':d.get('zip'),'lat':d.get('lat'),'lon':d.get('lon'),'timezone':d.get('timezone'),'isp':d.get('isp'),'org':d.get('org'),'as_number':d.get('as'),'as_name':d.get('asname'),'reverse_dns':d.get('reverse'),'is_mobile':d.get('mobile'),'is_proxy_vpn':d.get('proxy'),'is_hosting':d.get('hosting')}
        except:pass
        try:
            r=self.s.get(f"{Config.API_GEOJS}{ip}.json",timeout=8)
            if r.status_code==200:d=r.json();return{'ip':ip,'country':d.get('country'),'region':d.get('region'),'city':d.get('city'),'org':d.get('organization_name'),'timezone':d.get('timezone')}
        except:pass
        return{'ip':ip,'error':'Geo lookup failed'}
    def hosting_info(self,geo):
        if not geo or geo.get('error'):return{'provider':'Unknown','type':'Unknown','confidence':'NONE'}
        combined=f"{geo.get('org','')} {geo.get('isp','')} {geo.get('as_name','')}".lower();reverse=(geo.get('reverse_dns') or '').lower();is_h=geo.get('is_hosting',False)
        provider=None
        for prov,kws in self.HOSTS.items():
            if any(k in combined or k in reverse for k in kws):provider=prov;break
        itype='Unknown'
        if is_h:
            if any(k in combined for k in['dedicated','dedi','bare metal']):itype='Dedicated Server'
            elif any(k in combined for k in['vps','virtual','cloud','instance']):itype='VPS / Cloud Instance'
            elif any(k in combined for k in['shared','cpanel','plesk']):itype='Shared Hosting'
            else:itype='Hosting (VPS/Dedicated)'
        elif geo.get('is_proxy_vpn'):itype='Proxy / VPN'
        elif geo.get('is_mobile'):itype='Mobile Network'
        elif any(k in combined for k in self.VPS_IND):itype='Likely VPS/Hosting'
        else:itype='Residential / ISP'
        panel='Unknown'
        if any(k in combined or k in reverse for k in['shockbyte','apex','bisect','mcpro','pebblehost']):panel='Minecraft Panel (Pterodactyl/Multicraft)'
        elif 'pterodactyl' in reverse or 'ptero' in reverse:panel='Pterodactyl'
        elif 'multicraft' in reverse:panel='Multicraft'
        return{'provider':provider or geo.get('org') or geo.get('isp') or 'Unknown','type':itype,'is_hosting':is_h,'is_proxy_vpn':geo.get('is_proxy_vpn',False),'is_mobile':geo.get('is_mobile',False),'isp':geo.get('isp'),'org':geo.get('org'),'as_number':geo.get('as_number'),'as_name':geo.get('as_name'),'reverse_dns':geo.get('reverse_dns'),'guessed_panel':panel,'confidence':'HIGH' if provider else 'MEDIUM','datacenter_location':f"{geo.get('city','')}, {geo.get('region','')}, {geo.get('country','')}".strip(', ')}

class RDNS:
    @staticmethod
    def lookup(ip,sess):
        if not IPV.ok(ip):return[]
        results=[]
        try:
            p=ip.split('.');ptr=f"{p[3]}.{p[2]}.{p[1]}.{p[0]}.in-addr.arpa"
            r=sess.get(Config.API_DNS_GOOGLE,params={'name':ptr,'type':'PTR'},timeout=8)
            if r.status_code==200:
                for a in r.json().get('Answer',[]):
                    if a.get('type')==12:h=a['data'].rstrip('.');results.append(h) if h not in results else None
        except:pass
        return results

class Shoics:
    @staticmethod
    def lookup(ip):
        if not IPV.ok(ip):return{}
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.settimeout(5);s.connect(('whois.arin.net',43));s.send(f"n {ip}\r\n".encode())
            d=b''
            while True:
                c=s.recv(4096)
                if not c:break
                d+=c
            s.close();txt=d.decode('utf-8',errors='ignore');result={}
            for line in txt.split('\n'):
                if ':' in line and not line.startswith('#') and not line.startswith('%'):
                    k,v=line.split(':',1);k=k.strip();v=v.strip()
                    if v and k:result[k]=v
            return result
        except:return{}

class Checkx:
    @staticmethod
    def lookup(ip,sess):
        if not IPV.ok(ip):return{}
        try:
            r=sess.get(f"{Config.API_SHODAN}{ip}",timeout=8)
            if r.status_code==200:return r.json()
        except:pass
        return{}

class McScans:
    def __init__(self,sess):self.s=sess
    def search(self,query):
        result={'query':query,'status':'SEARCHING','servers':[],'total':0}
        try:
            r=self.s.get(Config.MCSCANS_SERVERS,params={'query':query},timeout=15)
            if r.status_code==200:
                data=r.json()
                if isinstance(data,list):c=self._cl(data);result['servers']=c;result['total']=len(c);result['status']='FOUND' if c else 'NO_RESULTS'
                elif isinstance(data,dict):
                    for k in['results','servers','data','hits','items']:
                        if k in data and isinstance(data[k],list):c=self._cl(data[k]);result['servers']=c;result['total']=data.get('total',len(c));result['status']='FOUND' if c else 'NO_RESULTS';break
                    else:c=self._cd(data);result['servers']=[c] if c else [];result['total']=1 if c else 0;result['status']='FOUND' if c else 'NO_RESULTS'
                else:result['status']='API_ERROR';result['http_code']=r.status_code
        except Exception as e:result['status']='ERROR';result['error']=str(e)
        return result
    def get_server(self,address):
        result={'query':address,'status':'FETCHING'}
        try:
            r=self.s.get(f"{Config.MCSCANS_SERVER}{quote(str(address),safe='.:')}",timeout=15)
            if r.status_code==200:
                data=r.json()
                if isinstance(data,dict):c=self._cd(data);result['status']='FOUND';result['server_data']=c;result['extracted']=self._ex(c)
                else:result['status']='FOUND';result['server_data']=data
            elif r.status_code==404:result['status']='NOT_FOUND'
            else:result['status']='ERROR';result['http_code']=r.status_code
        except Exception as e:result['status']='ERROR';result['error']=str(e)
        return result
    def _cl(self,lst):return[self._cd(i) if isinstance(i,dict) else i for i in lst if i]
    def _cd(self,d):
        if not isinstance(d,dict):return d
        c={}
        for k,v in d.items():
            if k in('icon','favicon','server_icon') and isinstance(v,str) and len(v)>200:continue
            elif isinstance(v,str) and 'data:image' in v:continue
            elif isinstance(v,dict):c[k]=self._cd(v)
            elif isinstance(v,list):c[k]=[self._cd(i) if isinstance(i,dict) else i for i in v]
            else:c[k]=v
        return c
    def _ex(self,data):
        if not isinstance(data,dict):return{}
        ext={};maps={'ip':['ip','address','host','server_ip','ipAddress','serverIp','ip_address'],'port':['port','server_port','serverPort'],'domain':['domain','hostname','name','server_name','serverName'],'version':['version','server_version','mcVersion','minecraft_version'],'players_online':['players_online','online_players','online','playersOnline','playerCount'],'players_max':['players_max','max_players','max','slots','maxPlayers'],'motd':['motd','description','server_motd'],'country':['country','geo_country','countryCode','country_code'],'software':['software','server_software','platform'],'plugins':['plugins'],'mods':['mods','modlist'],'cracked':['cracked','online_mode','onlineMode'],'last_seen':['last_seen','last_online','updatedAt','lastSeen'],'first_seen':['first_seen','createdAt','firstSeen'],'whitelist':['whitelist']}
        for tk,sks in maps.items():
            for sk in sks:
                v=data.get(sk)
                if v is not None:ext[tk]=v;break
        p=data.get('players') or {};
        if isinstance(p,dict):
            if 'players_online' not in ext:ext['players_online']=p.get('online') or p.get('now')
            if 'players_max' not in ext:ext['players_max']=p.get('max') or p.get('slots')
            s=p.get('sample') or p.get('list') or[];
            if s:ext['players_list']=s
        v=data.get('version') or {};
        if isinstance(v,dict):
            if 'version' not in ext:ext['version']=v.get('name') or v.get('name_clean')
            ext['protocol']=v.get('protocol')
        d=data.get('description') or data.get('motd') or {};
        if isinstance(d,dict):
            t=d.get('text','');ex=d.get('extra',[])
            if ex and isinstance(ex,list):t=''.join(e.get('text','') for e in ex if isinstance(e,dict))
            if t:ext['motd']=t
        if 'ip' in ext and not IPV.ok(str(ext['ip'])):del ext['ip']
        return ext

class LineHack:
    def __init__(self):
        self.s=requests.Session();self.s.headers.update({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36','Accept':'application/json, text/html, */*'})
        self.dns=DNS(self.s);self.geo=Geo(self.s);self.mcscans=McScans(self.s)
    def _addr(self,a):
        port=25565;host=a.strip()
        if ':' in host:
            parts=host.rsplit(':',1)
            try:port=int(parts[1]);host=parts[0]
            except:pass
        return host,port
    def _find_ip(self,*sources):
        ipr=re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        for src in sources:
            if not isinstance(src,dict):continue
            for ip in src.get('ipv4',[]):
                if IPV.ok(ip):return ip
            for k in['ip','address','host','ip_address','serverIp','resolved_ip']:
                v=str(src.get(k,''))
                if ipr.match(v) and IPV.ok(v):return v
            ext=src.get('extracted',{})
            if isinstance(ext,dict):
                v=str(ext.get('ip',''))
                if ipr.match(v) and IPV.ok(v):return v
            sd=src.get('server_data',{})
            if isinstance(sd,dict):
                for k in['ip','address','host','ip_address']:
                    v=str(sd.get(k,''))
                    if ipr.match(v) and IPV.ok(v):return v
            for sk,sv in src.get('sources',{}).items():
                if isinstance(sv,dict):
                    for k in['ip','ip_address','resolved_ip','host']:
                        v=str(sv.get(k,''))
                        if ipr.match(v) and IPV.ok(v):return v
            for srv in src.get('servers',[]):
                if isinstance(srv,dict):
                    for k in['ip','address','host']:
                        v=str(srv.get(k,''))
                        if ipr.match(v) and IPV.ok(v):return v
        return None
    def mode_1x(self,inp):
        r={'mode':'1X - SERVER STATUS','target':inp,'timestamp':datetime.now().isoformat(),'status':'SCANNING','sources':{}}
        host,port=self._addr(inp)
        try:
            resp=self.s.get(f"{Config.API_MCSRVSTAT}{inp}",timeout=12)
            if resp.status_code==200:
                d=resp.json();ip_v=d.get('ip','')
                if not IPV.ok(str(ip_v)):ip_v='Protected/Hidden'
                src={'online':d.get('online',False),'ip':ip_v,'port':d.get('port',25565),'hostname':d.get('hostname','N/A'),'version':d.get('version','N/A'),'software':d.get('software','N/A'),'players_online':d.get('players',{}).get('online',0),'players_max':d.get('players',{}).get('max',0),'players_list':d.get('players',{}).get('list',[]),'motd':d.get('motd',{}),'plugins':d.get('plugins',[]),'mods':d.get('mods',[])}
                r['sources']['checks']=src
                if d.get('online'):r['status']='ONLINE';r['server']={'ip':ip_v,'port':src['port'],'hostname':src['hostname'],'version':src['version'],'software':src['software']};r['players']={'online':src['players_online'],'max':src['players_max'],'list':src['players_list']};r['motd']=src['motd']
        except Exception as e:r['sources']['checks']={'error':str(e)}
        try:
            resp=self.s.get(f"{Config.API_MCSTATUS}{inp}",timeout=12)
            if resp.status_code==200:
                d=resp.json();ip_v=d.get('ip_address','')
                if not IPV.ok(str(ip_v)):ip_v='Protected/Hidden'
                src={'online':d.get('online',False),'host':d.get('host','N/A'),'ip_address':ip_v,'port':d.get('port',25565),'eula_blocked':d.get('eula_blocked',False),'version':d.get('version',{}),'players':d.get('players',{}),'motd':d.get('motd',{}),'software':d.get('software','N/A'),'plugins':d.get('plugins',[]),'mods':d.get('mods',[]),'srv_record':d.get('srv_record')}
                r['sources']['mcstatus_io']=src
                if d.get('online') and r['status']!='ONLINE':r['status']='ONLINE';r['server']={'ip':ip_v,'port':src['port'],'version':d.get('version',{}).get('name_clean','Unknown')};r['players']=d.get('players',{});r['motd']=d.get('motd',{})
        except Exception as e:r['sources']['mcstatus_io']={'error':str(e)}
        try:
            proto=MCPing.ping(host,port,timeout=5)
            if proto.get('resolved_ip') and not IPV.ok(proto['resolved_ip']):del proto['resolved_ip']
            r['sources']['protocol_ping']=proto
            if proto.get('online') and r['status']!='ONLINE':r['status']='ONLINE';r['server']={'ip':proto.get('resolved_ip',host),'port':port,'version':proto.get('version',{}).get('name','Unknown')};r['players']=proto.get('players',{});r['motd']=proto.get('motd','')
        except Exception as e:r['sources']['protocol_ping']={'error':str(e)}
        if r['status']=='SCANNING':r['status']='OFFLINE'
        w=sum(1 for s in r['sources'].values() if isinstance(s,dict) and 'error' not in s);r['sources_working']=f"{w}/{len(r['sources'])}";return r
    def mode_2x(self,name):
        r={'mode':'2X - DEEP INTELLIGENCE','target':name,'timestamp':datetime.now().isoformat(),'status':'SCANNING','intelligence':{}}
        try:
            search=self.mcscans.search(name);r['intelligence']['server_search']=search
            info=self.mcscans.get_server(name);r['intelligence']['server_info']=info
            if search.get('servers'):
                det=[];seen=set()
                for srv in search['servers'][:5]:
                    addr=None
                    if isinstance(srv,dict):
                        for k in['ip','host','address','domain','name','hostname']:
                            v=srv.get(k)
                            if v and isinstance(v,str) and v!=name and v not in seen:addr=v;seen.add(v);break
                    if addr:
                        d=self.mcscans.get_server(addr)
                        if d.get('status')=='FOUND':det.append(d)
                if det:r['intelligence']['related_servers']=det
            dns=self.dns.resolve(name);r['intelligence']['dns']=dns;pip=self._find_ip(dns,info,search)
            if pip:
                r['intelligence']['primary_ip']=pip;proto=MCPing.ping(pip,25565,timeout=5)
                if proto.get('resolved_ip') and not IPV.ok(proto['resolved_ip']):del proto['resolved_ip']
                r['intelligence']['protocol_ping']=proto;ports=Ports.scan(pip);r['intelligence']['port_scan']=ports
                geo=self.geo.locate(pip);r['intelligence']['geolocation']=geo;hosting=self.geo.hosting_info(geo);r['intelligence']['hosting_info']=hosting
                checkx=Checkx.lookup(pip,self.s)
                if checkx:r['intelligence']['checkx']=checkx
                rdns=RDNS.lookup(pip,self.s)
                if rdns:r['intelligence']['reverse_dns']=rdns
                shoics=Shoics.lookup(pip)
                if shoics:r['intelligence']['shoics']=shoics
                net=self._netanal(geo,hosting,ports,checkx,rdns);r['intelligence']['network_analysis']=net
            if '.' in name:subs=SubScan.scan(name,self.dns);r['intelligence']['subdomains']=subs
            if '.' in name:
                ht=self._ht(name)
                if ht:r['intelligence']['hackertarget']=ht
            assess=self._assess(r['intelligence']);r['intelligence']['security_assessment']=assess;r['status']='COMPLETE'
            r['summary']={'search_hits':search.get('total',0),'server_found':info.get('status')=='FOUND','primary_ip':pip or 'Not found','total_ips':len(dns.get('ipv4',[])),'open_ports':r['intelligence'].get('port_scan',{}).get('total_open',0),'subdomains':r['intelligence'].get('subdomains',{}).get('count',0),'hosting_provider':hosting.get('provider','Unknown') if pip else 'Unknown','hosting_type':hosting.get('type','Unknown') if pip else 'Unknown','risk_level':assess.get('risk_level','UNKNOWN'),'risk_score':assess.get('risk_score',0)}
        except Exception as e:r['status']='ERROR';r['error']=str(e)
        return r
    def _netanal(self,geo,hosting,ports,checkx,rdns):
        a={};a['infrastructure']={'provider':hosting.get('provider','Unknown'),'type':hosting.get('type','Unknown'),'datacenter':hosting.get('datacenter_location','Unknown'),'panel_guess':hosting.get('guessed_panel','Unknown'),'is_hosting':hosting.get('is_hosting',False),'is_proxy_vpn':hosting.get('is_proxy_vpn',False)}
        prot=[]
        if hosting.get('is_proxy_vpn'):prot.append('Behind Proxy/VPN')
        if any(x and 'cloudflare' in x.lower() for x in(rdns or[])):prot.append('Cloudflare Protected')
        if any(x and 'ddos-guard' in x.lower() for x in(rdns or[])):prot.append('DDoS-Guard Protected')
        if any(x and 'tcpshield' in x.lower() for x in(rdns or[])):prot.append('TCPShield Protected')
        if not prot:prot.append('No DDoS protection detected')
        a['protection']=prot;op=ports.get('open',[])
        a['service_groups']={'web':[p for p in op if p in[80,443,8080,8443,8888,8880,2082,2083,2086,2087,9090]],'minecraft':[p for p in op if 25565<=p<=25575],'databases':[p for p in op if p in[3306,5432,27017,6379,9200]],'remote':[p for p in op if p in[22,23,3389,5900,2222]],'total':len(op)}
        if 2082 in op or 2083 in op:a['control_panel']='cPanel'
        elif 2086 in op or 2087 in op:a['control_panel']='WHM'
        elif 8888 in op:a['control_panel']='Plesk'
        elif 2222 in op:a['control_panel']='DirectAdmin'
        elif 9090 in op:a['control_panel']='Cockpit'
        elif 8080 in op:a['control_panel']='Web panel (8080)'
        if checkx:a['known_cves']=checkx.get('vulns',[]);a['checkx_ports']=checkx.get('ports',[]);a['checkx_hostnames']=checkx.get('hostnames',[]);a['checkx_tags']=checkx.get('tags',[])
        return a
    def _ht(self,dom):
        r={}
        for t,n in[('dnslookup','DNS'),('reversedns','RevDNS'),('hostsearch','Hosts')]:
            try:
                resp=self.s.get(f"{Config.API_HACKERTARGET}{t}/?q={dom}",timeout=8)
                if resp.status_code==200 and 'error' not in resp.text.lower()[:50] and 'API count' not in resp.text:
                    lines=[l.strip() for l in resp.text.strip().split('\n') if l.strip()]
                    if lines:r[n]=lines
            except:pass
        return r
    def _assess(self,intel):
        vulns=[];score=0;op=intel.get('port_scan',{}).get('open',[])
        for port,name,sev,pts in[(23,'Telnet Exposed','CRITICAL',35),(3306,'MySQL Exposed','CRITICAL',40),(6379,'Redis Exposed','CRITICAL',40),(27017,'MongoDB Exposed','CRITICAL',40),(9200,'Elasticsearch Exposed','CRITICAL',40),(22,'SSH Exposed','HIGH',25),(3389,'RDP Exposed','HIGH',30),(5900,'VNC Exposed','HIGH',25),(5432,'PostgreSQL Exposed','HIGH',30),(25575,'RCON Exposed','HIGH',30),(1433,'MSSQL Exposed','HIGH',30),(21,'FTP Exposed','MEDIUM',15),(445,'SMB Exposed','HIGH',30)]:
            if port in op:vulns.append({'type':name,'severity':sev,'port':port});score+=pts
        mc=[p for p in op if 25565<=p<=25574]
        if len(mc)>3:vulns.append({'type':'Multiple MC instances','severity':'LOW','ports':mc});score+=10
        cx=intel.get('checkx',{})
        if cx.get('vulns'):vulns.append({'type':'Known CVEs (Checkx)','severity':'HIGH','cves':cx['vulns'][:10]});score+=35
        subs=intel.get('subdomains',{}).get('count',0)
        if subs>15:vulns.append({'type':'Large attack surface','severity':'MEDIUM','subdomains':subs});score+=15
        proto=intel.get('protocol_ping',{})
        if proto.get('online'):
            ver=str(proto.get('version',{}).get('name',''))
            if any(v in ver for v in['1.7','1.8','1.9','1.10','1.11','1.12']):vulns.append({'type':'Old MC version','severity':'MEDIUM','version':ver});score+=20
        na=intel.get('network_analysis',{})
        if na.get('protection')==['No DDoS protection detected']:vulns.append({'type':'No DDoS protection','severity':'MEDIUM'});score+=15
        score=min(score,100);lv='CRITICAL' if score>=70 else 'HIGH' if score>=50 else 'MEDIUM' if score>=30 else 'LOW'
        return{'risk_score':score,'risk_level':lv,'vulnerabilities':vulns,'total_vulns':len(vulns),'critical':len([v for v in vulns if v['severity']=='CRITICAL']),'high':len([v for v in vulns if v['severity']=='HIGH']),'medium':len([v for v in vulns if v['severity']=='MEDIUM']),'low':len([v for v in vulns if v['severity']=='LOW'])}

class Api:
    def __init__(self):self.lh=LineHack()
    def scan_1x(self,server):
        try:return json.dumps(self.lh.mode_1x(server),indent=2,default=str,ensure_ascii=False)
        except Exception as e:return json.dumps({'error':str(e)},indent=2)
    def scan_2x(self,server):
        try:return json.dumps(self.lh.mode_2x(server),indent=2,default=str,ensure_ascii=False)
        except Exception as e:return json.dumps({'error':str(e)},indent=2)

HTML=r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>QuboX v3.0</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&family=Rajdhani:wght@500;600;700&display=swap');
:root{--p:#00ff9d;--pd:#00cc7a;--s:#0affef;--t:#ff00ff;--bg:#050509;--bgd:#020204;--bgc:rgba(8,8,16,.85);--tx:#e0e0e0;--txd:#555568;--br:rgba(30,30,60,.6);--gl:0 0 25px rgba(0,255,157,.25);--gls:0 0 50px rgba(0,255,157,.4)}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Share Tech Mono',monospace;background:var(--bg);color:var(--tx);min-height:100vh;overflow-x:hidden}
/* LOADING */
#LS{position:fixed;inset:0;z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;overflow:hidden;transition:opacity 1s,transform 1s}
#LS.bye{opacity:0;transform:scale(1.1);pointer-events:none}
.LS-bg{position:absolute;inset:0;background:url('https://i.pinimg.com/1200x/fa/a9/14/faa9149183bc5ef2f693bcb8ba681f7c.jpg') center/cover;filter:blur(3px) brightness(.3);transform:scale(1.1)}
.LS-grid{position:absolute;inset:0;background:linear-gradient(rgba(0,255,157,.02) 1px,transparent 1px),linear-gradient(90deg,rgba(0,255,157,.02) 1px,transparent 1px);background-size:40px 40px;animation:gScroll 30s linear infinite}
@keyframes gScroll{to{background-position:40px 40px}}
.LS-vignette{position:absolute;inset:0;background:radial-gradient(ellipse at center,transparent 30%,rgba(0,0,0,.8) 100%)}
.LS-particles{position:absolute;inset:0;overflow:hidden}
.particle{position:absolute;width:2px;height:2px;background:var(--p);border-radius:50%;opacity:0;animation:pFloat linear infinite}
@keyframes pFloat{0%{opacity:0;transform:translateY(100vh) scale(0)}10%{opacity:1}90%{opacity:1}100%{opacity:0;transform:translateY(-10vh) scale(1.5)}}
.LS-content{position:relative;z-index:10;display:flex;flex-direction:column;align-items:center}
.LS-ring{position:relative;width:160px;height:160px;margin-bottom:40px}
.LS-ring-outer{position:absolute;inset:0;border:2px solid rgba(0,255,157,.15);border-top:2px solid var(--p);border-radius:50%;animation:rSpin 2s linear infinite}
.LS-ring-mid{position:absolute;inset:12px;border:2px solid rgba(10,255,239,.1);border-bottom:2px solid var(--s);border-radius:50%;animation:rSpin 3s linear infinite reverse}
.LS-ring-inner{position:absolute;inset:24px;border:2px solid rgba(255,0,255,.1);border-left:2px solid var(--t);border-radius:50%;animation:rSpin 1.5s linear infinite}
@keyframes rSpin{to{transform:rotate(360deg)}}
.LS-logo{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);width:80px;height:80px;border-radius:16px;border:2px solid var(--p);box-shadow:0 0 30px rgba(0,255,157,.4);animation:lGlow 2s ease-in-out infinite}
@keyframes lGlow{0%,100%{box-shadow:0 0 30px rgba(0,255,157,.4)}50%{box-shadow:0 0 60px rgba(0,255,157,.6),0 0 100px rgba(0,255,157,.2)}}
.LS-title{font-family:'Orbitron',sans-serif;font-size:48px;font-weight:900;letter-spacing:12px;margin-bottom:6px;background:linear-gradient(135deg,var(--p) 0%,var(--s) 50%,var(--t) 100%);background-size:200% 200%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;animation:tShift 3s ease infinite}
@keyframes tShift{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
.LS-ver{font-family:'Rajdhani',sans-serif;font-size:16px;color:var(--txd);letter-spacing:8px;margin-bottom:50px;font-weight:600}
.LS-pct{font-family:'Orbitron',sans-serif;font-size:28px;color:var(--p);letter-spacing:6px;margin-bottom:12px;text-shadow:0 0 20px rgba(0,255,157,.5)}
.LS-bar-out{width:420px;height:4px;background:rgba(255,255,255,.05);border-radius:2px;overflow:hidden;margin-bottom:12px;position:relative}
.LS-bar-out::before{content:'';position:absolute;inset:0;border:1px solid rgba(0,255,157,.1);border-radius:2px}
.LS-bar-in{height:100%;width:0%;background:linear-gradient(90deg,var(--p),var(--s));border-radius:2px;transition:width .25s;position:relative}
.LS-bar-in::after{content:'';position:absolute;right:0;top:-3px;width:10px;height:10px;background:var(--p);border-radius:50%;box-shadow:0 0 15px var(--p);animation:bPulse .8s ease-in-out infinite}
@keyframes bPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.6;transform:scale(.7)}}
.LS-stat{font-size:13px;color:var(--txd);letter-spacing:3px;margin-bottom:30px;height:18px}
.LS-steps{width:420px}
.LS-step{display:flex;align-items:center;gap:10px;padding:5px 0;opacity:0;transform:translateX(-30px);transition:all .5s cubic-bezier(.25,.46,.45,.94);font-size:12px;color:var(--txd)}
.LS-step.on{opacity:1;transform:translateX(0)}
.LS-step .dot{width:6px;height:6px;border-radius:50%;background:var(--p);box-shadow:0 0 8px var(--p);flex-shrink:0}
.LS-scanline{position:absolute;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--p),transparent);opacity:.3;animation:scanDown 4s linear infinite}
@keyframes scanDown{0%{top:-2px}100%{top:100%}}
/* MAIN */
#MA{display:none;opacity:0;transition:opacity .8s}
#MA.on{display:block;opacity:1}
.BG{position:fixed;inset:0;z-index:0;background:url('https://i.pinimg.com/1200x/fa/a9/14/faa9149183bc5ef2f693bcb8ba681f7c.jpg') center/cover}
.BO{position:fixed;inset:0;z-index:1;background:rgba(5,5,9,.9)}
.SL{position:fixed;inset:0;pointer-events:none;z-index:1000;background:linear-gradient(transparent 50%,rgba(0,0,0,.04) 50%);background-size:100% 3px;opacity:.04}
.HD{padding:16px 30px;border-bottom:1px solid var(--br);display:flex;align-items:center;justify-content:space-between;z-index:10;position:relative;background:rgba(5,5,9,.5);backdrop-filter:blur(20px)}
.HLS{display:flex;align-items:center;gap:16px}
.HLG{width:44px;height:44px;border-radius:10px;border:2px solid var(--p);box-shadow:var(--gl)}
.HTS h1{font-family:'Orbitron',sans-serif;font-size:22px;font-weight:900;background:linear-gradient(90deg,var(--p),var(--s));-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:3px}
.HTS .sub{font-size:10px;color:var(--txd);letter-spacing:4px;margin-top:2px}
.HRR{display:flex;align-items:center;gap:12px}
.HSI{display:flex;align-items:center;gap:6px;padding:6px 14px;background:rgba(0,255,157,.06);border:1px solid rgba(0,255,157,.2);border-radius:20px;font-size:11px}
.HSI .dot{width:7px;height:7px;background:var(--p);border-radius:50%;animation:dp 1.2s ease-in-out infinite}
@keyframes dp{50%{opacity:.3}}
.DC{display:flex;align-items:center;gap:7px;padding:6px 14px;background:rgba(88,101,242,.1);border:1px solid rgba(88,101,242,.3);border-radius:20px;font-size:11px;color:#7289da;text-decoration:none;transition:all .3s}
.DC:hover{background:rgba(88,101,242,.2);box-shadow:0 0 15px rgba(88,101,242,.2)}
.DC svg{width:16px;height:16px;fill:#7289da}
.NT{display:flex;justify-content:center;gap:8px;padding:20px 30px;z-index:10;position:relative}
.NB{font-family:'Orbitron',sans-serif;font-size:12px;font-weight:700;padding:12px 40px;background:rgba(10,10,20,.6);border:1px solid var(--br);color:var(--txd);cursor:pointer;transition:all .3s;clip-path:polygon(8px 0,100% 0,100% calc(100% - 8px),calc(100% - 8px) 100%,0 100%,0 8px);backdrop-filter:blur(5px);letter-spacing:2px}
.NB:hover{border-color:var(--p);color:var(--p);transform:translateY(-2px)}
.NB.ac{background:linear-gradient(135deg,rgba(0,255,157,.1),rgba(10,255,239,.05));border-color:rgba(0,255,157,.5);color:var(--p);box-shadow:var(--gl)}
.MN{max-width:1400px;margin:0 auto;padding:0 30px 30px;z-index:10;position:relative}
.SC{background:var(--bgc);border:1px solid var(--br);border-radius:16px;padding:28px;margin-bottom:20px;position:relative;overflow:hidden;backdrop-filter:blur(12px)}
.SC::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,var(--p),var(--s),var(--t),transparent)}
.SC::after{content:'';position:absolute;bottom:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(0,255,157,.1),transparent)}
.SH{display:flex;align-items:center;gap:12px;margin-bottom:18px}
.SI{font-size:26px}
.STL{font-family:'Orbitron',sans-serif;font-size:16px;color:var(--p);letter-spacing:2px}
.SST{font-size:10px;color:var(--txd);margin-top:2px;letter-spacing:1px}
.SB{display:flex;gap:10px;align-items:stretch}
.IW{flex:1;position:relative}
.INP{width:100%;padding:14px 18px 14px 42px;font-family:'Share Tech Mono',monospace;font-size:14px;background:rgba(5,5,9,.6);border:1px solid var(--br);border-radius:10px;color:var(--tx);outline:none;transition:all .3s}
.INP:focus{border-color:var(--p);box-shadow:0 0 20px rgba(0,255,157,.15)}
.INP::placeholder{color:var(--txd)}
.IX{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--txd);font-size:14px}
.BT{font-family:'Orbitron',sans-serif;font-size:11px;font-weight:700;padding:14px 35px;background:linear-gradient(135deg,var(--p),var(--pd));border:none;border-radius:10px;color:var(--bg);cursor:pointer;transition:all .3s;display:flex;align-items:center;gap:7px;text-transform:uppercase;letter-spacing:2px;white-space:nowrap;position:relative;overflow:hidden}
.BT::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:linear-gradient(transparent,rgba(255,255,255,.1),transparent);transform:rotate(45deg);transition:.6s}
.BT:hover::before{left:100%}
.BT:hover{transform:translateY(-2px);box-shadow:var(--gls)}
.BT:disabled{opacity:.4;cursor:not-allowed;transform:none!important}
.BT.m2{background:linear-gradient(135deg,var(--t),#aa00cc)}
.RS{background:var(--bgc);border:1px solid var(--br);border-radius:16px;overflow:hidden;backdrop-filter:blur(12px)}
.RH{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;border-bottom:1px solid var(--br);background:rgba(5,5,9,.4)}
.RT{font-family:'Orbitron',sans-serif;font-size:13px;color:var(--p);letter-spacing:2px}
.RB{padding:20px;max-height:58vh;overflow-y:auto}
.RB::-webkit-scrollbar{width:5px}
.RB::-webkit-scrollbar-track{background:transparent}
.RB::-webkit-scrollbar-thumb{background:rgba(0,255,157,.2);border-radius:3px}
.RB::-webkit-scrollbar-thumb:hover{background:rgba(0,255,157,.4)}
.JO{font-family:'Share Tech Mono',monospace;font-size:12px;line-height:1.7;white-space:pre-wrap;word-break:break-word}
.ES{text-align:center;padding:50px 25px}
.EI{font-size:50px;margin-bottom:12px;opacity:.2}
.ET{color:var(--txd);font-size:13px}
.TC{display:none}.TC.ac{display:block}
.CB{padding:7px 14px;background:rgba(0,255,157,.08);border:1px solid rgba(0,255,157,.3);border-radius:6px;color:var(--p);cursor:pointer;font-size:10px;font-family:'Orbitron',sans-serif;font-weight:600;transition:all .3s;letter-spacing:1px}
.CB:hover{background:rgba(0,255,157,.2)}
.CB.ok{background:rgba(0,255,157,.3)}
/* SCANNING ANIMATION */
.scan-anim{display:flex;flex-direction:column;align-items:center;gap:20px;padding:40px 0}
.scan-rings{position:relative;width:100px;height:100px}
.scan-r1,.scan-r2,.scan-r3{position:absolute;border-radius:50%;border:2px solid transparent}
.scan-r1{inset:0;border-top-color:var(--p);border-right-color:var(--p);animation:sr 1.2s linear infinite}
.scan-r2{inset:8px;border-bottom-color:var(--s);border-left-color:var(--s);animation:sr 1.8s linear infinite reverse}
.scan-r3{inset:16px;border-top-color:var(--t);animation:sr .9s linear infinite}
@keyframes sr{to{transform:rotate(360deg)}}
.scan-dot{position:absolute;top:50%;left:50%;width:12px;height:12px;background:var(--p);border-radius:50%;transform:translate(-50%,-50%);box-shadow:0 0 20px var(--p),0 0 40px rgba(0,255,157,.3);animation:sdp 1s ease-in-out infinite}
@keyframes sdp{0%,100%{transform:translate(-50%,-50%) scale(1);opacity:1}50%{transform:translate(-50%,-50%) scale(.6);opacity:.5}}
.scan-target{font-family:'Orbitron',sans-serif;font-size:14px;color:var(--p);letter-spacing:3px}
.scan-status{font-size:12px;color:var(--txd);letter-spacing:2px;animation:sPulse 1.5s ease-in-out infinite}
@keyframes sPulse{0%,100%{opacity:1}50%{opacity:.4}}
.scan-bars{display:flex;gap:3px;align-items:end;height:20px}
.scan-bar{width:4px;background:var(--p);border-radius:2px;animation:sBar .8s ease-in-out infinite}
.scan-bar:nth-child(1){height:8px;animation-delay:0s}
.scan-bar:nth-child(2){height:16px;animation-delay:.1s}
.scan-bar:nth-child(3){height:10px;animation-delay:.2s}
.scan-bar:nth-child(4){height:20px;animation-delay:.3s}
.scan-bar:nth-child(5){height:12px;animation-delay:.4s}
.scan-bar:nth-child(6){height:18px;animation-delay:.5s}
.scan-bar:nth-child(7){height:6px;animation-delay:.6s}
@keyframes sBar{0%,100%{opacity:.3;transform:scaleY(.5)}50%{opacity:1;transform:scaleY(1)}}
.ky{color:#00ff9d}.sg{color:#0affef}.nm{color:#ff8c00}.bl{color:#ff00ff}.nl{color:#ff0040}
.toast{position:fixed;bottom:20px;right:20px;background:rgba(8,8,16,.95);border:1px solid var(--p);border-radius:10px;padding:12px 20px;color:var(--p);font-family:'Orbitron',sans-serif;font-size:10px;z-index:9999;box-shadow:var(--gls);transform:translateY(60px);opacity:0;transition:all .4s cubic-bezier(.25,.46,.45,.94);pointer-events:none;backdrop-filter:blur(10px);letter-spacing:1px}
.toast.show{transform:translateY(0);opacity:1}
.PG{display:flex;gap:6px;align-items:center;justify-content:center;margin-top:10px}
.PG button{font-family:'Orbitron',sans-serif;font-size:9px;padding:6px 12px;background:rgba(5,5,9,.6);border:1px solid var(--br);border-radius:5px;color:var(--txd);cursor:pointer;transition:all .2s;letter-spacing:1px}
.PG button:hover{border-color:var(--p);color:var(--p)}
.PG button:disabled{opacity:.2;cursor:not-allowed}
.PG span{color:var(--txd);font-size:9px;letter-spacing:1px}
</style>
</head>
<body>
<!-- LOADING -->
<div id="LS">
<div class="LS-bg"></div>
<div class="LS-grid"></div>
<div class="LS-vignette"></div>
<div class="LS-scanline"></div>
<div class="LS-particles" id="LP"></div>
<div class="LS-content">
<div class="LS-ring">
<div class="LS-ring-outer"></div>
<div class="LS-ring-mid"></div>
<div class="LS-ring-inner"></div>
<img src="https://i.pinimg.com/1200x/09/9c/92/099c92bf55b68a6a6b1e1f79aeaf1377.jpg" class="LS-logo">
</div>
<div class="LS-title"></div>
<div class="LS-ver">QUBOX v3.0</div>
<div class="LS-pct" id="LP2">0%</div>
<div class="LS-bar-out"><div class="LS-bar-in" id="LB"></div></div>
<div class="LS-stat" id="LST">Initializing systems...</div>
<div class="LS-steps" id="LSS"></div>
</div>
</div>
<!-- MAIN -->
<div id="MA">
<div class="BG"></div><div class="BO"></div><div class="SL"></div>
<div class="toast" id="toast"></div>
<header class="HD">
<div class="HLS">
<img src="https://i.pinimg.com/1200x/09/9c/92/099c92bf55b68a6a6b1e1f79aeaf1377.jpg" class="HLG">
<div class="HTS"><h1></h1><div class="sub">QUBOX v3.0 · By LineHack</div></div>
</div>
<div class="HRR">
<a href="https://dsc.gg/LineHack" target="_blank" class="DC">
<svg viewBox="0 0 24 24"><path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994a.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"/></svg>
<span>Discord</span></a>
<div class="HSI"><div class="dot"></div><span>ONLINE</span></div>
</div>
</header>
<nav class="NT">
<button class="NB ac" data-p="1x" onclick="sw('1x')">MODE 1X</button>
<button class="NB" data-p="2x" onclick="sw('2x')">MODE 2X</button>
</nav>
<main class="MN">
<div class="TC ac" id="p-1x">
<div class="SC"><div class="SH"><span class="SI">🎯</span><div><div class="STL">MODE 1X — SERVER STATUS</div><div class="SST">Checks + PROTOCOL PING</div></div></div>
<div class="SB"><div class="IW"><span class="IX">⌘</span><input type="text" class="INP" id="i1" placeholder="hypixel.net or play.example.com:25565" onkeydown="if(event.key==='Enter')go('1x')"></div>
<button class="BT" id="b1" onclick="go('1x')">⚡ SCAN</button></div></div>
<div class="RS"><div class="RH"><div class="RT">SCAN RESULTS</div><button class="CB" id="c1" onclick="cp('1x')">COPY</button></div>
<div class="RB"><div class="ES" id="e1"><div class="EI">🔍</div><div class="ET">Enter a target and execute scan</div></div>
<div class="JO" id="o1" style="display:none"></div><div class="PG" id="pg1" style="display:none"></div></div></div></div>
<div class="TC" id="p-2x">
<div class="SC"><div class="SH"><span class="SI">💀</span><div><div class="STL">MODE 2X — DEEP INTELLIGENCE</div><div class="SST">SEARCH + DNS + PORTS + GEO + HOSTING + CHECKX + SHOICS + SUBDOMAINS + SECURITY</div></div></div>
<div class="SB"><div class="IW"><span class="IX">⌘</span><input type="text" class="INP" id="i2" placeholder="applemc or hypixel.net or 1.2.3.4" onkeydown="if(event.key==='Enter')go('2x')"></div>
<button class="BT m2" id="b2" onclick="go('2x')">💀 DEEP SCAN</button></div></div>
<div class="RS"><div class="RH"><div class="RT">INTELLIGENCE RESULTS</div><button class="CB" id="c2" onclick="cp('2x')">COPY</button></div>
<div class="RB"><div class="ES" id="e2"><div class="EI">🌍</div><div class="ET">Enter a target for deep intelligence</div></div>
<div class="JO" id="o2" style="display:none"></div><div class="PG" id="pg2" style="display:none"></div></div></div></div>
</main></div>
<script>
// PARTICLES
(function(){var c=document.getElementById('LP');for(var i=0;i<40;i++){var p=document.createElement('div');p.className='particle';p.style.left=Math.random()*100+'%';p.style.animationDuration=(4+Math.random()*8)+'s';p.style.animationDelay=Math.random()*10+'s';p.style.width=p.style.height=(1+Math.random()*3)+'px';var colors=['#00ff9d','#0affef','#ff00ff'];p.style.background=colors[Math.floor(Math.random()*3)];c.appendChild(p);}})();
// LOADING
(function(){
var S=[
{t:'Booting core engine',d:500},{t:'Loading bogon IP filter',d:400},
{t:'Initializing MC protocol pinger',d:450},{t:'Loading port scanner (40+ ports)',d:550},
{t:'Starting location engine',d:400},{t:'Loading hosting detector (50+ providers)',d:500},
{t:'Initializing Checkx engine',d:400},{t:'Initializing Shoics engine',d:350},
{t:'Connecting search',d:550},{t:'Loading security assessment',d:450},
{t:'All systems operational',d:600}
];
var bar=document.getElementById('LB'),pct=document.getElementById('LP2'),
stat=document.getElementById('LST'),steps=document.getElementById('LSS'),i=0,N=S.length;
function next(){
if(i>=N){pct.textContent='100%';bar.style.width='100%';stat.textContent='LAUNCHING QuboX...';
setTimeout(function(){document.getElementById('LS').classList.add('bye');
setTimeout(function(){var m=document.getElementById('MA');m.style.display='block';
requestAnimationFrame(function(){m.classList.add('on');});},1000);},500);return;}
var s=S[i],p=Math.round(((i+1)/N)*100);pct.textContent=p+'%';bar.style.width=p+'%';stat.textContent=s.t+'...';
var el=document.createElement('div');el.className='LS-step';el.innerHTML='<div class="dot"></div><span>'+s.t+'</span>';
steps.appendChild(el);setTimeout(function(){el.classList.add('on');},30);
i++;setTimeout(next,s.d);}
setTimeout(next,800);
})();
// APP
var D={},PG2={},LPP=250;
function sw(p){document.querySelectorAll('.NB').forEach(function(t){t.classList.toggle('ac',t.dataset.p===p)});document.querySelectorAll('.TC').forEach(function(c){c.classList.toggle('ac',c.id==='p-'+p)});}
function go(m){
var ids=m==='1x'?{i:'i1',o:'o1',e:'e1',b:'b1',pg:'pg1'}:{i:'i2',o:'o2',e:'e2',b:'b2',pg:'pg2'};
var inp=document.getElementById(ids.i),out=document.getElementById(ids.o),
emp=document.getElementById(ids.e),btn=document.getElementById(ids.b),pg=document.getElementById(ids.pg);
var val=inp.value.trim();if(!val){alert('Enter a target');return;}
btn.disabled=true;D[m]='';
emp.innerHTML='<div class="scan-anim"><div class="scan-rings"><div class="scan-r1"></div><div class="scan-r2"></div><div class="scan-r3"></div><div class="scan-dot"></div></div><div class="scan-target">'+val+'</div><div class="scan-bars"><div class="scan-bar"></div><div class="scan-bar"></div><div class="scan-bar"></div><div class="scan-bar"></div><div class="scan-bar"></div><div class="scan-bar"></div><div class="scan-bar"></div></div><div class="scan-status">SCANNING TARGET...</div></div>';
emp.style.display='block';out.style.display='none';pg.style.display='none';
var fn=m==='1x'?pywebview.api.scan_1x(val):pywebview.api.scan_2x(val);
fn.then(function(r){D[m]=r;rP(m,1);emp.style.display='none';btn.disabled=false;
}).catch(function(e){D[m]='ERROR: '+e;out.innerHTML='<span style="color:#ff0040">'+e+'</span>';out.style.display='block';emp.style.display='none';pg.style.display='none';btn.disabled=false;});}
function rP(m,page){
var ids=m==='1x'?{o:'o1',pg:'pg1'}:{o:'o2',pg:'pg2'};
var out=document.getElementById(ids.o),pgE=document.getElementById(ids.pg);
var raw=D[m]||'',lines=raw.split('\n'),tp=Math.max(1,Math.ceil(lines.length/LPP));
if(page<1)page=1;if(page>tp)page=tp;
var s=(page-1)*LPP,e=Math.min(s+LPP,lines.length);
out.innerHTML=hl(lines.slice(s,e).join('\n'));out.style.display='block';
if(tp>1){pgE.innerHTML='<button '+(page<=1?'disabled':'')+' onclick="rP(\''+m+'\','+(page-1)+')">◀</button><span>'+page+'/'+tp+'</span><button '+(page>=tp?'disabled':'')+' onclick="rP(\''+m+'\','+(page+1)+')">▶</button>';pgE.style.display='flex';}
else pgE.style.display='none';}
function hl(s){s=s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
return s.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,function(m){
var c='nm';if(/^"/.test(m))c=/:$/.test(m)?'ky':'sg';else if(/true|false/.test(m))c='bl';else if(/null/.test(m))c='nl';
return'<span class="'+c+'">'+m+'</span>';});}
function cp(m){var t=D[m]||'';if(!t.trim()){toast('No results');return;}
var a=document.createElement('textarea');a.value=t;a.style.cssText='position:fixed;left:-9999px;opacity:0';
document.body.appendChild(a);a.focus();a.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}document.body.removeChild(a);
if(ok){toast('✓ Copied!');var b=document.getElementById(m==='1x'?'c1':'c2');b.classList.add('ok');b.textContent='✓ COPIED';setTimeout(function(){b.classList.remove('ok');b.textContent='COPY';},2000);}
else if(navigator.clipboard)navigator.clipboard.writeText(t).then(function(){toast('✓ Copied!');});else toast('Failed');}
function toast(m){var t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(function(){t.classList.remove('show');},2500);}
</script>
</body>
</html>"""

def main():
    print("    [+] Starting QuboX v3.0...")
    api = Api()
    try:
        # Critical fix for PyInstaller: set proper window parameters
        window = webview.create_window(
            'QuboX v3.0',
            html=HTML,
            js_api=api,
            width=1400,
            height=900,
            resizable=True,
            frameless=False,  # Required for proper window management in frozen apps
            easy_drag=True
        )
        webview.start(debug=False, gui='edgechromium')  # Force Edge Chromium backend on Windows
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        print(f"[!] Critical error: {e}")
        if getattr(sys, 'frozen', False):
            input("Press Enter to exit...")  # Keep window open on error in frozen app
        sys.exit(1)

if __name__ == '__main__':
    main()