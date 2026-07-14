import os
import sys
import logging
import platform
import getpass
import psutil  # pip install psutil
import wmi      # pip install wmi (только для Windows)
from datetime import datetime

# Настройка логирования
LOG_DIR = r"C:\Logs"
LOG_FILE = os.path.join(LOG_DIR, "usb_scan.log")

os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def get_system_info():
    """Собирает информацию о системе и пользователе."""
    info = {
        "hostname": platform.node(),
        "os": platform.system() + " " + platform.release(),
        "processor": platform.processor(),
        "architecture": platform.machine(),
        "python_version": sys.version,
        "username": getpass.getuser(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    }
    return info

def log_system_info(info):
    """Логирует информацию о системе."""
    logging.info("--- Информация о системе ---")
    for key, value in info.items():
        logging.info(f"{key}: {value}")
    logging.info("---------------------------")

def find_android_folders(drive):
    """Рекурсивно ищет папку 'Android' на указанном диске."""
    android_paths = []
    try:
        for root, dirs, files in os.walk(drive, topdown=True):
            # Оптимизация: пропускаем скрытые папки, если нужно
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            if "Android" in dirs:
                android_path = os.path.join(root, "Android")
                android_paths.append(android_path)
                # Можно прекратить поиск глубже в этой ветке, если нужна только первая находка
                # dirs[:] = [] 
    except PermissionError:
        logging.warning(f"Нет доступа к диску {drive}, пропускаем.")
    except Exception as e:
        logging.error(f"Ошибка при сканировании {drive}: {e}")
    
    return android_paths

def scan_usb_drives():
    """Находит подключенные USB-накопители и ищет на них папку Android."""
    c = wmi.WMI()
    usb_drives = []

    # Получаем все логические диски
    logical_disks = c.Win32_LogicalDisk()

    for disk in logical_disks:
        # Фильтруем только съемные диски (USB)
        if disk.DriveType == 2:  # 2 = Removable Disk
            drive_letter = disk.Caption
            usb_drives.append(drive_letter)
            logging.info(f"Найден съемный диск: {drive_letter}")

    if not usb_drives:
        logging.info("Съемные USB-диски не найдены.")
        return

    for drive in usb_drives:
        full_drive = f"{drive}\\"
        logging.info(f"Сканирование диска: {full_drive}")
        
        android_found = find_android_folders(full_drive)
        
        if android_found:
            logging.info(f"На диске {drive} найдена папка Android по пути(ям):")
            for path in android_found:
                logging.info(f"  -> {path}")
        else:
            logging.info(f"На диске {drive} папка 'Android' не найдена.")

def main():
    try:
        logging.info("Запуск сканирования USB и поиска папки Android...")
        
        # 1. Получаем и логируем информацию о ПК и пользователе
        system_info = get_system_info()
        log_system_info(system_info)
        
        # 2. Сканируем USB и ищем папку Android
        scan_usb_drives()
        
        logging.info("Сканирование завершено.")
        
    except Exception as e:
        logging.critical(f"Критическая ошибка в работе скрипта: {e}", exc_info=True)
        print(f"Произошла ошибка. Проверьте лог в {LOG_FILE}")

if __name__ == "__main__":
    main()