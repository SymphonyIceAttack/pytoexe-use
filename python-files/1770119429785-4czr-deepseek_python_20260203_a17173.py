import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import re
from collections import defaultdict
import csv
import json

class PCFParserGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Парсер PCF-файлов - Фланцевые соединения")
        self.root.geometry("1400x700")
        
        # Переменные
        self.files = []  # Список файлов
        self.results = []  # Результаты анализа
        
        # Создание интерфейса
        self.create_widgets()
    
    def create_widgets(self):
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов строк и столбцов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Кнопки управления
        ttk.Button(main_frame, text="Добавить файлы", 
                  command=self.add_files).grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        ttk.Button(main_frame, text="Добавить папку", 
                  command=self.add_folder).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Button(main_frame, text="Анализировать", 
                  command=self.analyze_files).grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Button(main_frame, text="Экспорт в CSV", 
                  command=self.export_csv).grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        ttk.Button(main_frame, text="Очистить", 
                  command=self.clear_all).grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        
        # Список файлов
        ttk.Label(main_frame, text="Выбранные файлы:").grid(row=1, column=0, columnspan=5, 
                                                          sticky=tk.W, padx=5, pady=(10, 0))
        
        # Treeview для файлов
        self.file_tree = ttk.Treeview(main_frame, columns=("file", "status"), 
                                     show="headings", height=5)
        self.file_tree.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), 
                           padx=5, pady=5)
        self.file_tree.heading("file", text="Файл")
        self.file_tree.heading("status", text="Статус")
        self.file_tree.column("file", width=400)
        self.file_tree.column("status", width=150)
        
        # Скроллбар для списка файлов
        file_scrollbar = ttk.Scrollbar(main_frame, orient="vertical", 
                                      command=self.file_tree.yview)
        file_scrollbar.grid(row=2, column=5, sticky=(tk.N, tk.S), pady=5)
        self.file_tree.configure(yscrollcommand=file_scrollbar.set)
        
        # Таблица результатов
        ttk.Label(main_frame, text="Результаты анализа:").grid(row=3, column=0, 
                                                              columnspan=6, sticky=tk.W, 
                                                              padx=5, pady=(10, 0))
        
        # Treeview для результатов
        columns = ("№", "Файл", "Альбом", "Линия", "Зона", "Код фланца", 
                  "Описание фланца", "Код болта", "Кол-во болтов", 
                  "Код гайки", "Кол-во гаек", "Всего")
        
        self.result_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=15)
        self.result_tree.grid(row=4, column=0, columnspan=6, sticky=(tk.W, tk.E, tk.N, tk.S), 
                             padx=5, pady=5)
        
        # Настройка колонок
        col_widths = [40, 120, 100, 80, 80, 100, 200, 100, 80, 100, 80, 60]
        for col, width in zip(columns, col_widths):
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=width, anchor="center")
        
        # Скроллбары для результатов
        result_scrollbar_v = ttk.Scrollbar(main_frame, orient="vertical", 
                                          command=self.result_tree.yview)
        result_scrollbar_v.grid(row=4, column=6, sticky=(tk.N, tk.S), pady=5)
        
        result_scrollbar_h = ttk.Scrollbar(main_frame, orient="horizontal", 
                                          command=self.result_tree.xview)
        result_scrollbar_h.grid(row=5, column=0, columnspan=6, sticky=(tk.W, tk.E), 
                               padx=5)
        
        self.result_tree.configure(yscrollcommand=result_scrollbar_v.set,
                                  xscrollcommand=result_scrollbar_h.set)
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, columnspan=7, sticky=(tk.W, tk.E), 
                       padx=5, pady=(5, 0))
    
    def add_files(self):
        """Добавление файлов"""
        filetypes = [
            ("PCF файлы", "*.pcf *.PCF"),
            ("Текстовые файлы", "*.txt"),
            ("Все файлы", "*.*")
        ]
        
        files = filedialog.askopenfilenames(title="Выберите PCF файлы", filetypes=filetypes)
        for file_path in files:
            self.add_single_file(file_path)
    
    def add_folder(self):
        """Добавление папки с файлами"""
        folder = filedialog.askdirectory(title="Выберите папку с PCF файлами")
        if folder:
            extensions = ('.pcf', '.PCF', '.txt')
            for root_dir, dirs, files in os.walk(folder):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in extensions):
                        file_path = os.path.join(root_dir, file)
                        self.add_single_file(file_path)
    
    def add_single_file(self, file_path):
        """Добавление одного файла в список"""
        if not os.path.exists(file_path):
            return
        
        # Проверяем, не добавлен ли уже файл
        for item in self.file_tree.get_children():
            if self.file_tree.item(item, 'values')[0] == file_path:
                return
        
        # Добавляем файл
        self.files.append(file_path)
        self.file_tree.insert("", "end", values=(file_path, "В ожидании"))
        self.status_var.set(f"Добавлен файл: {os.path.basename(file_path)}")
    
    def analyze_files(self):
        """Анализ всех файлов"""
        if not self.files:
            messagebox.showwarning("Внимание", "Сначала добавьте файлы для анализа!")
            return
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        total_connections = 0
        
        for idx, file_path in enumerate(self.files):
            try:
                # Обновляем статус файла
                for item in self.file_tree.get_children():
                    if self.file_tree.item(item, 'values')[0] == file_path:
                        self.file_tree.item(item, values=(file_path, "Анализ..."))
                        self.root.update()
                        break
                
                # Анализируем файл
                connections = self.analyze_single_file(file_path)
                total_connections += len(connections)
                
                # Отображаем результаты
                for i, conn in enumerate(connections, start=len(self.results) + 1):
                    self.result_tree.insert("", "end", values=(
                        i,
                        os.path.basename(file_path),
                        conn.get('album', ''),
                        conn.get('pipeline', ''),
                        conn.get('zone', ''),
                        conn.get('flange_code', ''),
                        conn.get('flange_desc', '')[:100] + "..." if len(conn.get('flange_desc', '')) > 100 else conn.get('flange_desc', ''),
                        conn.get('bolt_code', ''),
                        conn.get('bolt_qty', ''),
                        conn.get('nut_code', ''),
                        conn.get('nut_qty', ''),
                        conn.get('total', '')
                    ))
                    self.results.append(conn)
                
                # Обновляем статус файла
                for item in self.file_tree.get_children():
                    if self.file_tree.item(item, 'values')[0] == file_path:
                        self.file_tree.item(item, values=(file_path, f"✓ {len(connections)} соедин."))
                        break
                
            except Exception as e:
                self.status_var.set(f"Ошибка в файле {os.path.basename(file_path)}: {str(e)}")
                for item in self.file_tree.get_children():
                    if self.file_tree.item(item, 'values')[0] == file_path:
                        self.file_tree.item(item, values=(file_path, "Ошибка"))
                        break
        
        self.status_var.set(f"Анализ завершен. Найдено {total_connections} соединений в {len(self.files)} файлах")
    
    def analyze_single_file(self, file_path):
        """Анализ одного PCF файла"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Извлекаем общую информацию
        album = self.extract_value(content, 'ATTRIBUTE67')
        pipeline = self.extract_value(content, 'PIPELINE-REFERENCE')
        zone = self.extract_value(content, 'ATTRIBUTE61')
        
        # Ищем все фланцы FLWN и связанные компоненты
        connections = []
        
        # Разбиваем файл на секции
        sections = self.split_into_sections(content)
        
        # Собираем все компоненты
        components = {}
        for section in sections:
            if section['type'] in ['FLANGE', 'BOLT', 'ADDITIONAL-ITEM']:
                comp_id = section.get('COMPONENT-IDENTIFIER')
                if comp_id:
                    components[comp_id] = section
        
        # Ищем фланцы FLWN
        for comp_id, comp in components.items():
            if comp['type'] == 'FLANGE' and 'FLWN' in comp.get('SKEY', ''):
                # Найден фланец FLWN, ищем связанные болты
                flange_code = comp.get('ITEM-CODE', '')
                flange_desc = comp.get('ITEM-DESCRIPTION', '')
                
                # Ищем болты, привязанные к этому фланцу
                for bolt_id, bolt in components.items():
                    if (bolt['type'] == 'BOLT' and 
                        bolt.get('MASTER-COMPONENT-IDENTIFIER') == comp_id):
                        
                        # Находим гайки для этого болта
                        for nut_id, nut in components.items():
                            if (nut['type'] == 'ADDITIONAL-ITEM' and 
                                nut.get('MASTER-COMPONENT-IDENTIFIER') == bolt_id and
                                self.is_nut(nut)):
                                
                                # Подсчитываем количество
                                try:
                                    bolt_qty = int(bolt.get('BOLT-QUANTITY', '0'))
                                    nut_qty = int(nut.get('BOLT-QUANTITY', '0'))
                                    total = bolt_qty + nut_qty
                                except:
                                    bolt_qty = 0
                                    nut_qty = 0
                                    total = 0
                                
                                connection = {
                                    'album': album,
                                    'pipeline': pipeline,
                                    'zone': zone,
                                    'flange_code': flange_code,
                                    'flange_desc': flange_desc,
                                    'bolt_code': bolt.get('BOLT-ITEM-CODE', ''),
                                    'bolt_qty': str(bolt_qty),
                                    'nut_code': nut.get('BOLT-ITEM-CODE', ''),
                                    'nut_qty': str(nut_qty),
                                    'total': str(total)
                                }
                                connections.append(connection)
        
        return connections
    
    def split_into_sections(self, content):
        """Разбивает PCF файл на секции"""
        sections = []
        current_section = None
        current_type = None
        
        for line in content.split('\n'):
            line = line.rstrip()
            
            if not line:
                if current_section:
                    sections.append(current_section)
                    current_section = None
                continue
            
            # Проверяем, начинается ли новая секция
            if not line.startswith(' ') and not line.startswith('\t'):
                # Сохраняем предыдущую секцию
                if current_section:
                    sections.append(current_section)
                
                # Начинаем новую секцию
                current_type = line.strip()
                current_section = {'type': current_type}
            else:
                # Это атрибут текущей секции
                if current_section is not None:
                    parts = line.strip().split(None, 1)
                    if len(parts) == 2:
                        key, value = parts
                        current_section[key] = value
        
        # Добавляем последнюю секцию
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def extract_value(self, content, key):
        """Извлекает значение по ключу из контента"""
        pattern = rf'{key}\s+(\S+)'
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return ''
    
    def is_nut(self, component):
        """Проверяет, является ли компонент гайкой"""
        desc = component.get('BOLT-ITEM-DESCRIPTION', '').upper()
        item_group = component.get('ITEM-GROUP', '').upper()
        
        if 'ГАЙКА' in desc or 'NUT' in desc or item_group == 'BOLT':
            return True
        return False
    
    def export_csv(self):
        """Экспорт результатов в CSV"""
        if not self.results:
            messagebox.showwarning("Внимание", "Нет данных для экспорта!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV файлы", "*.csv"), ("Все файлы", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Заголовки
                writer.writerow(['№', 'Файл', 'Альбом', 'Линия', 'Зона', 
                                'Код фланца', 'Описание фланца', 'Код болта', 
                                'Кол-во болтов', 'Код гайки', 'Кол-во гаек', 'Всего'])
                
                # Данные
                for idx, result in enumerate(self.results, 1):
                    writer.writerow([
                        idx,
                        result.get('file', ''),
                        result.get('album', ''),
                        result.get('pipeline', ''),
                        result.get('zone', ''),
                        result.get('flange_code', ''),
                        result.get('flange_desc', ''),
                        result.get('bolt_code', ''),
                        result.get('bolt_qty', ''),
                        result.get('nut_code', ''),
                        result.get('nut_qty', ''),
                        result.get('total', '')
                    ])
            
            self.status_var.set(f"Данные экспортированы в {os.path.basename(filename)}")
            messagebox.showinfo("Успех", f"Данные успешно экспортированы в CSV файл:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при экспорте в CSV:\n{str(e)}")
    
    def clear_results(self):
        """Очистка результатов анализа"""
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.results = []
    
    def clear_files(self):
        """Очистка списка файлов"""
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.files = []
    
    def clear_all(self):
        """Очистка всего"""
        self.clear_results()
        self.clear_files()
        self.status_var.set("Готов к работе")

def main():
    root = tk.Tk()
    app = PCFParserGUI(root)
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()