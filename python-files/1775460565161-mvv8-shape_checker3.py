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

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
LOG_FILE = None

def setup_logging():
    """Создаёт файл лога рядом с программой"""
    global LOG_FILE
    log_dir = Path(__file__).parent if hasattr(sys, 'frozen') else Path.cwd()
    log_filename = log_dir / f"shape_checker_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    LOG_FILE = log_filename
    return LOG_FILE

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

# ========== ПОПЫТКА ИМПОРТА БИБЛИОТЕК С ЛОГИРОВАНИЕМ ==========

log_message("=" * 60)
log_message("ЗАПУСК ПРОГРАММЫ")
log_message(f"Python версия: {sys.version}")
log_message(f"Рабочая директория: {os.getcwd()}")
log_message("=" * 60)

# Словарь для хранения статуса импорта
libs_status = {}

def try_import(lib_name, import_cmd, alternative_note=""):
    """Пытается импортировать библиотеку и логирует результат"""
    log_message(f"Попытка импорта: {lib_name}")
    try:
        exec(import_cmd)
        libs_status[lib_name] = True
        log_message(f"✓ {lib_name} успешно импортирован")
        return True
    except ImportError as e:
        libs_status[lib_name] = False
        log_message(f"✗ {lib_name} НЕ ИМПОРТИРОВАН: {str(e)}", "ERROR")
        if alternative_note:
            log_message(f"  Примечание: {alternative_note}", "WARNING")
        return False
    except Exception as e:
        libs_status[lib_name] = False
        log_message(f"✗ {lib_name} - неожиданная ошибка: {str(e)}", "ERROR")
        log_error(f"Ошибка при импорте {lib_name}", True)
        return False

# Пробуем импортировать каждую библиотеку
try_import("shapefile", "import shapefile")
try_import("ogr", "from osgeo import ogr", "Требуется GDAL")
try_import("osr", "from osgeo import osr", "Требуется GDAL")
try_import("dbf", "import dbf")
try_import("chardet", "import chardet")

# Проверяем GDAL целиком
gdal_available = libs_status.get("ogr", False) and libs_status.get("osr", False)

# Создаём переменные для импортированных модулей
if libs_status.get("shapefile", False):
    import shapefile
else:
    shapefile = None

if gdal_available:
    from osgeo import ogr, osr
else:
    ogr = None
    osr = None

if libs_status.get("dbf", False):
    import dbf
else:
    dbf = None

if libs_status.get("chardet", False):
    import chardet
else:
    chardet = None

# Анализируем результат
missing_libs = [lib for lib, status in libs_status.items() if not status]
if missing_libs:
    log_message("=" * 60)
    log_message("ОТСУТСТВУЮТ БИБЛИОТЕКИ:", "ERROR")
    for lib in missing_libs:
        log_message(f"  - {lib}", "ERROR")
    log_message("=" * 60)
    
    # Формируем сообщение для пользователя
    error_msg = "Отсутствуют необходимые библиотеки:\n\n"
    for lib in missing_libs:
        error_msg += f"• {lib}\n"
    
    error_msg += "\nРекомендации по установке:\n"
    error_msg += "1. Установите через pip:\n"
    error_msg += "   pip install pyshp dbf chardet\n\n"
    
    if not gdal_available:
        error_msg += "2. Для GDAL (самый сложный):\n"
        error_msg += "   Вариант A (рекомендуется): Установите Anaconda/Miniconda\n"
        error_msg += "   conda install -c conda-forge gdal\n\n"
        error_msg += "   Вариант B: Скачайте предварительно собранное колесо\n"
        error_msg += "   https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal\n\n"
        error_msg += "   Вариант C: Используйте без проверки самопересечений\n"
        error_msg += "   (в коде закомментируйте блок с ogr)\n"
    
    error_msg += f"\nПодробный лог сохранён в: {LOG_FILE}"
    
    # Показываем окно с ошибкой
    root = tk.Tk()
    root.withdraw()  # Скрываем главное окно
    messagebox.showerror("Ошибка импорта библиотек", error_msg)
    root.destroy()
    
    log_message("Программа завершена из-за отсутствия библиотек")
    sys.exit(1)

