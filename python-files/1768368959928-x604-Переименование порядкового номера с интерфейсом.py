import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
import logging
from datetime import datetime

class FolderRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Number Renamer")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # Настройка стилей
        self.setup_styles()
        
        # Переменные
        self.path_var = tk.StringVar()
        self.operation_var = tk.StringVar(value="decrease")
        self.start_var = tk.StringVar()
        self.end_var = tk.StringVar()
        self.step_var = tk.StringVar(value="1")
        self.folders = []
        self.original_folders = []
        self.changes = {}  # Хранит информацию о предпросмотре
        
        # Настройка логирования
        self.setup_logging()
        
        # Создание интерфейса
        self.create_widgets()
        
    def setup_styles(self):
        """Настройка стилей элементов"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Кастомные стили
        style.configure('Title.TLabel', font=('Helvetica', 16, 'bold'))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Warning.TLabel', foreground='orange')
        style.configure('Error.TLabel', foreground='red')
        
    def setup_logging(self):
        """Настройка логирования"""
        log_dir = Path.home() / "FolderRenamerLogs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка веса строк и столбцов
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame, 
            text="Folder Number Renamer", 
            style='Title.TLabel'
        )
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Блок выбора директории
        dir_frame = ttk.LabelFrame(main_frame, text="Выбор директории", padding="10")
        dir_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="Путь:").grid(row=0, column=0, padx=(0, 5), sticky=tk.W)
        
        path_entry = ttk.Entry(dir_frame, textvariable=self.path_var, width=60)
        path_entry.grid(row=0, column=1, padx=(0, 5), sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(
            dir_frame, 
            text="Обзор...", 
            command=self.browse_directory
        )
        browse_btn.grid(row=0, column=2, padx=(5, 0))
        
        refresh_btn = ttk.Button(
            dir_frame,
            text="Обновить список",
            command=self.load_folders
        )
        refresh_btn.grid(row=0, column=3, padx=(10, 0))
        
        # Блок списка папок
        list_frame = ttk.LabelFrame(main_frame, text="Список папок", padding="10")
        list_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        # Создаем Treeview для отображения папок
        columns = ('#', 'Текущее имя', 'Новое имя', 'Статус', 'Число')
        self.folder_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=12)
        
        # Настройка колонок
        column_widths = {
            '#': 40,
            'Текущее имя': 250,
            'Новое имя': 250,
            'Статус': 150,
            'Число': 80
        }
        
        for col in columns:
            self.folder_tree.heading(col, text=col)
            self.folder_tree.column(col, width=column_widths.get(col, 100))
        
        self.folder_tree.column('#', anchor='center')
        self.folder_tree.column('Число', anchor='center')
        
        # Scrollbar для Treeview
        tree_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.folder_tree.yview)
        self.folder_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Scrollbar горизонтальная
        tree_scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.folder_tree.xview)
        self.folder_tree.configure(xscrollcommand=tree_scrollbar_h.set)
        
        self.folder_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Блок настроек
        settings_frame = ttk.LabelFrame(main_frame, text="Настройки переименования", padding="10")
        settings_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Операция
        ttk.Label(settings_frame, text="Операция:").grid(row=0, column=0, padx=(0, 10), sticky=tk.W)
        
        operation_frame = ttk.Frame(settings_frame)
        operation_frame.grid(row=0, column=1, columnspan=3, sticky=tk.W)
        
        ttk.Radiobutton(
            operation_frame, 
            text="Уменьшить номер", 
            variable=self.operation_var, 
            value="decrease",
            command=self.on_operation_change
        ).pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Radiobutton(
            operation_frame, 
            text="Увеличить номер", 
            variable=self.operation_var, 
            value="increase",
            command=self.on_operation_change
        ).pack(side=tk.LEFT)
        
        # Шаг изменения
        ttk.Label(settings_frame, text="Шаг изменения:").grid(row=1, column=0, pady=(10, 0), padx=(0, 10), sticky=tk.W)
        
        step_frame = ttk.Frame(settings_frame)
        step_frame.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        self.step_spinbox = ttk.Spinbox(
            step_frame,
            from_=1,
            to=999,
            textvariable=self.step_var,
            width=10,
            validate='key',
            validatecommand=(self.root.register(self.validate_step), '%P')
        )
        self.step_spinbox.pack(side=tk.LEFT)
        ttk.Label(step_frame, text="(целое положительное число)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Диапазон
        ttk.Label(settings_frame, text="Диапазон папок:").grid(row=2, column=0, pady=(10, 0), padx=(0, 10), sticky=tk.W)
        
        range_frame = ttk.Frame(settings_frame)
        range_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, pady=(10, 0))
        
        ttk.Label(range_frame, text="С").pack(side=tk.LEFT)
        self.start_spinbox = ttk.Spinbox(
            range_frame, 
            from_=1, 
            to=1000, 
            textvariable=self.start_var, 
            width=10,
            validate='key',
            validatecommand=(self.root.register(self.validate_range), '%P')
        )
        self.start_spinbox.pack(side=tk.LEFT, padx=(5, 20))
        
        ttk.Label(range_frame, text="По").pack(side=tk.LEFT)
        self.end_spinbox = ttk.Spinbox(
            range_frame, 
            from_=1, 
            to=1000, 
            textvariable=self.end_var, 
            width=10,
            validate='key',
            validatecommand=(self.root.register(self.validate_range), '%P')
        )
        self.end_spinbox.pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(
            range_frame,
            text="Весь список",
            command=self.select_all_folders,
            width=12
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # Блок информации о предпросмотре
        self.info_frame = ttk.LabelFrame(main_frame, text="Информация о предпросмотре", padding="10")
        self.info_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        self.info_frame.grid_remove()  # Скрываем до предпросмотра
        
        self.info_label = ttk.Label(self.info_frame, text="")
        self.info_label.grid(row=0, column=0, sticky=tk.W)
        
        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=4, pady=(10, 0))
        
        self.preview_btn = ttk.Button(
            button_frame,
            text="🔍 Предпросмотр изменений",
            command=self.preview_changes,
            state='disabled',
            width=25
        )
        self.preview_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.execute_btn = ttk.Button(
            button_frame,
            text="✅ Выполнить переименование",
            command=self.execute_renaming,
            state='disabled',
            width=25
        )
        self.execute_btn.pack(side=tk.LEFT)
        
        # Блок лога операций
        log_frame = ttk.LabelFrame(main_frame, text="Лог операций", padding="10")
        log_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN,
            padding=(5, 2)
        )
        status_bar.grid(row=7, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def validate_step(self, value):
        """Валидация шага изменения"""
        if value == "":
            return True
        try:
            num = int(value)
            return 1 <= num <= 999
        except ValueError:
            return False
            
    def validate_range(self, value):
        """Валидация диапазона"""
        if value == "":
            return True
        try:
            int(value)
            return True
        except ValueError:
            return False
            
    def on_operation_change(self):
        """Обработчик изменения операции"""
        if hasattr(self, 'changes') and self.changes:
            self.preview_changes()
            
    def select_all_folders(self):
        """Выбрать весь список папок"""
        if self.folders:
            self.start_var.set("1")
            self.end_var.set(str(len(self.folders)))
            
    def browse_directory(self):
        """Открыть диалог выбора директории"""
        path = filedialog.askdirectory(title="Выберите директорию")
        if path:
            self.path_var.set(path)
            self.load_folders()
            
    def extract_number(self, folder_name):
        """Извлекает число из начала имени папки"""
        match = re.match(r'^(\d+)', folder_name)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None
        
    def log_message(self, message, level="INFO"):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Добавляем в текстовый виджет
        self.log_text.insert(tk.END, formatted_message + "\n")
        self.log_text.see(tk.END)
        
        # Цветовое выделение
        if level == "ERROR":
            self.log_text.tag_add("error", "end-2l", "end-1l")
            self.log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            self.log_text.tag_add("warning", "end-2l", "end-1l")
            self.log_text.tag_config("warning", foreground="orange")
        elif level == "SUCCESS":
            self.log_text.tag_add("success", "end-2l", "end-1l")
            self.log_text.tag_config("success", foreground="green")
            
    def load_folders(self):
        """Загрузка списка папок из выбранной директории"""
        path = self.path_var.get().strip()
        
        if not path:
            messagebox.showwarning("Внимание", "Укажите путь к директории")
            return
            
        if not os.path.isdir(path):
            messagebox.showerror("Ошибка", "Указанная директория не существует!")
            return
            
        # Получение списка папок
        try:
            items = os.listdir(path)
            self.folders = [
                item for item in items 
                if os.path.isdir(os.path.join(path, item))
            ]
            
            # Сортировка по числу в начале имени
            self.folders.sort(key=lambda x: self.extract_number(x) or float('inf'))
            self.original_folders = self.folders.copy()
            
            # Обновление Treeview
            self.update_folder_list()
            
            # Обновление состояния кнопок
            if self.folders:
                self.preview_btn.config(state='normal')
                self.execute_btn.config(state='normal')
                self.status_var.set(f"Найдено {len(self.folders)} папок")
                self.log_message(f"Загружено {len(self.folders)} папок из {path}")
                
                # Установка диапазона по умолчанию
                self.select_all_folders()
            else:
                self.preview_btn.config(state='disabled')
                self.execute_btn.config(state='disabled')
                self.status_var.set("В указанной директории нет папок")
                self.log_message("В указанной директории нет папок", "WARNING")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить список папок: {str(e)}")
            self.log_message(f"Ошибка загрузки папок: {str(e)}", "ERROR")
            
    def update_folder_list(self, changes=None):
        """Обновление списка папок в Treeview"""
        # Очистка Treeview
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
            
        # Заполнение данными
        for i, folder in enumerate(self.folders, 1):
            current_number = self.extract_number(folder)
            new_name = folder
            status = "Не изменена"
            new_number = ""
            
            if changes and i-1 in changes:
                new_name = changes[i-1]['new_name']
                status = changes[i-1]['status']
                if new_name != folder:
                    new_number = self.extract_number(new_name) or ""
                    
            self.folder_tree.insert(
                '', 
                'end', 
                values=(
                    i, 
                    folder, 
                    new_name if new_name != folder else "",
                    status,
                    f"{current_number} → {new_number}" if new_number and new_number != current_number else current_number or ""
                )
            )
            
    def calculate_new_name(self, old_name, operation, step):
        """Вычисление нового имени папки"""
        match = re.match(r'^(\d+)', old_name)
        if not match:
            return old_name, "Нет числа в начале", None
            
        try:
            current_number = int(match.group(1))
            step_int = int(step)
            
            if operation == "decrease":
                new_number = current_number - step_int
                if new_number < 0:
                    return old_name, "Отрицательный номер", None
            else:  # increase
                new_number = current_number + step_int
                
            # Заменяем только первое вхождение числа
            new_name = re.sub(r'^\d+', str(new_number), old_name, count=1)
            
            return new_name, "Готово", new_number
            
        except ValueError:
            return old_name, "Ошибка числа", None
            
    def preview_changes(self):
        """Предпросмотр изменений"""
        path = self.path_var.get().strip()
        if not path or not self.folders:
            return
            
        try:
            start = int(self.start_var.get()) if self.start_var.get() else 1
            end = int(self.end_var.get()) if self.end_var.get() else len(self.folders)
            step = int(self.step_var.get()) if self.step_var.get() else 1
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа для диапазона и шага!")
            self.log_message("Ошибка ввода данных", "ERROR")
            return
            
        # Проверка валидности диапазона
        if start < 1 or end > len(self.folders) or start > end:
            messagebox.showerror("Ошибка", "Некорректный диапазон!")
            self.log_message("Некорректный диапазон", "ERROR")
            return
            
        if step < 1:
            messagebox.showerror("Ошибка", "Шаг должен быть положительным числом!")
            self.log_message("Шаг должен быть положительным числом", "ERROR")
            return
            
        operation = self.operation_var.get()
        self.changes = {}
        conflicts = 0
        
        # Проверка на конфликты
        for i in range(start-1, end):
            old_name = self.folders[i]
            new_name, status, new_number = self.calculate_new_name(old_name, operation, step)
            
            old_path = os.path.join(path, old_name)
            new_path = os.path.join(path, new_name)
            
            # Проверка существования нового имени
            if new_name != old_name and os.path.exists(new_path):
                status = "Конфликт имен"
                conflicts += 1
                
            self.changes[i] = {
                'old_name': old_name,
                'new_name': new_name,
                'status': status,
                'new_number': new_number
            }
            
        self.update_folder_list(self.changes)
        
        # Показываем информационный блок
        self.info_frame.grid()
        
        # Статистика
        total = end - start + 1
        operation_text = "уменьшение" if operation == "decrease" else "увеличение"
        
        info_text = (
            f"Будет переименовано папок: {total}\n"
            f"Операция: {operation_text} на {step}\n"
            f"Диапазон: папки с {start} по {end}\n"
        )
        
        if conflicts > 0:
            info_text += f"⚠ Найдено конфликтов: {conflicts}"
            self.info_label.config(style='Warning.TLabel')
        else:
            self.info_label.config(style='')
            
        self.info_label.config(text=info_text)
        self.status_var.set(f"Предпросмотр: {operation_text} номеров на {step}")
        
        self.log_message(f"Предпросмотр: {operation_text} на {step} в диапазоне {start}-{end}")
        
    def execute_renaming(self):
        """Выполнение переименования"""
        path = self.path_var.get().strip()
        if not path:
            return
            
        # Проверяем, есть ли предпросмотр
        if not self.changes:
            messagebox.showwarning("Внимание", "Сначала выполните предпросмотр изменений!")
            return
            
        try:
            start = int(self.start_var.get()) if self.start_var.get() else 1
            end = int(self.end_var.get()) if self.end_var.get() else len(self.folders)
            step = int(self.step_var.get()) if self.step_var.get() else 1
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректные числа для диапазона и шага!")
            return
            
        if start < 1 or end > len(self.folders) or start > end:
            messagebox.showerror("Ошибка", "Некорректный диапазон!")
            return
            
        # Подтверждение действия
        operation_text = "уменьшение" if self.operation_var.get() == "decrease" else "увеличение"
        confirm_text = (
            f"Выполнить {operation_text} номеров папок на {step}?\n\n"
            f"Диапазон: папки с {start} по {end}\n"
            f"Всего папок: {end - start + 1}\n\n"
            "Вы уверены?"
        )
        
        confirm = messagebox.askyesno(
            "Подтверждение переименования",
            confirm_text
        )
        
        if not confirm:
            self.log_message("Операция отменена пользователем", "WARNING")
            return
            
        operation = self.operation_var.get()
        successful = 0
        failed = 0
        changes_made = []
        
        self.log_message(f"Начало переименования: {operation_text} на {step}", "INFO")
        
        for i in range(start-1, end):
            if i not in self.changes:
                continue
                
            change_info = self.changes[i]
            old_name = change_info['old_name']
            new_name = change_info['new_name']
            
            if new_name == old_name:
                failed += 1
                self.log_message(f"Пропущено: {old_name} ({change_info['status']})", "WARNING")
                continue
                
            old_path = os.path.join(path, old_name)
            new_path = os.path.join(path, new_name)
            
            # Двойная проверка конфликта имен
            if os.path.exists(new_path):
                self.log_message(f"Конфликт: {new_name} уже существует", "ERROR")
                failed += 1
                continue
                
            try:
                # Переименование
                os.rename(old_path, new_path)
                successful += 1
                
                # Логирование
                log_msg = f"Успешно: {old_name} → {new_name}"
                self.log_message(log_msg, "SUCCESS")
                
                # Запись для обновления списка
                changes_made.append((old_name, new_name))
                
            except PermissionError:
                error_msg = f"Ошибка доступа: нет прав для переименования {old_name}"
                self.log_message(error_msg, "ERROR")
                failed += 1
            except Exception as e:
                error_msg = f"Ошибка при переименовании {old_name}: {str(e)}"
                self.log_message(error_msg, "ERROR")
                failed += 1
                
        # Обновление списка папок
        for old_name, new_name in changes_made:
            if old_name in self.folders:
                idx = self.folders.index(old_name)
                self.folders[idx] = new_name
                
        # Обновление интерфейса
        self.update_folder_list()
        self.changes.clear()  # Очищаем предпросмотр
        self.info_frame.grid_remove()
        
        # Вывод результатов
        result_text = (
            f"Переименование завершено!\n\n"
            f"✓ Успешно: {successful}\n"
            f"✗ Не удалось: {failed}\n"
            f"▷ Всего обработано: {successful + failed}"
        )
        
        if successful > 0:
            messagebox.showinfo("Готово", result_text)
            self.status_var.set(f"Успешно переименовано {successful} из {successful + failed} папок")
            self.log_message(f"Переименование завершено. Успешно: {successful}, Не удалось: {failed}", "SUCCESS")
        else:
            messagebox.showwarning("Результат", result_text)
            self.status_var.set("Переименование не выполнено")
            
        # Очистка лога если слишком много записей
        if self.log_text.index('end-1c').split('.')[0] > 100:
            self.log_text.delete(1.0, tk.END)

def main():
    """Запуск приложения"""
    root = tk.Tk()
    app = FolderRenamerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()