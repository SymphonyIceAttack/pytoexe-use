import os
import socket
import platform
from datetime import datetime
import subprocess
import ctypes
import re

# --- МАГИЯ СКРЫТИЯ ОКНА ---
try:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
except Exception:
    pass

LOG_PATH = r"C:\Logs"
HOSTNAME = socket.gethostname()
LOG_FILE = os.path.join(LOG_PATH, f"{HOSTNAME}_usb_logs.log")

ANDROID_FOLDERS = {"DCIM", "Pictures", "Android", "Camera", "Movies", "Music", "Download"}

DEFAULT_DISK_GUID = "53F56307-B6BF-11D0-94F2-00A0C91EFB8B"

def log_error(message):
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except:
        pass

def get_system_info():
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": HOSTNAME,
        "username": os.environ.get("USERNAME") or os.environ.get("USER", "unknown"),
    }

def run_wmic_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=False,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW 
        )
        
        output = result.stdout.decode('cp866', errors='replace')
        error = result.stderr.decode('cp866', errors='replace') if result.stderr else ""
        
        if result.returncode != 0:
            return None, f"Ошибка WMIC: {error}"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Ошибка: выполнение команды WMIC заняло слишком много времени."
    except Exception as e:
        return None, str(e)

def parse_usb_device_id(device_id_string):
    result = {
        "bus_class": "",
        "dev_type": "",
        "vendor": "Unknown",
        "product": "Unknown",
        "rev": "Unknown",
        "serial": "Unknown"
    }

    match = re.search(r'USBSTOR\\([A-Z]+)&(.*?)\\(.+)', device_id_string)
    if not match:
        result["bus_class"] = "USBSTOR"
        return result

    dev_type_raw = match.group(1)
    props_part = match.group(2)
    serial_part = match.group(3)

    result["bus_class"] = "USBSTOR"
    result["dev_type"] = dev_type_raw

    props = {}
    for item in props_part.split('&'):
        if '=' in item:
            k, v = item.split('=', 1)
            props[k] = v
        elif '_' in item:
            key_val = item.split('_', 1)
            if len(key_val) == 2:
                props[key_val[0]] = key_val[1]

    result["vendor"] = props.get("VEN", "Unknown")
    result["product"] = props.get("PROD", "Unknown")
    result["rev"] = props.get("REV", "Unknown")

    if '&' in serial_part:
        serial_val = serial_part.rsplit('&', 1)[0]
        result["serial"] = serial_val
    else:
        result["serial"] = serial_part

    return result

def get_usb_devices_wmic():
    # Получаем список устройств. Для компактности берём только DeviceID
    cmd = 'wmic path Win32_PnPEntity where "DeviceID like \'USBSTOR%\'" get DeviceID /format:list'
    output, err = run_wmic_command(cmd)
    
    if err:
        return [], err
    
    devices = []
    current_device = {}
    
    # Парсим формат list: DeviceID=...\r\n\r\n
    blocks = output.strip().split("\r\n\r\n")
    for block in blocks:
        if "DeviceID=" in block:
            device_id = block.split("DeviceID=", 1)[1].strip()
            parsed = parse_usb_device_id(device_id)
            devices.append(parsed)
            
    return devices, None

def find_android_folders():
    disk_cmd = 'wmic logicaldisk get Caption,DriveType'
    output, err = run_wmic_command(disk_cmd)
    
    if err:
        return []

    lines = output.strip().splitlines()
    removable_drives = []

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 2:
            continue
        drive_letter = parts[0].strip()
        drive_type = parts[-1].strip()
        
        # DriveType 2 = Removable Disk
        if drive_type == "2":
            removable_drives.append(drive_letter)

    found_paths = []
    
    for drive in removable_drives:
        root_path = f"{drive}\\"
        try:
            if os.path.exists(root_path):
                entries = os.listdir(root_path)
                for entry in entries:
                    entry_path = os.path.join(root_path, entry)
                    if os.path.isdir(entry_path):
                        folder_name = entry.strip().lower()
                        if folder_name in {f.lower() for f in ANDROID_FOLDERS}:
                            found_paths.append(f"[НАЙДЕНО] {entry_path}")
        except PermissionError:
            found_paths.append(f"[Отказано в доступе к диску {drive}]")
        except Exception as e:
            found_paths.append(f"[Ошибка сканирования {drive}: {e}]")

    return found_paths

def save_to_log(info, usb_devices, android_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Извлекаем данные для одной строки
    timestamp = info.get("timestamp", "Unknown")
    hostname = info.get("hostname", "Unknown")
    username = info.get("username", "Unknown")
    
    # Берем первое устройство из списка, если есть
    if usb_devices and len(usb_devices) > 0:
        first_usb = usb_devices[0]
        vendor = first_usb.get("vendor", "Unknown")
        product = first_usb.get("product", "Unknown")
        serial = first_usb.get("serial", "Unknown")
    else:
        vendor, product, serial = "NoUSB", "NoUSB", "NoUSB"
    
    # Формируем строку найденных папок (через запятую)
    if android_results:
        android_str = ", ".join(android_results)
    else:
        android_str = "[Папки не найдены]"

    # ФОРМИРУЕМ ИТОГОВУЮ СТРОКУ
    log_line = f"{timestamp} || {hostname} || {username} || {vendor} || {product} || {serial} || {android_str}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data, usb_err = get_usb_devices_wmic()
        android_data = find_android_folders()
        
        save_to_log(system_info, usb_data, android_data, LOG_FILE)
        
    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")