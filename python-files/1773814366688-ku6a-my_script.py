#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Altium to EmPro ODB++ Automation Tool
Программа для автоматизации экспорта из Altium Designer в ODB++
и импорта в Keysight EmPro с получением отчета
"""

import os
import sys
import time
import subprocess
import tempfile
import shutil
import json
import logging
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('Altium2EmPro')


class Altium2EmProAutomation:
    """
    Основной класс автоматизации экспорта из Altium и импорта в EmPro
    """
    
    def __init__(self):
        self.config = self._load_config()
        self.altium_script_path = None
        self.empro_script_path = None
        self.odbpp_path = None
        self.log_content = []
        
    def _load_config(self):
        """Загрузка или создание конфигурации"""
        config_file = Path.home() / '.altium2empro_config.json'
        
        default_config = {
            'altium_path': r'C:\Program Files\Altium\AD22\X2.EXE',
            'empro_path': r'C:\Program Files\Keysight\EMPro2023\bin\empro.exe',
            'default_output_dir': str(Path.home() / 'Desktop' / 'ODB++_Exports'),
            'units': 'mil',  # 'mil' или 'um'
            'layers': [
                'Top Layer', 'Bottom Layer', 'Top Solder', 'Bottom Solder',
                'Top Overlay', 'Bottom Overlay', 'Drill Guide'
            ],
            'timeout_seconds': 300,
            'auto_close_empro': False
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except:
                return default_config
        else:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
    
    def save_config(self):
        """Сохранение конфигурации"""
        config_file = Path.home() / '.altium2empro_config.json'
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def generate_altium_script(self, pcb_file, output_dir):
        """
        Генерация скрипта для Altium Designer
        """
        script_content = f"""
{-------------------------------------------------------------------------------
    Altium DelphiScript для экспорта в ODB++
    Автоматически сгенерировано Altium2EmPro Automation Tool
-------------------------------------------------------------------------------}

Procedure ExportToODB;
Var
    PCBSystem    : IServer;
    PCBDocument  : IServerDocument;
    PCBProject   : IProject;
    PCB          : IPCB_Board;
    Report       : TStringList;
    FilePath     : String;
    OutputPath   : String;
    DateTimeStr  : String;
Begin
    // Получаем текущий документ
    PCBDocument := GetWorkSpace.DM_FocusedDocument;
    if PCBDocument = Nil Then
    Begin
        ShowMessage('Не найден открытый PCB документ');
        Exit;
    End;
    
    // Получаем объект платы
    PCB := PCBServer.GetCurrentPCBBoard;
    if PCB = Nil Then
    Begin
        ShowMessage('Не удалось получить объект платы');
        Exit;
    End;
    
    // Создаем отчет
    Report := TStringList.Create;
    DateTimeStr := FormatDateTime('yyyy-mm-dd hh:nn:ss', Now);
    Report.Add('=== Altium ODB++ Export Log ===');
    Report.Add('Date: ' + DateTimeStr);
    Report.Add('File: ' + PCBDocument.FileName);
    
    // Формируем путь для экспорта
    OutputPath := '{output_dir}' + '\\' + ExtractFileName(PCBDocument.FileName) + '_ODB++';
    
    // Запускаем экспорт ODB++
    ShowMessage('Начинаем экспорт ODB++ в: ' + OutputPath);
    
    // Используем ODB++ экспорт через CAM-процесс
    ResetParameters;
    AddStringParameter('OutputFile', OutputPath);
    AddStringParameter('Format', 'ODB++');
    AddStringParameter('Layers', 'All'); // Можно указать конкретные слои
    AddStringParameter('Units', '{self.config['units']}');
    AddStringParameter('OpenAfterExport', 'False');
    
    // Выполняем экспорт
    RunProcess('PCB:ExportODB');
    
    // Проверяем результат
    If FileExists(OutputPath + '\\matrix') Then
    Begin
        Report.Add('Export: УСПЕШНО');
        Report.Add('Output path: ' + OutputPath);
    End
    Else
    Begin
        Report.Add('Export: ОШИБКА - Файлы ODB++ не найдены');
    End;
    
    // Сохраняем отчет
    Report.SaveToFile(OutputPath + '\\export_log.txt');
    Report.Free;
    
    ShowMessage('Экспорт ODB++ завершен. Лог сохранен.');
End;

Procedure Start;
Begin
    ExportToODB;
End;

