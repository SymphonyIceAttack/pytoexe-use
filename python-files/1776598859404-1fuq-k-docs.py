import os
import shutil
import threading
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class FileOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("📁 File Organizer Pro v2.0 - Windows 11")
        self.root.geometry("850x650")
        self.root.resizable(True, True)
        
        # Категории файлов
        self.categories = {
            '📷 Изображения': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico', '.svg', '.raw'],
            '🎵 Музыка': ['.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'],
            '🎬 Видео': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            '📄 Документы': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx', '.md'],
            '🗜️ Архивы': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso'],
            '💻 Программы': ['.exe', '.msi', '.bat', '.cmd', '.ps1', '.sh', '.appx'],
            '📁 Код': ['.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.php', '.rb', '.go', '.rs', '.json', '.xml'],
            '⚙️ Настройки': ['.ini', '.cfg', '.conf', '.reg', '.config'],
        }
        self.misc_folder = '📂 Прочее'
        
        # Выбранные категории (все по умолчанию)
        self.selected_categories = {cat: True for cat in self.categories.keys()}
        
        # Переменные
        self.source_path = tk.StringVar()  # Откуда берем файлы
        self.dest_path = tk.StringVar()    # Куда перемещаем
        self.operation_mode = tk.StringVar(value="move")  # move или copy
        self.status_text = tk.StringVar(value="Готов к работе")
        self.progress_value = tk.IntVar(value=0)
        
        self.setup_ui()
        
    def setup_ui(self):
        # Стиль
        style = ttk.Style()
        style.theme_use('vista' if 'vista' in style.theme_names() else 'default')
        
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="📁 File Organizer Pro v2.0", 
                                font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Исходная папка (откуда берем)
        source_frame = ttk.LabelFrame(main_frame, text="📂 Исходная папка (откуда взять файлы)", padding="10")
        source_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        source_frame.columnconfigure(0, weight=1)
        
        source_entry = ttk.Entry(source_frame, textvariable=self.source_path, font=('Segoe UI', 10))
        source_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        source_browse_btn = ttk.Button(source_frame, text="Обзор", command=self.browse_source)
        source_browse_btn.grid(row=0, column=1)
        
        quick_buttons_frame = ttk.Frame(source_frame)
        quick_buttons_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(quick_buttons_frame, text="📂 Рабочий стол", 
                  command=lambda: self.source_path.set(str(Path.home() / 'Desktop'))).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="⬇️ Загрузки", 
                  command=lambda: self.source_path.set(str(Path.home() / 'Downloads'))).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons_frame, text="📁 Текущая папка", 
                  command=lambda: self.source_path.set(os.getcwd())).pack(side=tk.LEFT, padx=2)
        
        # Целевая папка (куда перемещаем) - НОВАЯ ФУНКЦИЯ!
        dest_frame = ttk.LabelFrame(main_frame, text="🎯 Целевая папка (куда переместить файлы)", padding="10")
        dest_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dest_frame.columnconfigure(0, weight=1)
        
        dest_entry = ttk.Entry(dest_frame, textvariable=self.dest_path, font=('Segoe UI', 10))
        dest_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        dest_browse_btn = ttk.Button(dest_frame, text="Обзор", command=self.browse_dest)
        dest_browse_btn.grid(row=0, column=1)
        
        # Быстрые варианты для целевой папки
        dest_quick_frame = ttk.Frame(dest_frame)
        dest_quick_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(dest_quick_frame, text="Та же, что исходная", 
                  command=self.set_dest_same_as_source).pack(side=tk.LEFT, padx=2)
        ttk.Button(dest_quick_frame, text="📁 Создать папку 'Organized'", 
                  command=self.create_organized_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(dest_quick_frame, text="💿 Другой диск", 
                  command=self.choose_other_drive).pack(side=tk.LEFT, padx=2)
        
        # Режим работы (перемещение или копирование)
        mode_frame = ttk.LabelFrame(main_frame, text="⚙️ Режим работы", padding="10")
        mode_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="✂️ Переместить файлы (исходные удалятся)", 
                       variable=self.operation_mode, value="move").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="📋 Копировать файлы (исходные останутся)", 
                       variable=self.operation_mode, value="copy").pack(anchor=tk.W, pady=2)
        
        # Категории (с прокруткой)
        categories_frame = ttk.LabelFrame(main_frame, text="📋 Категории для сортировки", padding="10")
        categories_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        categories_frame.columnconfigure(0, weight=1)
        categories_frame.rowconfigure(0, weight=1)
        
        # Canvas + Scrollbar для категорий
        canvas = tk.Canvas(categories_frame, highlightthickness=0, height=150)
        scrollbar = ttk.Scrollbar(categories_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Чекбоксы для категорий
        self.category_vars = {}
        for i, (category, extensions) in enumerate(self.categories.items()):
            var = tk.BooleanVar(value=True)
            self.category_vars[category] = var
            cb = ttk.Checkbutton(scrollable_frame, text=f"{category} ({len(extensions)} типов)", 
                                variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2, padx=5)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        categories_frame.columnconfigure(0, weight=1)
        categories_frame.rowconfigure(0, weight=1)
        
        # Кнопки действий
        actions_frame = ttk.Frame(main_frame)
        actions_frame.grid(row=5, column=0, pady=(0, 10))
        
        self.preview_btn = ttk.Button(actions_frame, text="🔍 Предпросмотр", 
                                     command=self.preview_organization, width=15)
        self.preview_btn.pack(side=tk.LEFT, padx=5)
        
        self.organize_btn = ttk.Button(actions_frame, text="🚀 Выполнить", 
                                      command=self.organize_files, width=15)
        self.organize_btn.pack(side=tk.LEFT, padx=5)
        
        self.select_all_btn = ttk.Button(actions_frame, text="✅ Выбрать всё", 
                                        command=self.select_all, width=12)
        self.select_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.deselect_all_btn = ttk.Button(actions_frame, text="❌ Снять всё", 
                                          command=self.deselect_all, width=12)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=5)
        
        # Прогресс-бар
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_value, 
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Статус
        status_label = ttk.Label(main_frame, textvariable=self.status_text, 
                                font=('Segoe UI', 9), relief=tk.SUNKEN, anchor=tk.W)
        status_label.grid(row=7, column=0, sticky=(tk.W, tk.E))
        
        # Таблица результатов
        results_frame = ttk.LabelFrame(main_frame, text="📊 Результаты", padding="5")
        results_frame.grid(row=8, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        # Treeview для результатов
        columns = ('Файл', 'Категория', 'Размер', 'Статус', 'Путь')
        self.tree = ttk.Treeview(results_frame, columns=columns, show='tree headings', height=8)
        self.tree.heading('#0', text='#')
        self.tree.heading('Файл', text='Файл')
        self.tree.heading('Категория', text='Категория')
        self.tree.heading('Размер', text='Размер')
        self.tree.heading('Статус', text='Статус')
        self.tree.heading('Путь', text='Целевой путь')
        
        self.tree.column('#0', width=40)
        self.tree.column('Файл', width=180)
        self.tree.column('Категория', width=120)
        self.tree.column('Размер', width=80)
        self.tree.column('Статус', width=100)
        self.tree.column('Путь', width=200)
        
        tree_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Кнопка очистки результатов
        ttk.Button(results_frame, text="Очистить", command=self.clear_results).grid(row=1, column=0, pady=5)
        
    def browse_source(self):
        folder = filedialog.askdirectory(title="Выберите исходную папку (откуда взять файлы)")
        if folder:
            self.source_path.set(folder)
            # Если целевая папка не задана, предлагаем ту же
            if not self.dest_path.get():
                self.dest_path.set(folder)
    
    def browse_dest(self):
        folder = filedialog.askdirectory(title="Выберите целевую папку (куда переместить файлы)")
        if folder:
            self.dest_path.set(folder)
    
    def set_dest_same_as_source(self):
        if self.source_path.get():
            self.dest_path.set(self.source_path.get())
        else:
            messagebox.showwarning("Предупреждение", "Сначала выберите исходную папку!")
    
    def create_organized_folder(self):
        if not self.source_path.get():
            messagebox.showwarning("Предупреждение", "Сначала выберите исходную папку!")
            return
        organized_path = Path(self.source_path.get()) / "Organized_Files"
        organized_path.mkdir(exist_ok=True)
        self.dest_path.set(str(organized_path))
        messagebox.showinfo("Готово", f"Папка создана:\n{organized_path}")
    
    def choose_other_drive(self):
        drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
        if not drives:
            messagebox.showerror("Ошибка", "Не найдено других дисков!")
            return
        
        # Создаем диалог выбора диска
        drive_window = tk.Toplevel(self.root)
        drive_window.title("Выбор диска")
        drive_window.geometry("300x200")
        drive_window.resizable(False, False)
        
        ttk.Label(drive_window, text="Выберите диск:", font=('Segoe UI', 10)).pack(pady=10)
        
        listbox = tk.Listbox(drive_window, height=8)
        for drive in drives:
            try:
                total, used, free = shutil.disk_usage(drive)
                free_gb = free / (1024**3)
                listbox.insert(tk.END, f"{drive} (свободно: {free_gb:.1f} ГБ)")
            except:
                listbox.insert(tk.END, f"{drive}")
        listbox.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                selected = listbox.get(selection[0]).split()[0]
                self.dest_path.set(selected)
                drive_window.destroy()
        
        ttk.Button(drive_window, text="Выбрать", command=on_select).pack(pady=10)
    
    def select_all(self):
        for var in self.category_vars.values():
            var.set(True)
    
    def deselect_all(self):
        for var in self.category_vars.values():
            var.set(False)
    
    def clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
    
    def get_category(self, filename):
        ext = Path(filename).suffix.lower()
        for category, extensions in self.categories.items():
            if ext in extensions:
                return category
        return self.misc_folder
    
    def format_size(self, size_bytes):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} ТБ"
    
    def add_result(self, filename, category, size, status, dest_path=None, color=None):
        item = self.tree.insert('', 'end', values=(filename, category, size, status, dest_path or ''))
        if color:
            self.tree.tag_configure(color, foreground=color)
            self.tree.item(item, tags=(color,))
    
    def preview_organization(self):
        if not self.source_path.get():
            messagebox.showwarning("Предупреждение", "Выберите исходную папку!")
            return
        if not self.dest_path.get():
            messagebox.showwarning("Предупреждение", "Выберите целевую папку!")
            return
        
        self.clear_results()
        self.status_text.set("🔍 Анализ папки...")
        self.progress_value.set(0)
        
        thread = threading.Thread(target=self._preview_worker)
        thread.daemon = True
        thread.start()
    
    def _preview_worker(self):
        try:
            source = Path(self.source_path.get())
            dest = Path(self.dest_path.get())
            
            if not source.exists():
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Исходная папка не найдена!"))
                return
            
            files = [f for f in source.iterdir() if f.is_file()]
            total = len(files)
            
            selected_cats = [cat for cat, var in self.category_vars.items() if var.get()]
            
            for i, file in enumerate(files):
                category = self.get_category(file.name)
                size = self.format_size(file.stat().st_size)
                dest_folder = dest / category
                dest_path = dest_folder / file.name
                
                if category in selected_cats or category == self.misc_folder:
                    status = "✅ Будет обработан"
                    color = "green"
                else:
                    status = "⏸️ Пропущен"
                    color = "gray"
                
                self.root.after(0, lambda f=file.name, c=category, s=size, st=status, dp=str(dest_path), col=color: 
                               self.add_result(f, c, s, st, dp, col))
                
                progress = ((i + 1) / total) * 100
                self.root.after(0, lambda p=progress: self.progress_value.set(p))
                self.root.after(0, lambda i=i, t=total: self.status_text.set(f"🔍 Анализ: {i+1}/{t} файлов"))
            
            self.root.after(0, lambda: self.status_text.set(f"✅ Предпросмотр завершён. Найдено {total} файлов"))
            self.root.after(0, lambda: messagebox.showinfo("Готово", f"Предпросмотр завершён!\nНайдено {total} файлов.\nЦелевая папка: {dest}"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.root.after(0, lambda: self.status_text.set("❌ Ошибка при анализе"))
    
    def organize_files(self):
        if not self.source_path.get():
            messagebox.showwarning("Предупреждение", "Выберите исходную папку!")
            return
        if not self.dest_path.get():
            messagebox.showwarning("Предупреждение", "Выберите целевую папку!")
            return
        
        if self.source_path.get() == self.dest_path.get():
            result = messagebox.askyesno("Подтверждение", 
                                       "Исходная и целевая папки совпадают!\n"
                                       "Файлы будут организованы внутри этой же папки.\n"
                                       "Продолжить?")
        else:
            result = messagebox.askyesno("Подтверждение", 
                                       f"Файлы будут {'ПЕРЕМЕЩЕНЫ' if self.operation_mode.get() == 'move' else 'СКОПИРОВАНЫ'}\n"
                                       f"Из: {self.source_path.get()}\n"
                                       f"В: {self.dest_path.get()}\n\n"
                                       f"Продолжить?")
        
        if not result:
            return
        
        self.clear_results()
        self.status_text.set("🚀 Выполнение операции...")
        self.progress_value.set(0)
        
        thread = threading.Thread(target=self._organize_worker)
        thread.daemon = True
        thread.start()
    
    def _organize_worker(self):
        try:
            source = Path(self.source_path.get())
            dest = Path(self.dest_path.get())
            
            if not source.exists():
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Исходная папка не найдена!"))
                return
            
            dest.mkdir(parents=True, exist_ok=True)
            
            files = [f for f in source.iterdir() if f.is_file()]
            total = len(files)
            processed = 0
            skipped = 0
            errors = 0
            
            selected_cats = [cat for cat, var in self.category_vars.items() if var.get()]
            operation = self.operation_mode.get()
            
            for i, file in enumerate(files):
                category = self.get_category(file.name)
                size = self.format_size(file.stat().st_size)
                
                if category in selected_cats or category == self.misc_folder:
                    dest_folder = dest / category
                    dest_folder.mkdir(parents=True, exist_ok=True)
                    
                    dest_path = dest_folder / file.name
                    
                    # Обработка конфликта имён
                    if dest_path.exists():
                        name, ext = os.path.splitext(file.name)
                        counter = 1
                        while dest_path.exists():
                            new_name = f"{name}_{counter}{ext}"
                            dest_path = dest_folder / new_name
                            counter += 1
                    
                    try:
                        if operation == "move":
                            shutil.move(str(file), str(dest_path))
                            status = "✅ Перемещён"
                        else:
                            shutil.copy2(str(file), str(dest_path))
                            status = "📋 Скопирован"
                        
                        processed += 1
                        self.root.after(0, lambda f=file.name, c=category, s=size, st=status, dp=str(dest_path): 
                                       self.add_result(f, c, s, st, dp, "green"))
                    except Exception as e:
                        errors += 1
                        self.root.after(0, lambda f=file.name, c=category, s=size, e=str(e): 
                                       self.add_result(f, c, s, f"❌ {e[:30]}", "", "red"))
                else:
                    skipped += 1
                    self.root.after(0, lambda f=file.name, c=category, s=size: 
                                   self.add_result(f, c, s, "⏸️ Пропущен", "", "gray"))
                
                progress = ((i + 1) / total) * 100
                self.root.after(0, lambda p=progress: self.progress_value.set(p))
                self.root.after(0, lambda i=i, t=total: self.status_text.set(f"🚀 Прогресс: {i+1}/{t} файлов"))
            
            summary = f"✅ Готово! Обработано: {processed}, Пропущено: {skipped}, Ошибок: {errors}"
            self.root.after(0, lambda: self.status_text.set(summary))
            self.root.after(0, lambda: messagebox.showinfo("Завершено", summary))
            
            # Предложение открыть целевую папку
            if processed > 0:
                open_folder = messagebox.askyesno("Открыть папку", 
                                                f"Обработано {processed} файлов.\nОткрыть целевую папку?")
                if open_folder:
                    os.startfile(str(dest))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            self.root.after(0, lambda: self.status_text.set("❌ Ошибка при выполнении"))

def main():
    root = tk.Tk()
    app = FileOrganizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()