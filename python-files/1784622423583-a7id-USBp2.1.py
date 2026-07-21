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

def get_final_log_path():
    """
    Возвращает путь к файлу лога.
    Приоритет: Сетевая папка. Если нельзя туда писать -> Локальная папка.
    Имя файла: ИмяКомпьютера.txt
    """
    computer_name = socket.gethostname()
    filename = f"{computer_name}.txt"
    
    # 1. Пробуем сетевую папку
    try:
        net_path = os.path.join(NETWORK_SHARE, filename)
        
        # Проверка существования папки и прав на запись
        if os.path.exists(NETWORK_SHARE):
            # Делаем тестовую запись, чтобы убедиться, что права есть
            test_file = net_path + ".tmp_check"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("check")
            os.remove(test_file)
            
            return net_path
    except Exception:
        pass # Игнорируем ошибку, переходим к локальной папке

    # 2. Фоллбэк на локальную папку
    try:
        os.makedirs(LOCAL_FALLBACK, exist_ok=True)
        return os.path.join(LOCAL_FALLBACK, filename)
    except Exception:
        return None

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

def write_log_line(file_path, line_content):
    """Записывает одну строку в файл с кодировкой utf-8-sig"""
    try:
        with open(file_path, "a", encoding="utf-8-sig") as f:
            f.write(line_content + "\n")
    except Exception:
        # Если даже сюда нельзя записать - ничего не делаем, чтобы не спамить ошибками
        pass

def log_usb_devices():
    computer_name = socket.gethostname()
    user_name = getpass.getuser()
    
    log_path = get_final_log_path()
    
    if not log_path:
        # Критический сбой: некуда писать вообще. 
        # Так как консоль может быть скрыта, мы ничего не выводим, данные теряются.
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    raw_lines = run_powershell_script()
    
    count = 0
    
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
                
                # ФОРМАТ СТРОКИ СТРОГО КАК ПРОСИЛИ
                log_line = f"[{timestamp}]; {computer_name}; {user_name}; {formatted_entry}; Android Folder: {android_status}"
                
                write_log_line(log_path, log_line)
                count += 1
            else:
                # Если распарсить не удалось, просто пропускаем, ничего не пишем в лог
                pass
    else:
        # Нет данных от PowerShell, ничего не пишем
        pass

    # Обработка MTP устройств (телефоны)
    mtp_found = check_mtp_android_via_com()
    if mtp_found:
        for path in mtp_found:
            log_line = (
                f"[{timestamp}]; {computer_name}; {user_name}; "
                f"MTP Device; Serial: N/A; Letter: N/A; Android Folder: {path}"
            )
            write_log_line(log_path, log_line)
            count += 1

if __name__ == "__main__":
    log_usb_devices()