log_message("Все необходимые библиотеки успешно загружены")
log_message("=" * 60)

# ========== ЭТАЛОН СТРУКТУРЫ ПОЛЕЙ ==========
EXPECTED_FIELDS = [
    ("fo", "C", 254, 0),
    ("sri", "C", 254, 0),
    ("mu", "C", 254, 0),
    ("gir", "C", 254, 0),
    ("ugir", "C", 254, 0),
    ("kv", "C", 5, 0),
    ("sknr", "C", 5, 0),
    ("mk", "C", 254, 0),
    ("mk_pf", "C", 254, 0),
    ("mk_pf_cat", "C", 254, 0),
    ("ozu", "C", 254, 0),
    ("arenda", "C", 254, 0),
    ("arenda_vid", "C", 254, 0),
    ("pl", "N", 8, 4),
    ("turlhl", "N", 4, 0),
    ("sknr_lp", "C", 5, 0),
    ("pl_uch_ga", "N", 11, 4),
    ("lat_centra", "N", 7, 5),
    ("lon_centra", "N", 8, 5),
    ("s_cond", "C", 254, 0),
    ("turlhl_d", "N", 6, 0),
    ("kod_prich", "C", 254, 0),
    ("prichn", "C", 254, 0),
    ("god_povr", "N", 4, 0),
    ("id_snimka", "C", 254, 0),
    ("dat_snimka", "D", 10, 0),
    ("dat_deshif", "D", 10, 0),
    ("filial", "C", 254, 0),
    ("ispolnit", "C", 254, 0),
    ("primech", "C", 254, 0),
    ("_n_subject", "N", 4, 0),
]

# ========== ФУНКЦИИ ПРОВЕРКИ С ЛОГИРОВАНИЕМ ==========

def check_crs(prj_path):
    """Проверка системы координат (WGS 84)"""
    log_message(f"Проверка CRS: {prj_path}")
    
    if not os.path.exists(prj_path):
        log_message("Файл .prj не найден", "WARNING")
        return False, "Отсутствует файл .prj (система координат не определена)"
    
    try:
        with open(prj_path, 'r', encoding='utf-8', errors='ignore') as f:
            prj_content = f.read().lower()
        
        log_message(f"Содержимое .prj (первые 200 символов): {prj_content[:200]}")
        
        # Проверяем наличие WGS 84
        if 'wgs 84' in prj_content or 'wgs_1984' in prj_content:
            if 'web_mercator' not in prj_content and '3857' not in prj_content:
                log_message("CRS: WGS 84 - OK")
                return True, "OK"
            else:
                msg = f"Система координат: Web Mercator. Должна быть WGS 84 (EPSG:4326)"
                log_message(msg, "ERROR")
                return False, msg
        else:
            # Попробуем извлечь название СК
            crs_name = "Неизвестная"
            if 'geogcs' in prj_content:
                match = re.search(r'geogcs\["([^"]+)"', prj_content)
                if match:
                    crs_name = match.group(1)
            msg = f"Система координат: {crs_name}. Должна быть WGS 84 (EPSG:4326)"
            log_message(msg, "ERROR")
            return False, msg
    except Exception as e:
        log_error(f"Ошибка чтения .prj: {str(e)}", True)
        return False, f"Ошибка чтения .prj: {str(e)}"

