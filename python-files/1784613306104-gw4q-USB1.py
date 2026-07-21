import wmi
import datetime

def get_usb_log_entry():
    c = wmi.WMI()
    
    # Аналог: Get-CimInstance Win32_DiskDrive | Where-Object { $_.InterfaceType -eq 'USB' }
    disks = c.Win32_DiskDrive(InterfaceType='USB')
    
    if not disks:
        return None

    # Берем первый диск (аналог Select-Object -First 1)
    disk = disks[0]
    
    # Получаем разделы (аналог Get-CimAssociatedInstance ... Win32_DiskPartition)
    partitions = disk.associators(wmi_result_class='Win32_DiskPartition')
    
    for part in partitions:
        # Получаем тома/буквы (аналог Win32_LogicalDisk)
        volumes = part.associators(wmi_result_class='Win32_LogicalDisk')
        
        for vol in volumes:
            device_name = disk.Caption
            pnp_id = disk.PNPDeviceID
            drive_letter = vol.DeviceID
            
            # --- ЛОГИКА ПАРСИНГА И ФОРМАТИРОВАНИЯ ---
            # Извлекаем серийный номер из PNPDeviceID:
            # Исходник: USBSTOR\DISK&VEN_...&PROD_...&REV_...\90007B43F1154607&0
            # Нам нужно: 90007B43F1154607
            
            serial = "N/A"
            if '\\' in pnp_id:
                # Берем часть после последнего слэша и до следующего амперсанда
                parts = pnp_id.split('\\')[-1].split('&')
                if len(parts) > 0:
                    serial = parts[0]

            # Формируем строку для лога: "Название; Серийник; Буква"
            log_entry = f"{device_name}; {serial}; {drive_letter}"
            return log_entry

    return None

# --- ЗАПИСЬ В ЛОГ ---
log_file = "usb_log.txt"
entry = get_usb_log_entry()

if entry:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {entry}\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_line)
    
    print(f"Успешно записано в {log_file}: {entry}")
else:
    print("USB накопителей не найдено.")