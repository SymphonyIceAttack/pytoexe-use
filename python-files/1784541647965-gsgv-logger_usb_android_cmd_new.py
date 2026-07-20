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
        
        # Пробуем разные кодировки, если cp866 не подходит (частая проблема на разных Windows)
        encodings = ['cp866', 'utf-8', 'latin1']
        output = ""
        error = ""
        
        for enc in encodings:
            try:
                output = result.stdout.decode(enc, errors='ignore')
                break
            except:
                continue
                
        for enc in encodings:
            try:
                error = result.stderr.decode(enc, errors='ignore') if result.stderr else ""
                break
            except:
                continue
        
        if result.returncode != 0:
            return None, f"Ошибка WMIC: {error}"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Ошибка: выполнение команды WMIC заняло слишком много времени."
    except Exception as e:
        return None, str(e)

def parse_usb_device_id(device_id_string):
    result = {
        "bus_class": "USBSTOR",
        "dev_type": "Unknown",
        "vendor": "Unknown",
        "product": "Unknown",
        "rev": "Unknown",
        "serial": "Unknown"
    }

    # Очистка строки от мусора, если есть
    device_id = device_id_string.strip()
    
    # Ищем основную структуру: USBSTOR\TYPE&...
    match = re.search(r'USBSTOR\\([A-Za-z0-9]+)&', device_id)
    if match:
        result["dev_type"] = match.group(1)

    # Разбиваем строку на части после USBSTOR
    # Пример: USBSTOR\DISK&VEN_GENERIC&PROD_FLASH_DISK&REV_PMAP\123456789&0
    parts_after_usbstor = device_id.split('USBSTOR\\')[-1]
    
    # Сначала берем всё до последнего слэша (там лежат свойства и тип)
    core_part, _, serial_candidate = parts_after_usbstor.rpartition('\\')
    
    # Извлекаем серийный номер (берем всё до первого '&' в конце, убирая хвост типа '&0')
    if serial_candidate:
        clean_serial = serial_candidate.split('&')[0]
        if clean_serial:
            result["serial"] = clean_serial

    # Теперь разбираем core_part (где VEN, PROD, REV)
    # Формат может быть: DISK&VEN_...&PROD_...&REV_...
    props = {}
    
    # Разделяем по &
    tokens = core_part.split('&')
    
    for token in tokens:
        if '=' in token:
            k, v = token.split('=', 1)
            props[k] = v
        elif '_' in token:
            # Пытаемся найти паттерны VEN_..., PROD_..., REV_...
            if token.startswith('VEN_'):
                result["vendor"] = token.replace('VEN_', '')
            elif token.startswith('PROD_'):
                result["product"] = token.replace('PROD_', '')
            elif token.startswith('REV_'):
                result["rev"] = token.replace('REV_', '')
        else:
            # Если это просто слово (например, DISK), это может быть dev_type, но мы уже взяли его выше
            pass
            
    # Если через нижнее подчеркивание не нашли, пробуем поискать в виде KEY=VALUE внутри всей строки
    # Иногда WMIC выдает иначе
    if result["vendor"] == "Unknown":
        m = re.search(r'VEN_?=([^&\\]+)', device_id)
        if m: result["vendor"] = m.group(1)
        
    if result["product"] == "Unknown":
        m = re.search(r'PROD_?=([^&\\]+)', device_id)
        if m: result["product"] = m.group(1)
        
    if result["rev"] == "Unknown":
        m = re.search(r'REV_?=([^&\\]+)', device_id)
        if m: result["rev"] = m.group(1)

    return result

def get_usb_devices_wmic():
    # Используем формат list для надежного парсинга
    cmd = 'wmic path Win32_PnPEntity where "DeviceID like \'USBSTOR%\'" get DeviceID /format:list'
    output, err = run_wmic_command(cmd)
    
    if err:
        return [], err
    
    devices = []
    blocks = output.strip().split("\r\n\r\n")
    
    for block in blocks:
        block = block.strip()
        if not block: continue
        
        # Ищем DeviceID=...
        match = re.search(r'DeviceID\s*=\s*"([^"]+)"', block)
        if not match:
            match = re.search(r'DeviceID=(\S+)', block) # Fallback без кавычек
            
        if match:
            device_id = match.group(1)
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
        # DriveType 2 = Removable Disk
        if parts[-1].strip() == "2":
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
    
    timestamp = info.get("timestamp", "Unknown")
    hostname = info.get("hostname", "Unknown")
    username = info.get("username", "Unknown")
    
    if usb_devices and len(usb_devices) > 0:
        first_usb = usb_devices[0]
        usb_details = (
            f"bus_class: {first_usb.get('bus_class', 'Unknown')} || "
            f"dev_type: {first_usb.get('dev_type', 'Unknown')} || "
            f"vendor: {first_usb.get('vendor', 'Unknown')} || "
            f"product: {first_usb.get('product', 'Unknown')} || "
            f"rev: {first_usb.get('rev', 'Unknown')}"
        )
        serial = first_usb.get("serial", "NoSerial")
    else:
        usb_details = "bus_class: NoUSB || dev_type: NoUSB || vendor: NoUSB || product: NoUSB || rev: NoUSB"
        serial = "NoUSB"
    
    if android_results:
        android_str = ", ".join(android_results)
    else:
        android_str = "[Папки не найдены]"

    log_line = (
        f"{timestamp} || {hostname} || {username} || "
        f"{usb_details} || {serial} || {android_str}\n"
    )
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data, usb_err = get_usb_devices_wmic()
        
        if usb_err:
            log_error(usb_err)
            # Даже если USB не найден, можно попробовать найти папки на дисках, 
            # но для чистоты лога лучше записать ошибку или заглушку.
            # Здесь мы всё равно запустим поиск папок, но USB данные будут заглушками.
            android_data = find_android_folders()
            save_to_log(system_info, [], android_data, LOG_FILE)
        else:
            android_data = find_android_folders()
            save_to_log(system_info, usb_data, android_data, LOG_FILE)
        
    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")