def check_codepage(shp_path):
    """Проверка кодировки (кириллическая: 1251 или 866)"""
    log_message(f"Проверка кодировки для: {shp_path}")
    
    # Проверяем наличие .cpg
    cpg_path = shp_path.replace('.shp', '.cpg')
    
    if os.path.exists(cpg_path):
        try:
            with open(cpg_path, 'r', encoding='utf-8') as f:
                codepage = f.read().strip().lower()
            log_message(f"Найден файл .cpg с содержимым: {codepage}")
        except Exception as e:
            log_error(f"Ошибка чтения .cpg: {str(e)}", True)
            codepage = "unknown"
        
        if codepage in ['1251', 'windows-1251', 'ansi 1251', 'cp1251']:
            log_message("Кодировка Windows-1251 - OK")
            return True, "Windows-1251 (допустимо)", codepage
        elif codepage in ['866', 'cp866', 'oem 866']:
            log_message("Кодировка CP866 - OK")
            return True, "CP866 (допустимо)", codepage
        else:
            msg = f"Кодировка: {codepage}. Должна быть кириллической: Windows-1251 или CP866"
            log_message(msg, "ERROR")
            return False, msg, codepage
    else:
        log_message("Файл .cpg не найден, пробуем определить кодировку из .dbf", "WARNING")
        # Пытаемся определить кодировку из .dbf
        dbf_path = shp_path.replace('.shp', '.dbf')
        if os.path.exists(dbf_path) and chardet:
            try:
                with open(dbf_path, 'rb') as f:
                    raw = f.read(1000)
                    detected = chardet.detect(raw)
                    if detected['encoding']:
                        enc = detected['encoding'].lower()
                        log_message(f"Определена кодировка: {enc} (уверенность: {detected['confidence']})")
                        if '1251' in enc or 'windows-1251' in enc:
                            return True, f"Windows-1251 (определено автоматически)", enc
                        elif '866' in enc:
                            return True, f"CP866 (определено автоматически)", enc
                        else:
                            msg = f"Кодировка: {enc}. Должна быть кириллической: Windows-1251 или CP866"
                            log_message(msg, "ERROR")
                            return False, msg, enc
            except Exception as e:
                log_error(f"Ошибка определения кодировки: {str(e)}", True)
        
        return False, "Отсутствует файл .cpg (кодировка не определена)", "неизвестна"