Start;
        """
        
        # Создаем временный файл скрипта
        temp_dir = tempfile.mkdtemp()
        script_file = Path(temp_dir) / 'export_odbpp.pas'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_file
    
    def generate_empro_script(self, odbpp_path):
        """
        Генерация Python скрипта для EmPro
        """
        script_content = f'''# -*- coding: utf-8 -*-
"""
EmPro Python скрипт для импорта ODB++
Автоматически сгенерировано Altium2EmPro Automation Tool
Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

import sys
import os
import time
import json
from datetime import datetime

# Импортируем EmPro модули
try:
    import empro
    from empro import common
    from empro.core import Application
    from empro.toolkit import pcb
except ImportError as e:
    print(f"Ошибка импорта модулей EmPro: {{e}}")
    sys.exit(1)

def import_odbpp_and_get_logs(odbpp_path):
    """
    Импорт ODB++ файла и получение логов
    """
    result = {{
        'status': 'unknown',
        'logs': [],
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }}
    
    try:
        print(f"Начинаем импорт ODB++ из: {{odbpp_path}}")
        
        # Создаем приложение EmPro
        app = Application()
        app.start()
        
        # Импортируем PCB
        importer = pcb.ODBppImporter()
        
        # Настраиваем параметры импорта
        importer.setFilePath(odbpp_path)
        importer.setUnits('{self.config['units']}')  # mil или um
        
        # Выбираем слои для импорта
        layers = {self.config['layers']}
        for layer in layers:
            importer.enableLayer(layer, True)
        
        # Запускаем импорт
        print("Запуск процесса импорта...")
        
        # Перехватываем логи
        log_capture = []
        
        def log_handler(message, level):
            log_capture.append({{
                'message': message,
                'level': level,
                'time': datetime.now().isoformat()
            }})
            print(f"[{{level}}] {{message}}")
        
        # Устанавливаем обработчик логов
        common.logging.addHandler(log_handler)
        
        # Выполняем импорт
        success = importer.importPCB()
        
        # Ждем завершения импорта
        time.sleep(2)
        
        # Собираем результаты
        result['logs'] = log_capture
        result['status'] = 'success' if success else 'failed'
        
        # Дополнительно читаем логи из EmPro
        if hasattr(common, 'getLogs'):
            empro_logs = common.getLogs()
            result['empro_logs'] = empro_logs
        
        print(f"Импорт завершен. Статус: {{result['status']}}")
        
        # Сохраняем результат в файл
        output_file = os.path.join(os.path.dirname(odbpp_path), 'empro_import_log.json')
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Лог сохранен в: {{output_file}}")
        
    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
        print(f"Ошибка при импорте: {{e}}")
    
    finally:
        if 'app' in locals():
            if not {str(self.config['auto_close_empro']).lower()}:
                # Оставляем EmPro открытым
                print("EmPro оставлен открытым для просмотра результатов")
            else:
                app.stop()
    
    return result

if __name__ == "__main__":
    odbpp_path = r"{odbpp_path}"
    result = import_odbpp_and_get_logs(odbpp_path)
    
    # Выводим результат в формате JSON для захвата основной программой
    print("===EMPRO_RESULT_START===")
    print(json.dumps(result))
    print("===EMPRO_RESULT_END===")
