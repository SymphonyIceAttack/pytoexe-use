import subprocess
import re
import datetime
import os
import socket

def run_powershell_script():
    """
    Запускает PowerShell скрипт для получения данных обо всех USB дисках.
    Возвращает список строк или None при ошибке.
    """
    ps_script = r"""
    Get-CimInstance Win32_DiskDrive | Where-Object { $_.InterfaceType -eq 'USB' } | ForEach-Object {
        $disk = $_
        $partitions = Get-CimAssociatedInstance -InputObject $disk -ResultClassName Win32_DiskPartition
        foreach ($part in $partitions) {
            $volumes = Get-CimAssociatedInstance -InputObject $part -ResultClassName Win32_LogicalDisk
            foreach ($vol in $volumes) {
                "{0} OK {1} {2}" -f $disk.Caption, $disk.PNPDeviceID, $vol.DeviceID
            }
        }
    }
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Ошибка PowerShell: {result.stderr}")
            return None
            
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines
        
    except FileNotFoundError:
        print("Ошибка: Не найден исполняемый файл PowerShell.")
        return None
    except subprocess.TimeoutExpired:
        print("Ошибка: Превышено время ожидания ответа от PowerShell.")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None

def parse_and_format(raw_string):
    """
    Парсит строку из PS и приводит к формату:
    "Название устройства; Серийный номер; Буква диска"
    Убирает лишнее слово 'Device' из названия.
    """
    if not raw_string:
        return None

    # Регулярка ищет: (Название) OK (PNP_ID) (Буква)
    pattern = r"^(.*?)\s+OK\s+(.*?)\s+([A-Za-z]:)$"
    match = re.match(pattern, raw_string)
    
    if match:
        device_name = match.group(1).strip()
        pnp_id = match.group(2).strip()
        drive_letter = match.group(3).strip()
        
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Удаляем слово " Device" (с пробелом перед ним), если оно есть
        device_name_clean = device_name.replace(" Device", "")
        # На случай, если там было " Device " или лишние пробелы после удаления
        device_name_clean = " ".join(device_name_clean.split()) 
        # -----------------------
        
        serial = "N/A"
        try:
            if '\\' in pnp_id:
                last_part = pnp_id.rsplit('\\', 1)[-1]
                serial = last_part.split('&')[0]
                if not serial:
                    serial = "Unknown"
        except Exception:
            serial = "ParseError"
            
        return f"{device_name_clean}; {serial}; {drive_letter}"
    
    return None

def log_usb_devices():
    computer_name = socket.gethostname()
    base_path = r"C:\Logs"
    log_filename = f"{computer_name}.txt"
    full_log_path = os.path.join(base_path, log_filename)
    
    try:
        os.makedirs(base_path, exist_ok=True)
        print(f"Путь для лога: {full_log_path}")
    except PermissionError:
        print(f"Нет прав на создание папки {base_path}. Запустите скрипт от имени Администратора.")
        return
    except OSError as e:
        print(f"Ошибка создания папки: {e}")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_lines = run_powershell_script()
    
    if not raw_lines:
        print("Нет данных от PowerShell (возможно, USB не подключен).")
        return

    count = 0
    for raw_line in raw_lines:
        formatted_entry = parse_and_format(raw_line)
        
        if formatted_entry:
            log_line = f"[{timestamp}] {formatted_entry}\n"
            try:
                with open(full_log_path, "a", encoding="utf-8") as f:
                    f.write(log_line)
                print(f"[OK] Записано: {formatted_entry}")
                count += 1
            except IOError as e:
                print(f"Ошибка записи в файл: {e}")
        else:
            print(f"[WARN] Не удалось распарсить строку: {raw_line}")

    if count == 0:
        print("Данные получены, но ни одна строка не была успешно распарсена.")

if __name__ == "__main__":
    log_usb_devices()