def check_geometry(shp_path):
    """Проверка геометрии"""
    log_message(f"Проверка геометрии: {shp_path}")
    errors = []
    warnings = []
    
    try:
        if not shapefile:
            log_message("Библиотека shapefile не доступна", "ERROR")
            errors.append("Библиотека pyshp не загружена")
            return errors, warnings
            
        reader = shapefile.Reader(shp_path)
        shapes = reader.shapes()
        records = reader.records()
        
        log_message(f"Найдено объектов: {len(shapes)}")
        
        # Проверка типа геометрии
        shape_type = reader.shapeType
        shape_type_name = {
            5: 'Polygon',
            15: 'PolygonZ',
            25: 'PolygonM'
        }.get(shape_type, f'Тип {shape_type}')
        
        log_message(f"Тип геометрии: {shape_type_name} (код: {shape_type})")
        
        if shape_type not in [5, 15, 25]:
            msg = f"Тип геометрии — {shape_type_name}. Должен быть Polygon (полигоны)"
            errors.append(msg)
            log_message(msg, "ERROR")
        
        # Проверка количества объектов
        if len(shapes) == 0:
            msg = "Файл не содержит ни одного объекта (0 объектов)"
            errors.append(msg)
            log_message(msg, "ERROR")
        
        # Проверка каждого объекта
        for i, shape in enumerate(shapes, 1):
            # Пустая геометрия
            if shape.points is None or len(shape.points) == 0:
                msg = f"Объект №{i} — пустая геометрия (Null geometry)"
                errors.append(msg)
                log_message(msg, "ERROR")
                continue
            
            # Проверка замкнутости полигонов
            for part_idx, part in enumerate(shape.parts):
                start = part
                if part_idx + 1 < len(shape.parts):
                    end = shape.parts[part_idx + 1]
                else:
                    end = len(shape.points)
                
                part_points = shape.points[start:end]
                if len(part_points) > 0:
                    first = part_points[0]
                    last = part_points[-1]
                    if first != last:
                        msg = f"Объект №{i} — полигон не замкнут (первая и последняя точки не совпадают)"
                        errors.append(msg)
                        log_message(msg, "ERROR")
                        break
            
            # Проверка площади (если есть геометрия и это полигон)
            if shape_type in [5, 15, 25] and len(shape.points) > 0:
                # Вычисляем площадь (упрощённо)
                area = 0
                for part_idx, part in enumerate(shape.parts):
                    start = part
                    if part_idx + 1 < len(shape.parts):
                        end = shape.parts[part_idx + 1]
                    else:
                        end = len(shape.points)
                    part_points = shape.points[start:end]
                    
                    for j in range(len(part_points) - 1):
                        x1, y1 = part_points[j]
                        x2, y2 = part_points[j + 1]
                        area += x1 * y2 - x2 * y1
                
                area = abs(area) / 2.0
                
                if area == 0:
                    msg = f"Объект №{i} — площадь полигона равна 0"
                    warnings.append(msg)
                    log_message(msg, "WARNING")
        
        # Проверка самопересечений (через OGR для точности)
        if gdal_available and ogr:
            log_message("Проверка самопересечений через OGR")
            try:
                ds = ogr.Open(shp_path)
                if ds:
                    layer = ds.GetLayer(0)
                    invalid_count = 0
                    for i, feature in enumerate(layer, 1):
                        geom = feature.GetGeometryRef()
                        if geom and geom.IsValid() == 0:
                            msg = f"Объект №{i} — самопересечение полигона"
                            errors.append(msg)
                            log_message(msg, "ERROR")
                            invalid_count += 1
                    ds = None
                    log_message(f"Проверено объектов: {i}, найдено самопересечений: {invalid_count}")
                else:
                    log_message("Не удалось открыть файл через OGR", "WARNING")
            except Exception as e:
                log_error(f"Ошибка OGR при проверке самопересечений: {str(e)}", True)
        else:
            log_message("Проверка самопересечений пропущена (GDAL не доступен)", "WARNING")
            warnings.append("Проверка самопересечений не выполнена (требуется GDAL)")
            
    except Exception as e:
        log_error(f"Ошибка проверки геометрии: {str(e)}", True)
        errors.append(f"Ошибка чтения геометрии: {str(e)}")
    
    log_message(f"Результат проверки геометрии: {len(errors)} ошибок, {len(warnings)} предупреждений")
    return errors, warnings

