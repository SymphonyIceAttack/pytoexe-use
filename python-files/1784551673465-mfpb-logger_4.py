
import os
import socket
import platform
from datetime import datetime
import json
import ctypes
import re
import wmi

# --- МАГИЯ СКРЫТИЯ ОКНА ---
try:
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
except Exception:
    pass

LOG_PATH = r"C:\Logs"
HOSTNAME = socket.gethostname()
LOG_FILE = os.path.join(LOG_PATH, f"{HOSTNAME}_usb_logs.json")

ANDROID_FOLDERS = {"DCIM", "Pictures", "Android", "Camera", "Movies", "Music", "Download"}


def translit_text(text: str) -> str:
    """Простая транслитерация кириллицы в латиницу."""
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


def log_error(message: str):
    try:
        os.makedirs(LOG_PATH, exist_ok=True)
        message_latin = translit_text(message)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[ERROR] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message_latin}\n")
    except Exception:
        pass


def get_system_info():
    return {
        "timestamp": datetime.now().isoformat(),
        "hostname": HOSTNAME,
        "username": os.environ.get("USERNAME") or os.environ.get("USER", "unknown"),
    }


def parse_usb_device_id(device_id_string: str):
    """
    Парсит DeviceID вида: USBSTOR\Disk&Ven_...&Prod_...&Rev_...\Serial
    Возвращает dict с vendor, product, rev, serial.
    """
    result = {
        "bus_class": "USBSTOR",
        "dev_type": "Disk",
        "vendor": "Unknown",
        "product": "Unknown",
        "rev": "Unknown",
        "serial": "Unknown"
    }

    match = re.search(r'USBSTOR\\([A-Z]+)&(.*?)\\(.+)', device_id_string)
    if not match:
        # Если формат не совпал, всё равно возвращаем заглушку
        return result

    dev_type_raw = match.group(1)
    props_part = match.group(2)
    serial_part = match.group(3)

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

    # Серийник может содержать &, поэтому берём всё после последнего &
    if '&' in serial_part:
        serial_val = serial_part.rsplit('&', 1)[0]
        result["serial"] = serial_val
    else:
        result["serial"] = serial_part

    return result


def scan_android_folders_on_drive(drive_letter: str):
    """Сканирует корень диска на наличие папок Android и возвращает отчёт по этому диску."""
    root_path = f"{drive_letter}\\"
    report = {
        "letter": drive_letter,
        "status": "not_found",
        "paths": [],
        "found_folders": []
    }

    report["paths"].append(translit_text(f"Проверка диска {drive_letter}"))

    if not os.path.exists(root_path):
        report["paths"].append(translit_text(f"[Диск недоступен или не смонтирован]"))
        report["status"] = "error"
        return report

    try:
        entries = os.listdir(root_path)
    except PermissionError:
        report["paths"].append(translit_text(f"[Отказано в доступе к диску {drive_letter}]"))
        report["status"] = "error"
        return report
    except Exception as e:
        report["paths"].append(translit_text(f"[Ошибка при сканировании {drive_letter}: {e}]"))
        report["status"] = "error"
        return report

    found_any = False
    for entry in entries:
        entry_path = os.path.join(root_path, entry)
        if os.path.isdir(entry_path):
            folder_name = entry.strip().lower()
            if folder_name in {f.lower() for f in ANDROID_FOLDERS}:
                report["paths"].append(f"{translit_text('[НАЙДЕНО]')} {entry_path}")
                report["found_folders"].append(entry)
                found_any = True

    if found_any:
        report["status"] = "found"
    else:
        report["paths"].append(translit_text("[Нет характерных папок Android]"))

    return report


def build_usb_disk_mapping():
    """
    Строит надёжное соответствие: USB-устройство -> список логических дисков (букв).
    Использует WMI-связи: Win32_DiskDrive (USB) -> разделы -> логические диски.
    Возвращает список словарей:
      [
        {
          "device_id": "...",
          "parsed": {...},
          "drives": [ { "letter": "E:", "status": "...", "paths": [...] }, ... ]
        },
        ...
      ]
    """
    c = wmi.WMI()

    # 1. Получаем все USB-диски (Win32_DiskDrive, InterfaceType == 'USB')
    usb_disk_drives = []
    for disk in c.Win32_DiskDrive():
        if disk.InterfaceType.upper() == "USB":
            usb_disk_drives.append(disk)

    # 2. Для каждого USB-диска находим его разделы и логические диски
    mapped_devices = []

    for disk in usb_disk_drives:
        device_id = disk.PNPDeviceID  # Это тот самый DeviceID, который можно сопоставить с USBSTOR
        parsed = parse_usb_device_id(device_id)

        # Получаем разделы этого диска
        partitions = list(c.Win32_DiskPartition(DiskIndex=disk.Index))

        drive_reports = []
        for part in partitions:
            # Получаем логические диски, привязанные к этому разделу
            logical_disks = list(c.Win32_LogicalDisk(Partition=part))
            for ld in logical_disks:
                letter = ld.Caption  # например, "E:"
                if not letter:
                    continue
                drive_report = scan_android_folders_on_drive(letter)
                drive_reports.append(drive_report)

        if drive_reports:
            mapped_devices.append({
                "device_id": device_id,
                "parsed": parsed,
                "drives": drive_reports
            })
        else:
            # Устройство есть, но ни одного логического диска не найдено (например, нет разделов)
            mapped_devices.append({
                "device_id": device_id,
                "parsed": parsed,
                "drives": []
            })

    return mapped_devices


def save_to_log(info, usb_devices, log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    log_entry = {
        "system": info,
        "usb_devices": []
    }

    for dev in usb_devices:
        log_entry["usb_devices"].append({
            "device_id": dev["device_id"],
            "bus": dev["parsed"]["bus_class"],
            "type": dev["parsed"]["dev_type"],
            "vendor": dev["parsed"]["vendor"],
            "product": dev["parsed"]["product"],
            "rev": dev["parsed"]["rev"],
            "serial": dev["parsed"]["serial"],
            "drives": dev["drives"]
        })

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        system_info = get_system_info()
        usb_devices = build_usb_disk_mapping()
        save_to_log(system_info, usb_devices, LOG_FILE)
    except PermissionError:
        log_error("Нет прав на запись в C:\\Logs. Требуется запуск от администратора.")
    except Exception as e:
        log_error(f"Критическая ошибка скрипта: {str(e)}")