import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

INI_FILE = 'settings.ini'
SCRIPT_EXTENSIONS = ['.asi', '.cs', '.lua']

def load_settings():
    if os.path.exists(INI_FILE):
        with open(INI_FILE, 'r', encoding='utf-8') as f:
            path = f.read().strip()
            if os.path.exists(path):
                return path
    return ''

def save_settings(path):
    with open(INI_FILE, 'w', encoding='utf-8') as f:
        f.write(path)

def select_game_path():
    path = filedialog.askdirectory()
    if path:
        save_settings(path)
        return path
    return None

def is_executable(filename):
    return filename.lower() in ['gta_sa.exe', 'gta-sa.exe']

def find_executable(folder):
    for fname in os.listdir(folder):
        if is_executable(fname):
            return os.path.join(folder, fname)
    return None

def scan_for_scripts(folder):
    scripts = []
    for root, dirs, files in os.walk(folder):
        rel_path = os.path.relpath(root, folder).replace('\\', '/')
        if rel_path != '.' and rel_path not in ['moonloader', 'sampfuncs', 'scripts'] and not rel_path.startswith('modloader'):
            continue
        for file in files:
            if any(file.lower().endswith(ext) for ext in SCRIPT_EXTENSIONS):
                scripts.append(os.path.join(root, file))
    return scripts

def load_script_states(scripts):
    states = {}
    for script in scripts:
        disabled_path = script + '.disabled'
        states[script] = not os.path.exists(disabled_path)
    return states

def toggle_script(script, enable):
    disabled_path = script + '.disabled'
    if enable:
        if os.path.exists(disabled_path):
            os.remove(disabled_path)
    else:
        with open(disabled_path, 'w', encoding='utf-8') as f:
            f.write('disabled')

def create_batch_file(gta_exe_path):
    batch_path = os.path.join(os.path.dirname(__file__), 'launch_gta.bat')
    if os.path.exists(batch_path):
        return batch_path
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(f'@echo off\n"{gta_exe_path}"\n')
    return batch_path

class GTA_Mod_Manager:
    def __init__(self, root):
        self.root = root
        self.root.title("GTA San Andreas Mod Manager")
        self.game_path = load_settings()
        self.scripts = []
        self.script_vars = {}  # script: tk.BooleanVar()

        self.setup_ui()
        self.load_game()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=10)
        frame.pack(fill='both', expand=True)

        top_frame = ttk.Frame(frame)
        top_frame.pack(fill='x')

        self.path_label = ttk.Label(top_frame, text="Путь: не выбран")
        self.path_label.pack(side='left', fill='x', expand=True)

        btn_select = ttk.Button(top_frame, text="Выбрать папку", command=self.change_path)
        btn_select.pack(side='right')

        self.list_frame = ttk.Frame(frame)
        self.list_frame.pack(fill='both', expand=True, pady=10)

        self.canvas = tk.Canvas(self.list_frame)
        self.scrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        self.scrollbar.pack(side='right', fill='y')

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', pady=5)

        self.btn_launch = ttk.Button(btn_frame, text="Запустить игру", command=self.launch_game)
        self.btn_launch.pack(side='left', padx=5)

        self.btn_close = ttk.Button(btn_frame, text="Закрыть", command=self.root.destroy)
        self.btn_close.pack(side='right', padx=5)

    def load_game(self):
        self.game_path = load_settings()
        if not os.path.isdir(self.game_path):
            messagebox.showerror("Ошибка", "Путь к игре недействителен.")
            self.game_path = ''
        else:
            self.path_label.config(text=f"Путь: {self.game_path}")
            self.populate_scripts()

        # Создать батник
        if self.game_path:
            self.batch_file = create_batch_file(find_executable(self.game_path))
        else:
            self.batch_file = None

    def change_path(self):
        path = select_game_path()
        if path:
            self.game_path = path
            self.path_label.config(text=f"Путь: {self.game_path}")
            self.populate_scripts()
            if self.game_path:
                self.batch_file = create_batch_file(find_executable(self.game_path))
            else:
                self.batch_file = None

    def populate_scripts(self):
        # Очищаем предыдущие
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.scripts = []

        if not self.game_path:
            return

        # Сканы
        scripts = []

        scripts += scan_for_scripts(self.game_path)
        for subfolder in ['moonloader', 'sampfuncs', 'scripts']:
            sub_path = os.path.join(self.game_path, subfolder)
            if os.path.isdir(sub_path):
                scripts += scan_for_scripts(sub_path)

        modloader_path = os.path.join(self.game_path, 'modloader')
        if os.path.isdir(modloader_path):
            for root, dirs, files in os.walk(modloader_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in SCRIPT_EXTENSIONS):
                        scripts.append(os.path.join(root, file))
        self.scripts = list(set(scripts))
        self.script_vars.clear()

        # Загружаем состояния
        states = load_script_states(self.scripts)

        # Создаём чекбоксы
        for script in self.scripts:
            var = tk.BooleanVar(value=states[script])
            cb = ttk.Checkbutton(self.scrollable_frame, text=os.path.basename(script), variable=var)
            cb.pack(anchor='w')
            self.script_vars[script] = var

    def save_script_states(self):
        for script, var in self.script_vars.items():
            toggle_script(script, var.get())

    def launch_game(self):
        self.save_script_states()
        if hasattr(self, 'batch_file') and self.batch_file:
            subprocess.Popen([self.batch_file])
        else:
            messagebox.showerror("Ошибка", "Нет файла запуска. Выберите папку с игрой.")

if __name__ == '__main__':
    root = tk.Tk()
    app = GTA_Mod_Manager(root)
    root.mainloop()