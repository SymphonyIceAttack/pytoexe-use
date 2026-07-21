import subprocess
import re
import datetime
import os
import socket

def run_powershell_command(script_block):
    """
    Универсальный запуск PowerShell скрипта.
    Возвращает stdout (очищенный) или None при ошибке.
    """
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script_block],
            capture_output=True,
            text=True,
            timeout=15,
            encoding='utf-8'
        )
        if result.returncode != 0:
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"Ошибка выполнения PS: {e}")
        return None

def get_usb_drives_info():
    """
    Получает список флешек: Название, Серийник, Буква.
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
    
    raw_lines = run_powershell_command(ps_script)
    if not raw_lines:
        return []
    
    lines = [line.strip() for line in raw_lines.splitlines() if line.strip()]
    
    devices = []
    for line in lines:
        pattern = r"^(.*?)\s+OK\s+(.*?)\s+([A-Za-z]:)$"
        match = re.match(pattern, line)
        if match:
            name = match.group(1).strip().replace(" Device", "")
            name = " ".join(name.split())
            
            pnp_id = match.group(2).strip()
            letter = match.group(3).strip()
            
            serial = "N/A"
            if '\\' in pnp_id:
                last_part = pnp_id.rsplit('\\', 1)[-1]
                serial = last_part.split('&')[0]
            
            devices.append({
                "name": name,
                "serial": serial,
                "letter": letter
            })
    return devices

def check_android_folder(drive_letter):
    """
    Запускает PS скрипт проверки папки Android на конкретном диске.
    Возвращает текстовый статус (Found / Not found).
    """
    ps_check_script = f"""
    $drive = "{drive_letter}"
    $path = Join-Path -Path $drive -ChildPath 'Android'
    if (Test-Path -Path $path -PathType Container) {{
        "FOUND:{path}"
    }} else {{
        "NOT_FOUND:{drive}"
    }}
    """
    
    res = run_powershell_command(ps_check_script)
    
    if res and res.startswith("FOUND:"):
        path = res.split(":", 1)[1]
        return f"Found: {path}"
    elif res and res.startswith("NOT_FOUND:"):
        return f"Not found on {drive_letter}"
    else:
        return "Check error"

def log_usb_devices():
    computer_name = socket.gethostname()
    base_path = r"C:\Logs"
    log_filename = f"{computer_name}.txt"
    full_log_path = os.path.join(base_path, log_filename)
    
    try:
        os.makedirs(base_path, exist_ok=True)
        print(f"Путь для лога: {full_log_path}")
    except PermissionError:
        print(f"Нет прав на создание папки {base_path}. Запустите от имени Администратора.")
        return
    except OSError as e:
        print(f"Ошибка создания папки: {e}")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    devices = get_usb_drives_info()
    
    if not devices:
        print("USB накопителей не найдено.")
        return

    print(f"Найдено устройств: {len(devices)}. Начинаем проверку...")
    
    count = 0
    for dev in devices:
        status_msg = check_android_folder(dev["letter"])
        
        # Формат: [Дата]; Название; Серийник; Буква; Статус
        log_entry = f"{dev['name']}; {dev['serial']}; {dev['letter']}; {status_msg}"
        log_line = f"[{timestamp}]; {log_entry}\n"
        
        try:
            with open(full_log_path, "a", encoding="utf-8") as f:
                f.write(log_line)
            print(f"{log_entry}")
            count += 1
        except IOError as e:
            print(f"Ошибка записи в файл: {e}")

    if count == 0:
        print("Ничего не было записано в лог.")

if __name__ == "__main__":
    log_usb_devices()