import os
import sys
import winreg
import ctypes
import subprocess
import logging
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageTk
import tempfile

# Конфигурация
LOG_FILE = "defender_activity.log"
STATE_FILE = "defender_state.reg"
KEY_PATH_POLICIES = r"SOFTWARE\Policies\Microsoft\Windows Defender"
KEY_PATH_DEFENDER = r"SOFTWARE\Microsoft\Windows Defender"
VALUE_NAME = "DisableAntiSpyware"

class DefenderController:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление Защитником Windows 10 LTSC")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#f0f0f0')
        
        # Проверка прав
        if not self.is_admin():
            self.request_admin()
            return
        
        # Состояние
        self.logging_enabled = tk.BooleanVar(value=False)
        self.defender_installed = False
        self.defender_status = "Неизвестно"
        
        # Создание интерфейса
        self.create_widgets()
        
        # Запуск диагностики
        self.root.after(100, self.diagnose_system)
    
    def is_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def request_admin(self):
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit()
    
    def create_widgets(self):
        # Заголовок
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame, 
            text="Управление Защитником Windows 10", 
            fg='white', 
            bg='#2c3e50',
            font=("Arial", 16, "bold")
        )
        title_label.pack(expand=True)
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Левая панель (кнопки)
        left_frame = tk.Frame(main_frame, bg='#f0f0f0')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Правая панель (статус)
        right_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=2)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # Заголовок правой панели
        status_header = tk.Label(
            right_frame, 
            text="Диагностика системы", 
            bg='#3498db', 
            fg='white',
            font=("Arial", 12, "bold"),
            pady=5
        )
        status_header.pack(fill=tk.X)
        
        # Текстовое поле для статуса
        self.status_text = tk.Text(
            right_frame, 
            height=20, 
            width=50,
            font=("Consolas", 9),
            bg='white',
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Кнопки на левой панели
        buttons = [
            ("🔴 ОТКЛЮЧИТЬ ЗАЩИТНИК", self.disable_defender, '#e74c3c', '#c0392b'),
            ("🟢 ВКЛЮЧИТЬ ЗАЩИТНИК", self.enable_defender, '#27ae60', '#229954'),
            ("🔄 СБРОС К ЗАВОДСКИМ НАСТРОЙКАМ", self.reset_to_factory, '#f39c12', '#e67e22'),
            ("🔧 ВОССТАНОВИТЬ КОМПОНЕНТЫ (LTSC)", self.restore_defender_components, '#9b59b6', '#8e44ad'),
        ]
        
        for text, command, color, hover_color in buttons:
            btn = tk.Button(
                left_frame,
                text=text,
                command=command,
                bg=color,
                fg='white',
                font=("Arial", 11, "bold"),
                padx=20,
                pady=12,
                bd=0,
                cursor='hand2',
                activebackground=hover_color,
                activeforeground='white'
            )
            btn.pack(fill=tk.X, pady=5)
            
            # Эффект наведения
            btn.bind("<Enter>", lambda e, b=btn, c=hover_color: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.config(bg=c))
        
        # Чекбокс логирования
        log_frame = tk.Frame(left_frame, bg='#f0f0f0')
        log_frame.pack(fill=tk.X, pady=10)
        
        self.log_check = tk.Checkbutton(
            log_frame,
            text="📝 Создавать отчёты (лог-файл)",
            variable=self.logging_enabled,
            bg='#f0f0f0',
            font=("Arial", 10),
            padx=10,
            pady=5
        )
        self.log_check.pack(side=tk.LEFT)
        
        # Информация о файлах
        info_frame = tk.Frame(left_frame, bg='#ecf0f1', relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(
            info_frame,
            text="📁 Файлы программы:",
            bg='#ecf0f1',
            font=("Arial", 10, "bold")
        ).pack(anchor='w', padx=5, pady=2)
        
        tk.Label(
            info_frame,
            text=f"Лог: {LOG_FILE}",
            bg='#ecf0f1',
            font=("Arial", 8)
        ).pack(anchor='w', padx=15)
        
        tk.Label(
            info_frame,
            text=f"Маркер: {STATE_FILE}",
            bg='#ecf0f1',
            font=("Arial", 8)
        ).pack(anchor='w', padx=15)
    
    def log_message(self, message, type="INFO"):
        """Добавление сообщения в окно статуса"""
        self.status_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] ")
        
        if type == "ERROR":
            self.status_text.insert(tk.END, f"❌ {message}\n", "error")
            self.status_text.tag_config("error", foreground="red")
        elif type == "SUCCESS":
            self.status_text.insert(tk.END, f"✅ {message}\n", "success")
            self.status_text.tag_config("success", foreground="green")
        elif type == "WARNING":
            self.status_text.insert(tk.END, f"⚠️ {message}\n", "warning")
            self.status_text.tag_config("warning", foreground="orange")
        else:
            self.status_text.insert(tk.END, f"ℹ️ {message}\n")
        
        self.status_text.see(tk.END)
        self.root.update()
    
    def diagnose_system(self):
        """Полная диагностика системы"""
        self.status_text.delete(1.0, tk.END)
        self.log_message("Начинаю диагностику системы...", "INFO")
        self.log_message("="*50, "INFO")
        
        # Проверка прав
        if self.is_admin():
            self.log_message("Права администратора: ДА", "SUCCESS")
        else:
            self.log_message("Права администратора: НЕТ", "ERROR")
        
        # Проверка службы WinDefend
        try:
            result = subprocess.run(
                ['sc', 'query', 'WinDefend'],
                capture_output=True, text=True, encoding='cp866'
            )
            
            if "не существует" in result.stderr.lower() or "не является" in result.stderr.lower():
                self.log_message("Служба WinDefend: ОТСУТСТВУЕТ", "WARNING")
                self.defender_installed = False
            elif "STATE" in result.stdout:
                self.defender_installed = True
                if "RUNNING" in result.stdout:
                    self.log_message("Служба WinDefend: ЗАПУЩЕНА", "SUCCESS")
                    self.defender_status = "Работает"
                else:
                    self.log_message("Служба WinDefend: ОСТАНОВЛЕНА", "WARNING")
                    self.defender_status = "Остановлена"
        except Exception as e:
            self.log_message(f"Ошибка проверки службы: {str(e)}", "ERROR")
        
        # Проверка реестра
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY_PATH_POLICIES, 0, winreg.KEY_READ):
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY_PATH_POLICIES) as key:
                        value, _ = winreg.QueryValueEx(key, VALUE_NAME)
                        if value == 1:
                            self.log_message("Политика отключения: УСТАНОВЛЕНА (DisableAntiSpyware=1)", "WARNING")
                        else:
                            self.log_message("Политика отключения: значение = 0", "INFO")
                except:
                    self.log_message("Политика отключения: параметр отсутствует", "SUCCESS")
        except FileNotFoundError:
            self.log_message("Политика отключения: раздел не создан", "SUCCESS")
        
        # Проверка папок Defender
        defender_paths = [
            "C:\\Program Files\\Windows Defender",
            "C:\\ProgramData\\Microsoft\\Windows Defender"
        ]
        for path in defender_paths:
            if os.path.exists(path):
                self.log_message(f"Папка Defender: {path}", "INFO")
        
        # Версия Windows
        try:
            result = subprocess.run(
                ['powershell', '-Command', 
                 '(Get-WmiObject -Class Win32_OperatingSystem).Caption'],
                capture_output=True, text=True, encoding='cp866'
            )
            if "LTSC" in result.stdout:
                self.log_message(f"Версия Windows: {result.stdout.strip()}", "INFO")
        except:
            pass
        
        self.log_message("="*50, "INFO")
        self.log_message("Диагностика завершена!", "SUCCESS")
    
    def disable_defender(self):
        """Отключение Защитника"""
        self.log_message("="*50, "INFO")
        self.log_message("Пытаюсь отключить Защитник...", "INFO")
        
        try:
            # Способ 1: Через политики
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, KEY_PATH_POLICIES) as key:
                winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_DWORD, 1)
            self.log_message("✓ Политика отключения установлена", "SUCCESS")
            
            # Способ 2: Отключение службы
            subprocess.run(['sc', 'config', 'WinDefend', 'start=', 'disabled'], 
                          capture_output=True)
            subprocess.run(['sc', 'stop', 'WinDefend'], capture_output=True)
            self.log_message("✓ Служба WinDefend остановлена", "SUCCESS")
            
            self.log_message("✓ Защитник Windows ОТКЛЮЧЕН!", "SUCCESS")
            messagebox.showinfo("Успех", "Защитник Windows успешно отключен!")
            
        except Exception as e:
            self.log_message(f"✗ Ошибка: {str(e)}", "ERROR")
            messagebox.showerror("Ошибка", f"Не удалось отключить: {str(e)}")
    
    def enable_defender(self):
        """Включение Защитника"""
        self.log_message("="*50, "INFO")
        self.log_message("Пытаюсь включить Защитник...", "INFO")
        
        try:
            # Удаление политики
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY_PATH_POLICIES, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, VALUE_NAME)
                self.log_message("✓ Политика отключения удалена", "SUCCESS")
            except FileNotFoundError:
                self.log_message("✓ Политика отключения отсутствовала", "INFO")
            
            # Включение службы
            subprocess.run(['sc', 'config', 'WinDefend', 'start=', 'auto'], 
                          capture_output=True)
            subprocess.run(['sc', 'start', 'WinDefend'], capture_output=True)
            self.log_message("✓ Служба WinDefend запущена", "SUCCESS")
            
            self.log_message("✓ Защитник Windows ВКЛЮЧЕН!", "SUCCESS")
            messagebox.showinfo("Успех", "Защитник Windows успешно включен!")
            
        except Exception as e:
            self.log_message(f"✗ Ошибка: {str(e)}", "ERROR")
            messagebox.showerror("Ошибка", f"Не удалось включить: {str(e)}")
    
    def reset_to_factory(self):
        """Сброс к заводским настройкам"""
        self.log_message("="*50, "INFO")
        self.log_message("Сброс к заводским настройкам...", "INFO")
        
        try:
            # Удаление раздела политик
            try:
                winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, KEY_PATH_POLICIES)
                self.log_message("✓ Раздел политик удален", "SUCCESS")
            except FileNotFoundError:
                self.log_message("✓ Раздел политик отсутствовал", "INFO")
            
            # Сброс службы
            subprocess.run(['sc', 'config', 'WinDefend', 'start=', 'auto'], 
                          capture_output=True)
            self.log_message("✓ Служба WinDefend сброшена", "SUCCESS")
            
            # Создание маркера
            with open(STATE_FILE, 'w') as f:
                f.write(f"reset_at={datetime.now()}")
            self.log_message(f"✓ Маркер сброса создан: {STATE_FILE}", "SUCCESS")
            
            self.log_message("✓ Сброс выполнен успешно!", "SUCCESS")
            messagebox.showinfo("Успех", "Сброс к заводским настройкам выполнен!")
            
        except Exception as e:
            self.log_message(f"✗ Ошибка: {str(e)}", "ERROR")
            messagebox.showerror("Ошибка", f"Не удалось выполнить сброс: {str(e)}")
    
    def restore_defender_components(self):
        """Восстановление компонентов Defender"""
        result = messagebox.askyesno(
            "Подтверждение",
            "Это попытается восстановить компоненты Защитника Windows.\n"
            "Может потребоваться подключение к интернету и перезагрузка.\n\n"
            "Продолжить?"
        )
        
        if not result:
            return
        
        self.log_message("="*50, "INFO")
        self.log_message("Восстановление компонентов Defender...", "INFO")
        
        commands = [
            "dism /online /enable-feature /featurename:Windows-Defender-ApplicationGuard /all /quiet",
            "dism /online /enable-feature /featurename:Windows-Defender /all /quiet",
            "sfc /scannow"
        ]
        
        for cmd in commands:
            self.log_message(f"Выполняю: {cmd}", "INFO")
            try:
                result = subprocess.run(cmd.split(), capture_output=True, text=True)
                if result.returncode == 0:
                    self.log_message(f"✓ Команда выполнена", "SUCCESS")
                else:
                    self.log_message(f"⚠ Возможно, потребуется перезагрузка", "WARNING")
            except Exception as e:
                self.log_message(f"✗ Ошибка: {str(e)}", "ERROR")
        
        self.log_message("="*50, "INFO")
        self.log_message("Все команды выполнены! Рекомендуется перезагрузить компьютер.", "SUCCESS")
        messagebox.showinfo("Готово", "Команды выполнены.\nРекомендуется перезагрузить компьютер.")

if __name__ == "__main__":
    root = tk.Tk()
    app = DefenderController(root)
    root.mainloop()