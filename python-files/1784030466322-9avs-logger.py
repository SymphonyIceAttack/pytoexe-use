import os
import socket
import platform
from datetime import datetime

LOG_PATH = r"C:\Logs"
LOG_FILE = os.path.join(LOG_PATH, "usb_logs.log")

def get_system_info():
    """Собирает информацию о системе и пользователе."""
    info = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        # Более надёжный способ получить имя пользователя без os.getlogin()
        "username": os.environ.get("USERNAME") or os.environ.get("USER", "unknown"),
        "os_name": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cwd": os.getcwd(),
        "python_version": platform.python_version(),
    }
    return info

def save_to_log(info, log_file):
    """Создаёт папку (если нет) и записывает информацию в лог-файл."""
    # Создаём директорию, если её не существует
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
        f.write("=" * 60 + "\n\n")

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        save_to_log(system_info, LOG_FILE)
        print(f"Информация успешно сохранена в {LOG_FILE}")
    except PermissionError:
        print("Ошибка: нет прав на запись в C:\\Logs. Запустите скрипт от имени администратора.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")