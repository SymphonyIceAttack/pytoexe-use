import subprocess
import re
import datetime
import os
import socket
import getpass
import shutil

# --- НАСТРОЙКИ ---
NETWORK_SHARE = r"\\SRV-DNS-01\Android"
LOCAL_FALLBACK = r"C:\Logs"
LOG_FILENAME_PREFIX = "usb_log_"
# -----------------

def safe_log(file_path, message):
    """Пытается записать сообщение в лог, игнорируя ошибки записи."""
    try:
        # Добавляем BOM для корректного отображения кириллицы в Блокноте Windows
        with open(file_path, "a", encoding="utf-8-sig") as f:
            f.write(f"{message}\n")
    except Exception as e:
        # Если даже в локальный файл нельзя написать - это критическая ошибка среды
        print(f"[CRITICAL] Не удалось записать в лог-файл даже локально: {e}")

def get_log_path():
    """
    Определяет путь для лога.
    Сначала пытается использовать сетевую папку, если не выходит - локальную.
    Возвращает кортеж: (полный_путь_к_файлу, тип_хранилища)
    """
    computer_name = socket.gethostname()
    timestamp_part = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{LOG_FILENAME_PREFIX}{computer_name}_{timestamp_part}.txt"
    
    # 1. Пробуем сетевую папку
    try:
        net_path = os.path.join(NETWORK_SHARE, filename)
        
        # Проверка: существует ли папка и можем ли мы туда писать?
        # os.access работает для сетевых путей в Windows
        if os.path.exists(NETWORK_SHARE) and os.access(NETWORK_SHARE, os.W_OK):
            # Создаем файл-тест, чтобы проверить реальные права на запись (иногда os.access врет для SMB)
            test_file = net_path + ".test"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file) # Удаляем тестовый файл
            
            print(f"[INFO] Запись в сетевую папку: {net_path}")
            return net_path, "Network"
        else:
            raise PermissionError("Нет прав или папка не найдена")
            
    except Exception as e:
        print(f"[WARN] Сетевая папка недоступна ({e}). Переключаемся на локальную.")
        safe_log(os.path.join(LOCAL_FALLBACK, "error_log.txt"), f"Network write failed: {e}")

    # 2. Фоллбэк на локальную папку
    try:
        os.makedirs(LOCAL_FALLBACK, exist_ok=True)
        local_path = os.path.join(LOCAL_FALLBACK, filename)
        print(f"[INFO] Запись в локальную папку: {local_path}")
        return local_path, "Local"
    except Exception as e:
        print(f"[CRITICAL] Не удалось создать локальную папку и записать лог: {e}")
        return None, "Failed"

def run_powershell_script():
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
            return None
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return lines
    except Exception:
        return None

def parse_and_format(raw_string):
    if not raw_string:
        return None
    pattern = r"^(.*?)\s+OK\s+(.*?)\s+([A-Za-z]:|NO_LETTER)$"
    match = re.match(pattern, raw_string)
    if match:
        device_name = match.group(1).strip().replace(" Device", "")
        device_name_clean = " ".join(device_name.split()) 
        pnp_id = match.group(2).strip()
        drive_letter = match.group(3).strip()
        
        serial = "N/A"
        try:
            if '\\' in pnp_id and pnp_id != "NO_LETTER":
                last_part = pnp_id.rsplit('\\', 1)[-1]
                serial = last_part.split('&')[0] or "Unknown"
        except Exception:
            serial = "ParseError"
            
        return f"{device_name_clean}; {serial}; {drive_letter}"
    return None

def check_android_folder_via_powershell(drive_letter):
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
            return True, output[6:]
        return False, ""
    except Exception:
        return False, ""

def check_mtp_android_via_com():
    ps_mtp = r"""
    $shell = New-Object -ComObject Shell.Application
    $namespace = $shell.NameSpace(0x11)
    $results = @()
    foreach ($item in $namespace.Items()) {
        if ($item.IsFolder -and $item.Type -match "Drive") {
            try {
                $androidFolder = $item.GetFolder().Items() | Where-Object { $_.Name -eq "Android" }
                if ($androidFolder) {
                    $results += "$($item.Name)\Android"
                }
            } catch {}
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
    except Exception:
        return []

def log_mtp_entries(file_path, timestamp, computer_name, user_name, paths):
    for path in paths:
        log_line = (
            f"[{timestamp}]; {computer_name}; {user_name}; "
            f"MTP Device; Serial: N/A; Letter: N/A; Android Folder: {path}"
        )
        safe_log(file_path, log_line)

def log_usb_devices():
    computer_name = socket.gethostname()
    user_name = getpass.getuser()
    
    # Получаем путь и тип хранилища
    log_path, storage_type = get_log_path()
    
    if not log_path:
        print("Критическая ошибка: невозможно определить место для логов. Завершение.")
        return

    # Пишем системную информацию о том, куда пишем
    safe_log(log_path, f"=== LOG SESSION STARTED ===")
    safe_log(log_path, f"Target Storage: {storage_type}")
    safe_log(log_path, f"Computer: {computer_name}")
    safe_log(log_path, f"User: {user_name}")
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_lines = run_powershell_script()
    
    count = 0
    
    if raw_lines:
        for raw_line in raw_lines:
            formatted_entry = parse_and_format(raw_line)
            
            if formatted_entry:
                parts = formatted_entry.split("; ")
                device_name = parts[0]
                serial = parts[1]
                drive_letter = parts[2]
                
                found, path = check_android_folder_via_powershell(drive_letter)
                android_status = path if found else "Not Found"
                
                log_line = (
                    f"[{timestamp}]; {computer_name}; {user_name}; "
                    f"{formatted_entry}; Android Folder: {android_status}"
                )
                
                safe_log(log_path, log_line)
                count += 1
            else:
                safe_log(log_path, f"[WARN] Не удалось распарсить строку: {raw_line}")
    else:
        safe_log(log_path, "Нет данных от PowerShell (возможно, USB не подключен).")

    mtp_found = check_mtp_android_via_com()
    if mtp_found:
        log_mtp_entries(log_path, timestamp, computer_name, user_name, mtp_found)
        count += len(mtp_found)

    safe_log(log_path, f"Total entries written: {count}")
    safe_log(log_path, f"=== LOG SESSION ENDED ===\n")

if __name__ == "__main__":
    log_usb_devices()