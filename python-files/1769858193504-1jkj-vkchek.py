import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import os
from datetime import datetime
import threading
import time

class VKChecker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VK ID Checker Pro")
        self.root.geometry("1000x800")
        self.root.configure(bg='#2b2d42')
        
        # Указываем путь для сохранения файлов
        self.save_directory = r"C:\Users\nikol\Desktop\vkcheker"
        
        # Создаем папку если она не существует
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
            print(f"Создана папка: {self.save_directory}")
        
        # База данных (ID -> данные)
        self.database = {
            '189241258': {'phone': '79125924654', 'fio': 'Никита Куликов', 'birth': '8.6.2003'},
            'mgimaev2': {'phone': '79028370737', 'fio': 'Максим Гимаев', 'birth': ''},
            'aeyiii': {'phone': '79125930769', 'fio': 'Андрей Никитин', 'birth': '5.9'},
            '160203236': {'phone': '79824907096 79956047096', 'fio': 'Анастасия Куликова', 'birth': '18.2.1998'},
            'gorobtsova98': {'phone': '79197043347', 'fio': 'Таня Горобцова', 'birth': '9.6.1998'},
            '408113538': {'phone': '79504656434', 'fio': 'Viktoria Muratova', 'birth': ''},
            '201188633': {'phone': '79028393218 79128884860', 'fio': 'Тамара Чеснокова', 'birth': '23.12.1949'}
        }
        
        # Лог файл в указанной папке
        self.log_file_path = os.path.join(self.save_directory, "vk_checker_log.txt")
        self.links_file_path = os.path.join(self.save_directory, "links.txt")
        
        # Переменные для массовой проверки
        self.is_mass_checking = False
        self.checking_thread = None
        self.progress_var = tk.DoubleVar()
        
        self.setup_ui()
        self.create_log_file()
        self.check_links_file()
        
    def setup_ui(self):
        # Заголовок с информацией о пути сохранения
        title_frame = tk.Frame(self.root, bg='#2b2d42')
        title_frame.pack(pady=15)
        
        title_label = tk.Label(
            title_frame,
            text="🔍 VK ID Checker Pro",
            font=('Arial', 28, 'bold'),
            fg='#edf2f4',
            bg='#2b2d42'
        )
        title_label.pack()
        
        # Информация о пути сохранения
        path_info = tk.Label(
            title_frame,
            text=f"Файлы сохраняются в: {self.save_directory}",
            font=('Arial', 10),
            fg='#8d99ae',
            bg='#2b2d42'
        )
        path_info.pack(pady=(5, 0))
        
        # Панель вкладок
        self.tab_control = ttk.Notebook(self.root)
        
        # Вкладка единичной проверки
        self.single_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.single_tab, text='Одиночная проверка')
        self.setup_single_tab()
        
        # Вкладка массовой проверки
        self.mass_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.mass_tab, text='Массовая проверка')
        self.setup_mass_tab()
        
        self.tab_control.pack(expand=1, fill='both', padx=10, pady=10)
        
        # Статус бар
        self.status_bar = tk.Label(
            self.root,
            text=f"Готов к работе | Файлы сохраняются в: {self.save_directory}",
            bg='#8d99ae',
            fg='#2b2d42',
            font=('Arial', 10),
            anchor='w',
            relief='sunken',
            padx=10
        )
        self.status_bar.pack(side='bottom', fill='x')
        
    def setup_single_tab(self):
        """Настройка вкладки одиночной проверки"""
        # Ввод данных
        input_frame = tk.Frame(self.single_tab, bg='#2b2d42')
        input_frame.pack(pady=15, padx=20, fill='x')
        
        tk.Label(
            input_frame,
            text="Введите ссылку VK:",
            font=('Arial', 12, 'bold'),
            fg='#edf2f4',
            bg='#2b2d42'
        ).pack(anchor='w')
        
        # Поле ввода со стилем
        entry_frame = tk.Frame(input_frame, bg='#2b2d42')
        entry_frame.pack(pady=10, fill='x')
        
        self.entry = tk.Entry(
            entry_frame,
            font=('Arial', 12),
            width=50,
            bg='#edf2f4',
            fg='#2b2d42',
            relief='flat',
            insertbackground='#2b2d42'
        )
        self.entry.pack(side='left', fill='x', expand=True)
        self.entry.insert(0, "https://vk.ru/id12345678")
        
        # Примеры ссылок
        examples_label = tk.Label(
            input_frame,
            text="Примеры: https://vk.ru/id271985956 | https://vk.ru/mamont | https://vk.ru/kakashka",
            font=('Arial', 9),
            fg='#8d99ae',
            bg='#2b2d42',
            justify='left'
        )
        examples_label.pack(anchor='w', pady=(5, 0))
        
        # Кнопки
        button_frame = tk.Frame(self.single_tab, bg='#2b2d42')
        button_frame.pack(pady=10)
        
        style = ttk.Style()
        style.configure('Check.TButton', font=('Arial', 11), padding=10)
        style.configure('Clear.TButton', font=('Arial', 11), padding=10)
        
        check_button = ttk.Button(
            button_frame,
            text="🔎 Проверить",
            style='Check.TButton',
            command=self.check_id
        )
        check_button.pack(side='left', padx=5)
        
        clear_button = ttk.Button(
            button_frame,
            text="🗑️ Очистить",
            style='Clear.TButton',
            command=self.clear_fields
        )
        clear_button.pack(side='left', padx=5)
        
        # Результаты
        results_frame = tk.Frame(self.single_tab, bg='#2b2d42')
        results_frame.pack(pady=15, padx=20, fill='both', expand=True)
        
        results_header = tk.Frame(results_frame, bg='#2b2d42')
        results_header.pack(fill='x')
        
        tk.Label(
            results_header,
            text="Результаты проверки:",
            font=('Arial', 14, 'bold'),
            fg='#edf2f4',
            bg='#2b2d42'
        ).pack(side='left')
        
        # Индикатор сохранения
        self.save_indicator = tk.Label(
            results_header,
            text="",
            font=('Arial', 10),
            fg='#4CAF50',
            bg='#2b2d42'
        )
        self.save_indicator.pack(side='right', padx=10)
        
        # Стили для Treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
            background="#edf2f4",
            foreground="#2b2d42",
            rowheight=30,
            fieldbackground="#edf2f4",
            font=('Arial', 10)
        )
        style.configure("Treeview.Heading",
            font=('Arial', 11, 'bold'),
            background='#8d99ae',
            foreground='#2b2d42'
        )
        
        # Таблица результатов
        columns = ('Параметр', 'Значение')
        self.tree = ttk.Treeview(
            results_frame,
            columns=columns,
            show='headings',
            height=6,
            style="Treeview"
        )
        
        self.tree.heading('Параметр', text='Параметр')
        self.tree.heading('Значение', text='Значение')
        self.tree.column('Параметр', width=200, anchor='w')
        self.tree.column('Значение', width=500, anchor='w')
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def setup_mass_tab(self):
        """Настройка вкладки массовой проверки"""
        main_frame = tk.Frame(self.mass_tab, bg='#2b2d42')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Информация о файле links.txt
        file_info_frame = tk.Frame(main_frame, bg='#2b2d42')
        file_info_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            file_info_frame,
            text="📄 Массовая проверка из файла links.txt",
            font=('Arial', 14, 'bold'),
            fg='#edf2f4',
            bg='#2b2d42'
        ).pack(anchor='w')
        
        self.links_file_info = tk.Label(
            file_info_frame,
            text=f"Файл: {self.links_file_path}",
            font=('Arial', 10),
            fg='#8d99ae',
            bg='#2b2d42'
        )
        self.links_file_info.pack(anchor='w', pady=(5, 0))
        
        # Статистика файла
        stats_frame = tk.Frame(main_frame, bg='#2b2d42')
        stats_frame.pack(fill='x', pady=(0, 15))
        
        self.links_count_label = tk.Label(
            stats_frame,
            text="Загружено ссылок: 0",
            font=('Arial', 11),
            fg='#edf2f4',
            bg='#2b2d42'
        )
        self.links_count_label.pack(side='left', padx=(0, 20))
        
        self.valid_links_label = tk.Label(
            stats_frame,
            text="Валидных ссылок: 0",
            font=('Arial', 11),
            fg='#edf2f4',
            bg='#2b2d42'
        )
        self.valid_links_label.pack(side='left', padx=(0, 20))
        
        # Превью файла
        preview_frame = tk.Frame(main_frame, bg='#2b2d42')
        preview_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        tk.Label(
            preview_frame,
            text="Содержимое файла links.txt:",
            font=('Arial', 12, 'bold'),
            fg='#edf2f4',
            bg='#2b2d42'
        ).pack(anchor='w', pady=(0, 10))
        
        # Текстовое поле для просмотра ссылок
        self.links_preview = scrolledtext.ScrolledText(
            preview_frame,
            height=10,
            font=('Consolas', 10),
            bg='#1e1e2e',
            fg='#cdd6f4',
            wrap=tk.WORD,
            relief='flat'
        )
        self.links_preview.pack(fill='both', expand=True)
        
        # Панель управления массовой проверкой
        control_frame = tk.Frame(main_frame, bg='#2b2d42')
        control_frame.pack(fill='x', pady=(0, 15))
        
        # Кнопки управления
        btn_frame = tk.Frame(control_frame, bg='#2b2d42')
        btn_frame.pack()
        
        self.load_btn = ttk.Button(
            btn_frame,
            text="🔄 Загрузить файл",
            command=self.load_links_file
        )
        self.load_btn.pack(side='left', padx=5)
        
        self.start_mass_check_btn = ttk.Button(
            btn_frame,
            text="▶ Начать проверку",
            command=self.start_mass_check,
            state='disabled'
        )
        self.start_mass_check_btn.pack(side='left', padx=5)
        
        self.stop_mass_check_btn = ttk.Button(
            btn_frame,
            text="⏹ Остановить",
            command=self.stop_mass_check,
            state='disabled'
        )
        self.stop_mass_check_btn.pack(side='left', padx=5)
        
        self.create_template_btn = ttk.Button(
            btn_frame,
            text="📝 Создать шаблон",
            command=self.create_links_template
        )
        self.create_template_btn.pack(side='left', padx=5)
        
        self.open_links_folder_btn = ttk.Button(
            btn_frame,
            text="📁 Открыть папку",
            command=lambda: os.startfile(self.save_directory)
        )
        self.open_links_folder_btn.pack(side='left', padx=5)
        
        # Прогресс бар
        progress_frame = tk.Frame(main_frame, bg='#2b2d42')
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="Прогресс:",
            font=('Arial', 11),
            fg='#edf2f4',
            bg='#2b2d42'
        )
        self.progress_label.pack(anchor='w', pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400,
            mode='determinate'
        )
        self.progress_bar.pack(fill='x')
        
        self.progress_status = tk.Label(
            progress_frame,
            text="Ожидание запуска...",
            font=('Arial', 10),
            fg='#8d99ae',
            bg='#2b2d42'
        )
        self.progress_status.pack(anchor='w', pady=(5, 0))
        
        # Статистика проверки
        stats_check_frame = tk.Frame(main_frame, bg='#2b2d42')
        stats_check_frame.pack(fill='x')
        
        self.found_label = tk.Label(
            stats_check_frame,
            text="Найдено: 0",
            font=('Arial', 11),
            fg='#4CAF50',
            bg='#2b2d42'
        )
        self.found_label.pack(side='left', padx=(0, 20))
        
        self.not_found_label = tk.Label(
            stats_check_frame,
            text="Не найдено: 0",
            font=('Arial', 11),
            fg='#f44336',
            bg='#2b2d42'
        )
        self.not_found_label.pack(side='left', padx=(0, 20))
        
        self.total_checked_label = tk.Label(
            stats_check_frame,
            text="Всего проверено: 0",
            font=('Arial', 11),
            fg='#edf2f4',
            bg='#2b2d42'
        )
        self.total_checked_label.pack(side='left')
        
    def check_links_file(self):
        """Проверяет наличие файла links.txt и загружает его"""
        if os.path.exists(self.links_file_path):
            self.load_links_file()
        else:
            self.links_preview.insert('end', "Файл links.txt не найден.\n")
            self.links_preview.insert('end', f"Создайте файл в папке: {self.save_directory}\n")
            self.links_preview.insert('end', "Или нажмите 'Создать шаблон' для создания примера.")
    
    def load_links_file(self):
        """Загружает ссылки из файла"""
        try:
            if not os.path.exists(self.links_file_path):
                self.show_mass_notification("Файл не найден", f"Файл links.txt не найден в папке:\n{self.save_directory}")
                return
            
            with open(self.links_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Очищаем превью
            self.links_preview.delete(1.0, 'end')
            
            valid_links = []
            for i, line in enumerate(lines, 1):
                link = line.strip()
                if link and not link.startswith('#'):  # Игнорируем пустые строки и комментарии
                    self.links_preview.insert('end', f"{i}. {link}\n")
                    valid_links.append(link)
            
            total_links = len(valid_links)
            
            # Обновляем статистику
            self.links_count_label.config(text=f"Загружено ссылок: {total_links}")
            self.valid_links_label.config(text=f"Валидных ссылок: {total_links}")
            
            # Сохраняем ссылки
            self.loaded_links = valid_links
            
            # Активируем кнопку проверки если есть ссылки
            if total_links > 0:
                self.start_mass_check_btn.config(state='normal')
                self.links_file_info.config(text=f"Файл: {self.links_file_path} | Ссылок: {total_links}")
                self.show_mass_notification("Файл загружен", f"Успешно загружено {total_links} ссылок")
            else:
                self.start_mass_check_btn.config(state='disabled')
                self.show_mass_notification("Файл пуст", "Файл links.txt не содержит валидных ссылок")
            
            # Сбрасываем статистику
            self.reset_mass_stats()
            
        except Exception as e:
            self.show_mass_notification("Ошибка загрузки", f"Не удалось загрузить файл:\n{str(e)}")
    
    def create_links_template(self):
        """Создает шаблонный файл links.txt"""
        try:
            template_content = """# Файл links.txt для массовой проверки VK
# Каждая ссылка должна быть на отдельной строке
# Пустые строки и строки начинающиеся с # игнорируются

https://vk.ru/id189241258
https://vk.ru/mgimaev2
https://vk.ru/aeyiii
https://vk.ru/id160203236
https://vk.ru/gorobtsova98
https://vk.ru/id408113538
https://vk.ru/id201188633

# Дополнительные ссылки (примеры):
# https://vk.ru/username
# https://vk.com/id123456789
# vk.ru/id123456789"""
            
            with open(self.links_file_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # Загружаем созданный файл
            self.load_links_file()
            
            self.show_mass_notification("Шаблон создан", f"Файл links.txt создан в папке:\n{self.save_directory}")
            
        except Exception as e:
            self.show_mass_notification("Ошибка создания", f"Не удалось создать шаблон:\n{str(e)}")
    
    def start_mass_check(self):
        """Запускает массовую проверку в отдельном потоке"""
        if not hasattr(self, 'loaded_links') or not self.loaded_links:
            self.show_mass_notification("Нет ссылок", "Сначала загрузите ссылки из файла")
            return
        
        if self.is_mass_checking:
            return
        
        # Сбрасываем статистику
        self.reset_mass_stats()
        
        # Активируем флаг проверки
        self.is_mass_checking = True
        
        # Обновляем кнопки
        self.start_mass_check_btn.config(state='disabled')
        self.stop_mass_check_btn.config(state='normal')
        self.load_btn.config(state='disabled')
        
        # Создаем файл для результатов массовой проверки
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.mass_results_file = os.path.join(self.save_directory, f"mass_check_{timestamp}.txt")
        
        # Записываем заголовок в файл результатов
        with open(self.mass_results_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(" " * 20 + "РЕЗУЛЬТАТЫ МАССОВОЙ ПРОВЕРКИ VK\n")
            f.write("=" * 70 + "\n")
            f.write(f"Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего ссылок: {len(self.loaded_links)}\n")
            f.write("=" * 70 + "\n\n")
        
        # Запускаем проверку в отдельном потоке
        self.checking_thread = threading.Thread(target=self.mass_check_thread)
        self.checking_thread.daemon = True
        self.checking_thread.start()
    
    def mass_check_thread(self):
        """Поток для массовой проверки"""
        total_links = len(self.loaded_links)
        found_count = 0
        not_found_count = 0
        
        for i, link in enumerate(self.loaded_links, 1):
            if not self.is_mass_checking:
                break
            
            # Обновляем прогресс
            progress = (i / total_links) * 100
            self.progress_var.set(progress)
            
            # Обновляем статус
            self.root.after(0, self.update_progress_status, f"Проверка {i}/{total_links}: {link[:50]}...")
            
            # Проверяем ссылку
            vk_id = self.extract_id(link)
            found = vk_id in self.database
            
            # Записываем результат в файл
            with open(self.mass_results_file, 'a', encoding='utf-8') as f:
                if found:
                    data = self.database[vk_id]
                    f.write(f"{i}. ✅ НАЙДЕНО: {link}\n")
                    f.write(f"   Номер: {data['phone']}\n")
                    f.write(f"   ID: {vk_id}\n")
                    f.write(f"   ФИО: {data['fio']}\n")
                    if data['birth']:
                        f.write(f"   Дата рождения: {data['birth']}\n")
                    found_count += 1
                else:
                    f.write(f"{i}. ❌ НЕ НАЙДЕНО: {link}\n")
                    f.write(f"   Извлеченный ID: {vk_id}\n")
                    not_found_count += 1
                f.write("-" * 40 + "\n")
            
            # Обновляем статистику в UI
            self.root.after(0, self.update_mass_stats, found_count, not_found_count, i)
            
            # Небольшая задержка для имитации работы
            time.sleep(0.1)
        
        # Завершаем проверку
        self.root.after(0, self.finish_mass_check, found_count, not_found_count, total_links)
    
    def update_progress_status(self, status):
        """Обновляет статус прогресса"""
        self.progress_status.config(text=status)
    
    def update_mass_stats(self, found, not_found, total):
        """Обновляет статистику массовой проверки"""
        self.found_label.config(text=f"Найдено: {found}")
        self.not_found_label.config(text=f"Не найдено: {not_found}")
        self.total_checked_label.config(text=f"Всего проверено: {total}")
    
    def finish_mass_check(self, found, not_found, total):
        """Завершает массовую проверку"""
        self.is_mass_checking = False
        
        # Обновляем кнопки
        self.start_mass_check_btn.config(state='normal')
        self.stop_mass_check_btn.config(state='disabled')
        self.load_btn.config(state='normal')
        
        # Обновляем прогресс
        self.progress_var.set(100)
        self.progress_status.config(text=f"Проверка завершена! Найдено: {found}, Не найдено: {not_found}")
        
        # Добавляем итоги в файл результатов
        with open(self.mass_results_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 70 + "\n")
            f.write("ИТОГИ ПРОВЕРКИ:\n")
            f.write("=" * 70 + "\n")
            f.write(f"Всего проверено: {total}\n")
            f.write(f"Найдено в базе: {found}\n")
            f.write(f"Не найдено: {not_found}\n")
            f.write(f"Процент успеха: {(found/total*100 if total > 0 else 0):.1f}%\n")
            f.write("=" * 70 + "\n")
        
        # Показываем уведомление
        self.show_mass_notification(
            "Проверка завершена",
            f"Проверено: {total} ссылок\nНайдено: {found}\nНе найдено: {not_found}\n\nРезультаты сохранены в файл:\n{os.path.basename(self.mass_results_file)}"
        )
        
        # Обновляем статус бар
        self.status_bar.config(text=f"✓ Массовая проверка завершена! Проверено: {total}, Найдено: {found}")
    
    def stop_mass_check(self):
        """Останавливает массовую проверку"""
        self.is_mass_checking = False
        
        # Обновляем кнопки
        self.start_mass_check_btn.config(state='normal')
        self.stop_mass_check_btn.config(state='disabled')
        self.load_btn.config(state='normal')
        
        self.progress_status.config(text="Проверка остановлена пользователем")
        self.show_mass_notification("Проверка остановлена", "Массовая проверка была остановлена пользователем")
    
    def reset_mass_stats(self):
        """Сбрасывает статистику массовой проверки"""
        self.found_label.config(text="Найдено: 0")
        self.not_found_label.config(text="Не найдено: 0")
        self.total_checked_label.config(text="Всего проверено: 0")
        self.progress_var.set(0)
        self.progress_status.config(text="Ожидание запуска...")
    
    def show_mass_notification(self, title, message):
        """Показывает уведомление для массовой проверки"""
        # Просто обновляем статус в логе
        self.progress_status.config(text=title + ": " + message[:50] + "...")
    
    # Остальные методы остаются без изменений
    def extract_id(self, url):
        """Извлекает ID из ссылки"""
        # Убираем пробелы
        url = url.strip()
        
        # Убираем префиксы
        prefixes = ['https://vk.ru/', 'https://vk.com/', 'vk.ru/', 'vk.com/', 'http://vk.ru/', 'http://vk.com/']
        
        for prefix in prefixes:
            if url.startswith(prefix):
                url = url.replace(prefix, '')
                break
        
        # Убираем 'id' если есть
        if url.startswith('id'):
            url = url[2:]
        
        # Убираем слэши
        url = url.strip('/')
        
        return url
    
    def check_id(self):
        """Основная функция проверки (одиночная)"""
        url = self.entry.get().strip()
        
        if not url:
            messagebox.showwarning("Внимание", "Введите ссылку VK!")
            return
            
        try:
            vk_id = self.extract_id(url)
            
            # Очищаем таблицу
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Сбрасываем индикатор
            self.save_indicator.config(text="")
            
            # Ищем в базе
            found = False
            result_data = None
            
            # Проверяем точное совпадение
            if vk_id in self.database:
                found = True
                result_data = self.database[vk_id]
            else:
                # Проверяем на частичное совпадение (без префикса id)
                for db_id in self.database.keys():
                    if db_id.endswith(vk_id) or vk_id.endswith(db_id):
                        found = True
                        vk_id = db_id
                        result_data = self.database[db_id]
                        break
            
            if found and result_data:
                data = result_data
                
                # Добавляем данные в таблицу
                rows = [
                    ('🔗 Ссылка VK', url),
                    ('🆔 ID', vk_id),
                    ('📱 Номер телефона', data['phone']),
                    ('👤 ФИО', data['fio'])
                ]
                
                if data['birth']:
                    rows.append(('🎂 Дата рождения', data['birth']))
                
                for row in rows:
                    self.tree.insert('', 'end', values=row)
                
                # Сохраняем в файл
                save_result = self.save_to_file(url, vk_id, data)
                if save_result:
                    self.save_indicator.config(text="✓ Сохранено")
                
                self.status_bar.config(text=f"✓ Найдено: {data['fio']} | ID: {vk_id}")
                
            else:
                self.tree.insert('', 'end', values=('❌ Статус', 'ID не найден в базе данных'))
                self.tree.insert('', 'end', values=('🔍 Введенный ID', vk_id))
                self.tree.insert('', 'end', values=('📊 Записей в базе', str(len(self.database))))
                
                self.status_bar.config(text="✗ ID не найден в базе данных")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{str(e)}")
            self.status_bar.config(text="⚠ Ошибка при проверке")
    
    def save_to_file(self, url, vk_id, data):
        """Сохраняет данные в текстовый файл"""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                line += f"URL: {url} | "
                line += f"Номер: {data['phone']} | "
                line += f"ID: {vk_id} | "
                line += f"ФИО: {data['fio']}"
                if data['birth']:
                    line += f" | Дата рождения: {data['birth']}"
                line += "\n"
                f.write(line)
            return True
        except Exception as e:
            return False
    
    def clear_fields(self):
        """Очищает поля"""
        self.entry.delete(0, 'end')
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.save_indicator.config(text="")
        self.status_bar.config(text="Поля очищены | Готов к работе")
    
    def create_log_file(self):
        """Создает файл для логов если его нет"""
        try:
            if not os.path.exists(self.log_file_path):
                with open(self.log_file_path, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("ЛОГ ПРОВЕРОК VK ID CHECKER\n")
                    f.write("=" * 60 + "\n")
                    f.write(f"Программа запущена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Папка сохранения: {self.save_directory}\n")
                    f.write("=" * 60 + "\n\n")
        except Exception:
            pass
    
    def run(self):
        """Запускает приложение"""
        # Центрируем окно
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
        self.root.mainloop()

if __name__ == "__main__":
    app = VKChecker()
    app.run()