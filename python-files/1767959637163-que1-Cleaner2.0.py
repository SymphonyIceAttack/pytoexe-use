import os
import sys
import ctypes
import shutil
import winreg
import hashlib
import subprocess
import threading
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from datetime import datetime

# ==================== HWID ЗАЩИТА ====================

class HWIDProtection:
    def __init__(self):
        self.hwid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".license")
        self.current_hwid = self.get_hwid()
    
    def get_hwid(self):
        hwid_parts = []
        
        try:
            result = subprocess.run('wmic baseboard get serialnumber', shell=True, capture_output=True, text=True)
            serial = result.stdout.strip().split('\n')[-1].strip()
            if serial and serial not in ['SerialNumber', 'To be filled by O.E.M.', '']:
                hwid_parts.append(serial)
        except:
            pass
        
        try:
            result = subprocess.run('wmic csproduct get uuid', shell=True, capture_output=True, text=True)
            uuid = result.stdout.strip().split('\n')[-1].strip()
            if uuid and uuid != 'UUID':
                hwid_parts.append(uuid)
        except:
            pass
        
        try:
            result = subprocess.run('wmic diskdrive get serialnumber', shell=True, capture_output=True, text=True)
            lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip()]
            if len(lines) > 1:
                hwid_parts.append(lines[1])
        except:
            pass
        
        try:
            result = subprocess.run('getmac /fo csv /nh', shell=True, capture_output=True, text=True)
            mac = result.stdout.strip().split(',')[0].replace('"', '')
            if mac:
                hwid_parts.append(mac)
        except:
            pass
        
        hwid_parts.append(os.environ.get('COMPUTERNAME', ''))
        
        hwid_string = '|'.join(hwid_parts)
        return hashlib.sha256(hwid_string.encode()).hexdigest()
    
    def check_license(self):
        if not os.path.exists(self.hwid_file):
            return self.first_run()
        
        try:
            with open(self.hwid_file, 'r') as f:
                data = json.load(f)
                saved_hwid = data.get('hwid', '')
                
                if saved_hwid == self.current_hwid:
                    return True
                else:
                    self.show_blocked()
                    return False
        except:
            return self.first_run()
    
    def first_run(self):
        try:
            data = {
                'hwid': self.current_hwid,
                'pc': os.environ.get('COMPUTERNAME', ''),
                'user': os.environ.get('USERNAME', ''),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            with open(self.hwid_file, 'w') as f:
                json.dump(data, f)
            
            os.system(f'attrib +h "{self.hwid_file}"')
            return True
        except:
            return False
    
    def show_blocked(self):
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Доступ запрещен",
            f"⛔ Программа привязана к другому ПК!\n\nВаш HWID:\n{self.current_hwid[:32]}..."
        )
        root.destroy()
        sys.exit()
    
    def get_info(self):
        return f"HWID: {self.current_hwid[:24]}...\nПК: {os.environ.get('COMPUTERNAME', '')}\nПользователь: {os.environ.get('USERNAME', '')}"


# ==================== ПРОВЕРКА ПРАВ ====================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
        sys.exit()


# ==================== ГЛАВНОЕ ПРИЛОЖЕНИЕ ====================

