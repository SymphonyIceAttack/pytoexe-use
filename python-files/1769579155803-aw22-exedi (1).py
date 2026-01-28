import tkinter as tk
from tkinter import messagebox, ttk
import subprocess
import os
import shutil
import ctypes
import sys

# Настройка цветовой палитры (Dark Theme)
BG_COLOR = "#2b2b2b"        # Темно-серый фон
SIDEBAR_COLOR = "#1f1f1f"   # Еще темнее для меню
TEXT_COLOR = "#ffffff"      # Белый текст
ACCENT_COLOR = "#007acc"    # Синий акцент
BTN_HOVER = "#005f9e"
DANGER_COLOR = "#d9534f"    # Красный для опасных зон

class AntivirusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Guardian Pro")
        self.root.geometry("700x500")
        self.root.configure(bg=BG_COLOR)
        
        # Проверка прав администратора (нужна для Реестра и очистки)
        self.is_admin = self.check_admin()
        if not self.is_admin:
            messagebox.showwarning("Внимание", "Программа запущена без прав Администратора.\nФункции Реестра и Очистки могут работать некорректно.")

        self.create_widgets()

    def check_admin(self):
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def create_widgets(self):
        # --- Боковая панель (Заголовок) ---
        sidebar = tk.Frame(self.root, bg=SIDEBAR_COLOR, width=200)
        sidebar.pack(side="left", fill="y")
        
        title_label = tk.Label(sidebar, text="🛡 GUARDIAN", bg=SIDEBAR_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 20, "bold"))
        title_label.pack(pady=30, padx=20)

        info_label = tk.Label(sidebar, text="System Status:\nSECURE", bg=SIDEBAR_COLOR, fg="#28a745", font=("Segoe UI", 10))
        info_label.pack(pady=10)

        # --- Основная рабочая область ---
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Заголовок секции
        lbl_tools = tk.Label(main_frame, text="Инструменты безопасности", bg=BG_COLOR, fg=TEXT_COLOR, font=("Segoe UI", 14))
        lbl_tools.pack(anchor="w", pady=(0, 20))

        # --- Сетка кнопок ---
        # Мы используем Grid для красивого расположения
        
        # 1. Открыть Реестр (С исправлением)
        self.create_card(main_frame, "Редактор Реестра", "🔍", self.open_registry, 0, 0)
        
        # 2. Открыть CMD
        self.create_card(main_frame, "Командная строка", "💻", self.open_cmd, 0, 1)

        # 3. Диспетчер задач (Убить вирус)
        self.create_card(main_frame, "Диспетчер задач", "📊", self.open_taskmgr, 1, 0)
        
        # 4. Папка Автозагрузки (Где живут вирусы)
        self.create_card(main_frame, "Автозагрузка", "🚀", self.open_startup, 1, 1)

        # 5. Очистка Temp (Удалить дропперы)
        self.create_card(main_frame, "Очистить Temp", "🧹", self.clean_temp_files, 2, 0, color=DANGER_COLOR)

        # 6. Сетевые подключения (Куда уходят данные)
        self.create_card(main_frame, "Сетевой монитор", "🌐", self.check_network, 2, 1)

    def create_card(self, parent, text, icon, command, row, col, color=ACCENT_COLOR):
        """Создает красивую кнопку-карточку"""
        frame = tk.Frame(parent, bg=SIDEBAR_COLOR, bd=0, highlightthickness=1, highlightbackground="#444")
        frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)

        btn = tk.Button(frame, text=f"{icon}  {text}", bg=color, fg="white", 
                        font=("Segoe UI", 11, "bold"), bd=0, activebackground=BTN_HOVER,
                        command=command, cursor="hand2")
        btn.pack(fill="both", expand=True, padx=1, pady=1)

    # --- ФУНКЦИИ ---

    def open_cmd(self):
        # Открывает CMD только по нажатию
        subprocess.Popen('start cmd', shell=True)

    def open_registry(self):
        # Исправленный метод открытия реестра
        try:
            # Используем ShellExecute для запроса прав, если их нет
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "regedit.exe", None, None, 1)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть реестр: {e}")

    def open_taskmgr(self):
        # Открытие диспетчера задач
        subprocess.Popen('taskmgr')

    def open_startup(self):
        # Открытие папки автозагрузки текущего пользователя
        startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup')
        os.startfile(startup_path)

    def clean_temp_files(self):
        # Очистка папки Temp (частое место обитания вирусов-дропперов)
        temp_path = os.getenv('TEMP')
        deleted_count = 0
        try:
            for filename in os.listdir(temp_path):
                file_path = os.path.join(temp_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        deleted_count += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        deleted_count += 1
                except Exception:
                    pass # Пропускаем файлы, которые используются системой
            messagebox.showinfo("Очистка", f"Очистка завершена.\nУдалено объектов: {deleted_count}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def check_network(self):
        # Показать активные подключения (аналог netstat)
        subprocess.Popen('start cmd /k netstat -ano', shell=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = AntivirusApp(root)
    root.mainloop()