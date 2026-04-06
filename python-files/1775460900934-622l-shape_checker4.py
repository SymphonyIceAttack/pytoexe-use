import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
import zipfile
import tempfile
import os
import shutil
import re
import sys
import traceback
from pathlib import Path
from datetime import datetime

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ (РАБОТАЕТ НА СЕТЕВЫХ ДИСКАХ) ==========
LOG_FILE = None

def setup_logging():
    """Создаёт файл лога в локальной папке пользователя"""
    global LOG_FILE
    try:
        # Используем локальную папку пользователя вместо сетевого диска
        log_dir = Path(os.environ.get('TEMP', Path.home() / 'AppData' / 'Local' / 'Temp'))
        log_dir = log_dir / "ShapefileChecker"
        log_dir.mkdir(exist_ok=True)
        
        log_filename = log_dir / f"shape_checker_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        LOG_FILE = log_filename
        return LOG_FILE
    except Exception as e:
        print(f"Не удалось создать лог: {e}")
        return None

def log_message(msg, level="INFO"):
    """Записывает сообщение в лог и выводит в консоль"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] [{level}] {msg}"
    print(log_entry)
    
    if LOG_FILE:
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except:
            pass

def log_error(error_msg, exc_info=None):
    """Записывает ошибку с трейсбеком"""
    log_message(error_msg, "ERROR")
    if exc_info:
        tb_str = traceback.format_exc()
        log_message(f"Traceback:\n{tb_str}", "ERROR")

# Создаём лог сразу
setup_logging()
log_message("=" * 60)
log_message("ЗАПУСК ПРОГРАММЫ (СЕТЕВОЙ ДИСК)")
log_message(f"Python версия: {sys.version}")
log_message(f"Рабочая директория: {os.getcwd()}")
log_message(f"Папка логов: {LOG_FILE}")
log_message("=" * 60)

# ========== ДИАГНОСТИКА PYTHON PATH ==========
log_message("Содержимое sys.path:")
for i, path in enumerate(sys.path):
    log_message(f"  {i}: {path}")

# ========== ПОПЫТКА ИМПОРТА БИБЛИОТЕК С РАСШИРЕННОЙ ДИАГНОСТИКОЙ ==========

def check_pip_install():
    """Проверяет, установлены ли библиотеки через pip"""
    import subprocess
    
    libs = ['pyshp', 'dbf', 'chardet', 'gdal']
    results = {}
    
    for lib in libs:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', lib],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Парсим версию
                for line in result.stdout.split('\n'):
                    if line.startswith('Version:'):
                        results[lib] = line.split(':')[1].strip()
                        break
                else:
                    results[lib] = "установлена"
            else:
                results[lib] = "НЕ УСТАНОВЛЕНА"
        except Exception as e:
            results[lib] = f"Ошибка проверки: {e}"
    
    return results

def try_import_with_diagnostic(lib_name, import_cmd, pip_name=None):
    """Пытается импортировать библиотеку с подробной диагностикой"""
    log_message(f"Попытка импорта: {lib_name}")
    
    if pip_name is None:
        pip_name = lib_name
    
    try:
        exec(import_cmd)
        log_message(f"✓ {lib_name} успешно импортирован")
        return True
    except ImportError as e:
        log_message(f"✗ {lib_name} НЕ ИМПОРТИРОВАН: {str(e)}", "ERROR")
        
        # Проверяем, установлена ли библиотека через pip
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', pip_name],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                log_message(f"  Библиотека {pip_name} установлена в pip, но не импортируется", "WARNING")
                # Показываем где установлена
                for line in result.stdout.split('\n'):
                    if line.startswith('Location:'):
                        log_message(f"  Установлена в: {line}", "INFO")
                        break
            else:
                log_message(f"  Библиотека {pip_name} НЕ найдена в pip", "WARNING")
        except:
            pass
        
        return False
    except Exception as e:
        log_message(f"✗ {lib_name} - неожиданная ошибка: {str(e)}", "ERROR")
        log_error(f"Ошибка при импорте {lib_name}", True)
        return False

# Проверяем установку через pip
log_message("=" * 60)
log_message("ПРОВЕРКА УСТАНОВКИ БИБЛИОТЕК ЧЕРЕЗ PIP:")
pip_status = check_pip_install()
for lib, status in pip_status.items():
    log_message(f"  {lib}: {status}")
log_message("=" * 60)

# Пробуем импортировать библиотеки
shapefile_ok = try_import_with_diagnostic("shapefile", "import shapefile", "pyshp")
ogr_ok = try_import_with_diagnostic("ogr", "from osgeo import ogr", "gdal")
osr_ok = try_import_with_diagnostic("osr", "from osgeo import osr", "gdal")
dbf_ok = try_import_with_diagnostic("dbf", "import dbf", "dbf")
chardet_ok = try_import_with_diagnostic("chardet", "import chardet", "chardet")

gdal_available = ogr_ok and osr_ok

# Создаём переменные для импортированных модулей
if shapefile_ok:
    import shapefile
else:
    shapefile = None

if gdal_available:
    from osgeo import ogr, osr
else:
    ogr = None
    osr = None

if dbf_ok:
    import dbf
else:
    dbf = None

if chardet_ok:
    import chardet
else:
    chardet = None

# Проверяем, все ли библиотеки импортированы
all_ok = shapefile_ok and dbf_ok and chardet_ok

if not all_ok:
    log_message("=" * 60)
    log_message("ОТСУТСТВУЮТ БИБЛИОТЕКИ:", "ERROR")
    
    missing = []
    if not shapefile_ok:
        missing.append("pyshp (shapefile)")
    if not dbf_ok:
        missing.append("dbf")
    if not chardet_ok:
        missing.append("chardet")
    
    for lib in missing:
        log_message(f"  - {lib}", "ERROR")
    
    log_message("=" * 60)
    
    # Формируем сообщение для пользователя
    error_msg = "Отсутствуют необходимые библиотеки:\n\n"
    for lib in missing:
        error_msg += f"• {lib}\n"
    
    error_msg += "\nРЕШЕНИЕ: Установите библиотеки в локальную папку\n"
    error_msg += f"Откройте командную строку (Win+R -> cmd) и выполните:\n\n"
    error_msg += f'cd /d "%LOCALAPPDATA%"\n'
    error_msg += f'mkdir PythonLibs\n'
    error_msg += f'cd PythonLibs\n'
    error_msg += f'{sys.executable} -m pip install --target="%CD%" pyshp dbf chardet\n\n'
    error_msg += "Затем добавьте в начало программы:\n"
    error_msg += f'import sys\n'
    error_msg += f'sys.path.insert(0, r"%LOCALAPPDATA%\\PythonLibs")\n\n'
    
    error_msg += f"\nПодробный лог сохранён в: {LOG_FILE}"
    
    # Показываем окно с ошибкой
    root = tk.Tk()
    root.withdraw()
    
    # Спрашиваем, хочет ли пользователь автоматически установить библиотеки
    answer = messagebox.askyesno(
        "Ошибка импорта библиотек", 
        error_msg + "\n\nХотите автоматически установить недостающие библиотеки в локальную папку?"
    )
    
    if answer:
        # Автоматическая установка
        install_window = tk.Toplevel(root)
        install_window.title("Установка библиотек")
        install_window.geometry("500x300")
        
        text_area = scrolledtext.ScrolledText(install_window, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        def install_libs():
            import subprocess
            local_lib_path = os.path.join(os.environ['LOCALAPPDATA'], 'PythonLibs')
            os.makedirs(local_lib_path, exist_ok=True)
            
            text_area.insert(tk.END, f"Установка в: {local_lib_path}\n")
            text_area.insert(tk.END, "-" * 50 + "\n")
            text_area.see(tk.END)
            
            for lib in ['pyshp', 'dbf', 'chardet']:
                text_area.insert(tk.END, f"Установка {lib}...\n")
                text_area.see(tk.END)
                
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--target', local_lib_path, lib],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    text_area.insert(tk.END, f"✓ {lib} установлен\n", "green")
                else:
                    text_area.insert(tk.END, f"✗ Ошибка установки {lib}:\n{result.stderr}\n", "red")
                
                text_area.see(tk.END)
            
            text_area.insert(tk.END, "\n" + "=" * 50 + "\n")
            text_area.insert(tk.END, "Установка завершена!\n")
            text_area.insert(tk.END, "Перезапустите программу.\n")
            
            # Добавляем инструкцию
            text_area.insert(tk.END, "\nВАЖНО: Добавьте эти строки в начало программы:\n")
            text_area.insert(tk.END, f'import sys\n')
            text_area.insert(tk.END, f'sys.path.insert(0, r"{local_lib_path}")\n')
        
        install_btn = tk.Button(install_window, text="Начать установку", command=install_libs)
        install_btn.pack(pady=(0, 10))
    else:
        root.destroy()
        sys.exit(1)
    
    root.destroy()
    
    if not answer:
        sys.exit(1)

log_message("Все необходимые библиотеки успешно загружены")
log_message("=" * 60)

# Добавляем локальную папку в PATH если её там нет
local_lib_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'PythonLibs')
if os.path.exists(local_lib_path) and local_lib_path not in sys.path:
    sys.path.insert(0, local_lib_path)
    log_message(f"Добавлен путь к библиотекам: {local_lib_path}")

# ========== ОСТАЛЬНОЙ КОД (ФУНКЦИИ ПРОВЕРКИ) ==========
# ... (здесь идёт весь остальной код из предыдущего сообщения,
#      начиная с EXPECTED_FIELDS и всех функций check_*)

# ========== GUI ПРИЛОЖЕНИЯ ==========

class ShapefileCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проверка шейп-файлов (Сетевая версия)")
        self.root.geometry("450x300")
        self.root.resizable(False, False)
        
        self.archive_path = None
        self.temp_dir = None
        
        self.create_widgets()
        
        # Показываем информацию
        log_message("GUI приложение запущено")
        
        info_frame = tk.Frame(self.root)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)
        
        log_label = tk.Label(info_frame, text=f"Лог: {LOG_FILE.name if LOG_FILE else 'не создан'}", 
                            font=("Arial", 8), fg="gray")
        log_label.pack(side=tk.LEFT)
        
        path_label = tk.Label(info_frame, text=f"Python: {sys.version[:10]}", 
                            font=("Arial", 8), fg="gray")
        path_label.pack(side=tk.RIGHT)
    
    def create_widgets(self):
        # Предупреждение о сетевом диске
        warning_frame = tk.Frame(self.root, bg="#ffeecc", relief=tk.RIDGE, bd=1)
        warning_frame.pack(fill=tk.X, padx=10, pady=5)
        
        warning_label = tk.Label(warning_frame, 
                                text="⚠️ ВНИМАНИЕ: Запуск с сетевого диска может работать медленнее\n"
                                     "Рекомендуется скопировать программу на локальный диск",
                                bg="#ffeecc", fg="#cc6600", justify=tk.CENTER)
        warning_label.pack(padx=5, pady=5)
        
        # Поле для пути к файлу
        tk.Label(self.root, text="Выберите архив с шейп-файлом:").pack(pady=(10, 5))
        
        self.path_var = tk.StringVar()
        path_entry = tk.Entry(self.root, textvariable=self.path_var, width=50)
        path_entry.pack(padx=10, pady=(0, 5), fill=tk.X)
        
        # Кнопка обзора
        browse_btn = tk.Button(self.root, text="Обзор...", command=self.browse_file)
        browse_btn.pack(pady=(0, 5))
        
        # Кнопка проверки
        self.check_btn = tk.Button(self.root, text="Проверить", command=self.start_check, state=tk.DISABLED)
        self.check_btn.pack(pady=(0, 5))
        
        # Статус
        self.status_label = tk.Label(self.root, text="Статус: Файл не выбран", fg="gray")
        self.status_label.pack(pady=(10, 0))
        
        # Кнопки
        button_frame = tk.Frame(self.root)
        button_frame.pack(side=tk.BOTTOM, pady=5)
        
        log_btn = tk.Button(button_frame, text="Показать лог", command=self.show_log)
        log_btn.pack(side=tk.LEFT, padx=5)
        
        install_btn = tk.Button(button_frame, text="Проверить библиотеки", command=self.check_libs)
        install_btn.pack(side=tk.LEFT, padx=5)
    
    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите архив с шейп-файлом",
            filetypes=[
                ("ZIP архивы", "*.zip"),
                ("Все файлы", "*.*")
            ]
        )
        
        if filepath:
            self.archive_path = filepath
            self.path_var.set(filepath)
            self.status_label.config(text=f"Статус: Файл выбран", fg="green")
            self.check_btn.config(state=tk.NORMAL)
            log_message(f"Выбран файл: {filepath}")
    
    def check_libs(self):
        """Проверка установленных библиотек"""
        result_window = tk.Toplevel(self.root)
        result_window.title("Проверка библиотек")
        result_window.geometry("500x400")
        
        text_area = scrolledtext.ScrolledText(result_window, wrap=tk.WORD, font=("Consolas", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_area.insert(tk.END, "ПРОВЕРКА БИБЛИОТЕК\n", "bold")
        text_area.insert(tk.END, "=" * 50 + "\n\n")
        
        # Проверяем каждую библиотеку
        libs = [
            ("shapefile (pyshp)", shapefile is not None),
            ("ogr (GDAL)", ogr is not None),
            ("osr (GDAL)", osr is not None),
            ("dbf", dbf is not None),
            ("chardet", chardet is not None),
        ]
        
        for lib_name, status in libs:
            if status:
                text_area.insert(tk.END, f"✓ {lib_name}: ДОСТУПНА\n", "green")
            else:
                text_area.insert(tk.END, f"✗ {lib_name}: НЕ ДОСТУПНА\n", "red")
        
        text_area.insert(tk.END, "\n" + "=" * 50 + "\n")
        text_area.insert(tk.END, f"Путь к логу: {LOG_FILE}\n")
        
        # Настраиваем цвета
        text_area.tag_config("green", foreground="green")
        text_area.tag_config("red", foreground="red")
        text_area.tag_config("bold", font=("Consolas", 10, "bold"))
    
    def show_log(self):
        """Показывает содержимое лог-файла"""
        if LOG_FILE and LOG_FILE.exists():
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                
                log_window = tk.Toplevel(self.root)
                log_window.title("Лог программы")
                log_window.geometry("700x500")
                
                text_area = scrolledtext.ScrolledText(log_window, wrap=tk.WORD, font=("Consolas", 9))
                text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_area.insert(tk.END, log_content)
                text_area.config(state=tk.DISABLED)
                
                def copy_log():
                    self.root.clipboard_clear()
                    self.root.clipboard_append(log_content)
                    messagebox.showinfo("Скопировано", "Лог скопирован в буфер обмена")
                
                btn_frame = tk.Frame(log_window)
                btn_frame.pack(fill=tk.X, padx=10, pady=5)
                
                copy_btn = tk.Button(btn_frame, text="Копировать лог", command=copy_log)
                copy_btn.pack(side=tk.LEFT, padx=5)
                
                open_btn = tk.Button(btn_frame, text="Открыть папку с логом", 
                                    command=lambda: os.startfile(str(LOG_FILE.parent)))
                open_btn.pack(side=tk.LEFT, padx=5)
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось прочитать лог: {e}")
        else:
            messagebox.showinfo("Лог не найден", f"Лог-файл не создан или ещё не существует")
    
    def start_check(self):
        if not self.archive_path:
            return
        
        self.check_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Статус: Проверка...", fg="blue")
        self.root.update()
        
        import threading
        thread = threading.Thread(target=self.run_check)
        thread.daemon = True
        thread.start()
    
    def run_check(self):
        errors = []
        warnings = []
        
        try:
            self.temp_dir = tempfile.mkdtemp()
            log_message(f"Создана временная папка: {self.temp_dir}")
            
            self.status_label.config(text="Статус: Распаковка архива...")
            self.root.update()
            
            if self.archive_path.lower().endswith('.zip'):
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    zf.extractall(self.temp_dir)
            else:
                errors.append("Поддерживаются только ZIP архивы")
                self.show_results(errors, warnings)
                return
            
            shp_files = list(Path(self.temp_dir).rglob("*.shp"))
            if not shp_files:
                errors.append("В архиве не найден .shp файл")
                self.show_results(errors, warnings)
                return
            
            shp_path = str(shp_files[0])
            log_message(f"Найден шейп-файл: {shp_path}")
            
            self.status_label.config(text="Статус: Проверка...")
            self.root.update()
            
            # Здесь вызываются функции проверки
            # (код из предыдущего сообщения)
            
        except Exception as e:
            errors.append(f"Ошибка: {str(e)}")
            log_error("Ошибка в run_check", True)
        finally:
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
        
        self.show_results(errors, warnings)
    
    def show_results(self, errors, warnings):
        # Аналогично предыдущей версии
        pass

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    root = tk.Tk()
    app = ShapefileCheckerApp(root)
    root.mainloop()