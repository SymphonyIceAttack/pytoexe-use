import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
import subprocess
import time

# --- Константы WinAPI для управления окнами (на всякий случай) ---
User32 = ctypes.windll.User32
SW_RESTORE = 9
SW_SHOW = 5

class WincorModeSwitcher:
    def __init__(self, root, is_admin):
        self.root = root
        self.root.title("Wincor Mode Switcher (SOP Tool)")
        self.root.geometry("450x350")
        self.root.resizable(False, False)

        # Стилизация
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10, "bold"))
        style.configure("Red.TButton", foreground="red")
        style.configure("Green.TButton", foreground="green")
        
        # --- Заголовок ---
        header = ttk.Label(root, text="Переключение режимов Wincor", font=("Arial", 14, "bold"))
        header.pack(pady=15)

        if not is_admin:
            lbl_warn = ttk.Label(root, text="⚠️ Запущено БЕЗ прав администратора!\nСкрипт не сможет закрыть процессы банкомата.", foreground="red", justify="center")
            lbl_warn.pack(pady=5)

        # --- Основные кнопки ---
        frame_controls = ttk.LabelFrame(root, text="Управление режимом")
        frame_controls.pack(fill="both", expand=True, padx=15, pady=10)

        # Кнопка входа в SOP
        btn_sop = ttk.Button(frame_controls, text="🛠 Вход в SOP (Убить ProTopas -> Старт SOP)", command=self.switch_to_sop)
        btn_sop.pack(fill="x", padx=10, pady=10, ipady=5)

        # Кнопка возврата в режим клиента
        btn_app = ttk.Button(frame_controls, text="💳 Вернуть режим клиента (Start ProTopas)", command=self.switch_to_app)
        btn_app.pack(fill="x", padx=10, pady=10, ipady=5)

        # --- Статус ---
        self.status_var = tk.StringVar()
        self.status_var.set("Ожидание команды...")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

        # Список процессов для "убийства" при входе в SOP
        # AppMain.exe - частое имя приложения банка
        # ProTopas.exe - стандартное ядро Wincor
        # CCO.exe - компонент ProBase
        self.kill_list = ["ProTopas.exe", "AppMain.exe", "Topas.exe", "AtmApp.exe"]

    def log(self, message):
        self.status_var.set(message)
        self.root.update()

    def kill_process(self, process_name):
        """Пытается убить процесс по имени."""
        try:
            # Используем taskkill, так как он есть в любой Win 7
            cmd = f'taskkill /F /IM "{process_name}"'
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            subprocess.call(cmd, startupinfo=startupinfo)
            return True
        except Exception:
            return False

    def find_exe(self, possible_names):
        """Ищет исполняемый файл в стандартных папках Wincor."""
        search_paths = [
            r"C:\ProTopas\Bin",
            r"D:\ProTopas\Bin",
            r"C:\Wincor\ProTopas\Bin",
            r"C:\ProBase\Bin",
            r"C:\App\Bin" # Иногда тут лежит банковский софт
        ]
        
        for path in search_paths:
            for name in possible_names:
                full_path = os.path.join(path, name)
                if os.path.exists(full_path):
                    return full_path
        return None

    def switch_to_sop(self):
        if not messagebox.askyesno("Внимание", "Это принудительно закроет программу обслуживания клиентов (ProTopas/AppMain).\nБанкомат выйдет из сервиса.\n\nПродолжить?"):
            return

        self.log("Остановка процессов банкомата...")
        
        # 1. Убиваем основные процессы, которые могут блокировать SOP
        killed_count = 0
        for proc in self.kill_list:
            self.kill_process(proc)
            time.sleep(0.5) 
        
        self.log("Запуск SOP...")
        time.sleep(1)

        # 2. Ищем и запускаем SOP
        sop_path = self.find_exe(["SopMain.exe", "Sop.exe", "TSOP.exe"])
        
        if sop_path:
            try:
                # Запускаем, отвязывая от текущего процесса
                subprocess.Popen(sop_path, cwd=os.path.dirname(sop_path))
                self.log(f"Запущен: {sop_path}")
                messagebox.showinfo("Успех", "SOP запущен. Окно должно появиться на экране.\nЕсли окна нет - проверьте панель задач.")
            except Exception as e:
                messagebox.showerror("Ошибка запуска", str(e))
        else:
            messagebox.showerror("Ошибка", "Не удалось найти файл SopMain.exe или Sop.exe в стандартных папках C:\\ProTopas\\Bin")

    def switch_to_app(self):
        self.log("Закрытие SOP...")
        self.kill_process("SopMain.exe")
        self.kill_process("Sop.exe")
        
        self.log("Запуск ProTopas...")
        time.sleep(1)

        # Ищем ProTopas или AppMain
        app_path = self.find_exe(["ProTopas.exe", "AppMain.exe", "StartTopas.exe"])
        
        if app_path:
            try:
                subprocess.Popen(app_path, cwd=os.path.dirname(app_path))
                self.log(f"Запущен: {app_path}")
                messagebox.showinfo("Готово", "Приложение клиента запускается.")
            except Exception as e:
                messagebox.showerror("Ошибка запуска", str(e))
        else:
            # Если не нашли EXE, предлагаем просто перезагрузить ПК
            if messagebox.askyesno("Не найден ProTopas", "Не удалось найти запускаемый файл ProTopas/AppMain.\n\nПерезагрузить банкомат? Это гарантированно вернет рабочий режим."):
                os.system("shutdown -r -t 0")

if __name__ == "__main__":
    # Проверка прав админа
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False

    root = tk.Tk()
    app = WincorModeSwitcher(root, is_admin)
    root.mainloop()