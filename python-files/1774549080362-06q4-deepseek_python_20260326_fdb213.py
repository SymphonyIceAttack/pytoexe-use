#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINT Tool v3.1 - ИСПРАВЛЕННАЯ ВЕРСИЯ
Фикс: автоустановка requests
"""

import sys
import os
import subprocess
import importlib.util
from datetime import datetime

# ========== КОРРЕКТНАЯ АВТОУСТАНОВКА ==========
def check_and_install(package):
    """Проверка и установка пакета"""
    try:
        # Проверяем наличие пакета
        spec = importlib.util.find_spec(package)
        if spec is not None:
            return True
    except:
        pass
    
    print(f"[*] Установка {package}...")
    try:
        # Пробуем разные способы установки
        commands = [
            [sys.executable, "-m", "pip", "install", package, "--quiet", "--user"],
            [sys.executable, "-m", "pip", "install", package, "--quiet"],
            ["pip", "install", package, "--quiet"],
            ["pip3", "install", package, "--quiet"]
        ]
        
        for cmd in commands:
            try:
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except:
                continue
        
        return False
    except:
        return False

# Установка необходимых пакетов
packages_to_install = ['requests']

for pkg in packages_to_install:
    if not check_and_install(pkg):
        print(f"[!] Не удалось установить {pkg}")
        print(f"[*] Установите вручную: pip install {pkg}")
        # Не выходим, продолжим без пакета если возможно

# ========== ИМПОРТЫ ==========
try:
    import requests
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    print("[!] Библиотека requests не установлена")
    print("[*] Установите: pip install requests")
    print("[*] Некоторые функции будут недоступны")

import socket
import re
import json
import time
import urllib.parse
from typing import Dict, List, Tuple, Optional

# Попытка импорта GUI
GUI_AVAILABLE = False
try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox, font
    GUI_AVAILABLE = True
except ImportError:
    pass

# Попытка импорта дополнительных модулей
try:
    import whois
    WHOIS_AVAILABLE = True
except:
    WHOIS_AVAILABLE = False

try:
    import dns.resolver
    DNS_AVAILABLE = True
except:
    DNS_AVAILABLE = False

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

# ========== ОСНОВНОЙ КЛАСС OSINT ==========
class UniversalOSINT:
    """Универсальный OSINT движок"""
    
    def __init__(self):
        self.version = "3.1"
        self.results = []
        
        # Инициализация сессии только если requests доступен
        if REQUESTS_OK:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        else:
            self.session = None
    
    def log(self, msg: str, level: str = "INFO"):
        """Логирование с временем"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
    
    def search_username(self, username: str) -> Dict:
        """Поиск по username на популярных платформах"""
        self.log(f"Поиск username: {username}")
        
        if not REQUESTS_OK:
            return {"error": "Библиотека requests не установлена. Установите: pip install requests"}
        
        platforms = {
            "GitHub": f"https://github.com/{username}",
            "Twitter": f"https://twitter.com/{username}",
            "Instagram": f"https://instagram.com/{username}",
            "Reddit": f"https://reddit.com/user/{username}",
            "YouTube": f"https://youtube.com/@{username}",
            "TikTok": f"https://tiktok.com/@{username}",
            "Telegram": f"https://t.me/{username}",
            "Pinterest": f"https://pinterest.com/{username}",
            "Twitch": f"https://twitch.tv/{username}",
            "VK": f"https://vk.com/{username}"
        }
        
        results = {
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "found": [],
            "not_found": []
        }
        
        for platform, url in platforms.items():
            try:
                response = self.session.get(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    results["found"].append({"platform": platform, "url": url})
                    self.log(f"[+] {platform}: {url}")
                elif response.status_code == 404:
                    results["not_found"].append(platform)
            except Exception as e:
                self.log(f"[!] {platform}: {str(e)[:50]}", "ERROR")
        
        return results
    
    def analyze_domain(self, domain: str) -> Dict:
        """Анализ домена"""
        self.log(f"Анализ домена: {domain}")
        
        results = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "ip": None
        }
        
        # Получение IP (работает без requests)
        try:
            results["ip"] = socket.gethostbyname(domain)
            self.log(f"IP: {results['ip']}")
        except:
            results["ip"] = "Не определен"
        
        # WHOIS (если доступно)
        if WHOIS_AVAILABLE:
            try:
                w = whois.whois(domain)
                if w.registrar:
                    results["registrar"] = w.registrar
                if w.creation_date:
                    results["created"] = str(w.creation_date)
                if w.expiration_date:
                    results["expires"] = str(w.expiration_date)
            except:
                pass
        
        return results
    
    def analyze_ip(self, ip: str) -> Dict:
        """Геолокация IP"""
        self.log(f"Анализ IP: {ip}")
        
        if not REQUESTS_OK:
            return {"error": "Библиотека requests не установлена"}
        
        results = {
            "ip": ip,
            "timestamp": datetime.now().isoformat(),
            "geo": {}
        }
        
        try:
            response = self.session.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = response.json()
            if data.get('status') == 'success':
                results["geo"] = {
                    "country": data.get('country'),
                    "city": data.get('city'),
                    "isp": data.get('isp')
                }
        except Exception as e:
            results["geo"]["error"] = str(e)
        
        return results
    
    def check_email(self, email: str) -> Dict:
        """Проверка email"""
        self.log(f"Проверка email: {email}")
        
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "valid_format": False
        }
        
        # Проверка формата (работает без requests)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        results["valid_format"] = bool(re.match(email_pattern, email))
        
        if results["valid_format"]:
            domain = email.split('@')[1]
            results["domain"] = domain
        
        # Проверка утечек (если есть requests)
        if REQUESTS_OK:
            try:
                response = self.session.get(
                    f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                    timeout=10
                )
                if response.status_code == 200:
                    results["breaches"] = len(response.json())
                elif response.status_code == 404:
                    results["breaches"] = 0
            except:
                results["breaches_check"] = "Недоступно"
        
        return results
    
    def analyze_phone(self, phone: str) -> Dict:
        """Анализ телефонного номера"""
        self.log(f"Анализ номера: {phone}")
        
        results = {
            "phone": phone,
            "timestamp": datetime.now().isoformat(),
            "valid": False
        }
        
        # Очистка номера
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        if len(cleaned) >= 7:
            results["valid"] = True
            # Определение страны
            if cleaned.startswith('+7') or cleaned.startswith('8'):
                results["country"] = "Россия (+7)"
                results["operator"] = "МТС/Билайн/Мегафон/Tele2"
            elif cleaned.startswith('+380'):
                results["country"] = "Украина (+380)"
            elif cleaned.startswith('+1'):
                results["country"] = "США/Канада (+1)"
            elif cleaned.startswith('+44'):
                results["country"] = "Великобритания (+44)"
            elif cleaned.startswith('+49'):
                results["country"] = "Германия (+49)"
            else:
                results["country"] = "Неизвестно"
        
        return results
    
    def analyze_image_metadata(self, image_path: str) -> Dict:
        """Анализ метаданных изображения"""
        self.log(f"Анализ изображения: {image_path}")
        
        results = {
            "path": image_path,
            "timestamp": datetime.now().isoformat(),
            "exif": {}
        }
        
        if not PIL_AVAILABLE:
            results["error"] = "PIL не установлен. Установите: pip install Pillow"
            return results
        
        try:
            img = Image.open(image_path)
            results["size"] = f"{img.size[0]}x{img.size[1]}"
            results["format"] = img.format
            results["mode"] = img.mode
            
            exifdata = img.getexif()
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    results["exif"][str(tag)] = str(value)[:100]  # Ограничиваем длину
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def format_results(self, data: Dict, format_type: str = "text") -> str:
        """Форматирование результатов"""
        if format_type == "json":
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"OSINT Tool v{self.version}")
        lines.append("=" * 60)
        
        for key, value in data.items():
            if value and key not in ['timestamp']:
                if isinstance(value, dict):
                    lines.append(f"\n{key.upper()}:")
                    for k, v in value.items():
                        if v:
                            lines.append(f"  {k}: {v}")
                elif isinstance(value, list):
                    if value:
                        lines.append(f"\n{key.upper()}:")
                        for item in value[:5]:
                            if isinstance(item, dict):
                                lines.append(f"  - {item.get('platform', item)}")
                            else:
                                lines.append(f"  - {item}")
                else:
                    lines.append(f"\n{key.upper()}: {value}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

# ========== КОНСОЛЬНЫЙ ИНТЕРФЕЙС ==========
class ConsoleInterface:
    """Консольная версия"""
    
    def __init__(self):
        self.osint = UniversalOSINT()
        
        # Проверка зависимостей
        if not REQUESTS_OK:
            print("\n[!] ВНИМАНИЕ: Библиотека 'requests' не установлена")
            print("[*] Установите вручную командой: pip install requests")
            print("[*] Без неё некоторые функции будут недоступны\n")
    
    def print_banner(self):
        print(f"""
╔════════════════════════════════════════════════╗
║         OSINT TOOL v{self.osint.version}              ║
║     Универсальный инструмент разведки         ║
╚════════════════════════════════════════════════╝
        """)
    
    def run(self):
        self.print_banner()
        
        while True:
            print("\n" + "─" * 50)
            print("Доступные функции:")
            print("  1. Поиск по username")
            print("  2. Анализ домена")
            print("  3. Анализ IP адреса")
            print("  4. Проверка email")
            print("  5. Анализ телефона")
            print("  6. Анализ изображения")
            print("  7. Выход")
            print("─" * 50)
            
            choice = input("\nВыберите действие (1-7): ").strip()
            
            if choice == "1":
                username = input("Username: ").strip()
                if username:
                    result = self.osint.search_username(username)
                    print(self.osint.format_results(result))
            elif choice == "2":
                domain = input("Домен: ").strip()
                if domain:
                    result = self.osint.analyze_domain(domain)
                    print(self.osint.format_results(result))
            elif choice == "3":
                ip = input("IP адрес: ").strip()
                if ip:
                    result = self.osint.analyze_ip(ip)
                    print(self.osint.format_results(result))
            elif choice == "4":
                email = input("Email: ").strip()
                if email:
                    result = self.osint.check_email(email)
                    print(self.osint.format_results(result))
            elif choice == "5":
                phone = input("Телефон: ").strip()
                if phone:
                    result = self.osint.analyze_phone(phone)
                    print(self.osint.format_results(result))
            elif choice == "6":
                path = input("Путь к изображению: ").strip()
                if path:
                    result = self.osint.analyze_image_metadata(path)
                    print(self.osint.format_results(result))
            elif choice == "7":
                print("\nДо свидания!")
                break
            else:
                print("\n[!] Неверный выбор!")

# ========== GUI ИНТЕРФЕЙС ==========
class GUInterface:
    """GUI версия"""
    
    def __init__(self, root):
        self.root = root
        self.osint = UniversalOSINT()
        self.root.title(f"OSINT Tool v{self.osint.version}")
        self.root.geometry("900x650")
        
        self.setup_ui()
        
        # Проверка зависимостей
        if not REQUESTS_OK:
            messagebox.showwarning(
                "Внимание", 
                "Библиотека 'requests' не установлена.\n"
                "Некоторые функции могут не работать.\n\n"
                "Установите вручную: pip install requests"
            )
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title = ttk.Label(main_frame, text=f"OSINT Tool v{self.osint.version}", font=('Arial', 14, 'bold'))
        title.pack(pady=5)
        
        # Ввод
        input_frame = ttk.LabelFrame(main_frame, text="Входные данные", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Цель:").grid(row=0, column=0, padx=5)
        self.target_entry = ttk.Entry(input_frame, width=50)
        self.target_entry.grid(row=0, column=1, padx=5, sticky='ew')
        
        # Выбор действия
        self.action_var = tk.StringVar(value="username")
        actions = [
            ("👤 Username", "username"),
            ("🌐 Домен", "domain"),
            ("📍 IP", "ip"),
            ("📧 Email", "email"),
            ("📱 Телефон", "phone"),
            ("🖼️ Изображение", "image")
        ]
        
        for i, (text, value) in enumerate(actions):
            rb = ttk.Radiobutton(input_frame, text=text, variable=self.action_var, value=value)
            rb.grid(row=1, column=i, padx=5, pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=6, pady=10)
        
        ttk.Button(btn_frame, text="▶ Выполнить", command=self.run).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑 Очистить", command=self.clear).pack(side=tk.LEFT, padx=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # Результаты
        result_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=25)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Статус
        self.status = ttk.Label(main_frame, text="Готов", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, pady=5)
    
    def run(self):
        target = self.target_entry.get().strip()
        action = self.action_var.get()
        
        if not target and action != 'image':
            messagebox.showwarning("Ошибка", "Введите данные")
            return
        
        self.status.config(text="Выполняется...")
        self.result_text.delete(1.0, tk.END)
        self.root.update()
        
        try:
            if action == "username":
                result = self.osint.search_username(target)
            elif action == "domain":
                result = self.osint.analyze_domain(target)
            elif action == "ip":
                result = self.osint.analyze_ip(target)
            elif action == "email":
                result = self.osint.check_email(target)
            elif action == "phone":
                result = self.osint.analyze_phone(target)
            elif action == "image":
                from tkinter import filedialog
                path = filedialog.askopenfilename()
                if path:
                    result = self.osint.analyze_image_metadata(path)
                else:
                    return
            else:
                result = {"error": "Неизвестное действие"}
            
            formatted = self.osint.format_results(result)
            self.result_text.insert(1.0, formatted)
            self.status.config(text="Готов")
        except Exception as e:
            self.result_text.insert(1.0, f"Ошибка: {e}")
            self.status.config(text="Ошибка")
    
    def clear(self):
        self.target_entry.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)

# ========== ЗАПУСК ==========
def main():
    if len(sys.argv) > 1 and sys.argv[1] in ['--console', '-c']:
        console = ConsoleInterface()
        console.run()
    elif GUI_AVAILABLE:
        root = tk.Tk()
        app = GUInterface(root)
        root.mainloop()
    else:
        console = ConsoleInterface()
        console.run()

if __name__ == "__main__":
    main()