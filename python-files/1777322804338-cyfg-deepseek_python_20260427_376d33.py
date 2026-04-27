import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3
import pandas as pd
import os
from datetime import datetime

class DatabaseMerger:
    def __init__(self, root):
        self.root = root
        self.root.title("Объединение баз данных с тегами")
        self.root.geometry("900x700")
        
        # Список выбранных файлов
        self.selected_files = []
        
        # Создание интерфейса
        self.create_widgets()
        
    def create_widgets(self):
        # Заголовок
        title_label = ttk.Label(self.root, text="Объединение баз данных", 
                                font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Фрейм для выбора файлов
        files_frame = ttk.LabelFrame(self.root, text="Выбор файлов для объединения", 
                                     padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Кнопки управления файлами
        btn_frame = ttk.Frame(files_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Добавить файлы", 
                  command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить выбранный", 
                  command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить список", 
                  command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # Список файлов
        self.files_listbox = tk.Listbox(files_frame, height=8, selectmode=tk.EXTENDED)
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, 
                                 command=self.files_listbox.yview)
        self.files_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Фрейм для тегов
        tags_frame = ttk.LabelFrame(self.root, text="Теги для объединенной базы", 
                                    padding=10)
        tags_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tags_input_frame = ttk.Frame(tags_frame)
        tags_input_frame.pack(fill=tk.X)
        
        ttk.Label(tags_input_frame, text="Теги (через запятую):").pack(side=tk.LEFT, padx=5)
        self.tags_entry = ttk.Entry(tags_input_frame, width=50)
        self.tags_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.tags_entry.insert(0, "")
        
        # Фрейм для настроек
        settings_frame = ttk.LabelFrame(self.root, text="Настройки", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Выбор формата выходного файла
        ttk.Label(settings_frame, text="Формат выходного файла:").grid(row=0, column=0, 
                                                                        sticky=tk.W, padx=5)
        self.output_format = ttk.Combobox(settings_frame, values=['SQLite', 'CSV', 'Excel'], 
                                          state='readonly', width=15)
        self.output_format.set('SQLite')
        self.output_format.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Опция добавления столбца с именем исходного файла
        self.add_source_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Добавить столбец с источником", 
                       variable=self.add_source_var).grid(row=1, column=0, columnspan=2, 
                                                          sticky=tk.W, padx=5, pady=5)
        
        # Опция удаления дубликатов
        self.remove_dupes_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Удалить дубликаты", 
                       variable=self.remove_dupes_var).grid(row=2, column=0, columnspan=2,
                                                           sticky=tk.W, padx=5)
        
        # Фрейм для вывода информации
        info_frame = ttk.LabelFrame(self.root, text="Информация", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Текстовое поле для лога
        self.log_text = tk.Text(info_frame, height=10, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, 
                                     command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка объединения
        self.merge_btn = ttk.Button(self.root, text="Объединить базы данных", 
                                   command=self.merge_databases, 
                                   style='Accent.TButton')
        self.merge_btn.pack(pady=10)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Выберите файлы баз данных",
            filetypes=[
                ("Все поддерживаемые форматы", "*.db;*.sqlite;*.csv;*.xlsx;*.xls"),
                ("SQLite базы данных", "*.db;*.sqlite"),
                ("CSV файлы", "*.csv"),
                ("Excel файлы", "*.xlsx;*.xls"),
                ("Все файлы", "*.*")
            ]
        )
        
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.files_listbox.insert(tk.END, os.path.basename(file))
                self.log(f"Добавлен файл: {file}")
                
    def remove_selected(self):
        selected = self.files_listbox.curselection()
        for idx in reversed(selected):
            self.files_listbox.delete(idx)
            del self.selected_files[idx]
            self.log(f"Файл удален из списка")
            
    def clear_files(self):
        self.files_listbox.delete(0, tk.END)
        self.selected_files.clear()
        self.log("Список файлов очищен")
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def read_file(self, file_path):
        """Чтение файла в DataFrame"""
        ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if ext in ['.db', '.sqlite']:
                conn = sqlite3.connect(file_path)
                
                # Получаем все таблицы
                tables = pd.read_sql_query(
                    "SELECT name FROM sqlite_master WHERE type='table';", conn
                )
                
                if tables.empty:
                    raise Exception("В базе данных нет таблиц")
                
                # Читаем первую таблицу (или можно спросить пользователя)
                table_name = tables.iloc[0]['name']
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                conn.close()
                
            elif ext == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
                
            elif ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
                
            else:
                raise Exception(f"Неподдерживаемый формат файла: {ext}")
                
            return df
            
        except Exception as e:
            self.log(f"Ошибка при чтении файла {file_path}: {str(e)}")
            return None
            
    def merge_databases(self):
        if not self.selected_files:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы один файл для объединения!")
            return
            
        self.progress.start()
        self.merge_btn.configure(state='disabled')
        
        try:
            # Получаем теги
            tags = [tag.strip() for tag in self.tags_entry.get().split(',') if tag.strip()]
            
            # Список для хранения DataFrame'ов
            dataframes = []
            
            # Читаем все файлы
            for file_path in self.selected_files:
                self.log(f"Чтение файла: {file_path}")
                df = self.read_file(file_path)
                
                if df is not None:
                    # Добавляем столбец с источником если нужно
                    if self.add_source_var.get():
                        df['source_file'] = os.path.basename(file_path)
                    
                    # Добавляем теги если они указаны
                    if tags:
                        df['tags'] = ', '.join(tags)
                    
                    dataframes.append(df)
                    self.log(f"Прочитано {len(df)} записей из {os.path.basename(file_path)}")
                    
            if not dataframes:
                raise Exception("Не удалось прочитать ни одного файла")
                
            # Объединяем все DataFrame'ы
            self.log("Объединение данных...")
            merged_df = pd.concat(dataframes, ignore_index=True)
            
            # Удаляем дубликаты если нужно
            if self.remove_dupes_var.get():
                initial_count = len(merged_df)
                merged_df = merged_df.drop_duplicates()
                self.log(f"Удалено {initial_count - len(merged_df)} дубликатов")
                
            # Сохраняем результат
            self.save_merged_data(merged_df, tags)
            
            self.log(f"Объединение завершено! Всего записей: {len(merged_df)}")
            messagebox.showinfo("Успех", f"Базы данных успешно объединены!\nВсего записей: {len(merged_df)}")
            
        except Exception as e:
            self.log(f"Ошибка при объединении: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось объединить базы данных: {str(e)}")
            
        finally:
            self.progress.stop()
            self.merge_btn.configure(state='normal')
            
    def save_merged_data(self, df, tags):
        """Сохранение объединенных данных"""
        output_format = self.output_format.get()
        
        if output_format == 'SQLite':
            file_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("SQLite база данных", "*.db")]
            )
            if file_path:
                conn = sqlite3.connect(file_path)
                df.to_sql('merged_data', conn, if_exists='replace', index=False)
                
                # Создаем таблицу с метаданными
                metadata = pd.DataFrame({
                    'merge_date': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    'source_files': [', '.join([os.path.basename(f) for f in self.selected_files])],
                    'tags': [', '.join(tags)],
                    'total_records': [len(df)]
                })
                metadata.to_sql('merge_metadata', conn, if_exists='replace', index=False)
                conn.close()
                self.log(f"Данные сохранены в SQLite: {file_path}")
                
        elif output_format == 'CSV':
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV файл", "*.csv")]
            )
            if file_path:
                df.to_csv(file_path, index=False, encoding='utf-8')
                self.log(f"Данные сохранены в CSV: {file_path}")
                
        elif output_format == 'Excel':
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel файл", "*.xlsx")]
            )
            if file_path:
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Merged Data', index=False)
                    
                    # Добавляем лист с метаданными
                    metadata = pd.DataFrame({
                        'Свойство': ['Дата объединения', 'Исходные файлы', 'Теги', 'Всего записей'],
                        'Значение': [
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            '\n'.join([os.path.basename(f) for f in self.selected_files]),
                            ', '.join(tags),
                            len(df)
                        ]
                    })
                    metadata.to_excel(writer, sheet_name='Metadata', index=False)
                self.log(f"Данные сохранены в Excel: {file_path}")

def main():
    root = tk.Tk()
    app = DatabaseMerger(root)
    
    # Настройка стиля
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Arial', 11, 'bold'))
    
    root.mainloop()

if __name__ == "__main__":
    main()