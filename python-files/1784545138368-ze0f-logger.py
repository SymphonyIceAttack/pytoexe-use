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
            # Здесь разделитель не используется, оставляем как есть
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
    # Теперь используем ; вместо |
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


def find_android_folders():
    result_lines = []
    result_lines.append(translit_text("Поиск папок Android на съёмных дисках:"))

    disk_cmd = 'wmic logicaldisk get Caption,Description,DriveType'
    output, err = run_wmic_command(disk_cmd)

    if err:
        return [f"Не удалось получить список дисков: {translit_text(err)}"]

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
        return [translit_text("Съёмные диски не найдены.")]

    result_lines.append(translit_text(f"Найдено съёмных дисков: {', '.join(removable_drives)}"))

    for drive in removable_drives:
        root_path = f"{drive}\\"
        result_lines.append(translit_text(f"Проверка диска {drive}"))
        found_any = False

        try:
            if os.path.exists(root_path):
                entries = os.listdir(root_path)
                for entry in entries:
                    entry_path = os.path.join(root_path, entry)
                    if os.path.isdir(entry_path):
                        folder_name = entry.strip().lower()
                        if folder_name in {f.lower() for f in ANDROID_FOLDERS}:
                            result_lines.append(f"{translit_text('[НАЙДЕНО]')} {entry_path}")
                            found_any = True
                if not found_any:
                    result_lines.append(translit_text("[Нет характерных папок Android]"))
            else:
                result_lines.append(translit_text(f"[Диск недоступен или не смонтирован]"))
        except PermissionError:
            result_lines.append(translit_text(f"[Отказано в доступе к диску {drive}]"))
        except Exception as e:
            result_lines.append(translit_text(f"[Ошибка при сканировании {drive}: {e}]"))

    return result_lines


def save_to_log(info, usb_output, android_results, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    parts = []

    # SYSTEM INFO — теперь через ;
    sys_info_str = (
        f"sys_timestamp={info['timestamp']};"
        f"sys_hostname={info['hostname']};"
        f"sys_username={info['username']}"
    )
    parts.append(sys_info_str)

    # USB DEVICES
    usb_parts = []
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
                usb_parts.append(format_parsed_usb(parsed))

    if usb_parts:
        parts.append("usb_devices=" + ";".join(usb_parts))
    else:
        parts.append("usb_devices=none")

    # ANDROID FOLDERS
    android_results_latin = [translit_text(line) for line in android_results]
    
    # Сначала экранируем внутренние ; заменой на ^, чтобы не ломать структуру
    android_str = ";".join(android_results_latin)
    android_str = android_str.replace(";", "^")
    
    parts.append(f"android_results={android_str}")

    # ИТОГОВАЯ ОДНА СТРОКА — теперь все части разделены ;
    full_line = ";".join(parts) + "\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(full_line)


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