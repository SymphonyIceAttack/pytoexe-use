import sys
import traceback
import os

def show_error_and_wait():
    """Показывает ошибку и ждёт нажатия Enter"""
    error_text = traceback.format_exc()
    
    # Пытаемся показать в GUI окне
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()  # Скрываем главное окно
        messagebox.showerror("Критическая ошибка", f"Произошла ошибка:\n\n{error_text}\n\nПрограмма будет закрыта.")
        root.destroy()
    except:
        # Если GUI не работает, пишем в консоль
        print("=" * 60)
        print("КРИТИЧЕСКАЯ ОШИБКА:")
        print("=" * 60)
        print(error_text)
        print("=" * 60)
        input("Нажмите Enter для выхода...")
    
    sys.exit(1)

# Перехватываем все необработанные исключения
sys.excepthook = lambda exc_type, exc_value, exc_tb: show_error_and_wait()
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import zipfile
import tempfile
import os
import shutil
import re
from pathlib import Path

# Только чистые Python библиотеки (легко упаковываются в exe)
import shapefile
import dbf
import chardet

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

# ========== ФУНКЦИИ ПРОВЕРКИ ==========

def check_crs(prj_path):
    """Проверка системы координат (WGS 84)"""
    if not os.path.exists(prj_path):
        return False, "Отсутствует файл .prj (система координат не определена)"
    
    try:
        with open(prj_path, 'r', encoding='utf-8', errors='ignore') as f:
            prj_content = f.read().lower()
        
        # Проверяем наличие WGS 84 (исключая Web Mercator)
        if 'wgs 84' in prj_content or 'wgs_1984' in prj_content:
            if 'web_mercator' in prj_content or '3857' in prj_content:
                return False, "Система координат: Web Mercator. Должна быть WGS 84 (EPSG:4326)"
            else:
                return True, "OK"
        else:
            # Пытаемся извлечь название СК
            crs_name = "Неизвестная"
            match = re.search(r'geogcs\["([^"]+)"', prj_content)
            if match:
                crs_name = match.group(1)
            return False, f"Система координат: {crs_name}. Должна быть WGS 84 (EPSG:4326)"
    except Exception as e:
        return False, f"Ошибка чтения .prj: {str(e)}"

def check_codepage(shp_path):
    """Проверка кодировки (кириллическая: 1251 или 866)"""
    cpg_path = shp_path.replace('.shp', '.cpg')
    
    if os.path.exists(cpg_path):
        try:
            with open(cpg_path, 'r', encoding='utf-8') as f:
                codepage = f.read().strip().lower()
        except:
            codepage = ""
        
        if codepage in ['1251', 'windows-1251', 'ansi 1251', 'cp1251']:
            return True, "Windows-1251 (допустимо)"
        elif codepage in ['866', 'cp866', 'oem 866']:
            return True, "CP866 (допустимо)"
        else:
            return False, f"Кодировка: {codepage}. Должна быть кириллической: Windows-1251 или CP866"
    else:
        # Пытаемся определить кодировку из .dbf
        dbf_path = shp_path.replace('.shp', '.dbf')
        if os.path.exists(dbf_path):
            try:
                with open(dbf_path, 'rb') as f:
                    raw = f.read(5000)
                    detected = chardet.detect(raw)
                    if detected and detected['encoding']:
                        enc = detected['encoding'].lower()
                        if '1251' in enc or 'windows-1251' in enc:
                            return True, f"Windows-1251 (определено автоматически)"
                        elif '866' in enc or 'cp866' in enc:
                            return True, f"CP866 (определено автоматически)"
                        else:
                            return False, f"Кодировка: {enc}. Должна быть кириллической: Windows-1251 или CP866"
            except:
                pass
        
        return False, "Отсутствует файл .cpg (кодировка не определена)"

def check_self_intersections(shapes):
    """Проверка самопересечений полигонов (упрощённая версия без GDAL)"""
    # Простая проверка: ищем пересечения между частями полигона
    # Для большинства случаев этого достаточно
    import math
    
    def segments_intersect(p1, p2, p3, p4):
        """Проверка пересечения двух отрезков"""
        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        
        d1 = cross(p3, p4, p1)
        d2 = cross(p3, p4, p2)
        d3 = cross(p1, p2, p3)
        d4 = cross(p1, p2, p4)
        
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        return False
    
    for shape in shapes:
        points = shape.points
        if len(points) < 4:
            continue
        
        # Проверяем пересечения между всеми отрезками
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            for j in range(i + 2, len(points) - 1):
                p3 = points[j]
                p4 = points[j + 1]
                if segments_intersect(p1, p2, p3, p4):
                    return True
    return False

