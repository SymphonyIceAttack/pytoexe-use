import os
import sys
import subprocess
import winreg
import shutil
import ctypes
import tempfile
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog

# ========== Проверка прав администратора ==========
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    # Перезапуск с правами администратора
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# ========== Вспомогательные функции ==========
def run_cmd(cmd, capture=True):
    """Выполняет команду cmd и возвращает вывод (если capture=True)"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='cp866')
            return result.stdout + result.stderr
        else:
            subprocess.Popen(cmd, shell=True)
            return ""
    except Exception as e:
        return str(e)

def reg_key_exists(hive, subkey):
    """Проверяет существование ключа реестра"""
    try:
        key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False

def reg_delete_key(hive, subkey, key_name=None):
    """Удаляет ключ или значение"""
    try:
        key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_WRITE)
        if key_name:
            winreg.DeleteValue(key, key_name)
        else:
            winreg.DeleteKey(key, "")
        winreg.CloseKey(key)
        return True
    except:
        return False

def reg_set_value(hive, subkey, name, value, typ=winreg.REG_SZ):
    """Устанавливает значение в реестре"""
    try:
        key = winreg.CreateKey(hive, subkey)
        winreg.SetValueEx(key, name, 0, typ, value)
        winreg.CloseKey(key)
        return True
    except:
        return False

# ========== GUI ==========
class SystemCommander(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("System Commander Pro")
        self.geometry("1100x700")
        self.configure(bg="#1e1e2e")
        
        # Стиль
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background="#1e1e2e", bordercolor="#3c3c4a")
        style.configure("TNotebook.Tab", background="#2a2a36", foreground="#cdd6f4", padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", "#45475a")])
        style.configure("TFrame", background="#2a2a36")
        style.configure("TLabel", background="#2a2a36", foreground="#cdd6f4")
        style.configure("TButton", background="#45475a", foreground="#cdd6f4", borderwidth=0, focusthickness=0)
        style.map("TButton", background=[("active", "#585b70")])
        style.configure("Treeview", background="#1e1e2e", foreground="#cdd6f4", fieldbackground="#1e1e2e", borderwidth=0)
        style.map("Treeview", background=[("selected", "#45475a")])
        
        # Вкладки
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.create_processes_tab()
        self.create_autorun_tab()
        self.create_services_tab()
        self.create_registry_tab()
        self.create_cleaner_tab()
        self.create_users_tab()
        self.create_associations_tab()
        self.create_advanced_tab()
    
    # ------------------ Диспетчер задач ------------------
    def create_processes_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Диспетчер задач")
        
        # Таблица
        columns = ("PID", "Имя", "CPU %", "Память (МБ)")
        self.process_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        for col in columns:
            self.process_tree.heading(col, text=col)
            self.process_tree.column(col, width=100)
        self.process_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_processes).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Завершить процесс", command=self.kill_process).pack(side='left', padx=5)
        
        self.refresh_processes()
    
    def refresh_processes(self):
        # Очистка
        for row in self.process_tree.get_children():
            self.process_tree.delete(row)
        # Получение списка процессов через tasklist
        output = run_cmd("tasklist /FO CSV /NH", capture=True)
        for line in output.strip().split('\n'):
            if not line:
                continue
            parts = line.strip('"').split('","')
            if len(parts) >= 5:
                pid = parts[1]
                name = parts[0]
                mem = int(parts[4].replace(',', '')) // (1024 * 1024) if parts[4].isdigit() else 0
                # CPU через wmic (можно и так, но оставим простым)
                self.process_tree.insert('', 'end', values=(pid, name, "N/A", mem))
        # Обновление CPU через wmic (отдельно)
        # Для простоты оставим CPU как N/A, либо можно сделать отдельный поток
    
    def kill_process(self):
        selected = self.process_tree.selection()
        if not selected:
            messagebox.showwarning("Нет выбора", "Выберите процесс для завершения")
            return
        pid = self.process_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Подтверждение", f"Завершить процесс PID {pid}?"):
            run_cmd(f"taskkill /F /PID {pid}", capture=False)
            self.refresh_processes()
    
    # ------------------ Автозагрузка ------------------
    def create_autorun_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Автозагрузка")
        
        self.autorun_tree = ttk.Treeview(frame, columns=("Источник", "Имя", "Команда"), show="headings")
        for col in ("Источник", "Имя", "Команда"):
            self.autorun_tree.heading(col, text=col)
            self.autorun_tree.column(col, width=200)
        self.autorun_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_autorun).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Удалить запись", command=self.delete_autorun_entry).pack(side='left', padx=5)
        
        self.refresh_autorun()
    
    def refresh_autorun(self):
        for row in self.autorun_tree.get_children():
            self.autorun_tree.delete(row)
        
        # Реестр Run (HKLM, HKCU)
        autorun_locations = [
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM\\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU\\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKLM\\RunOnce"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce", "HKCU\\RunOnce"),
        ]
        for hive, subkey, source in autorun_locations:
            try:
                key = winreg.OpenKey(hive, subkey, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        self.autorun_tree.insert('', 'end', values=(source, name, value))
                        i += 1
                    except WindowsError:
                        break
                winreg.CloseKey(key)
            except:
                pass
        
        # Папка автозагрузки
        startup_folder = os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup")
        if os.path.exists(startup_folder):
            for file in os.listdir(startup_folder):
                if file.endswith(('.lnk', '.exe', '.bat')):
                    self.autorun_tree.insert('', 'end', values=("Папка автозагрузки", file, os.path.join(startup_folder, file)))
        
        # Планировщик задач (через schtasks)
        output = run_cmd("schtasks /Query /FO CSV /NH", capture=True)
        for line in output.split('\n'):
            if line and '"' in line:
                parts = line.strip('"').split('","')
                if len(parts) >= 2:
                    taskname = parts[0]
                    next_run = parts[1] if len(parts) > 1 else ""
                    self.autorun_tree.insert('', 'end', values=("Планировщик", taskname, next_run))
        
        # Службы (автозапуск)
        services = run_cmd('sc query type= service state= all | findstr /C:"SERVICE_NAME" /C:"START_TYPE"', capture=True)
        # Парсинг сложный, упростим: выводим только имя службы с автозапуском через sc query
        # Но для краткости пропустим, службы есть в отдельной вкладке
    
    def delete_autorun_entry(self):
        selected = self.autorun_tree.selection()
        if not selected:
            return
        values = self.autorun_tree.item(selected[0])['values']
        source = values[0]
        name = values[1]
        if "HKLM" in source or "HKCU" in source:
            # Определяем hive
            if "HKLM" in source:
                hive = winreg.HKEY_LOCAL_MACHINE
            else:
                hive = winreg.HKEY_CURRENT_USER
            subkey = source.split('\\', 1)[1]  # после HKLM\ или HKCU\
            if reg_delete_key(hive, subkey, name):
                messagebox.showinfo("Удалено", f"Запись '{name}' удалена из реестра")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить запись")
        elif source == "Папка автозагрузки":
            file_path = values[2]
            if os.path.exists(file_path):
                os.remove(file_path)
                messagebox.showinfo("Удалено", f"Файл {name} удалён из папки автозагрузки")
        else:
            messagebox.showinfo("Инфо", "Удаление из планировщика или служб не реализовано в этой вкладке")
        self.refresh_autorun()
    
    # ------------------ Службы ------------------
    def create_services_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Службы")
        
        self.services_tree = ttk.Treeview(frame, columns=("Имя", "Отображаемое имя", "Статус", "Тип запуска"), show="headings")
        for col in ("Имя", "Отображаемое имя", "Статус", "Тип запуска"):
            self.services_tree.heading(col, text=col)
            self.services_tree.column(col, width=200)
        self.services_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Обновить", command=self.refresh_services).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Запустить", command=self.start_service).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Остановить", command=self.stop_service).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_service).pack(side='left', padx=5)
        
        self.refresh_services()
    
    def refresh_services(self):
        for row in self.services_tree.get_children():
            self.services_tree.delete(row)
        output = run_cmd('sc query type= service state= all', capture=True)
        # Парсинг sc query (сложно, используем wmic для простоты)
        wmic_output = run_cmd('wmic service get name,displayname,startmode,state /format:csv', capture=True)
        lines = wmic_output.split('\n')
        for line in lines[1:]:
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                name = parts[1].strip('"')
                display = parts[2].strip('"')
                startmode = parts[3].strip('"')
                state = parts[4].strip('"')
                self.services_tree.insert('', 'end', values=(name, display, state, startmode))
    
    def start_service(self):
        selected = self.services_tree.selection()
        if not selected:
            return
        name = self.services_tree.item(selected[0])['values'][0]
        run_cmd(f"net start {name}", capture=False)
        self.refresh_services()
    
    def stop_service(self):
        selected = self.services_tree.selection()
        if not selected:
            return
        name = self.services_tree.item(selected[0])['values'][0]
        run_cmd(f"net stop {name}", capture=False)
        self.refresh_services()
    
    def delete_service(self):
        selected = self.services_tree.selection()
        if not selected:
            return
        name = self.services_tree.item(selected[0])['values'][0]
        if messagebox.askyesno("Удаление службы", f"Удалить службу {name}? Это действие необратимо."):
            run_cmd(f"sc delete {name}", capture=False)
            self.refresh_services()
    
    # ------------------ Реестр и блокировки ------------------
    def create_registry_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Блокировки")
        
        notebook2 = ttk.Notebook(frame)
        notebook2.pack(fill='both', expand=True)
        
        # Вкладка Hosts
        hosts_frame = ttk.Frame(notebook2)
        notebook2.add(hosts_frame, text="Hosts")
        self.hosts_text = scrolledtext.ScrolledText(hosts_frame, bg="#1e1e2e", fg="#cdd6f4", insertbackground="white")
        self.hosts_text.pack(fill='both', expand=True, padx=5, pady=5)
        ttk.Button(hosts_frame, text="Сохранить hosts", command=self.save_hosts).pack(pady=5)
        self.load_hosts()
        
        # Вкладка DisallowRun
        disallow_frame = ttk.Frame(notebook2)
        notebook2.add(disallow_frame, text="DisallowRun")
        self.disallow_listbox = tk.Listbox(disallow_frame, bg="#1e1e2e", fg="#cdd6f4")
        self.disallow_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        btn_frame_dis = ttk.Frame(disallow_frame)
        btn_frame_dis.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame_dis, text="Добавить программу", command=self.add_disallow).pack(side='left', padx=5)
        ttk.Button(btn_frame_dis, text="Удалить программу", command=self.remove_disallow).pack(side='left', padx=5)
        self.load_disallow()
        
        # Вкладка ScancodeMap
        scancode_frame = ttk.Frame(notebook2)
        notebook2.add(scancode_frame, text="ScancodeMap")
        self.scancode_text = scrolledtext.ScrolledText(scancode_frame, height=10, bg="#1e1e2e", fg="#cdd6f4")
        self.scancode_text.pack(fill='both', expand=True, padx=5, pady=5)
        ttk.Button(scancode_frame, text="Применить", command=self.apply_scancode).pack(pady=5)
        self.load_scancode()
        
        # Вкладка Debuggers (Image File Execution Options)
        debug_frame = ttk.Frame(notebook2)
        notebook2.add(debug_frame, text="Debuggers")
        self.debug_list = ttk.Treeview(debug_frame, columns=("Приложение", "Debugger"), show="headings")
        self.debug_list.heading("Приложение", text="Приложение")
        self.debug_list.heading("Debugger", text="Debugger")
        self.debug_list.column("Приложение", width=200)
        self.debug_list.column("Debugger", width=300)
        self.debug_list.pack(fill='both', expand=True, padx=5, pady=5)
        btn_frame_deb = ttk.Frame(debug_frame)
        btn_frame_deb.pack(fill='x')
        ttk.Button(btn_frame_deb, text="Удалить", command=self.remove_debugger).pack(side='left', padx=5)
        self.load_debuggers()
    
    def load_hosts(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            with open(hosts_path, 'r', encoding='utf-8') as f:
                self.hosts_text.delete(1.0, tk.END)
                self.hosts_text.insert(tk.END, f.read())
        except:
            self.hosts_text.insert(tk.END, "Не удалось прочитать файл hosts")
    
    def save_hosts(self):
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts"
        try:
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.write(self.hosts_text.get(1.0, tk.END))
            messagebox.showinfo("Успех", "Файл hosts сохранён")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def load_disallow(self):
        self.disallow_listbox.delete(0, tk.END)
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            try:
                disallow_key = winreg.OpenKey(key, "DisallowRun", 0, winreg.KEY_READ)
                i = 0
                while True:
                    name, value, _ = winreg.EnumValue(disallow_key, i)
                    self.disallow_listbox.insert(tk.END, f"{name} = {value}")
                    i += 1
            except:
                pass
            winreg.CloseKey(key)
        except:
            pass
    
    def add_disallow(self):
        prog = filedialog.askopenfilename(title="Выберите программу для запрета")
        if prog:
            name = os.path.basename(prog)
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun"
            reg_set_value(winreg.HKEY_CURRENT_USER, key_path, name, prog, winreg.REG_SZ)
            self.load_disallow()
    
    def remove_disallow(self):
        sel = self.disallow_listbox.curselection()
        if sel:
            entry = self.disallow_listbox.get(sel[0])
            name = entry.split(' = ')[0]
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer\DisallowRun"
            reg_delete_key(winreg.HKEY_CURRENT_USER, key_path, name)
            self.load_disallow()
    
    def load_scancode(self):
        key_path = r"SYSTEM\CurrentControlSet\Control\Keyboard Layout"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "Scancode Map")
            self.scancode_text.delete(1.0, tk.END)
            self.scancode_text.insert(tk.END, str(value))
            winreg.CloseKey(key)
        except:
            self.scancode_text.delete(1.0, tk.END)
            self.scancode_text.insert(tk.END, "Scancode Map не установлен")
    
    def apply_scancode(self):
        # Здесь нужно парсить ввод и записывать бинарные данные. Для простоты покажем сообщение.
        messagebox.showinfo("Инфо", "Для Scancode Map требуется ввод в виде hex-строки. Функция в разработке.")
    
    def load_debuggers(self):
        for row in self.debug_list.get_children():
            self.debug_list.delete(row)
        key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                    try:
                        debugger, _ = winreg.QueryValueEx(subkey, "Debugger")
                        self.debug_list.insert('', 'end', values=(subkey_name, debugger))
                    except:
                        pass
                    winreg.CloseKey(subkey)
                    i += 1
                except WindowsError:
                    break
            winreg.CloseKey(key)
        except:
            pass
    
    def remove_debugger(self):
        selected = self.debug_list.selection()
        if not selected:
            return
        app = self.debug_list.item(selected[0])['values'][0]
        key_path = rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\{app}"
        if reg_delete_key(winreg.HKEY_LOCAL_MACHINE, key_path):
            messagebox.showinfo("Удалено", f"Debugger для {app} удалён")
            self.load_debuggers()
        else:
            messagebox.showerror("Ошибка", "Не удалось удалить")
    
    # ------------------ Очистка системы ------------------
    def create_cleaner_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Очистка")
        
        self.cleaner_text = scrolledtext.ScrolledText(frame, bg="#1e1e2e", fg="#cdd6f4", height=15)
        self.cleaner_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Очистить систему", command=self.run_cleanup).pack(side='left', padx=5)
    
    def run_cleanup(self):
        self.cleaner_text.delete(1.0, tk.END)
        self.cleaner_text.insert(tk.END, "Начало очистки...\n")
        self.update_idletasks()
        
        # Очистка временных папок
        temp_folders = [os.environ.get('TEMP'), os.environ.get('TMP'), r"C:\Windows\Temp"]
        for folder in temp_folders:
            if folder and os.path.exists(folder):
                self.cleaner_text.insert(tk.END, f"Очистка {folder}...\n")
                for root, dirs, files in os.walk(folder, topdown=False):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
                    for dir in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, dir))
                        except:
                            pass
        
        # Корзина
        self.cleaner_text.insert(tk.END, "Очистка корзины...\n")
        try:
            # SHEmptyRecycleBin
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
        except:
            pass
        
        # Кэш браузеров (упрощённо)
        browsers = {
            "Chrome": os.path.join(os.getenv('LOCALAPPDATA'), r"Google\Chrome\User Data\Default\Cache"),
            "Firefox": os.path.join(os.getenv('APPDATA'), r"Mozilla\Firefox\Profiles"),
            "Edge": os.path.join(os.getenv('LOCALAPPDATA'), r"Microsoft\Edge\User Data\Default\Cache")
        }
        for name, path in browsers.items():
            if os.path.exists(path):
                self.cleaner_text.insert(tk.END, f"Очистка кэша {name}...\n")
                shutil.rmtree(path, ignore_errors=True)
        
        self.cleaner_text.insert(tk.END, "Очистка завершена.\n")
    
    # ------------------ Пользователи ------------------
    def create_users_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Пользователи")
        
        self.user_list = tk.Listbox(frame, bg="#1e1e2e", fg="#cdd6f4")
        self.user_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_users).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Создать пользователя", command=self.create_user).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Удалить пользователя", command=self.delete_user).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Сбросить пароль на 1", command=self.reset_password).pack(side='left', padx=5)
        
        self.load_users()
    
    def load_users(self):
        self.user_list.delete(0, tk.END)
        output = run_cmd("net user", capture=True)
        lines = output.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('--'):
                parts = line.split()
                for p in parts:
                    self.user_list.insert(tk.END, p)
    
    def create_user(self):
        name = tk.simpledialog.askstring("Создание", "Введите имя пользователя:")
        if name:
            run_cmd(f"net user {name} /add", capture=False)
            self.load_users()
    
    def delete_user(self):
        sel = self.user_list.curselection()
        if sel:
            name = self.user_list.get(sel[0])
            if messagebox.askyesno("Удаление", f"Удалить пользователя {name}?"):
                run_cmd(f"net user {name} /del", capture=False)
                self.load_users()
    
    def reset_password(self):
        sel = self.user_list.curselection()
        if sel:
            name = self.user_list.get(sel[0])
            run_cmd(f"net user {name} 1", capture=False)
            messagebox.showinfo("Пароль", f"Пароль пользователя {name} изменён на '1'")
    
    # ------------------ Ассоциации файлов ------------------
    def create_associations_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Ассоциации")
        
        extensions = [".exe", ".bat", ".txt", ".lnk", ".html"]
        self.assoc_list = ttk.Treeview(frame, columns=("Расширение", "Текущая ассоциация"), show="headings")
        self.assoc_list.heading("Расширение", text="Расширение")
        self.assoc_list.heading("Текущая ассоциация", text="Текущая ассоциация")
        self.assoc_list.pack(fill='both', expand=True, padx=5, pady=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="Обновить", command=self.load_associations).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Восстановить по умолчанию", command=self.restore_association).pack(side='left', padx=5)
        
        self.load_associations()
    
    def load_associations(self):
        for row in self.assoc_list.get_children():
            self.assoc_list.delete(row)
        extensions = [".exe", ".bat", ".txt", ".lnk", ".html"]
        for ext in extensions:
            try:
                # Получаем ProgID
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext, 0, winreg.KEY_READ)
                progid, _ = winreg.QueryValueEx(key, "")
                self.assoc_list.insert('', 'end', values=(ext, progid))
                winreg.CloseKey(key)
            except:
                self.assoc_list.insert('', 'end', values=(ext, "Не найдено"))
    
    def restore_association(self):
        selected = self.assoc_list.selection()
        if not selected:
            return
        ext = self.assoc_list.item(selected[0])['values'][0]
        # Просто удаляем ключ, Windows восстановит ассоциацию по умолчанию
        try:
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, ext)
            messagebox.showinfo("Восстановлено", f"Ассоциация для {ext} сброшена")
        except:
            messagebox.showerror("Ошибка", "Не удалось удалить ключ")
        self.load_associations()
    
    # ------------------ Дополнительные возможности ------------------
    def create_advanced_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Дополнительно")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Перезагрузка ПК", command=lambda: run_cmd("shutdown /r /t 5", capture=False)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Выход из пользователя", command=lambda: run_cmd("shutdown /l", capture=False)).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Вход в WinRE", command=self.boot_winre).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Проверка целостности (sfc)", command=self.run_sfc).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Восстановление экрана входа", command=self.restore_login_screen).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Откл. драйверы без подписи", command=self.disable_driver_signing).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Управление дисками", command=self.manage_disks).pack(side='left', padx=5)
    
    def boot_winre(self):
        run_cmd("shutdown /r /o /t 5", capture=False)
    
    def run_sfc(self):
        # Запускаем в новом окне
        subprocess.Popen("cmd /c sfc /scannow", shell=True)
    
    def restore_login_screen(self):
        # Восстановление экрана входа через реестр
        reg_set_value(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon", "AutoAdminLogon", 0, winreg.REG_DWORD)
        messagebox.showinfo("Готово", "Экран входа будет показываться")
    
    def disable_driver_signing(self):
        # Включить тестовый режим для отключения проверки подписей
        run_cmd("bcdedit /set testsigning on", capture=False)
        messagebox.showinfo("Инфо", "Включён тестовый режим. Перезагрузите ПК для применения.")
    
    def manage_disks(self):
        # Просто открываем diskpart
        subprocess.Popen("diskpart", shell=True)

if __name__ == "__main__":
    app = SystemCommander()
    app.mainloop()