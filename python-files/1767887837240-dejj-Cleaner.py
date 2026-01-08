import os
import sys
import ctypes
import shutil
import winreg
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, sys.argv[0], None, 1)
        sys.exit()

class AppRemover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Удаление программ с диска C")
        self.root.geometry("800x600")
        self.root.configure(bg="#2b2b2b")
        
        self.found_items = []
        self.is_searching = False
        
        self.create_widgets()
    
    def create_widgets(self):
        # Заголовок
        title = tk.Label(
            self.root, 
            text="🗑️ Удаление программ с диска C", 
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="white"
        )
        title.pack(pady=15)
        
        # Статус
        admin = "✓ Администратор" if is_admin() else "✗ Нет прав"
        color = "#4CAF50" if is_admin() else "#f44336"
        status = tk.Label(self.root, text=admin, bg="#2b2b2b", fg=color, font=("Arial", 10))
        status.pack()
        
        # Поиск
        search_frame = tk.Frame(self.root, bg="#2b2b2b")
        search_frame.pack(pady=15, fill=tk.X, padx=20)
        
        tk.Label(
            search_frame, 
            text="Название программы:", 
            bg="#2b2b2b", 
            fg="white",
            font=("Arial", 11)
        ).pack(side=tk.LEFT)
        
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_frame, 
            textvariable=self.search_var,
            width=30, 
            font=("Arial", 12)
        )
        self.search_entry.pack(side=tk.LEFT, padx=10, ipady=5)
        self.search_entry.bind('<Return>', lambda e: self.start_search())
        
        self.search_btn = tk.Button(
            search_frame, 
            text="🔍 Найти", 
            command=self.start_search,
            font=("Arial", 11),
            bg="#2196F3",
            fg="white",
            padx=15,
            pady=5
        )
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = tk.Button(
            search_frame, 
            text="🗑️ Удалить всё", 
            command=self.delete_all,
            font=("Arial", 11),
            bg="#f44336",
            fg="white",
            padx=15,
            pady=5
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        # Прогресс
        self.progress_var = tk.StringVar(value="Готов к работе")
        progress_label = tk.Label(
            self.root, 
            textvariable=self.progress_var,
            bg="#2b2b2b",
            fg="#888",
            font=("Arial", 10)
        )
        progress_label.pack()
        
        # Список найденного
        list_frame = tk.Frame(self.root, bg="#2b2b2b")
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        # Treeview
        columns = ("Путь", "Тип", "Размер")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        self.tree.heading("Путь", text="Путь")
        self.tree.heading("Тип", text="Тип")
        self.tree.heading("Размер", text="Размер")
        
        self.tree.column("Путь", width=500)
        self.tree.column("Тип", width=80)
        self.tree.column("Размер", width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Лог
        log_frame = tk.LabelFrame(self.root, text="Лог", bg="#2b2b2b", fg="white")
        log_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00"
        )
        self.log_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Счетчик
        self.count_var = tk.StringVar(value="Найдено: 0")
        count_label = tk.Label(
            self.root,
            textvariable=self.count_var,
            bg="#2b2b2b",
            fg="white",
            font=("Arial", 11, "bold")
        )
        count_label.pack(pady=5)
    
    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update()
    
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
    
    def start_search(self):
        pattern = self.search_var.get().strip()
        
        if not pattern:
            messagebox.showwarning("Внимание", "Введите название программы")
            return
        
        if len(pattern) < 2:
            messagebox.showwarning("Внимание", "Минимум 2 символа")
            return
        
        if self.is_searching:
            return
        
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.found_items = []
        self.is_searching = True
        self.search_btn.config(state=tk.DISABLED)
        
        # Запускаем поиск в отдельном потоке
        thread = threading.Thread(target=self.search_disk, args=(pattern,))
        thread.daemon = True
        thread.start()
    
    def search_disk(self, pattern):
        pattern_lower = pattern.lower()
        
        self.log(f"\n=== Поиск: '{pattern}' ===")
        self.progress_var.set(f"Поиск '{pattern}'...")
        
        # Папки для поиска
        search_paths = [
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\ProgramData",
            os.environ.get('APPDATA', ''),
            os.environ.get('LOCALAPPDATA', ''),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Downloads'),
            os.path.join(os.environ.get('USERPROFILE', ''), 'Documents'),
            os.environ.get('TEMP', ''),
            os.path.join(os.environ.get('WINDIR', ''), 'Prefetch'),
        ]
        
        # Поиск файлов и папок
        for base_path in search_paths:
            if not base_path or not os.path.exists(base_path):
                continue
            
            self.progress_var.set(f"Сканирую: {base_path}")
            self.log(f"Сканирую: {base_path}")
            
            try:
                # Первый уровень
                for item in os.listdir(base_path):
                    if pattern_lower in item.lower():
                        full_path = os.path.join(base_path, item)
                        self.add_found_item(full_path)
                
                # Глубокий поиск в некоторых папках
                if 'AppData' in base_path or 'ProgramData' in base_path:
                    for root, dirs, files in os.walk(base_path):
                        # Ограничиваем глубину
                        depth = root.replace(base_path, '').count(os.sep)
                        if depth > 2:
                            continue
                        
                        for d in dirs:
                            if pattern_lower in d.lower():
                                self.add_found_item(os.path.join(root, d))
                        
                        for f in files:
                            if pattern_lower in f.lower():
                                self.add_found_item(os.path.join(root, f))
            except PermissionError:
                pass
            except Exception as e:
                pass
        
        # Поиск в реестре
        self.progress_var.set("Поиск в реестре...")
        self.log("Поиск в реестре...")
        self.search_registry(pattern_lower)
        
        # Готово
        self.progress_var.set(f"Готово. Найдено: {len(self.found_items)}")
        self.count_var.set(f"Найдено: {len(self.found_items)}")
        self.log(f"\n=== Найдено: {len(self.found_items)} ===")
        
        self.is_searching = False
        self.search_btn.config(state=tk.NORMAL)
    
    def add_found_item(self, path):
        if path in [item['path'] for item in self.found_items]:
            return
        
        try:
            if os.path.isfile(path):
                size = os.path.getsize(path)
                item_type = "Файл"
            else:
                size = self.get_folder_size(path)
                item_type = "Папка"
            
            size_str = self.format_size(size)
            
            self.found_items.append({
                'path': path,
                'type': item_type,
                'size': size
            })
            
            self.tree.insert("", tk.END, values=(path, item_type, size_str))
            self.count_var.set(f"Найдено: {len(self.found_items)}")
            self.root.update()
        except:
            pass
    
    def search_registry(self, pattern):
        # Ключи для поиска
        reg_locations = [
            (winreg.HKEY_CURRENT_USER, r"Software"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        
        for hkey, base_path in reg_locations:
            try:
                key = winreg.OpenKey(hkey, base_path, 0, winreg.KEY_READ)
                
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        
                        if pattern in subkey_name.lower():
                            hkey_name = "HKCU" if hkey == winreg.HKEY_CURRENT_USER else "HKLM"
                            full_path = f"{hkey_name}\\{base_path}\\{subkey_name}"
                            
                            self.found_items.append({
                                'path': full_path,
                                'type': 'Реестр',
                                'size': 0,
                                'hkey': hkey,
                                'reg_path': f"{base_path}\\{subkey_name}"
                            })
                            
                            self.tree.insert("", tk.END, values=(full_path, "Реестр", "-"))
                            self.count_var.set(f"Найдено: {len(self.found_items)}")
                        
                        i += 1
                    except OSError:
                        break
                
                winreg.CloseKey(key)
            except:
                pass
    
    def delete_all(self):
        if not self.found_items:
            messagebox.showwarning("Внимание", "Сначала выполните поиск")
            return
        
        count = len(self.found_items)
        
        if not messagebox.askyesno(
            "Подтверждение", 
            f"Удалить {count} найденных элементов?\n\nЭто действие необратимо!"
        ):
            return
        
        self.log(f"\n=== Удаление {count} элементов ===")
        self.progress_var.set("Удаление...")
        
        deleted = 0
        errors = 0
        
        for item in self.found_items:
            path = item['path']
            item_type = item['type']
            
            try:
                if item_type == "Реестр":
                    # Удаление из реестра
                    hkey_name = "HKCU" if "HKCU" in path else "HKLM"
                    reg_path = item.get('reg_path', '')
                    
                    if reg_path:
                        cmd = f'reg delete "{hkey_name}\\{reg_path}" /f'
                        result = os.system(f'{cmd} >nul 2>&1')
                        
                        if result == 0:
                            self.log(f"[OK] Реестр: {path}")
                            deleted += 1
                        else:
                            self.log(f"[X] Реестр: {path}")
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
                            # Принудительное удаление
                            os.system(f'rd /s /q "{path}" >nul 2>&1')
                            if not os.path.exists(path):
                                self.log(f"[OK] Папка (force): {path}")
                                deleted += 1
                            else:
                                self.log(f"[X] Папка: {path}")
                                errors += 1
            
            except PermissionError:
                self.log(f"[X] Нет доступа: {path}")
                errors += 1
            except Exception as e:
                self.log(f"[X] Ошибка: {path} - {e}")
                errors += 1
        
        # Очищаем связанные данные
        self.clean_related()
        
        # Очищаем список
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.found_items = []
        
        self.progress_var.set(f"Удалено: {deleted}, Ошибок: {errors}")
        self.count_var.set("Найдено: 0")
        
        self.log(f"\n=== Удалено: {deleted}, Ошибок: {errors} ===")
        messagebox.showinfo("Готово", f"Удалено: {deleted}\nОшибок: {errors}")
    
    def clean_related(self):
        """Очистка связанных данных"""
        self.log("\nОчистка связанных данных...")
        
        # ShellBag
        keys = [
            r"HKCU\Software\Microsoft\Windows\Shell\BagMRU",
            r"HKCU\Software\Microsoft\Windows\Shell\Bags",
        ]
        for key in keys:
            os.system(f'reg delete "{key}" /f >nul 2>&1')
        
        # UserAssist
        try:
            ua_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ua_path, 0, winreg.KEY_READ)
            
            i = 0
            guids = []
            while True:
                try:
                    guids.append(winreg.EnumKey(key, i))
                    i += 1
                except:
                    break
            winreg.CloseKey(key)
            
            for guid in guids:
                count_path = f"{ua_path}\\{guid}\\Count"
                try:
                    ck = winreg.OpenKey(winreg.HKEY_CURRENT_USER, count_path, 0, winreg.KEY_ALL_ACCESS)
                    
                    pattern = self.search_var.get().strip().lower()
                    
                    vals_to_delete = []
                    j = 0
                    while True:
                        try:
                            name = winreg.EnumValue(ck, j)[0]
                            
                            # ROT13
                            decoded = ""
                            for c in name:
                                if 'a' <= c <= 'z':
                                    decoded += chr((ord(c) - ord('a') + 13) % 26 + ord('a'))
                                elif 'A' <= c <= 'Z':
                                    decoded += chr((ord(c) - ord('A') + 13) % 26 + ord('A'))
                                else:
                                    decoded += c
                            
                            if pattern in decoded.lower():
                                vals_to_delete.append(name)
                            
                            j += 1
                        except:
                            break
                    
                    for name in vals_to_delete:
                        try:
                            winreg.DeleteValue(ck, name)
                        except:
                            pass
                    
                    winreg.CloseKey(ck)
                except:
                    pass
        except:
            pass
        
        # Prefetch
        pattern = self.search_var.get().strip().lower()
        prefetch = os.path.join(os.environ.get('WINDIR', ''), 'Prefetch')
        
        if os.path.exists(prefetch):
            for f in os.listdir(prefetch):
                if pattern in f.lower() and f.endswith('.pf'):
                    try:
                        os.remove(os.path.join(prefetch, f))
                        self.log(f"[OK] Prefetch: {f}")
                    except:
                        pass
        
        # Recent
        recent = os.path.join(os.environ.get('APPDATA', ''), 'Microsoft', 'Windows', 'Recent')
        if os.path.exists(recent):
            for f in os.listdir(recent):
                if pattern in f.lower():
                    try:
                        os.remove(os.path.join(recent, f))
                        self.log(f"[OK] Recent: {f}")
                    except:
                        pass
        
        self.log("Связанные данные очищены")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    run_as_admin()
    
    try:
        app = AppRemover()
        app.run()
    except Exception as e:
        print(f"Ошибка: {e}")
        input("Enter...")