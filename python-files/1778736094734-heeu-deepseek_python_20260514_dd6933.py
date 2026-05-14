import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import shutil
import pickle
import math
import random
import sys
from datetime import datetime

# Скрываем консольное окно на Windows
if os.name == 'nt':
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# ---------- Конфигурация ----------
DATA_DIR = "electro_data"
COUNTERS_FILE = os.path.join(DATA_DIR, "counters.pkl")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ---------- Типы устройств ----------
DEVICE_TYPES = {
    "СЧ": {"name": "Счётчик", "color": "#2c3e50", "icon": "СЧ", "desc": "Электросчётчик"},
    "ТТ": {"name": "Трансформатор тока", "color": "#16a085", "icon": "ТТ", "desc": "ТТ"},
    "ТН": {"name": "Трансформатор напряжения", "color": "#8e44ad", "icon": "ТН", "desc": "ТН"}
}

# ---------- Генератор иконок ----------
class IconGenerator:
    @staticmethod
    def create_device_icon(parent, size=130, value=12345, name="", device_type="СЧ"):
        canvas = tk.Canvas(parent, width=size, height=size, bg='white', 
                          highlightthickness=0, cursor="hand2", bd=0)
        
        margin = 10
        type_info = DEVICE_TYPES.get(device_type, DEVICE_TYPES["СЧ"])
        color = type_info["color"]
        
        # Тень
        canvas.create_rectangle(margin+3, margin+3, size-margin+3, size-margin+3,
                               fill="#d5d8dc", outline="", width=0, rounded_corners=True)
        
        # Корпус с закруглёнными углами
        canvas.create_rectangle(margin, margin, size-margin, size-margin,
                               fill=color, outline="#1a252f", width=2,
                               rounded_corners=True, corner_radius=15)
        
        # Внутренняя рамка
        canvas.create_rectangle(margin+3, margin+3, size-margin-3, size-margin-3,
                               outline="#ffffff", width=1, 
                               rounded_corners=True, corner_radius=12)
        
        # Круглая область для букв
        center_x = size // 2
        center_y = size // 2 - 15
        circle_r = 35
        
        # Тень для круга
        canvas.create_oval(center_x-circle_r+2, center_y-circle_r+2,
                          center_x+circle_r+2, center_y+circle_r+2,
                          fill="#95a5a6", outline="")
        
        # Основной круг
        canvas.create_oval(center_x-circle_r, center_y-circle_r,
                          center_x+circle_r, center_y+circle_r,
                          fill="#ecf0f1", outline="#bdc3c7", width=2)
        
        # Буквы в круге
        canvas.create_text(center_x, center_y, text=type_info["icon"],
                          font=('Arial', 28, 'bold'), fill=color)
        
        # Маленькие буквы описания под кругом
        canvas.create_text(center_x, center_y + circle_r + 8, 
                          text=type_info["desc"],
                          font=('Arial', 8), fill="#ecf0f1")
        
        # Дисплей с цифрами
        display_y = center_y + circle_r + 25
        display_w = 80
        display_h = 25
        
        # Дисплей
        canvas.create_rectangle(center_x-display_w//2, display_y,
                               center_x+display_w//2, display_y+display_h,
                               fill="#1a252f", outline="#000000", width=1,
                               rounded_corners=True, corner_radius=5)
        
        # Цифры
        display_text = f"{value:05d}"
        digit_x = center_x - 35
        for i, digit in enumerate(display_text):
            canvas.create_text(digit_x + i*14, display_y+13, text=digit,
                              fill="#00ff00", font=('Courier', 10, 'bold'))
        
        # Индикатор
        indicator = canvas.create_oval(size-margin-12, margin+8,
                                      size-margin-4, margin+16,
                                      fill="#e74c3c", outline="#c0392b", width=1)
        
        # Название внизу
        name_text = name[:12] + "..." if len(name) > 12 else name
        canvas.create_text(center_x, size-margin-8, text=name_text,
                          fill="#ecf0f1", font=('Arial', 8, 'bold'))
        
        canvas.indicator = indicator
        canvas.device_type = device_type
        canvas.counter_value = value
        
        return canvas
    
    @staticmethod
    def update_indicator(canvas, frame):
        if hasattr(canvas, 'indicator'):
            if frame % 20 < 10:
                canvas.itemconfig(canvas.indicator, fill="#ff6b6b")
            else:
                canvas.itemconfig(canvas.indicator, fill="#e74c3c")

