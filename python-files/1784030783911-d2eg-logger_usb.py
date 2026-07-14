import os
import socket
import platform
import subprocess
from datetime import datetime

LOG_PATH = r"C:\Logs"
LOG_FILE = os.path.join(LOG_PATH, "usb_logs.log")

def get_system_info():
    """Собирает базовую информацию о системе и пользователе."""
    info = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
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

def get_usb_devices():
    """
    Получает список подключённых USB-устройств через wmic.
    Возвращает строку с отформатированным выводом.
    """
    try:
        # Команда для получения информации о USB-устройствах
        # Win32_PnPEntity содержит Name, Manufacturer, PNPDeviceID (где есть VID/PID), SerialNumber (если доступен)
        cmd = [
            "wmic",
            "path", "Win32_PnPEntity",
            "where", "Name like '%USB%'",
            "get", "Name,Manufacturer,PNPDeviceID,SerialNumber",
            "/format:table"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
            encoding="utf-8",
            errors="replace"
        )
        output = result.stdout.strip()
        if not output:
            return "Нет данных об USB-устройствах или команда вернула пустой результат."
        return output
    except FileNotFoundError:
        return "Ошибка: утилита wmic не найдена (возможно, не Windows)."
    except subprocess.TimeoutExpired:
        return "Ошибка: превышение времени ожидания при сборе данных об USB."
    except Exception as e:
        return f"Ошибка при сборе данных об USB: {e}"

def save_to_log(system_info, usb_info, log_file):
    """Создаёт папку (если нет) и записывает всю информацию в лог-файл."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("ОБЩАЯ ИНФОРМАЦИЯ О СИСТЕМЕ\n")
        f.write("=" * 60 + "\n")
        for key, value in system_info.items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("ИНФОРМАЦИЯ О ПОДКЛЮЧЁННЫХ USB-УСТРОЙСТВАХ\n")
        f.write("=" * 60 + "\n")
        f.write(usb_info)
        f.write("\n\n")

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_info = get_usb_devices()
        save_to_log(system_info, usb_info, LOG_FILE)
        print(f"Информация успешно сохранена в {LOG_FILE}")
    except PermissionError:
        print("Ошибка: нет прав на запись в C:\\Logs. Запустите скрипт от имени администратора.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")