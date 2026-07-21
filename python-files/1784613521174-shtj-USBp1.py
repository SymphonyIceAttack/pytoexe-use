import subprocess
import re
import datetime

def run_powershell_script():
    # Ваш оригинальный скрипт, экранированный для передачи в cmd
    ps_script = r"""
    Get-CimInstance Win32_DiskDrive | Where-Object { $_.InterfaceType -eq 'USB' } | Select-Object -First 1 | ForEach-Object {
        $disk = $_
        $partitions = Get-CimAssociatedInstance -InputObject $disk -ResultClassName Win32_DiskPartition
        foreach ($part in $partitions) {
            $volumes = Get-CimAssociatedInstance -InputObject $part -ResultClassName Win32_LogicalDisk
            foreach ($vol in $volumes) {
                "{0} OK {1} {2}" -f $disk.Caption, $disk.PNPDeviceID, $vol.DeviceID
                return
            }
        }
    }
    """
    
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Ошибка выполнения PowerShell: {e.stderr}")
        return None

def parse_and_format(raw_string):
    """
    Вход: "USB DISK 2.0 USB Device OK USBSTOR\DISK&VEN_&PROD_USB_DISK_2.0&REV_PMAP\90007B43F1154607&0 E:"
    Выход: "USB DISK 2.0 USB; 90007B43F1154607; E:"
    """
    if not raw_string:
        return None

    # Регулярное выражение для разбора строки
    # Группа 1: Название устройства (до слова OK)
    # Группа 2: PNP ID (между OK и буквой диска)
    # Группа 3: Буква диска (в конце)
    pattern = r"^(.*?)\s+OK\s+(.*?)\s+([A-Za-z]:)$"
    match = re.match(pattern, raw_string)
    
    if match:
        device_name = match.group(1).strip()
        pnp_id = match.group(2).strip()
        drive_letter = match.group(3).strip()
        
        # Извлекаем серийный номер из PNP ID
        # Формат: ...\SERIAL_NUMBER&...
        serial = "N/A"
        if '\\' in pnp_id:
            last_part = pnp_id.split('\\')[-1] # Берем часть после последнего \
            # Серийник обычно идет первым до символа &
            serial = last_part.split('&')[0]
            
        return f"{device_name}; {serial}; {drive_letter}"
    
    return None

# --- ОСНОВНОЙ ПРОЦЕСС ---
raw_output = run_powershell_script()

if raw_output:
    formatted_entry = parse_and_format(raw_output)
    
    if formatted_entry:
        log_file = "usb_log.txt"
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {formatted_entry}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
            
        print(f"Исходная строка: {raw_output}")
        print(f"В лог записано:   {formatted_entry}")
    else:
        print("Не удалось распарсить строку.")
else:
    print("Нет данных от PowerShell (возможно, USB не подключен).")