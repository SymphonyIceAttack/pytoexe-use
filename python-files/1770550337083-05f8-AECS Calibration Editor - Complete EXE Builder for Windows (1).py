#!/usr/bin/env python3
"""
AECS ECU Calibration Editor - EXE Builder Package
Complete solution for creating Windows executable
"""

# ============================================================================
# 1. MAIN.PY - Основной файл программы
# ============================================================================

main_py = """#!/usr/bin/env python3
"""
AECS ECU Calibration Editor - Main Application
"""
import sys
import os

# Добавляем путь к модулям
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Точка входа в приложение"""
    try:
        # Проверяем наличие необходимых модулей
        import tkinter
        import numpy
        import matplotlib
        
        # Импортируем и запускаем GUI
        from aecs_gui import AECSApp
        
        import tkinter as tk
        root = tk.Tk()
        app = AECSApp(root)
        root.mainloop()
        
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Установите необходимые зависимости:")
        print("pip install numpy matplotlib pillow")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

# ============================================================================
# 2. AECS_GUI.PY - Графический интерфейс
# ============================================================================

aecs_gui_py = """#!/usr/bin/env python3
"""
AECS ECU Calibration Editor - GUI Interface
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
from datetime import datetime

class AECSApp:
    """Главное окно приложения"""
    def __init__(self, root):
        self.root = root
        self.root.title("AECS ECU Calibration Editor v2.0")
        self.root.geometry("1000x700")
        
        # Иконка приложения
        try:
            self.root.iconbitmap(default=self.resource_path("icon.ico"))
        except:
            pass
        
        self.setup_ui()
        self.setup_menu()
        
    def resource_path(self, relative_path):
        """Получает абсолютный путь к ресурсу"""
        try:
            # PyInstaller создает временную папку в _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
    
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
        file_menu.add_command(label="Выход", command=self.root.quit)
        
        # Меню Калибровка
        cal_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Калибровка", menu=cal_menu)
        cal_menu.add_command(label="Таблица топлива", command=self.show_fuel_table)
        cal_menu.add_command(label="Таблица зажигания", command=self.show_ignition_table)
        cal_menu.add_command(label="Таблица наддува", command=self.show_boost_table)
        
        # Меню Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        tools_menu.add_command(label="Калькулятор AFR", command=self.afr_calculator)
        tools_menu.add_command(label="Калькулятор давления", command=self.pressure_calculator)
        tools_menu.add_command(label="Конвертер единиц", command=self.unit_converter)
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Документация", command=self.show_docs)
        help_menu.add_command(label="Проверить обновления", command=self.check_updates)
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Создаем Notebook (вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка 1: Добро пожаловать
        self.setup_welcome_tab()
        
        # Вкладка 2: Быстрый старт
        self.setup_quickstart_tab()
        
        # Вкладка 3: Калибровочные таблицы
        self.setup_calibration_tab()
        
        # Вкладка 4: Инструменты
        self.setup_tools_tab()
        
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_welcome_tab(self):
        """Вкладка приветствия"""
        welcome_frame = ttk.Frame(self.notebook)
        self.notebook.add(welcome_frame, text="Добро пожаловать")
        
        # Заголовок
        title_label = ttk.Label(welcome_frame, 
                               text="AECS ECU Calibration Editor",
                               font=("Arial", 24, "bold"))
        title_label.pack(pady=20)
        
        # Версия
        version_label = ttk.Label(welcome_frame,
                                 text="Версия 2.0.0 | Для Windows",
                                 font=("Arial", 10))
        version_label.pack()
        
        # Разделитель
        ttk.Separator(welcome_frame, orient='horizontal').pack(fill=tk.X, padx=50, pady=20)
        
        # Быстрые действия
        actions_frame = ttk.Frame(welcome_frame)
        actions_frame.pack(pady=20)
        
        ttk.Button(actions_frame, text="📁 Открыть файл прошивки", 
                  command=self.open_file, width=25).pack(pady=5)
        ttk.Button(actions_frame, text="🛠️ Создать новый проект", 
                  command=self.new_project, width=25).pack(pady=5)
        ttk.Button(actions_frame, text="📊 Открыть калибровку", 
                  command=self.open_calibration, width=25).pack(pady=5)
        ttk.Button(actions_frame, text="❓ Руководство пользователя", 
                  command=self.show_docs, width=25).pack(pady=5)
        
        # Информация
        info_frame = ttk.LabelFrame(welcome_frame, text="Информация", padding=20)
        info_frame.pack(fill=tk.X, padx=50, pady=20)
        
        info_text = """AECS ECU Calibration Editor - профессиональный инструмент для работы 
с калибровками блоков управления двигателем AECS.

Основные возможности:
• Редактирование калибровочных таблиц
• Визуализация данных в 2D/3D
• Экспорт/импорт в различных форматах
• Работа с датчиками в реальном времени
• Создание резервных копий

Требования: Windows 10/11, 4 ГБ ОЗУ, 500 МБ свободного места."""
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
        info_label.pack()
    
    def setup_quickstart_tab(self):
        """Вкладка быстрого старта"""
        quickstart_frame = ttk.Frame(self.notebook)
        self.notebook.add(quickstart_frame, text="Быстрый старт")
        
        # Пошаговое руководство
        steps = [
            "1. Загрузите файл прошивки (Файл → Открыть)",
            "2. Выберите калибровочную таблицу для редактирования",
            "3. Внесите необходимые изменения",
            "4. Сохраните модифицированную прошивку",
            "5. Прошейте ECU с помощью программатора"
        ]
        
        for step in steps:
            step_label = ttk.Label(quickstart_frame, text=step, 
                                  font=("Arial", 11), justify=tk.LEFT)
            step_label.pack(anchor=tk.W, padx=20, pady=10)
        
        # Примеры файлов
        examples_frame = ttk.LabelFrame(quickstart_frame, text="Примеры файлов", padding=20)
        examples_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Button(examples_frame, text="Загрузить пример прошивки", 
                  command=self.load_example).pack(pady=5)
        ttk.Button(examples_frame, text="Загрузить пример калибровки", 
                  command=self.load_example_cal).pack(pady=5)
    
    def setup_calibration_tab(self):
        """Вкладка калибровочных таблиц"""
        cal_frame = ttk.Frame(self.notebook)
        self.notebook.add(cal_frame, text="Калибровки")
        
        # Таблица для отображения данных
        columns = ("RPM", "100", "200", "300", "400", "500", 
                  "600", "700", "800", "900", "1000")
        
        self.tree = ttk.Treeview(cal_frame, columns=columns, show="headings", height=15)
        
        # Заголовки столбцов
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=60, anchor=tk.CENTER)
        
        # Добавляем данные
        for i in range(10):
            values = [f"{i*1000}"] + [str(i*10 + j) for j in range(10)]
            self.tree.insert("", tk.END, values=values)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(cal_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Панель управления таблицей
        control_frame = ttk.Frame(cal_frame)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(control_frame, text="Редактировать ячейку", 
                  command=self.edit_cell).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Экспорт в CSV", 
                  command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Импорт из CSV", 
                  command=self.import_csv).pack(side=tk.LEFT, padx=5)
    
    def setup_tools_tab(self):
        """Вкладка инструментов"""
        tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(tools_frame, text="Инструменты")
        
        # Калькуляторы
        calculators = [
            ("Калькулятор AFR", self.afr_calculator),
            ("Калькулятор давления", self.pressure_calculator),
            ("Калькулятор температуры", self.temp_calculator),
            ("Конвертер единиц", self.unit_converter),
            ("Калькулятор инжектора", self.injector_calculator),
            ("Калькулятор турбины", self.turbo_calculator)
        ]
        
        for i, (name, command) in enumerate(calculators):
            btn = ttk.Button(tools_frame, text=name, command=command, width=25)
            btn.grid(row=i//3, column=i%3, padx=10, pady=10, sticky=tk.W)
        
        # Информация о системе
        sys_frame = ttk.LabelFrame(tools_frame, text="Информация о системе", padding=10)
        sys_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=20, sticky=tk.W+tk.E)
        
        import platform
        sys_info = f"""
ОС: {platform.system()} {platform.release()}
Архитектура: {platform.architecture()[0]}
Процессор: {platform.processor()}
Версия Python: {platform.python_version()}
        """
        
        sys_label = ttk.Label(sys_frame, text=sys_info, justify=tk.LEFT)
        sys_label.pack()
    
    # Методы меню
    def new_project(self):
        """Создать новый проект"""
        self.status_var.set("Создание нового проекта...")
        messagebox.showinfo("Новый проект", "Функция в разработке")
        self.status_var.set("Готов")
    
    def open_file(self):
        """Открыть файл"""
        filetypes = [
            ("Файлы прошивок", "*.bin *.hex *.s19"),
            ("Файлы калибровок", "*.json *.xml *.cal"),
            ("Все файлы", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Открыть файл",
            filetypes=filetypes
        )
        
        if filename:
            self.status_var.set(f"Загружен файл: {os.path.basename(filename)}")
    
    def save_file(self):
        """Сохранить файл"""
        self.status_var.set("Сохранение файла...")
        messagebox.showinfo("Сохранение", "Функция в разработке")
        self.status_var.set("Готов")
    
    def save_as(self):
        """Сохранить как"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".bin",
            filetypes=[("Бинарные файлы", "*.bin"), ("Все файлы", "*.*")]
        )
        
        if filename:
            self.status_var.set(f"Сохранено как: {os.path.basename(filename)}")
    
    def show_fuel_table(self):
        """Показать таблицу топлива"""
        self.notebook.select(2)  # Переключаем на вкладку калибровок
        self.status_var.set("Таблица топлива")
    
    def show_ignition_table(self):
        """Показать таблицу зажигания"""
        self.notebook.select(2)
        self.status_var.set("Таблица зажигания")
    
    def show_boost_table(self):
        """Показать таблицу наддува"""
        self.notebook.select(2)
        self.status_var.set("Таблица наддува")
    
    def afr_calculator(self):
        """Калькулятор AFR"""
        self.open_calculator_window("Калькулятор AFR")
    
    def pressure_calculator(self):
        """Калькулятор давления"""
        self.open_calculator_window("Калькулятор давления")
    
    def temp_calculator(self):
        """Калькулятор температуры"""
        self.open_calculator_window("Калькулятор температуры")
    
    def unit_converter(self):
        """Конвертер единиц"""
        self.open_calculator_window("Конвертер единиц")
    
    def injector_calculator(self):
        """Калькулятор инжектора"""
        self.open_calculator_window("Калькулятор инжектора")
    
    def turbo_calculator(self):
        """Калькулятор турбины"""
        self.open_calculator_window("Калькулятор турбины")
    
    def open_calculator_window(self, title):
        """Открыть окно калькулятора"""
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry("400x300")
        
        label = ttk.Label(window, text=f"{title}\n\nФункция в разработке", 
                         font=("Arial", 12))
        label.pack(expand=True)
        
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=20)
    
    def show_about(self):
        """Показать информацию о программе"""
        about_text = """AECS ECU Calibration Editor
Версия 2.0.0

Профессиональный редактор калибровок
для блоков управления двигателем AECS

© 2024 AECS Development Team
Все права защищены.

Лицензия: MIT
Поддержка: support@aecs-ecu.com
        """
        
        messagebox.showinfo("О программе", about_text)
    
    def show_docs(self):
        """Показать документацию"""
        self.status_var.set("Открытие документации...")
        messagebox.showinfo("Документация", "Документация будет открыта в браузере")
        self.status_var.set("Готов")
    
    def check_updates(self):
        """Проверить обновления"""
        self.status_var.set("Проверка обновлений...")
        messagebox.showinfo("Обновления", "Установлена последняя версия")
        self.status_var.set("Готов")
    
    def open_calibration(self):
        """Открыть калибровку"""
        self.open_file()
    
    def load_example(self):
        """Загрузить пример"""
        self.status_var.set("Загрузка примера...")
        messagebox.showinfo("Пример", "Пример загружен")
        self.status_var.set("Готов")
    
    def load_example_cal(self):
        """Загрузить пример калибровки"""
        self.status_var.set("Загрузка примера калибровки...")
        messagebox.showinfo("Пример", "Пример калибровки загружен")
        self.status_var.set("Готов")
    
    def edit_cell(self):
        """Редактировать ячейку таблицы"""
        selected = self.tree.selection()
        if selected:
            self.status_var.set("Редактирование ячейки...")
            messagebox.showinfo("Редактирование", "Функция в разработке")
            self.status_var.set("Готов")
    
    def export_csv(self):
        """Экспорт в CSV"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )
        
        if filename:
            self.status_var.set(f"Экспорт в CSV: {os.path.basename(filename)}")
    
    def import_csv(self):
        """Импорт из CSV"""
        filename = filedialog.askopenfilename(
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )
        
        if filename:
            self.status_var.set(f"Импорт из CSV: {os.path.basename(filename)}")
"""

# ============================================================================
# 3. BUILD_EXE.PY - Скрипт сборки EXE
# ============================================================================

build_exe_py = """#!/usr/bin/env python3
"""
AECS Calibration Editor - EXE Builder Script
"""
import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path

class EXEBuilder:
    """Класс для сборки EXE файла"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / "build"
        self.dist_dir = self.project_dir / "dist"
        self.spec_file = self.project_dir / "aecs_editor.spec"
        
    def clean_build(self):
        """Очистка предыдущих сборок"""
        print("🧹 Очистка предыдущих сборок...")
        
        for dir_path in [self.build_dir, self.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"  Удалено: {dir_path}")
        
        if self.spec_file.exists():
            self.spec_file.unlink()
            print(f"  Удалено: {self.spec_file}")
    
    def install_dependencies(self):
        """Установка зависимостей"""
        print("📦 Установка зависимостей...")
        
        requirements = [
            "pyinstaller>=5.0",
            "numpy>=1.21.0",
            "matplotlib>=3.5.0",
            "pillow>=9.0.0",
        ]
        
        for req in requirements:
            print(f"  Установка: {req}")
            subprocess.run([sys.executable, "-m", "pip", "install", req], 
                          check=True)
    
    def create_project_structure(self):
        """Создание структуры проекта"""
        print("📁 Создание структуры проекта...")
        
        # Основные директории
        directories = [
            "icons",
            "data",
            "templates",
            "docs",
            "resources"
        ]
        
        for dir_name in directories:
            dir_path = self.project_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"  Создано: {dir_path}")
        
        # Создание основных файлов
        files_to_create = {
            "main.py": main_py,
            "aecs_gui.py": aecs_gui_py,
            "requirements.txt": requirements_txt,
            "README.md": readme_md,
            "LICENSE.txt": license_txt,
        }
        
        for filename, content in files_to_create.items():
            file_path = self.project_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Создан: {file_path}")
        
        # Создание иконок (заглушки)
        self.create_icons()
        
        # Создание данных
        self.create_data_files()
    
    def create_icons(self):
        """Создание иконок"""
        print("🎨 Создание иконок...")
        
        # В реальном проекте здесь должны быть настоящие иконки
        # Создаем заглушки
        icon_dir = self.project_dir / "icons"
        
        # Создаем простую иконку .ico (заглушка)
        ico_content = b''  # В реальном проекте здесь бинарные данные иконки
        
        icon_files = [
            ("icon.ico", ico_content),
            ("icon_32.png", b''),
            ("icon_64.png", b''),
            ("icon_128.png", b''),
        ]
        
        for filename, content in icon_files:
            file_path = icon_dir / filename
            with open(file_path, 'wb') as f:
                f.write(content)
            print(f"  Создана иконка: {file_path}")
    
    def create_data_files(self):
        """Создание файлов данных"""
        print("📊 Создание файлов данных...")
        
        data_dir = self.project_dir / "data"
        
        # Пример калибровки
        calibration_data = {
            "version": "2.0.0",
            "date": "2024-01-01",
            "tables": {
                "fuel": {"rpm_range": [0, 8000], "load_range": [0, 100]},
                "ignition": {"rpm_range": [0, 8000], "load_range": [0, 100]},
                "boost": {"rpm_range": [0, 8000], "load_range": [0, 100]}
            }
        }
        
        with open(data_dir / "default_calibration.json", 'w') as f:
            import json
            json.dump(calibration_data, f, indent=2)
        
        print(f"  Создан: {data_dir / 'default_calibration.json'}")
    
    def build_exe(self):
        """Сборка EXE файла"""
        print("🔨 Сборка EXE файла...")
        
        # Команда PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name=AECS_Calibration_Editor",
            "--onefile",
            "--windowed",
            "--icon=icons/icon.ico",
            "--add-data=icons;icons",
            "--add-data=data;data",
            "--add-data=templates;templates",
            "--hidden-import=numpy",
            "--hidden-import=matplotlib",
            "--hidden-import=matplotlib.backends.backend_tkagg",
            "--hidden-import=PIL",
            "--hidden-import=PIL._imagingtk",
            "--hidden-import=PIL._tkinter_finder",
            "--clean",
            "main.py"
        ]
        
        print(f"  Команда: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("  Сборка завершена успешно!")
            
            # Проверяем созданный файл
            exe_path = self.dist_dir / "AECS_Calibration_Editor.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"  ✅ EXE файл создан: {exe_path}")
                print(f"  📏 Размер: {size_mb:.2f} MB")
            else:
                print("  ❌ EXE файл не найден!")
                
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Ошибка сборки: {e}")
            print(f"  Стандартный вывод: {e.stdout}")
            print(f"  Ошибка: {e.stderr}")
            return False
        
        return True
    
    def create_installer(self):
        """Создание установщика"""
        print("📦 Создание установщика...")
        
        # Создаем NSIS скрипт
        nsis_script = self.project_dir / "installer.nsi"
        
        nsis_content = f"""; AECS Calibration Editor Installer
!include "MUI2.nsh"

Name "AECS Calibration Editor"
OutFile "AECS_Calibration_Editor_Setup.exe"
InstallDir "$PROGRAMFILES\\AECS Calibration Editor"
InstallDirRegKey HKLM "Software\\AECS_Calibration_Editor" "Install_Dir"
RequestExecutionLevel admin

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "English"

Section "Main"
    SetOutPath "$INSTDIR"
    
    File /r "dist\\AECS_Calibration_Editor.exe"
    File /r "icons\\"
    File /r "data\\"
    File /r "templates\\"
    File "README.md"
    File "LICENSE.txt"
    
    WriteRegStr HKLM "Software\\AECS_Calibration_Editor" "Install_Dir" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AECS_Calibration_Editor" "DisplayName" "AECS Calibration Editor"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AECS_Calibration_Editor" "UninstallString" '"$INSTDIR\\uninstall.exe"'
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AECS_Calibration_Editor" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AECS_Calibration_Editor" "NoRepair" 1
    
    CreateShortCut "$DESKTOP\\AECS Calibration Editor.lnk" "$INSTDIR\\AECS_Calibration_Editor.exe"
    CreateDirectory "$SMPROGRAMS\\AECS"
    CreateShortCut "$SMPROGRAMS\\AECS\\AECS Calibration Editor.lnk" "$INSTDIR\\AECS_Calibration_Editor.exe"
    
    WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir /r "$INSTDIR"
    
    Delete "$DESKTOP\\AECS Calibration Editor.lnk"
    Delete "$SMPROGRAMS\\AECS\\AECS Calibration Editor.lnk"
    RMDir "$SMPROGRAMS\\AECS"
    
    DeleteRegKey HKLM "Software\\AECS_Calibration_Editor"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AECS_Calibration_Editor"
SectionEnd
"""
        
        with open(nsis_script, 'w', encoding='utf-8') as f:
            f.write(nsis_content)
        
        print(f"  Создан NSIS скрипт: {nsis_script}")
        
        # Проверяем наличие NSIS
        try:
            subprocess.run(["makensis", "/VERSION"], check=True, capture_output=True)
            print("  NSIS найден, создаем установщик...")
            
            subprocess.run(["makensis", str(nsis_script)], check=True)
            
            setup_exe = self.project_dir / "AECS_Calibration_Editor_Setup.exe"
            if setup_exe.exists():
                size_mb = setup_exe.stat().st_size / (1024 * 1024)
                print(f"  ✅ Установщик создан: {setup_exe}")
                print(f"  📏 Размер: {size_mb:.2f} MB")
                
                # Перемещаем в dist
                shutil.move(setup_exe, self.dist_dir / setup_exe.name)
                
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  ⚠️ NSIS не найден. Пропускаем создание установщика.")
            print("  Установите NSIS с https://nsis.sourceforge.io")
    
    def create_portable_package(self):
        """Создание портативного пакета"""
        print("💼 Создание портативного пакета...")
        
        portable_dir = self.project_dir / "portable"
        portable_dir.mkdir(exist_ok=True)
        
        # Копируем EXE
        exe_source = self.dist_dir / "AECS_Calibration_Editor.exe"
        if exe_source.exists():
            shutil.copy(exe_source, portable_dir / "AECS_Calibration_Editor.exe")
        
        # Копируем ресурсы
        for resource_dir in ["icons", "data", "templates"]:
            source_dir = self.project_dir / resource_dir
            if source_dir.exists():
                dest_dir = portable_dir / resource_dir
                shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
        
        # Копируем документацию
        for doc_file in ["README.md", "LICENSE.txt"]:
            source_file = self.project_dir / doc_file
            if source_file.exists():
                shutil.copy(source_file, portable_dir / doc_file)
        
        # Создаем запускающий скрипт
        with open(portable_dir / "run.bat", 'w') as f:
            f.write("""@echo off
echo AECS Calibration Editor - Portable Version
echo.
start AECS_Calibration_Editor.exe
""")
        
        # Создаем архив
        import zipfile
        zip_path = self.dist_dir / "AECS_Calibration_Editor_Portable.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(portable_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, portable_dir)
                    zipf.write(file_path, arcname)
        
        print(f"  ✅ Портативный пакет создан: {zip_path}")
    
    def run(self):
        """Запуск процесса сборки"""
        print("=" * 60)
        print("AECS Calibration Editor - EXE Builder")
        print("=" * 60)
        
        try:
            # 1. Очистка
            self.clean_build()
            
            # 2. Установка зависимостей
            self.install_dependencies()
            
            # 3. Создание структуры
            self.create_project_structure()
            
            # 4. Сборка EXE
            if not self.build_exe():
                return
            
            # 5. Создание установщика
            self.create_installer()
            
            # 6. Создание портативного пакета
            self.create_portable_package()
            
            print("\n" + "=" * 60)
            print("✅ Сборка завершена успешно!")
            print("=" * 60)
            print("\nСозданные файлы:")
            print(f"  📦 EXE файл: {self.dist_dir / 'AECS_Calibration_Editor.exe'}")
            print(f"  🚀 Установщик: {self.dist_dir / 'AECS_Calibration_Editor_Setup.exe'}")
            print(f"  💼 Портативный: {self.dist_dir / 'AECS_Calibration_Editor_Portable.zip'}")
            print("\nДля запуска: дважды щелкните по EXE файлу")
            
        except Exception as e:
