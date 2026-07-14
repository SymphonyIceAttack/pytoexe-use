import os
import socket
import platform
import subprocess
import re
import csv
from io import StringIO
from datetime import datetime

LOG_PATH = r"C:\Logs"
LOG_FILE = os.path.join(LOG_PATH, "usb_logs.log")

def get_system_info():
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

def extract_device_id(wmic_output_line):
    """
    Извлекает DeviceID из строки вида:
    \\.\root\cimv2:Win32_PnPEntity.DeviceID="USBSTOR\\DISK&VEN_KINGSTON&PROD_DATATRAVELER_G4&REV_PMAP\\...
    """
    match = re.search(r'DeviceID="(.*?)"', wmic_output_line)
    if match:
        return match.group(1)
    return None

def get_usb_storage_devices():
    """
    1. Находит устройства через: wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"
    2. Для каждого найденного ID получает полные данные: Name, Manufacturer, SerialNumber и т.д.
    """
    try:
        # ШАГ 1: Поиск устройств хранения (USBSTOR)
        # Используем findstr вместо find для лучшей совместимости, но find тоже ок.
        cmd_find = [
            "wmic", "path", "Win32_USBControllerDevice", "get", "Dependent",
            "/format:textvaluelist" # Этот формат проще парсить, чем таблицу
        ]
        
        result_find = subprocess.run(
            cmd_find, capture_output=True, text=True, timeout=15, encoding="utf-8", errors="replace"
        )
        
        if "ОШИБКА" in result_find.stderr or "ERROR" in result_find.stderr:
            return f"Ошибка при поиске устройств: {result_find.stderr.strip()}"

        # Фильтруем строки, содержащие USBSTOR, и извлекаем ID
        storage_ids = []
        for line in result_find.stdout.splitlines():
            if "USBSTOR" in line:
                dev_id = extract_device_id(line)
                if dev_id:
                    storage_ids.append(dev_id)

        if not storage_ids:
            return "Устройства класса USBSTOR не найдены (возможно, флешек/дисков нет)."

        # ШАГ 2: Получение детальной информации по каждому ID
        # Формируем запрос: wmic path Win32_PnPEntity where "DeviceID='ID'" get Name,Manufacturer,SerialNumber /format:csv
        all_devices_data = []
        
        # Чтобы не делать 100 запросов к wmic (это медленно), попробуем собрать все ID в один запрос,
        # но wmic плохо работает с OR в where. Поэтому делаем цикл, но кэшируем результат, если устройств много.
        # Для простоты и надежности сделаем по одному запросу на устройство (для 5-10 флешек это мгновенно).
        
        for dev_id in storage_ids:
            # Экранируем кавычки для wmic
            safe_id = dev_id.replace('"', '\\"')
            cmd_details = [
                "wmic", "path", "Win32_PnPEntity",
                "where", f'DeviceID="{safe_id}"',
                "get", "Name,Manufacturer,PNPDeviceID,SerialNumber",
                "/format:csv"
            ]
            
            res = subprocess.run(cmd_details, capture_output=True, text=True, timeout=10, encoding="utf-8", errors="replace")
            
            if res.stdout.strip():
                reader = csv.DictReader(StringIO(res.stdout))
                for row in reader:
                    all_devices_data.append(row)

        if not all_devices_data:
            return "Не удалось получить детали устройств."

        # ФОРМАТИРОВАНИЕ ВЫВОДА
        output_lines = [f"{'Name':<45} {'Manufacturer':<20} {'Serial':<15} {'VID/PID'}"]
        output_lines.append("-" * 110)
        
        for dev in all_devices_data:
            name = (dev.get("Name") or "N/A")[:43]
            manuf = (dev.get("Manufacturer") or "N/A")[:18]
            serial = (dev.get("SerialNumber") or "N/A")[:13]
            pnp = dev.get("PNPDeviceID", "")
            
            vid = pid = "N/A"
            if "VID_" in pnp and "PID_" in pnp:
                parts = pnp.split("&")
                for part in parts:
                    if part.startswith("VID_"): vid = part.replace("VID_", "")
                    if part.startswith("PID_"): pid = part.replace("PID_", "")
            
            output_lines.append(f"{name:<45} {manuf:<20} {serial:<15} {vid}:{pid}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Произошла ошибка при сборе данных: {e}"

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
        f.write("[USB НАКОПИТЕЛИ (USBSTOR)]\n")
        f.write("=" * 60 + "\n")
        f.write(usb_info)
        f.write("\n\n")

if __name__ == "__main__":
    try:
        sys_info = get_system_info()
        usb_info = get_usb_storage_devices()
        save_to_log(sys_info, usb_info, LOG_FILE)
        print(f"Лог сохранен в: {LOG_FILE}")
        print("\n--- Результат сбора USBSTOR ---")
        print(usb_info)
    except PermissionError:
        print("ОШИБКА: Нет прав на запись в C:\\Logs. Запустите от имени Администратора!")
    except Exception as e:
        print(f"Критическая ошибка: {e}")