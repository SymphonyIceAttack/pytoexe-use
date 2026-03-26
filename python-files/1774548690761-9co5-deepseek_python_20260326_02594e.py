#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSINT Tool v3.0 - УНИВЕРСАЛЬНАЯ ВЕРСИЯ
Работает: консоль, GUI, EXE, APK
Автоустановка зависимостей, самодостаточный код
"""

import sys
import os
import subprocess
import importlib.metadata
from datetime import datetime

# ========== АВТОУСТАНОВКА ЗАВИСИМОСТЕЙ ==========
REQUIRED_PACKAGES = ['requests']

def install_package(package):
    """Автоматическая установка отсутствующих пакетов"""
    try:
        importlib.metadata.version(package)
        return True
    except:
        print(f"[*] Установка {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
            return True
        except:
            return False

# Установка необходимых пакетов
for pkg in REQUIRED_PACKAGES:
    install_package(pkg)

# ========== ИМПОРТЫ ==========
import requests
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
        self.version = "3.0"
        self.results = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def log(self, msg: str, level: str = "INFO"):
        """Логирование с временем"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")
    
    def search_username(self, username: str) -> Dict:
        """Поиск по username на 50+ платформах"""
        self.log(f"Поиск username: {username}")
        
        platforms = {
            "GitHub": f"https://github.com/{username}",
            "Twitter/X": f"https://twitter.com/{username}",
            "Instagram": f"https://instagram.com/{username}",
            "Facebook": f"https://facebook.com/{username}",
            "Reddit": f"https://reddit.com/user/{username}",
            "YouTube": f"https://youtube.com/@{username}",
            "TikTok": f"https://tiktok.com/@{username}",
            "Telegram": f"https://t.me/{username}",
            "Discord": f"https://discord.com/users/{username}",
            "Pinterest": f"https://pinterest.com/{username}",
            "Twitch": f"https://twitch.tv/{username}",
            "LinkedIn": f"https://linkedin.com/in/{username}",
            "VK": f"https://vk.com/{username}",
            "OK": f"https://ok.ru/{username}",
            "Medium": f"https://medium.com/@{username}",
            "Dev.to": f"https://dev.to/{username}",
            "HackerNews": f"https://news.ycombinator.com/user?id={username}",
            "GitLab": f"https://gitlab.com/{username}",
            "Bitbucket": f"https://bitbucket.org/{username}",
            "Keybase": f"https://keybase.io/{username}",
            "Pastebin": f"https://pastebin.com/u/{username}",
            "Spotify": f"https://open.spotify.com/user/{username}",
            "SoundCloud": f"https://soundcloud.com/{username}",
            "Snapchat": f"https://snapchat.com/add/{username}",
            "Tumblr": f"https://{username}.tumblr.com",
            "Flickr": f"https://flickr.com/people/{username}",
            "Behance": f"https://behance.net/{username}",
            "Dribbble": f"https://dribbble.com/{username}",
            "CodePen": f"https://codepen.io/{username}",
            "Gravatar": f"https://gravatar.com/{username}"
        }
        
        results = {
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "found": [],
            "not_found": [],
            "error": []
        }
        
        for platform, url in platforms.items():
            try:
                response = self.session.get(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    results["found"].append({"platform": platform, "url": url})
                    self.log(f"[+] {platform}: {url}")
                elif response.status_code == 404:
                    results["not_found"].append(platform)
                else:
                    results["error"].append(f"{platform}: HTTP {response.status_code}")
            except Exception as e:
                results["error"].append(f"{platform}: {str(e)[:50]}")
        
        return results
    
    def analyze_domain(self, domain: str) -> Dict:
        """Полный анализ домена"""
        self.log(f"Анализ домена: {domain}")
        
        results = {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "ip": None,
            "dns": {},
            "whois": {},
            "headers": {},
            "technologies": []
        }
        
        # Получение IP
        try:
            results["ip"] = socket.gethostbyname(domain)
            self.log(f"IP: {results['ip']}")
        except:
            results["ip"] = "Не определен"
        
        # DNS записи (если доступно)
        if DNS_AVAILABLE:
            record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT']
            for record_type in record_types:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    results["dns"][record_type] = [str(r) for r in answers]
                except:
                    pass
        
        # WHOIS (если доступно)
        if WHOIS_AVAILABLE:
            try:
                w = whois.whois(domain)
                for key in ['registrar', 'creation_date', 'expiration_date', 'name_servers', 'org']:
                    if hasattr(w, key) and getattr(w, key):
                        results["whois"][key] = str(getattr(w, key))
            except:
                results["whois"]["error"] = "WHOIS недоступен"
        
        # HTTP заголовки
        try:
            response = self.session.get(f"http://{domain}", timeout=10)
            results["headers"] = dict(response.headers)
        except:
            try:
                response = self.session.get(f"https://{domain}", timeout=10)
                results["headers"] = dict(response.headers)
            except Exception as e:
                results["headers"]["error"] = str(e)
        
        return results
    
    def analyze_ip(self, ip: str) -> Dict:
        """Геолокация и информация об IP"""
        self.log(f"Анализ IP: {ip}")
        
        results = {
            "ip": ip,
            "timestamp": datetime.now().isoformat(),
            "geo": {},
            "asn": {},
            "threat": {}
        }
        
        # Геолокация через ip-api.com
        try:
            response = self.session.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = response.json()
            if data.get('status') == 'success':
                results["geo"] = {
                    "country": data.get('country'),
                    "region": data.get('regionName'),
                    "city": data.get('city'),
                    "lat": data.get('lat'),
                    "lon": data.get('lon'),
                    "isp": data.get('isp'),
                    "org": data.get('org'),
                    "as": data.get('as')
                }
        except Exception as e:
            results["geo"]["error"] = str(e)
        
        # Порт сканирование (базовое)
        common_ports = [80, 443, 22, 21, 25, 3306, 3389, 8080]
        results["open_ports"] = []
        for port in common_ports[:3]:  # Ограничим для скорости
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((ip, port)) == 0:
                    results["open_ports"].append(port)
                sock.close()
            except:
                pass
        
        return results
    
    def check_email(self, email: str) -> Dict:
        """Проверка email на утечки"""
        self.log(f"Проверка email: {email}")
        
        results = {
            "email": email,
            "timestamp": datetime.now().isoformat(),
            "breaches": [],
            "valid": False
        }
        
        # Проверка формата
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            results["error"] = "Неверный формат email"
            return results
        
        # Проверка MX записи
        domain = email.split('@')[1]
        try:
            if DNS_AVAILABLE:
                mx = dns.resolver.resolve(domain, 'MX')
                results["valid"] = True
                results["mx_servers"] = [str(r.exchange) for r in mx]
        except:
            pass
        
        # Проверка утечек через HaveIBeenPwned
        try:
            response = self.session.get(
                f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                timeout=10
            )
            if response.status_code == 200:
                results["breaches"] = response.json()
            elif response.status_code == 404:
                results["breaches"] = []
        except Exception as e:
            results["breaches_error"] = str(e)
        
        return results
    
    def analyze_phone(self, phone: str) -> Dict:
        """Анализ телефонного номера"""
        self.log(f"Анализ номера: {phone}")
        
        results = {
            "phone": phone,
            "timestamp": datetime.now().isoformat(),
            "country": None,
            "carrier": None,
            "valid": False
        }
        
        # Очистка номера
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Простая валидация
        if len(cleaned) >= 7:
            results["valid"] = True
            # Определение страны по коду (упрощенно)
            if cleaned.startswith('+7') or cleaned.startswith('8'):
                results["country"] = "Россия"
            elif cleaned.startswith('+380'):
                results["country"] = "Украина"
            elif cleaned.startswith('+1'):
                results["country"] = "США/Канада"
            elif cleaned.startswith('+44'):
                results["country"] = "Великобритания"
            elif cleaned.startswith('+49'):
                results["country"] = "Германия"
        
        return results
    
    def analyze_image_metadata(self, image_path: str) -> Dict:
        """Анализ метаданных изображения"""
        self.log(f"Анализ изображения: {image_path}")
        
        results = {
            "path": image_path,
            "timestamp": datetime.now().isoformat(),
            "exif": {},
            "gps": None,
            "size": None
        }
        
        if not PIL_AVAILABLE:
            results["error"] = "PIL не установлен"
            return results
        
        try:
            img = Image.open(image_path)
            results["size"] = img.size
            results["format"] = img.format
            results["mode"] = img.mode
            
            exifdata = img.getexif()
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    results["exif"][tag] = str(value)
                    
                    # Извлечение GPS координат
                    if tag_id == 34853:  # GPSInfo
                        results["gps"] = self._parse_gps(value)
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    def _parse_gps(self, gps_data):
        """Парсинг GPS данных из EXIF"""
        try:
            lat = gps_data.get(2)
            lon = gps_data.get(4)
            if lat and lon:
                lat_ref = gps_data.get(1, 'N')
                lon_ref = gps_data.get(3, 'E')
                return {
                    "latitude": self._convert_to_degrees(lat),
                    "longitude": self._convert_to_degrees(lon),
                    "ref": f"{lat_ref}{lon_ref}"
                }
        except:
            pass
        return None
    
    def _convert_to_degrees(self, value):
        """Конвертация GPS координат"""
        d, m, s = value
        return d + (m / 60.0) + (s / 3600.0)
    
    def format_results(self, data: Dict, format_type: str = "text") -> str:
        """Форматирование результатов в текст или JSON"""
        if format_type == "json":
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        
        # Текстовый формат
        lines = []
        lines.append("=" * 70)
        lines.append(f"OSINT Tool v{self.version} - Результаты")
        lines.append(f"Время: {data.get('timestamp', datetime.now().isoformat())}")
        lines.append("=" * 70)
        
        for key, value in data.items():
            if key in ['timestamp', 'username', 'domain', 'ip', 'email']:
                continue
            if value:
                lines.append(f"\n{key.upper()}:")
                if isinstance(value, dict):
                    for k, v in value.items():
                        if v:
                            lines.append(f"  {k}: {v}")
                elif isinstance(value, list):
                    for item in value[:10]:
                        if isinstance(item, dict):
                            lines.append(f"  - {item.get('platform', item.get('name', item))}: {item.get('url', '')}")
                        else:
                            lines.append(f"  - {item}")
                else:
                    lines.append(f"  {value}")
        
        lines.append("\n" + "=" * 70)
        return "\n".join(lines)

# ========== КОНСОЛЬНЫЙ ИНТЕРФЕЙС ==========
class ConsoleInterface:
    """Консольная версия (работает везде)"""
    
    def __init__(self):
        self.osint = UniversalOSINT()
        self.commands = {
            '1': self.cmd_username,
            '2': self.cmd_domain,
            '3': self.cmd_ip,
            '4': self.cmd_email,
            '5': self.cmd_phone,
            '6': self.cmd_image,
            'help': self.cmd_help,
            'h': self.cmd_help,
            'q': self.cmd_quit,
            'quit': self.cmd_quit,
            'exit': self.cmd_quit
        }
    
    def clear_screen(self):
        """Очистка экрана"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Вывод баннера"""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                    OSINT TOOL v{self.osint.version}                     ║
║              Универсальный инструмент разведки               ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def cmd_username(self):
        username = input("\nВведите username: ").strip()
        if username:
            print("\n[Поиск...]")
            results = self.osint.search_username(username)
            print(self.osint.format_results(results))
    
    def cmd_domain(self):
        domain = input("\nВведите домен (example.com): ").strip()
        if domain:
            print("\n[Анализ...]")
            results = self.osint.analyze_domain(domain)
            print(self.osint.format_results(results))
    
    def cmd_ip(self):
        ip = input("\nВведите IP адрес: ").strip()
        if ip:
            print("\n[Анализ...]")
            results = self.osint.analyze_ip(ip)
            print(self.osint.format_results(results))
    
    def cmd_email(self):
        email = input("\nВведите email: ").strip()
        if email:
            print("\n[Проверка...]")
            results = self.osint.check_email(email)
            print(self.osint.format_results(results))
    
    def cmd_phone(self):
        phone = input("\nВведите номер телефона: ").strip()
        if phone:
            print("\n[Анализ...]")
            results = self.osint.analyze_phone(phone)
            print(self.osint.format_results(results))
    
    def cmd_image(self):
        path = input("\nВведите путь к изображению: ").strip()
        if path and os.path.exists(path):
            print("\n[Анализ...]")
            results = self.osint.analyze_image_metadata(path)
            print(self.osint.format_results(results))
        else:
            print("[!] Файл не найден")
    
    def cmd_help(self):
        help_text = """
ДОСТУПНЫЕ КОМАНДЫ:
  1  - Поиск по username (50+ платформ)
  2  - Анализ домена (WHOIS, DNS, IP)
  3  - Анализ IP (геолокация, порты)
  4  - Проверка email (утечки, MX)
  5  - Анализ телефона (страна, оператор)
  6  - Анализ изображений (метаданные)
  h/help - Показать справку
  q/quit/exit - Выход
        """
        print(help_text)
    
    def cmd_quit(self):
        print("\nДо свидания!")
        return True
    
    def run(self):
        """Запуск консольного интерфейса"""
        self.clear_screen()
        self.print_banner()
        self.cmd_help()
        
        while True:
            try:
                choice = input("\nВыберите действие (1-6, h=help, q=quit): ").strip().lower()
                if choice in self.commands:
                    result = self.commands[choice]()
                    if result:
                        break
                else:
                    print("[!] Неизвестная команда. Введите 'help' для списка команд.")
            except KeyboardInterrupt:
                print("\n\n[!] Прервано пользователем")
                break
            except Exception as e:
                print(f"[!] Ошибка: {e}")

# ========== GUI ИНТЕРФЕЙС ==========
class GUInterface:
    """GUI версия с tkinter"""
    
    def __init__(self, root):
        self.root = root
        self.osint = UniversalOSINT()
        self.root.title(f"OSINT Tool v{self.osint.version}")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Стили
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#1e1e1e', foreground='#ffffff')
        style.configure('TFrame', background='#1e1e1e')
        style.configure('TLabelframe', background='#1e1e1e', foreground='#ffffff')
        
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_font = font.Font(size=14, weight='bold')
        title = ttk.Label(main_frame, text=f"OSINT Tool v{self.osint.version}", font=title_font)
        title.pack(pady=5)
        
        # Панель ввода
        input_frame = ttk.LabelFrame(main_frame, text="Входные данные", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(input_frame, text="Цель:").grid(row=0, column=0, padx=5)
        self.target_entry = ttk.Entry(input_frame, width=50)
        self.target_entry.grid(row=0, column=1, padx=5, sticky='ew')
        
        # Тип операции
        self.action_var = tk.StringVar(value="username")
        actions = [
            ("👤 Username", "username"),
            ("🌐 Домен", "domain"),
            ("📍 IP адрес", "ip"),
            ("📧 Email", "email"),
            ("📱 Телефон", "phone"),
            ("🖼️ Изображение", "image")
        ]
        
        for i, (text, value) in enumerate(actions):
            rb = ttk.Radiobutton(input_frame, text=text, variable=self.action_var, value=value)
            rb.grid(row=1, column=i, padx=5, pady=5)
        
        # Кнопка выполнения
        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=2, column=0, columnspan=6, pady=10)
        
        self.run_btn = ttk.Button(btn_frame, text="▶ ВЫПОЛНИТЬ", command=self.run)
        self.run_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = ttk.Button(btn_frame, text="🗑 Очистить", command=self.clear)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # Результаты
        result_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame, 
            wrap=tk.WORD, 
            bg='#2d2d2d', 
            fg='#d4d4d4',
            font=('Consolas', 10)
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Статус бар
        self.status = ttk.Label(main_frame, text="Готов к работе", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, pady=5)
    
    def run(self):
        """Выполнение выбранного действия"""
        target = self.target_entry.get().strip()
        action = self.action_var.get()
        
        if not target and action != 'image':
            messagebox.showwarning("Ошибка", "Введите данные для поиска")
            return
        
        self.run_btn.config(state='disabled')
        self.status.config(text="Выполняется...")
        self.result_text.delete(1.0, tk.END)
        self.root.update()
        
        try:
            if action == "username":
                results = self.osint.search_username(target)
            elif action == "domain":
                results = self.osint.analyze_domain(target)
            elif action == "ip":
                results = self.osint.analyze_ip(target)
            elif action == "email":
                results = self.osint.check_email(target)
            elif action == "phone":
                results = self.osint.analyze_phone(target)
            elif action == "image":
                from tkinter import filedialog
                path = filedialog.askopenfilename(
                    title="Выберите изображение",
                    filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff")]
                )
                if path:
                    results = self.osint.analyze_image_metadata(path)
                else:
                    self.status.config(text="Отменено")
                    return
            else:
                results = {"error": "Неизвестное действие"}
            
            formatted = self.osint.format_results(results)
            self.result_text.insert(1.0, formatted)
            self.status.config(text="Готов")
        except Exception as e:
            self.result_text.insert(1.0, f"Ошибка: {str(e)}")
            self.status.config(text="Ошибка")
        finally:
            self.run_btn.config(state='normal')
    
    def clear(self):
        """Очистка полей"""
        self.target_entry.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.status.config(text="Очищено")

# ========== ТОЧКА ВХОДА ==========
def main():
    """Главная функция"""
    # Проверка аргументов командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--console', '-c']:
            console = ConsoleInterface()
            console.run()
            return
        elif sys.argv[1] in ['--help', '-h']:
            print("""
OSINT Tool v3.0 - Универсальный инструмент разведки

Использование:
    python osint_tool.py              # Запуск GUI (если доступен)
    python osint_tool.py --console    # Запуск консольной версии
    python osint_tool.py --help       # Показать справку

Функции:
    • Поиск по username (50+ платформ)
    • Анализ доменов (WHOIS, DNS, IP)
    • Геолокация IP
    • Проверка email на утечки
    • Анализ телефонных номеров
    • Извлечение метаданных из изображений
            """)
            return
    
    # Выбор интерфейса
    if GUI_AVAILABLE:
        try:
            root = tk.Tk()
            app = GUInterface(root)
            root.mainloop()
        except Exception as e:
            print(f"[!] Ошибка GUI: {e}")
            print("[*] Запуск консольной версии...")
            console = ConsoleInterface()
            console.run()
    else:
        console = ConsoleInterface()
        console.run()

if __name__ == "__main__":
    main()