class SystemCleanerPro:
    def __init__(self, hwid_info):
        self.root = tk.Tk()
        self.root.title("System Cleaner Pro v3.0")
        self.root.geometry("950x750")
        self.root.configure(bg="#0d1117")
        self.root.resizable(True, True)
        
        self.hwid_info = hwid_info
        self.found_items = []
        self.is_working = False
        
        self.setup_styles()
        self.create_widgets()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Treeview",
                       background="#161b22",
                       foreground="#c9d1d9",
                       fieldbackground="#161b22",
                       font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                       background="#21262d",
                       foreground="#c9d1d9",
                       font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', '#388bfd')])
        
        style.configure("TNotebook", background="#0d1117")
        style.configure("TNotebook.Tab", 
                       background="#21262d", 
                       foreground="#c9d1d9",
                       padding=[15, 8],
                       font=("Segoe UI", 10))
        style.map("TNotebook.Tab", 
                 background=[('selected', '#388bfd')],
                 foreground=[('selected', 'white')])
        
        style.configure("TCheckbutton",
                       background="#0d1117",
                       foreground="#c9d1d9",
                       font=("Segoe UI", 10))
        
        style.configure("TProgressbar", background="#388bfd", troughcolor="#21262d")
    
    def create_widgets(self):
        # === ЗАГОЛОВОК ===
        header = tk.Frame(self.root, bg="#161b22", pady=10)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🛡️ System Cleaner Pro", font=("Segoe UI", 22, "bold"),
                bg="#161b22", fg="#58a6ff").pack(side=tk.LEFT, padx=20)
        
        info_frame = tk.Frame(header, bg="#161b22")
        info_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(info_frame, text="✓ Лицензия активна", bg="#161b22", fg="#3fb950",
                font=("Segoe UI", 9, "bold")).pack(anchor=tk.E)
        
        admin_text = "✓ Администратор" if is_admin() else "✗ Требуются права"
        admin_color = "#3fb950" if is_admin() else "#f85149"
        tk.Label(info_frame, text=admin_text, bg="#161b22", fg=admin_color,
                font=("Segoe UI", 9)).pack(anchor=tk.E)
        
        tk.Button(info_frame, text="ℹ HWID", command=self.show_hwid,
                 bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 8),
                 relief=tk.FLAT, cursor="hand2").pack(anchor=tk.E, pady=2)
        
        # === ПОИСК ===
        search_frame = tk.Frame(self.root, bg="#21262d", pady=12)
        search_frame.pack(fill=tk.X, padx=15, pady=10)
        
        tk.Label(search_frame, text="🔍 Поиск программы:", bg="#21262d", fg="#c9d1d9",
                font=("Segoe UI", 11)).pack(side=tk.LEFT, padx=10)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                    width=35, font=("Segoe UI", 12),
                                    bg="#0d1117", fg="#c9d1d9",
                                    insertbackground="#c9d1d9", relief=tk.FLAT)
        self.search_entry.pack(side=tk.LEFT, padx=10, ipady=6)
        self.search_entry.bind('<Return>', lambda e: self.start_search())
        
        self.search_btn = tk.Button(search_frame, text="🔍 Найти", command=self.start_search,
                                   font=("Segoe UI", 11), bg="#238636", fg="white",
                                   relief=tk.FLAT, padx=20, pady=5, cursor="hand2")
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = tk.Button(search_frame, text="🗑️ Удалить всё", command=self.delete_all,
                                   font=("Segoe UI", 11), bg="#da3633", fg="white",
                                   relief=tk.FLAT, padx=20, pady=5, cursor="hand2")
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # === ВКЛАДКИ ===
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        self.create_search_tab()
        self.create_quick_tab()
        self.create_browser_tab()
        self.create_registry_tab()
        self.create_log_tab()
        
        # === ПРОГРЕСС ===
        progress_frame = tk.Frame(self.root, bg="#0d1117")
        progress_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                        maximum=100, length=400)
        self.progress.pack(side=tk.LEFT, padx=10)
        
        self.status_var = tk.StringVar(value="Готов к работе")
        tk.Label(progress_frame, textvariable=self.status_var, bg="#0d1117",
                fg="#8b949e", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=10)
        
        self.count_var = tk.StringVar(value="Найдено: 0")
        tk.Label(progress_frame, textvariable=self.count_var, bg="#0d1117",
                fg="#58a6ff", font=("Segoe UI", 10, "bold")).pack(side=tk.RIGHT, padx=10)
    
    def create_search_tab(self):
        tab = tk.Frame(self.notebook, bg="#0d1117")
        self.notebook.add(tab, text="📁 Результаты поиска")
        
        columns = ("Путь", "Тип", "Размер")
        self.tree = ttk.Treeview(tab, columns=columns, show="headings", height=18)
        
        self.tree.heading("Путь", text="Путь к файлу/папке")
        self.tree.heading("Тип", text="Тип")
        self.tree.heading("Размер", text="Размер")
        
        self.tree.column("Путь", width=580)
        self.tree.column("Тип", width=100)
        self.tree.column("Размер", width=100)
        
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    def create_quick_tab(self):
        tab = tk.Frame(self.notebook, bg="#0d1117")
        self.notebook.add(tab, text="⚡ Быстрая очистка")
        
        self.clean_options = {}
        
        options = [
            ("prefetch", "📁 Prefetch (предзагрузка)", True),
            ("temp", "🗑️ Временные файлы (Temp)", True),
            ("recent", "📄 Недавние документы", True),
            ("thumbnails", "🖼️ Кэш миниатюр", True),
            ("shellbag", "📂 История папок (ShellBag)", True),
            ("userassist", "▶️ История запуска (UserAssist)", True),
            ("runmru", "⌨️ История команд (RunMRU)", True),
            ("typedpaths", "📝 Введенные пути", True),
            ("dns", "🌐 Кэш DNS", True),
            ("recycle", "♻️ Корзина", False),
            ("eventlog", "📋 Журналы событий", False),
            ("jumplist", "📌 Jump Lists", True),
        ]
        
        frame = tk.Frame(tab, bg="#0d1117")
        frame.pack(pady=20, padx=30)
        
        for i, (key, text, default) in enumerate(options):
            var = tk.BooleanVar(value=default)
            self.clean_options[key] = var
            
            cb = ttk.Checkbutton(frame, text=text, variable=var)
            cb.grid(row=i//3, column=i%3, sticky=tk.W, padx=25, pady=10)
        
        btn_frame = tk.Frame(tab, bg="#0d1117")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="✓ Выбрать всё", command=self.select_all,
                 bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 10),
                 relief=tk.FLAT, padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="✗ Снять всё", command=self.deselect_all,
                 bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 10),
                 relief=tk.FLAT, padx=15, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="🧹 Очистить выбранное", command=self.clean_selected,
                 bg="#238636", fg="white", font=("Segoe UI", 11, "bold"),
                 relief=tk.FLAT, padx=25, pady=8, cursor="hand2").pack(side=tk.LEFT, padx=20)
    
    def create_browser_tab(self):
        tab = tk.Frame(self.notebook, bg="#0d1117")
        self.notebook.add(tab, text="🌐 Браузеры")
        
        self.browser_options = {}
        
        browsers = [
            ("chrome", "🌐 Google Chrome"),
            ("edge", "🌐 Microsoft Edge"),
            ("firefox", "🦊 Mozilla Firefox"),
            ("opera", "🔴 Opera"),
        ]
        
        data_types = [
            ("history", "История"),
            ("cookies", "Cookies"),
            ("cache", "Кэш"),
            ("passwords", "Пароли"),
        ]
        
        frame = tk.Frame(tab, bg="#0d1117")
        frame.pack(pady=30)
        
        tk.Label(frame, text="Браузер", bg="#0d1117", fg="#58a6ff",
                font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=20, pady=10)
        
        for j, (_, name) in enumerate(data_types, 1):
            tk.Label(frame, text=name, bg="#0d1117", fg="#58a6ff",
                    font=("Segoe UI", 10, "bold")).grid(row=0, column=j, padx=15, pady=10)
        
        for i, (browser, bname) in enumerate(browsers, 1):
            tk.Label(frame, text=bname, bg="#0d1117", fg="#c9d1d9",
                    font=("Segoe UI", 10)).grid(row=i, column=0, sticky=tk.W, padx=20, pady=8)
            
            for j, (dtype, _) in enumerate(data_types, 1):
                key = f"{browser}_{dtype}"
                var = tk.BooleanVar(value=(dtype != "passwords"))
                self.browser_options[key] = var
                
                cb = ttk.Checkbutton(frame, variable=var)
                cb.grid(row=i, column=j, padx=15, pady=8)
        
        tk.Button(tab, text="🧹 Очистить браузеры", command=self.clean_browsers,
                 bg="#238636", fg="white", font=("Segoe UI", 11, "bold"),
                 relief=tk.FLAT, padx=30, pady=10, cursor="hand2").pack(pady=20)
        
        tk.Label(tab, text="⚠️ Закройте все браузеры перед очисткой!",
                bg="#0d1117", fg="#f0883e", font=("Segoe UI", 10)).pack()
    
    def create_registry_tab(self):
        tab = tk.Frame(self.notebook, bg="#0d1117")
        self.notebook.add(tab, text="🔧 Реестр")
        
        btn_frame = tk.Frame(tab, bg="#0d1117")
        btn_frame.pack(pady=30)
        
        buttons = [
            ("📂 Очистить ShellBag", self.clean_shellbag_full),
            ("▶️ Очистить UserAssist", self.clean_userassist_full),
            ("📄 Очистить RecentDocs", self.clean_recentdocs),
            ("⌨️ Очистить RunMRU", self.clean_runmru),
            ("📝 Очистить TypedPaths", self.clean_typedpaths),
            ("🔗 Очистить ComDlg32", self.clean_comdlg),
            ("🔄 Очистить MUICache", self.clean_muicache),
        ]
        
        for i, (text, cmd) in enumerate(buttons):
            tk.Button(btn_frame, text=text, command=cmd,
                     bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 10),
                     relief=tk.FLAT, padx=20, pady=8, width=25, cursor="hand2"
                     ).grid(row=i//2, column=i%2, padx=15, pady=10)
        
        tk.Button(tab, text="🧹 ОЧИСТИТЬ ВСЁ В РЕЕСТРЕ", command=self.clean_all_registry,
                 bg="#da3633", fg="white", font=("Segoe UI", 12, "bold"),
                 relief=tk.FLAT, padx=30, pady=12, cursor="hand2").pack(pady=30)
    
    def create_log_tab(self):
        tab = tk.Frame(self.notebook, bg="#0d1117")
        self.notebook.add(tab, text="📋 Лог")
        
        self.log_text = scrolledtext.ScrolledText(tab, font=("Consolas", 10),
                                                  bg="#161b22", fg="#7ee787",
                                                  insertbackground="#7ee787")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        btn_frame = tk.Frame(tab, bg="#0d1117")
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="🗑️ Очистить лог", command=self.clear_log,
                 bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 9),
                 relief=tk.FLAT, padx=15, cursor="hand2").pack(side=tk.LEFT, padx=10)
        
        tk.Button(btn_frame, text="💾 Сохранить лог", command=self.save_log,
                 bg="#21262d", fg="#c9d1d9", font=("Segoe UI", 9),
                 relief=tk.FLAT, padx=15, cursor="hand2").pack(side=tk.LEFT, padx=10)
    
    # ==================== ФУНКЦИИ ====================
    
    def log(self, msg, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def show_hwid(self):
        messagebox.showinfo("Информация о лицензии", self.hwid_info)
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text", "*.txt")])
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            messagebox.showinfo("Готово", f"Лог сохранен: {filename}")
    
    def select_all(self):
        for var in self.clean_options.values():
            var.set(True)
    
    def deselect_all(self):
        for var in self.clean_options.values():
            var.set(False)
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def get_folder_size(self, path):
        total = 0
        try:
            for root, dirs, files in os.walk(path):
                for f in files:
                    try:
                        total += os.path.getsize(os.path.join(root, f))
                    except:
                        pass
        except:
            pass
        return total
    
    # ==================== ПОИСК ====================
    
    def start_search(self):
        pattern = self.search_var.get().strip()
        
        if not pattern:
            messagebox.showwarning("Внимание", "Введите название программы")
            return
        
        if len(pattern) < 2:
            messagebox.showwarning("Внимание", "Минимум 2 символа")
            return
        
        if self.is_working:
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.found_items = []
        self.is_working = True
        self.search_btn.config(state=tk.DISABLED)
        self.notebook.select(0)
        
        thread = threading.Thread(target=self.search_disk, args=(pattern,))
        thread.daemon = True
        thread.start()
    
    def search_disk(self, pattern):
        pattern_lower = pattern.lower()
        
        self.log(f"\n{'='*50}")
        self.log(f"ПОИСК: '{pattern}'")
        self.log(f"{'='*50}")
        
        search_paths = [
            ("C:\\Program Files", 1),
            ("C:\\Program Files (x86)", 1),
            ("C:\\ProgramData", 2),
            (os.environ.get('APPDATA', ''), 3),
            (os.environ.get('LOCALAPPDATA', ''), 3),
            (os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'), 1),
            (os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads'), 1),
            (os.path.join(os.environ.get('USERPROFILE', ''), 'Documents'), 1),
            (os.environ.get('TEMP', ''), 1),
            (os.path.join(os.environ.get('WINDIR', ''), 'Prefetch'), 1),
        ]
        
        total_paths = len(search_paths)
        
        for idx, (base_path, max_depth) in enumerate(search_paths):
            if not base_path or not os.path.exists(base_path):
                continue
            
            self.progress_var.set((idx / total_paths) * 50)
            self.status_var.set(f"Сканирую: {os.path.basename(base_path)}")
            
            try:
                for root, dirs, files in os.walk(base_path):
                    depth = root.replace(base_path, '').count(os.sep)
                    if depth > max_depth:
                        dirs.clear()
                        continue
                    
                    for name in dirs + files:
                        if pattern_lower in name.lower():
                            self.add_found_item(os.path.join(root, name))
            except:
                pass
        
        self.progress_var.set(60)
        self.status_var.set("Поиск в реестре...")
        self.log("Поиск в реестре...")
        self.search_registry(pattern_lower)
        
        self.progress_var.set(100)
        self.status_var.set(f"Готово. Найдено: {len(self.found_items)}")
        self.count_var.set(f"Найдено: {len(self.found_items)}")
        self.log(f"\n{'='*50}")
        self.log(f"НАЙДЕНО: {len(self.found_items)} элементов")
        self.log(f"{'='*50}")
        
        self.is_working = False
        self.search_btn.config(state=tk.NORMAL)
    
    def add_found_item(self, path):
        if path in [item['path'] for item in self.found_items]:
            return
        
        try:
            if os.path.isfile(path):
                size = os.path.getsize(path)
                item_type = "Файл"
            elif os.path.isdir(path):
                size = self.get_folder_size(path)
                item_type = "Папка"
            else:
                return
            
            self.found_items.append({'path': path, 'type': item_type, 'size': size})
            self.tree.insert("", tk.END, values=(path, item_type, self.format_size(size)))
            self.count_var.set(f"Найдено: {len(self.found_items)}")
            self.root.update()
        except:
            pass
    
    def search_registry(self, pattern):
        locations = [
            (winreg.HKEY_CURRENT_USER, "HKCU", r"Software"),
            (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"SOFTWARE"),
            (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hkey, hkey_name, base_path in locations:
            try:
                key = winreg.OpenKey(hkey, base_path, 0, winreg.KEY_READ)
                
                i = 0
                while True:
                    try:
                        subkey = winreg.EnumKey(key, i)
                        
                        if pattern in subkey.lower():
                            full_path = f"{hkey_name}\\{base_path}\\{subkey}"
                            
                            self.found_items.append({
                                'path': full_path,
                                'type': 'Реестр',
                                'size': 0,
                                'hkey': hkey,
                                'reg_path': f"{base_path}\\{subkey}"
                            })
                            
                            self.tree.insert("", tk.END, values=(full_path, "Реестр", "-"))
                            self.count_var.set(f"Найдено: {len(self.found_items)}")
                        
                        i += 1
                    except OSError:
                        break
                
                winreg.CloseKey(key)
            except:
                pass
    
    # ==================== УДАЛЕНИЕ ====================
    
    def delete_all(self):
        if not self.found_items:
            messagebox.showwarning("Внимание", "Сначала выполните поиск")
            return
        
        if not messagebox.askyesno("Подтверждение",
                                   f"Удалить {len(self.found_items)} элементов?\n\nЭто действие необратимо!"):
            return
        
        self.is_working = True
        thread = threading.Thread(target=self.do_delete_all)
        thread.daemon = True
        thread.start()
    
    def do_delete_all(self):
        self.log(f"\n{'='*50}")
        self.log(f"УДАЛЕНИЕ: {len(self.found_items)} элементов")
        self.log(f"{'='*50}")
        
        deleted = 0
        errors = 0
        total = len(self.found_items)
        
        for i, item in enumerate(self.found_items):
            self.progress_var.set((i / total) * 100)
            path = item['path']
            item_type = item['type']
            
            try:
                if item_type == "Реестр":
                    hkey_name = "HKCU" if "HKCU" in path else "HKLM"
                    reg_path = item.get('reg_path', '')
                    if reg_path:
                        result = os.system(f'reg delete "{hkey_name}\\{reg_path}" /f >nul 2>&1')
                        if result == 0:
                            self.log(f"[OK] Реестр: {path}")
                            deleted += 1
                        else:
                            errors += 1
                
                elif item_type == "Файл":
                    if os.path.exists(path):
                        os.remove(path)
                        self.log(f"[OK] Файл: {path}")
                        deleted += 1
                
                elif item_type == "Папка":
                    if os.path.exists(path):
                        shutil.rmtree(path, ignore_errors=True)
                        if not os.path.exists(path):
                            self.log(f"[OK] Папка: {path}")
                            deleted += 1
                        else:
                            os.system(f'rd /s /q "{path}" >nul 2>&1')
                            deleted += 1
            except Exception as e:
                self.log(f"[X] Ошибка: {path}")
                errors += 1
        
        self.clean_related_traces()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.found_items = []
        
        self.progress_var.set(100)
        self.status_var.set(f"Удалено: {deleted}, Ошибок: {errors}")
        self.count_var.set("Найдено: 0")
        
        self.log(f"\n{'='*50}")
        self.log(f"УДАЛЕНО: {deleted}, ОШИБОК: {errors}")
        self.log(f"{'='*50}")
        
        self.is_working = False
        messagebox.showinfo("Готово", f"Удалено: {deleted}\nОшибок: {errors}")
    
    def clean_related_traces(self):
        self.log("\nОчистка связанных следов...")
        
        pattern = self.search_var.get().strip().lower()
        
        # ShellBag
        for key in [r"HKCU\Software\Microsoft\Windows\Shell\BagMRU",
                    r"HKCU\Software\Microsoft\Windows\Shell\Bags"]:
            os.system(f'reg delete "{key}" /f >nul 2>&1')
        
        # UserAssist
        self.clean_userassist_pattern(pattern)
        
        # Prefetch
        prefetch = os.path.join(os.environ.get('WINDIR', ''), 'Prefetch')
        if os.path.exists(prefetch):
            for f in os.listdir(prefetch):
                if pattern in f.lower() and f.endswith('.pf'):
                    try:
                        os.remove(os.path.join(prefetch, f))
                    except:
                        pass
        
        # Recent
        recent = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Recent')
        if os.path.exists(recent):
            for f in os.listdir(recent):
                if pattern in f.lower():
                    try:
                        p = os.path.join(recent, f)
                        if os.path.isfile(p):
                            os.remove(p)
                    except:
                        pass
        
        self.log("Следы очищены")
    
    def clean_userassist_pattern(self, pattern):
        try:
            ua_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ua_path, 0, winreg.KEY_READ)
            
            guids = []
            i = 0
            while True:
                try:
                    guids.append(winreg.EnumKey(key, i))
                    i += 1
                except:
                    break
            winreg.CloseKey(key)
            
            for guid in guids:
                try:
                    count_path = f"{ua_path}\\{guid}\\Count"
                    ck = winreg.OpenKey(winreg.HKEY_CURRENT_USER, count_path, 0, winreg.KEY_ALL_ACCESS)
                    
                    to_delete = []
                    j = 0
                    while True:
                        try:
                            name = winreg.EnumValue(ck, j)[0]
                            decoded = self.rot13(name)
                            if pattern in decoded.lower():
                                to_delete.append(name)
                            j += 1
                        except:
                            break
                    
                    for name in to_delete:
                        try:
                            winreg.DeleteValue(ck, name)
                        except:
                            pass
                    
                    winreg.CloseKey(ck)
                except:
                    pass
        except:
            pass
    
    def rot13(self, text):
        result = ""
        for c in text:
            if 'a' <= c <= 'z':
                result += chr((ord(c) - ord('a') + 13) % 26 + ord('a'))
            elif 'A' <= c <= 'Z':
                result += chr((ord(c) - ord('A') + 13) % 26 + ord('A'))
            else:
                result += c
        return result
    
    # ==================== БЫСТРАЯ ОЧИСТКА ====================
    
    def clean_selected(self):
        if not messagebox.askyesno("Подтверждение", "Выполнить очистку выбранных элементов?"):
            return
        
        self.is_working = True
        thread = threading.Thread(target=self.do_clean_selected)
        thread.daemon = True
        thread.start()
    
    def do_clean_selected(self):
        self.log(f"\n{'='*50}")
        self.log("БЫСТРАЯ ОЧИСТКА")
        self.log(f"{'='*50}")
        
        total = 0
        opts = self.clean_options
        
        if opts["prefetch"].get():
            total += self.clean_prefetch()
        if opts["temp"].get():
            total += self.clean_temp()
        if opts["recent"].get():
            total += self.clean_recent()
        if opts["thumbnails"].get():
            total += self.clean_thumbnails()
        if opts["shellbag"].get():
            total += self.clean_shellbag()
        if opts["userassist"].get():
            total += self.clean_userassist()
        if opts["runmru"].get():
            total += self.clean_runmru_silent()
        if opts["typedpaths"].get():
            total += self.clean_typedpaths_silent()
        if opts["dns"].get():
            self.clean_dns()
        if opts["recycle"].get():
            self.clean_recycle()
        if opts["eventlog"].get():
            self.clean_eventlog()
        if opts["jumplist"].get():
            total += self.clean_jumplist()
        
        self.progress_var.set(100)
        self.status_var.set(f"Очищено: {total}")
        
        self.log(f"\n{'='*50}")
        self.log(f"ОЧИЩЕНО: {total} элементов")
        self.log(f"{'='*50}")
        
        self.is_working = False
        messagebox.showinfo("Готово", f"Очистка завершена!\nУдалено: {total}")
    
    def clean_prefetch(self):
        self.log("Очистка Prefetch...")
        count = 0
        prefetch = os.path.join(os.environ.get('WINDIR', ''), 'Prefetch')
        
        if os.path.exists(prefetch):
            for f in os.listdir(prefetch):
                if f.endswith('.pf'):
                    try:
                        os.remove(os.path.join(prefetch, f))
                        count += 1
                    except:
                        pass
        
        self.log(f"  Prefetch: {count}")
        return count
    
    def clean_temp(self):
        self.log("Очистка Temp...")
        count = 0
        
        for temp in [os.environ.get('TEMP', ''), os.path.join(os.environ.get('WINDIR', ''), 'Temp')]:
            if temp and os.path.exists(temp):
                for item in os.listdir(temp):
                    try:
                        path = os.path.join(temp, item)
                        if os.path.isfile(path):
                            os.remove(path)
                        else:
                            shutil.rmtree(path, ignore_errors=True)
                        count += 1
                    except:
                        pass
        
        self.log(f"  Temp: {count}")
        return count
    
    def clean_recent(self):
        self.log("Очистка Recent...")
        count = 0
        recent = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Recent')
        
        if os.path.exists(recent):
            for item in os.listdir(recent):
                try:
                    path = os.path.join(recent, item)
                    if os.path.isfile(path):
                        os.remove(path)
                    else:
                        shutil.rmtree(path, ignore_errors=True)
                    count += 1
                except:
                    pass
        
        self.log(f"  Recent: {count}")
        return count
    
    def clean_thumbnails(self):
        self.log("Очистка Thumbnails...")
        count = 0
        thumbs = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Explorer')
        
        if os.path.exists(thumbs):
            for f in os.listdir(thumbs):
                if 'thumbcache' in f.lower() or f.endswith('.db'):
                    try:
                        os.remove(os.path.join(thumbs, f))
                        count += 1
                    except:
                        pass
        
        self.log(f"  Thumbnails: {count}")
        return count
    
    def clean_shellbag(self):
        self.log("Очистка ShellBag...")
        count = 0
        
        keys = [
            r"HKCU\Software\Microsoft\Windows\Shell\BagMRU",
            r"HKCU\Software\Microsoft\Windows\Shell\Bags",
            r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU",
            r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\Bags",
        ]
        
        for key in keys:
            if os.system(f'reg delete "{key}" /f >nul 2>&1') == 0:
                count += 1
        
        self.log(f"  ShellBag: {count}")
        return count
    
    def clean_userassist(self):
        self.log("Очистка UserAssist...")
        count = 0
        
        try:
            ua_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ua_path, 0, winreg.KEY_READ)
            
            guids = []
            i = 0
            while True:
                try:
                    guids.append(winreg.EnumKey(key, i))
                    i += 1
                except:
                    break
            winreg.CloseKey(key)
            
            for guid in guids:
                try:
                    count_path = f"{ua_path}\\{guid}\\Count"
                    ck = winreg.OpenKey(winreg.HKEY_CURRENT_USER, count_path, 0, winreg.KEY_ALL_ACCESS)
                    
                    while True:
                        try:
                            name = winreg.EnumValue(ck, 0)[0]
                            winreg.DeleteValue(ck, name)
                            count += 1
                        except:
                            break
                    
                    winreg.CloseKey(ck)
                except:
                    pass
        except:
            pass
        
        self.log(f"  UserAssist: {count}")
        return count
    
    def clean_runmru_silent(self):
        os.system(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU" /f >nul 2>&1')
        return 1
    
    def clean_typedpaths_silent(self):
        os.system(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths" /f >nul 2>&1')
        return 1
    
    def clean_dns(self):
        self.log("Очистка DNS...")
        os.system('ipconfig /flushdns >nul 2>&1')
        self.log("  DNS: OK")
    
    def clean_recycle(self):
        self.log("Очистка корзины...")
        os.system('PowerShell.exe -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"')
        self.log("  Корзина: OK")
    
    def clean_eventlog(self):
        self.log("Очистка журналов...")
        for log in ['Application', 'Security', 'System']:
            os.system(f'wevtutil cl {log} >nul 2>&1')
        self.log("  Журналы: OK")
    
    def clean_jumplist(self):
        self.log("Очистка Jump Lists...")
        count = 0
        
        for folder in ['AutomaticDestinations', 'CustomDestinations']:
            path = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Recent', folder)
            if os.path.exists(path):
                for f in os.listdir(path):
                    try:
                        os.remove(os.path.join(path, f))
                        count += 1
                    except:
                        pass
        
        self.log(f"  Jump Lists: {count}")
        return count
    
    # ==================== КНОПКИ РЕЕСТРА ====================
    
    def clean_shellbag_full(self):
        self.log("\n=== Очистка ShellBag ===")
        count = self.clean_shellbag()
        messagebox.showinfo("Готово", f"ShellBag очищен: {count}")
    
    def clean_userassist_full(self):
        self.log("\n=== Очистка UserAssist ===")
        count = self.clean_userassist()
        messagebox.showinfo("Готово", f"UserAssist очищен: {count}")
    
    def clean_recentdocs(self):
        self.log("\n=== Очистка RecentDocs ===")
        os.system(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs" /f >nul 2>&1')
        messagebox.showinfo("Готово", "RecentDocs очищен")
    
    def clean_runmru(self):
        self.log("\n=== Очистка RunMRU ===")
        os.system(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU" /f >nul 2>&1')
        messagebox.showinfo("Готово", "RunMRU очищен")
    
    def clean_typedpaths(self):
        self.log("\n=== Очистка TypedPaths ===")
        os.system(r'reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths" /f >nul 2>&1')
        messagebox.showinfo("Готово", "TypedPaths очищен")
    
    def clean_comdlg(self):
        self.log("\n=== Очистка ComDlg32 ===")
        keys = [
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU",
        ]
        for key in keys:
            os.system(f'reg delete "{key}" /f >nul 2>&1')
        messagebox.showinfo("Готово", "ComDlg32 очищен")
    
    def clean_muicache(self):
        self.log("\n=== Очистка MUICache ===")
        os.system(r'reg delete "HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache" /f >nul 2>&1')
        messagebox.showinfo("Готово", "MUICache очищен")
    
    def clean_all_registry(self):
        if not messagebox.askyesno("Подтверждение", "Очистить ВСЕ следы в реестре?"):
            return
        
        self.log("\n=== ПОЛНАЯ ОЧИСТКА РЕЕСТРА ===")
        
        self.clean_shellbag()
        self.clean_userassist()
        self.clean_runmru_silent()
        self.clean_typedpaths_silent()
        
        keys = [
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePidlMRU",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU",
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery",
            r"HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache",
        ]
        
        for key in keys:
            os.system(f'reg delete "{key}" /f >nul 2>&1')
        
        self.log("Реестр полностью очищен")
        messagebox.showinfo("Готово", "Реестр полностью очищен!")
    
    # ==================== БРАУЗЕРЫ ====================
    
    def clean_browsers(self):
        if not messagebox.askyesno("Подтверждение", "Очистить данные браузеров?\n\nЗакройте все браузеры!"):
            return
        
        self.log("\n=== ОЧИСТКА БРАУЗЕРОВ ===")
        
        browsers = {
            'chrome': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data', 'Default'),
            'edge': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data', 'Default'),
            'firefox': os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles'),
            'opera': os.path.join(os.environ.get('APPDATA', ''), 'Opera Software', 'Opera Stable'),
        }
        
        files_map = {
            'history': ['History', 'Visited Links', 'History-journal'],
            'cookies': ['Cookies', 'Cookies-journal'],
            'cache': ['Cache', 'Code Cache', 'GPUCache'],
            'passwords': ['Login Data', 'Login Data-journal'],
        }
        
        count = 0
        
        for browser, base_path in browsers.items():
            if not os.path.exists(base_path):
                continue
            
            for dtype, files in files_map.items():
                key = f"{browser}_{dtype}"
                if key in self.browser_options and self.browser_options[key].get():
                    for fname in files:
                        fpath = os.path.join(base_path, fname)
                        if os.path.exists(fpath):
                            try:
                                if os.path.isfile(fpath):
                                    os.remove(fpath)
                                else:
                                    shutil.rmtree(fpath, ignore_errors=True)
                                self.log(f"  [{browser}] {fname}")
                                count += 1
                            except:
                                pass
        
        self.log(f"\nОчищено файлов браузеров: {count}")
        messagebox.showinfo("Готово", f"Браузеры очищены!\nУдалено: {count}")
    
    def run(self):
        self.root.mainloop()


# ==================== ЗАПУСК ====================

def main():
    # Проверка HWID
    hwid = HWIDProtection()
    
    if not hwid.check_license():
        sys.exit()
    
    # Права администратора
    run_as_admin()
    
    # Запуск
    try:
        app = SystemCleanerPro(hwid.get_info())
        app.run()
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

if __name__ == "__main__":
    main()