'''
        
        # Создаем временный файл скрипта
        temp_dir = tempfile.mkdtemp()
        script_file = Path(temp_dir) / 'import_odbpp.py'
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_file
    
    def run_altium_export(self, pcb_file, callback=None):
        """
        Запуск Altium Designer и экспорт в ODB++
        """
        if callback:
            callback("Запуск Altium Designer...")
        
        # Проверяем существование файла
        if not os.path.exists(pcb_file):
            raise FileNotFoundError(f"PCB файл не найден: {pcb_file}")
        
        # Создаем выходную директорию
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pcb_name = Path(pcb_file).stem
        output_dir = Path(self.config['default_output_dir']) / f"{pcb_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем скрипт для Altium
        script_file = self.generate_altium_script(pcb_file, output_dir)
        self.altium_script_path = script_file
        
        if callback:
            callback(f"Скрипт Altium создан: {script_file}")
            callback("Запуск Altium Designer с параметрами...")
        
        # Запускаем Altium с нашим скриптом
        try:
            # Команда для запуска Altium с выполнением скрипта
            cmd = [
                self.config['altium_path'],
                pcb_file,
                '-RunScript',
                str(script_file)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            
            # Ждем завершения процесса или таймаута
            timeout = self.config['timeout_seconds']
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # Проверяем наличие файлов ODB++
                odbpp_dirs = list(output_dir.glob('*_ODB++'))
                if odbpp_dirs:
                    self.odbpp_path = str(odbpp_dirs[0])
                    
                    # Проверяем наличие лога экспорта
                    log_file = Path(self.odbpp_path) / 'export_log.txt'
                    if log_file.exists():
                        with open(log_file, 'r') as f:
                            log_content = f.read()
                        self.log_content.append(log_content)
                    
                    if callback:
                        callback(f"ODB++ экспорт завершен: {self.odbpp_path}")
                    
                    return self.odbpp_path
                
                time.sleep(2)
            
            raise TimeoutError(f"Таймаут экспорта Altium ({timeout} секунд)")
            
        except Exception as e:
            if callback:
                callback(f"Ошибка при экспорте из Altium: {e}")
            raise
    
    def run_empro_import(self, odbpp_path, callback=None):
        """
        Запуск EmPro и импорт ODB++ с получением логов
        """
        if callback:
            callback("Запуск EmPro для импорта ODB++...")
        
        # Проверяем существование ODB++ директории
        if not os.path.exists(odbpp_path):
            raise FileNotFoundError(f"ODB++ директория не найдена: {odbpp_path}")
        
        # Генерируем скрипт для EmPro
        script_file = self.generate_empro_script(odbpp_path)
        self.empro_script_path = script_file
        
        if callback:
            callback(f"Скрипт EmPro создан: {script_file}")
            callback("Запуск EmPro с импортом...")
        
        # Запускаем EmPro с нашим скриптом
        try:
            cmd = [
                self.config['empro_path'],
                '--script',
                str(script_file)
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            
            # Собираем вывод
            stdout_lines = []
            in_result = False
            result_json = []
            
            for line in process.stdout:
                stdout_lines.append(line)
                
                if "===EMPRO_RESULT_START===" in line:
                    in_result = True
                    result_json = []
                elif "===EMPRO_RESULT_END===" in line:
                    in_result = False
                    # Парсим результат
                    try:
                        result_data = json.loads(''.join(result_json))
                        if callback:
                            callback("\n=== Результат импорта EmPro ===")
                            callback(f"Статус: {result_data['status']}")
                            
                            if 'logs' in result_data:
                                callback("\nЛоги импорта:")
                                for log in result_data['logs']:
                                    callback(f"  [{log['level']}] {log['message']}")
                            
                            if 'errors' in result_data and result_data['errors']:
                                callback("\nОшибки:")
                                for error in result_data['errors']:
                                    callback(f"  {error}")
                            
                            self.log_content.append(json.dumps(result_data, indent=2))
                    except Exception as e:
                        if callback:
                            callback(f"Ошибка парсинга результата: {e}")
                elif in_result:
                    result_json.append(line)
                else:
                    # Обычный вывод
                    if callback and line.strip():
                        callback(f"EmPro: {line.strip()}")
            
            # Ждем завершения процесса
            process.wait(timeout=self.config['timeout_seconds'])
            
            # Проверяем наличие лог-файла
            log_file = Path(odbpp_path) / 'empro_import_log.json'
            if log_file.exists():
                with open(log_file, 'r') as f:
                    log_content = f.read()
                self.log_content.append(log_content)
                if callback:
                    callback(f"\nЛог сохранен в: {log_file}")
            
            if callback:
                callback("\nИмпорт в EmPro завершен")
            
        except Exception as e:
            if callback:
                callback(f"Ошибка при импорте в EmPro: {e}")
            raise
    
    def run_full_process(self, pcb_file, callback=None):
        """
        Полный процесс: экспорт из Altium + импорт в EmPro
        """
        self.log_content = []
        
        try:
            # Шаг 1: Экспорт из Altium
            if callback:
                callback("=== ШАГ 1: Экспорт из Altium Designer в ODB++ ===")
            
            odbpp_path = self.run_altium_export(pcb_file, callback)
            
            # Шаг 2: Импорт в EmPro
            if callback:
                callback("\n=== ШАГ 2: Импорт ODB++ в Keysight EmPro ===")
            
            self.run_empro_import(odbpp_path, callback)
            
            if callback:
                callback("\n=== ПРОЦЕСС ЗАВЕРШЕН УСПЕШНО ===")
            
            return True
            
        except Exception as e:
            if callback:
                callback(f"\n=== ОШИБКА: {e} ===")
            return False


class Altium2EmProGUI:
    """
    Графический интерфейс для программы автоматизации
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Altium to EmPro ODB++ Automation Tool")
        self.root.geometry("800x700")
        
        self.automation = Altium2EmProAutomation()
        self.current_process = None
        
        self.create_widgets()
        self.load_config()
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(
            main_frame,
            text="Altium Designer → ODB++ → Keysight EmPro",
            font=('Arial', 14, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Выбор PCB файла
        ttk.Label(main_frame, text="PCB файл:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        
        self.pcb_file_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.pcb_file_var, width=50).grid(
            row=1, column=1, padx=5, pady=5
        )
        
        ttk.Button(
            main_frame,
            text="Обзор...",
            command=self.browse_pcb_file
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Ноутбук для вкладок
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Вкладка настроек
        settings_frame = ttk.Frame(notebook, padding="5")
        notebook.add(settings_frame, text="Настройки")
        
        # Пути к программам
        ttk.Label(settings_frame, text="Altium Designer:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.altium_path_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.altium_path_var, width=60).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(
            settings_frame,
            text="Обзор...",
            command=lambda: self.browse_program('altium')
        ).grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="Keysight EmPro:").grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.empro_path_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.empro_path_var, width=60).grid(
            row=1, column=1, padx=5, pady=5
        )
        ttk.Button(
            settings_frame,
            text="Обзор...",
            command=lambda: self.browse_program('empro')
        ).grid(row=1, column=2, padx=5, pady=5)
        
        # Директория вывода
        ttk.Label(settings_frame, text="Директория вывода:").grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.output_dir_var = tk.StringVar()
        ttk.Entry(settings_frame, textvariable=self.output_dir_var, width=60).grid(
            row=2, column=1, padx=5, pady=5
        )
        ttk.Button(
            settings_frame,
            text="Обзор...",
            command=self.browse_output_dir
        ).grid(row=2, column=2, padx=5, pady=5)
        
        # Единицы измерения
        ttk.Label(settings_frame, text="Единицы измерения:").grid(
            row=3, column=0, sticky=tk.W, pady=5
        )
        self.units_var = tk.StringVar()
        units_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.units_var,
            values=['mil', 'um'],
            state='readonly',
            width=10
        )
        units_combo.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Таймаут
        ttk.Label(settings_frame, text="Таймаут (сек):").grid(
            row=4, column=0, sticky=tk.W, pady=5
        )
        self.timeout_var = tk.IntVar(value=300)
        ttk.Spinbox(
            settings_frame,
            from_=30,
            to=3600,
            textvariable=self.timeout_var,
            width=10
        ).grid(row=4, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Автозакрытие EmPro
        self.auto_close_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            settings_frame,
            text="Автоматически закрывать EmPro после импорта",
            variable=self.auto_close_var
        ).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Выбор слоев
        ttk.Label(settings_frame, text="Слои для импорта:").grid(
            row=6, column=0, sticky=tk.W, pady=5
        )
        
        layers_frame = ttk.Frame(settings_frame)
        layers_frame.grid(row=6, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.layer_vars = {}
        default_layers = [
            'Top Layer', 'Bottom Layer', 'Top Solder', 'Bottom Solder',
            'Top Overlay', 'Bottom Overlay', 'Drill Guide'
        ]
        
        for i, layer in enumerate(default_layers):
            var = tk.BooleanVar(value=True)
            self.layer_vars[layer] = var
            ttk.Checkbutton(
                layers_frame,
                text=layer,
                variable=var
            ).grid(row=i//2, column=i%2, sticky=tk.W, padx=10)
        
        # Кнопка сохранения настроек
        ttk.Button(
            settings_frame,
            text="Сохранить настройки",
            command=self.save_config
        ).grid(row=7, column=0, columnspan=3, pady=10)
        
        # Вкладка управления
        control_frame = ttk.Frame(notebook, padding="5")
        notebook.add(control_frame, text="Управление")
        
        # Кнопки управления
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=0, column=0, pady=10)
        
        self.start_button = ttk.Button(
            button_frame,
            text="Запустить процесс",
            command=self.start_process,
            width=20
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(
            button_frame,
            text="Остановить",
            command=self.stop_process,
            state=tk.DISABLED,
            width=20
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.clear_button = ttk.Button(
            button_frame,
            text="Очистить лог",
            command=self.clear_log,
            width=20
        )
        self.clear_button.grid(row=0, column=2, padx=5)
        
        # Вкладка логов
        logs_frame = ttk.Frame(notebook, padding="5")
        notebook.add(logs_frame, text="Логи")
        
        # Текстовое поле для вывода логов
        self.log_text = scrolledtext.ScrolledText(
            logs_frame,
            wrap=tk.WORD,
            width=90,
            height=30,
            font=('Courier', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Прогресс бар
        self.progress = ttk.Progressbar(
            main_frame,
            mode='indeterminate'
        )
        self.progress.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
    
    def browse_pcb_file(self):
        """Выбор PCB файла"""
        filename = filedialog.askopenfilename(
            title="Выберите PCB файл",
            filetypes=[("PCB files", "*.pcb"), ("All files", "*.*")]
        )
        if filename:
            self.pcb_file_var.set(filename)
    
    def browse_program(self, prog_type):
        """Выбор исполняемого файла программы"""
        if prog_type == 'altium':
            title = "Выберите исполняемый файл Altium Designer (X2.EXE)"
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
            var = self.altium_path_var
        else:
            title = "Выберите исполняемый файл Keysight EmPro (empro.exe)"
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
            var = self.empro_path_var
        
        filename = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if filename:
            var.set(filename)
    
    def browse_output_dir(self):
        """Выбор директории для вывода"""
        dirname = filedialog.askdirectory(title="Выберите директорию для вывода")
        if dirname:
            self.output_dir_var.set(dirname)
    
    def load_config(self):
        """Загрузка конфигурации в интерфейс"""
        self.altium_path_var.set(self.automation.config.get('altium_path', ''))
        self.empro_path_var.set(self.automation.config.get('empro_path', ''))
        self.output_dir_var.set(self.automation.config.get('default_output_dir', ''))
        self.units_var.set(self.automation.config.get('units', 'mil'))
        self.timeout_var.set(self.automation.config.get('timeout_seconds', 300))
        self.auto_close_var.set(self.automation.config.get('auto_close_empro', False))
        
        # Загрузка слоев
        layers = self.automation.config.get('layers', [])
        for layer, var in self.layer_vars.items():
            var.set(layer in layers)
    
    def save_config(self):
        """Сохранение конфигурации из интерфейса"""
        self.automation.config['altium_path'] = self.altium_path_var.get()
        self.automation.config['empro_path'] = self.empro_path_var.get()
        self.automation.config['default_output_dir'] = self.output_dir_var.get()
        self.automation.config['units'] = self.units_var.get()
        self.automation.config['timeout_seconds'] = self.timeout_var.get()
        self.automation.config['auto_close_empro'] = self.auto_close_var.get()
        
        # Сохранение слоев
        layers = [layer for layer, var in self.layer_vars.items() if var.get()]
        self.automation.config['layers'] = layers
        
        self.automation.save_config()
        self.log("Настройки сохранены")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, tk.END)
    
    def callback(self, message):
        """Callback функция для вывода сообщений"""
        self.log(message)
    
    def start_process(self):
        """Запуск процесса автоматизации"""
        pcb_file = self.pcb_file_var.get()
        
        if not pcb_file:
            messagebox.showerror("Ошибка", "Выберите PCB файл")
            return
        
        if not os.path.exists(pcb_file):
            messagebox.showerror("Ошибка", f"Файл не существует: {pcb_file}")
            return
        
        # Сохраняем настройки перед запуском
        self.save_config()
        
        # Блокируем кнопки
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # Запускаем прогресс бар
        self.progress.start()
        
        # Запускаем процесс в отдельном потоке
        self.current_process = threading.Thread(
            target=self.run_process,
            args=(pcb_file,)
        )
        self.current_process.daemon = True
        self.current_process.start()
        
        # Проверяем завершение потока
        self.check_process()
    
    def run_process(self, pcb_file):
        """Запуск процесса в отдельном потоке"""
        try:
            success = self.automation.run_full_process(pcb_file, self.callback)
            
            if success:
                self.root.after(0, lambda: self.log("✓ Процесс успешно завершен"))
            else:
                self.root.after(0, lambda: self.log("✗ Процесс завершен с ошибками"))
        
        except Exception as e:
            self.root.after(0, lambda: self.log(f"✗ Критическая ошибка: {e}"))
        
        finally:
            self.root.after(0, self.process_finished)
    
    def check_process(self):
        """Проверка состояния процесса"""
        if self.current_process and self.current_process.is_alive():
            self.root.after(100, self.check_process)
        else:
            self.process_finished()
    
    def process_finished(self):
        """Действия при завершении процесса"""
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.current_process = None
    
    def stop_process(self):
        """Остановка процесса"""
        if self.current_process and self.current_process.is_alive():
            # В Python нет прямого способа остановить поток,
            # поэтому просто отмечаем, что процесс должен быть остановлен
            self.log("Запрос на остановку процесса...")
            # Здесь можно добавить механизм остановки через флаг


def main():
    """Главная функция"""
    root = tk.Tk()
    app = Altium2EmProGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()