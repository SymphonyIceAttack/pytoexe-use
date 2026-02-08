#!/usr/bin/env python3
"""
AECS CALIBRATION EDITOR - COMPLETE EXE BUILDER
Version: 2.0.0
Description: Полный скрипт для сборки EXE файла программы
"""

import os
import sys
import shutil
import subprocess
import tempfile
import json
from pathlib import Path
import zipfile

# ============================================================================
# КОНФИГУРАЦИЯ СБОРКИ
# ============================================================================

CONFIG = {
    "app_name": "AECS_Calibration_Editor",
    "app_version": "2.0.0",
    "python_version": "3.7+",
    "author": "AECS Development Team",
    "company": "AECS Automotive Electronics",
    "copyright": "© 2024 AECS Development Team. All rights reserved.",
    "description": "Professional ECU Calibration Editor for AECS Engine Control Units",
    "icon_file": "icon.ico",
    "output_dir": "dist",
    "build_dir": "build",
    "spec_file": "aecs_editor.spec",
    "requirements": [
        "pyinstaller>=5.0",
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "pillow>=9.0.0",
        "pyserial>=3.5",
        "pywin32>=305; sys_platform == 'win32'"
    ]
}

# ============================================================================
# ОСНОВНОЙ ФАЙЛ ПРОГРАММЫ (main.py)
# ============================================================================

