import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
import subprocess
import sys

# --- WinAPI константы ---
User32 = ctypes.windll.User32
SW_RESTORE = 9
SW_SHOW = 5

class SOPManagerApp:
    def __init__(self, root, is_admin):
        self.root = root
        self.root.title("Wincor SOP Mover (x86 Compatible)")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        
        # Стили
        style = ttk.Style()
        style.configure("TButton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 11))
        
        # --- Шапка ---
        header_frame = ttk.Frame(root)
        header_frame.pack(pady=10, fill="x")
        
        lbl_title = ttk.Label(header_frame, text="Управление окном SOP", font=("Arial", 14, "bold"))
        lbl_title.pack()

        # Индикатор прав
        admin_text = "Режим: АДМИНИСТРАТОР (Полный доступ)" if is_admin else "Режим: ПОЛЬЗОВАТЕЛЬ (Возможны ошибки доступа)"
        admin_color = "green" if is_admin else "red"
        lbl_admin = tk.Label(header_frame, text=admin_text, fg=admin_color, font=("Arial", 9))
        lbl_admin.pack()

        # --- Список окон ---
        list_frame = ttk.LabelFrame(root, text="Список окон (Ищите SOP/ProTopas)")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=("Handle", "Title"), show="headings", height=10)
        self.tree.heading("Handle", text="ID")
        self.tree.heading("Title", text="Заголовок окна")
        self.tree.column("Handle", width=80, anchor="center")
        self.tree.column("Title", width=380)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_refresh = ttk.Button(root, text="🔄 Обновить список", command=self.refresh_windows)
        btn_refresh.pack(pady=5)

        # --- Действия ---
        action_frame = ttk.LabelFrame(root, text="Операции")
        action_frame.pack(fill="x", padx=10, pady=10)

        btn_move = ttk.Button(action_frame, text="📺 Перенести на ГЛАВНЫЙ ЭКРАН (0,0)", command=self.move_window_to_main)
        btn_move.pack(fill="x", padx=10, pady=5)

        btn_launch = ttk.Button(action_frame, text="🚀 Запустить SopMain.exe (если закрыт)", command=self.launch_sop_process)
        btn_launch.pack(fill="x", padx=10, pady=5)
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов.")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")

        self.root.after(500, self.refresh_windows)

    def get_windows(self):
        windows = []
        def enum_windows_proc(hwnd, lParam):
            length = User32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                User32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                if User32.IsWindowVisible(hwnd):
                    windows.append((hwnd, title))
            return True
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        User32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)
        return windows

    def refresh_windows(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        windows = self.get_windows()
        # Сортировка: приоритет окнам с "SOP" или "ProTopas" в названии
        windows.sort(key=lambda x: 0 if any(k in x[1].upper() for k in ["SOP", "PROTOPAS", "OPERATOR"]) else 1)

        count = 0
        for hwnd, title in windows:
            # Игнорируем менеджер программ и само это приложение
            if title == "Program Manager" or "Wincor SOP Mover" in title:
                continue
                
            tags = ()
            if any(x in title.upper() for x in ["SOP", "OPERATOR", "SERVICE", "PROTOPAS"]):
                tags = ('target',)
            
            self.tree.insert("", "end", values=(hwnd, title), tags=tags)
            count += 1
        
        self.tree.tag_configure('target', background='#d4edda', foreground='#155724') # Зеленый цвет
        self.status_var.set(f"Найдено окон: {count}")

    def move_window_to_main(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Сначала выберите окно в списке!")
            return

        item = self.tree.item(selected[0])
        hwnd = item['values'][0]
        title = item['values'][1]

        try:
            # Восстановить если свернуто
            User32.ShowWindow(hwnd, SW_RESTORE)
            
            # Переместить в 0,0 размером 800x600
            # Аргументы: hwnd, X, Y, Width, Height, Repaint(bool)
            success = User32.MoveWindow(hwnd, 0, 0, 800, 600, True)
            
            if not success:
                raise Exception("Windows отказала в доступе (MoveWindow failed).")

            # Попытка вынести на передний план
            try:
                User32.SetForegroundWindow(hwnd)
            except:
                pass 
            
            self.status_var.set(f"Перемещено: {title}")
            messagebox.showinfo("Готово", f"Окно '{title}' перемещено в левый верхний угол.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переместить окно.\nПричина: {e}\n\nПопробуйте запустить программу от Администратора.")

    def launch_sop_process(self):
        paths = [
            r"C:\ProTopas\Bin\SopMain.exe",
            r"C:\ProTopas\Bin\Sop.exe",
            r"D:\ProTopas\Bin\SopMain.exe"
        ]
        for path in paths:
            if os.path.exists(path):
                try:
                    subprocess.Popen(path)
                    self.status_var.set(f"Запущен: {path}")
                    messagebox.showinfo("Запуск", f"Команда отправлена:\n{path}")
                    return
                except Exception as e:
                    messagebox.showerror("Ошибка", str(e))
                    return
        messagebox.showwarning("Не найдено", "Файл SopMain.exe не найден в стандартных папках.")

if __name__ == "__main__":
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        is_admin = False

    root = tk.Tk()
    app = SOPManagerApp(root, is_admin)
    root.mainloop()