import os
import winreg as reg
import time
import ctypes
import tempfile
import subprocess

hidden_path = os.path.join(tempfile.gettempdir(), "svchost.exe")
marker = os.path.join(tempfile.gettempdir(), "svchost.lock")
startup_folder = r"C:\Users\Home\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Collapse.exe"
reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

def hide_console():
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def kill_process():
    try:
        subprocess.run(['taskkill', '/f', '/im', 'svchost.exe'], capture_output=True)
        subprocess.run(['taskkill', '/f', '/im', 'Collapse.exe'], capture_output=True)
    except:
        pass

def remove_from_startup():
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, reg_path, 0, reg.KEY_SET_VALUE)
        reg.DeleteValue(key, "WindowsService")
        reg.DeleteValue(key, "Collapse")
        reg.CloseKey(key)
    except:
        pass

def delete_files():
    try:
        if os.path.exists(marker):
            os.remove(marker)
        if os.path.exists(hidden_path):
            os.remove(hidden_path)
        if os.path.exists(startup_folder):
            os.remove(startup_folder)
    except:
        pass

if __name__ == "__main__":
    hide_console()
    kill_process()
    time.sleep(1)
    remove_from_startup()
    delete_files()