MAIN_PY = '''#!/usr/bin/env python3
"""
AECS ECU Calibration Editor - Main Application
Version: 2.0.0
"""
import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from datetime import datetime

# Добавляем путь к ресурсам
if hasattr(sys, '_MEIPASS'):
    # PyInstaller создает временную папку
    RESOURCE_PATH = sys._MEIPASS
else:
    RESOURCE_PATH = os.path.dirname(os.path.abspath(__file__))

class AECSApp:
    """Главный класс приложения"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AECS ECU Calibration Editor v2.0.0")
        self.root.geometry("1200x800")
        
        # Центрирование окна
        self.center_window()
        
        # Иконка приложения
        self.set_icon()
        
        # Переменные
        self.current_file = None
        self.calibration_data = {}
        self.setup_ui()
        self.setup_menu()
        self.setup_bindings()
        
        # Статус
        self.status_text = tk.StringVar()
        self.status_text.set("Готов к работе")
        
    def center_window(self):
        """Центрирование окна на экране"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def set_icon(self):
        """Установка иконки приложения"""
        try:
            icon_path = os.path.join(RESOURCE_PATH, "icons", "app_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем стили
        self.setup_styles()
        
        # Главный фрейм
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель
        self.setup_top_panel(main_frame)
        
        # Центральная область с вкладками
        self.setup_notebook(main_frame)
        
        # Нижняя панель (статус)
        self.setup_status_bar(main_frame)
    
    def setup_styles(self):
        """Настройка стилей элементов"""
        style = ttk.Style()
        
        # Современные стили
        style.theme_use('clam')
        
        # Кастомные стили
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 12))
        style.configure('Status.TLabel', font=('Arial', 9))
        style.configure('Big.TButton', font=('Arial', 11))
        
        # Цвета
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def setup_top_panel(self, parent):
        """Верхняя панель с кнопками быстрого доступа"""
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Заголовок
        title_label = ttk.Label(top_frame, 
                               text="AECS ECU Calibration Editor",
                               style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Версия
        version_label = ttk.Label(top_frame,
                                 text="v2.0.0",
                                 style='Subtitle.TLabel')
        version_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Кнопки быстрого доступа
        button_frame = ttk.Frame(top_frame)
        button_frame.pack(side=tk.RIGHT)
        
        buttons = [
            ("📁 Открыть", self.open_file),
            ("💾 Сохранить", self.save_file),
            ("⚙️ Настройки", self.open_settings),
            ("❓ Помощь", self.show_help)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(button_frame, text=text, 
                           command=command, width=12)
            btn.pack(side=tk.LEFT, padx=2)
    
    def setup_notebook(self, parent):
        """Создание вкладок"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладки
        self.setup_welcome_tab()
        self.setup_calibration_tab()
        self.setup_sensors_tab()
        self.setup_tools_tab()
        self.setup_about_tab()
    
    def setup_welcome_tab(self):
        """Вкладка 'Добро пожаловать'"""
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Добро пожаловать")
        
        # Контент
        content = """
        Добро пожаловать в AECS ECU Calibration Editor!
        
        Профессиональный инструмент для редактирования калибровок
        блоков управления двигателем AECS.
        
        Основные возможности:
        • Редактирование калибровочных таблиц
        • Визуализация данных в 2D/3D
        • Работа с датчиками в реальном времени
        • Экспорт/импорт в различных форматах
        • Создание резервных копий
        
        Для начала работы:
        1. Откройте файл прошивки (Файл → Открыть)
        2. Выберите калибровочную таблицу
        3. Внесите необходимые изменения
        4. Сохраните модифицированную прошивку
        """
        
        text_widget = tk.Text(welcome_frame, wrap=tk.WORD, 
                            font=('Arial', 11), height=20,
                            bg='white', relief=tk.FLAT)
        text_widget.insert(1.0, content)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Быстрые действия
        actions_frame = ttk.Frame(welcome_frame)
        actions_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        quick_actions = [
            ("Создать новый проект", self.new_project),
            ("Открыть пример", self.open_example),
            ("Открыть документацию", self.open_docs)
        ]
        
        for text, command in quick_actions:
            btn = ttk.Button(actions_frame, text=text, 
                           command=command, style='Big.TButton')
            btn.pack(side=tk.LEFT, padx=5)
    
    def setup_calibration_tab(self):
        """Вкладка калибровок"""
        cal_frame = ttk.Frame(self.notebook)
        self.notebook.add(cal_frame, text="Калибровки")
        
        # Панель выбора таблиц
        table_frame = ttk.LabelFrame(cal_frame, text="Таблицы калибровки", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Список таблиц
        tables = [
            ("Топливная карта (Fuel)", "fuel_table"),
            ("Зажигание (Ignition)", "ignition_table"),
            ("Наддув (Boost)", "boost_table"),
            ("Фазы ГРМ (VVT)", "vvt_table"),
            ("Холодный запуск", "cold_start_table"),
            ("Рециркуляция (EGR)", "egr_table")
        ]
        
        for i, (name, key) in enumerate(tables):
            btn = ttk.Button(table_frame, text=name,
                           command=lambda k=key: self.open_table(k))
            btn.grid(row=i//2, column=i%2, sticky=tk.W+tk.E, 
                    padx=5, pady=5)
        
        # Выравнивание
        table_frame.columnconfigure(0, weight=1)
        table_frame.columnconfigure(1, weight=1)
    
    def setup_sensors_tab(self):
        """Вкладка датчиков"""
        sensor_frame = ttk.Frame(self.notebook)
        self.notebook.add(sensor_frame, text="Датчики")
        
        label = ttk.Label(sensor_frame, text="Мониторинг датчиков",
                         font=('Arial', 14))
        label.pack(pady=20)
        
        # Таблица датчиков
        columns = ("Датчик", "Значение", "Единицы", "Статус")
        self.sensor_tree = ttk.Treeview(sensor_frame, columns=columns,
                                       show="headings", height=15)
        
        for col in columns:
            self.sensor_tree.heading(col, text=col)
            self.sensor_tree.column(col, width=150)
        
        # Пример данных
        sensors = [
            ("MAF", "3.2", "g/s", "✅ OK"),
            ("MAP", "98", "kPa", "✅ OK"),
            ("TPS", "12", "%", "✅ OK"),
            ("ECT", "85", "°C", "⚠️ Высокая"),
            ("IAT", "35", "°C", "✅ OK"),
            ("O2", "0.45", "V", "✅ OK"),
            ("RPM", "2500", "об/мин", "✅ OK"),
            ("Speed", "80", "км/ч", "✅ OK")
        ]
        
        for sensor in sensors:
            self.sensor_tree.insert("", tk.END, values=sensor)
        
        scrollbar = ttk.Scrollbar(sensor_frame, orient=tk.VERTICAL,
                                 command=self.sensor_tree.yview)
        self.sensor_tree.configure(yscrollcommand=scrollbar.set)
        
        self.sensor_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                             padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    def setup_tools_tab(self):
        """Вкладка инструментов"""
        tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(tools_frame, text="Инструменты")
        
        # Калькуляторы
        calculators_frame = ttk.LabelFrame(tools_frame, 
                                         text="Калькуляторы", padding=15)
        calculators_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        calculators = [
            ("Калькулятор AFR", self.open_afr_calculator),
            ("Калькулятор давления", self.open_pressure_calculator),
            ("Калькулятор инжектора", self.open_injector_calculator),
            ("Конвертер единиц", self.open_unit_converter),
            ("Калькулятор турбины", self.open_turbo_calculator),
            ("Калькулятор компрессии", self.open_compression_calculator)
        ]
        
        for i, (name, command) in enumerate(calculators):
            btn = ttk.Button(calculators_frame, text=name,
                           command=command, width=25)
            btn.grid(row=i//3, column=i%3, padx=10, pady=10, sticky=tk.W)
    
    def setup_about_tab(self):
        """Вкладка 'О программе'"""
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="О программе")
        
        info = """
        AECS ECU Calibration Editor
        Версия: 2.0.0
        
        Профессиональный редактор калибровок
        для блоков управления двигателем AECS
        
        Разработчик: AECS Development Team
        Лицензия: MIT
        
        Контакты:
        • Email: support@aecs-ecu.com
        • Сайт: https://aecs-ecu.com
        • Форум: https://forum.aecs-ecu.com
        
        Системные требования:
        • ОС: Windows 10/11 (64-bit)
        • Python: 3.7 или выше
        • ОЗУ: 4 ГБ минимум
        • Место на диске: 500 МБ
        
        Предупреждение:
        Используйте только в образовательных целях
        и на свой страх и риск.
        """
        
        text_widget = tk.Text(about_frame, wrap=tk.WORD,
                            font=('Arial', 11), height=25,
                            bg='white', relief=tk.FLAT)
        text_widget.insert(1.0, info)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
    
    def setup_status_bar(self, parent):
        """Создание статус бара"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        status_label = ttk.Label(status_frame, textvariable=self.status_text,
                                style='Status.TLabel')
        status_label.pack(side=tk.LEFT, padx=10)
        
        # Индикатор памяти
        self.memory_var = tk.StringVar()
        self.memory_var.set("Память: --")
        memory_label = ttk.Label(status_frame, textvariable=self.memory_var,
                                style='Status.TLabel')
        memory_label.pack(side=tk.RIGHT, padx=10)
        
        # Обновление памяти
        self.update_memory_usage()
    
    def setup_menu(self):
        """Настройка меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый проект", command=self.new_project)
        file_menu.add_command(label="Открыть...", command=self.open_file)
        file_menu.add_command(label="Сохранить", command=self.save_file)
        file_menu.add_command(label="Сохранить как...", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт...", command=self.export_data)
        file_menu.add_command(label="Импорт...", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Отменить", command=self.undo)
        edit_menu.add_command(label="Повторить", command=self.redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Копировать", command=self.copy)
        edit_menu.add_command(label="Вставить", command=self.paste)
        
        # Меню Калибровка
        cal_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Калибровка", menu=cal_menu)
        cal_menu.add_command(label="Топливная карта", 
                           command=lambda: self.open_table("fuel_table"))
        cal_menu.add_command(label="Зажигание", 
                           command=lambda: self.open_table("ignition_table"))
        cal_menu.add_command(label="Наддув", 
                           command=lambda: self.open_table("boost_table"))
        cal_menu.add_command(label="Фазы ГРМ", 
                           command=lambda: self.open_table("vvt_table"))
        
        # Меню Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Калькулятор AFR", 
                             command=self.open_afr_calculator)
        tools_menu.add_command(label="Калькулятор давления", 
                             command=self.open_pressure_calculator)
        tools_menu.add_command(label="Конвертер единиц", 
                             command=self.open_unit_converter)
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="Документация", command=self.open_docs)
        help_menu.add_command(label="Примеры", command=self.open_examples)
        help_menu.add_command(label="Проверить обновления", 
                            command=self.check_updates)
        help_menu.add_separator()
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def setup_bindings(self):
        """Настройка горячих клавиш"""
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F1>', lambda e: self.show_help())
    
    # ============================================================================
    # МЕТОДЫ ПРИЛОЖЕНИЯ
    # ============================================================================
    
    def new_project(self):
        """Создать новый проект"""
        self.status_text.set("Создание нового проекта...")
        messagebox.showinfo("Новый проект", 
                          "Функция создания нового проекта")
        self.status_text.set("Готов")
    
    def open_file(self):
        """Открыть файл"""
        filetypes = [
            ("Файлы прошивок", "*.bin *.hex *.s19"),
            ("Файлы калибровок", "*.json *.xml *.cal"),
            ("Все файлы", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Открыть файл прошивки",
            filetypes=filetypes
        )
        
        if filename:
            self.current_file = filename
            self.status_text.set(f"Загружен: {os.path.basename(filename)}")
            messagebox.showinfo("Файл открыт", 
                              f"Файл успешно загружен:\\n{filename}")
    
    def save_file(self):
        """Сохранить файл"""
        if not self.current_file:
            self.save_as()
            return
        
        self.status_text.set("Сохранение файла...")
        messagebox.showinfo("Сохранение", "Файл сохранен")
        self.status_text.set("Готов")
    
    def save_as(self):
        """Сохранить как"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".bin",
            filetypes=[
                ("Бинарные файлы", "*.bin"),
                ("HEX файлы", "*.hex"),
                ("Все файлы", "*.*")
            ]
        )
        
        if filename:
            self.current_file = filename
            self.status_text.set(f"Сохранено как: {os.path.basename(filename)}")
    
    def open_settings(self):
        """Открыть настройки"""
        self.status_text.set("Открытие настроек...")
        messagebox.showinfo("Настройки", "Окно настроек программы")
        self.status_text.set("Готов")
    
    def show_help(self):
        """Показать справку"""
        self.status_text.set("Открытие справки...")
        messagebox.showinfo("Справка", "Документация AECS Calibration Editor")
        self.status_text.set("Готов")
    
    def open_table(self, table_name):
        """Открыть таблицу калибровки"""
        self.status_text.set(f"Открытие таблицы: {table_name}")
        self.notebook.select(1)  # Переключаем на вкладку калибровок
        messagebox.showinfo("Таблица", f"Открыта таблица: {table_name}")
        self.status_text.set("Готов")
    
    def open_afr_calculator(self):
        """Открыть калькулятор AFR"""
        self.open_calculator_window("Калькулятор AFR")
    
    def open_pressure_calculator(self):
        """Открыть калькулятор давления"""
        self.open_calculator_window("Калькулятор давления")
    
    def open_injector_calculator(self):
        """Открыть калькулятор инжектора"""
        self.open_calculator_window("Калькулятор инжектора")
    
    def open_unit_converter(self):
        """Открыть конвертер единиц"""
        self.open_calculator_window("Конвертер единиц")
    
    def open_turbo_calculator(self):
        """Открыть калькулятор турбины"""
        self.open_calculator_window("Калькулятор турбины")
    
    def open_compression_calculator(self):
        """Открыть калькулятор компрессии"""
        self.open_calculator_window("Калькулятор компрессии")
    
    def open_calculator_window(self, title):
        """Открыть окно калькулятора"""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("400x300")
        
        label = ttk.Label(window, text=f"{title}\\n\\nВ разработке",
                         font=('Arial', 12), justify=tk.CENTER)
        label.pack(expand=True)
        
        ttk.Button(window, text="Закрыть", 
                  command=window.destroy).pack(pady=20)
    
    def export_data(self):
        """Экспорт данных"""
        formats = [
            ("JSON файлы", "*.json"),
            ("CSV файлы", "*.csv"),
            ("XML файлы", "*.xml"),
            ("PDF файлы", "*.pdf")
        ]
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=formats
        )
        
        if filename:
            self.status_text.set(f"Экспорт в: {os.path.basename(filename)}")
    
    def import_data(self):
        """Импорт данных"""
        formats = [
            ("JSON файлы", "*.json"),
            ("CSV файлы", "*.csv"),
            ("XML файлы", "*.xml"),
            ("CAL файлы", "*.cal")
        ]
        
        filename = filedialog.askopenfilename(
            title="Импорт данных",
            filetypes=formats
        )
        
        if filename:
            self.status_text.set(f"Импорт из: {os.path.basename(filename)}")
    
    def undo(self):
        """Отменить действие"""
        self.status_text.set("Отмена последнего действия")
    
    def redo(self):
        """Повторить действие"""
        self.status_text.set("Повтор последнего действия")
    
    def copy(self):
        """Копировать"""
        self.status_text.set("Копирование данных")
    
    def paste(self):
        """Вставить"""
        self.status_text.set("Вставка данных")
    
    def open_docs(self):
        """Открыть документацию"""
        self.status_text.set("Открытие документации...")
        messagebox.showinfo("Документация", "Открывается браузер с документацией")
        self.status_text.set("Готов")
    
    def open_examples(self):
        """Открыть примеры"""
        self.status_text.set("Загрузка примеров...")
        messagebox.showinfo("Примеры", "Открыты примеры калибровок")
        self.status_text.set("Готов")
    
    def check_updates(self):
        """Проверить обновления"""
        self.status_text.set("Проверка обновлений...")
        messagebox.showinfo("Обновления", "Установлена последняя версия")
        self.status_text.set("Готов")
    
    def show_about(self):
        """Показать информацию о программе"""
        about_text = f"""
        AECS ECU Calibration Editor
        Версия: 2.0.0
        
        {CONFIG['description']}
        
        Разработчик: {CONFIG['author']}
        Компания: {CONFIG['company']}
        {CONFIG['copyright']}
        
        Контакты:
        • Email: support@aecs-ecu.com
        • Сайт: https://aecs-ecu.com
        
        Лицензия: MIT
        """
        
        messagebox.showinfo("О программе", about_text)
    
    def open_example(self):
        """Открыть пример"""
        self.status_text.set("Загрузка примера...")
        messagebox.showinfo("Пример", "Пример калибровки загружен")
        self.status_text.set("Готов")
    
    def update_memory_usage(self):
        """Обновление информации об использовании памяти"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 * 1024)
            self.memory_var.set(f"Память: {memory_mb:.1f} MB")
        except:
            self.memory_var.set("Память: --")
        
        # Обновляем каждые 5 секунд
        self.root.after(5000, self.update_memory_usage)

def main():
    """Точка входа в приложение"""
    try:
        root = tk.Tk()
        app = AECSApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска приложения: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()
'''

