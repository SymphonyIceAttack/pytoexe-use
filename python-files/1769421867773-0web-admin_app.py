import json
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, Listbox, END

PROGRAMS_FILE = "programs.json"
TITLE = "AdminTool — Админ"

def load_programs():
    if not os.path.exists(PROGRAMS_FILE):
        return []
    try:
        with open(PROGRAMS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_programs(programs):
    with open(PROGRAMS_FILE, 'w', encoding='utf-8') as f:
        json.dump(programs, f, ensure_ascii=False, indent=2)

def add_program():
    path = filedialog.askopenfilename(filetypes=[("Executables", "*.exe")])
    if not path:
        return
    name = os.path.basename(path)
    programs = load_programs()
    programs.append({"name": name, "path": path})
    save_programs(programs)
    refresh_list()

def remove_program():
    selected = listbox.curselection()
    if not selected:
        return
    programs = load_programs()
    del programs[selected[0]]
    save_programs(programs)
    refresh_list()

def launch_as_admin():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите программу для запуска")
        return
    programs = load_programs()
    program = programs[selected[0]]
    try:
        subprocess.run(['runas', '/user:Administrator', program['path']], check=True)
    except subprocess.CalledProcessError:
        messagebox.showerror("Ошибка", "Не удалось запустить от имени администратора")
    except:
        messagebox.showerror("Ошибка", "Запуск отменён или не поддерживается")

def refresh_list():
    listbox.delete(0, END)
    for p in load_programs():
        listbox.insert(END, p["name"])

def toggle_autostart():
    reg_path = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
    key_name = 'AdminToolUser'
    exe_path = os.path.abspath('AdminTool_User.exe')  # Убедитесь, что путь правильный
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE) as key:
            if autostart_var.get():
                winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, key_name)
                except:
                    pass
    except:
        messagebox.showerror("Ошибка", "Не удалось настроить автозапуск")

def exit_app():
    root.destroy()

# GUI
root = tk.Tk()
root.title(TITLE)
root.geometry("500x400")

tk.Label(root, text="AdminTool — Управление программами", font=("Arial", 14)).pack(pady=10)

listbox = Listbox(root, width=60)
listbox.pack(pady=5, fill=tk.BOTH, expand=True)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Добавить", command=add_program).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="Удалить", command=remove_program).pack(side=tk.LEFT, padx=2)
tk.Button(btn_frame, text="Запустить от Админа", command=launch_as_admin).pack(side=tk.LEFT, padx=2)

autostart_var = tk.BooleanVar()
tk.Checkbutton(root, text="Автозапуск пользовательского интерфейса", variable=autostart_var, command=toggle_autostart).pack(pady=5)

tk.Button(root, text="Выход", command=exit_app, bg="red", fg="white").pack(pady=10)

refresh_list()
toggle_autostart()  # Sync state

root.mainloop()