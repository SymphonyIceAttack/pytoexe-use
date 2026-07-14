import os
import sys
import logging
import socket
import getpass
import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

# Библиотеки для Windows WMI (только для Windows)
if sys.platform == "win32":
    import wmi
    import win32api
    import win32con
    import win32file
else:
    raise OSError("Этот скрипт предназначен только для ОС Windows.")

# --- ЛОГИКА ОПРЕДЕЛЕНИЯ ПУТИ ДЛЯ ЛОГА ---
DEFAULT_LOG_FOLDER = r"C:\Logs"
FALLBACK_LOG_NAME = "usb_android_scan.log"

def get_log_path():
    """
    Пытается вернуть путь C:\Logs\usb_android_scan.log.
    Если нет прав или ошибка - возвращает путь рядом с exe/скриптом.
    """
    try:
        target_dir = Path(DEFAULT_LOG_FOLDER)
        target_dir.mkdir(parents=True, exist_ok=True)

        test_file = target_dir / ".write_test"
        test_file.touch()
        test_file.unlink()

        return str(target_dir / FALLBACK_LOG_NAME)
    except PermissionError:
        print(f"[!] Нет прав на запись в {DEFAULT_LOG_FOLDER}. Используем альтернативный путь.")
    except Exception as e:
        print(f"[!] Ошибка доступа к {DEFAULT_LOG_FOLDER}: {e}. Используем альтернативный путь.")

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(application_path, FALLBACK_LOG_NAME)

LOG_FILE = get_log_path()

def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        encoding="utf-8"
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    logging.getLogger().addHandler(console_handler)

    logging.info(f"Инициализация логгера. Путь к файлу: {LOG_FILE}")

def get_system_info():
    return {
        "pc_name": socket.gethostname(),
        "username": getpass.getuser(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_disk_serial_number(drive_letter):
    try:
        vol_name, _, serial_num, _ = win32file.GetVolumeInformation(drive_letter + ":\\")
        return str(serial_num) if serial_num else None
    except Exception:
        return None

def scan_usb_devices():
    c = wmi.WMI()
    usb_info_list = []

    logical_disks = {ld.DeviceID: ld for ld in c.Win32_LogicalDisk()}

    for disk in c.Win32_DiskDrive():
        if disk.InterfaceType != "USB":
            continue

        serial = disk.SerialNumber.strip() if disk.SerialNumber else "N/A"
        model = disk.Model.strip() if disk.Model else "N/A"
        size_gb = round(int(disk.Size) / (1024**3), 2) if disk.Size else 0

        partitions = c.Win32_DiskPartition(DiskIndex=disk.Index)
        drive_letters = []
        for part in partitions:
            logical_disk = next((ld for ld in logical_disks.values() if ld.DeviceID == part.Caption), None)
            if logical_disk and logical_disk.DeviceID:
                drive_letters.append(logical_disk.DeviceID)

        for letter in drive_letters:
            serial_vol = get_disk_serial_number(letter)
            path = f"{letter}:\\Android"
            has_android_folder = os.path.isdir(path)

            info = {
                "disk_model": model,
                "disk_size_gb": size_gb,
                "device_serial": serial,
                "volume_serial": serial_vol,
                "drive_letter": letter,
                "has_android_folder": has_android_folder,
                "android_path": path if has_android_folder else None,
                "interface": disk.InterfaceType
            }
            usb_info_list.append(info)

    return usb_info_list

def write_json_report(system_info, usb_data, output_path):
    report = {
        "system": system_info,
        "devices": usb_data
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    logging.info(f"[ОТЧЁТ] JSON сохранён: {output_path}")

def write_csv_report(system_info, usb_data, output_path):
    fieldnames = [
        "disk_model", "disk_size_gb", "device_serial", "volume_serial",
        "drive_letter", "interface", "has_android_folder", "android_path"
    ]
    # Добавляем системные данные как отдельные строки или в отдельный файл — здесь добавим как метаданные в первую строку
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(usb_data)

    # Отдельно сохраним системные данные в тот же CSV как комментарий (первая строка)
    # Но CSV не поддерживает комментарии «из коробки», поэтому лучше сохранить метаданные в лог или отдельным TXT.
    # Здесь просто запишем их в лог, чтобы не ломать формат CSV.
    logging.info(f"[ОТЧЁТ] CSV сохранён: {output_path}")
    logging.info(f"[МЕТАДАННЫЕ] ПК: {system_info['pc_name']}, Пользователь: {system_info['username']}, Время: {system_info['timestamp']}")

def log_results(system_info, usb_data):
    logging.info("=" * 60)
    logging.info(f"СКАНИРОВАНИЕ USB‑УСТРОЙСТВ")
    logging.info(f"Дата/время: {system_info['timestamp']}")
    logging.info(f"Имя ПК: {system_info['pc_name']}")
    logging.info(f"Пользователь: {system_info['username']}")
    logging.info("=" * 60)

    if not usb_data:
        logging.warning("Подключённых USB‑накопителей с буквой диска не найдено.")
        return

    for i, dev in enumerate(usb_data, 1):
        logging.info(f"\n--- Устройство #{i} ---")
        logging.info(f"Модель диска: {dev['disk_model']}")
        logging.info(f"Размер: {dev['disk_size_gb']} ГБ")
        logging.info(f"Серийный номер устройства: {dev['device_serial']}")
        logging.info(f"Серийный номер тома: {dev['volume_serial'] or 'Недоступен'}")
        logging.info(f"Буква диска: {dev['drive_letter']}")
        logging.info(f"Интерфейс: {dev['interface']}")

        if dev["has_android_folder"]:
            logging.info(f"[НАЙДЕНО] Папка Android: {dev['android_path']}")
        else:
            logging.info("[НЕТ] Папка Android не найдена.")

    logging.info("=" * 60)
    logging.info("Сканирование завершено.")

def main():
    parser = argparse.ArgumentParser(description="Сканирование USB-устройств на наличие папки Android")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Формат отчёта (по умолчанию: json)")
    parser.add_argument("--output", type=str, help="Путь к файлу отчёта. Если не указан, генерируется автоматически рядом с логом.")
    args = parser.parse_args()

    setup_logging()
    system_info = get_system_info()
    logging.info(f"Запуск сканирования от пользователя: {system_info['username']} на ПК: {system_info['pc_name']}")

    usb_data = scan_usb_devices()
    log_results(system_info, usb_data)

    # Определение пути для отчёта
    if args.output:
        report_path = args.output
    else:
        # Автоматически: папка лога или рядом со скриптом
        log_dir = os.path.dirname(LOG_FILE)
        base_name = "usb_android_report"
        ext = ".json" if args.format == "json" else ".csv"
        report_path = os.path.join(log_dir, f"{base_name}{ext}")

    # Запись отчёта в выбранном формате
    if args.format == "json":
        write_json_report(system_info, usb_data, report_path)
    elif args.format == "csv":
        write_csv_report(system_info, usb_data, report_path)

if __name__ == "__main__":
    main()