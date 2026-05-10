import os
import sys
import subprocess
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ------------------------------------------------------------
# Конфигурация
# ------------------------------------------------------------
CONFIG_FILE = "launcher_config.json"

class AppLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("App Launcher")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        # Стиль
        style = ttk.Style()
        style.theme_use('clam')

        # Данные
        self.apps = []  # Список словарей: {"name": ..., "path": ...}
        self.load_config()

        # Создание интерфейса
        self.create_widgets()
        self.refresh_list()

        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.save_and_exit)

    def create_widgets(self):
        # Основная рамка
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Панель инструментов
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="Add App", command=self.add_app).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Remove Selected", command=self.remove_app).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Launch", command=self.launch_app).pack(side=tk.LEFT, padx=(0, 5))

        # Список приложений
        list_frame = ttk.LabelFrame(main_frame, text="Applications", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.app_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Segoe UI", 10))
        self.app_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.app_listbox.yview)

        # Двойной клик для запуска
        self.app_listbox.bind("<Double-Button-1>", lambda event: self.launch_app())

        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))

    def refresh_list(self):
        self.app_listbox.delete(0, tk.END)
        for app in self.apps:
            display_text = f"{app['name']} :: {app['path']}"
            self.app_listbox.insert(tk.END, display_text)

    def add_app(self):
        file_path = filedialog.askopenfilename(
            title="Select executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if not file_path:
            return

        # Проверяем, не добавлено ли уже
        for app in self.apps:
            if app['path'] == file_path:
                messagebox.showwarning("Duplicate", "This application is already in the list.")
                return

        # Предлагаем имя по умолчанию
        default_name = Path(file_path).stem
        name = self.ask_for_name(default_name)
        if not name:  # Если пользователь отменил
            return

        self.apps.append({"name": name, "path": file_path})
        self.refresh_list()
        self.save_config()
        self.status_var.set(f"Added: {name}")

    def ask_for_name(self, default_name):
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter Application Name")
        dialog.geometry("300x100")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Name:").pack(pady=(10, 0))
        name_entry = ttk.Entry(dialog)
        name_entry.insert(0, default_name)
        name_entry.pack(pady=5, padx=10, fill=tk.X)

        result = {"value": None}

        def on_ok():
            result["value"] = name_entry.get().strip()
            if result["value"]:
                dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)

        self.root.wait_window(dialog)
        return result["value"]

    def remove_app(self):
        selection = self.app_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an application to remove.")
            return

        index = selection[0]
        removed_name = self.apps[index]['name']
        del self.apps[index]
        self.refresh_list()
        self.save_config()
        self.status_var.set(f"Removed: {removed_name}")

    def launch_app(self):
        selection = self.app_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an application to launch.")
            return

        index = selection[0]
        app = self.apps[index]
        app_path = app['path']

        if not os.path.exists(app_path):
            messagebox.showerror("Error", f"File not found:\n{app_path}")
            self.status_var.set(f"Error: {app['name']} not found")
            # Удаляем из списка, если файла нет
            del self.apps[index]
            self.refresh_list()
            self.save_config()
            return

        try:
            self.status_var.set(f"Launching: {app['name']}...")
            self.root.update()
            # Запуск .exe без ожидания
            subprocess.Popen([app_path], shell=True)
            self.status_var.set(f"Launched: {app['name']}")
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch {app['name']}:\n{str(e)}")
            self.status_var.set(f"Launch failed: {app['name']}")

    def load_config(self):
        config_path = Path(CONFIG_FILE)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.apps = data.get('apps', [])
            except Exception as e:
                print(f"Error loading config: {e}")
                self.apps = []

    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"apps": self.apps}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_and_exit(self):
        self.save_config()
        self.root.destroy()

# ------------------------------------------------------------
# Точка входа
# ------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()