import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import shutil
import pickle
import math
import random

# ---------- Конфигурация ----------
DATA_DIR = "electro_data"
COUNTERS_FILE = os.path.join(DATA_DIR, "counters.pkl")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------- Генератор красивых иконок счётчиков (без Pillow) ----------
class CounterIconGenerator:
    @staticmethod
    def create_meter_icon(parent, size=140, value=12345, name=""):
        """Создаёт красивую иконку счётчика с помощью Canvas"""
        # Создаём Canvas для иконки
        canvas = tk.Canvas(parent, width=size, height=size, bg='white', 
                          highlightthickness=0, cursor="hand2")
        
        # Основные параметры
        margin = 8
        body_color = "#2c3e50"
        glass_color = "#ecf0f1"
        display_color = "#1a252f"
        
        # Тень (эффект глубины)
        canvas.create_rectangle(margin+2, margin+2, size-margin+2, size-margin+2,
                               fill="#bdc3c7", outline="", width=0)
        
        # Корпус счётчика (основной блок)
        canvas.create_rectangle(margin, margin, size-margin, size-margin,
                               fill=body_color, outline="#1a252f", width=2)
        
        # Рамка корпуса (декоративная)
        canvas.create_rectangle(margin+2, margin+2, size-margin-2, size-margin-2,
                               outline="#34495e", width=1)
        
        # Стеклянное окошко
        glass_margin = margin + 12
        canvas.create_rectangle(glass_margin, glass_margin, 
                               size-glass_margin, size-glass_margin-25,
                               fill=glass_color, outline="#bdc3c7", width=1)
        
        # Блик на стекле
        canvas.create_line(glass_margin+5, glass_margin+5, 
                          glass_margin+30, glass_margin+5,
                          fill="white", width=2, stipple="gray25")
        
        # Дисплей (чёрный экран)
        display_margin = glass_margin + 8
        display_width = size - (display_margin * 2)
        display_height = 35
        canvas.create_rectangle(display_margin, display_margin,
                               size-display_margin, display_margin + display_height,
                               fill=display_color, outline="#000000", width=1)
        
        # Цифры на дисплее (имитация ЖК-дисплея)
        display_text = f"{value:06d}"  # Формат: 012345
        # Эффект свечения цифр
        for i, digit in enumerate(display_text):
            x_pos = display_margin + 8 + (i * 18)
            # Тень цифр
            canvas.create_text(x_pos+1, display_margin+22, text=digit,
                              fill="#003300", font=('Courier', 16, 'bold'))
            # Основные цифры
            canvas.create_text(x_pos, display_margin+21, text=digit,
                              fill="#00ff00", font=('Courier', 16, 'bold'))
        
        # Анимированный индикатор работы (красная мигающая точка)
        self.indicator = canvas.create_oval(
            size-glass_margin-15, glass_margin+5,
            size-glass_margin-5, glass_margin+15,
            fill="#e74c3c", outline="#c0392b", width=1
        )
        
        # Индикаторная надпись "POWER"
        canvas.create_text(size-glass_margin-28, glass_margin+15, 
                          text="PWR", fill="#7f8c8d", 
                          font=('Arial', 6, 'bold'), angle=90)
        
        # Логотип и серийный номер
        canvas.create_text(margin+25, size-margin-10, text="⚡ ЭЭ",
                          fill="#ecf0f1", font=('Arial', 10, 'bold'))
        
        canvas.create_text(size-margin-30, size-margin-10, 
                          text=f"№{hash(name) % 10000:04d}",
                          fill="#95a5a6", font=('Arial', 8))
        
        # Декоративные болтики по углам
        bolt_positions = [(margin+4, margin+4), (size-margin-4, margin+4),
                         (margin+4, size-margin-4), (size-margin-4, size-margin-4)]
        for x, y in bolt_positions:
            canvas.create_oval(x-2, y-2, x+2, y+2, fill="#95a5a6", outline="#7f8c8d")
        
        return canvas
    
    @staticmethod
    def update_indicator(canvas, indicator_id, frame):
        """Анимирует индикатор работы"""
        # Мигание с изменением цвета
        alpha = 0.3 + 0.7 * abs(math.sin(frame * 0.3))
        brightness = int(100 + 155 * alpha)
        
        if frame % 20 < 10:
            color = f"#{brightness:02x}{40:02x}{40:02x}"
        else:
            color = "#e74c3c"
        
        canvas.itemconfig(indicator_id, fill=color)