# Кастомный Canvas с закруглёнными прямоугольниками
class RoundedCanvas(tk.Canvas):
    def create_rectangle(self, x1, y1, x2, y2, rounded_corners=False, corner_radius=10, **kwargs):
        if rounded_corners:
            points = []
            for x, y in [(x1+corner_radius, y1), (x2-corner_radius, y1),
                        (x2, y1), (x2, y1+corner_radius),
                        (x2, y2-corner_radius), (x2, y2),
                        (x2-corner_radius, y2), (x1+corner_radius, y2),
                        (x1, y2), (x1, y2-corner_radius),
                        (x1, y1+corner_radius), (x1, y1)]:
                points.extend([x, y])
            return super().create_polygon(points, smooth=True, **kwargs)
        return super().create_rectangle(x1, y1, x2, y2, **kwargs)

# ---------- Модель данных ----------
class DeviceManager:
    def __init__(self):
        self.devices = self.load_devices()
        self.device_values = {}

    def load_devices(self):
        if os.path.exists(COUNTERS_FILE):
            try:
                with open(COUNTERS_FILE, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        return data
            except:
                pass
        return {}

    def save_devices(self):
        with open(COUNTERS_FILE, 'wb') as f:
            pickle.dump(self.devices, f)

    def add_device(self, name, device_type):
        if name in self.devices:
            return False
        path = os.path.join(DATA_DIR, name)
        os.makedirs(path, exist_ok=True)
        os.makedirs(os.path.join(path, "photos"), exist_ok=True)
        os.makedirs(os.path.join(path, "videos"), exist_ok=True)
        
        # Сохраняем тип устройства
        with open(os.path.join(path, "type.txt"), 'w') as f:
            f.write(device_type)
        
        self.devices[name] = {"path": path, "type": device_type}
        self.device_values[name] = random.randint(1000, 99999)
        self.save_devices()
        return True

    def delete_device(self, name):
        if name in self.devices:
            shutil.rmtree(self.devices[name]["path"])
            del self.devices[name]
            if name in self.device_values:
                del self.device_values[name]
            self.save_devices()

    def get_device_path(self, name):
        return self.devices[name]["path"] if name in self.devices else None
    
    def get_device_type(self, name):
        return self.devices[name]["type"] if name in self.devices else "СЧ"
    
    def update_device_value(self, name):
        if name in self.device_values:
            self.device_values[name] += random.randint(0, 3)
            return self.device_values[name]
        return 0

# ---------- Окно устройства ----------
class DeviceWindow:
    def __init__(self, parent, device_name, device_path, device_type):
        self.window = tk.Toplevel(parent)
        self.window.title(f"⚡ {device_name}")
        self.window.geometry("900x650")
        self.window.configure(bg="#f5f6fa")
        self.window.transient(parent)
        
        self.device_name = device_name
        self.device_path = device_path
        self.device_type = device_type
        self.photos_path = os.path.join(device_path, "photos")
        self.videos_path = os.path.join(device_path, "videos")
        
        self.create_widgets()
        self.refresh_list()
    
    def create_widgets(self):
        type_info = DEVICE_TYPES.get(self.device_type, DEVICE_TYPES["СЧ"])
        
        # Заголовок с закруглениями
        header = tk.Frame(self.window, bg=type_info["color"], height=110)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Значение
        value_frame = tk.Frame(header, bg=type_info["color"])
        value_frame.pack(pady=(15, 5))
        
        tk.Label(value_frame, text="ТЕКУЩИЕ ПОКАЗАНИЯ", 
                font=('Arial', 9), fg="#ecf0f1", bg=type_info["color"]).pack()
        
        self.value_label = tk.Label(value_frame, text="0 kWh", 
                                   font=('Arial', 26, 'bold'), 
                                   fg="#00ff00", bg=type_info["color"])
        self.value_label.pack()
        
        tk.Label(header, text=f"{type_info['icon']} {self.device_name}", 
                font=('Arial', 16, 'bold'), 
                fg="white", bg=type_info["color"]).pack()
        
        self.load_counter_value()
        
        # Панель инструментов
        toolbar = tk.Frame(self.window, bg="#f5f6fa", height=50)
        toolbar.pack(fill=tk.X, padx=20, pady=(15, 10))
        toolbar.pack_propagate(False)
        
        buttons = [
            ("📸 Загрузить фото", self.upload_photo, "#27ae60"),
            ("🎬 Загрузить видео", self.upload_video, "#2980b9"),
            ("👁️ Открыть", self.open_selected, "#f39c12"),
            ("🗑️ Удалить", self.delete_selected, "#e74c3c"),
            ("➕ Добавить показания", self.add_reading, "#8e44ad")
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(toolbar, text=text, command=command,
                          font=('Arial', 9, 'bold'),
                          bg=color, fg="white",
                          padx=15, pady=6,
                          relief=tk.FLAT, cursor="hand2",
                          bd=0)
            btn.pack(side=tk.LEFT, padx=4)
        
        # Список файлов с закруглениями
        list_container = tk.Frame(self.window, bg="#f5f6fa")
        list_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Стилизованный фрейм
        list_frame = tk.Frame(list_container, bg="white", relief=tk.FLAT, bd=0)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовки
        header_frame = tk.Frame(list_frame, bg="#34495e", height=35)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="Тип", width=8, 
                font=('Arial', 9, 'bold'), fg="white", bg="#34495e").pack(side=tk.LEFT, padx=10)
        tk.Label(header_frame, text="Имя файла", 
                font=('Arial', 9, 'bold'), fg="white", bg="#34495e").pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)
        tk.Label(header_frame, text="Размер", width=10,
                font=('Arial', 9, 'bold'), fg="white", bg="#34495e").pack(side=tk.RIGHT, padx=10)
        
        # Список
        list_area = tk.Frame(list_frame, bg="white")
        list_area.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_area)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_area, 
                                 yscrollcommand=scrollbar.set,
                                 font=('Arial', 10),
                                 bg="white",
                                 fg="#2c3e50",
                                 selectbackground="#3498db",
                                 selectforeground="white",
                                 relief=tk.FLAT,
                                 bd=0,
                                 highlightthickness=0)
        self.listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.listbox.yview)
        
        # Информация
        info_frame = tk.Frame(list_frame, bg="#ecf0f1", height=30)
        info_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.info_label = tk.Label(info_frame, text="", 
                                  font=('Arial', 8), fg="#7f8c8d", bg="#ecf0f1")
        self.info_label.pack(pady=5)
    
    def load_counter_value(self):
        value_file = os.path.join(self.device_path, "value.txt")
        if os.path.exists(value_file):
            try:
                with open(value_file, 'r') as f:
                    value = int(f.read())
                    self.value_label.config(text=f"{value} kWh")
            except:
                pass
    
    def save_counter_value(self, value):
        value_file = os.path.join(self.device_path, "value.txt")
        with open(value_file, 'w') as f:
            f.write(str(value))
    
    def get_file_size(self, filepath):
        size = os.path.getsize(filepath)
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"
    
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        all_files = []
        
        for f in os.listdir(self.photos_path):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                full_path = os.path.join(self.photos_path, f)
                size = self.get_file_size(full_path)
                all_files.append(("🖼️ ФОТО", f, size))
        
        for f in os.listdir(self.videos_path):
            if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                full_path = os.path.join(self.videos_path, f)
                size = self.get_file_size(full_path)
                all_files.append(("🎬 ВИДЕО", f, size))
        
        if not all_files:
            self.listbox.insert(tk.END, "📭  Нет загруженных файлов")
            self.listbox.itemconfig(0, fg="#95a5a6", font=('Arial', 10, 'italic'))
            self.info_label.config(text="Нет файлов")
        else:
            for ftype, fname, size in sorted(all_files, key=lambda x: x[1]):
                display_text = f"{ftype:<8}  {fname:<50}  {size:>10}"
                self.listbox.insert(tk.END, display_text)
            self.info_label.config(text=f"Всего: {len(all_files)} файлов")
    
    def upload_photo(self):
        file_path = filedialog.askopenfilename(
            title="Выберите фото",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            dest = os.path.join(self.photos_path, os.path.basename(file_path))
            shutil.copy(file_path, dest)
            self.refresh_list()
    
    def upload_video(self):
        file_path = filedialog.askopenfilename(
            title="Выберите видео",
            filetypes=[("Видео", "*.mp4 *.avi *.mov *.mkv *.webm")]
        )
        if file_path:
            dest = os.path.join(self.videos_path, os.path.basename(file_path))
            shutil.copy(file_path, dest)
            self.refresh_list()
    
    def add_reading(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Добавить показания")
        dialog.geometry("350x200")
        dialog.configure(bg="#f5f6fa")
        dialog.transient(self.window)
        
        current_text = self.value_label.cget("text").replace(" kWh", "")
        
        tk.Label(dialog, text="Новые показания", 
                font=('Arial', 12, 'bold'), bg="#f5f6fa", fg="#2c3e50").pack(pady=15)
        
        tk.Label(dialog, text=f"Текущие: {current_text} kWh", 
                font=('Arial', 10), bg="#f5f6fa", fg="#7f8c8d").pack()
        
        entry = tk.Entry(dialog, font=('Arial', 14), width=12, justify='center',
                        relief=tk.FLAT, bd=1)
        entry.pack(pady=15)
        entry.focus()
        
        def save():
            try:
                new_value = int(entry.get())
                if new_value < int(current_text):
                    messagebox.showwarning("Ошибка", "Новые показания не могут быть меньше текущих!")
                    return
                self.value_label.config(text=f"{new_value} kWh")
                self.save_counter_value(new_value)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное число!")
        
        btn_frame = tk.Frame(dialog, bg="#f5f6fa")
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Сохранить", command=save,
                 bg="#27ae60", fg="white", font=('Arial', 9, 'bold'),
                 padx=15, pady=5, relief=tk.FLAT, cursor="hand2",
                 bd=0).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Отмена", command=dialog.destroy,
                 bg="#95a5a6", fg="white", font=('Arial', 9, 'bold'),
                 padx=15, pady=5, relief=tk.FLAT, cursor="hand2",
                 bd=0).pack(side=tk.LEFT, padx=5)
        
        entry.bind('<Return>', lambda e: save())
    
    def open_selected(self):
        selection = self.listbox.curselection()
        if not selection or self.listbox.get(selection[0]).startswith("📭"):
            return
        
        item = self.listbox.get(selection[0])
        parts = item.split("  ")
        if len(parts) >= 2:
            fname = parts[1].strip()
            
            for folder_path in [self.photos_path, self.videos_path]:
                full_path = os.path.join(folder_path, fname)
                if os.path.exists(full_path):
                    if os.name == 'nt':
                        os.startfile(full_path)
                    else:
                        os.system(f'xdg-open "{full_path}"')
                    return
    
    def delete_selected(self):
        selection = self.listbox.curselection()
        if not selection or self.listbox.get(selection[0]).startswith("📭"):
            return
        
        item = self.listbox.get(selection[0])
        parts = item.split("  ")
        if len(parts) >= 2:
            fname = parts[1].strip()
            
            if messagebox.askyesno("Подтверждение", f"Удалить '{fname}'?"):
                for folder_path in [self.photos_path, self.videos_path]:
                    full_path = os.path.join(folder_path, fname)
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        self.refresh_list()
                        return

