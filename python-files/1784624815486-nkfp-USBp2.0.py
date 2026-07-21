import subprocess
import re
import datetime
import os
import socket
import getpass

# --- Вспомогательные функции для безопасного логирования ---

def safe_log(file_path, message):
    """Пытается записать сообщение в лог, игнорируя ошибки записи."""
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"[SYSTEM] {message}\n")
    except Exception:
        pass

def safe_log_network(network_base_path, message):
    """
    Пытается записать сообщение в сетевой лог.
    Если папки нет, нет прав или ошибка сети — просто игнорирует ошибку.
    """
    try:
        # Проверяем существование сетевой папки. 
        # os.path.exists для сетевых путей может работать медленно, но надежно.
        if not os.path.isdir(network_base_path):
            return  # Если папки нет — ничего не делаем, как требовалось
        
        computer_name = socket.gethostname()
        filename = f"{computer_name}.log"
        full_file_path = os.path.join(network_base_path, filename)
        
        with open(full_file_path, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    except Exception:
        # Любая ошибка (нет прав, диск занят, сеть упала) — молча игнорируем
        pass

def log_usb_devices():
    computer_name = socket.gethostname()
    user_name = getpass.getuser()
    
    base_path = r"C:\Logs"
    # ИЗМЕНЕНИЕ 1: Расширение .log вместо .txt
    log_filename = f"{computer_name}.log"
    full_log_path = os.path.join(base_path, log_filename)
    
    # Путь для сетевой записи
    network_base_path = r"\\SRV-DNS-01\Android"

    # Пытаемся создать локальную папку
    try:
        os.makedirs(base_path, exist_ok=True)
    except PermissionError:
        err_msg = f"Нет прав на создание папки {base_path}. Запустите от имени Администратора."
        safe_log(full_log_path, err_msg)
        print(err_msg)
        return
    except OSError as e:
        err_msg = f"Ошибка создания папки: {e}"
        safe_log(full_log_path, err_msg)
        print(err_msg)
        return

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
                
                # Формируем строку лога
                log_line = (
                    f"[{timestamp}]; {computer_name}; {user_name}; "
                    f"{formatted_entry}; Android Folder: {android_status}"
                )
                
                try:
                    # 1. Пишем в локальный файл
                    with open(full_log_path, "a", encoding="utf-8") as f:
                        f.write(log_line + "\n")
                    
                    # 2. ИЗМЕНЕНИЕ 2: Параллельно пишем в сеть (если папка доступна)
                    safe_log_network(network_base_path, log_line)
                    
                    count += 1
                except IOError as e:
                    safe_log(full_log_path, f"Ошибка записи в файл: {e}")
            else:
                safe_log(full_log_path, f"[WARN] Не удалось распарсить строку: {raw_line}")
    else:
        safe_log(full_log_path, "Нет данных от PowerShell (возможно, USB не подключен).")

    mtp_found = check_mtp_android_via_com()
    if mtp_found:
        # Передаем network_base_path в функцию логирования MTP
        log_mtp_entries(full_log_path, timestamp, computer_name, user_name, mtp_found, network_base_path)
        count += len(mtp_found)

    if count == 0:
        msg = "Данные получены, но ни одна строка не была успешно распарсена или папка Android не найдена."
        safe_log(full_log_path, msg)

# --- Остальные функции (логика сохранена, добавлены аргументы для сети) ---

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
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
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

def log_mtp_entries(file_path, timestamp, computer_name, user_name, paths, network_base_path=None):
    for path in paths:
        log_line = (
            f"[{timestamp}]; {computer_name}; {user_name}; "
            f"MTP Device; Serial: N/A; Letter: N/A; Android Folder: {path}"
        )
        try:
            # Пишем в локальный файл
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(log_line + "\n")
            
            # ИЗМЕНЕНИЕ 3: Если передан путь к сети, пытаемся писать туда тоже
            if network_base_path:
                safe_log_network(network_base_path, log_line)
                
        except IOError:
            pass

if __name__ == "__main__":
    log_usb_devices()