# ---------- Кастомный Canvas с прокруткой для рабочего стола ----------
class ScrollableCanvas:
    def __init__(self, parent, bg_color="#ecf0f1"):
        self.parent = parent
        self.canvas = tk.Canvas(parent, bg=bg_color, highlightthickness=0)
        self.scrollbar_y = tk.Scrollbar(parent, orient="vertical", command=self.canvas.yview)
        self.scrollbar_x = tk.Scrollbar(parent, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, 
                             xscrollcommand=self.scrollbar_x.set)
        
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.inner_frame = tk.Frame(self.canvas, bg=bg_color)
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", self._on_configure)
        
        # Привязка прокрутки колесиком
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def get_inner_frame(self):
        return self.inner_frame

# ---------- Модель данных ----------
class CounterManager:
    def __init__(self):
        self.counters = self.load_counters()
        self.counter_values = {}
        self.animation_frame = 0

    def load_counters(self):
        if os.path.exists(COUNTERS_FILE):
            try:
                with open(COUNTERS_FILE, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        return data
            except:
                pass
        return {}

    def save_counters(self):
        with open(COUNTERS_FILE, 'wb') as f:
            pickle.dump(self.counters, f)

    def add_counter(self, name):
        if name in self.counters:
            return False
        path = os.path.join(DATA_DIR, name)
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, "photos"), exist_ok=True)
        os.makedirs(os.path.join(path, "videos"), exist_ok=True)
        self.counters[name] = path
        self.counter_values[name] = random.randint(1000, 99999)
        self.save_counters()
        return True

    def delete_counter(self, name):
        if name in self.counters:
            shutil.rmtree(self.counters[name])
            del self.counters[name]
            if name in self.counter_values:
                del self.counter_values[name]
            self.save_counters()

    def get_counter_path(self, name):
        return self.counters.get(name)
    
    def update_counter_value(self, name):
        """Обновляет значение счётчика (имитация работы)"""
        if name in self.counter_values:
            self.counter_values[name] += random.randint(0, 5)
            return self.counter_values[name]
        return 0