def check_geometry(shp_path):
    """Проверка геометрии"""
    errors = []
    warnings = []
    
    try:
        reader = shapefile.Reader(shp_path)
        shapes = reader.shapes()
        
        # Проверка типа геометрии
        shape_type = reader.shapeType
        shape_type_name = {
            1: 'Point',
            3: 'Polyline',
            5: 'Polygon',
            15: 'PolygonZ',
            25: 'PolygonM'
        }.get(shape_type, f'Тип {shape_type}')
        
        if shape_type not in [5, 15, 25]:
            errors.append(f"Тип геометрии — {shape_type_name}. Должен быть Polygon (полигоны)")
        
        # Проверка количества объектов
        if len(shapes) == 0:
            errors.append("Файл не содержит ни одного объекта (0 объектов)")
        
        # Проверка самопересечений
        if check_self_intersections(shapes):
            warnings.append("Обнаружены возможные самопересечения полигонов (упрощённая проверка)")
        
        # Проверка каждого объекта
        for i, shape in enumerate(shapes, 1):
            # Пустая геометрия
            if not shape.points or len(shape.points) == 0:
                errors.append(f"Объект №{i} — пустая геометрия (Null geometry)")
                continue
            
            # Проверка замкнутости полигонов
            for part_idx, part in enumerate(shape.parts):
                start = part
                if part_idx + 1 < len(shape.parts):
                    end = shape.parts[part_idx + 1]
                else:
                    end = len(shape.points)
                
                part_points = shape.points[start:end]
                if len(part_points) >= 3:
                    first = part_points[0]
                    last = part_points[-1]
                    # Проверяем с некоторым допуском (0.000001)
                    if abs(first[0] - last[0]) > 0.000001 or abs(first[1] - last[1]) > 0.000001:
                        errors.append(f"Объект №{i} — полигон не замкнут (первая и последняя точки не совпадают)")
                        break
            
            # Вычисление площади
            try:
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
                
                if area < 0.000001:  # Допуск для нулевой площади
                    warnings.append(f"Объект №{i} — площадь полигона равна 0")
            except:
                pass
            
    except Exception as e:
        errors.append(f"Ошибка чтения геометрии: {str(e)}")
    
    return errors, warnings

def check_fields(dbf_path):
    """Проверка структуры полей"""
    errors = []
    
    try:
        table = dbf.Table(dbf_path, codepage='cp1251')
        table.open()
        
        actual_fields = []
        for field in table.fields:
            if field.name and field.name[0] != '_':  # Пропускаем внутренние поля
                field_type = 'C' if field.type == 'C' else 'N' if field.type == 'N' else 'D' if field.type == 'D' else 'C'
                actual_fields.append((
                    field.name,
                    field_type,
                    field.length,
                    field.decimal_count if hasattr(field, 'decimal_count') else 0
                ))
        
        # Проверка количества полей
        if len(actual_fields) != len(EXPECTED_FIELDS):
            errors.append(f"Количество полей: {len(actual_fields)}, ожидалось: {len(EXPECTED_FIELDS)}")
        
        # Проверка порядка и содержимого
        for i, (exp_name, exp_type, exp_len, exp_prec) in enumerate(EXPECTED_FIELDS):
            if i >= len(actual_fields):
                errors.append(f"Отсутствует обязательное поле \"{exp_name}\"")
                continue
            
            act_name, act_type, act_len, act_prec = actual_fields[i]
            
            if act_name != exp_name:
                errors.append(f"Поле {i+1}: имя \"{act_name}\", ожидалось \"{exp_name}\"")
            
            if act_type != exp_type:
                errors.append(f"Поле \"{exp_name}\": тип {act_type}, ожидался {exp_type}")
            
            if act_len != exp_len:
                errors.append(f"Поле \"{exp_name}\": длина {act_len}, ожидалась {exp_len}")
            
            if act_prec != exp_prec:
                errors.append(f"Поле \"{exp_name}\": точность {act_prec}, ожидалась {exp_prec}")
        
        # Проверка лишних полей
        if len(actual_fields) > len(EXPECTED_FIELDS):
            for i in range(len(EXPECTED_FIELDS), len(actual_fields)):
                errors.append(f"Лишнее поле \"{actual_fields[i][0]}\" — не найдено в эталоне")
        
        table.close()
        
    except Exception as e:
        errors.append(f"Ошибка проверки полей: {str(e)}")
    
    return errors