def check_fields(dbf_path):
    """Проверка структуры полей"""
    log_message(f"Проверка полей: {dbf_path}")
    errors = []
    
    try:
        if not dbf:
            log_message("Библиотека dbf не доступна", "ERROR")
            errors.append("Библиотека dbf не загружена")
            return errors
            
        table = dbf.Table(dbf_path, codepage='cp1251')
        table.open()
        
        actual_fields = []
        for field in table.fields:
            if field.name:  # Пропускаем пустые
                field_type = field.type
                # Преобразуем тип dbf в наш формат
                type_map = {
                    'C': 'C',  # Character/String
                    'N': 'N',  # Numeric
                    'D': 'D',  # Date
                }
                actual_fields.append((
                    field.name,
                    type_map.get(field_type, 'C'),
                    field.length,
                    field.decimal_count
                ))
        
        log_message(f"Найдено полей в файле: {len(actual_fields)}, ожидается: {len(EXPECTED_FIELDS)}")
        
        # Проверка количества полей
        if len(actual_fields) != len(EXPECTED_FIELDS):
            msg = f"Количество полей: {len(actual_fields)}, ожидалось: {len(EXPECTED_FIELDS)}"
            errors.append(msg)
            log_message(msg, "ERROR")
        
        # Проверка порядка и содержимого
        for i, (exp_name, exp_type, exp_len, exp_prec) in enumerate(EXPECTED_FIELDS):
            if i >= len(actual_fields):
                msg = f"Отсутствует обязательное поле \"{exp_name}\""
                errors.append(msg)
                log_message(msg, "ERROR")
                continue
            
            act_name, act_type, act_len, act_prec = actual_fields[i]
            
            if act_name != exp_name:
                msg = f"Поле {i+1}: имя \"{act_name}\", ожидалось \"{exp_name}\""
                errors.append(msg)
                log_message(msg, "ERROR")
            
            if act_type != exp_type:
                msg = f"Поле \"{exp_name}\": тип {act_type}, ожидался {exp_type}"
                errors.append(msg)
                log_message(msg, "ERROR")
            
            if act_len != exp_len:
                msg = f"Поле \"{exp_name}\": длина {act_len}, ожидалась {exp_len}"
                errors.append(msg)
                log_message(msg, "ERROR")
            
            if act_prec != exp_prec:
                msg = f"Поле \"{exp_name}\": точность {act_prec}, ожидалась {exp_prec}"
                errors.append(msg)
                log_message(msg, "ERROR")
        
        # Проверка лишних полей
        if len(actual_fields) > len(EXPECTED_FIELDS):
            for i in range(len(EXPECTED_FIELDS), len(actual_fields)):
                msg = f"Лишнее поле \"{actual_fields[i][0]}\" — не найдено в эталоне"
                errors.append(msg)
                log_message(msg, "ERROR")
        
        table.close()
        log_message(f"Проверка полей завершена. Найдено ошибок: {len(errors)}")
        
    except Exception as e:
        log_error(f"Ошибка проверки полей: {str(e)}", True)
        errors.append(f"Ошибка проверки полей: {str(e)}")
    
    return errors

def check_shapefile(shp_path):
    """Основная функция проверки шейп-файла"""
    log_message("=" * 60)
    log_message(f"НАЧАЛО ПРОВЕРКИ ШЕЙП-ФАЙЛА: {shp_path}")
    log_message("=" * 60)
    
    all_errors = []
    all_warnings = []
    
    # 1. Проверка системы координат
    prj_path = shp_path.replace('.shp', '.prj')
    crs_ok, crs_msg = check_crs(prj_path)
    if not crs_ok:
        all_errors.append(crs_msg)
    
    # 2. Проверка кодировки
    cp_ok, cp_msg, cp_actual = check_codepage(shp_path)
    if not cp_ok:
        all_errors.append(cp_msg)
    else:
        all_warnings.append(cp_msg)
    
    # 3. Проверка геометрии
    geom_errors, geom_warnings = check_geometry(shp_path)
    all_errors.extend(geom_errors)
    all_warnings.extend(geom_warnings)
    
    # 4. Проверка структуры полей
    dbf_path = shp_path.replace('.shp', '.dbf')
    if os.path.exists(dbf_path):
        field_errors = check_fields(dbf_path)
        all_errors.extend(field_errors)
    else:
        msg = "Отсутствует файл .dbf (таблица атрибутов)"
        all_errors.append(msg)
        log_message(msg, "ERROR")
    
    log_message("=" * 60)
    log_message(f"ИТОГ: {len(all_errors)} ошибок, {len(all_warnings)} предупреждений")
    log_message("=" * 60)
    
    return all_errors, all_warnings

# ========== GUI ПРИЛОЖЕНИЯ ==========

class ShapefileCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проверка шейп-файлов")
        self.root.geometry("450x250")
        self.root.resizable(False, False)
        
        self.archive_path = None
        self.temp_dir = None
        
        self.create_widgets()
        
        # Показываем информацию о логе
        log_message("GUI приложение запущено")
        log_label = tk.Label(self.root, text=f"Лог: {LOG_FILE.name if LOG_FILE else 'не создан'}", 
                            font=("Arial", 8), fg="gray")
        log_label.pack(side=tk.BOTTOM, pady=2)
    
    def create_widgets(self):
        # Поле для пути к файлу
        tk.Label(self.root, text="Выберите архив с шейп-файлом:").pack(pady=(10, 5))
        
        self.path_var = tk.StringVar()
        path_entry = tk.Entry(self.root, textvariable=self.path_var, width=50)
        path_entry.pack(padx=10, pady=(0, 5), fill=tk.X)
        
        # Кнопка обзора
        browse_btn = tk.Button(self.root, text="Обзор...", command=self.browse_file)
        browse_btn.pack(pady=(0, 5))
        
        # Кнопка проверки (изначально скрыта)
        self.check_btn = tk.Button(self.root, text="Проверить", command=self.start_check, state=tk.DISABLED)
        self.check_btn.pack(pady=(0, 5))
        
        # Статус
        self.status_label = tk.Label(self.root, text="Статус: Файл не выбран", fg="gray")
        self.status_label.pack(pady=(10, 0))
        
        # Кнопка просмотра лога
        log_btn = tk.Button(self.root, text="Показать лог", command=self.show_log)
        log_btn.pack(side=tk.BOTTOM, pady=5)
    
    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите архив с шейп-файлом",
            filetypes=[
                ("Архивы", "*.zip *.7z *.rar"),
                ("ZIP файлы", "*.zip"),
                ("Все файлы", "*.*")
            ]
        )
        
        if filepath:
            self.archive_path = filepath
            self.path_var.set(filepath)
            self.status_label.config(text=f"Статус: Файл выбран", fg="green")
            self.check_btn.config(state=tk.NORMAL)
            log_message(f"Выбран файл: {filepath}")
    
    def start_check(self):
        if not self.archive_path:
            return
        
        # Блокируем кнопку
        self.check_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Статус: Проверка...", fg="blue")
        self.root.update()
        
        # Запускаем проверку в отдельном потоке
        import threading
        thread = threading.Thread(target=self.run_check)
        thread.daemon = True
        thread.start()
    
    def run_check(self):
        errors = []
        warnings = []
        shp_path = None
        
        try:
            # Создаём временную папку
            self.temp_dir = tempfile.mkdtemp()
            log_message(f"Создана временная папка: {self.temp_dir}")
            
            # Распаковываем архив
            self.status_label.config(text="Статус: Распаковка архива...")
            self.root.update()
            
            if self.archive_path.lower().endswith('.zip'):
                log_message(f"Распаковка ZIP: {self.archive_path}")
                with zipfile.ZipFile(self.archive_path, 'r') as zf:
                    zf.extractall(self.temp_dir)
                log_message("Распаковка завершена")
            else:
                # Для 7z и rar нужны внешние программы
                msg = f"Поддерживаются только ZIP архивы. Для {self.archive_path} требуется ручная распаковка"
                errors.append(msg)
                log_message(msg, "ERROR")
                self.show_results(errors, warnings)
                return
            
            # Ищем .shp файл
            shp_files = list(Path(self.temp_dir).rglob("*.shp"))
            log_message(f"Найдено .shp файлов: {len(shp_files)}")
            
            if not shp_files:
                errors.append("В архиве не найден .shp файл")
                log_message("В архиве не найден .shp файл", "ERROR")
                self.show_results(errors, warnings)
                return
            
            shp_path = str(shp_files[0])
            log_message(f"Выбран шейп-файл: {shp_path}")
            
            # Запускаем проверку
            self.status_label.config(text="Статус: Проверка шейп-файла...")
            self.root.update()
            
            check_errors, check_warnings = check_shapefile(shp_path)
            errors.extend(check_errors)
            warnings.extend(check_warnings)
            
        except zipfile.BadZipFile:
            msg = "Файл не является ZIP архивом или повреждён"
            errors.append(msg)
            log_message(msg, "ERROR")
        except Exception as e:
            msg = f"Неожиданная ошибка: {str(e)}"
            errors.append(msg)
            log_error(msg, True)
        finally:
            # Очищаем временную папку
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                    log_message(f"Временная папка удалена: {self.temp_dir}")
                except Exception as e:
                    log_message(f"Не удалось удалить временную папку: {e}", "WARNING")
        
        self.show_results(errors, warnings)
    
    def show_results(self, errors, warnings):
        # Создаём окно результатов
        result_window = tk.Toplevel(self.root)
        result_window.title("Результаты проверки шейп-файла")
        result_window.geometry("600x500")
        result_window.minsize(400, 300)
        
        # Делаем окно модальным
        result_window.transient(self.root)
        result_window.grab_set()
        
        # Текстовая область с прокруткой
        text_area = scrolledtext.ScrolledText(result_window, wrap=tk.WORD, font=("Consolas", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настраиваем теги для цветов
        text_area.tag_config("error", foreground="red", font=("Consolas", 10, "bold"))
        text_area.tag_config("warning", foreground="orange")
        text_area.tag_config("success", foreground="green", font=("Consolas", 10, "bold"))
        text_area.tag_config("info", foreground="blue")
        
        # Выводим информацию о логе
        text_area.insert(tk.END, f"Лог файл: {LOG_FILE}\n", "info")
        text_area.insert(tk.END, "=" * 60 + "\n\n", "info")
        
        # Выводим ошибки
        if errors:
            text_area.insert(tk.END, "❌ ОШИБКИ:\n", "error")
            text_area.insert(tk.END, "─" * 50 + "\n", "error")
            for err in errors:
                text_area.insert(tk.END, f"• {err}\n", "error")
            text_area.insert(tk.END, "\n")
        else:
            text_area.insert(tk.END, "✅ ОШИБОК НЕ НАЙДЕНО\n", "success")
        
        # Выводим предупреждения
        if warnings:
            text_area.insert(tk.END, "⚠️ ПРЕДУПРЕЖДЕНИЯ:\n", "warning")
            text_area.insert(tk.END, "─" * 50 + "\n", "warning")
            for warn in warnings:
                text_area.insert(tk.END, f"• {warn}\n", "warning")
        else:
            text_area.insert(tk.END, "\n⚠️ ПРЕДУПРЕЖДЕНИЙ НЕТ\n", "warning")
        
        # Если нет ошибок
        if not errors:
            text_area.insert(tk.END, "\n" + "=" * 60 + "\n", "success")
            text_area.insert(tk.END, "Файл соответствует требованиям\n", "success")
        
        # Кнопки внизу
        button_frame = tk.Frame(result_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def save_report():
            filename = filedialog.asksaveasfilename(
                title="Сохранить отчёт",
                defaultextension=".txt",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"Отчёт о проверке шейп-файла\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Файл: {self.archive_path}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    f.write("ОШИБКИ:\n")
                    if errors:
                        for err in errors:
                            f.write(f"- {err}\n")
                    else:
                        f.write("Ошибок не найдено\n")
                    
                    f.write("\nПРЕДУПРЕЖДЕНИЯ:\n")
                    if warnings:
                        for warn in warnings:
                            f.write(f"- {warn}\n")
                    else:
                        f.write("Предупреждений нет\n")
                    
                    f.write(f"\n\nПолный лог программы: {LOG_FILE}\n")
                
                messagebox.showinfo("Сохранено", f"Отчёт сохранён в:\n{filename}")
        
        def copy_log_path():
            if LOG_FILE:
                self.root.clipboard_clear()
                self.root.clipboard_append(str(LOG_FILE))
                messagebox.showinfo("Скопировано", f"Путь к логу скопирован:\n{LOG_FILE}")
        
        save_btn = tk.Button(button_frame, text="Сохранить отчёт", command=save_report)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        copy_log_btn = tk.Button(button_frame, text="Скопировать путь к логу", command=copy_log_path)
        copy_log_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(button_frame, text="Закрыть", command=result_window.destroy)
        close_btn.pack(side=tk.RIGHT)
        
        # Разблокируем главную кнопку
        self.check_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Статус: Готов", fg="green")
        self