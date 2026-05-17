import subprocess
import sys
import ctypes
import re
import time
import os

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

def get_driver_packages(keyword):
    result = subprocess.run(
        f'pnputil /enum-drivers | findstr /i "{keyword}"',
        shell=True, capture_output=True, text=True
    )
    lines = result.stdout.split('\n')
    packages = []
    for line in lines:
        match = re.search(r'(oem\d+\.inf)', line, re.IGNORECASE)
        if match:
            packages.append(match.group(1))
    return list(set(packages))

def force_remove_driver(package_name):
    subprocess.run(f'pnputil /delete-driver {package_name} /uninstall /force', shell=True, capture_output=True)

def delete_driver_files():
    commands = [
        'takeown /f "C:\\Windows\\System32\\drivers\\net*.*" /a',
        'icacls "C:\\Windows\\System32\\drivers\\net*.*" /grant Administrators:F',
        'del /f /q "C:\\Windows\\System32\\drivers\\net*.sys" 2>nul',
        'del /f /q "C:\\Windows\\System32\\drivers\\wlan*.sys" 2>nul',
        'del /f /q "C:\\Windows\\System32\\drivers\\usb*.sys" 2>nul',
        'del /f /q "C:\\Windows\\System32\\DriverStore\\FileRepository\\*net*" 2>nul',
        'del /f /q "C:\\Windows\\System32\\DriverStore\\FileRepository\\*wlan*" 2>nul',
        'del /f /q "C:\\Windows\\System32\\DriverStore\\FileRepository\\*usb*" 2>nul',
        'del /f /q "C:\\Windows\\INF\\net*.inf" 2>nul',
        'del /f /q "C:\\Windows\\INF\\wlan*.inf" 2>nul',
        'del /f /q "C:\\Windows\\INF\\usb*.inf" 2>nul'
    ]
    for cmd in commands:
        subprocess.run(cmd, shell=True, capture_output=True)

def disable_network_adapters():
    subprocess.run('netsh interface set interface "Wi-Fi" admin=disable', shell=True, capture_output=True)
    subprocess.run('netsh interface set interface "Беспроводная сеть" admin=disable', shell=True, capture_output=True)
    subprocess.run('netsh wlan set autoconfig enabled=no interface="*"', shell=True, capture_output=True)
    
    ps_script = '''
    Get-NetAdapter | Where-Object {$_.Name -like "*WiFi*" -or $_.Name -like "*Wireless*" -or $_.Name -like "*WLAN*"} | Disable-NetAdapter -Confirm:$false
    Get-PnpDevice | Where-Object {$_.FriendlyName -like "*WiFi*" -or $_.FriendlyName -like "*Wireless*"} | Disable-PnpDevice -Confirm:$false
    '''
    subprocess.run(f'powershell -Command "{ps_script}"', shell=True, capture_output=True)

def delete_service_keys():
    commands = [
        'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\WlanSvc" /f',
        'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\WLAN" /f',
        'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\vwifibus" /f',
        'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\vwififlt" /f',
        'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\vwifimp" /f',
        'reg delete "HKLM\\SYSTEM\\CurrentControlSet\\Services\\NativeWifiP" /f'
    ]
    for cmd in commands:
        subprocess.run(cmd, shell=True, capture_output=True)

def main():
    run_as_admin()
    print("\n" + "="*60)
    print("    ПОЛНОЕ УДАЛЕНИЕ ДРАЙВЕРОВ Wi-Fi И USB")
    print("              WINDOWS 10/11")
    print("="*60 + "\n")
    
    print("[1/5] Поиск драйверов...")
    keywords = ["Wi-Fi", "Wireless", "WLAN", "Network", "USB", "Realtek", "Intel"]
    removed = []
    for kw in keywords:
        drivers = get_driver_packages(kw)
        for drv in drivers:
            print(f"    Удаление: {drv}")
            force_remove_driver(drv)
            removed.append(drv)
            time.sleep(0.2)
    
    print("\n[2/5] Удаление файлов драйверов (.sys, .inf)...")
    delete_driver_files()
    
    print("[3/5] Отключение сетевых адаптеров...")
    disable_network_adapters()
    
    print("[4/5] Очистка реестра...")
    delete_service_keys()
    
    print("[5/5] Блокировка авто-установки...")
    subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\DriverSearching" /v SearchOrderConfig /t REG_DWORD /d 0 /f', shell=True)
    subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate" /v ExcludeWUDriversInQualityUpdate /t REG_DWORD /d 1 /f', shell=True)
    
    print("\n" + "="*60)
    print("[✓] Драйверы ПОЛНОСТЬЮ УДАЛЕНЫ!")
    print("[!] Wi-Fi и USB устройства НЕ будут работать.")
    print("[!] Для восстановления требуются драйверы с сайта производителя")
    print("="*60)
    
    input("\nНажми Enter для перезагрузки...")
    subprocess.run('shutdown /r /t 5 /c "Перезагрузка для применения изменений"', shell=True)

if __name__ == "__main__":
    main()