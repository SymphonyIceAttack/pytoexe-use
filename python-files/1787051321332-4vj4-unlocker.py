import ctypes
import sys
import os
import winreg
import subprocess
import time
import psutil
import tkinter as tk
from tkinter import messagebox, Toplevel, Label, Entry, Button

# Константы
PROCESS_NAME = "python.exe"  # или имя вашего EXE, если переименовали
LOCKER_WINDOW_TITLE = "⛧ SWILL LOCK ⛧"

# ======== 1. УДАЛЕНИЕ ХУКА КЛАВИАТУРЫ ========
def remove_keyboard_hook():
    """Принудительно удаляет низкоуровневый хук клавиатуры"""
    try:
        # Проходим по всем хукам и удаляем их
        ctypes.windll.user32.UnhookWindowsHookEx(0)  # Сбрасываем хуки
        # Альтернативный метод - перезапуск explorer
        os.system("taskkill /f /im explorer.exe")
        time.sleep(1)
        os.system("start explorer.exe")
        return True
    except:
        return False

# ======== 2. ВОССТАНОВЛЕНИЕ РЕЕСТРА ========
def restore_registry():
    """Удаляет все блокировки из реестра"""
    try:
        # Восстанавливаем Alt+Tab
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, "AltTabSettings")
            winreg.CloseKey(key)
        except:
            pass
        
        # Удаляем NoAltTab
        try:
            key_path2 = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            key2 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path2, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key2, "NoAltTab")
            winreg.CloseKey(key2)
        except:
            pass
        
        # Восстанавливаем Task Manager
        try:
            key_path3 = r"Software\Microsoft\Windows\CurrentVersion\Policies\System"
            key3 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path3, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key3, "DisableTaskMgr")
            winreg.DeleteValue(key3, "DisableLockWorkstation")
            winreg.DeleteValue(key3, "DisableChangePassword")
            winreg.CloseKey(key3)
        except:
            pass
        
        # Удаляем блокировку через Explorer
        try:
            key_path4 = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
            key4 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path4, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key4, "NoWinKeys")
            winreg.CloseKey(key4)
        except:
            pass
        
        return True
    except:
        return False

# ======== 3. ЗАВЕРШЕНИЕ ПРОЦЕССА ВИНЛОКЕРА ========
def kill_locker_process():
    """Находит и завершает процесс винлокера"""
    try:
        # Ищем процесс по имени
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Проверяем, является ли процесс нашим винлокером
                if proc.info['name'] == PROCESS_NAME:
                    # Проверяем, содержит ли командная строка признаки винлокера
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'swill' in cmdline.lower() or 'lock' in cmdline.lower() or 'devil' in cmdline.lower():
                        proc.kill()
                        return True
                
                # Также ищем по имени окна
                try:
                    import win32gui
                    import win32con
                    
                    def enum_callback(hwnd, hwnds):
                        if win32gui.IsWindowVisible(hwnd):
                            window_text = win32gui.GetWindowText(hwnd)
                            if LOCKER_WINDOW_TITLE in window_text:
                                hwnds.append(hwnd)
                        return True
                    
                    hwnds = []
                    win32gui.EnumWindows(enum_callback, hwnds)
                    
                    for hwnd in hwnds:
                        # Отправляем сообщение на закрытие
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
                        ctypes.windll.user32.PostMessageW(hwnd, 0x0002, 0, 0)  # WM_DESTROY
                        return True
                except:
                    pass
            except:
                continue
        return False
    except:
        return False

# ======== 4. ПЕРЕЗАПУСК EXPLORER ========
def restart_explorer():
    """Перезапускает Explorer для полного снятия блокировок"""
    try:
        os.system("taskkill /f /im explorer.exe")
        time.sleep(2)
        os.system("start explorer.exe")
        return True
    except:
        return False

