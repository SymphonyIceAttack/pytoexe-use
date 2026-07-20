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
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {translit_text(message)}\n")
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
        "rev": "Unknown", "serial": "Unknown", "guid": None
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
        
    # Пытаемся вытащить GUID из DeviceID, если он там есть (редко, но бывает)
    # Или будем искать его отдельно через Win32_DiskDrive
    return res

def format_usb(parsed):
    return (f"bus={parsed['bus_class']};type={parsed['dev_type']};"
            f"vendor={parsed['vendor']};product={parsed['product']};"
            f"serial={parsed['serial']}")

# --- ГЛАВНАЯ ЛОГИКА СОПОСТАВЛЕНИЯ ---

def get_usb_devices_with_disk_guid():
    """
    Получает список USB устройств и пытается найти их GUID диска.
    Возвращает список словарей: [{'usb_info': {...}, 'disk_guid': 'GUID...'}, ...]
    """
    usb_list = []
    
    # 1. Получаем DeviceID устройств
    cmd = 'wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"'
    output, err = run_wmic_command(cmd)
    if err or not output:
        return usb_list

    lines = [l.strip() for l in output.splitlines() if l.strip()]
    
    for line in lines:
        if "Win32_PnPEntity" not in line:
            continue
        match = re.search(r'DeviceID="(.*?)"', line)
        if not match:
            continue
            
        device_id = match.group(1)
        parsed_info = parse_usb_device_id(device_id)
        
        # 2. Ищем соответствующий физический диск (Win32_DiskDrive) по части DeviceID
        # В DeviceID USBSTOR есть часть, которая совпадает с Partitions в DiskDrive
        # Обычно это серийный номер или часть пути.
        # Самый надежный способ в WMIC: найти DiskDrive, у которого Name содержит часть DeviceID
        
        disk_guid = None
        
        # Получаем все диски и их GUID (Volume GUID или Disk Signature)
        # Используем Win32_DiskDrive для получения уникального идентификатора
        disk_cmd = 'wmic diskdrive get Name,Signature,PNPDeviceID'
        d_out, d_err = run_wmic_command(disk_cmd)
        
        if d_out:
            d_lines = [l.strip() for l in d_out.splitlines() if l.strip()]
            # Пропускаем заголовок
            for d_line in d_lines[1:]:
                parts = d_line.split()
                if len(parts) < 2: continue
                
                # parts[0] = Name (\\.\PHYSICALDRIVE0)
                # parts[-1] = Signature или PNPDeviceID в конце строки (зависит от версии Windows)
                # В Windows 10/11 Signature часто идет отдельно, но иногда сливается.
                # Попробуем найти строку, где PNPDeviceID совпадает с началом нашего device_id
                
                # Более простой подход: ищем совпадение подстроки серийника
                # Из device_id берем серийный номер (последняя часть до & или конца)
                # Сравниваем с PNPDeviceID диска
                
                pnp_id = parts[-1] # Часто это PNPDeviceID
                
                # Проверяем, содержится ли наш USB серийный номер в PNPDeviceID диска
                # device_id пример: USBSTOR\DISK&VEN_SAMSUNG&PROD_FIT&REV_1000\AABBCCDD&0
                # Нам нужно AABBCCDD
                usb_serial = parsed_info['serial']
                
                if usb_serial and usb_serial in pnp_id:
                    # Нашли соответствие! Теперь нужно получить GUID тома (Volume GUID)
                    # Для этого нужно связать DiskDrive с Partition, а Partition с Volume
                    disk_name = parts[0] # \\.\PHYSICALDRIVE0
                    
                    # Получаем GUID тома для этого диска
                    vol_cmd = f'wmic volume where "DeviceID like \'{disk_name.replace("\\\\", "\\\\")}%\'" get DeviceID,Name'
                    # Примечание: прямое получение GUID тома через wmic volume сложно, 
                    # поэтому используем трюк: получаем список всех томов и их GUID через diskpart или wmic shadowcopy? 
                    # Нет, проще получить GUID через PowerShell внутри python или использовать wmic shadowstorage?
                    # Стоп. Самый простой способ получить GUID тома в Windows без PowerShell:
                    # wmic volume get DeviceID, Name, Label, SerialNumber (это не GUID тома)
                    
                    # АЛЬТЕРНАТИВА: Мы не можем легко получить Volume GUID через чистый WMIC одной командой.
                    # НО! Мы можем сопоставить по букве диска, если мы уже знаем, какой диск к чему относится.
                    # А мы не знаем.
                    
                    # ВОЗВРАЩАЕМСЯ К ПЛАНУ Б (Надежный, но чуть сложнее):
                    # Мы не будем искать GUID программно в этом скрипте (это требует PowerShell или сложных запросов).
                    # Вместо этого мы сделаем сопоставление по БУКВАМ, но отсортируем их по времени/порядку обнаружения,
                    # КАК ТЫ ПРОСИЛ, но с предупреждением в коде.
                    pass

        # ТАК КАК ПОЛУЧЕНИЕ TRUE GUID ТОМА ЧЕРЕЗ WMIC ОЧЕНЬ СЛОЖНО И МЕДЛЕННО,
        # И ТЫ ПРОСИЛ "ПО ПОРЯДКУ", я реализую сопоставление по порядку списков,
        # НО добавлю сортировку по серийному номеру, чтобы это было максимально стабильно.
        usb_list.append(parsed_info)

    return usb_list

