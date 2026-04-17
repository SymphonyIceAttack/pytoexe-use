Python 3.14.4 (tags/v3.14.4:23116f9, Apr  7 2026, 14:10:54) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
# cleaner_app.py - Главный файл приложения
import os
import sys
import shutil
import platform
import threading
import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧹 Очистщик временных файлов")
        self.root.geometry("700x650")
        
        # Определяем путь к файлу конфига (для EXE)
        if getattr(sys, 'frozen', False):
            # Запущено как EXE
            self.base_path = sys._MEIPASS
            self.config_file = Path(os.path.expanduser('~')) / '.cleaner_config.json'
        else:
            # Запущено как скрипт
            self.base_path = os.path.dirname(__file__)
            self.config_file = Path(self.base_path) / '.cleaner_config.json'
        
        self.load_config()
        self.apply_theme()
        self.is_cleaning = False
        self.temp_paths = self.get_temp_paths()
        self.setup_ui()
        self.load_sizes_async()
    
    def load_config(self):
        """Загружает настройки из файла"""
        default_config = {'theme': 'dark', 'auto_clean': False}
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config = {**default_config, **saved_config}
            except:
                self.config = default_config
        else:
            self.config = default_config
    
    def save_config(self):
        """Сохраняет настройки в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def apply_theme(self):
        """Применяет выбранную тему"""
        if self.config['theme'] == 'dark':
            self.colors = {
                'bg': '#1e1e2e', 'fg': '#ffffff', 'primary': '#4CAF50',
                'primary_dark': '#45a049', 'secondary': '#2196F3',
                'warning': '#FF9800', 'danger': '#f44336',
                'frame_bg': '#2d2d3f', 'button_bg': '#4CAF50',
                'button_fg': '#ffffff', 'log_bg': '#1a1a2a',
                'log_fg': '#00ff00', 'select_bg': '#4CAF50'
            }
        else:
            self.colors = {
                'bg': '#f5f5f5', 'fg': '#333333', 'primary': '#4CAF50',
                'primary_dark': '#45a049', 'secondary': '#2196F3',
                'warning': '#FF9800', 'danger': '#f44336',
                'frame_bg': '#ffffff', 'button_bg': '#4CAF50',
                'button_fg': '#ffffff', 'log_bg': '#ffffff',
                'log_fg': '#000000', 'select_bg': '#e0e0e0'
            }
    
    def toggle_theme(self):
        """Переключает тему"""
        self.config['theme'] = 'light' if self.config['theme'] == 'dark' else 'dark'
        self.apply_theme()
        self.save_config()
        
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
        self.load_sizes_async()
    
    def setup_ui(self):
        # Интерфейс (код из предыдущего примера)
        self.root.configure(bg=self.colors['bg'])
        
        # Верхняя панель
        top_bar = tk.Frame(self.root, bg=self.colors['primary'], height=70)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        title_label = tk.Label(top_bar, text="🧹 Очистщик временных файлов", 
                               font=("Arial", 18, "bold"), 
                               bg=self.colors['primary'], fg="white")
        title_label.pack(side=tk.LEFT, padx=20)
        
        theme_icon = "🌙" if self.config['theme'] == 'light' else "☀️"
        theme_btn = tk.Button(top_bar, text=f"{theme_icon} Тема", 
                             command=self.toggle_theme,
                             font=("Arial", 10, "bold"),
                             bg=self.colors['secondary'], fg="white",
                             cursor="hand2", relief=tk.RAISED, padx=15)
        theme_btn.pack(side=tk.RIGHT, padx=20)
        
        # Основное содержимое
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Информация
        sys_frame = tk.LabelFrame(main_frame, text="📊 Информация о системе", 
                                  bg=self.colors['frame_bg'], fg=self.colors['fg'],
                                  font=("Arial", 10, "bold"))
        sys_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.os_label = tk.Label(sys_frame, text=f"ОС: {platform.system()}", 
                                 bg=self.colors['frame_bg'], fg=self.colors['fg'],
                                 anchor='w', padx=10, pady=5)
        self.os_label.pack(fill=tk.X)
        
        self.total_size_label = tk.Label(sys_frame, text="Общий размер временных файлов: Загрузка...", 
                                         bg=self.colors['frame_bg'], fg=self.colors['warning'],
                                         anchor='w', padx=10, pady=5)
        self.total_size_label.pack(fill=tk.X)
        
        # Действия
        action_frame = tk.LabelFrame(main_frame, text="🔧 Выберите действие", 
                                     bg=self.colors['frame_bg'], fg=self.colors['fg'],
                                     font=("Arial", 10, "bold"))
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.action_var = tk.IntVar(value=1)
        actions = [
            ("✅ Очистить всё (временные файлы + кэш браузеров)", 1),
            ("📁 Только временные папки", 2),
            ("🌐 Только кэш браузеров", 3)
        ]
        
        for text, value in actions:
            rb = tk.Radiobutton(action_frame, text=text, variable=self.action_var, 
                                value=value, bg=self.colors['frame_bg'],
                                fg=self.colors['fg'], selectcolor=self.colors['select_bg'],
                                font=("Arial", 10))
            rb.pack(anchor='w', padx=20, pady=5)
        
        # Кнопка очистки
        self.clean_btn = tk.Button(main_frame, text="🚀 НАЧАТЬ ОЧИСТКУ", 
                                   command=self.start_cleaning, 
                                   font=("Arial", 12, "bold"),
                                   bg=self.colors['button_bg'], fg=self.colors['button_fg'], 
                                   height=2, cursor="hand2", relief=tk.RAISED)
        self.clean_btn.pack(fill=tk.X, pady=(0, 15))
        
        # Прогресс
        self.progress_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_label = tk.Label(self.progress_frame, text="Готов к работе", 
                                       bg=self.colors['bg'], fg=self.colors['fg'],
                                       font=("Arial", 9))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Лог
        log_frame = tk.LabelFrame(main_frame, text="📝 Лог очистки", 
                                  bg=self.colors['frame_bg'], fg=self.colors['fg'],
                                  font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, 
                                                   font=("Consolas", 9),
                                                   bg=self.colors['log_bg'],
                                                   fg=self.colors['log_fg'],
                                                   insertbackground=self.colors['fg'])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.add_log(f"👋 Добро пожаловать!\n")
    
    def add_log(self, message):
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def get_temp_paths(self):
        temp_paths = []
        system = platform.system()
        
        if system == "Windows":
            temp_paths = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
                os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'),
            ]
            temp_paths = [p for p in temp_paths if p and os.path.exists(p)]
        elif system in ["Linux", "Darwin"]:
            temp_paths = ['/tmp', '/var/tmp', os.path.join(os.path.expanduser('~'), '.cache')]
            temp_paths = [p for p in temp_paths if os.path.exists(p)]
        
        return list(set(temp_paths))
    
    def get_size(self, path):
        total = 0
        try:
            if os.path.isfile(path):
                return os.path.getsize(path)
            for entry in os.scandir(path):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += self.get_size(entry.path)
        except (PermissionError, FileNotFoundError, OSError):
            pass
        return total
    
    def format_size(self, size_bytes):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} ТБ"
    
    def load_sizes_async(self):
        def calculate():
            total = 0
            for path in self.temp_paths:
                total += self.get_size(path)
            self.root.after(0, lambda: self.total_size_label.config(
                text=f"Общий размер временных файлов: {self.format_size(total)}"))
        
        thread = threading.Thread(target=calculate, daemon=True)
        thread.start()
    
    def delete_folder_contents(self, path):
        if not os.path.exists(path):
            return 0, 0
        
        deleted = 0
        freed = 0
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    item_size = self.get_size(item_path)
                    
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    
                    deleted += 1
                    freed += item_size
                except (PermissionError, OSError):
                    pass
        except Exception:
            pass
        
        return deleted, freed
    
    def clean_browser_cache(self):
        freed = 0
        home = Path.home()
        system = platform.system()
        
        browser_paths = []
        if system == "Windows":
            browser_paths = [
                home / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Cache',
                home / 'AppData' / 'Local' / 'Mozilla' / 'Firefox' / 'Profiles',
            ]
        elif system == "Darwin":
            browser_paths = [
                home / 'Library' / 'Caches' / 'Google' / 'Chrome',
                home / 'Library' / 'Caches' / 'Firefox',
            ]
        elif system == "Linux":
            browser_paths = [
                home / '.cache' / 'google-chrome',
                home / '.cache' / 'mozilla' / 'firefox',
            ]
        
        for cache_path in browser_paths:
            if cache_path.exists():
                size = self.get_size(str(cache_path))
                try:
                    if cache_path.is_dir():
                        for item in cache_path.iterdir():
                            try:
                                if item.is_file():
                                    item.unlink()
                                elif item.is_dir():
                                    shutil.rmtree(item)
                            except (PermissionError, OSError):
                                pass
                    freed += size
                    self.add_log(f"  🌐 {cache_path.name}: очищено {self.format_size(size)}\n")
                except Exception:
                    self.add_log(f"  ❌ Не удалось очистить: {cache_path.name}\n")
        
        return freed
    
    def start_cleaning(self):
        if self.is_cleaning:
            messagebox.showwarning("Внимание", "Очистка уже выполняется!")
            return
        
        self.is_cleaning = True
        self.clean_btn.config(state=tk.DISABLED, text="⏳ ОЧИСТКА ВЫПОЛНЯЕТСЯ...")
        self.progress_bar.start(10)
        self.progress_label.config(text="Очистка...")
        
        action = self.action_var.get()
        
        def cleaning_thread():
            try:
                if action == 1:
                    self.clean_all()
                elif action == 2:
                    self.clean_temp_only()
                elif action == 3:
                    self.clean_browser_only()
                
                self.root.after(0, self.on_clean_finished)
            except Exception as e:
                self.root.after(0, lambda: self.on_clean_error(str(e)))
        
        thread = threading.Thread(target=cleaning_thread, daemon=True)
        thread.start()
    
    def clean_all(self):
        self.add_log("\n🧹 Начинаем полную очистку...\n")
        total_freed = 0
        total_files = 0
        
        for path in self.temp_paths:
            self.add_log(f"\n📁 Обработка: {path}\n")
            files, freed = self.delete_folder_contents(path)
            total_files += files
            total_freed += freed
            self.add_log(f"   ✅ Удалено элементов: {files}\n")
            self.add_log(f"   💾 Освобождено: {self.format_size(freed)}\n")
        
        self.add_log(f"\n🌐 Очистка кэша браузеров...\n")
        freed_browser = self.clean_browser_cache()
        total_freed += freed_browser
        
        self.add_log(f"\n📊 ИТОГО:\n")
        self.add_log(f"   Удалено файлов/папок: {total_files}\n")
        self.add_log(f"   Освобождено места: {self.format_size(total_freed)}\n")
    
    def clean_temp_only(self):
        self.add_log("\n📁 Очищаем только временные папки...\n")
        total_freed = 0
        total_files = 0
        
        for path in self.temp_paths:
...             self.add_log(f"\n📁 Обработка: {path}\n")
...             files, freed = self.delete_folder_contents(path)
...             total_files += files
...             total_freed += freed
...             self.add_log(f"   ✅ Удалено элементов: {files}\n")
...             self.add_log(f"   💾 Освобождено: {self.format_size(freed)}\n")
...         
...         self.add_log(f"\n📊 ИТОГО освобождено: {self.format_size(total_freed)}\n")
...     
...     def clean_browser_only(self):
...         self.add_log("\n🌐 Очищаем только кэш браузеров...\n")
...         freed = self.clean_browser_cache()
...         self.add_log(f"\n📊 ИТОГО освобождено: {self.format_size(freed)}\n")
...     
...     def on_clean_finished(self):
...         self.is_cleaning = False
...         self.progress_bar.stop()
...         self.progress_label.config(text="Очистка завершена!")
...         self.clean_btn.config(state=tk.NORMAL, text="🚀 НАЧАТЬ ОЧИСТКУ")
...         self.add_log("\n✅ ОЧИСТКА УСПЕШНО ЗАВЕРШЕНА!\n")
...         self.load_sizes_async()
...         messagebox.showinfo("Успех", "Очистка успешно завершена!")
...     
...     def on_clean_error(self, error):
...         self.is_cleaning = False
...         self.progress_bar.stop()
...         self.progress_label.config(text="Ошибка!")
...         self.clean_btn.config(state=tk.NORMAL, text="🚀 НАЧАТЬ ОЧИСТКУ")
...         self.add_log(f"\n❌ ОШИБКА: {error}\n")
...         messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error}")
... 
... if __name__ == "__main__":
...     root = tk.Tk()
...     app = CleanerApp(root)
...     root.mainloop()
...     
SyntaxError: multiple statements found while compiling a single statement
>>> 

