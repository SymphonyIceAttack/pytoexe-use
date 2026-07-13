import os
import sys
import subprocess
import re
import time
from datetime import datetime
from pathlib import Path

# ================= НАСТРОЙКИ =================
TARGET_FOLDER_NAME = "Android"
LOG_FILE_PATH = r"C:\Logs\USB_Search.log"
# =============================================

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def write_log(message):
    """Обычная запись строки в лог и консоль"""
    timestamp = get_timestamp()
    log_entry = f"{timestamp} | {message}"
    
    # Пишем в файл
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"❌ Ошибка записи в лог-файл: {e}")
    
    # Выводим в консоль
    print(log_entry)

def write_device_separator(drive_letter):
    """Выводит разделители для нового устройства"""
    sep1 = "=" * 31
    sep2 = "+" * 31
    msg = f">>> НАЧАЛО ОБРАБОТКИ ДИСКА: {drive_letter} <<<"
    
    full_msg = f"\n{sep1}\n{msg}\n{sep2}"
    
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(full_msg + "\n")
        print(full_msg)
    except Exception as e:
        print(f"❌ Ошибка при записи разделителей: {e}")

def check_admin_rights():
    """Проверяет права администратора. Если нет - перезапускает скрипт от имени админа."""
    import ctypes
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапускает скрипт с правами администратора"""
    if not check_admin_rights():
        import ctypes
        params = ' '.join([f'"{arg}"' for arg in sys.argv])
        # Запуск через ShellExecute с флагом runas
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        if ret <= 32: # Ошибка ShellExecute
            print("❌ Не удалось перезапустить скрипт от имени администратора!")
            print("Пожалуйста, запустите этот скрипт вручную правой кнопкой мыши -> 'Запуск от имени администратора'.")
            sys.exit(1)
        sys.exit(0)

def get_usb_disk_mapping():
    """
    Получает соответствие: Номер диска <-> Модель/Имя устройства.
    Использует wmic для надежного маппинга (аналог CIM в PowerShell).
    Возвращает список словарей: [{'disk_number': 0, 'model': '...', 'pnp_name': '...'}, ...]
    """
    mapping = []
    
    # 1. Получаем список физических дисков и их связи с PnP устройствами
    # wmic diskdrive get index, model, caption, interfacetype
    cmd_disk = "wmic diskdrive get index,model,caption,interfacetype /format:table"
    result_disk = subprocess.run(cmd_disk, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    if result_disk.returncode != 0:
        return mapping

    # Парсим вывод wmic (он немного кривой, нужно чистить)
    lines = [l.strip() for l in result_disk.stdout.splitlines() if l.strip()]
    # Первая строка - заголовки, пропускаем
    for line in lines[1:]:
        parts = re.split(r'\s{2,}', line) # Разделяем по множественным пробелам
        if len(parts) >= 4:
            try:
                disk_num = int(parts[0])
                model = parts[1].strip()
                caption = parts[2].strip()
                interface = parts[3].strip()
                
                # Фильтруем только USB
                if "USB" in interface.upper():
                    # Теперь нужно найти PnP имя для этого диска.
                    # wmic path Win32_PnPEntity where "ClassGuid='{4d36e967-e325-11ce-bfc1-08002be10318}'" get Caption, DeviceID
                    # Это медленно делать в цикле, лучше получить все PnP устройства один раз.
                    mapping.append({
                        'disk_number': disk_num,
                        'model': model,
                        'caption': caption,
                        'interface': interface
                    })
            except ValueError:
                continue

    # Оптимизация: Получаем все PnP устройства одним запросом и маппим их
    # Запрос всех DiskDrive PnP устройств
    cmd_pnp = 'wmic path Win32_PnPEntity where "ClassGuid=\'{4d36e967-e325-11ce-bfc1-08002be10318}\'" get Caption, DeviceID /format:table'
    result_pnp = subprocess.run(cmd_pnp, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    pnp_devices = {}
    if result_pnp.returncode == 0:
        pnp_lines = [l.strip() for l in result_pnp.stdout.splitlines() if l.strip()]
        for line in pnp_lines[1:]: # Пропускаем заголовки
            parts = re.split(r'\s{2,}', line)
            if len(parts) >= 2:
                pnp_caption = parts[0].strip()
                device_id = parts[1].strip()
                # Пытаемся вытащить номер диска из DeviceID, если он там есть (редко, но бывает)
                # Но основной маппинг мы сделаем через связь в wmic diskdrive to pnpevidence, 
                # однако самый простой способ в Python без тяжелых библиотек - использовать ассоциацию через index.
                # В wmic diskdrive нет прямой колонки PnP ID. 
                # Поэтому мы полагаемся на то, что порядок вывода или модель помогут, 
                # НО! Самый надежный способ в чистом wmic - это запрос ассоциации.
                pass 

    # ПЕРЕПИСЫВАЕМ ЛОГИКУ МАППИНГА НА БОЛЕЕ НАДЕЖНУЮ ЧЕРЕЗ ASSOCIATORS
    # Это единственный способ получить точную связь без PowerShell CIM
    final_mapping = []
    
    # Получаем все диски
    disks_raw = subprocess.run("wmic diskdrive list brief /format:csv", shell=True, capture_output=True, text=True)
    # Получаем все PnP сущности
    pnps_raw = subprocess.run('wmic path Win32_PnPEntity list brief /format:csv', shell=True, capture_output=True, text=True)
    
    # Так как парсить CSV из wmic сложно и медленно в цикле, 
    # вернемся к простому методу: wmic diskdrive get /value и поиск связей.
    # Для простоты и скорости в этом скрипте используем подход:
    # 1. Берем диски (index, model).
    # 2. Для каждого диска пытаемся найти устройство через wmic path Win32_DiskDrive where "Index=X" assoc /resultclass:Win32_PnPEntity
    
    # Перебираем найденные ранее диски
    for disk_info in mapping:
        idx = disk_info['disk_number']
        # Ищем связанные PnP устройства
        assoc_cmd = f'wmic path Win32_DiskDrive where "Index={idx}" assoc /resultclass:Win32_PnPEntity /format:list'
        res_assoc = subprocess.run(assoc_cmd, shell=True, capture_output=True, text=True)
        
        pnp_name = "Неизвестно"
        device_id_short = ""
        
        if res_assoc.returncode == 0 and res_assoc.stdout:
            # Парсим вывод формата list: Name=..., DeviceID=...
            lines = res_assoc.stdout.splitlines()
            for l in lines:
                if l.startswith("Name="):
                    pnp_name = l.split("=", 1)[1].strip()
                if l.startswith("DeviceID="):
                    did = l.split("=", 1)[1].strip()
                    device_id_short = did[:50] + "..." if len(did) > 50 else did
        
        final_mapping.append({
            'disk_number': idx,
            'model': disk_info['model'],
            'pnp_name': pnp_name,
            'device_id': device_id_short,
            'interface': disk_info['interface']
        })

    return final_mapping

def find_folder_recursive(root_path, target_name, max_depth=10):
    """Рекурсивный поиск папки с ограничением глубины"""
    root = Path(root_path)
    if not root.exists():
        return None
    
    # os.walk не имеет параметра depth, поэтому реализуем ручную проверку глубины
    start_depth = root.parts
    
    for current_dir, dirs, files in os.walk(root):
        current_path = Path(current_dir)
        current_depth = len(current_path.parts) - len(start_depth)
        
        if current_depth > max_depth:
            dirs[:] = [] # Очищаем список директорий, чтобы os.walk не заходил глубже
            continue
            
        if target_name in dirs:
            return str(current_path / target_name)
            
    return None

def main():
    # 1. Проверка прав администратора
    if not check_admin_rights():
        write_log("⚠️ Скрипт запущен НЕ от имени Администратора. Попытка перезапуска...")
        run_as_admin()
        return

    write_log("=== ЗАПУСК СКРИПТА ПОИСКА USB (Python Version) ===")
    
    # Создаем папку для логов, если нет
    Path(os.path.dirname(LOG_FILE_PATH)).mkdir(parents=True, exist_ok=True)

    # 2. Сбор информации о дисках (Этап 1)
    write_log("🔍 Сбор информации о подключенных USB-дисках...")
    usb_mapping = get_usb_disk_mapping()
    
    if usb_mapping:
        write_log(f"✅ Найдено USB-устройств: {len(usb_mapping)}")
        # Вывод таблицы в лог (упрощенно)
        log_header = f"{'Disk #':<8} {'Model':<30} {'PnP Name':<40}"
        write_log(log_header)
        write_log("-" * 85)
        for dev in usb_mapping:
            line = f"{dev['disk_number']:<8} {dev['model'][:30]:<30} {dev['pnp_name'][:40]:<40}"
            write_log(line)
        write_log("-" * 85)
    else:
        write_log("⚠️ Не найдено ни одного USB-диска или ошибка получения данных.")

    # 3. Перебор букв дисков (Этап 2)
    found = False
    
    # Получаем список всех букв дисков через wmic logicaldisk
    ld_res = subprocess.run("wmic logicaldisk get caption /format:value", shell=True, capture_output=True, text=True)
    drives = []
    if ld_res.returncode == 0:
        for line in ld_res.stdout.splitlines():
            if line.startswith("Caption="):
                drives.append(line.split("=")[1].strip())
    
    # Если wmic не сработал, пробуем стандартный метод (менее надежно для фильтрации)
    if not drives:
        import string
        drives = [f"{d}:" for d in string.ascii_uppercase if os.path.exists(f"{d}:")]

    for drive in drives:
        root_path = f"{drive}\\"
        
        # Пропускаем системный диск C:\
        if root_path == "C:\\":
            continue
            
        # Проверка существования (на случай извлечения флешки в момент запуска)
        if not os.path.exists(root_path):
            continue

        # ВЫВОД РАЗДЕЛИТЕЛЕЙ ДЛЯ КАЖДОГО УСТРОЙСТВА
        write_device_separator(root_path)

        try:
            # Определяем номер диска для этой буквы
            # Используем wmic partition get diskindex, name
            part_cmd = f'wmic partition where "DeviceID=\'{drive.replace(":", "")}\'" get diskindex /format:list'
            part_res = subprocess.run(part_cmd, shell=True, capture_output=True, text=True)
            
            disk_number = None
            if part_res.returncode == 0:
                for line in part_res.stdout.splitlines():
                    if line.startswith("DiskIndex="):
                        disk_number = int(line.split("=")[1])
                        break
            
            if disk_number is None:
                write_log(f"⚠️ Не удалось определить номер диска для {drive}")
                continue

            write_log(f"💾 Проверяем диск: {root_path} (Disk Number: {disk_number})")

            # Поиск информации об устройстве в нашем списке
            device_info = "Неизвестно"
            match = next((d for d in usb_mapping if d['disk_number'] == disk_number), None)
            
            if match:
                device_info = f"Model: '{match['model']}' | PnP: '{match['pnp_name']}'"
                write_log(f"✅ Устройство сопоставлено: {device_info}")
            else:
                # Возможно, это не USB, или данные не сошлись
                # Дополнительная проверка типа шины через wmic diskdrive
                bus_check = subprocess.run(f'wmic diskdrive where "Index={disk_number}" get interfacetype /format:list', shell=True, capture_output=True, text=True)
                is_usb = False
                for l in bus_check.stdout.splitlines():
                    if l.startswith("InterfaceType=") and "USB" in l:
                        is_usb = True
                        break
                
                if not is_usb:
                    write_log(f"❌ Диск {disk_number} не является USB устройством. Пропуск.")
                    continue
                else:
                    write_log(f"⚠️ Диск {disk_number} определен как USB, но не найден в списке PnP устройств.")

            # ПОИСК ПАПКИ
            write_log(f"🔍 Начинаю поиск папки '{TARGET_FOLDER_NAME}' на {root_path}...")
            
            result_path = find_folder_recursive(root_path, TARGET_FOLDER_NAME, max_depth=10)
            
            if result_path:
                write_log("✅ ПАПКА НАЙДЕНА!")
                write_log(f"Путь: {result_path}")
                found = True
                # break # Можно раскомментировать, если нужно остановиться после первого успеха
            else:
                write_log(f"❌ Папка не найдена на диске {root_path}")

        except Exception as e:
            write_log(f"⚠️ Критическая ошибка обработки диска {drive}: {str(e)}")

    if not found:
        write_log(f"=== Поиск завершён. Папка '{TARGET_FOLDER_NAME}' не найдена ===")
    else:
        write_log("=== УСПЕХ! Папка найдена. ===")

if __name__ == "__main__":
    main()