# ---------- Красивое окно счётчика ----------
class CounterWindow:
    def __init__(self, parent, counter_name, counter_path):
        self.window = tk.Toplevel(parent)
        self.window.title(f"⚡ {counter_name} | Электросчётчик")
        self.window.geometry("900x650")
        self.window.configure(bg="#ecf0f1")
        
        self.counter_name = counter_name
        self.counter_path = counter_path
        self.photos_path = os.path.join(counter_path, "photos")
        self.videos_path = os.path.join(counter_path, "videos")
        
        # Создаём красивый заголовок
        self.create_header()
        
        # Основной контент
        main_frame = tk.Frame(self.window, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Создаём панель инструментов
        self.create_toolbar(main_frame)
        
        # Создаём список файлов
        self.create_file_list(main_frame)
        
        self.refresh_list()
    
    def create_header(self):
        """Создаёт красивый заголовок с информацией о счётчике"""
        header = tk.Frame(self.window, bg="#2c3e50", height=120)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Текущее значение счётчика
        value_frame = tk.Frame(header, bg="#2c3e50")
        value_frame.pack(pady=(20, 5))
        
        tk.Label(value_frame, text="ТЕКУЩИЕ ПОКАЗАНИЯ", 
                font=('Arial', 10), fg="#95a5a6", bg="#2c3e50").pack()
        
        self.value_label = tk.Label(value_frame, text="0 kWh", 
                                   font=('Arial', 32, 'bold'), 
                                   fg="#00ff00", bg="#2c3e50")
        self.value_label.pack()
        
        # Название счётчика
        tk.Label(header, text=f"📊 {self.counter_name}", 
                font=('Arial', 18, 'bold'), 
                fg="#ecf0f1", bg="#2c3e50").pack(pady=5)
        
        # Загружаем сохранённое значение
        self.load_counter_value()
    
    def load_counter_value(self):
        """Загружает значение счётчика из файла"""
        value_file = os.path.join(self.counter_path, "value.txt")
        if os.path.exists(value_file):
            try:
                with open(value_file, 'r') as f:
                    value = int(f.read())
                    self.value_label.config(text=f"{value} kWh")
            except:
                pass
    
    def save_counter_value(self, value):
        """Сохраняет значение счётчика"""
        value_file = os.path.join(self.counter_path, "value.txt")
        with open(value_file, 'w') as f:
            f.write(str(value))
    
    def create_toolbar(self, parent):
        """Создаёт панель инструментов"""
        toolbar = tk.Frame(parent, bg="#ecf0f1")
        toolbar.pack(fill=tk.X, pady=(0, 15))
        
        # Кнопки с иконками
        buttons = [
            ("📸  Загрузить фото", self.upload_photo, "#27ae60", "#2ecc71"),
            ("🎬  Загрузить видео", self.upload_video, "#2980b9", "#3498db"),
            ("👁️  Открыть", self.open_selected, "#f39c12", "#f1c40f"),
            ("🗑️  Удалить", self.delete_selected, "#e74c3c", "#c0392b"),
            ("➕  Добавить показания", self.add_reading, "#8e44ad", "#9b59b6")
        ]
        
        for text, command, color, hover_color in buttons:
            btn = tk.Button(toolbar, text=text, command=command,
                          font=('Arial', 10, 'bold'),
                          bg=color, fg="white",
                          padx=20, pady=8,
                          relief=tk.FLAT, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
            
            # Hover эффект
            def on_enter(e, b=btn, c=hover_color):
                b.configure(bg=c)
            def on_leave(e, b=btn, c=color):
                b.configure(bg=c)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
    
    def create_file_list(self, parent):
        """Создаёт красивый список файлов"""
        # Фрейм для списка
        list_frame = tk.Frame(parent, bg="white", relief=tk.FLAT, bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовки колонок
        header_frame = tk.Frame(list_frame, bg="#34495e", height=35)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="ТИП", width=5, 
                font=('Arial', 10, 'bold'), fg="white", bg="#34495e").pack(side=tk.LEFT, padx=10)
        tk.Label(header_frame, text="ИМЯ ФАЙЛА", 
                font=('Arial', 10, 'bold'), fg="white", bg="#34495e").pack(side=tk.LEFT, padx=10)
        tk.Label(header_frame, text="РАЗМЕР", width=10,
                font=('Arial', 10, 'bold'), fg="white", bg="#34495e").pack(side=tk.RIGHT, padx=10)
        
        # Список с прокруткой
        list_container = tk.Frame(list_frame, bg="white")
        list_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_container, 
                                 yscrollcommand=scrollbar.set,
                                 font=('Arial', 11),
                                 bg="white",
                                 fg="#2c3e50",
                                 selectbackground="#3498db",
                                 selectforeground="white",
                                 relief=tk.FLAT,
                                 borderwidth=0,
                                 height=20)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.listbox.yview)
        
        # Информационная строка
        info_frame = tk.Frame(list_frame, bg="#ecf0f1", height=30)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        info_frame.pack_propagate(False)
        
        self.info_label = tk.Label(info_frame, text="", 
                                  font=('Arial', 9), fg="#7f8c8d", bg="#ecf0f1")
        self.info_label.pack(pady=5)
    
    def get_file_size(self, filepath):
        """Возвращает читаемый размер файла"""
        size = os.path.getsize(filepath)
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"
    
    def refresh_list(self):
        """Обновляет список файлов"""
        self.listbox.delete(0, tk.END)
        all_files = []
        
        # Собираем фото
        for f in os.listdir(self.photos_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                full_path = os.path.join(self.photos_path, f)
                size = self.get_file_size(full_path)
                all_files.append(("🖼️ ФОТО", f, size, full_path))
        
        # Собираем видео
        for f in os.listdir(self.videos_path):
            if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv')):
                full_path = os.path.join(self.videos_path, f)
                size = self.get_file_size(full_path)
                all_files.append(("🎬 ВИДЕО", f, size, full_path))
        
        if not all_files:
            self.listbox.insert(tk.END, "📭  Нет загруженных файлов")
            self.listbox.itemconfig(0, fg="#95a5a6", font=('Arial', 11, 'italic'))
            self.info_label.config(text="Нет файлов")
        else:
            for ftype, fname, size, fpath in sorted(all_files, key=lambda x: x[1]):
                # Форматируем строку для красивого отображения
                display_text = f"{ftype:<8}  {fname:<40}  {size:>10}"
                self.listbox.insert(tk.END, display_text)
                # Сохраняем путь к файлу
                self.listbox.itemconfig(tk.END, fg="#2c3e50")
            
            self.info_label.config(text=f"Всего файлов: {len(all_files)}")
    
    def upload_photo(self):
        file_path = filedialog.askopenfilename(
            title="Выберите фото",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            dest = os.path.join(self.photos_path, os.path.basename(file_path))
            shutil.copy(file_path, dest)
            self.refresh_list()
            self.show_notification("✅ Фото успешно загружено!")
    
    def upload_video(self):
        file_path = filedialog.askopenfilename(
            title="Выберите видео",
            filetypes=[("Видео", "*.mp4 *.avi *.mov *.mkv *.webm")]
        )
        if file_path:
            dest = os.path.join(self.videos_path, os.path.basename(file_path))
            shutil.copy(file_path, dest)
            self.refresh_list()
            self.show_notification("✅ Видео успешно загружено!")
    
    def add_reading(self):
        """Добавляет новые показания счётчика"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Добавить показания")
        dialog.geometry("400x250")
        dialog.configure(bg="#ecf0f1")
        
        tk.Label(dialog, text="Новые показания счётчика", 
                font=('Arial', 14, 'bold'), bg="#ecf0f1", fg="#2c3e50").pack(pady=20)
        
        current_text = self.value_label.cget("text").replace(" kWh", "")
        tk.Label(dialog, text=f"Текущие: {current_text} kWh", 
                font=('Arial', 11), bg="#ecf0f1", fg="#7f8c8d").pack()
        
        tk.Label(dialog, text="Введите новые показания:", 
                font=('Arial', 11), bg="#ecf0f1", fg="#2c3e50").pack(pady=(20, 5))
        
        entry = tk.Entry(dialog, font=('Arial', 14), width=15, justify='center')
        entry.pack(pady=10)
        
        def save():
            try:
                new_value = int(entry.get())
                if new_value < int(current_text):
                    messagebox.showwarning("Ошибка", "Новые показания не могут быть меньше текущих!")
                    return
                self.value_label.config(text=f"{new_value} kWh")
                self.save_counter_value(new_value)
                self.show_notification(f"✅ Показания обновлены: {new_value} kWh")
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число!")
        
        btn_frame = tk.Frame(dialog, bg="#ecf0f1")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Сохранить", command=save,
                 bg="#27ae60", fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                 bg="#95a5a6", fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    def show_notification(self, message):
        """Показывает временное уведомление"""
        notification = tk.Toplevel(self.window)
        notification.title("Уведомление")
        notification.geometry("300x80")
        notification.configure(bg="#2c3e50")
        
        # Центрируем относительно родительского окна
        x = self.window.winfo_x() + self.window.winfo_width() // 2 - 150
        y = self.window.winfo_y() + self.window.winfo_height() // 2 - 40
        notification.geometry(f"+{x}+{y}")
        
        tk.Label(notification, text=message, 
                font=('Arial', 11, 'bold'), 
                fg="#00ff00", bg="#2c3e50").pack(expand=True)
        
        notification.after(2000, notification.destroy)
    
    def open_selected(self):
        selection = self.listbox.curselection()
        if not selection or self.listbox.get(selection[0]).startswith("📭"):
            messagebox.showwarning("Внимание", "Выберите файл для открытия")
            return
        
        item = self.listbox.get(selection[0])
        # Извлекаем имя файла из форматированной строки
        parts = item.split("  ")
        if len(parts) >= 2:
            fname = parts[1].strip()
            
            # Ищем файл
            for folder, folder_path in [("photos", self.photos_path), ("videos", self.videos_path)]:
                full_path = os.path.join(folder_path, fname)
                if os.path.exists(full_path):
                    if os.name == 'nt':
                        os.startfile(full_path)
                    else:
                        os.system(f'xdg-open "{full_path}"')
                    return
            
            messagebox.showerror("Ошибка", "Файл не найден")
    
    def delete_selected(self):
        selection = self.listbox.curselection()
        if not selection or self.listbox.get(selection[0]).startswith("📭"):
            return
        
        item = self.listbox.get(selection[0])
        parts = item.split("  ")
        if len(parts) >= 2:
            fname = parts[1].strip()
            
            if messagebox.askyesno("Подтверждение", f"Удалить файл '{fname}'?"):
                # Ищем и удаляем файл
                for folder_path in [self.photos_path, self.videos_path]:
                    full_path = os.path.join(folder_path, fname)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        self.refresh_list()
                        self.show_notification("🗑️ Файл удалён")
                        return

# ---------- Главное окно приложения ----------
class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Электросчётчики | Рабочий стол")
        self.root.geometry("1200x750")
        self.root.configure(bg="#ecf0f1")
        
        self.manager = CounterManager()
        self.icon_generator = CounterIconGenerator()
        self.counter_widgets = {}  # Хранилище виджетов иконок
        
        # Создаём интерфейс
        self.create_header()
        self.create_search_and_controls()
        self.create_counter_area()
        
        # Запускаем анимацию
        self.animate_indicators()
        
        # Обновляем список счётчиков
        self.update_counter_list()
    
    def create_header(self):
        """Создаёт красивый заголовок"""
        header = tk.Frame(self.root, bg="white", height=120)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Градиентный эффект через рамки
        top_bar = tk.Frame(header, bg="#2c3e50", height=5)
        top_bar.pack(fill=tk.X)
        
        # Логотип и название
        title_frame = tk.Frame(header, bg="white")
        title_frame.pack(expand=True)
        
        tk.Label(title_frame, text="⚡", font=('Arial', 48), 
                fg="#f39c12", bg="white").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(title_frame, text="ЭЛЕКТРОСЧЁТЧИКИ", 
                font=('Arial', 28, 'bold'), 
                fg="#2c3e50", bg="white").pack(side=tk.LEFT)
        
        tk.Label(title_frame, text="v2.0", 
                font=('Arial', 12), 
                fg="#95a5a6", bg="white").pack(side=tk.LEFT, padx=(10, 0))
        
        # Статистика
        stats_frame = tk.Frame(header, bg="white")
        stats_frame.pack(pady=(0, 10))
        
        self.stats_label = tk.Label(stats_frame, text="", 
                                    font=('Arial', 10), 
                                    fg="#7f8c8d", bg="white")
        self.stats_label.pack()
    
    def create_search_and_controls(self):
        """Создаёт панель поиска и управления"""
        control_panel = tk.Frame(self.root, bg="#34495e", height=70)
        control_panel.pack(fill=tk.X, pady=(0, 20))
        control_panel.pack_propagate(False)
        
        # Поиск
        search_frame = tk.Frame(control_panel, bg="#34495e")
        search_frame.pack(side=tk.LEFT, padx=30, pady=15)
        
        tk.Label(search_frame, text="🔍", font=('Arial', 16), 
                bg="#34495e", fg="#ecf0f1").pack(side=tk.LEFT, padx=(0, 10))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.update_counter_list())
        
        self.search_entry = tk.Entry(search_frame, 
                                     textvariable=self.search_var,
                                     font=('Arial', 12),
                                     width=35,
                                     bg="#ecf0f1",
                                     fg="#2c3e50",
                                     relief=tk.FLAT,
                                     highlightthickness=2,
                                     highlightcolor="#3498db")
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.insert(0, "Поиск счётчиков...")
        self.search_entry.bind('<FocusIn>', lambda e: self.clear_placeholder())
        self.search_entry.bind('<FocusOut>', lambda e: self.restore_placeholder())
        
        # Кнопки управления
        btn_frame = tk.Frame(control_panel, bg="#34495e")
        btn_frame.pack(side=tk.RIGHT, padx=30)
        
        buttons = [
            ("➕  Новый счётчик", self.create_counter, "#27ae60", "#2ecc71"),
            ("🗑️  Удалить", self.delete_counter, "#e74c3c", "#c0392b"),
            ("📊  Статистика", self.show_statistics, "#3498db", "#2980b9")
        ]
        
        for text, command, color, hover_color in buttons:
            btn = tk.Button(btn_frame, text=text, command=command,
                          font=('Arial', 10, 'bold'),
                          bg=color, fg="white",
                          padx=15, pady=8,
                          relief=tk.FLAT, cursor="hand2")
            btn.pack(side=tk.LEFT, padx=5)
            
            def on_enter(e, b=btn, c=hover_color):
                b.configure(bg=c)
            def on_leave(e, b=btn, c=color):
                b.configure(bg=c)
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
    
    def clear_placeholder(self):
        if self.search_entry.get() == "Поиск счётчиков...":
            self.search_entry.delete(0, tk.END)
    
    def restore_placeholder(self):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Поиск счётчиков...")
    
    def create_counter_area(self):
        """Создаёт прокручиваемую область для счётчиков"""
        self.scrollable = ScrollableCanvas(self.root, bg_color="#ecf0f1")
        self.inner_frame = self.scrollable.get_inner_frame()
    
    def update_counter_list(self):
        """Обновляет список счётчиков с красивыми иконками"""
        # Очищаем
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        self.counter_widgets.clear()
        
        # Фильтрация
        search_text = self.search_var.get().lower()
        if search_text == "поиск счётчиков...":
            search_text = ""
        
        filtered = {name: path for name, path in self.manager.counters.items() 
                   if search_text in name.lower()}
        
        if not filtered:
            empty_frame = tk.Frame(self.inner_frame, bg="#ecf0f1")
            empty_frame.pack(expand=True, fill=tk.BOTH, pady=100)
            
            tk.Label(empty_frame, text="📭", font=('Arial', 64), 
                    fg="#bdc3c7", bg="#ecf0f1").pack()
            tk.Label(empty_frame, text="Нет счётчиков", 
                    font=('Arial', 18, 'bold'), 
                    fg="#95a5a6", bg="#ecf0f1").pack(pady=10)
            tk.Label(empty_frame, text="Нажмите «Новый счётчик» для создания", 
                    font=('Arial', 11), 
                    fg="#7f8c8d", bg="#ecf0f1").pack()
            return
        
        # Создаём сетку
        cols = 4
        row, col = 0, 0
        
        for name, path in filtered.items():
            # Получаем или создаём значение счётчика
            if name not in self.manager.counter_values:
                self.manager.counter_values[name] = random.randint(1000, 99999)
            
            value = self.manager.counter_values[name]
            
            # Карточка счётчика
            card = tk.Frame(self.inner_frame, bg="white", relief=tk.RAISED, 
                           bd=0, highlightthickness=1, highlightcolor="#bdc3c7")
            card.grid(row=row, column=col, padx=15, pady=15, sticky="n")
            
            # Иконка счётчика (кастомный Canvas)
            icon_canvas = self.icon_generator.create_meter_icon(
                card, size=140, value=value, name=name
            )
            icon_canvas.pack(padx=15, pady=(15, 5))
            icon_canvas.bind("<Button-1>", lambda e, n=name: self.open_counter(n))
            
            # Название счётчика
            name_label = tk.Label(card, text=name, 
                                 font=('Arial', 12, 'bold'),
                                 fg="#2c3e50", bg="white",
                                 wraplength=120)
            name_label.pack(pady=(5, 0))
            
            # Показания
            value_label = tk.Label(card, text=f"{value} kWh", 
                                  font=('Arial', 10, 'italic'),
                                  fg="#7f8c8d", bg="white")
            value_label.pack(pady=(0, 5))
            
            # Кнопка открытия
            open_btn = tk.Button(card, text="🔓 Открыть", 
                                command=lambda n=name: self.open_counter(n),
                                font=('Arial', 9, 'bold'),
                                bg="#3498db", fg="white",
                                padx=20, pady=5,
                                relief=tk.FLAT, cursor="hand2")
            open_btn.pack(pady=(0, 15))
            
            # Hover эффект
            def on_enter(e, c=card):
                c.configure(highlightthickness=2, highlightcolor="#3498db")
            def on_leave(e, c=card):
                c.configure(highlightthickness=1, highlightcolor="#bdc3c7")
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            
            # Сохраняем информацию для анимации
            self.counter_widgets[name] = {
                'canvas': icon_canvas,
                'indicator_id': getattr(icon_canvas, 'indicator', None),
                'value_label': value_label
            }
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        # Обновляем статистику
        self.update_statistics()
    
    def update_statistics(self):
        """Обновляет статистику в заголовке"""
        total_counters = len(self.manager.counters)
        total_files = 0
        
        for path in self.manager.counters.values():
            photos_dir = os.path.join(path, "photos")
            videos_dir = os.path.join(path, "videos")
            if os.path.exists(photos_dir):
                total_files += len([f for f in os.listdir(photos_dir) 
                                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])
            if os.path.exists(videos_dir):
                total_files += len([f for f in os.listdir(videos_dir)
                                   if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))])
        
        self.stats_label.config(text=f"📊 Счётчиков: {total_counters}  |  📁 Файлов: {total_files}")
    
    def animate_indicators(self):
        """Анимирует индикаторы на всех счётчиках"""
        self.manager.animation_frame += 1
        
        for name, info in self.counter_widgets.items():
            if info['canvas'] and info['indicator_id']:
                self.icon_generator.update_indicator(
                    info['canvas'], 
                    info['indicator_id'], 
                    self.manager.animation_frame
                )
            
            # Обновляем значения счётчиков (медленно увеличиваются)
            if self.manager.animation_frame % 30 == 0:  # Каждые 30 кадров
                new_value = self.manager.update_counter_value(name)
                if info['value_label']:
                    info['value_label'].config(text=f"{new_value} kWh")
        
        self.root.after(500, self.animate_indicators)
    
    def create_counter(self):
        name = simpledialog.askstring("Новый счётчик", 
                                     "Введите название счётчика:", 
                                     parent=self.root)
        if name and name.strip():
            name = name.strip()
            if self.manager.add_counter(name):
                self.update_counter_list()
                self.show_notification(f"✅ Счётчик «{name}» создан!")
            else:
                messagebox.showerror("Ошибка", "Счётчик с таким именем уже существует")
    
    def delete_counter(self):
        if not self.manager.counters:
            messagebox.showwarning("Внимание", "Нет счётчиков для удаления")
            return
        
        # Создаём красивое окно выбора
        dialog = tk.Toplevel(self.root)
        dialog.title("Удаление счётчика")
        dialog.geometry("450x350")
        dialog.configure(bg="#ecf0f1")
        
        tk.Label(dialog, text="🗑️  Удаление счётчика", 
                font=('Arial', 16, 'bold'), 
                bg="#ecf0f1", fg="#2c3e50").pack(pady=20)
        
        tk.Label(dialog, text="Выберите счётчик для удаления:", 
                font=('Arial', 11), 
                bg="#ecf0f1", fg="#7f8c8d").pack()
        
        listbox = tk.Listbox(dialog, font=('Arial', 11), 
                            height=10, bg="white", 
                            selectbackground="#3498db")
        listbox.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        for name in self.manager.counters.keys():
            listbox.insert(tk.END, f"⚡ {name}")
        
        def confirm_delete():
            selection = listbox.curselection()
            if selection:
                name = listbox.get(selection[0]).replace("⚡ ", "")
                if messagebox.askyesno("Подтверждение", 
                                      f"Удалить счётчик «{name}» и все файлы?\n\nЭто действие нельзя отменить!",
                                      parent=dialog):
                    self.manager.delete_counter(name)
                    self.update_counter_list()
                    dialog.destroy()
                    self.show_notification(f"🗑️ Счётчик «{name}» удалён")
        
        btn_frame = tk.Frame(dialog, bg="#ecf0f1")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="🗑️  Удалить", command=confirm_delete,
                 bg="#e74c3c", fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                 bg="#95a5a6", fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=5)
    
    def show_statistics(self):
        """Показывает статистику по всем счётчикам"""
        if not self.manager.counters:
            messagebox.showinfo("Статистика", "Нет счётчиков для отображения")
            return
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Статистика счётчиков")
        stats_window.geometry("500x400")
        stats_window.configure(bg="#ecf0f1")
        
        tk.Label(stats_window, text="Статистика счётчиков", 
                font=('Arial', 18, 'bold'), 
                bg="#ecf0f1", fg="#2c3e50").pack(pady=20)
        
        # Создаём текстовое поле для статистики
        text_frame = tk.Frame(stats_window, bg="white", relief=tk.FLAT, bd=1)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget = tk.Text(text_frame, yscrollcommand=scrollbar.set,
                             font=('Courier', 10), bg="white",
                             relief=tk.FLAT, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_widget.yview)
        
        # Заполняем статистику
        total_photos = 0
        total_videos = 0
        total_value = 0
        
        text_widget.insert(tk.END, "="*50 + "\n")
        text_widget.insert(tk.END, "📊  ДЕТАЛЬНАЯ СТАТИСТИКА\n")
        text_widget.insert(tk.END, "="*50 + "\n\n")
        
        for name, path in self.manager.counters.items():
            # Количество файлов
            photos_count = len([f for f in os.listdir(os.path.join(path, "photos")) 
                               if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))])
            videos_count = len([f for f in os.listdir(os.path.join(path, "videos"))
                               if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))])
            
            # Значение счётчика
            value_file = os.path.join(path, "value.txt")
            if os.path.exists(value_file):
                with open(value_file, 'r') as f:
                    value = int(f.read())
            else:
                value = self.manager.counter_values.get(name, 0)
            
            total_photos += photos_count
            total_videos += videos_count
            total_value += value
            
            text_widget.insert(tk.END, f"🔌 {name}\n")
            text_widget.insert(tk.END, f"   Показания: {value} kWh\n")
            text_widget.insert(tk.END, f"   Фото: {photos_count}  |  Видео: {videos_count}\n")
            text_widget.insert(tk.END, "-"*40 + "\n")
        
        text_widget.insert(tk.END, "\n" + "="*50 + "\n")
        text_widget.insert(tk.END, "📈  ОБЩАЯ СТАТИСТИКА\n")
        text_widget.insert(tk.END, "="*50 + "\n")
        text_widget.insert(tk.END, f"Всего счётчиков: {len(self.manager.counters)}\n")
        text_widget.insert(tk.END, f"Всего фото: {total_photos}\n")
        text_widget.insert(tk.END, f"Всего видео: {total_videos}\n")
        text_widget.insert(tk.END, f"Общее потребление: {total_value} kWh\n")
        
        text_widget.configure(state='disabled')
        
        # Кнопка закрытия
        tk.Button(stats_window, text="Закрыть", command=stats_window.destroy,
                 bg="#3498db", fg="white", font=('Arial', 10, 'bold'),
                 padx=20, pady=8, relief=tk.FLAT, cursor="hand2").pack(pady=20)
    
    def show_notification(self, message):
        """Показывает всплывающее уведомление"""
        notification = tk.Toplevel(self.root)
        notification.title("Уведомление")
        notification.geometry("300x60")
        notification.configure(bg="#2c3e50")
        
        # Центрируем
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 150
        y = self.root.winfo_y() + 50
        notification.geometry(f"+{x}+{y}")
        
        tk.Label(notification, text=message, 
                font=('Arial', 10, 'bold'), 
                fg="#00ff00", bg="#2c3e50").pack(expand=True)
        
        notification.after(2000, notification.destroy)
    
    def open_counter(self, name):
        path = self.manager.get_counter_path(name)
        if path:
            CounterWindow(self.root, name, path)

# ---------- Запуск приложения ----------
if __name__ == "__main__":
    root = tk.Tk()
    
    # Устанавливаем иконку окна (опционально)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = DesktopApp(root)
    root.mainloop()