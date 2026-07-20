import os
import socket
import platform
from datetime import datetime
import subprocess
import ctypes
import re
import shutil

# --- МАГИЯ СКРЫТИЯ ОКНА ---
try:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
except Exception:
    pass

# --- КОНФИГУРАЦИЯ ПУТЕЙ ---
LOCAL_LOG_PATH = r"C:\Logs"
NETWORK_LOG_PATH = r"\\SRV-DNS-01\Android"  # Путь к общей папке
HOSTNAME = socket.gethostname()
LOG_FILENAME = f"{HOSTNAME}_usb_logs.log"

# Формируем полные пути
LOCAL_LOG_FILE = os.path.join(LOCAL_LOG_PATH, LOG_FILENAME)
NETWORK_LOG_FILE = os.path.join(NETWORK_LOG_PATH, LOG_FILENAME)

ANDROID_FOLDERS = {"DCIM", "Pictures", "Android", "Camera", "Movies", "Music", "Download"}
DEFAULT_DISK_GUID = "53F56307-B6BF-11D0-94F2-00A0C91EFB8B"


def check_network_path(path):
    """Проверяет, существует ли сетевой путь и доступен ли он для записи."""
    try:
        # Проверяем существование пути
        if not os.path.exists(path):
            return False
        
        # Пробуем создать тестовый файл, чтобы проверить права на запись
        test_file = os.path.join(path, ".write_test_" + str(datetime.now().timestamp()))
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        return True
    except (PermissionError, OSError):
        return False


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


def log_error(message, extra_context=""):
    """Универсальная функция логирования ошибок (в локальный файл)."""
    try:
        os.makedirs(LOCAL_LOG_PATH, exist_ok=True)
        message_latin = translit_text(message)
        full_msg = f"{extra_context} {message_latin}" if extra_context else message_latin
        
        with open(LOCAL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {full_msg}\n")
    except Exception as e:
        print(f"Critical logging failure: {e}")


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
    results = []
    
    disk_cmd = 'wmic logicaldisk get Caption,Description,DriveType'
    output, err = run_wmic_command(disk_cmd)

    if err:
        return [{"drive": "UNKNOWN", "status": "error", "paths": [translit_text("Не удалось получить список дисков")]}]

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
        results.append({
            "drive": "NONE",
            "status": "none",
            "paths": [translit_text("Съёмные диски не найдены")]
        })
        return results

    for drive in removable_drives:
        root_path = f"{drive}\\"
        drive_result = {
            "drive": drive,
            "status": "not_found",
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


def write_log_line(log_path, line_content):
    """Вспомогательная функция для записи одной строки в указанный файл."""
    try:
        dir_path = os.path.dirname(log_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line_content)
        return True
    except Exception as e:
        log_error(f"Не удалось записать в файл {log_path}: {str(e)}", extra_context="[Network/Local Log]")
        return False


def save_to_log(info, usb_output, disk_scan_results):
    # 1. Формируем общие данные системы
    sys_info_str = (
        f"sys_timestamp={info['timestamp']};"
        f"sys_hostname={info['hostname']};"
        f"sys_username={info['username']}"
    )

    # 2. Парсим USB-устройства
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

    # 3. Формируем отчет по дискам (единый для всех строк)
    disk_report_parts = []
    for res in disk_scan_results:
        paths_str = "^".join(res["paths"])
        paths_str = paths_str.replace(";", "^")
        disk_report_parts.append(
            f"drive={res['drive']};status={res['status']};paths={paths_str}"
        )
    full_disk_report = ";".join(disk_report_parts)

    # Если устройств нет — пишем одну строку
    if not usb_devices:
        base_line = f"{sys_info_str};usb_devices=none;disk_report={full_disk_report}\n"
        
        # Пытаемся записать на сетевой диск
        if check_network_path(NETWORK_LOG_PATH):
            write_log_line(NETWORK_LOG_FILE, base_line)
        else:
            log_error("Сетевая папка недоступна или нет прав. Запись только локально.", extra_context="[Network Check]")
            
        # Обязательно пишем локально (как бэкап)
        write_log_line(LOCAL_LOG_FILE, base_line)
        return

    # ГЛАВНАЯ ЛОГИКА: Для КАЖДОГО USB-устройства пишем ОТДЕЛЬНУЮ строку
    for parsed in usb_devices:
        usb_part = format_parsed_usb(parsed)
        full_line = f"{sys_info_str};{usb_part};disk_report={full_disk_report}\n"

        # --- ЗАПИСЬ НА СЕТЬ ---
        if check_network_path(NETWORK_LOG_PATH):
            success = write_log_line(NETWORK_LOG_FILE, full_line)
            if not success:
                log_error(f"Ошибка записи на сервер для устройства {parsed['serial']}", extra_context="[Network Write]")
        else:
            # Если сеть недоступна, логируем это один раз (не для каждой строки, чтобы не спамить)
            # Проверка делается выше в цикле, но можно вынести флаг, если строк тысячи.
            pass 

        # --- ЗАПИСЬ ЛОКАЛЬНО (БЭКАП) ---
        write_log_line(LOCAL_LOG_FILE, full_line)


if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_data = get_usb_devices_wmic()
        disk_data = scan_disks_for_android()

        save_to_log(system_info, usb_data, disk_data)

    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")