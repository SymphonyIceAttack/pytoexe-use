import os
import socket
import platform
from datetime import datetime
import subprocess
import ctypes
import re

# --- МАГИЯ СКРЫТИЯ ОКНА (Консоль исчезает) ---
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

# --- ТРАНСЛИТЕРАЦИЯ КИРИЛЛИЦЫ В ЛАТИНИЦУ ---
def translit_text(text: str) -> str:
    if not text:
        return text
    trans_table = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': 'y', 'ы': 'y', 'ь': "'", 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Shch',
        'Ъ': 'Y', 'Ы': 'Y', 'Ь': "'", 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }
    return ''.join(trans_table.get(ch, ch) for ch in text)

def log_error(message):
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        msg_latin = translit_text(message)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg_latin}\n")
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
            command, shell=True, capture_output=True, text=False, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        output = result.stdout.decode('cp866', errors='replace')
        error = result.stderr.decode('cp866', errors='replace') if result.stderr else ""
        if result.returncode != 0:
            return None, f"Ошибка WMIC: {error}"
        return output, None
    except subprocess.TimeoutExpired:
        return None, "Таймаут WMIC"
    except Exception as e:
        return None, str(e)

def parse_usb_device_id(device_id_string):
    res = {
        "bus_class": "USBSTOR",
        "dev_type": "", "vendor": "Unknown", "product": "Unknown",
        "rev": "Unknown", "serial": "Unknown"
    }
    match = re.search(r'USBSTOR\\([A-Z]+)&(.*?)\\(.+)', device_id_string)
    if not match:
        return res
    
    res["dev_type"] = match.group(1)
    props_part = match.group(2)
    serial_part = match.group(3)
    
    props = {}
    for item in props_part.split('&'):
        if '=' in item:
            k, v = item.split('=', 1)
            props[k] = v
    
    res["vendor"] = props.get("VEN", "Unknown")
    res["product"] = props.get("PROD", "Unknown")
    res["rev"] = props.get("REV", "Unknown")
    
    if '&' in serial_part:
        res["serial"] = serial_part.rsplit('&', 1)[0]
    else:
        res["serial"] = serial_part
        
    return res

def format_usb(parsed):
    return (f"bus={parsed['bus_class']};type={parsed['dev_type']};"
            f"vendor={parsed['vendor']};product={parsed['product']};"
            f"serial={parsed['serial']}")

def get_usb_devices_ordered():
    """
    Получает список USB устройств. Порядок зависит от того, как их вернет WMI.
    Это будет тот же порядок, который мы используем для сопоставления.
    """
    usb_list = []
    cmd = 'wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"'
    output, err = run_wmic_command(cmd)
    
    if err or not output:
        return usb_list

    lines = [l.strip() for l in output.splitlines() if l.strip()]
    for line in lines:
        if "Win32_PnPEntity" not in line:
            continue
        match = re.search(r'DeviceID="(.*?)"', line)
        if match:
            device_id = match.group(1)
            parsed_info = parse_usb_device_id(device_id)
            usb_list.append(parsed_info)
            
    return usb_list

def scan_disks_ordered():
    """
    Сканирует диски и возвращает список в порядке их обнаружения системой.
    Важно: порядок здесь должен совпадать с логикой получения списка дисков.
    """
    results = []
    # Получаем только съемные диски (DriveType = 2)
    cmd = 'wmic logicaldisk where "DriveType=2" get Caption'
    output, err = run_wmic_command(cmd)
    
    if err:
        # Если ошибка, возвращаем заглушку, чтобы скрипт не упал
        return [{"drive": "UNKNOWN", "status": "error", "paths": [translit_text("Ошибка получения списка дисков")]}]

    lines = [l.strip() for l in output.splitlines() if l.strip()]
    # Первая строка - заголовок "Caption", пропускаем её
    disks = []
    for line in lines[1:]:
        if line: # Убеждаемся, что строка не пустая
            disks.append(line)
    
    # Теперь сканируем каждый диск из списка
    for drive in disks:
        root = f"{drive}\\"
        res = {"drive": drive, "status": "not_found", "paths": []}
        res["paths"].append(translit_text(f"Проверка диска {drive}"))
        
        try:
            if os.path.exists(root):
                entries = os.listdir(root)
                found = False
                for entry in entries:
                    path = os.path.join(root, entry)
                    if os.path.isdir(path):
                        if entry.strip().lower() in {f.lower() for f in ANDROID_FOLDERS}:
                            res["paths"].append(f"{translit_text('[НАЙДЕНО]')} {path}")
                            found = True
                if found:
                    res["status"] = "found"
                else:
                    res["paths"].append(translit_text("[Нет характерных папок Android]"))
            else:
                res["paths"].append(translit_text("[Диск недоступен или не смонтирован]"))
                res["status"] = "error"
        except PermissionError:
            res["paths"].append(translit_text(f"[Отказано в доступе к диску {drive}]"))
            res["status"] = "error"
        except Exception as e:
            res["paths"].append(translit_text(f"[Ошибка сканирования: {e}]"))
            res["status"] = "error"
            
        results.append(res)
    return results

def save_to_log(info, usb_devices, disk_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    sys_info = (f"sys_timestamp={info['timestamp']};"
                f"sys_hostname={info['hostname']};"
                f"sys_username={info['username']}")

    count = min(len(usb_devices), len(disk_results))
    
    # 1. Пишем строки для пар (USB + Диск)
    for i in range(count):
        usb = usb_devices[i]
        disk = disk_results[i]
        
        usb_part = format_usb(usb)
        
        # Экранируем внутренние точки с запятой в путях заменой на ^
        paths_str = "^".join(disk["paths"])
        paths_str = paths_str.replace(";", "^")
        
        disk_part = f"drive={disk['drive']};status={disk['status']};paths={paths_str}"
        
        full_line = f"{sys_info};{usb_part};{disk_part}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_line)

    # 2. Если USB устройств больше, чем дисков -> пишем остаток USB без диска
    if len(usb_devices) > count:
        for i in range(count, len(usb_devices)):
            usb = usb_devices[i]
            usb_part = format_usb(usb)
            disk_part = "drive=none;status=unknown;paths=No_Disk_Assigned"
            full_line = f"{sys_info};{usb_part};{disk_part}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(full_line)

    # 3. Если дисков больше, чем USB (редкий кейс, но возможен при сбоях) -> пишем диски отдельно
    if len(disk_results) > count:
        for i in range(count, len(disk_results)):
            disk = disk_results[i]
            usb_part = "usb_devices=none"
            paths_str = "^".join(disk["paths"]).replace(";", "^")
            disk_part = f"drive={disk['drive']};status={disk['status']};paths={paths_str}"
            full_line = f"{sys_info};{usb_part};{disk_part}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(full_line)

if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data = get_usb_devices_ordered()
        disk_data = scan_disks_ordered()

        save_to_log(system_info, usb_data, disk_data, LOG_FILE)

    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")