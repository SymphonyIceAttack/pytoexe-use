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
    
    # ==================== УДАЛЕНИЕ ВСТРОЕННЫХ ПРОГРАММ ====================
    
    def get_installed_apps(self):
        """Получение списка установленных приложений через PowerShell"""
        apps = []
        try:
            # Получаем список приложений через PowerShell
            ps_script = '''
Get-AppxPackage | Select-Object -Property Name, PackageFullName, InstallLocation | ConvertTo-Json -Compress
'''
            with open('temp_apps.ps1', 'w', encoding='utf-8') as f:
                f.write(ps_script)
            
            result = subprocess.run('powershell -ExecutionPolicy Bypass -File "temp_apps.ps1"', 
                                   shell=True, capture_output=True, text=True, timeout=30)
            os.remove('temp_apps.ps1')
            
            if result.stdout:
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    if item.get('Name'):
                        apps.append({
                            'name': item['Name'],
                            'fullname': item.get('PackageFullName', ''),
                            'location': item.get('InstallLocation', '')
                        })
        except Exception as e:
            self.log(" Ошибка получения списка приложений: " + str(e), "error")
        
        return apps
    
    def get_win32_apps(self):
        """Получение списка обычных программ через реестр"""
        apps = []
        try:
            reg_paths = [
                r"HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall",
                r"HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
                r"HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for reg_path in reg_paths:
                try:
                    result = subprocess.run(f'reg query "{reg_path}" /s', shell=True, capture_output=True, text=True, timeout=30)
                    lines = result.stdout.split('\n')
                    current_app = {}
                    for line in lines:
                        if 'DisplayName' in line:
                            name = line.split('    ')[-1].strip()
                            if name and not any(x in name.lower() for x in ['update', 'redist', 'directx', 'vc++']):
                                current_app['name'] = name
                        elif 'UninstallString' in line and current_app.get('name'):
                            apps.append({'name': current_app['name'], 'type': 'win32'})
                            current_app = {}
                except:
                    pass
        except Exception as e:
            self.log(" Ошибка получения списка программ: " + str(e), "error")
        
        return apps
    
    def uninstall_app(self, app_name, app_fullname=None):
        """Удаление приложения через PowerShell"""
        try:
            if app_fullname:
                # Удаление UWP приложения
                cmd = f'powershell -Command "Get-AppxPackage *{app_name}* | Remove-AppxPackage"'
            else:
                # Удаление обычной программы
                cmd = f'powershell -Command "Get-Package -Name \"{app_name}\" | Uninstall-Package"'
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except:
            return False
    
    def uninstall_builtin_app(self, app_name, app_id):
        """Удаление встроенного приложения Windows"""
        try:
            # Команда для удаления встроенных приложений
            cmd = f'powershell -Command "Get-AppxPackage *{app_id}* | Remove-AppxPackage"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            return result.returncode == 0
        except:
            return False
    
    def show_uninstall_apps(self):
        """Показать список установленных программ для удаления"""
        def task():
            self.log("=" * 80, "info")
            self.log(" УПРАВЛЕНИЕ ПРОГРАММАМИ", "accent")
            self.log(" Загрузка списка программ...", "info")
            
            # Получаем список приложений
            uwp_apps = self.get_installed_apps()
            win32_apps = self.get_win32_apps()
            
            all_apps = []
            for app in uwp_apps[:50]:
                all_apps.append({'name': app['name'], 'type': 'uwp', 'fullname': app.get('fullname', '')})
            for app in win32_apps[:50]:
                if app not in all_apps:
                    all_apps.append({'name': app['name'], 'type': 'win32', 'fullname': ''})
            
            if not all_apps:
                self.log(" Не удалось загрузить список программ", "error")
                return
            
            # Создаём диалог выбора
            dialog = tk.Toplevel(self.root)
            dialog.title("Удаление программ")
            dialog.geometry("600x500")
            dialog.configure(bg=self.colors['bg_secondary'])
            dialog.transient(self.root)
            dialog.grab_set()
            
            tk.Label(dialog, text="Выберите программу для удаления", font=('Segoe UI', 12, 'bold'),
                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=15)
            
            # Список программ
            listbox_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
            listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            listbox = tk.Listbox(listbox_frame, bg=self.colors['bg_input'], fg=self.colors['text_primary'],
                                 selectbackground=self.colors['accent'], font=('Segoe UI', 10))
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=listbox.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox.config(yscrollcommand=scrollbar.set)
            
            for app in all_apps:
                type_icon = "📦" if app['type'] == 'uwp' else "💿"
                listbox.insert(tk.END, f"{type_icon} {app['name']}")
            
            # Кнопки управления
            btn_frame = tk.Frame(dialog, bg=self.colors['bg_secondary'])
            btn_frame.pack(pady=15)
            
            def uninstall_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("Выбор", "Выберите программу для удаления")
                    return
                
                app = all_apps[selection[0]]
                
                if messagebox.askyesno("Подтверждение", f"Вы действительно хотите удалить:\n\n{app['name']}\n\nЭто действие может быть необратимым!"):
                    self.log(" Удаление: " + app['name'], "warning")
                    
                    if app['type'] == 'uwp':
                        success = self.uninstall_app(app['name'], app.get('fullname'))
                    else:
                        success = self.uninstall_app(app['name'])
                    
                    if success:
                        self.log(" Программа удалена: " + app['name'], "success")
                        messagebox.showinfo("Успех", f"Программа '{app['name']}' успешно удалена!")
                        dialog.destroy()
                    else:
                        self.log(" Ошибка удаления: " + app['name'], "error")
                        messagebox.showerror("Ошибка", f"Не удалось удалить '{app['name']}'\nВозможно, требуются права администратора.")
            
            def uninstall_builtin():
                """Удаление встроенных приложений Windows"""
                builtin_apps = [
                    ("3D Builder", "Microsoft.3DBuilder"),
                    ("Калькулятор (старый)", "Microsoft.WindowsCalculator"),
                    ("Календарь и Почта", "microsoft.windowscommunicationsapps"),
                    ("Камера", "Microsoft.WindowsCamera"),
                    ("Cortana", "Microsoft.549981C3F5F10"),
                    ("Films & TV", "Microsoft.ZuneVideo"),
                    ("Get Help", "Microsoft.GetHelp"),
                    ("Get Started", "Microsoft.Getstarted"),
                    ("Groove Music", "Microsoft.ZuneMusic"),
                    ("Карты", "Microsoft.WindowsMaps"),
                    ("Microsoft News", "Microsoft.BingNews"),
                    ("Microsoft Solitaire Collection", "Microsoft.MicrosoftSolitaireCollection"),
                    ("Microsoft Sticky Notes", "Microsoft.MicrosoftStickyNotes"),
                    ("OneNote", "Microsoft.Office.OneNote"),
                    ("Paint 3D", "Microsoft.MSPaint"),
                    ("People", "Microsoft.People"),
                    ("Power Automate", "Microsoft.PowerAutomateDesktop"),
                    ("Skype", "Microsoft.SkypeApp"),
                    ("Snip & Sketch", "Microsoft.ScreenSketch"),
                    ("Spotify", "SpotifyAB.SpotifyMusic"),
                    ("Microsoft Teams", "Microsoft.Teams"),
                    ("To Do", "Microsoft.Todos"),
                    ("Voice Recorder", "Microsoft.WindowsSoundRecorder"),
                    ("Weather", "Microsoft.BingWeather"),
                    ("Xbox Console Companion", "Microsoft.XboxApp"),
                    ("Xbox Game Bar", "Microsoft.XboxGamingOverlay"),
                    ("Xbox Live", "Microsoft.XboxIdentityProvider"),
                    ("Your Phone", "Microsoft.YourPhone"),
                    ("Zune Music", "Microsoft.ZuneMusic"),
                    ("Zune Video", "Microsoft.ZuneVideo"),
                ]
                
                builtin_dialog = tk.Toplevel(dialog)
                builtin_dialog.title("Удаление встроенных приложений Windows")
                builtin_dialog.geometry("500x450")
                builtin_dialog.configure(bg=self.colors['bg_secondary'])
                builtin_dialog.transient(dialog)
                builtin_dialog.grab_set()
                
                tk.Label(builtin_dialog, text="Встроенные приложения Windows", font=('Segoe UI', 12, 'bold'),
                        bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(pady=15)
                
                tk.Label(builtin_dialog, text="ВНИМАНИЕ! Удаление некоторых приложений может повлиять на работу системы",
                        font=('Segoe UI', 9), bg=self.colors['bg_secondary'], fg=self.colors['danger']).pack()
                
                builtin_listbox = tk.Listbox(builtin_dialog, bg=self.colors['bg_input'], fg=self.colors['text_primary'],
                                             selectbackground=self.colors['accent'], font=('Segoe UI', 10), height=15)
                builtin_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
                
                for name, _ in builtin_apps:
                    builtin_listbox.insert(tk.END, f"⚠️ {name}")
                
                def remove_selected_builtin():
                    selection = builtin_listbox.curselection()
                    if not selection:
                        return
                    
                    app_name, app_id = builtin_apps[selection[0]]
                    
                    if messagebox.askyesno("Подтверждение", f"⚠️ ВНИМАНИЕ!\n\nВы собираетесь удалить:\n{app_name}\n\nЭто действие может повлиять на работу Windows.\n\nПродолжить?"):
                        self.log(" Удаление встроенного приложения: " + app_name, "warning")
                        success = self.uninstall_builtin_app(app_name, app_id)
                        
                        if success:
                            self.log(" Приложение удалено: " + app_name, "success")
                            builtin_listbox.delete(selection[0])
                            messagebox.showinfo("Успех", f"Приложение '{app_name}' успешно удалено!")
                        else:
                            self.log(" Ошибка удаления: " + app_name, "error")
                            messagebox.showerror("Ошибка", f"Не удалось удалить '{app_name}'")
                
                btn_builtin_frame = tk.Frame(builtin_dialog, bg=self.colors['bg_secondary'])
                btn_builtin_frame.pack(pady=15)
                
                tk.Button(btn_builtin_frame, text="Удалить выбранное", command=remove_selected_builtin,
                         bg=self.colors['danger'], fg='white', cursor='hand2', borderwidth=0, padx=20, pady=8).pack()
            
            tk.Button(btn_frame, text="Удалить программу", command=uninstall_selected,
                     bg=self.colors['danger'], fg='white', cursor='hand2', borderwidth=0, padx=20, pady=8).pack(side=tk.LEFT, padx=10)
            
            tk.Button(btn_frame, text="Удалить встроенные приложения Windows", command=uninstall_builtin,
                     bg=self.colors['warning'], fg='white', cursor='hand2', borderwidth=0, padx=20, pady=8).pack(side=tk.LEFT, padx=10)
            
            tk.Button(btn_frame, text="Закрыть", command=dialog.destroy,
                     bg=self.colors['accent'], fg='white', cursor='hand2', borderwidth=0, padx=20, pady=8).pack(side=tk.LEFT, padx=10)
            
            self.log(" Загружено программ: " + str(len(all_apps)), "info")
        
        self.run_task(task)
    
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
                import ctypes
                if not ctypes.windll.shell32.IsUserAnAdmin():
                    self.log(" Требуются права администратора", "warning")
                    messagebox.showwarning("Планировщик", "Требуются права администратора")
                    return
                
                script_path = os.path.abspath(__file__)
                python_path = sys.executable
                bat_path = os.path.join(os.environ['TEMP'], 'onevalve_clean.bat')
                with open(bat_path, 'w') as f:
                    f.write('@echo off\n')
                    f.write('"' + python_path + '" "' + script_path + '" --auto-clean\n')
                
                task_name = "ONEVALVE_Cleaner"
                subprocess.run('schtasks /delete /tn "' + task_name + '" /f', shell=True, capture_output=True)
                
                if schedule_type == "daily":
                    time_str = self.schedule_time_var.get()
                    subprocess.run('schtasks /create /tn "' + task_name + '" /tr "' + bat_path + '" /sc daily /st ' + time_str + ' /f', shell=True)
                    self.log(" Очистка настроена на ежедневно в " + time_str, "success")
                elif schedule_type == "weekly":
                    subprocess.run('schtasks /create /tn "' + task_name + '" /tr "' + bat_path + '" /sc weekly /f', shell=True)
                    self.log(" Очистка настроена на еженедельно", "success")
                elif schedule_type == "startup":
                    subprocess.run('schtasks /create /tn "' + task_name + '" /tr "' + bat_path + '" /sc onlogon /f', shell=True)
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
        
        for value, text in [("never", "Отключена"), ("daily", "Ежедневно"), ("weekly", "Еженедельно"), ("startup", "При входе в систему")]:
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
            
            def add_path