import json
import os
import subprocess
import tkinter as tk
from tkinter import messagebox, Listbox, END

PROGRAMS_FILE = "programs.json"
TITLE = "AdminTool — Пользователь"

def load_programs():
    if not os.path.exists(PROGRAMS_FILE):
        return []
    try:
        with open(PROGRAMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def launch_program():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите программу")
        return
    programs = load_programs()
    program = programs[selected[0]]
    # Запуск с запросом UAC
    try:
        subprocess.run(['runas', '/user:Administrator', program['path']], check=True)
    except:
        messagebox.showerror("Ошибка", "Запуск отменён")

def refresh_list():
    listbox.delete(0, END)
    for p in load_programs():
        listbox.insert(END, p["name"])

def exit_app():
    root.destroy()

root = tk.Tk()
root.title(TITLE)
root.geometry("400x350")

tk.Label(root, text="AdminTool — Пользователь", font=("Arial", 14)).pack(pady=10)

listbox = Listbox(root, width=50)
listbox.pack(pady=5, fill=tk.BOTH, expand=True)

tk.Button(root, text="Запустить от Админа", command=launch_program).pack(pady=5)
tk.Button(root, text="Обновить", command=refresh_list).pack(pady=5)
tk.Button(root, text="Выход", command=exit_app, bg="red", fg="white").pack(pady=10)

refresh_list()

# Синхронизация в реальном времени — опционально через watchdog
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    class ReloadHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path.endswith("programs.json"):
                refresh_list()

    observer = Observer()
    observer.schedule(ReloadHandler(), path='.', recursive=False)
    observer.start()
except ImportError:
    print("Установите watchdog: pip install watchdog")

root.mainloop()