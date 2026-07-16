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
    # ОСТАВИЛИ ТОЛЬКО САМОЕ НУЖНОЕ
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
        "serial": "Unknown",
        # GUID тут остаётся для внутренней логики, но мы его просто не будем писать в лог
        "guid": DEFAULT_DISK_GUID
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

def format_parsed_usb(parsed_data):
    # УБРАЛИ GUID ИЗ ВЫВОДА
    lines = [
        f"bus_class: {parsed_data['bus_class']}",
        f"dev_type: {parsed_data['dev_type']}",
        f"vendor: {parsed_data['vendor']}",
        f"product: {parsed_data['product']}",
        f"rev: {parsed_data['rev']}",
        f"serial: {parsed_data['serial']}"
    ]
    return "\n".join(lines)

def get_usb_devices_wmic():
    cmd = 'wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"'
    output, err = run_wmic_command(cmd)
    if err:
        return err
    return output if output.strip() else "(Нет подключенных устройств USBSTOR)"

def find_android_folders():
    result_lines = []
    result_lines.append("Поиск папок Android на съёмных дисках:")
    
    disk_cmd = 'wmic logicaldisk get Caption,Description,DriveType'
    output, err = run_wmic_command(disk_cmd)
    
    if err:
        return [f"Не удалось получить список дисков: {err}"]

    lines = output.strip().splitlines()
    removable_drives = []

    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        drive_letter = parts[0].strip()
        drive_type = parts[-1].strip()
        
        if drive_type == "2":
            removable_drives.append(drive_letter)

    if not removable_drives:
        return ["Съёмные диски не найдены."]

    result_lines.append(f"Найдено съёмных дисков: {', '.join(removable_drives)}\n")

    for drive in removable_drives:
        root_path = f"{drive}\\"
        result_lines.append(f"--- Проверка диска {drive} ---")
        found_any = False
        
        try:
            if os.path.exists(root_path):
                entries = os.listdir(root_path)
                for entry in entries:
                    entry_path = os.path.join(root_path, entry)
                    if os.path.isdir(entry_path):
                        folder_name = entry.strip().lower()
                        if folder_name in {f.lower() for f in ANDROID_FOLDERS}:
                            result_lines.append(f"[НАЙДЕНО] {entry_path}")
                            found_any = True
                if not found_any:
                    result_lines.append(f"[Нет характерных папок Android]")
            else:
                result_lines.append(f"[Диск недоступен или не смонтирован]")
        except PermissionError:
            result_lines.append(f"[Отказано в доступе к диску {drive}]")
        except Exception as e:
            result_lines.append(f"[Ошибка при сканировании {drive}: {e}]")

    return result_lines

def save_to_log(info, usb_output, android_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write(f"LOG ENTRY: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        # --- SYSTEM INFO: ТОЛЬКО МИНИМУМ ---
        f.write("--- SYSTEM INFO ---\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n--- USB DEVICES (PARSED DETAILS) ---\n")
        if isinstance(usb_output, str):
            lines = usb_output.strip().splitlines()
            found_devices = False
            for line in lines:
                line = line.strip()
                if not line or "Win32_PnPEntity" not in line:
                    continue
                
                match = re.search(r'DeviceID="(.*?)"', line)
                if match:
                    found_devices = True
                    device_id = match.group(1)
                    parsed = parse_usb_device_id(device_id)
                    f.write(format_parsed_usb(parsed) + "\n")
                    # Разделитель после каждого устройства, но без лишнего текста
                    f.write("-" * 30 + "\n")
            
            if not found_devices:
                f.write("Не удалось распарсить данные об устройствах.\n")
        else:
            f.write("Нет данных об USB устройствах.\n")

        # БЛОК RAW USB DEVICES ПОЛНОСТЬЮ УДАЛЁН
        
        f.write("\n--- ANDROID FOLDERS SEARCH RESULTS ---\n")
        for line in android_results:
            f.write(line + "\n")
            
        f.write("=" * 60 + "\n\n")

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data = get_usb_devices_wmic()
        android_data = find_android_folders()
        
        save_to_log(system_info, usb_data, android_data, LOG_FILE)
        
    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")