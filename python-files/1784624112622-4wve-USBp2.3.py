import subprocess
import re
import datetime
import os
import socket
import getpass

# --- НАСТРОЙКИ ПУТЕЙ ---
NETWORK_SHARE = r"\\SRV-DNS-01\Android"
LOCAL_FALLBACK = r"C:\Logs"
# -----------------------

def ensure_local_folder():
    """Пытается создать локальную папку, если её нет."""
    try:
        if not os.path.exists(LOCAL_FALLBACK):
            os.makedirs(LOCAL_FALLBACK, exist_ok=True)
        return True
    except PermissionError:
        # Нет прав на создание папки в C:\
        return False
    except Exception:
        return False

def get_network_log_path():
    """Возвращает путь к сетевому файлу, если туда можно писать."""
    computer_name = socket.gethostname()
    filename = f"{computer_name}.log"
    net_path = os.path.join(NETWORK_SHARE, filename)
    
    try:
        # Проверяем, существует ли сетевая папка
        if not os.path.exists(NETWORK_SHARE):
            return None
            
        # Тестовая запись, чтобы убедиться, что есть права на запись (SMB права)
        test_file = net_path + ".tmp_check"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("check")
        os.remove(test_file)
        
        return net_path
    except Exception:
        # Если ошибка (нет сети, нет прав, папка удалена) - возвращаем None
        return None

def get_local_log_path():
    """Возвращает путь к локальному файлу."""
    if not ensure_local_folder():
        return None
        
    computer_name = socket.gethostname()
    filename = f"{computer_name}.log"
    return os.path.join(LOCAL_FALLBACK, filename)

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

def write_to_multiple_paths(paths, line_content):
    """Пытается записать одну строку во все переданные пути."""
    for path in paths:
        try:
            # Создаем промежуточные папки для локального пути, если вдруг их нет (на всякий случай)
            dir_path = os.path.dirname(path)
            if dir_path and not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                except PermissionError:
                    continue # Не можем создать папку - пропускаем этот путь
            
            with open(path, "a", encoding="utf-8-sig") as f:
                f.write(line_content + "\n")
        except Exception:
            # Если не удалось записать в конкретный файл - просто игнорируем и идем дальше
            pass

def log_usb_devices():
    computer_name = socket.gethostname()
    user_name = getpass.getuser()
    
    # Получаем пути для записи
    net_path = get_network_log_path()
    local_path = get_local_log_path()
    
    # Формируем список путей, куда будем писать. 
    # Если какой-то путь None, он просто не попадет в список, и запись туда не произойдет.
    write_targets = []
    if net_path:
        write_targets.append(net_path)
    if local_path:
        write_targets.append(local_path)
        
    # Если некуда писать вообще - выходим
    if not write_targets:
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_lines = run_powershell_script()
    
    # Обработка обычных дисков
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
                
                log_line = f"[{timestamp}]; {computer_name}; {user_name}; {formatted_entry}; Android Folder: {android_status}"
                
                # ЗАПИСЫВАЕМ ОДНОВРЕМЕННО ВО ВСЕ ДОСТУПНЫЕ ПУТИ
                write_to_multiple_paths(write_targets, log_line)

    # Обработка MTP устройств (телефоны)
    mtp_found = check_mtp_android_via_com()
    if mtp_found:
        for path in mtp_found:
            log_line = (
                f"[{timestamp}]; {computer_name}; {user_name}; "
                f"MTP Device; Serial: N/A; Letter: N/A; Android Folder: {path}"
            )
            write_to_multiple_paths(write_targets, log_line)

if __name__ == "__main__":
    log_usb_devices()