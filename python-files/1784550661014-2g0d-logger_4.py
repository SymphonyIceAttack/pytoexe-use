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

    result = []
    for ch in text:
        result.append(trans_table.get(ch, ch))
    return ''.join(result)


def log_error(message):
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        message_latin = translit_text(message)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message_latin}\n")
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
        "serial": "Unknown",
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
    return (
        f"bus={parsed_data['bus_class']};"
        f"type={parsed_data['dev_type']};"
        f"vendor={parsed_data['vendor']};"
        f"product={parsed_data['product']};"
        f"rev={parsed_data['rev']};"
        f"serial={parsed_data['serial']}"
    )


def get_usb_devices_wmic():
    cmd = 'wmic path Win32_USBControllerDevice get Dependent | find "USBSTOR"'
    output, err = run_wmic_command(cmd)
    if err:
        return err
    return output if output.strip() else "(Нет подключенных устройств USBSTOR)"


def scan_disks_for_android():
    """
    Возвращает список словарей: [{'drive': 'E:', 'status': 'found', 'paths': [...]}, ...]
    """
    results = []
    
    disk_cmd = 'wmic logicaldisk get Caption,Description,DriveType'
    output, err = run_wmic_command(disk_cmd)

    if err:
        # Если не смогли получить диски, возвращаем заглушку
        return [{"drive": "UNKNOWN", "status": "error", "paths": [translit_text("Не удалось получить список дисков")]}]

    lines = output.strip().splitlines()
    removable_drives = []

    # Парсим диски
    for line in lines[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        drive_letter = parts[0].strip()
        drive_type = parts[-1].strip()

        # Тип 2 = Removable Disk
        if drive_type == "2":
            removable_drives.append(drive_letter)

    if not removable_drives:
        results.append({
            "drive": "NONE",
            "status": "none",
            "paths": [translit_text("Съёмные диски не найдены")]
        })
        return results

    # Сканируем каждый диск
    for drive in removable_drives:
        root_path = f"{drive}\\"
        drive_result = {
            "drive": drive,
            "status": "not_found", # По умолчанию не найдено
            "paths": []
        }
        
        drive_result["paths"].append(translit_text(f"Проверка диска {drive}"))

        try:
            if os.path.exists(root_path):
                entries = os.listdir(root_path)
                found_any = False
                
                for entry in entries:
                    entry_path = os.path.join(root_path, entry)
                    if os.path.isdir(entry_path):
                        folder_name = entry.strip().lower()
                        if folder_name in {f.lower() for f in ANDROID_FOLDERS}:
                            drive_result["paths"].append(f"{translit_text('[НАЙДЕНО]')} {entry_path}")
                            found_any = True
                
                if found_any:
                    drive_result["status"] = "found"
                else:
                    drive_result["paths"].append(translit_text("[Нет характерных папок Android]"))
            else:
                drive_result["paths"].append(translit_text(f"[Диск недоступен или не смонтирован]"))
                drive_result["status"] = "error"
                
        except PermissionError:
            drive_result["paths"].append(translit_text(f"[Отказано в доступе к диску {drive}]"))
            drive_result["status"] = "error"
        except Exception as e:
            drive_result["paths"].append(translit_text(f"[Ошибка при сканировании {drive}: {e}]"))
            drive_result["status"] = "error"

        results.append(drive_result)

    return results


def save_to_log(info, usb_output, disk_scan_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # --- ЧАСТЬ 1: Информация о системе и USB (первые 2 строки) ---
    sys_info_str = (
        f"sys_timestamp={info['timestamp']};"
        f"sys_hostname={info['hostname']};"
        f"sys_username={info['username']}"
    )

    usb_devices = []
    if isinstance(usb_output, str):
        lines = usb_output.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line or "Win32_PnPEntity" not in line:
                continue
            match = re.search(r'DeviceID="(.*?)"', line)
            if match:
                device_id = match.group(1)
                parsed = parse_usb_device_id(device_id)
                usb_devices.append(parsed)

    # Строка 1: только данные системы
    part1_lines = [sys_info_str]

    # Строка 2: сводка по всем USB-устройствам
    if not usb_devices:
        usb_summary = "usb_devices=none"
    else:
        usb_parts = []
        for parsed in usb_devices:
            usb_parts.append(format_parsed_usb(parsed))
        usb_summary = "usb_devices=" + ";".join(usb_parts)

    part1_lines.append(usb_summary)

    # --- ЧАСТЬ 2: Информация о найденных папках (по каждому диску отдельно) ---
    part2_lines = []

    for res in disk_scan_results:
        paths_str = "^".join(res["paths"])
        # Экранируем возможные ; внутри путей, чтобы не ломать формат
        paths_str = paths_str.replace(";", "^")

        line = (
            f"drive={res['drive']};"
            f"status={res['status']};"
            f"paths={paths_str}"
        )
        part2_lines.append(line)

    # --- ЗАПИСЬ В ЛОГ ---
    with open(log_file, "a", encoding="utf-8") as f:
        # Пишем Часть 1 (2 строки)
        for line in part1_lines:
            f.write(line + "\n")
        
        # Разделитель между частями
        f.write("---DISK_REPORT_START---\n")
        
        # Пишем Часть 2 (строки по каждому диску)
        for line in part2_lines:
            f.write(line + "\n")
            
        # Завершающий разделитель
        f.write("---DISK_REPORT_END---\n\n")  # \n\n для отступа до следующего запуска


if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data = get_usb_devices_wmic()
        disk_data = scan_disks_for_android()

        save_to_log(system_info, usb_data, disk_data, LOG_FILE)

    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")