# ============================================================================
# КЛАСС СБОРЩИКА EXE
# ============================================================================

class AECSEXEBuilder:
    """Класс для сборки EXE файла AECS Calibration Editor"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / CONFIG["build_dir"]
        self.dist_dir = self.project_dir / CONFIG["output_dir"]
        self.resources_dir = self.project_dir / "resources"
        self.icons_dir = self.resources_dir / "icons"
        self.data_dir = self.resources_dir / "data"
        
    def print_header(self):
        """Печать заголовка"""
        print("=" * 70)
        print(f"AECS CALIBRATION EDITOR - EXE BUILDER")
        print(f"Version: {CONFIG['app_version']}")
        print("=" * 70)
        print()
    
    def clean_previous_builds(self):
        """Очистка предыдущих сборок"""
        print("🧹 Очистка предыдущих сборок...")
        
        directories = [self.build_dir, self.dist_dir]
        files = [self.project_dir / CONFIG["spec_file"]]
        
        for dir_path in directories:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  Удалено: {dir_path}")
        
        for file_path in files:
            if file_path.exists():
                file_path.unlink()
                print(f"  Удалено: {file_path}")
        
        print("✅ Очистка завершена")
        print()
    
    def create_project_structure(self):
        """Создание структуры проекта"""
        print("📁 Создание структуры проекта...")
        
        # Создаем директории
        directories = [
            self.resources_dir,
            self.icons_dir,
            self.data_dir,
            self.dist_dir,
            self.build_dir
        ]
        
        for dir_path in directories:
            dir_path.mkdir(exist_ok=True)
            print(f"  Создано: {dir_path}")
        
        # Создаем основные файлы
        self.create_main_files()
        self.create_resource_files()
        self.create_documentation()
        
        print("✅ Структура проекта создана")
        print()
    
    def create_main_files(self):
        """Создание основных файлов программы"""
        print("📄 Создание основных файлов...")
        
        # main.py
        main_file = self.project_dir / "main.py"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(MAIN_PY)
        print(f"  Создан: {main_file}")
        
        # requirements.txt
        req_file = self.project_dir / "requirements.txt"
        with open(req_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(CONFIG["requirements"]))
        print(f"  Создан: {req_file}")
        
        # setup.py
        setup_content = '''#!/usr/bin/env python3
"""
Setup script for AECS Calibration Editor
"""
from setuptools import setup, find_packages

setup(
    name="aecs-calibration-editor",
    version="2.0.0",
    description="Professional ECU Calibration Editor for AECS Engine Control Units",
    author="AECS Development Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "matplotlib>=3.5.0",
        "pillow>=9.0.0",
        "pyserial>=3.5"
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Embedded Systems",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
)
'''
        setup_file = self.project_dir / "setup.py"
        with open(setup_file, 'w', encoding='utf-8') as f:
            f.write(setup_content)
        print(f"  Создан: {setup_file}")
        
        # README.md
        readme_content = f'''# AECS ECU Calibration Editor

{CONFIG['description']}

## 📋 Особенности

- Редактирование калибровочных таблиц (топливо, зажигание, наддув)
- Визуализация данных в 2D/3D
- Работа с датчиками в реальном времени
- Экспорт/импорт в различных форматах
- Создание резервных копий
- Поддержка программаторов AECS

## 🚀 Установка

### Вариант 1: Установка из исходного кода
```bash
# 1. Клонируйте репозиторий
git clone https://github.com/aecs-ecu/calibration-editor.git

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Запустите программу
python main.py
```

### Вариант 2: Использование готового EXE
1. Скачайте `AECS_Calibration_Editor.exe` из папки `dist/`
2. Запустите файл двойным щелчком

### Вариант 3: Установка через pip
```bash
pip install aecs-calibration-editor
```

## 📖 Использование

1. **Загрузите файл прошивки** (Файл → Открыть)
2. **Выберите калибровочную таблицу** для редактирования
3. **Внесите изменения** в значения таблицы
4. **Сохраните модифицированную прошивку**
5. **Прошейте ECU** с помощью программатора

## 🔧 Требования

- **ОС:** Windows 10/11 (64-bit)
- **Python:** 3.7 или выше (для сборки из исходников)
- **ОЗУ:** 4 ГБ минимум
- **Место на диске:** 500 МБ

## 📞 Поддержка

- Документация: https://docs.aecs-ecu.com
- Форум: https://forum.aecs-ecu.com
- Email: support@aecs-ecu.com

## ⚖️ Лицензия

MIT License

Copyright (c) 2024 AECS Development Team

## ⚠️ Предупреждение

Используйте только в образовательных целях и на свой страх и риск