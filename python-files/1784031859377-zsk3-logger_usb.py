import os
import socket
import platform
import subprocess
import csv
from io import StringIO
from datetime import datetime

LOG_PATH = r"C:\Logs"
LOG_FILE = os.path.join(LOG_PATH, "usb_logs.log")

def get_system_info():
    """Базовая информация о системе."""
    return {
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

def get_usb_devices():
    """
    Получает список устройств через wmic, фильтрует только USB и возвращает текст.
    Использует CSV для надежного парсинга.
    """
    try:
        # Максимально простой запрос: никаких условий WHERE, просто список полей
        cmd = [
            "wmic",
            "path", "Win32_PnPEntity",
            "get", "Name,Manufacturer,PNPDeviceID,SerialNumber",
            "/format:csv"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=20,
            encoding="utf-8",
            errors="replace"
        )

        # Если wmic вернул ошибку текстом (как в твоем случае "ОШИБКА. Описание: ...")
        if "ОШИБКА" in result.stderr or "ERROR" in result.stderr:
            return f"WMI вернул ошибку:\n{result.stderr.strip()}"
        
        if not result.stdout.strip():
            return "Пустой ответ от wmic."

        # Парсим CSV
        reader = csv.DictReader(StringIO(result.stdout))
        usb_devices = []

        for row in reader:
            # Внимание: wmic иногда добавляет лишние пробелы или специфичные имена колонок
            pnp_id = row.get("PNPDeviceID", "").strip()
            
            # ГЛАВНОЕ: Фильтруем именно по началу строки PNPDeviceID
            if pnp_id.startswith("USB\\"):
                usb_devices.append(row)

        if not usb_devices:
            return "Подключенные USB-устройства не найдены (или у них нет префикса USB\\ в ID)."

        # Формируем красивый вывод для лога
        output_lines = [f"{'Name':<40} {'Manufacturer':<20} {'Serial':<15} {'VID/PID'}"]
        output_lines.append("-" * 100)
        
        for dev in usb_devices:
            name = dev.get("Name", "N/A")[:38] # Обрезаем длинное имя
            manuf = dev.get("Manufacturer", "N/A")[:18]
            serial = dev.get("SerialNumber", "N/A")[:13]
            pnp = dev.get("PNPDeviceID", "")
            
            # Извлекаем VID и PID из строки вида USB\VID_1234&PID_5678...
            vid = pid = "N/A"
            if "VID_" in pnp and "PID_" in pnp:
                parts = pnp.split("&")
                for part in parts:
                    if part.startswith("VID_"): vid = part.replace("VID_", "")
                    if part.startswith("PID_"): pid = part.replace("PID_", "")
            
            output_lines.append(f"{name:<40} {manuf:<20} {serial:<15} {vid}:{pid}")

        return "\n".join(output_lines)

    except FileNotFoundError:
        return "Утилита wmic не найдена. Это скрипт только для Windows."
    except subprocess.TimeoutExpired:
        return "Превышено время ожидания ответа от системы."
    except Exception as e:
        return f"Произошла непредвиденная ошибка: {e}"

def save_to_log(system_info, usb_info, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"ЛОГ СОБЫТИЯ: {system_info['timestamp']}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("[СИСТЕМА]\n")
        for key, value in system_info.items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("[USB УСТРОЙСТВА]\n")
        f.write("=" * 60 + "\n")
        f.write(usb_info)
        f.write("\n\n")

if __name__ == "__main__":
    try:
        sys_info = get_system_info()
        usb_info = get_usb_devices()
        save_to_log(sys_info, usb_info, LOG_FILE)
        print(f"Лог сохранен в: {LOG_FILE}")
        
        # Дублируем результат в консоль, чтобы сразу видеть, нет ли ошибки
        print("\n--- Результат сбора USB ---")
        print(usb_info)

    except PermissionError:
        print("ОШИБКА: Нет прав на запись в C:\\Logs. Запустите терминал от имени Администратора!")
    except Exception as e:
        print(f"Критическая ошибка скрипта: {e}")