import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
import subprocess
import psutil # Требуется установка: pip install psutil

# --- WinAPI константы и структуры ---
User32 = ctypes.windll.User32
SW_RESTORE = 9
SW_SHOW = 5
HWND_TOP = 0
SWP_SHOWWINDOW = 0x0040

class SOPManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wincor SOP Mover / Launcher")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # Стили
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 11))
        
        # Заголовок
        header = ttk.Label(root, text="Управление окном SOP (Wincor Nixdorf)", font=("Arial", 12, "bold"))
        header.pack(pady=10)

        # Фрейм списка окон
        list_frame = ttk.LabelFrame(root, text="Найдено окон (выберите SOP)")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Скроллбар и список
        self.tree = ttk.Treeview(list_frame, columns=("Handle", "Title"), show="headings", height=10)
        self.tree.heading("Handle", text="ID")
        self.tree.heading("Title", text="Заголовок окна")
        self.tree.column("Handle", width=80)
        self.tree.column("Title", width=350)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Кнопка обновления списка
        btn_refresh = ttk.Button(root, text="🔄 Обновить список окон", command=self.refresh_windows)
        btn_refresh.pack(pady=5)

        # Фрейм действий
        action_frame = ttk.LabelFrame(root, text="Действия")
        action_frame.pack(fill="x", padx=10, pady=10)

        # Кнопка переноса
        btn_move = ttk.Button(action_frame, text="📺 Перенести на ГЛАВНЫЙ ЭКРАН", command=self.move_window_to_main)
        btn_move.pack(fill="x", padx=10, pady=5)

        # Кнопка запуска процесса (если SOP упал)
        btn_launch = ttk.Button(action_frame, text="🚀 Запустить SopMain.exe (Стандартный путь)", command=self.launch_sop_process)
        btn_launch.pack(fill="x", padx=10, pady=5)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе. Нажмите 'Обновить список'.")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

        # Автоматическое обновление при старте
        self.root.after(500, self.refresh_windows)

    def get_windows(self):
        """Перечисляет все видимые окна Windows."""
        windows = []
        
        def enum_windows_proc(hwnd, lParam):
            length = User32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                User32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                # Фильтруем пустые или системные окна (опционально)
                if User32.IsWindowVisible(hwnd):
                    windows.append((hwnd, title))
            return True

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        User32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
        return windows

    def refresh_windows(self):
        """Обновляет список в GUI."""
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        windows = self.get_windows()
        # Сортируем: сначала те, что похожи на SOP, потом остальные
        windows.sort(key=lambda x: "SOP" not in x[1].upper())

        for hwnd, title in windows:
            # Подсвечиваем вероятные цели
            if any(x in title.upper() for x in ["SOP", "OPERATOR", "SERVICE", "PROTOPAS"]):
                self.tree.insert("", "end", values=(hwnd, title), tags=('target',))
            else:
                self.tree.insert("", "end", values=(hwnd, title))
        
        self.tree.tag_configure('target', background='#d1e7dd', foreground='black') # Зеленоватый фон для вероятных целей
        self.status_var.set(f"Найдено окон: {len(windows)}")

    def move_window_to_main(self):
        """Перемещает выбранное окно в координаты 0,0 и делает его активным."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите окно из списка!")
            return

        item = self.tree.item(selected[0])
        hwnd = item['values'][0]
        title = item['values'][1]

        try:
            # 1. Восстанавливаем окно, если оно свернуто
            User32.ShowWindow(hwnd, SW_RESTORE)
            
            # 2. Перемещаем в 0,0 (ширина 800, высота 600 - стандарт для SOP)
            # Параметры: hwnd, x, y, width, height, repaint
            User32.MoveWindow(hwnd, 0, 0, 800, 600, True)
            
            # 3. Делаем его поверх всех окон
            User32.SetForegroundWindow(hwnd)
            
            self.status_var.set(f"Окно '{title}' перемещено на главный экран.")
            messagebox.showinfo("Успех", f"Окно '{title}' должно появиться в левом верхнем углу.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переместить окно:\n{e}")

    def launch_sop_process(self):
        """Пытается найти и запустить стандартный EXE файл SOP."""
        # Стандартные пути для Wincor ProTopas / ProBase
        potential_paths = [
            r"C:\ProTopas\Bin\SopMain.exe",
            r"C:\ProTopas\Bin\Sop.exe",
            r"C:\Wincor\ProTopas\Bin\SopMain.exe",
            r"D:\ProTopas\Bin\SopMain.exe"
        ]

        found = False
        for path in potential_paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen(path)
                    self.status_var.set(f"Запущен процесс: {path}")
                    messagebox.showinfo("Запуск", f"Запущена команда:\n{path}\nПодождите пару секунд и нажмите 'Обновить список'.")
                    found = True
                    break
                except Exception as e:
                    messagebox.showerror("Ошибка запуска", str(e))
                    return

        if not found:
            # Если не нашли, просим пользователя выбрать вручную
            messagebox.showwarning("Не найдено", "Стандартный путь к SopMain.exe не найден.\nПроверьте папку C:\\ProTopas\\Bin вручную.")

if __name__ == "__main__":
    # Проверка прав администратора (желательно для управления чужими окнами)
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        print("Внимание: Рекомендуется запускать от имени Администратора для доступа ко всем окнам.")

    root = tk.Tk()
    # Иконка (если есть, иначе пропускаем)
    # root.iconbitmap("icon.ico") 
    app = SOPManagerApp(root)
    root.mainloop()