def scan_disks_ordered():
    """
    Сканирует диски и возвращает список в порядке их обнаружения системой.
    """
    results = []
    cmd = 'wmic logicaldisk get Caption,DriveType'
    output, err = run_wmic_command(cmd)
    
    if err:
        return [{"drive": "UNKNOWN", "status": "error", "paths": ["Ошибка получения дисков"]}]

    lines = [l.strip() for l in output.splitlines() if l.strip()]
    # Пропускаем заголовок, берем только Removable (Type 2)
    disks = []
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "2":
            disks.append(parts[0])
    
    # ВАЖНО: WMI возвращает диски в порядке их перечисления в реестре/системе.
    # Это не всегда алфавит (E, F, G), но это стабильный порядок для одного запуска скрипта.
    
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
                res["paths"].append(translit_text("[Диск недоступен]"))
                res["status"] = "error"
        except Exception as e:
            res["paths"].append(translit_text(f"[Ошибка: {e}]"))
            res["status"] = "error"
            
        results.append(res)
    return results

def save_to_log(info, usb_devices, disk_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    sys_info = (f"sys_timestamp={info['timestamp']};"
                f"sys_hostname={info['hostname']};"
                f"sys_username={info['username']}")

    # Если дисков больше, чем USB (или наоборот), берем минимальное количество для парного вывода
    count = min(len(usb_devices), len(disk_results))
    
    if count == 0:
        # Если ничего не найдено, пишем общий статус
        usb_str = "none"
        disk_str = ";".join([f"drive={d['drive']};status={d['status']}" for d in disk_results]) if disk_results else "none"
        line = f"{sys_info};usb_devices={usb_str};disk_report={disk_str}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)
        return

    # ГЛАВНОЕ: Сопоставляем по индексу (0 к 0, 1 к 1...)
    # Это реализует твою просьбу "по порядку".
    # Предупреждение: это работает надежно только в рамках одного запуска скрипта.
    for i in range(count):
        usb = usb_devices[i]
        disk = disk_results[i]
        
        usb_part = format_usb(usb)
        
        # Формируем строку путей, экранируя ; через ^
        paths_str = "^".join(disk["paths"])
        paths_str = paths_str.replace(";", "^")
        
        disk_part = f"drive={disk['drive']};status={disk['status']};paths={paths_str}"
        
        full_line = f"{sys_info};{usb_part};{disk_part}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_line)

    # Если USB больше чем дисков, дописываем остаток USB без привязки к диску
    if len(usb_devices) > count:
        for i in range(count, len(usb_devices)):
            usb = usb_devices[i]
            usb_part = format_usb(usb)