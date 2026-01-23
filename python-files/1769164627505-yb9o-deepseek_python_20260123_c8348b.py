import os
import sys
import time
import socket
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
from queue import Queue
import winreg

class ZapretWebGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zapret-WEB")
        self.root.geometry("1200x800")
        
        # Переменные
        self.bat_files = []
        self.current_process = None
        self.is_running = False
        self.current_file_index = 0
        
        # Для остановки процессов по имени файла
        self.process_map = {}  # {process_pid: filename}
        self.running_filename = None  # Имя запущенного файла
        self.selected_filename = None  # Выбранный файл для остановки
        
        # Очередь для вывода в лог
        self.log_queue = Queue()
        
        # Стили
        self.setup_styles()
        
        # Интерфейс
        self.setup_ui()
        
        # Запускаем обновление логов
        self.update_logs()
        
        # Сканируем файлы
        self.scan_bat_files()
        
        # Блокировка двойного клика
        self.double_click_blocked = False
    
    def setup_styles(self):
        """Настройка стилей"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цветовая схема
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'accent': '#4CAF50',
            'secondary': '#2196F3',
            'warning': '#FF9800',
            'error': '#f44336',
            'panel': '#2d2d30',
            'text': '#d4d4d4'
        }
        
        # Настройка цветов виджетов
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['accent'])
        style.configure('TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['accent'])
        
        # Кнопки
        style.configure('Run.TButton', background=self.colors['accent'], foreground='white')
        style.configure('Stop.TButton', background=self.colors['error'], foreground='white')
        style.configure('Scan.TButton', background=self.colors['secondary'], foreground='white')
        
        # Progress bar
        style.configure('Horizontal.TProgressbar', 
                       background=self.colors['accent'],
                       troughcolor=self.colors['panel'])
    
    def setup_ui(self):
        """Настройка интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Настройка растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # ===== ВЕРХНЯЯ ПАНЕЛЬ =====
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        
        # Заголовок
        title_label = tk.Label(top_frame, 
                              text="ZAPRET-WEB",
                              font=('Arial', 18, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['accent'])
        title_label.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        # Информация о папке
        self.folder_label = ttk.Label(top_frame, text="", font=('Arial', 9))
        self.folder_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))
        
        # ===== ПАНЕЛЬ УПРАВЛЕНИЯ =====
        control_frame = ttk.LabelFrame(main_frame, text="Управление", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Кнопки управления
        ttk.Button(control_frame, text="🔄 Сканировать файлы", 
                  command=self.scan_bat_files, style='Scan.TButton').pack(side=tk.LEFT, padx=(0, 5))
        
        self.run_selected_btn = ttk.Button(control_frame, text="▶ Запустить выбранный",
                                          command=self.run_selected_bat, style='Run.TButton',
                                          state='disabled')
        self.run_selected_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹ Остановить подключение",
                                  command=self.stop_selected_process, style='Stop.TButton',
                                  state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # ===== ОСНОВНОЙ КОНТЕЙНЕР =====
        middle_frame = ttk.Frame(main_frame)
        middle_frame.grid(row=2, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(0, 10))
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        # Список файлов (слева)
        file_frame = ttk.LabelFrame(middle_frame, text="📁 BAT файлы", padding="10")
        file_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=(0, 5))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)
        
        # Treeview для файлов
        columns = ('name', 'type', 'size', 'ports')
        self.tree = ttk.Treeview(file_frame, columns=columns, show='headings', height=15)
        
        # Заголовки
        self.tree.heading('name', text='Имя файла')
        self.tree.heading('type', text='Тип')
        self.tree.heading('size', text='Размер')
        self.tree.heading('ports', text='Порты')
        
        # Колонки
        self.tree.column('name', width=200)
        self.tree.column('type', width=120)
        self.tree.column('size', width=80, anchor='center')
        self.tree.column('ports', width=150)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Двойной клик
        self.tree.bind('<Double-1>', self.on_file_double_click)
        # Одиночный клик для выбора файла
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
        # Информация о файле (справа)
        info_frame = ttk.LabelFrame(middle_frame, text="📋 Информация", padding="10")
        info_frame.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        info_frame.columnconfigure(0, weight=1)
        
        # Поля информации
        info_fields = [
            ("Выбранный файл:", "file_info"),
            ("Тип:", "type_info"),
            ("Размер:", "size_info"),
            ("Портов найдено:", "ports_info"),
            ("Статус:", "status_info")
        ]
        
        for i, (label_text, var_name) in enumerate(info_fields):
            label_frame = ttk.Frame(info_frame)
            label_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=2)
            label_frame.columnconfigure(1, weight=1)
            
            ttk.Label(label_frame, text=label_text, width=15, anchor=tk.W).grid(row=0, column=0, sticky=tk.W)
            setattr(self, var_name, ttk.Label(label_frame, text="", anchor=tk.W))
            getattr(self, var_name).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Быстрые кнопки в инфо-панели
        button_frame = ttk.Frame(info_frame)
        button_frame.grid(row=len(info_fields), column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Показать код", 
                  command=self.show_file_code, width=15).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Копировать путь", 
                  command=self.copy_file_path, width=15).pack(side=tk.LEFT)
        
        # ===== ЛОГ =====
        log_frame = ttk.LabelFrame(main_frame, text="📝 Журнал выполнения", padding="10")
        log_frame.grid(row=3, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=15,
                                                 bg=self.colors['panel'],
                                                 fg=self.colors['text'],
                                                 font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Кнопки управления логом
        log_buttons = ttk.Frame(log_frame)
        log_buttons.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(log_buttons, text="Очистить лог", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_buttons, text="Сохранить лог", 
                  command=self.save_log).pack(side=tk.LEFT)
        
        # ===== СТАТУС БАР =====
        status_frame = ttk.Frame(main_frame, relief=tk.SUNKEN)
        status_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Готов к работе", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=10, pady=2)
        
        self.process_label = ttk.Label(status_frame, text="Процесс: не активен", anchor=tk.W)
        self.process_label.pack(side=tk.LEFT, padx=20, pady=2)
        
        self.time_label = ttk.Label(status_frame, text="", anchor=tk.E)
        self.time_label.pack(side=tk.RIGHT, padx=10, pady=2)
        
        # Обновление времени
        self.update_time()
    
    def update_time(self):
        """Обновление времени"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"Время: {current_time}")
        self.root.after(1000, self.update_time)
    
    def log(self, message, color=None):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        if color:
            # Помечаем для цветного вывода
            self.log_queue.put((log_message, color))
        else:
            self.log_queue.put((log_message, None))
    
    def update_logs(self):
        """Обновление лога из очереди (потокобезопасно)"""
        while not self.log_queue.empty():
            message, color = self.log_queue.get()
            
            self.log_text.insert(tk.END, message)
            
            if color:
                # Применяем цвет к последней вставленной строке
                start = self.log_text.index("end-1c linestart")
                end = self.log_text.index("end-1c lineend")
                self.log_text.tag_add(color, start, end)
                self.log_text.tag_config(color, foreground=color)
            
            self.log_text.see(tk.END)
            self.log_text.update()
        
        self.root.after(100, self.update_logs)
    
    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete(1.0, tk.END)
        self.log("Лог очищен", "#4CAF50")
    
    def save_log(self):
        """Сохранение лога в файл"""
        filename = f"zapret_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            
            self.log(f"Лог сохранен: {filename}", "#4CAF50")
            messagebox.showinfo("Успех", f"Лог сохранен в {filename}")
        except Exception as e:
            self.log(f"Ошибка сохранения лога: {e}", "#f44336")
    
    def scan_bat_files(self):
        """Сканирование BAT файлов (старая проверка файлов)"""
        self.log("🔍 Начинаю сканирование BAT файлов...")
        
        # Очищаем treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.bat_files = []
        script_dir = os.path.dirname(__file__) or os.getcwd()
        self.folder_label.config(text=f"📂 Папка: {script_dir}")
        
        count = 0
        for filename in os.listdir(script_dir):
            if filename.lower().endswith('.bat'):
                filepath = os.path.join(script_dir, filename)
                
                try:
                    # Получаем размер файла
                    size = os.path.getsize(filepath)
                    
                    # Определяем тип файла (старая проверка)
                    file_type = self.detect_file_type_old(filepath)
                    
                    # Извлекаем порты (старая проверка)
                    ports = self.extract_ports_old(filepath)
                    port_text = ', '.join(map(str, ports))
                    if len(ports) > 5:
                        port_text = f"{', '.join(map(str, ports[:5]))}... ({len(ports)})"
                    elif not ports:
                        port_text = "Не найдены"
                    
                    self.bat_files.append({
                        'name': filename,
                        'path': filepath,
                        'size': size,
                        'type': file_type,
                        'ports': ports,
                        'ports_count': len(ports)
                    })
                    
                    # Добавляем в treeview
                    self.tree.insert('', 'end', 
                                   values=(filename, 
                                          file_type,
                                          f"{size}",
                                          port_text))
                    count += 1
                    
                    self.log(f"✅ Найден: {filename} ({file_type}, {len(ports)} портов)", "#4CAF50")
                    
                except Exception as e:
                    self.log(f"⚠ Ошибка чтения {filename}: {e}", "#FF9800")
        
        if count > 0:
            self.log(f"✅ Всего найдено {count} BAT файлов", "#4CAF50")
            self.status_label.config(text=f"Найдено {count} файлов")
            
            # Активируем кнопку запуска только если нет запущенного процесса
            if not self.is_running:
                self.run_selected_btn.config(state='normal')
            
        else:
            self.log("❌ BAT файлы не найдены", "#f44336")
            self.status_label.config(text="Файлы не найдены")
            self.run_selected_btn.config(state='disabled')
    
    def detect_file_type_old(self, filepath):
        """Старая проверка типа BAT файла"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            content_lower = content.lower()
            
            # Старая логика определения типа
            if 'winws.exe' in content:
                if 'service.bat' in content:
                    return "Сервисный"
                elif '--update' in content_lower or 'update' in filename.lower():
                    return "Обновление"
                else:
                    return "Основной"
            elif 'check' in filename.lower():
                return "Проверочный"
            elif 'install' in filename.lower():
                return "Установка"
            elif 'uninstall' in filename.lower():
                return "Удаление"
            elif 'test' in filename.lower():
                return "Тестовый"
            elif 'backup' in filename.lower():
                return "Резервный"
            else:
                return "Пользовательский"
                
        except:
            return "Неизвестно"
    
    def extract_ports_old(self, filepath):
        """Старая проверка портов из BAT файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            ports = []
            
            # Старые паттерны для поиска портов
            patterns = [
                r'port\s*[=:]\s*(\d+)',  # PORT=8080 или PORT: 8080
                r':(\d{2,5})\b',  # :8080
                r'\b(\d{2,5})/tcp\b',  # 8080/tcp
                r'\b(\d{2,5})/udp\b',  # 8080/udp
                r'--port=(\d+)',  # --port=8080
                r'-p\s+(\d+)',  # -p 8080
                r'listen.*?(\d{2,5})',  # listen 8080
                r'bind.*?(\d{2,5})',  # bind 8080
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match.isdigit():
                        port = int(match)
                        if 1 <= port <= 65535 and port not in ports:
                            ports.append(port)
            
            # Ищем диапазоны портов (старого формата)
            range_patterns = [
                r'(\d+)-(\d+)',
                r'(\d+)\s*\.\.\s*(\d+)',
                r'from\s+(\d+)\s+to\s+(\d+)'
            ]
            
            for pattern in range_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for start_str, end_str in matches:
                    if start_str.isdigit() and end_str.isdigit():
                        start = int(start_str)
                        end = int(end_str)
                        if 1 <= start <= 65535 and 1 <= end <= 65535:
                            # Берем только первые 5 портов из диапазона
                            for port in range(start, min(end + 1, start + 6)):
                                if port not in ports:
                                    ports.append(port)
            
            # Сортируем и возвращаем только уникальные порты
            return sorted(list(set(ports)))
            
        except Exception as e:
            print(f"Ошибка при извлечении портов: {e}")
            return []
    
    def on_file_select(self, event):
        """Обработка выбора файла"""
        if self.double_click_blocked:
            self.double_click_blocked = False
            return
            
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        self.selected_filename = filename
        
        # Обновляем информацию о файле
        self.update_file_info()
        
        # Если процесс запущен, проверяем можно ли остановить этот файл
        if self.is_running:
            # Если выбран запущенный файл - активируем кнопку остановки
            if filename == self.running_filename:
                self.stop_btn.config(state='normal')
                self.log(f"✓ Выбран запущенный файл: {filename}. Можно остановить.", "#4CAF50")
            else:
                self.stop_btn.config(state='disabled')
                self.log(f"⚠ Внимание: запущен другой файл ({self.running_filename}). Сначала остановите его.", "#FF9800")
        else:
            # Если процесс не запущен, активируем кнопку запуска
            self.run_selected_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def on_file_double_click(self, event):
        """Двойной клик по файлу"""
        if self.double_click_blocked:
            return
            
        self.double_click_blocked = True
        
        # Проверяем, запущен ли уже процесс
        if self.is_running:
            self.log("❌ Нельзя запустить новый файл. Сначала остановите текущий процесс.", "#f44336")
            messagebox.showwarning("Внимание", "Сначала остановите текущий процесс!")
            return
        
        self.update_file_info()
        self.run_selected_bat()
    
    def update_file_info(self):
        """Обновление информации о выбранном файле"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        
        # Находим информацию о файле
        for bat in self.bat_files:
            if bat['name'] == filename:
                self.file_info.config(text=bat['name'])
                self.type_info.config(text=bat['type'])
                self.size_info.config(text=f"{bat['size']} байт")
                self.ports_info.config(text=str(bat['ports_count']))
                if bat['ports']:
                    port_text = ', '.join(map(str, bat['ports'][:10]))
                    if len(bat['ports']) > 10:
                        port_text += f"... (+{len(bat['ports'])-10})"
                    self.status_info.config(text=f"Порты: {port_text}")
                else:
                    self.status_info.config(text="Порты не найдены")
                break
    
    def run_selected_bat(self):
        """Запуск выбранного BAT файла (только если нет запущенного)"""
        # Проверяем, запущен ли уже процесс
        if self.is_running:
            self.log("❌ Нельзя запустить новый файл. Сначала остановите текущий процесс.", "#f44336")
            messagebox.showwarning("Внимание", "Сначала остановите текущий процесс!")
            return
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите BAT файл")
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        
        # Находим файл
        bat_info = None
        for bat in self.bat_files:
            if bat['name'] == filename:
                bat_info = bat
                break
        
        if not bat_info:
            messagebox.showerror("Ошибка", "Файл не найден")
            return
        
        self.log(f"\n{'='*60}", "#2196F3")
        self.log(f"🚀 ЗАПУСК: {bat_info['name']}", "#2196F3")
        self.log(f"📋 ТИП: {bat_info['type']}", "#2196F3")
        self.log(f"{'='*60}\n", "#2196F3")
        
        # Сохраняем имя запущенного файла
        self.running_filename = bat_info['name']
        
        # БЛОКИРУЕМ ИНТЕРФЕЙС: отключаем все кнопки запуска
        self.run_selected_btn.config(state='disabled')
        
        # Активируем кнопку остановки
        self.stop_btn.config(state='normal')
        
        # Обновляем статусы
        self.status_info.config(text="Запускается...")
        self.process_label.config(text=f"Процесс: {bat_info['name']}")
        self.status_label.config(text=f"Запущен: {bat_info['name']}")
        
        # Устанавливаем флаг запуска
        self.is_running = True
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=self.execute_bat_file, args=(bat_info,))
        thread.daemon = True
        thread.start()
    
    def execute_bat_file(self, bat_info):
        """Выполнение BAT файла"""
        try:
            self.log(f"📁 Файл: {bat_info['path']}")
            self.log(f"📊 Размер: {bat_info['size']} байт")
            
            if bat_info['ports']:
                self.log(f"🎯 Порты в конфиге: {', '.join(map(str, bat_info['ports']))}")
            else:
                self.log(f"🎯 Порты в конфиге: не найдены")
            
            self.log(f"\n⏳ Запускаю файл...\n")
            
            # Запускаем процесс
            self.current_process = subprocess.Popen(
                [bat_info['path']],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Сохраняем информацию о процессе
            if self.current_process.pid:
                self.process_map[self.current_process.pid] = bat_info['name']
                self.log(f"✅ Процесс запущен (PID: {self.current_process.pid})", "#4CAF50")
            
            # Обновляем UI в основном потоке
            self.root.after(0, self.update_running_status)
            
            # Читаем вывод в реальном времени
            for line in iter(self.current_process.stdout.readline, ''):
                if not self.is_running:
                    break
                
                line = line.rstrip()
                if line:
                    self.log(f"   {line}")
            
            # Ждем завершения
            self.current_process.wait()
            
            # Удаляем из map после завершения
            if self.current_process.pid in self.process_map:
                del self.process_map[self.current_process.pid]
            
            if self.current_process.returncode == 0:
                self.log(f"✅ Файл успешно завершен", "#4CAF50")
                self.status_info.config(text="Завершен успешно")
            else:
                self.log(f"⚠ Файл завершен с кодом {self.current_process.returncode}", "#FF9800")
                self.status_info.config(text=f"Код ошибки: {self.current_process.returncode}")
            
        except Exception as e:
            self.log(f"❌ Ошибка выполнения: {e}", "#f44336")
            self.status_info.config(text="Ошибка выполнения")
        
        # Завершаем
        self.root.after(0, self.on_process_finished)
    
    def update_running_status(self):
        """Обновление статуса запущенного процесса"""
        # Обновляем статус в UI
        if self.running_filename:
            self.process_label.config(text=f"Процесс: {self.running_filename} (активен)")
            self.status_label.config(text=f"Выполняется: {self.running_filename}")
            
        # Проверяем, активен ли процесс
        if self.current_process and self.current_process.poll() is None:
            # Процесс еще работает, проверяем снова через 1 секунду
            self.root.after(1000, self.update_running_status)
        else:
            # Процесс завершился
            self.root.after(0, self.on_process_finished)
    
    def stop_selected_process(self):
        """Остановка выбранного подключения"""
        # Проверяем, запущен ли процесс
        if not self.is_running:
            self.log("⚠ Нет запущенного процесса для остановки", "#FF9800")
            messagebox.showinfo("Информация", "Нет запущенного процесса")
            self.stop_btn.config(state='disabled')
            return
        
        filename_to_stop = self.running_filename
        
        # Если есть выбранный файл и он совпадает с запущенным
        if self.selected_filename and self.selected_filename != self.running_filename:
            response = messagebox.askyesno("Подтверждение", 
                f"Запущен файл: {self.running_filename}\n\n"
                f"Остановить его?")
            if not response:
                return
        
        self.log(f"\n⏹ Остановка подключения для файла: {filename_to_stop}", "#f44336")
        
        # Устанавливаем флаг остановки
        self.is_running = False
        
        # Останавливаем процесс несколькими способами
        stopped = self.stop_process_by_filename(filename_to_stop)
        
        if stopped:
            self.log(f"✅ Подключение для {filename_to_stop} остановлено", "#4CAF50")
            self.status_label.config(text=f"Остановлено: {filename_to_stop}")
            self.status_info.config(text="Остановлено")
            
            # Сбрасываем имя запущенного файла
            self.running_filename = None
            
            # ОТКРЫВАЕМ ДОСТУП К ИНТЕРФЕЙСУ: активируем кнопки
            self.stop_btn.config(state='disabled')
            if self.tree.selection():
                self.run_selected_btn.config(state='normal')
            
            # Обновляем статус процесса
            self.root.after(1000, self.check_and_update_process_status)
        else:
            self.log(f"⚠ Не удалось остановить подключение для {filename_to_stop}", "#FF9800")
            messagebox.showerror("Ошибка", f"Не удалось остановить {filename_to_stop}")
        
        # Обновляем UI
        self.process_label.config(text="Процесс: не активен")
    
    def stop_process_by_filename(self, filename):
        """Остановка процессов, связанных с файлом"""
        stopped = False
        
        # Способ 1: Остановка через PID из process_map
        pids_to_remove = []
        for pid, proc_name in self.process_map.items():
            if proc_name == filename:
                try:
                    self.log(f"   Завершаю процесс PID {pid}...")
                    import signal
                    try:
                        # Пробуем SIGTERM
                        os.kill(pid, signal.SIGTERM)
                    except:
                        # Если не сработало, пробуем SIGKILL
                        os.kill(pid, signal.SIGKILL)
                    
                    time.sleep(0.5)
                    stopped = True
                    pids_to_remove.append(pid)
                except Exception as e:
                    self.log(f"   Не удалось завершить PID {pid}: {e}", "#FF9800")
        
        # Удаляем завершенные процессы из map
        for pid in pids_to_remove:
            if pid in self.process_map:
                del self.process_map[pid]
        
        # Способ 2: Останавливаем основные процессы BAT файлов
        try:
            # Находим базовое имя без расширения
            base_name = os.path.splitext(filename)[0]
            
            # Останавливаем связанные процессы через taskkill
            commands = [
                f'taskkill /F /IM "{base_name}.exe"',
                f'taskkill /F /IM "{base_name}.bat"',
                f'taskkill /F /FI "WINDOWTITLE eq *{base_name}*"'
            ]
            
            for cmd in commands:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
                    if "SUCCESS" in result.stdout or "завершен" in result.stdout.lower():
                        self.log(f"   ✅ {cmd} - успешно", "#4CAF50")
                        stopped = True
                except subprocess.TimeoutExpired:
                    self.log(f"   ⏰ Таймаут для команды: {cmd}", "#FF9800")
                except Exception as e:
                    pass
                    
        except Exception as e:
            self.log(f"   Ошибка при остановке процессов: {e}", "#FF9800")
        
        # Способ 3: Закрываем порты, связанные с файлом
        try:
            # Находим файл и его порты
            bat_info = None
            for bat in self.bat_files:
                if bat['name'] == filename:
                    bat_info = bat
                    break
            
            if bat_info and bat_info['ports']:
                self.log(f"   🔒 Закрываю порты: {', '.join(map(str, bat_info['ports'][:5]))}...")
                
                # Закрываем основные порты через netstat и taskkill
                for port in bat_info['ports'][:10]:  # Берем первые 10 портов
                    try:
                        # Находим PID, использующий порт
                        cmd = f'netstat -ano | findstr :{port}'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=2)
                        
                        if result.stdout:
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if f':{port}' in line:
                                    parts = line.split()
                                    if len(parts) > 4:
                                        pid = parts[-1]
                                        # Завершаем процесс
                                        try:
                                            subprocess.run(f'taskkill /F /PID {pid}', 
                                                         shell=True, capture_output=True, timeout=2)
                                            stopped = True
                                        except:
                                            pass
                    except:
                        pass
                        
        except Exception as e:
            self.log(f"   Ошибка при закрытии портов: {e}", "#FF9800")
        
        return stopped
    
    def on_process_finished(self):
        """Завершение процесса"""
        self.is_running = False
        self.current_process = None
        self.running_filename = None
        
        # ОТКРЫВАЕМ ДОСТУП К ИНТЕРФЕЙСУ: активируем кнопки
        self.stop_btn.config(state='disabled')
        if self.tree.selection():
            self.run_selected_btn.config(state='normal')
        
        # Обновляем UI
        self.process_label.config(text="Процесс: не активен")
        self.status_label.config(text="Готов к работе")
        
        # Сбрасываем статус в информации о файле
        self.status_info.config(text="Завершен")
        
        self.log("✅ Процесс завершен. Можно запускать другие файлы.", "#4CAF50")
    
    def check_and_update_process_status(self):
        """Проверка и обновление статуса процесса"""
        # Проверяем, есть ли активные процессы
        if self.current_process and self.current_process.poll() is None:
            # Процесс все еще работает
            self.process_label.config(text=f"Процесс: {self.running_filename} (активен)")
        else:
            # Процесс завершился
            self.process_label.config(text="Процесс: не активен")
            self.stop_btn.config(state='disabled')
            if self.tree.selection():
                self.run_selected_btn.config(state='normal')
    
    def show_file_code(self):
        """Показать код выбранного файла"""
        # Блокируем если процесс запущен
        if self.is_running:
            self.log("⚠ Нельзя открыть код во время выполнения процесса", "#FF9800")
            messagebox.showwarning("Внимание", "Сначала остановите процесс!")
            return
            
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл")
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        
        # Находим файл
        for bat in self.bat_files:
            if bat['name'] == filename:
                # Создаем новое окно
                code_window = tk.Toplevel(self.root)
                code_window.title(f"Код: {filename}")
                code_window.geometry("900x600")
                
                # Текстовое поле
                text_widget = scrolledtext.ScrolledText(code_window, 
                                                       font=('Consolas', 10),
                                                       bg='#1e1e1e',
                                                       fg='#d4d4d4')
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Читаем файл
                try:
                    with open(bat['path'], 'r', encoding='utf-8') as f:
                        content = f.read()
                        text_widget.insert(tk.END, content)
                except Exception as e:
                    text_widget.insert(tk.END, f"Ошибка чтения: {e}")
                
                break
    
    def copy_file_path(self):
        """Копировать путь к файлу"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        filename = item['values'][0]
        
        for bat in self.bat_files:
            if bat['name'] == filename:
                self.root.clipboard_clear()
                self.root.clipboard_append(bat['path'])
                self.log(f"📋 Путь скопирован: {bat['path']}", "#4CAF50")
                break

def main():
    """Запуск приложения"""
    try:
        root = tk.Tk()
        app = ZapretWebGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        input("Нажмите Enter...")

if __name__ == "__main__":
    main()