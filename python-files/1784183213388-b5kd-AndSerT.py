import ctypes
import os
import string
import winreg
import subprocess
import shutil
import time

SIZE_TB = 6000
REAL_DRIVES = {'C:', 'E:', 'F:', 'Z:'}
BASE_FOLDER = r"C:\FakeDrives"

def delete_old_fake_drives():
    for d in string.ascii_uppercase:
        drive = f"{d}:"
        if drive not in REAL_DRIVES:
            subprocess.run(f"subst {drive} /d", shell=True, capture_output=True)
            ctypes.windll.kernel32.DefineDosDeviceW(2, drive, None)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\DOS Devices", 0, winreg.KEY_SET_VALUE)
        for d in string.ascii_uppercase:
            drive = f"{d}:"
            if drive not in REAL_DRIVES:
                try:
                    winreg.DeleteValue(key, drive)
                except:
                    pass
        winreg.CloseKey(key)
    except:
        pass
    if os.path.exists(BASE_FOLDER):
        try:
            shutil.rmtree(BASE_FOLDER, ignore_errors=True)
        except:
            pass

def get_free_drives():
    all_drives = [f"{d}:" for d in string.ascii_uppercase]
    used = set()
    for d in all_drives:
        if os.path.exists(d):
            used.add(d)
    used.update(REAL_DRIVES)
    return [d for d in all_drives if d not in used]

def create_fake_drive(drive_letter):
    letter = drive_letter.strip(':')
    drive_folder = os.path.join(BASE_FOLDER, letter)
    os.makedirs(drive_folder, exist_ok=True)
    subprocess.run(f"subst {drive_letter} {drive_folder}", shell=True)
    fake_file = os.path.join(drive_folder, "space.dat")
    with open(fake_file, "wb") as f:
        f.truncate(1024 * 1024)
    subprocess.run(f'fsutil sparse setflag "{fake_file}"', shell=True, capture_output=True)
    size_bytes = SIZE_TB * 1024 ** 4
    try:
        subprocess.run(f'fsutil file seteof "{fake_file}" {size_bytes}', shell=True, capture_output=True)
    except:
        subprocess.run(f'fsutil file seteof "{fake_file}" 17592186044416', shell=True, capture_output=True)
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\DOS Devices", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, drive_letter, 0, winreg.REG_SZ, rf"\??\{drive_folder}")
        winreg.CloseKey(key)
    except:
        pass
    
    # Удаляем папку сразу после создания диска
    try:
        shutil.rmtree(drive_folder, ignore_errors=True)
    except:
        pass
    
    return True

def main():
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    if not is_admin:
        exit()
    delete_old_fake_drives()
    time.sleep(1)
    free_drives = get_free_drives()
    if not free_drives:
        exit()
    created = 0
    for drive in free_drives:
        if create_fake_drive(drive):
            created += 1
    subprocess.run("taskkill /f /im explorer.exe", shell=True, capture_output=True)
    subprocess.run("start explorer.exe", shell=True)
    exit()

if __name__ == "__main__":
    main()