# ---------- Главное окно ----------
class DesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ Электрооборудование")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f5f6fa")
        self.root.minsize(800, 500)
        
        self.manager = DeviceManager()
        self.icon_generator = IconGenerator()
        self.animation_frame = 0
        
        self.create_widgets()
        self.animate_indicators()
        self.update_device_list()
    
    def create_widgets(self):
        # Заголовок с закруглениями
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_frame = tk.Frame(header, bg="#2c3e50")
        title_frame.pack(expand=True)
        
        tk.Label(title_frame, text="⚡", font=('Arial', 32), 
                fg="#f39c12", bg="#2c3e50").pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(title_frame, text="ЭЛЕКТРООБОРУДОВАНИЕ", 
                font=('Arial', 20, 'bold'), 
                fg="white", bg="#2c3e50").pack(side=tk.LEFT)
        
        # Панель управления
        control_panel = tk.Frame(self.root, bg="#34495e", height=55)
        control_panel.pack(fill=tk.X)
        control_panel.pack_propagate(False)
        
        # Поиск
        search_frame = tk.Frame(control_panel, bg="#34495e")
        search_frame.pack(side=tk.LEFT, padx=20, pady=10)
        
        tk.Label(search_frame, text="🔍", font=('Arial', 12), 
                bg="#34495e", fg="white").pack(side=tk.LEFT, padx=(0, 8))
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *args: self.update_device_list())
        
        self.search_entry = tk.Entry(search_frame, 
                                     textvariable=self.search_var,
                                     font=('Arial', 10),
                                     width=30,
                                     bg="#ecf0f1",
                                     relief=tk.FLAT,
                                     bd=0)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.insert(0, "Поиск...")
        self.search_entry.bind('<FocusIn>', lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Поиск..." else None)
        self.search_entry.bind('<FocusOut>', lambda e: self.search_entry.insert(0, "Поиск...") if not self.search_entry.get() else None)
        
        # Кнопки
        btn_frame = tk.Frame(control_panel, bg="#34495e")
        btn_frame.pack(side=tk.RIGHT, padx=20)
        
        # Выпадающий список для выбора типа устройства
        self.device_type_var = tk.StringVar(value="СЧ")
        
        type_menu = tk.OptionMenu(btn_frame, self.device_type_var, "СЧ", "ТТ", "ТН")
        type_menu.config(bg="#3498db", fg="white", font=('Arial', 9, 'bold'),
                        relief=tk.FLAT, bd=0, cursor="hand2")
        type_menu.pack(side=tk.LEFT, padx=4)
        
        tk.Button(btn_frame, text="➕ Новый", command=self.create_device,
                 bg="#27ae60", fg="white", font=('Arial', 9, 'bold'),
                 padx=15, pady=5, relief=tk.FLAT, cursor="hand2",
                 bd=0).pack(side=tk.LEFT, padx=4)
        
        tk.Button(btn_frame, text="🗑️ Удалить", command=self.delete_device,
                 bg="#e74c3c", fg="white", font=('Arial', 9, 'bold'),
                 padx=15, pady=5, relief=tk.FLAT, cursor="hand2",
                 bd=0).pack(side=tk.LEFT, padx=4)
        
        # Область для устройств
        canvas_frame = tk.Frame(self.root, bg="#f5f6fa")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#f5f6fa", highlightthickness=0)
        scrollbar_y = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        scrollbar_x = tk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.inner_frame = tk.Frame(self.canvas, bg="#f5f6fa")
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Статус
        status_frame = tk.Frame(self.root, bg="#bdc3c7", height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(status_frame, text="Готов к работе", 
                                     font=('Arial', 8), bg="#bdc3c7", fg="#2c3e50")
        self.status_label.pack(side=tk.LEFT, padx=10, pady=3)
        
        self.stats_label = tk.Label(status_frame, text="", 
                                    font=('Arial', 8), bg="#bdc3c7", fg="#2c3e50")
        self.stats_label.pack(side=tk.RIGHT, padx=10, pady=3)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def update_device_list(self):
        # Очищаем
        for widget in self.inner_frame.winfo_children():
            widget.destroy()
        
        # Фильтрация
        search_text = self.search_var.get().lower()
        if search_text == "поиск...":
            search_text = ""
        
        filtered = {name: info for name, info in self.manager.devices.items() 
                   if search_text in name.lower()}
        
        if not filtered:
            empty_label = tk.Label(self.inner_frame, 
                                   text="📭 Нет оборудования\n\nНажмите «Новый» для создания",
                                   font=('Arial', 14),
                                   fg="#95a5a6", bg="#f5f6fa",
                                   justify=tk.CENTER)
            empty_label.pack(expand=True, pady=100)
            self.stats_label.config(text="Всего: 0")
            return
        
        # Создаём сетку
        cols = 3
        row = 0
        col = 0
        
        for name, info in filtered.items():
            device_type = info["type"]
            
            if name not in self.manager.device_values:
                self.manager.device_values[name] = random.randint(1000, 99999)
            
            value = self.manager.device_values[name]
            
            # Карточка с закруглениями
            card = tk.Frame(self.inner_frame, bg="white", relief=tk.FLAT, bd=1)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="n")
            
            # Иконка
            icon = self.icon_generator.create_device_icon(card, size=130, value=value, name=name, device_type=device_type)
            icon.pack(padx=15, pady=(15, 5))
            icon.bind("<Button-1>", lambda e, n=name: self.open_device(n))
            
            # Название
            name_label = tk.Label(card, text=name, 
                                 font=('Arial', 10, 'bold'),
                                 fg="#2c3e50", bg="white")
            name_label.pack(pady=(5, 0))
            
            # Значение
            value_label = tk.Label(card, text=f"{value} kWh", 
                                  font=('Arial', 9),
                                  fg="#7f8c8d", bg="white")
            value_label.pack(pady=(0, 5))
            
            # Кнопка
            open_btn = tk.Button(card, text="Открыть", 
                                command=lambda n=name: self.open_device(n),
                                font=('Arial', 9),
                                bg="#3498db", fg="white",
                                padx=15, pady=3,
                                relief=tk.FLAT, cursor="hand2",
                                bd=0)
            open_btn.pack(pady=(0, 15))
            
            # Hover
            def on_enter(e, c=card):
                c.configure(highlightthickness=2, highlightcolor="#3498db")
            def on_leave(e, c=card):
                c.configure(highlightthickness=1, highlightcolor="#bdc3c7")
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            
            # Сохраняем для анимации
            icon.value_label = value_label
            
            col += 1
            if col >= cols:
                col = 0
                row += 1
        
        # Обновляем статистику
        total_devices = len(self.manager.devices)
        self.stats_label.config(text=f"Всего: {total_devices}")
        
        # Обновляем canvas
        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def animate_indicators(self):
        self.animation_frame += 1
        
        for widget in self.inner_frame.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tk.Canvas) and hasattr(child, 'indicator'):
                    if self.animation_frame % 20 < 10:
                        child.itemconfig(child.indicator, fill="#ff6b6b")
                    else:
                        child.itemconfig(child.indicator, fill="#e74c3c")
        
        self.root.after(500, self.animate_indicators)
    
    def create_device(self):
        name = simpledialog.askstring("Новое оборудование", "Введите название:", parent=self.root)
        if name and name.strip():
            name = name.strip()
            device_type = self.device_type_var.get()
            
            if self.manager.add_device(name, device_type):
                self.update_device_list()
                type_name = DEVICE_TYPES[device_type]["name"]
                self.status_label.config(text=f"{type_name} «{name}» создан")
                self.root.after(2000, lambda: self.status_label.config(text="Готов к работе"))
            else:
                messagebox.showerror("Ошибка", "Такое имя уже существует")
    
    def delete_device(self):
        if not self.manager.devices:
            messagebox.showwarning("Внимание", "Нет оборудования для удаления")
            return
        
        names = list(self.manager.devices.keys())
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Удалить оборудование")
        dialog.geometry("300x250")
        dialog.configure(bg="#f5f6fa")
        dialog.transient(self.root)
        
        tk.Label(dialog, text="Выберите оборудование:", 
                font=('Arial', 11), bg="#f5f6fa", fg="#2c3e50").pack(pady=10)
        
        listbox = tk.Listbox(dialog, font=('Arial', 10), 
                            bg="white", relief=tk.FLAT, bd=1)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        for name in names:
            device_type = self.manager.get_device_type(name)
            icon = DEVICE_TYPES[device_type]["icon"]
            listbox.insert(tk.END, f"{icon} {name}")
        
        def delete():
            selection = listbox.curselection()
            if selection:
                item = listbox.get(selection[0])
                name = item[2:]  # Убираем иконку
                if messagebox.askyesno("Подтверждение", f"Удалить «{name}»?"):
                    self.manager.delete_device(name)
                    self.update_device_list()
                    dialog.destroy()
                    self.status_label.config(text=f"«{name}» удалён")
                    self.root.after(2000, lambda: self.status_label.config(text="Готов к работе"))
        
        tk.Button(dialog, text="Удалить", command=delete,
                 bg="#e74c3c", fg="white", font=('Arial', 9, 'bold'),
                 padx=15, pady=5, relief=tk.FLAT, cursor="hand2",
                 bd=0).pack(pady=10)
    
    def open_device(self, name):
        path = self.manager.get_device_path(name)
        device_type = self.manager.get_device_type(name)
        if path:
            DeviceWindow(self.root, name, path, device_type)

# ---------- Запуск ----------
if __name__ == "__main__":
    root = tk.Tk()
    
    # Центрируем окно
    root.update_idletasks()
    width = 1100
    height = 700
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    app = DesktopApp(root)
    root.mainloop()