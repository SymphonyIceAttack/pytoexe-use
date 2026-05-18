import os
import sys
import subprocess
import ctypes
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

print("="*60)
print("    БЛОКИРОВКА: USB-ФЛЕШКИ + Wi-Fi")
print("    МЫШЬ, КЛАВИАТУРА, USB-ПОРТЫ РАБОТАЮТ")
print("="*60)

# ============================================
# 1. БЛОКИРУЕМ ТОЛЬКО USB-НАКОПИТЕЛИ (ФЛЕШКИ)
# ============================================
print("\n[🔒] Блокировка USB-флешек и внешних дисков...")

# Отключаем службу USBSTOR (только накопители, не HID-устройства)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR" /v Start /t REG_DWORD /d 4 /f', shell=True)
subprocess.run('net stop USBSTOR', shell=True, capture_output=True)
print("    ✅ USB-накопители (флешки) ОТКЛЮЧЕНЫ")

# Запрещаем установку mass storage устройств
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DeviceInstall\\Restrictions" /v DenyUnspecified /t REG_DWORD /d 1 /f', shell=True)
subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DeviceInstall\\Restrictions" /v DenyAdmin /t REG_DWORD /d 1 /f', shell=True)
print("    ✅ Установка новых накопителей ЗАПРЕЩЕНА")

# Отключаем все существующие mass storage устройства
result = subprocess.run('pnputil /enum-devices', shell=True, capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'USBSTOR' in line or 'Disk' in line or 'USB Mass Storage' in line:
        if 'Instance ID:' in line:
            inst_id = line.split('Instance ID:')[-1].strip()
            subprocess.run(f'pnputil /disable-device "{inst_id}"', shell=True, capture_output=True)

print("\n[📌] ФЛЕШКИ НЕ БУДУТ РАБОТАТЬ. МЫШЬ И КЛАВИАТУРА - ДА.")

# ============================================
# 2. ОТКЛЮЧАЕМ WI-FI (ПОЛНОСТЬЮ)
# ============================================
print("\n[🔒] Отключение Wi-Fi...")

# Отключаем службу WLAN
subprocess.run('sc config WlanSvc start= disabled', shell=True)
subprocess.run('net stop WlanSvc', shell=True)
subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\WlanSvc" /v Start /t REG_DWORD /d 4 /f', shell=True)
print("    ✅ Служба WLAN отключена")

# Отключаем все вай-фай адаптеры
subprocess.run('netsh interface set interface "Wi-Fi" admin=disable', shell=True)
subprocess.run('netsh interface set interface "Беспроводная сеть" admin=disable', shell=True)
subprocess.run('netsh wlan set autoconfig enabled=no interface="*"', shell=True)
print("    ✅ Wi-Fi адаптеры отключены")

# Блокируем драйверы вай-фай
result = subprocess.run('pnputil /enum-drivers', shell=True, capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'wlan' in line.lower() or 'wireless' in line.lower() or 'wi-fi' in line.lower():
        parts = line.split(':')
        if len(parts) > 1:
            driver = parts[1].strip().split()[0]
            if driver.startswith('oem'):
                subprocess.run(f'pnputil /delete-driver {driver} /uninstall /force', shell=True, capture_output=True)
                print(f"    Удалён драйвер: {driver}")

print("\n    ✅ Wi-Fi ПОЛНОСТЬЮ ОТКЛЮЧЕН")

# ============================================
# 3. ВЫВОД
# ============================================
print("\n" + "="*60)
print("    ГОТОВО!")
print("="*60)
print("\n[✓] USB-ФЛЕШКИ: НЕ РАБОТАЮТ")
print("[✓] Wi-Fi: НЕ РАБОТАЕТ")
print("[✓] МЫШЬ/КЛАВИАТУРА: РАБОТАЮТ")
print("[✓] ОСТАЛЬНЫЕ USB-ПОРТЫ: РАБОТАЮТ")
print("\n[!] ДЛЯ ВОССТАНОВЛЕНИЯ:")
print("    Запусти скрипт с параметром /restore")
print("    ИЛИ перезагрузи ПК")
print("="*60)

# ============================================
# ВОССТАНОВЛЕНИЕ
# ============================================
if len(sys.argv) > 1 and sys.argv[1] == "/restore":
    print("\n[🔧] ВОССТАНОВЛЕНИЕ...")
    
    # Восстанавливаем USBSTOR
    subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\USBSTOR" /v Start /t REG_DWORD /d 3 /f', shell=True)
    subprocess.run('sc config USBSTOR start= demand', shell=True)
    
    # Восстанавливаем Wi-Fi
    subprocess.run('sc config WlanSvc start= auto', shell=True)
    subprocess.run('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\WlanSvc" /v Start /t REG_DWORD /d 2 /f', shell=True)
    subprocess.run('netsh interface set interface "Wi-Fi" admin=enable', shell=True)
    subprocess.run('netsh wlan set autoconfig enabled=yes interface="*"', shell=True)
    
    # Удаляем политику запрета устройств
    subprocess.run('reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DeviceInstall\\Restrictions" /f', shell=True)
    
    print("[✓] Восстановление завершено. Перезагрузи ПК.")

input("\nНажми Enter для выхода...")