# ======== 5. GUI РАЗБЛОКИРОВЩИКА ========
class UnlockerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🔓 SWILL UNLOCKER 🔓")
        self.root.geometry("500x400")
        self.root.configure(bg='#0a0000')
        self.root.attributes('-topmost', True)
        self.root.resizable(False, False)
        
        # Заголовок
        title = tk.Label(self.root, text="🔓 СИСТЕМА РАЗБЛОКИРОВКИ 🔓",
                        font=('Arial', 20, 'bold'),
                        fg='#00FF00', bg='#0a0000')
        title.pack(pady=20)
        
        # Описание
        desc = tk.Label(self.root, text="Этот инструмент полностью удаляет блокировки\n"
                                        "восстанавливает реестр и завершает процесс винлокера",
                        font=('Arial', 12),
                        fg='#CCCCCC', bg='#0a0000', justify='center')
        desc.pack(pady=10)
        
        # Предупреждение
        warning = tk.Label(self.root, text="⚠️ ТРЕБУЮТСЯ ПРАВА АДМИНИСТРАТОРА ⚠️",
                          font=('Arial', 14, 'bold'),
                          fg='#FF0000', bg='#0a0000')
        warning.pack(pady=10)
        
        # Кнопка разблокировки
        self.unlock_btn = tk.Button(self.root, text="🔥 РАЗБЛОКИРОВАТЬ СИСТЕМУ 🔥",
                                   font=('Arial', 16, 'bold'),
                                   fg='white', bg='#8B0000',
                                   activeforeground='#FFD700',
                                   activebackground='#FF0000',
                                   command=self.start_unlock,
                                   relief='raised', bd=8)
        self.unlock_btn.pack(pady=20, ipadx=20, ipady=10)
        
        # Статус
        self.status_label = tk.Label(self.root, text="Готов к работе",
                                     font=('Arial', 11),
                                     fg='#00FF00', bg='#0a0000')
        self.status_label.pack(pady=10)
        
        # Строка прогресса (текстовая)
        self.progress_label = tk.Label(self.root, text="",
                                      font=('Arial', 10),
                                      fg='#FFD700', bg='#0a0000')
        self.progress_label.pack(pady=5)
        
        # Подпись
        footer = tk.Label(self.root, text="⛧ SWILL WAY - UNLOCKER ⛧",
                         font=('Arial', 9, 'italic'),
                         fg='#330000', bg='#0a0000')
        footer.pack(pady=15)
        
        self.root.mainloop()
    
    def update_status(self, text, color='#00FF00'):
        self.status_label.config(text=text, fg=color)
        self.root.update()
    
    def update_progress(self, text):
        self.progress_label.config(text=text)
        self.root.update()
    
    def start_unlock(self):
        # Блокируем кнопку
        self.unlock_btn.config(state='disabled', text='⏳ РАЗБЛОКИРОВКА...')
        self.update_status("Начинаем разблокировку...", '#FFD700')
        
        # Шаг 1: Удаляем хуки
        self.update_progress("[1/4] Удаление клавиатурных хуков...")
        if remove_keyboard_hook():
            self.update_status("✓ Хуки удалены", '#00FF00')
        else:
            self.update_status("⚠️ Хуки не найдены или уже удалены", '#FFA500')
        
        time.sleep(0.5)
        
        # Шаг 2: Восстанавливаем реестр
        self.update_progress("[2/4] Восстановление реестра...")
        if restore_registry():
            self.update_status("✓ Реестр восстановлен", '#00FF00')
        else:
            self.update_status("⚠️ Частичное восстановление реестра", '#FFA500')
        
        time.sleep(0.5)
        
        # Шаг 3: Завершаем процесс винлокера
        self.update_progress("[3/4] Завершение процесса винлокера...")
        if kill_locker_process():
            self.update_status("✓ Процесс винлокера завершен", '#00FF00')
        else:
            self.update_status("⚠️ Процесс не найден или уже завершен", '#FFA500')
        
        time.sleep(0.5)
        
        # Шаг 4: Перезапускаем Explorer
        self.update_progress("[4/4] Перезапуск оболочки Explorer...")
        if restart_explorer():
            self.update_status("✓ Explorer перезапущен", '#00FF00')
        else:
            self.update_status("⚠️ Перезапуск Explorer не удался", '#FFA500')
        
        time.sleep(0.5)
        
        # Финальное сообщение
        self.update_progress("✅ РАЗБЛОКИРОВКА ЗАВЕРШЕНА!")
        self.update_status("🎉 Система полностью разблокирована!", '#00FF00')
        self.unlock_btn.config(text='✅ ГОТОВО', bg='#006400')
        
        # Показываем уведомление
        messagebox.showinfo("✅ УСПЕШНО", 
                           "Система полностью разблокирована!\n\n"
                           "✅ Клавиатурные хуки удалены\n"
                           "✅ Реестр восстановлен\n"
                           "✅ Процесс винлокера завершен\n"
                           "✅ Explorer перезапущен\n\n"
                           "Теперь можно использовать систему нормально.")
        
        # Предложение закрыть программу
        if messagebox.askyesno("Выход", "Закрыть разблокировщик?"):
            self.root.destroy()
            sys.exit(0)
        else:
            self.unlock_btn.config(state='normal', text='🔥 РАЗБЛОКИРОВАТЬ СИСТЕМУ 🔥')

# ======== 6. ЗАПУСК С ПРАВАМИ АДМИНИСТРАТОРА ========
def run_as_admin():
    if sys.platform == 'win32':
        try:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                sys.exit()
        except:
            pass

# ======== 7. ОСНОВНОЙ КОД ========
if __name__ == "__main__":
    # Проверяем права администратора
    run_as_admin()
    
    # Запускаем GUI разблокировщика
    app = UnlockerGUI()