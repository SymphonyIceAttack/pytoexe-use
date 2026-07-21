import subprocess
import re
import datetime
import os
import socket
import getpass

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
        # Если разделов нет, но устройство есть (редкий кейс), выводим без буквы
        if ($partitions.Count -eq 0) {
             "{0} OK {1} NO_LETTER" -f $disk.Caption, $disk.PNPDeviceID
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

    # Поддерживаем вариант с NO_LETTER, если вдруг встретится
    pattern = r"^(.*?)\s+OK\s+(.*?)\s+([A-Za-z]:|NO_LETTER)$"
    match = re.match(pattern, raw_string)
    
    if match:
        device_name = match.group(1).strip()
        pnp_id = match.group(2).strip()
        drive_letter = match.group(3).strip()
        
        # Удаляем слово " Device" (с пробелом перед ним), если оно есть
        device_name_clean = device_name.replace(" Device", "")
        # Убираем возможные двойные пробелы
        device_name_clean = " ".join(device_name_clean.split()) 
        
        serial = "N/A"
        try:
            if '\\' in pnp_id and pnp_id != "NO_LETTER":
                last_part = pnp_id.rsplit('\\', 1)[-1]
                serial = last_part.split('&')[0]
                if not serial:
                    serial = "Unknown"
        except Exception:
            serial = "ParseError"
            
        return f"{device_name_clean}; {serial}; {drive_letter}"
    
    return None

def check_android_folder_via_powershell(drive_letter):
    """
    Пытается найти папку Android на диске через PowerShell.
    Работает только если у устройства есть буква диска.
    """
    if drive_letter == "NO_LETTER":
        return False, ""
        
    ps_check = f"""
    $path = "{drive_letter}\\Android"
    if (Test-Path -Path $path -PathType Container) {{
        Write-Output "FOUND:$path"
    }} else {{
        Write-Output "NOT_FOUND"
    }}
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_check],
            capture_output=True,
            text=True,
            timeout=5
        )
        output = res.stdout.strip()
        if output.startswith("FOUND:"):
            return True, output[6:] # Возвращаем путь
        return False, ""
    except Exception:
        return False, ""

def check_mtp_android_via_com():
    """
    Ищет устройства MTP (телефоны) и проверяет наличие папки Android.
    Использует COM-объект Shell.Application.
    Возвращает список найденных путей.
    """
    # PowerShell скрипт, использующий COM для обхода MTP устройств
    ps_mtp = r"""
    $shell = New-Object -ComObject Shell.Application
    $namespace = $shell.NameSpace(0x11) # 0x11 = My Computer
    
    $results = @()
    
    foreach ($item in $namespace.Items()) {
        # Проверяем, является ли элемент устройством хранения
        if ($item.IsFolder -and $item.Type -match "Drive") {
            try {
                $androidFolder = $item.GetFolder().Items() | Where-Object { $_.Name -eq "Android" }
                if ($androidFolder) {
                    $results += "$($item.Name)\Android"
                }
            } catch {
                # Игнорируем ошибки доступа
            }
        }
    }
    
    if ($results.Count -gt 0) {
        $results -join "|"
    } else {
        "NOT_FOUND"
    }
    """
    
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_mtp],
            capture_output=True,
            text=True,
            timeout=15
        )
        output = res.stdout.strip()
        if output == "NOT_FOUND":
            return []
        return output.split("|")
    except Exception as e:
        print(f"[WARN] Ошибка проверки MTP: {e}")
        return []

def log_usb_devices():
    # Получаем имя компьютера и имя пользователя
    computer_name = socket.gethostname()
    user_name = getpass.getuser()
    
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
    
    count = 0
    
    # 1. Обрабатываем обычные диски (флешки и т.д.)
    if raw_lines:
        for raw_line in raw_lines:
            formatted_entry = parse_and_format(raw_line)
            
            if formatted_entry:
                parts = formatted_entry.split("; ")
                device_name = parts[0]
                serial = parts[1]
                drive_letter = parts[2]
                
                # Ищем папку Android на этом диске
                found, path = check_android_folder_via_powershell(drive_letter)
                android_status = path if found else "Not Found"
                
                # ФОРМАТ ЛОГА ОБНОВЛЕН: добавлены computer_name и user_name
                log_line = (
                    f"[{timestamp}]; {computer_name}; {user_name}; "
                    f"{formatted_entry}; Android Folder: {android_status}\n"
                )
                
                try:
                    with open(full_log_path, "a", encoding="utf-8") as f:
                        f.write(log_line)
                    print(f"[OK] Записано: {formatted_entry} | Android: {android_status}")
                    count += 1
                except IOError as e:
                    print(f"Ошибка записи в файл: {e}")
            else:
                print(f"[WARN] Не удалось распарсить строку: {raw_line}")
    else:
        print("Нет данных от PowerShell (возможно, обычные USB-диски не подключены).")

    # 2. Отдельно проверяем MTP устройства (телефоны без буквы диска)
    mtp_found = check_mtp_android_via_com()
    if mtp_found:
        log_mtp_entries(full_log_path, timestamp, computer_name, user_name, mtp_found)
        count += len(mtp_found)

    if count == 0:
        print("Данные получены, но ни одна строка не была успешно распарсена или папка Android не найдена.")

def log_mtp_entries(file_path, timestamp, computer_name, user_name, paths):
    """Дописывает в лог найденные MTP устройства с именем ПК и пользователя"""
    for path in paths:
        # Для MTP у нас нет серийника и буквы, пишем заглушку
        log_line = (
            f"[{timestamp}]; {computer_name}; {user_name}; "
            f"MTP Device; Serial: N/A; Letter: N/A; Android Folder: {path}\n"
        )
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(log_line)
            print(f"[OK-MTP] Найдено на телефоне: {path}")
        except IOError as e:
            print(f"Ошибка записи MTP в файл: {e}")

if __name__ == "__main__":
    log_usb_devices()