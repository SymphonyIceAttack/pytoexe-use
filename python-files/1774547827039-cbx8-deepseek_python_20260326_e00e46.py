"""
OSINT Tool v1.0
Мультиинструмент для OSINT-разведки
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import requests
import json
import re
import socket
import dns.resolver
import whois
from datetime import datetime
import subprocess
import sys
import os
import webbrowser

class OSINTTool:
    def __init__(self, root):
        self.root = root
        self.root.title("OSINT Tool v1.0")
        self.root.geometry("1000x700")
        self.root.resizable(True, True)
        
        # Настройка стилей
        self.root.configure(bg='#2b2b2b')
        
        # Создание главного фрейма
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка сетки
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Создание вкладок
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Вкладки
        self.create_user_tab()
        self.create_domain_tab()
        self.create_ip_tab()
        self.create_email_tab()
        self.create_image_tab()
        self.create_phone_tab()
        
        # Лог-панель
        log_frame = ttk.LabelFrame(main_frame, text="Лог выполнения", padding="5")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, bg='#1e1e1e', fg='#d4d4d4')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Статус бар
        self.status_bar = ttk.Label(main_frame, text="Готов к работе", relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # API ключи (пользователь может добавить свои)
        self.api_keys = {
            'virustotal': '',  # Добавьте свой API ключ
            'shodan': '',      # Добавьте свой API ключ
        }
    
    def create_user_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Поиск по username")
        
        ttk.Label(tab, text="Username для поиска:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(tab, width=50)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tab, text="Начать поиск", command=lambda: self.run_threaded(self.search_username)).grid(row=0, column=2, padx=5, pady=5)
        
        self.user_result = scrolledtext.ScrolledText(tab, height=25, width=100, bg='#1e1e1e', fg='#d4d4d4')
        self.user_result.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
    
    def create_domain_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Анализ домена")
        
        ttk.Label(tab, text="Домен:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.domain_entry = ttk.Entry(tab, width=50)
        self.domain_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tab, text="Анализировать", command=lambda: self.run_threaded(self.analyze_domain)).grid(row=0, column=2, padx=5, pady=5)
        
        self.domain_result = scrolledtext.ScrolledText(tab, height=25, width=100, bg='#1e1e1e', fg='#d4d4d4')
        self.domain_result.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
    
    def create_ip_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Анализ IP")
        
        ttk.Label(tab, text="IP адрес:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ip_entry = ttk.Entry(tab, width=50)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tab, text="Анализировать", command=lambda: self.run_threaded(self.analyze_ip)).grid(row=0, column=2, padx=5, pady=5)
        
        self.ip_result = scrolledtext.ScrolledText(tab, height=25, width=100, bg='#1e1e1e', fg='#d4d4d4')
        self.ip_result.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
    
    def create_email_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Email OSINT")
        
        ttk.Label(tab, text="Email адрес:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.email_entry = ttk.Entry(tab, width=50)
        self.email_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tab, text="Анализировать", command=lambda: self.run_threaded(self.analyze_email)).grid(row=0, column=2, padx=5, pady=5)
        
        self.email_result = scrolledtext.ScrolledText(tab, height=25, width=100, bg='#1e1e1e', fg='#d4d4d4')
        self.email_result.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
    
    def create_image_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Анализ изображений")
        
        ttk.Label(tab, text="Путь к изображению:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.image_path = ttk.Entry(tab, width=40)
        self.image_path.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tab, text="Выбрать файл", command=self.select_image).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(tab, text="Анализировать метаданные", command=lambda: self.run_threaded(self.analyze_image)).grid(row=0, column=3, padx=5, pady=5)
        
        self.image_result = scrolledtext.ScrolledText(tab, height=25, width=100, bg='#1e1e1e', fg='#d4d4d4')
        self.image_result.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
    
    def create_phone_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Анализ телефона")
        
        ttk.Label(tab, text="Номер телефона:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.phone_entry = ttk.Entry(tab, width=50)
        self.phone_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(tab, text="Анализировать", command=lambda: self.run_threaded(self.analyze_phone)).grid(row=0, column=2, padx=5, pady=5)
        
        self.phone_result = scrolledtext.ScrolledText(tab, height=25, width=100, bg='#1e1e1e', fg='#d4d4d4')
        self.phone_result.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
    
    def run_threaded(self, func):
        thread = threading.Thread(target=func)
        thread.daemon = True
        thread.start()
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def set_status(self, status):
        self.status_bar.config(text=status)
        self.root.update_idletasks()
    
    def search_username(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Ошибка", "Введите username")
            return
        
        self.user_result.delete(1.0, tk.END)
        self.set_status(f"Поиск username: {username}")
        self.log(f"Начат поиск username: {username}")
        
        # Список популярных платформ для проверки
        platforms = [
            "github.com", "twitter.com", "facebook.com", "instagram.com",
            "reddit.com", "linkedin.com", "youtube.com", "tiktok.com",
            "telegram.org", "discord.com", "pinterest.com", "twitch.tv",
            "tumblr.com", "snapchat.com", "vk.com", "ok.ru"
        ]
        
        results = []
        for platform in platforms:
            url = f"https://{platform}/{username}"
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code == 200:
                    results.append(f"[+] НАЙДЕН: {url}")
                    self.log(f"Username найден на {platform}")
                elif response.status_code == 404:
                    results.append(f"[-] Не найден: {url}")
                else:
                    results.append(f"[?] Неизвестно ({response.status_code}): {url}")
            except Exception as e:
                results.append(f"[!] Ошибка {platform}: {str(e)[:50]}")
            
            # Обновляем результат постепенно
            self.user_result.insert(tk.END, results[-1] + "\n")
            self.user_result.see(tk.END)
        
        self.user_result.insert(tk.END, "\n" + "="*50 + "\n")
        self.user_result.insert(tk.END, f"Проверено {len(platforms)} платформ\n")
        self.set_status("Поиск завершен")
        self.log("Поиск username завершен")
    
    def analyze_domain(self):
        domain = self.domain_entry.get().strip()
        if not domain:
            messagebox.showwarning("Ошибка", "Введите домен")
            return
        
        self.domain_result.delete(1.0, tk.END)
        self.set_status(f"Анализ домена: {domain}")
        self.log(f"Начат анализ домена: {domain}")
        
        try:
            # WHOIS информация
            self.domain_result.insert(tk.END, "="*50 + "\n")
            self.domain_result.insert(tk.END, "WHOIS ИНФОРМАЦИЯ\n")
            self.domain_result.insert(tk.END, "="*50 + "\n")
            
            w = whois.whois(domain)
            for key, value in w.items():
                if value:
                    self.domain_result.insert(tk.END, f"{key}: {value}\n")
            
            # DNS записи
            self.domain_result.insert(tk.END, "\n" + "="*50 + "\n")
            self.domain_result.insert(tk.END, "DNS ЗАПИСИ\n")
            self.domain_result.insert(tk.END, "="*50 + "\n")
            
            record_types = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']
            for record_type in record_types:
                try:
                    answers = dns.resolver.resolve(domain, record_type)
                    self.domain_result.insert(tk.END, f"{record_type} записи:\n")
                    for answer in answers:
                        self.domain_result.insert(tk.END, f"  {answer}\n")
                except:
                    pass
            
            self.log(f"Анализ домена {domain} завершен")
        except Exception as e:
            self.domain_result.insert(tk.END, f"Ошибка: {str(e)}\n")
            self.log(f"Ошибка при анализе домена: {str(e)}")
        
        self.set_status("Анализ завершен")
    
    def analyze_ip(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("Ошибка", "Введите IP адрес")
            return
        
        self.ip_result.delete(1.0, tk.END)
        self.set_status(f"Анализ IP: {ip}")
        self.log(f"Начат анализ IP: {ip}")
        
        try:
            # Геолокация IP
            self.ip_result.insert(tk.END, "="*50 + "\n")
            self.ip_result.insert(tk.END, "ГЕОЛОКАЦИЯ\n")
            self.ip_result.insert(tk.END, "="*50 + "\n")
            
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=10)
            data = response.json()
            
            if data.get('status') == 'success':
                fields = ['country', 'regionName', 'city', 'zip', 'lat', 'lon', 'isp', 'org', 'as']
                for field in fields:
                    if field in data:
                        self.ip_result.insert(tk.END, f"{field}: {data[field]}\n")
            
            # DNS PTR запись
            try:
                hostname, _, _ = socket.gethostbyaddr(ip)
                self.ip_result.insert(tk.END, f"\nPTR запись: {hostname}\n")
            except:
                pass
            
            self.log(f"Анализ IP {ip} завершен")
        except Exception as e:
            self.ip_result.insert(tk.END, f"Ошибка: {str(e)}\n")
            self.log(f"Ошибка при анализе IP: {str(e)}")
        
        self.set_status("Анализ завершен")
    
    def analyze_email(self):
        email = self.email_entry.get().strip()
        if not email:
            messagebox.showwarning("Ошибка", "Введите email")
            return
        
        self.email_result.delete(1.0, tk.END)
        self.set_status(f"Анализ email: {email}")
        self.log(f"Начат анализ email: {email}")
        
        # Проверка через haveibeenpwned API
        try:
            self.email_result.insert(tk.END, "="*50 + "\n")
            self.email_result.insert(tk.END, "ПРОВЕРКА УТЕЧЕК\n")
            self.email_result.insert(tk.END, "="*50 + "\n")
            
            response = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}", 
                                  headers={'hibp-api-key': ''}, timeout=10)
            
            if response.status_code == 200:
                breaches = response.json()
                self.email_result.insert(tk.END, f"Найдено {len(breaches)} утечек!\n")
                for breach in breaches[:10]:  # Показываем первые 10
                    self.email_result.insert(tk.END, f"  - {breach.get('Name')} ({breach.get('BreachDate')})\n")
            elif response.status_code == 404:
                self.email_result.insert(tk.END, "Утечек не найдено\n")
            else:
                self.email_result.insert(tk.END, f"Не удалось проверить утечки (код {response.status_code})\n")
            
            self.log(f"Анализ email {email} завершен")
        except Exception as e:
            self.email_result.insert(tk.END, f"Ошибка: {str(e)}\n")
            self.log(f"Ошибка при анализе email: {str(e)}")
        
        self.set_status("Анализ завершен")
    
    def select_image(self):
        filename = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff")]
        )
        if filename:
            self.image_path.delete(0, tk.END)
            self.image_path.insert(0, filename)
    
    def analyze_image(self):
        image_path = self.image_path.get().strip()
        if not image_path:
            messagebox.showwarning("Ошибка", "Выберите изображение")
            return
        
        self.image_result.delete(1.0, tk.END)
        self.set_status(f"Анализ изображения: {image_path}")
        self.log(f"Начат анализ изображения: {image_path}")
        
        try:
            # Используем exiftool если доступен
            try:
                result = subprocess.run(['exiftool', image_path], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    self.image_result.insert(tk.END, "МЕТАДАННЫЕ ИЗОБРАЖЕНИЯ\n")
                    self.image_result.insert(tk.END, "="*50 + "\n")
                    self.image_result.insert(tk.END, result.stdout)
                else:
                    self.image_result.insert(tk.END, "ExifTool не найден. Установите ExifTool для полного анализа.\n")
                    self.image_result.insert(tk.END, "Вывод стандартных метаданных:\n")
                    # Простой анализ через PIL
                    try:
                        from PIL import Image
                        from PIL.ExifTags import TAGS
                        
                        img = Image.open(image_path)
                        self.image_result.insert(tk.END, f"Размер: {img.size}\n")
                        self.image_result.insert(tk.END, f"Формат: {img.format}\n")
                        self.image_result.insert(tk.END, f"Режим: {img.mode}\n")
                        
                        # Exif данные
                        exifdata = img.getexif()
                        if exifdata:
                            self.image_result.insert(tk.END, "\nExif данные:\n")
                            for tag_id, value in exifdata.items():
                                tag = TAGS.get(tag_id, tag_id)
                                self.image_result.insert(tk.END, f"  {tag}: {value}\n")
                    except ImportError:
                        self.image_result.insert(tk.END, "PIL не установлен. Установите Pillow: pip install Pillow\n")
            except FileNotFoundError:
                self.image_result.insert(tk.END, "ExifTool не найден в системе\n")
                self.image_result.insert(tk.END, "Для Windows: скачайте exiftool.exe и добавьте в PATH\n")
                self.image_result.insert(tk.END, "Или установите: pip install exiftool\n")
            
            self.log(f"Анализ изображения завершен")
        except Exception as e:
            self.image_result.insert(tk.END, f"Ошибка: {str(e)}\n")
            self.log(f"Ошибка при анализе изображения: {str(e)}")
        
        self.set_status("Анализ завершен")
    
    def analyze_phone(self):
        phone = self.phone_entry.get().strip()
        if not phone:
            messagebox.showwarning("Ошибка", "Введите номер телефона")
            return
        
        self.phone_result.delete(1.0, tk.END)
        self.set_status(f"Анализ номера: {phone}")
        self.log(f"Начат анализ номера: {phone}")
        
        try:
            # Определение страны и оператора через numverify API (демо)
            self.phone_result.insert(tk.END, "="*50 + "\n")
            self.phone_result.insert(tk.END, "ИНФОРМАЦИЯ О НОМЕРЕ\n")
            self.phone_result.insert(tk.END, "="*50 + "\n")
            
            # Используем бесплатный API для проверки
            # В реальном проекте используйте платный API или локальную базу
            
            # Простой парсинг номера
            import phonenumbers
            try:
                parsed = phonenumbers.parse(phone, None)
                if phonenumbers.is_valid_number(parsed):
                    self.phone_result.insert(tk.END, f"Страна: {phonenumbers.region_code_for_number(parsed)}\n")
                    self.phone_result.insert(tk.END, f"Тип номера: {phonenumbers.number_type(parsed)}\n")
                    self.phone_result.insert(tk.END, f"Форматированный: {phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)}\n")
                else:
                    self.phone_result.insert(tk.END, "Номер недействителен\n")
            except ImportError:
                self.phone_result.insert(tk.END, "Установите phonenumbers: pip install phonenumbers\n")
            except Exception as e:
                self.phone_result.insert(tk.END, f"Ошибка парсинга: {str(e)}\n")
            
            self.log(f"Анализ номера {phone} завершен")
        except Exception as e:
            self.phone_result.insert(tk.END, f"Ошибка: {str(e)}\n")
            self.log(f"Ошибка при анализе номера: {str(e)}")
        
        self.set_status("Анализ завершен")

def main():
    root = tk.Tk()
    app = OSINTTool(root)
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()