def check_shapefile(shp_path):
    """Основная функция проверки шейп-файла"""
    all_errors = []
    all_warnings = []
    
    # 1. Проверка системы координат
    prj_path = shp_path.replace('.shp', '.prj')
    crs_ok, crs_msg = check_crs(prj_path)
    if not crs_ok:
        all_errors.append(crs_msg)
    
    # 2. Проверка кодировки
    cp_ok, cp_msg = check_codepage(shp_path)
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
        all_errors.append("Отсутствует файл .dbf (таблица атрибутов)")
    
    return all_errors, all_warnings

# ========== GUI ПРИЛОЖЕНИЯ ==========

class ShapefileCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проверка шейп-файлов")
        self.root.geometry("480x220")
        self.root.resizable(False, False)
        
        self.archive_path = None
        self.temp_dir = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Заголовок
        tk.Label(self.root, text="Выберите ZIP архив с шейп-файлом:", font=("Arial", 10)).pack(pady=(15, 5))
        
        # Поле для пути к файлу
        path_frame = tk.Frame(self.root)
        path_frame.pack(padx=15, pady=(0, 10), fill=tk.X)
        
        self.path_var = tk.StringVar()
        path_entry = tk.Entry(path_frame, textvariable=self.path_var, font=("Arial", 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = tk.Button(path_frame, text="Обзор", command=self.browse_file, width=8)
        browse_btn.pack(side=tk.RIGHT)
        
        # Кнопка проверки (изначально скрыта)
        self.check_btn = tk.Button(self.root, text="Проверить", command=self.start_check, 
                                    state=tk.DISABLED, bg="#4CAF50", fg="white", 
                                    font=("Arial", 10, "bold"), width=15, height=1)
        self.check_btn.pack(pady=(5, 10))
        
        # Статус
        self.status_label = tk.Label(self.root, text="Статус: Файл не выбран", fg="gray", font=("Arial", 9))
        self.status_label.pack(pady=(5, 15))
    
    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Выберите ZIP архив с шейп-файлом",
            filetypes=[
                ("ZIP архивы", "*.zip"),
                ("Все файлы", "*.*")
            ]
        )
        
        if filepath:
            self.archive_path = filepath
            self.path_var.set(filepath)
            self.status_label.config(text="Статус: Файл выбран. Нажмите Проверить", fg="green")
            self.check_btn.config(state=tk.NORMAL)
    
    def start_check(self):
        if not self.archive_path:
            return
        
        # Блокируем кнопку
        self.check_btn.config(state=tk.DISABLED, bg="gray")
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
        
        try:
            # Создаём временную папку
            self.temp_dir = tempfile.mkdtemp()
            
            # Обновляем статус
            self.root.after(0, lambda: self.status_label.config(text="Статус: Распаковка архива..."))
            
            # Распаковываем архив (только ZIP)
            if not self.archive_path.lower().endswith('.zip'):
                errors.append("Поддерживаются только ZIP архивы")
                self.root.after(0, lambda: self.show_results(errors, warnings))
                return
            
            with zipfile.ZipFile(self.archive_path, 'r') as zf:
                zf.extractall(self.temp_dir)
            
            # Ищем .shp файл
            self.root.after(0, lambda: self.status_label.config(text="Статус: Поиск шейп-файла..."))
            
            shp_files = list(Path(self.temp_dir).rglob("*.shp"))
            if not shp_files:
                errors.append("В архиве не найден .shp файл")
                self.root.after(0, lambda: self.show_results(errors, warnings))
                return
            
            shp_path = str(shp_files[0])
            
            # Запускаем проверку
            self.root.after(0, lambda: self.status_label.config(text="Статус: Проверка шейп-файла..."))
            
            check_errors, check_warnings = check_shapefile(shp_path)
            errors.extend(check_errors)
            warnings.extend(check_warnings)
            
        except zipfile.BadZipFile:
            errors.append("Файл не является ZIP архивом или повреждён")
        except Exception as e:
            errors.append(f"Неожиданная ошибка: {str(e)}")
        finally:
            # Очищаем временную папку
            if self.temp_dir and os.path.exists(self.temp_dir):
                try:
                    shutil.rmtree(self.temp_dir)
                except:
                    pass
        
        self.root.after(0, lambda: self.show_results(errors, warnings))
    
    def show_results(self, errors, warnings):
        # Создаём окно результатов
        result_window = tk.Toplevel(self.root)
        result_window.title("Результаты проверки шейп-файла")
        result_window.geometry("700x550")
        result_window.minsize(500, 400)
        
        # Делаем окно модальным
        result_window.transient(self.root)
        result_window.grab_set()
        
        # Текстовая область с прокруткой
        text_area = scrolledtext.ScrolledText(result_window, wrap=tk.WORD, font=("Consolas", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настраиваем теги для цветов
        text_area.tag_config("error", foreground="#cc0000", font=("Consolas", 10, "bold"))
        text_area.tag_config("warning", foreground="#ff8c00")
        text_area.tag_config("success", foreground="#008000", font=("Consolas", 10, "bold"))
        text_area.tag_config("header", font=("Consolas", 11, "bold"))
        
        # Выводим ошибки
        if errors:
            text_area.insert(tk.END, "❌ ОШИБКИ:\n", "header")
            text_area.insert(tk.END, "─" * 60 + "\n", "error")
            for err in errors:
                text_area.insert(tk.END, f"• {err}\n", "error")
            text_area.insert(tk.END, "\n")
        else:
            text_area.insert(tk.END, "✅ ОШИБОК НЕ НАЙДЕНО\n", "success")
            text_area.insert(tk.END, "─" * 60 + "\n", "success")
        
        # Выводим предупреждения
        if warnings:
            text_area.insert(tk.END, "⚠️ ПРЕДУПРЕЖДЕНИЯ:\n", "header")
            text_area.insert(tk.END, "─" * 60 + "\n", "warning")
            for warn in warnings:
                text_area.insert(tk.END, f"• {warn}\n", "warning")
            text_area.insert(tk.END, "\n")
        else:
            text_area.insert(tk.END, "\n⚠️ ПРЕДУПРЕЖДЕНИЙ НЕТ\n", "warning")
        
        # Итог
        text_area.insert(tk.END, "\n" + "=" * 60 + "\n", "header")
        if not errors:
            text_area.insert(tk.END, "Файл соответствует требованиям\n", "success")
        else:
            text_area.insert(tk.END, f"Файл НЕ ПРОШЁЛ проверку. Найдено {len(errors)} ошибок.\n", "error")
        
        text_area.config(state=tk.DISABLED)  # Запрещаем редактирование
        
        # Кнопки внизу
        button_frame = tk.Frame(result_window)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        def save_report():
            from datetime import datetime
            filename = filedialog.asksaveasfilename(
                title="Сохранить отчёт",
                defaultextension=".txt",
                filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
            )
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("ОТЧЁТ О ПРОВЕРКЕ ШЕЙП-ФАЙЛА\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Файл: {self.archive_path}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    f.write("ОШИБКИ:\n")
                    f.write("-" * 40 + "\n")
                    if errors:
                        for err in errors:
                            f.write(f"  • {err}\n")
                    else:
                        f.write("  Ошибок не найдено\n")
                    
                    f.write("\nПРЕДУПРЕЖДЕНИЯ:\n")
                    f.write("-" * 40 + "\n")
                    if warnings:
                        for warn in warnings:
                            f.write(f"  • {warn}\n")
                    else:
                        f.write("  Предупреждений нет\n")
                    
                    f.write("\n" + "=" * 60 + "\n")
                    if not errors:
                        f.write("РЕЗУЛЬТАТ: Файл соответствует требованиям\n")
                    else:
                        f.write(f"РЕЗУЛЬТАТ: Файл НЕ ПРОШЁЛ проверку ({len(errors)} ошибок)\n")
                
                messagebox.showinfo("Сохранено", f"Отчёт сохранён в:\n{filename}")
        
        save_btn = tk.Button(button_frame, text="💾 Сохранить отчёт", command=save_report,
                              bg="#2196F3", fg="white", padx=10)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        close_btn = tk.Button(button_frame, text="Закрыть", command=result_window.destroy,
                               bg="#f44336", fg="white", padx=20)
        close_btn.pack(side=tk.RIGHT)
        
        # Разблокируем главную кнопку
        self.check_btn.config(state=tk.NORMAL, bg="#4CAF50")
        self.status_label.config(text="Статус: Готов", fg="green")

# ========== ЗАПУСК ==========

if __name__ == "__main__":
    root = tk.Tk()
    app = ShapefileCheckerApp(root)
    root.mainloop()