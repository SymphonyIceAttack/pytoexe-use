import os
import shutil
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import platform
import hashlib
import json
import webbrowser
import sys
import subprocess
import queue

# ====================================================================================
#                    ONE VALVE CLEANER - СТАБИЛЬНАЯ ВЕРСИЯ
#                             WWW.ONEVALVE.RU
#                          ТОЛЬКО НУЖНЫЕ ФУНКЦИИ
# ====================================================================================

class OneValveCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("ONE VALVE CLEANER")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        
        # Settings file
        self.settings_file = os.path.join(os.path.expanduser('~'), '.onevalve_settings.json')
        self.load_settings()
        
        # Current theme
        self.current_theme = self.settings.get('theme', 'steam_dark')
        
        # Apply theme
        self.apply_theme()
        self.root.configure(bg=self.colors['bg_main'])
        
        # Queue for async operations
        self.task_queue = queue.Queue()
        
        # Setup UI
        self.setup_ui()
        
        # Update system info
        self.update_time()
        self.update_disk_info()
        self.process_queue()
        
        # Log startup
        self.log("=" * 80, "info")
        self.log(" ONE VALVE CLEANER - СТАБИЛЬНАЯ ВЕРСИЯ", "accent")
        self.log(" " + datetime.now().strftime('%d.%m.%Y %H:%M:%S'), "info")
        self.log(" " + platform.system() + " " + platform.release() + " | " + os.getlogin(), "info")
        self.log("=" * 80, "info")
        
    def apply_theme(self):
        """Apply selected theme"""
        themes = {
            'steam_dark': {
                'name': 'Steam Dark',
                'bg_main': '#171a21', 'bg_secondary': '#1b1f2b', 'bg_tertiary': '#2a2e3d',
                'bg_input': '#0e1117', 'accent': '#2a475e', 'success': '#4c9c2e',
                'warning': '#d2a038', 'danger': '#a34c4c', 'text_primary': '#e6e6e6',
                'text_secondary': '#8f98a0', 'text_muted': '#5c666f',
                'log_bg': '#0e1117', 'log_fg': '#98fb98',
                'nav_button_bg': '#1b1f2b', 'nav_button_fg': '#8f98a0', 'nav_button_active': '#4c9c2e'
            },
            'github_black': {
                'name': 'GitHub Black',
                'bg_main': '#0d1117', 'bg_secondary': '#161b22', 'bg_tertiary': '#21262d',
                'bg_input': '#0d1117', 'accent': '#238636', 'success': '#2ea043',
                'warning': '#d29922', 'danger': '#f85149', 'text_primary': '#c9d1d9',
                'text_secondary': '#8b949e', 'text_muted': '#6e7681',
                'log_bg': '#0d1117', 'log_fg': '#58a6ff',
                'nav_button_bg': '#21262d', 'nav_button_fg': '#c9d1d9', 'nav_button_active': '#2ea043'
            },
            'arctic_white': {
                'name': 'Arctic White',
                'bg_main': '#e8edf2', 'bg_secondary': '#f0f4f8', 'bg_tertiary': '#ffffff',
                'bg_input': '#e8edf2', 'accent': '#2980b9', 'success': '#27ae60',
                'warning': '#e67e22', 'danger': '#e74c3c', 'text_primary': '#2c3e50',
                'text_secondary': '#7f8c8d', 'text_muted': '#bdc3c7',
                'log_bg': '#f0f4f8', 'log_fg': '#2c3e50',
                'nav_button_bg': '#ffffff', 'nav_button_fg': '#7f8c8d', 'nav_button_active': '#2980b9'
            }
        }
        self.colors = themes.get(self.current_theme, themes['steam_dark'])
    
    # ==================== УДАЛЕНИЕ ПРОГРАММ ====================
    
    def get_installed_apps(self):
        """Получение списка установленных приложений"""
        apps = []
        try:
            # Получаем список через WMIC
            result = subprocess.run('wmic product get name', shell=True, capture_output=True, text=True, timeout=30)
            lines = result.stdout.split('\n')
            for line in lines[1:]:  # Пропускаем заголовок
                name = line.strip()
                if name and len(name) > 2 and not name.startswith('Microsoft'):
                    apps.append({'name': name, 'type': 'win32'})
        except:
            pass
        
        # Получаем UWP приложения через PowerShell
        try:
            ps_script = 'Get-AppxPackage | Select-Object -ExpandProperty Name'
            result = subprocess.run(f'powershell -Command "{ps_script}"', shell=True, capture_output=True, text=True, timeout=30)
            for line in result.stdout.split('\n'):
                name = line.strip()
                if name and len(name) > 2:
                    apps.append({'name': name, 'type': 'uwp'})
        except:
            pass
        
        # Убираем дубликаты
        unique_apps = []
        seen_names = set()
        for app in apps:
            if app['name'] not in seen_names:
                seen_names.add(app['name'])
                unique_apps.append(app)
        
        return unique_apps[:100]  # Ограничиваем список
    
    def uninstall_app(self, app_name, app_type):
        """Удаление приложения"""
        try:
            if app_type == 'uwp':
                cmd = f'powershell -Command "Get-AppxPackage *{app_name}* | Remove-AppxPackage"'
            else:
                cmd = f'wmic product where name="{app_name}" call uninstall /nointeractive'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return result.returncode == 0 or 'success' in result.stdout.lower()
        except:
            return False
    
    def uninstall_builtin_app(self, app_id):
        """Удаление встроенного приложения Windows"""
        try:
            cmd = f'powershell -Command "Get-AppxPackage *{app_id}* | Remove-AppxPackage"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def show_uninstall_apps(self):
        """Показать список установленных программ"""
        def task():
            self.log("=" * 80, "info")
            self.log(" УПРАВЛЕНИЕ ПРОГРАММАМИ", "accent")
            self.log(" Загрузка списка программ...", "info")
            
            apps = self.get_installed_apps()
            
            if not apps:
                self.log(" Не удалось загрузить список программ", "error")
                messagebox.showerror("Ошибка", "Не удалось загрузить список программ")
                return
            
            # Создаём диалог выбора
            dialog = tk.Toplevel(self.root)
            dialog.title("Управление программами - ONE VALVE")
            dialog.geometry("650x550")
            dialog.configure(bg=self.colors['bg_secondary'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Заголовок
            header = tk.Frame(dialog, bg=self.colors['bg_tertiary'], height=45)
            header.pack(fill=tk.X)
            tk.Label(header, text=" УСТАНОВЛЕННЫЕ ПРОГРАММЫ", font=('Segoe UI', 12, 'bold'),
                    fg=self.colors['text_primary'], bg=self.colors['bg_tertiary']).pack(side=tk.LEFT, padx=15, pady=10)
            
            # Список программ
            listbox_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            # Создаём Canvas для скроллинга
            canvas = tk.Canvas(listbox_frame, bg=self.colors['bg_secondary'], highlightthickness=0)
            scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])
            
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=580)
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Кнопки для каждого приложения
            buttons = []
            for i, app in enumerate(apps):
                type_icon = "📦" if app['type'] == 'uwp' else "💿"
                btn_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_secondary'], height=40)
                btn_frame.pack(fill=tk.X, pady=2, padx=5)
                btn_frame.pack_propagate(False)
                
                # Иконка и название
                icon_label = tk.Label(btn_frame, text=type_icon, font=('Segoe UI', 14),
                                     bg=self.colors['bg_secondary'], fg=self.colors['success'])
                icon_label.pack(side=tk.LEFT, padx=10)
                
                name_label = tk.Label(btn_frame, text=app['name'], font=('Segoe UI', 10),
                                     bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], anchor=tk.W)
                name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
                
                # Кнопка удаления
                def make_uninstall_func(n=app['name'], t=app['type']):
                    return lambda: self.confirm_uninstall(n, t, dialog)
                
                uninstall_btn = tk.Button(btn_frame, text="УДАЛИТЬ", command=make_uninstall_func(),
                                         font=('Segoe UI', 8, 'bold'), bg=self.colors['danger'], fg='white',
                                         cursor='hand2', borderwidth=0, padx=10)
                uninstall_btn.pack(side=tk.RIGHT, padx=10)
                buttons.append(uninstall_btn)
            
            # Информационная панель
            info_frame = tk.Frame(dialog, bg=self.colors['bg_tertiary'], height=40)
            info_frame.pack(fill=tk.X, side=tk.BOTTOM)
            
            tk.Label(info_frame, text="⚠️ ВНИМАНИЕ: Удаление некоторых программ может повлиять на работу системы!",
                    font=('Segoe UI', 9), fg=self.colors['warning'], bg=self.colors['bg_tertiary']).pack(pady=10)
            
            # Кнопка для встроенных приложений
            builtin_btn = tk.Button(info_frame, text="🗑️ Удалить встроенные приложения Windows", 
                                   command=self.show_builtin_apps,
                                   font=('Segoe UI', 9, 'bold'), bg=self.colors['accent'], fg='white',
                                   cursor='hand2', borderwidth=0, padx=15, pady=5)
            builtin_btn.pack(side=tk.RIGHT, padx=15)
            
            self.log(" Загружено программ: " + str(len(apps)), "info")
        
        self.run_task(task)
    
    def confirm_uninstall(self, app_name, app_type, dialog):
        """Подтверждение удаления программы"""
        if messagebox.askyesno("Подтверждение", 
                               f"Вы действительно хотите удалить:\n\n{app_name}\n\nЭто действие может быть необратимым!"):
            
            def uninstall_task():
                self.log(" Удаление: " + app_name, "warning")
                success = self.uninstall_app(app_name, app_type)
                
                if success:
                    self.log(" Программа удалена: " + app_name, "success")
                    messagebox.showinfo("Успех", f"Программа '{app_name}' успешно удалена!")
                    dialog.destroy()
                else:
                    self.log(" Ошибка удаления: " + app_name, "error")
                    messagebox.showerror("Ошибка", f"Не удалось удалить '{app_name}'\nВозможно, требуются права администратора.")
            
            self.run_task(uninstall_task)
    
    def show_builtin_apps(self):
        """Показать список встроенных приложений Windows"""
        builtin_apps = [
            ("3D Builder", "Microsoft.3DBuilder"),
            ("Калькулятор", "Microsoft.WindowsCalculator"),
            ("Календарь и Почта", "microsoft.windowscommunicationsapps"),
            ("Камера", "Microsoft.WindowsCamera"),
            ("Cortana", "Microsoft.549981C3F5F10"),
            ("Films & TV", "Microsoft.ZuneVideo"),
            ("Get Help", "Microsoft.GetHelp"),
            ("Groove Music", "Microsoft.ZuneMusic"),
            ("Карты", "Microsoft.WindowsMaps"),
            ("Microsoft News", "Microsoft.BingNews"),
            ("Microsoft Solitaire Collection", "Microsoft.MicrosoftSolitaireCollection"),
            ("OneNote", "Microsoft.Office.OneNote"),
            ("Paint 3D", "Microsoft.MSPaint"),
            ("People", "Microsoft.People"),
            ("Skype", "Microsoft.SkypeApp"),
            ("Snip & Sketch", "Microsoft.ScreenSketch"),
            ("Spotify", "SpotifyAB.SpotifyMusic"),
            ("Microsoft Teams", "Microsoft.Teams"),
            ("To Do", "Microsoft.Todos"),
            ("Voice Recorder", "Microsoft.WindowsSoundRecorder"),
            ("Weather", "Microsoft.BingWeather"),
            ("Xbox Console Companion", "Microsoft.XboxApp"),
            ("Xbox Game Bar", "Microsoft.XboxGamingOverlay"),
            ("Your Phone", "Microsoft.YourPhone"),
        ]
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Встроенные приложения Windows")
        dialog.geometry("550x500")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        header = tk.Frame(dialog, bg=self.colors['bg_tertiary'], height=45)
        header.pack(fill=tk.X)
        tk.Label(header, text=" ВСТРОЕННЫЕ ПРИЛОЖЕНИЯ WINDOWS", font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_tertiary']).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Список
        listbox_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(listbox_frame, bg=self.colors['bg_secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=490)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        for name, app_id in builtin_apps:
            btn_frame = tk.Frame(scrollable_frame, bg=self.colors['bg_secondary'], height=40)
            btn_frame.pack(fill=tk.X, pady=2, padx=5)
            btn_frame.pack_propagate(False)
            
            icon_label = tk.Label(btn_frame, text="⚠️", font=('Segoe UI', 12),
                                 bg=self.colors['bg_secondary'], fg=self.colors['warning'])
            icon_label.pack(side=tk.LEFT, padx=10)
            
            name_label = tk.Label(btn_frame, text=name, font=('Segoe UI', 10),
                                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'], anchor=tk.W)
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            def make_uninstall_func(app_id=app_id, app_name=name, d=dialog):
                return lambda: self.confirm_builtin_uninstall(app_name, app_id, d)
            
            uninstall_btn = tk.Button(btn_frame, text="УДАЛИТЬ", command=make_uninstall_func(),
                                     font=('Segoe UI', 8, 'bold'), bg=self.colors['danger'], fg='white',
                                     cursor='hand2', borderwidth=0, padx=10)
            uninstall_btn.pack(side=tk.RIGHT, padx=10)
        
        info_frame = tk.Frame(dialog, bg=self.colors['bg_tertiary'], height=40)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        tk.Label(info_frame, text="⚠️ Удаление некоторых приложений может повлиять на работу системы!",
                font=('Segoe UI', 9), fg=self.colors['warning'], bg=self.colors['bg_tertiary']).pack(pady=10)
    
    def confirm_builtin_uninstall(self, app_name, app_id, dialog):
        """Подтверждение удаления встроенного приложения"""
        if messagebox.askyesno("Подтверждение", 
                               f"⚠️ ВНИМАНИЕ!\n\nВы собираетесь удалить:\n{app_name}\n\nЭто действие может повлиять на работу Windows.\n\nПродолжить?"):
            
            def uninstall_task():
                self.log(" Удаление встроенного приложения: " + app_name, "warning")
                success = self.uninstall_builtin_app(app_id)
                
                if success:
                    self.log(" Приложение удалено: " + app_name, "success")
                    messagebox.showinfo("Успех", f"Приложение '{app_name}' успешно удалено!")
                    dialog.destroy()
                else:
                    self.log(" Ошибка удаления: " + app_name, "error")
                    messagebox.showerror("Ошибка", f"Не удалось удалить '{app_name}'\nВозможно, оно уже удалено.")
            
            self.run_task(uninstall_task)
    
    # ==================== ОСТАЛЬНЫЕ ФУНКЦИИ ====================
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size < 1024.0:
                return "{:.2f} {}".format(size, unit)
            size /= 1024.0
        return "{:.2f} ТБ".format(size)
    
    def clean_temp_files(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ", "accent")
            temp_folders = [os.environ.get('TEMP', ''), os.environ.get('TMP', ''),
                           os.path.expanduser('~\\AppData\\Local\\Temp'), 'C:\\Windows\\Temp']
            extensions = ['.tmp', '.log', '.cache', '.temp', '.old', '.bak']
            deleted_count, deleted_size = 0, 0
            all_files = []
            for folder in temp_folders:
                if folder and os.path.exists(folder):
                    self.log(" Сканирование: " + folder, "info")
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in extensions):
                                all_files.append(os.path.join(root, file))
            if all_files:
                self.log(" Найдено файлов: " + str(len(all_files)), "info")
                for i, file_path in enumerate(all_files):
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        deleted_size += file_size
                        self.update_progress((i + 1) * 100 // len(all_files), "Удаление... " + str(deleted_count) + "/" + str(len(all_files)))
                    except:
                        pass
                self.log(" Удалено файлов: " + str(deleted_count), "success")
                self.log(" Освобождено: " + self.format_size(deleted_size), "success")
            else:
                self.log(" Временные файлы не найдены", "success")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def clean_downloads(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" ОЧИСТКА ПАПКИ ЗАГРУЗОК", "accent")
            downloads = os.path.expanduser('~\\Downloads')
            extensions = ['.exe', '.msi', '.tmp', '.crdownload', '.part', '.dmg']
            if os.path.exists(downloads):
                files = [f for f in os.listdir(downloads) if any(f.lower().endswith(ext) for ext in extensions)]
                if files:
                    self.log(" Найдено файлов: " + str(len(files)), "info")
                    total_size = 0
                    for i, file in enumerate(files):
                        try:
                            path = os.path.join(downloads, file)
                            size = os.path.getsize(path)
                            os.remove(path)
                            total_size += size
                            self.update_progress((i + 1) * 100 // len(files), "Удаление... " + str(i+1) + "/" + str(len(files)))
                        except:
                            pass
                    self.log(" Удалено файлов: " + str(len(files)), "success")
                    self.log(" Освобождено: " + self.format_size(total_size), "success")
                else:
                    self.log(" Папка загрузок чиста", "success")
            else:
                self.log(" Папка загрузок не найдена", "error")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def clean_duplicates(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" УДАЛЕНИЕ ДУБЛИКАТОВ", "accent")
            folder = os.path.expanduser('~\\Desktop')
            self.log(" Сканирование: " + folder, "info")
            hashes = {}
            duplicates = []
            for file in os.listdir(folder):
                path = os.path.join(folder, file)
                if os.path.isfile(path):
                    try:
                        with open(path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        if file_hash in hashes:
                            duplicates.append(path)
                            self.log(" Найден дубликат: " + file, "warning")
                        else:
                            hashes[file_hash] = path
                    except:
                        pass
            if duplicates:
                for dup in duplicates:
                    try:
                        os.remove(dup)
                    except:
                        pass
                self.log(" Удалено дубликатов: " + str(len(duplicates)), "success")
            else:
                self.log(" Дубликатов не найдено", "success")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def clean_old_files(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" ОЧИСТКА СТАРЫХ ФАЙЛОВ", "accent")
            days, folder = 30, os.path.expanduser('~\\Downloads')
            now, deleted, total_size = time.time(), 0, 0
            self.log(" Сканирование: " + folder, "info")
            for file in os.listdir(folder):
                path = os.path.join(folder, file)
                if os.path.isfile(path):
                    try:
                        file_time = os.path.getmtime(path)
                        age = (now - file_time) / (24 * 3600)
                        if age > days:
                            size = os.path.getsize(path)
                            os.remove(path)
                            deleted += 1
                            total_size += size
                    except:
                        pass
            self.log(" Удалено файлов: " + str(deleted), "success")
            self.log(" Освобождено: " + self.format_size(total_size), "success")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def clean_recycle_bin(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" ОЧИСТКА КОРЗИНЫ", "accent")
            try:
                import ctypes
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
                self.log(" Корзина очищена", "success")
            except Exception as e:
                self.log(" Ошибка: " + str(e), "error")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def clean_browser_cache(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" ОЧИСТКА КЭША БРАУЗЕРОВ", "accent")
            browsers = [("Chrome", os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache')),
                       ("Edge", os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache'))]
            for name, path in browsers:
                if os.path.exists(path):
                    try:
                        size = 0
                        for dirpath, dirnames, filenames in os.walk(path):
                            for f in filenames:
                                try:
                                    size += os.path.getsize(os.path.join(dirpath, f))
                                except:
                                    pass
                        shutil.rmtree(path, ignore_errors=True)
                        self.log("   " + name + ": очищено " + self.format_size(size), "success")
                    except:
                        self.log("   " + name + ": ошибка", "error")
                else:
                    self.log("   " + name + ": кэш не найден", "info")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def show_disk_stats(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" СТАТИСТИКА ДИСКОВ", "accent")
            for drive in range(65, 91):
                letter = chr(drive) + ":\\"
                if os.path.exists(letter):
                    try:
                        total, used, free = shutil.disk_usage(letter)
                        percent = (used / total) * 100
                        self.log(" ДИСК " + letter, "info")
                        self.log("    Всего: " + self.format_size(total), "info")
                        self.log("    Занято: " + self.format_size(used) + " (" + str(round(percent, 1)) + "%)", "warning" if percent > 70 else "success")
                        self.log("    Свободно: " + self.format_size(free), "success")
                    except:
                        pass
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def analyze_disk(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" АНАЛИЗАТОР ДИСКА", "accent")
            drive = "C:\\"
            self.log(" Сканирование диска " + drive + "...", "info")
            folders = []
            try:
                for entry in os.scandir(drive):
                    if entry.is_dir():
                        size = self.get_folder_size(entry.path)
                        folders.append((entry.name, size))
            except:
                pass
            folders.sort(key=lambda x: x[1], reverse=True)
            self.log(" ТОП-10 САМЫХ БОЛЬШИХ ПАПОК:", "accent")
            for i, (name, size) in enumerate(folders[:10], 1):
                if size > 0:
                    self.log(" " + str(i) + ". " + name + " - " + self.format_size(size), "warning" if i <= 3 else "info")
            self.log("=" * 80, "info")
        self.run_task(task)
    
    def get_folder_size(self, path):
        total = 0
        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_folder_size(entry.path)
        except:
            pass
        return total
    
    # ==================== ПЛАНИРОВЩИК ОЧИСТКИ ====================
    
    def schedule_cleanup(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" ПЛАНИРОВЩИК ОЧИСТКИ", "accent")
            
            schedule_type = self.schedule_var.get()
            
            if schedule_type == "never":
                self.log(" Планировщик отключён", "info")
                self.update_setting('schedule', 'never')
                messagebox.showinfo("Планировщик", "Автоматическая очистка отключена")
                return
            
            try:
                script_path = os.path.abspath(__file__)
                python_path = sys.executable
                
                task_name = "ONEVALVE_Cleaner"
                
                # Удаляем старую задачу
                subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, capture_output=True)
                
                if schedule_type == "daily":
                    time_str = self.schedule_time_var.get()
                    cmd = f'schtasks /create /tn "{task_name}" /tr "{python_path} \"{script_path}\"" /sc daily /st {time_str} /f'
                    subprocess.run(cmd, shell=True)
                    self.log(" Очистка настроена на ежедневно в " + time_str, "success")
                elif schedule_type == "weekly":
                    cmd = f'schtasks /create /tn "{task_name}" /tr "{python_path} \"{script_path}\"" /sc weekly /f'
                    subprocess.run(cmd, shell=True)
                    self.log(" Очистка настроена на еженедельно", "success")
                elif schedule_type == "startup":
                    cmd = f'schtasks /create /tn "{task_name}" /tr "{python_path} \"{script_path}\"" /sc onlogon /f'
                    subprocess.run(cmd, shell=True)
                    self.log(" Очистка настроена при входе", "success")
                
                self.update_setting('schedule', schedule_type)
                messagebox.showinfo("Планировщик", "Автоматическая очистка настроена!")
            except Exception as e:
                self.log(" Ошибка: " + str(e), "error")
                messagebox.showerror("Ошибка", "Не удалось настроить планировщик")
            self.log("=" * 80, "info")
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Планировщик очистки")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['bg_secondary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Настройка автоматической очистки", font=('Segoe UI', 12, 'bold'),
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=15)
        
        self.schedule_var = tk.StringVar(value=self.settings.get('schedule', 'never'))
        self.schedule_time_var = tk.StringVar(value="12:00")
        
        options = [("never", "Отключена"), ("daily", "Ежедневно"), ("weekly", "Еженедельно"), ("startup", "При входе в систему")]
        for value, text in options:
            tk.Radiobutton(dialog, text=text, variable=self.schedule_var, value=value,
                          bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                          selectcolor=self.colors['bg_secondary']).pack(anchor=tk.W, padx=30, pady=5)
        
        time_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
        time_frame.pack(anchor=tk.W, padx=50, pady=5)
        tk.Label(time_frame, text="Время:", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        tk.Spinbox(time_frame, from_=0, to=23, width=5, format="%02.0f", textvariable=self.schedule_time_var, font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
        tk.Label(time_frame, text=":00", bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        
        btn_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Применить", command=lambda: [self.run_task(task), dialog.destroy()],
                 bg=self.colors['success'], fg='white', cursor='hand2', borderwidth=0, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                 bg=self.colors['danger'], fg='white', cursor='hand2', borderwidth=0, padx=20, pady=5).pack(side=tk.LEFT, padx=10)
    
    # ==================== БЕЛЫЙ СПИСОК ====================
    
    def manage_whitelist(self):
        def task():
            self.log("=" * 80, "info")
            self.log(" БЕЛЫЙ СПИСОК", "accent")
            whitelist = self.settings.get('whitelist', [])
            
            dialog = tk.Toplevel(self.root)
            dialog.title("Белый список - исключения")
            dialog.geometry("500x400")
            dialog.configure(bg=self.colors['bg_secondary'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Папки, которые НЕ будут очищаться", font=('Segoe UI', 12, 'bold'),
                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=15)
            
            listbox = tk.Listbox(dialog, bg=self.colors['bg_input'], fg=self.colors['text_primary'],
                                 selectbackground=self.colors['accent'], font=('Segoe UI', 10))
            listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            for item in whitelist:
                listbox.insert(tk.END, item)
            
            def add_path():
                path = filedialog.askdirectory()
                if path and path not in whitelist:
                    whitelist.append(path)
                    listbox.insert(tk.END, path)
                    self.update_setting('whitelist', whitelist)
                    self.log(" Добавлено исключение: " + path, "success")
            
            def remove_path():
                selection = listbox.curselection()
                if selection:
                    item = listbox.get(selection[0])
                    whitelist.remove(item)
                    listbox.delete(selection[0])
                    self.update_setting('whitelist', whitelist)
                    self.log(" Удалено исключение: " + item, "success")
            
            btn_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
            btn_frame.pack(pady=10)
            tk.Button(btn_frame, text="Добавить папку", command=add_path,
                     bg=self.colors['success'], fg='white', cursor='hand2', borderwidth=0, padx=15, pady=5).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Удалить из списка", command=remove_path,
                     bg=self.colors['danger'], fg='white', cursor='hand2', borderwidth=0, padx=15, pady=5).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Закрыть", command=dialog.destroy,
                     bg=self.colors['accent'], fg='white', cursor='hand2', borderwidth=0, padx=15, pady=5).pack(side=tk.LEFT, padx=10)
        
        self.run_task(task)
    
    # ==================== UI И НАВИГАЦИЯ ====================
    
    def setup_ui(self):
        self.create_navbar()
        self.main_container = tk.Frame(self.root, bg=self.colors['bg_main'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 15))
        self.create_left_panel()
        self.create_right_panel()
        self.create_statusbar()
        self.show_tools_view()
    
    def create_navbar(self):
        self.navbar = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=50)
        self.navbar.pack(fill=tk.X)
        self.navbar.pack_propagate(False)
        
        logo_frame = tk.Frame(self.navbar, bg=self.colors['bg_secondary'])
        logo_frame.pack(side=tk.LEFT, padx=20)
        
        self.logo_label = tk.Label(logo_frame, text=" ONE VALVE", font=('Segoe UI', 16, 'bold'),
                                   fg=self.colors['success'], bg=self.colors['bg_secondary'])
        self.logo_label.pack(side=tk.LEFT)
        
        cleaner_label = tk.Label(logo_frame, text="  CLEANER", font=('Segoe UI', 16, 'bold'),
                                 fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'])
        cleaner_label.pack(side=tk.LEFT)
        
        self.nav_buttons = []
        nav_items = [
            ("ИНСТРУМЕНТЫ", self.show_tools_view),
            ("НАСТРОЙКИ", self.show_settings_view),
            ("О ПРОГРАММЕ", self.show_about_view)
        ]
        
        for text, command in nav_items:
            btn = tk.Button(self.navbar, text=text, font=('Segoe UI', 10, 'bold'),
                           bg=self.colors['nav_button_bg'], fg=self.colors['nav_button_fg'],
                           activebackground=self.colors['bg_secondary'],
                           activeforeground=self.colors['text_primary'],
                           relief=tk.FLAT, cursor='hand2', borderwidth=0, padx=25, pady=12,
                           command=command)
            btn.pack(side=tk.LEFT, padx=2)
            self.nav_buttons.append(btn)
        
        user_frame = tk.Frame(self.navbar, bg=self.colors['bg_secondary'])
        user_frame.pack(side=tk.RIGHT, padx=20)
        self.user_label = tk.Label(user_frame, text=" " + os.getlogin(), font=('Segoe UI', 9),
                                   fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'])
        self.user_label.pack()
    
    def create_left_panel(self):
        self.left_panel = tk.Frame(self.main_container, bg=self.colors['bg_secondary'], width=380)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        header = tk.Frame(self.left_panel, bg=self.colors['bg_tertiary'], height=45)
        header.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header, text=" ИНСТРУМЕНТЫ ОЧИСТКИ", font=('Segoe UI', 12, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_tertiary']).pack(side=tk.LEFT, padx=15, pady=10)
        
        canvas = tk.Canvas(self.left_panel, bg=self.colors['bg_secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=canvas.yview)
        self.tools_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])
        
        self.tools_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.tools_frame, anchor="nw", width=360)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Инструменты
        tools = [
            ("🗑️", "ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ", self.clean_temp_files),
            ("📁", "ОЧИСТКА ПАПКИ ЗАГРУЗОК", self.clean_downloads),
            ("🔄", "УДАЛЕНИЕ ДУБЛИКАТОВ", self.clean_duplicates),
            ("📊", "ОЧИСТКА СТАРЫХ ФАЙЛОВ", self.clean_old_files),
            ("🗑️", "ОЧИСТКА КОРЗИНЫ", self.clean_recycle_bin),
            ("🌐", "ОЧИСТКА КЭША БРАУЗЕРОВ", self.clean_browser_cache),
            ("💾", "СТАТИСТИКА ДИСКА", self.show_disk_stats),
            ("📊", "АНАЛИЗАТОР ДИСКА", self.analyze_disk),
            ("📦", "УДАЛЕНИЕ ПРОГРАММ", self.show_uninstall_apps),
            ("⏰", "ПЛАНИРОВЩИК ОЧИСТКИ", self.schedule_cleanup),
            ("📋", "БЕЛЫЙ СПИСОК", self.manage_whitelist),
        ]
        
        for icon, title, command in tools:
            self.create_tool_button(icon, title, command)
        
        self.create_progress_section()
    
    def create_tool_button(self, icon, title, command):
        btn_frame = tk.Frame(self.tools_frame, bg=self.colors['bg_secondary'], height=50)
        btn_frame.pack(fill=tk.X, pady=2, padx=5)
        btn_frame.pack_propagate(False)
        
        def on_enter(e):
            btn_frame.config(bg=self.colors['bg_tertiary'])
        def on_leave(e):
            btn_frame.config(bg=self.colors['bg_secondary'])
        def on_click(e):
            command()
        
        btn_frame.bind("<Enter>", on_enter)
        btn_frame.bind("<Leave>", on_leave)
        btn_frame.bind("<Button-1>", on_click)
        
        icon_label = tk.Label(btn_frame, text=icon, font=('Segoe UI', 18),
                             bg=self.colors['bg_secondary'], fg=self.colors['success'])
        icon_label.place(x=12, y=10)
        icon_label.bind("<Enter>", on_enter)
        icon_label.bind("<Leave>", on_leave)
        icon_label.bind("<Button-1>", on_click)
        
        title_label = tk.Label(btn_frame, text=title, font=('Segoe UI', 10, 'bold'),
                              bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        title_label.place(x=55, y=15)
        title_label.bind("<Enter>", on_enter)
        title_label.bind("<Leave>", on_leave)
        title_label.bind("<Button-1>", on_click)
    
    def create_progress_section(self):
        progress_frame = tk.Frame(self.left_panel, bg=self.colors['bg_tertiary'], height=100)
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        progress_frame.pack_propagate(False)
        
        self.progress_label = tk.Label(progress_frame, text="ГОТОВ К РАБОТЕ", font=('Segoe UI', 9, 'bold'),
                                       bg=self.colors['bg_tertiary'], fg=self.colors['success'])
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=340, mode='determinate')
        self.progress_bar.pack(pady=(0, 5), padx=15)
        
        self.progress_status = tk.Label(progress_frame, text="", font=('Segoe UI', 8),
                                        bg=self.colors['bg_tertiary'], fg=self.colors['text_secondary'])
        self.progress_status.pack()
    
    def create_right_panel(self):
        self.right_panel = tk.Frame(self.main_container, bg=self.colors['bg_secondary'])
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        content_header = tk.Frame(self.right_panel, bg=self.colors['bg_tertiary'], height=45)
        content_header.pack(fill=tk.X, pady=(0, 10))
        
        self.view_title = tk.Label(content_header, text=" КОНСОЛЬ ВЫПОЛНЕНИЯ", font=('Segoe UI', 12, 'bold'),
                                   fg=self.colors['text_primary'], bg=self.colors['bg_tertiary'])
        self.view_title.pack(side=tk.LEFT, padx=15)
        
        clear_btn = tk.Button(content_header, text="ОЧИСТИТЬ", command=self.clear_logs,
                             font=('Segoe UI', 8, 'bold'), bg=self.colors['bg_secondary'],
                             fg=self.colors['text_secondary'], cursor='hand2', 
                             borderwidth=0, padx=12)
        clear_btn.pack(side=tk.RIGHT, padx=10)
        
        self.tools_frame_right = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        self.settings_frame = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        self.about_frame = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        
        self.log_text = scrolledtext.ScrolledText(self.tools_frame_right, wrap=tk.WORD,
                                                  font=('Consolas', 10), bg=self.colors['log_bg'],
                                                  fg=self.colors['log_fg'], insertbackground='white', borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text.tag_config("success", foreground=self.colors['success'])
        self.log_text.tag_config("error", foreground=self.colors['danger'])
        self.log_text.tag_config("info", foreground=self.colors['text_secondary'])
        self.log_text.tag_config("warning", foreground=self.colors['warning'])
        self.log_text.tag_config("accent", foreground=self.colors['accent'])
        
        self.create_about_view()
        self.create_settings_view()
    
    def create_about_view(self):
        about_inner = tk.Frame(self.about_frame, bg=self.colors['bg_secondary'])
        about_inner.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        logo_frame = tk.Frame(about_inner, bg=self.colors['bg_tertiary'], height=100)
        logo_frame.pack(fill=tk.X, pady=(0, 20))
        logo_frame.pack_propagate(False)
        
        tk.Label(logo_frame, text=" ONE VALVE ", font=('Impact', 32, 'bold'),
                fg=self.colors['success'], bg=self.colors['bg_tertiary']).pack(pady=25)
        
        tk.Label(about_inner, text="Системный Очиститель", font=('Segoe UI', 20, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_secondary']).pack(pady=(0, 5))
        
        tk.Label(about_inner, text="Версия 2026.1 | Стабильная", font=('Segoe UI', 11),
                fg=self.colors['text_secondary'], bg=self.colors['bg_secondary']).pack(pady=(0, 20))
        
        desc_frame = tk.LabelFrame(about_inner, text=" О ПРОГРАММЕ ", font=('Segoe UI', 12, 'bold'),
                                   fg=self.colors['success'], bg=self.colors['bg_secondary'], bd=1, relief=tk.RIDGE)
        desc_frame.pack(fill=tk.X, pady=10)
        
        desc_text = """ONE VALVE Cleaner - надёжный инструмент для очистки системы от мусора.

ВОЗМОЖНОСТИ:
• Очистка временных файлов
• Очистка папки загрузок
• Удаление дубликатов
• Очистка старых файлов
• Очистка корзины
• Очистка кэша браузеров
• Статистика диска
• Анализатор диска
• Удаление программ
• Планировщик очистки
• Белый список исключений

ONE VALVE - забота о вашем компьютере!"""
        
        tk.Label(desc_frame, text=desc_text, font=('Segoe UI', 10), fg=self.colors['text_secondary'],
                bg=self.colors['bg_secondary'], justify=tk.LEFT, wraplength=800).pack(anchor=tk.W, padx=20, pady=15)
        
        tk.Label(about_inner, text="© 2026 ONE VALVE. Все права защищены.", font=('Segoe UI', 9),
                fg=self.colors['text_muted'], bg=self.colors['bg_secondary']).pack(pady=(20, 0))
    
    def create_settings_view(self):
        self.settings_canvas = tk.Canvas(self.settings_frame, bg=self.colors['bg_secondary'], highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=self.settings_canvas.yview)
        self.settings_inner = tk.Frame(self.settings_canvas, bg=self.colors['bg_secondary'])
        
        self.settings_inner.bind("<Configure>", lambda e: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")))
        self.settings_canvas.create_window((0, 0), window=self.settings_inner, anchor="nw", width=880)
        self.settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        
        def on_mousewheel(event):
            self.settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.settings_canvas.bind("<MouseWheel>", on_mousewheel)
        self.settings_inner.bind("<MouseWheel>", on_mousewheel)
        
        self.settings_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        settings_scrollbar.pack(side="right", fill="y")
        
        tk.Label(self.settings_inner, text="НАСТРОЙКИ ПРОГРАММЫ", font=('Segoe UI', 16, 'bold'),
                fg=self.colors['text_primary'], bg=self.colors['bg_secondary']).pack(anchor=tk.W, pady=(0, 20))
        
        # Внешний вид
        appearance_frame = tk.LabelFrame(self.settings_inner, text=" ВНЕШНИЙ ВИД ", font=('Segoe UI', 12, 'bold'),
                                         fg=self.colors['success'], bg=self.colors['bg_secondary'], bd=1, relief=tk.RIDGE)
        appearance_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(appearance_frame, text="Выберите тему оформления:", font=('Segoe UI', 10),
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        theme_frame = tk.Frame(appearance_frame, bg=self.colors['bg_secondary'])
        theme_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        themes = [("steam_dark", "Steam Dark"), ("github_black", "GitHub Black"), ("arctic_white", "Arctic White")]
        
        for theme_val, theme_name in themes:
            rb = tk.Radiobutton(theme_frame, text=theme_name, variable=self.theme_var, value=theme_val,
                               command=self.change_theme_instant, bg=self.colors['bg_secondary'],
                               fg=self.colors['text_primary'], selectcolor=self.colors['bg_secondary'],
                               activebackground=self.colors['bg_secondary'], font=('Segoe UI', 10))
            rb.pack(side=tk.LEFT, padx=(0, 15))
        
        self.preview_label = tk.Label(appearance_frame, text="", font=('Segoe UI', 9),
                                      bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'])
        self.preview_label.pack(anchor=tk.W, padx=20, pady=(5, 5))
        
        tk.Label(appearance_frame, text="ВНИМАНИЕ: Для применения темы требуется перезапуск программы!",
                font=('Segoe UI', 9), fg=self.colors['warning'], bg=self.colors['bg_secondary']).pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        tk.Button(appearance_frame, text="ПЕРЕЗАПУСТИТЬ ПРИЛОЖЕНИЕ", command=self.restart_app,
                 font=('Segoe UI', 10, 'bold'), bg=self.colors['success'], fg='white',
                 cursor='hand2', borderwidth=0, padx=20, pady=8).pack(pady=(5, 15))
        
        self.update_preview()
        
        # Системные настройки
        system_frame = tk.LabelFrame(self.settings_inner, text=" СИСТЕМНЫЕ НАСТРОЙКИ ", font=('Segoe UI', 12, 'bold'),
                                     fg=self.colors['success'], bg=self.colors['bg_secondary'], bd=1, relief=tk.RIDGE)
        system_frame.pack(fill=tk.X, pady=10)
        
        autostart_frame = tk.Frame(system_frame, bg=self.colors['bg_secondary'])
        autostart_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.autostart_var = tk.BooleanVar(value=self.check_autostart())
        tk.Checkbutton(autostart_frame, text="Запускать программу при старте Windows", variable=self.autostart_var,
                      command=self.toggle_autostart, bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                      selectcolor=self.colors['bg_secondary'], activebackground=self.colors['bg_secondary'],
                      font=('Segoe UI', 10)).pack(side=tk.LEFT)
        
        tk.Label(autostart_frame, text="(требуются права администратора)", font=('Segoe UI', 8),
                fg=self.colors['text_muted'], bg=self.colors['bg_secondary']).pack(side=tk.LEFT, padx=(10, 0))
        
        # Сброс настроек
        reset_frame = tk.LabelFrame(self.settings_inner, text=" СБРОС НАСТРОЕК ", font=('Segoe UI', 12, 'bold'),
                                    fg=self.colors['danger'], bg=self.colors['bg_secondary'], bd=1, relief=tk.RIDGE)
        reset_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(reset_frame, text="Сбросить все настройки к значениям по умолчанию", font=('Segoe UI', 10),
                bg=self.colors['bg_secondary'], fg=self.colors['text_secondary']).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        tk.Button(reset_frame, text="СБРОСИТЬ ВСЕ НАСТРОЙКИ", command=self.reset_settings,
                 font=('Segoe UI', 10, 'bold'), bg=self.colors['danger'], fg='white',
                 cursor='hand2', borderwidth=0, padx=20, pady=10).pack(pady=(5, 15))
    
    def update_preview(self):
        themes_preview = {
            'steam_dark': "Steam Dark: тёмно-синяя тема в стиле Steam",
            'github_black': "GitHub Black: чёрная тема в стиле GitHub",
            'arctic_white': "Arctic White: светлая тема в стиле арктической белизны"
        }
        self.preview_label.config(text=themes_preview.get(self.theme_var.get(), "Выберите тему"))
    
    def change_theme_instant(self):
        new_theme = self.theme_var.get()
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            self.update_setting('theme', new_theme)
            self.update_preview()
            self.log(" Тема изменена на " + new_theme, "success")
            self.log(" ДЛЯ ПРИМЕНЕНИЯ ТЕМЫ НАЖМИТЕ КНОПКУ ПЕРЕЗАПУСКА!", "warning")
            messagebox.showinfo("Смена темы", "Тема изменена на " + new_theme + "\n\nДля полного применения темы нажмите кнопку 'ПЕРЕЗАПУСТИТЬ ПРИЛОЖЕНИЕ'.")
    
    def update_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()
        self.log("Настройка " + key + " изменена на " + str(value), "info")
    
    def reset_settings(self):
        if messagebox.askyesno("Сброс настроек", "Сбросить все настройки к значениям по умолчанию?"):
            self.settings = {
                'theme': 'steam_dark',
                'autostart': False,
                'schedule': 'never',
                'whitelist': []
            }
            self.save_settings()
            self.theme_var.set('steam_dark')
            self.current_theme = 'steam_dark'
            self.autostart_var.set(False)
            self.disable_autostart()
            self.update_preview()
            self.log("Настройки сброшены к значениям по умолчанию!", "success")
            messagebox.showinfo("Сброс настроек", "Настройки успешно сброшены!")
    
    def show_tools_view(self):
        self.current_view = "tools"
        self.view_title.config(text=" КОНСОЛЬ ВЫПОЛНЕНИЯ")
        self.tools_frame_right.pack(fill=tk.BOTH, expand=True)
        self.settings_frame.pack_forget()
        self.about_frame.pack_forget()
        for btn in self.nav_buttons:
            if btn.cget('text') == "ИНСТРУМЕНТЫ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
    
    def show_settings_view(self):
        self.current_view = "settings"
        self.view_title.config(text=" НАСТРОЙКИ ПРОГРАММЫ")
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
        self.tools_frame_right.pack_forget()
        self.about_frame.pack_forget()
        for btn in self.nav_buttons:
            if btn.cget('text') == "НАСТРОЙКИ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
    
    def show_about_view(self):
        self.current_view = "about"
        self.view_title.config(text=" О ПРОГРАММЕ")
        self.about_frame.pack(fill=tk.BOTH, expand=True)
        self.tools_frame_right.pack_forget()
        self.settings_frame.pack_forget()
        for btn in self.nav_buttons:
            if btn.cget('text') == "О ПРОГРАММЕ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
    
    def create_statusbar(self):
        self.statusbar = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=30)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.pack_propagate(False)
        
        self.status_text = tk.Label(self.statusbar, text="● ГОТОВ", font=('Segoe UI', 8, 'bold'),
                                    fg=self.colors['success'], bg=self.colors['bg_secondary'])
        self.status_text.pack(side=tk.LEFT, padx=15)
        
        tk.Label(self.statusbar, text="ONE VALVE CLEANER - СТАБИЛЬНАЯ ВЕРСИЯ", font=('Segoe UI', 8),
                fg=self.colors['text_muted'], bg=self.colors['bg_secondary']).pack(side=tk.LEFT, padx=20)
        
        self.time_label = tk.Label(self.statusbar, text="", font=('Segoe UI', 8),
                                   fg=self.colors['text_muted'], bg=self.colors['bg_secondary'])
        self.time_label.pack(side=tk.RIGHT, padx=15)
        
        self.disk_label = tk.Label(self.statusbar, text="", font=('Segoe UI', 8),
                                   fg=self.colors['text_muted'], bg=self.colors['bg_secondary'])
        self.disk_label.pack(side=tk.RIGHT, padx=15)
    
    def update_time(self):
        self.time_label.config(text=" " + datetime.now().strftime('%H:%M:%S'))
        self.root.after(1000, self.update_time)
    
    def update_disk_info(self):
        try:
            total, used, free = shutil.disk_usage("C:\\")
            free_gb = free / (1024**3)
            self.disk_label.config(text=" Свободно: " + str(round(free_gb, 1)) + " ГБ")
        except:
            pass
        self.root.after(5000, self.update_disk_info)
    
    def log(self, message, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = "[" + timestamp + "] " + message + "\n"
        self.log_text.insert(tk.END, formatted, tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_logs(self):
        self.log_text.delete(1.0, tk.END)
        self.log("Консоль очищена", "info")
    
    def update_progress(self, value, text):
        self.progress_var.set(value)
        self.progress_status.config(text=text)
        self.root.update_idletasks()
    
    def run_task(self, func, *args):
        def target():
            self.status_text.config(text="● ВЫПОЛНЕНИЕ...", fg=self.colors['warning'])
            self.progress_label.config(text="ВЫПОЛНЕНИЕ...", fg=self.colors['warning'])
            self.root.config(cursor="watch")
            self.update_progress(0, "Запуск...")
            try:
                func(*args)
                self.update_progress(100, "Завершено!")
                self.status_text.config(text="● ГОТОВ", fg=self.colors['success'])
                self.progress_label.config(text="ГОТОВ К РАБОТЕ", fg=self.colors['success'])
            except Exception as e:
                self.log("Ошибка: " + str(e), "error")
                self.status_text.config(text="● ОШИБКА", fg=self.colors['danger'])
                self.progress_label.config(text="ОШИБКА", fg=self.colors['danger'])
            finally:
                self.root.config(cursor="")
                self.root.after(3000, lambda: self.update_progress(0, ""))
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
    
    def process_queue(self):
        try:
            while True:
                func, args = self.task_queue.get_nowait()
                self.run_task(func, *args)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)
    
    # ==================== АВТОЗАПУСК ====================
    
    def check_autostart(self):
        try:
            if platform.system() == 'Windows':
                startup_folder = os.path.join(os.environ['APPDATA'], 
                                             'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                shortcut_path = os.path.join(startup_folder, 'ONEVALVE_Cleaner.lnk')
                return os.path.exists(shortcut_path)
        except:
            pass
        return False
    
    def enable_autostart(self):
        try:
            if platform.system() == 'Windows':
                if getattr(sys, 'frozen', False):
                    app_path = sys.executable
                else:
                    app_path = sys.executable
                    script_path = os.path.abspath(__file__)
                    app_path = '"' + app_path + '" "' + script_path + '"'
                
                startup_folder = os.path.join(os.environ['APPDATA'], 
                                             'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                shortcut_path = os.path.join(startup_folder, 'ONEVALVE_Cleaner.lnk')
                
                powershell_script = f'''
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{app_path.split('"')[1] if '"' in app_path else app_path}"
$Shortcut.WorkingDirectory = "{os.path.dirname(os.path.abspath(__file__))}"
$Shortcut.Description = "ONEVALVE Cleaner"
$Shortcut.Save()
'''
                with open('temp_ps.ps1', 'w', encoding='utf-8') as f:
                    f.write(powershell_script)
                os.system('powershell -ExecutionPolicy Bypass -File "temp_ps.ps1"')
                os.remove('temp_ps.ps1')
                self.log(" Автозапуск включен", "success")
                return True
        except Exception as e:
            self.log(" Ошибка включения автозапуска: " + str(e), "error")
            return False
    
    def disable_autostart(self):
        try:
            if platform.system() == 'Windows':
                startup_folder = os.path.join(os.environ['APPDATA'], 
                                             'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                shortcut_path = os.path.join(startup_folder, 'ONEVALVE_Cleaner.lnk')
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    self.log(" Автозапуск выключен", "success")
                    return True
        except Exception as e:
            self.log(" Ошибка выключения автозапуска: " + str(e), "error")
            return False
    
    def toggle_autostart(self):
        if self.autostart_var.get():
            if self.enable_autostart():
                self.update_setting('autostart', True)
                messagebox.showinfo("Автозапуск", "Автозапуск программы включен!")
            else:
                self.autostart_var.set(False)
                messagebox.showerror("Ошибка", "Не удалось включить автозапуск.\nПопробуйте запустить программу от имени администратора.")
        else:
            if self.disable_autostart():
                self.update_setting('autostart', False)
                messagebox.showinfo("Автозапуск", "Автозапуск программы выключен.")
            else:
                self.autostart_var.set(True)
                messagebox.showerror("Ошибка", "Не удалось выключить автозапуск.")
    
    def restart_app(self):
        self.log(" Перезапуск приложения...", "warning")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def load_settings(self):
        default_settings = {
            'theme': 'steam_dark',
            'autostart': False,
            'schedule': 'never',
            'whitelist': []
        }
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = default_settings
        except:
            self.settings = default_settings
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except:
            pass
    
    def exit_app(self):
        self.log("Завершение работы...")
        self.root.after(500, self.root.destroy)

# ====================================================================================
#                              RUN APPLICATION
# ====================================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = OneValveCleaner(root)
    root.mainloop()