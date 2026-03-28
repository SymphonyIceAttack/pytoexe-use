import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
import json
import sys
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk
import random

# Виртуальная файловая система
class VirtualFileSystem:
    def __init__(self):
        self.root = {
            'name': 'System',
            'type': 'dir',
            'content': {},
            'parent': None
        }
        self.current_dir = self.root
        self.init_structure()
    
    def init_structure(self):
        # Создание папок
        docs = self.create_dir(self.root, 'Documents')
        downloads = self.create_dir(self.root, 'Downloads')
        music = self.create_dir(self.root, 'Music')
        pictures = self.create_dir(self.root, 'Pictures')
        videos = self.create_dir(self.root, 'Videos')
        desktop = self.create_dir(self.root, 'Desktop')
        
        # Создание файлов
        self.create_file(desktop, 'Welcome.txt', 'Добро пожаловать в AnonkisOS!')
        self.create_file(self.root, 'readme.txt', 'Это виртуальная файловая система')
    
    def create_dir(self, parent, name):
        dir_obj = {
            'name': name,
            'type': 'dir',
            'content': {},
            'parent': parent
        }
        parent['content'][name] = dir_obj
        return dir_obj
    
    def create_file(self, parent, name, content=''):
        file_obj = {
            'name': name,
            'type': 'file',
            'content': content,
            'parent': parent
        }
        parent['content'][name] = file_obj
        return file_obj
    
    def get_path(self):
        path = []
        current = self.current_dir
        while current and current['name'] != 'System':
            path.insert(0, current['name'])
            current = current['parent']
        return '/' + '/'.join(path)
    
    def go_up(self):
        if self.current_dir['parent']:
            self.current_dir = self.current_dir['parent']
            return True
        return False
    
    def change_dir(self, name):
        if name in self.current_dir['content'] and self.current_dir['content'][name]['type'] == 'dir':
            self.current_dir = self.current_dir['content'][name]
            return True
        return False
    
    def list_dir(self):
        items = []
        for name, item in self.current_dir['content'].items():
            items.append({
                'name': name,
                'type': item['type']
            })
        return items
    
    def read_file(self, name):
        if name in self.current_dir['content'] and self.current_dir['content'][name]['type'] == 'file':
            return self.current_dir['content'][name]['content']
        return None

# Внутреннее окно
class AppWindow:
    def __init__(self, parent, title, width=600, height=400):
        self.parent = parent
        self.title = title
        
        # Создание окна
        self.frame = tk.Frame(parent.window_area, bg='#2c2c2e', bd=1, relief=tk.SOLID)
        
        # Заголовок
        title_bar = tk.Frame(self.frame, bg='#3a3a3c', height=30)
        title_bar.pack(fill=tk.X)
        title_bar.pack_propagate(False)
        
        # Кнопка закрытия
        close_btn = tk.Button(title_bar, text="✕", bg='#3a3a3c', fg='#ff5f57',
                             relief=tk.FLAT, command=self.close)
        close_btn.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Заголовок
        title_label = tk.Label(title_bar, text=title, bg='#3a3a3c', fg='white')
        title_label.pack(side=tk.LEFT, padx=10)
        
        # Контент
        self.content = tk.Frame(self.frame, bg='#1c1c1e')
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Позиция
        x = 50 + len(parent.windows) * 30
        y = 50 + len(parent.windows) * 30
        self.frame.place(x=x, y=y, width=width, height=height)
        
        # Перетаскивание
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)
        
        self.drag_x = 0
        self.drag_y = 0
        self.parent.add_window(self)
    
    def start_move(self, event):
        self.drag_x = event.x
        self.drag_y = event.y
    
    def on_move(self, event):
        x = self.frame.winfo_x() + event.x - self.drag_x
        y = self.frame.winfo_y() + event.y - self.drag_y
        self.frame.place(x=x, y=y)
    
    def close(self):
        self.parent.close_window(self)
        self.frame.destroy()
    
    def get_content(self):
        return self.content

# Главное приложение
class AnonkisOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("AnonkisOS")
        
        # Полноэкранный режим
        self.root.attributes('-fullscreen', True)
        
        # Привязываем клавиши для выхода из полноэкранного режима
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.toggle_fullscreen)
        
        # Цвета
        self.bg_color = "#0a0a0a"
        self.accent_color = "#ff6b4a"
        self.secondary_color = "#1e1e1e"
        self.text_color = "#ffffff"
        
        self.root.configure(bg=self.bg_color)
        
        self.windows = []
        self.start_menu_visible = False
        self.fullscreen = True
        self.vfs = VirtualFileSystem()
        
        self.init_ui()
        self.create_wallpaper()
        self.update_clock()
        
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
    
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
    
    def init_ui(self):
        # Рабочий стол
        self.desktop = tk.Frame(self.root, bg=self.bg_color)
        self.desktop.pack(fill=tk.BOTH, expand=True)
        
        # Область для окон
        self.window_area = tk.Frame(self.desktop, bg=self.bg_color)
        self.window_area.pack(fill=tk.BOTH, expand=True)
        
        # Панель задач
        self.taskbar = tk.Frame(self.root, bg=self.secondary_color, height=50)
        self.taskbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.taskbar.pack_propagate(False)
        
        # Кнопка Пуск
        self.start_btn = tk.Button(self.taskbar, text="Пуск", font=('Arial', 11, 'bold'),
                                  bg=self.accent_color, fg='white', relief=tk.FLAT,
                                  padx=20, command=self.toggle_start_menu)
        self.start_btn.pack(side=tk.LEFT, padx=10, pady=8)
        
        # Панель открытых окон
        self.taskbar_windows = tk.Frame(self.taskbar, bg=self.secondary_color)
        self.taskbar_windows.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Часы
        self.clock_label = tk.Label(self.taskbar, bg=self.secondary_color, 
                                   fg=self.text_color, font=('Arial', 11))
        self.clock_label.pack(side=tk.RIGHT, padx=15)
        
        # Меню Пуск
        self.create_start_menu()
    
    def create_start_menu(self):
        self.start_menu = tk.Toplevel(self.root)
        self.start_menu.withdraw()
        self.start_menu.overrideredirect(True)
        self.start_menu.configure(bg=self.secondary_color)
        
        frame = tk.Frame(self.start_menu, bg=self.secondary_color)
        frame.pack(padx=10, pady=10)
        
        # Заголовок
        tk.Label(frame, text="AnonkisOS", bg=self.secondary_color,
                fg=self.accent_color, font=('Arial', 16, 'bold')).pack(pady=10)
        
        # Список приложений
        apps = [
            ("📝 Блокнот", self.open_notepad),
            ("🧮 Калькулятор", self.open_calculator),
            ("🎨 Paint", self.open_paint),
            ("📁 Проводник", self.open_explorer),
            ("⚡ Терминал", self.open_terminal),
            ("🎵 Медиаплеер", self.open_media_player),
            ("⚙️ Настройки", self.open_settings)
        ]
        
        for name, command in apps:
            btn = tk.Button(frame, text=name, bg=self.secondary_color,
                           fg=self.text_color, relief=tk.FLAT, anchor='w',
                           font=('Arial', 11), command=command)
            btn.pack(fill=tk.X, pady=2)
        
        # Кнопка выключения
        tk.Button(frame, text="⏻ Выключение", bg='#3a3a3a',
                 fg=self.text_color, relief=tk.FLAT,
                 command=self.show_power_menu).pack(fill=tk.X, pady=10)
    
    def toggle_start_menu(self):
        if self.start_menu_visible:
            self.start_menu.withdraw()
        else:
            x = self.start_btn.winfo_rootx()
            y = self.start_btn.winfo_rooty() - 300
            self.start_menu.geometry(f"250x400+{x}+{y}")
            self.start_menu.deiconify()
        self.start_menu_visible = not self.start_menu_visible
    
    def update_taskbar(self):
        for widget in self.taskbar_windows.winfo_children():
            widget.destroy()
        
        for window in self.windows:
            btn = tk.Button(self.taskbar_windows, text=window.title,
                           bg=self.secondary_color, fg=self.text_color,
                           relief=tk.FLAT, command=lambda w=window: w.frame.lift())
            btn.pack(side=tk.LEFT, padx=5)
    
    def add_window(self, window):
        self.windows.append(window)
        self.update_taskbar()
    
    def close_window(self, window):
        if window in self.windows:
            self.windows.remove(window)
            self.update_taskbar()
    
    def create_wallpaper(self):
        # Получаем размеры экрана
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        
        # Создание градиента
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        for i in range(height):
            r = int(180 - (i / height) * 80)
            g = int(100 - (i / height) * 60)
            b = int(80 - (i / height) * 50)
            draw.line([(0, i), (width, i)], fill=(r, g, b))
        
        # Добавляем звезды для красоты
        for _ in range(200):
            x = random.randint(0, width)
            y = random.randint(0, height)
            brightness = random.randint(100, 255)
            draw.point((x, y), fill=(brightness, brightness, brightness))
        
        self.wallpaper = ImageTk.PhotoImage(image)
        
        bg_label = tk.Label(self.desktop, image=self.wallpaper)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.lower()
    
    def open_notepad(self):
        window = AppWindow(self, "Блокнот", 700, 500)
        content = window.get_content()
        
        text = tk.Text(content, bg='#2a2a2a', fg='white',
                      insertbackground='white', font=('Consolas', 12),
                      wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        
        # Статусбар
        status = tk.Frame(content, bg='#3a3a3a', height=25)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        
        status_label = tk.Label(status, text="Готов", bg='#3a3a3a',
                               fg='gray', font=('Arial', 9))
        status_label.pack(side=tk.LEFT, padx=5)
        
        def update_status(event=None):
            chars = len(text.get('1.0', 'end-1c'))
            lines = len(text.get('1.0', 'end-1c').split('\n'))
            status_label.config(text=f"Символов: {chars} | Строк: {lines}")
        
        text.bind('<KeyRelease>', update_status)
        update_status()
    
    def open_calculator(self):
        window = AppWindow(self, "Калькулятор", 320, 450)
        content = window.get_content()
        
        display_var = tk.StringVar(value="0")
        display = tk.Entry(content, textvariable=display_var, font=('Arial', 24),
                          justify='right', bg='#2a2a2a', fg='white',
                          state='readonly', readonlybackground='#2a2a2a')
        display.pack(fill=tk.X, padx=10, pady=15, ipady=10)
        
        buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', 'C', '=', '+']
        ]
        
        current = ""
        
        def click(value):
            nonlocal current
            if value == 'C':
                current = ""
                display_var.set("0")
            elif value == '=':
                try:
                    result = eval(current)
                    if result == int(result):
                        result = int(result)
                    display_var.set(str(result))
                    current = str(result)
                except:
                    display_var.set("Ошибка")
                    current = ""
            else:
                if current == "0" and value not in '.':
                    current = value
                else:
                    current += value
                display_var.set(current)
        
        btn_frame = tk.Frame(content, bg='#1c1c1e')
        btn_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, row in enumerate(buttons):
            for j, val in enumerate(row):
                if val:
                    color = self.accent_color if val in ['=', 'C'] else '#3a3a3a'
                    btn = tk.Button(btn_frame, text=val, bg=color, fg='white',
                                   font=('Arial', 14), relief=tk.FLAT,
                                   command=lambda x=val: click(x))
                    btn.grid(row=i, column=j, padx=3, pady=3, sticky='nsew')
                    btn_frame.grid_columnconfigure(j, weight=1)
            btn_frame.grid_rowconfigure(i, weight=1)
    
    def open_paint(self):
        window = AppWindow(self, "Paint", 900, 600)
        content = window.get_content()
        
        color = self.accent_color
        size = 3
        
        # Панель инструментов
        toolbar = tk.Frame(content, bg='#3a3a3a', height=45)
        toolbar.pack(fill=tk.X)
        toolbar.pack_propagate(False)
        
        # Выбор цвета
        color_btn = tk.Button(toolbar, text="🎨 Цвет", bg='#3a3a3a', fg='white',
                             relief=tk.FLAT, command=lambda: self.choose_color(color_btn))
        color_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Размер кисти
        tk.Label(toolbar, text="Размер:", bg='#3a3a3a', fg='white').pack(side=tk.LEFT, padx=5)
        size_var = tk.IntVar(value=3)
        size_scale = tk.Scale(toolbar, from_=1, to=20, orient=tk.HORIZONTAL,
                             variable=size_var, bg='#3a3a3a', highlightthickness=0,
                             length=100)
        size_scale.pack(side=tk.LEFT, padx=5)
        
        # Очистить
        clear_btn = tk.Button(toolbar, text="🗑 Очистить", bg='#3a3a3a', fg='white',
                             relief=tk.FLAT, command=lambda: canvas.delete("all"))
        clear_btn.pack(side=tk.LEFT, padx=10)
        
        # Холст
        canvas = tk.Canvas(content, bg='white', highlightthickness=1,
                          highlightbackground='#3a3a3a')
        canvas.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        last_x, last_y = None, None
        
        def paint(event):
            nonlocal last_x, last_y
            if last_x and last_y:
                canvas.create_line(last_x, last_y, event.x, event.y,
                                 fill=color, width=size_var.get(),
                                 capstyle=tk.ROUND, smooth=True)
            last_x, last_y = event.x, event.y
        
        def reset(event):
            nonlocal last_x, last_y
            last_x, last_y = None, None
        
        canvas.bind("<B1-Motion>", paint)
        canvas.bind("<ButtonRelease-1>", reset)
    
    def choose_color(self, button):
        color = colorchooser.askcolor()[1]
        if color:
            button.config(bg=color)
            return color
        return self.accent_color
    
    def open_explorer(self):
        window = AppWindow(self, "Проводник", 800, 550)
        content = window.get_content()
        
        path_var = tk.StringVar(value=self.vfs.get_path())
        
        # Панель навигации
        nav = tk.Frame(content, bg='#3a3a3a', height=40)
        nav.pack(fill=tk.X)
        nav.pack_propagate(False)
        
        back_btn = tk.Button(nav, text="← Назад", bg='#3a3a3a', fg='white',
                            relief=tk.FLAT, command=lambda: self.explorer_back(tree, path_var))
        back_btn.pack(side=tk.LEFT, padx=10, pady=5)
        
        path_entry = tk.Entry(nav, textvariable=path_var, bg='#2a2a2a',
                             fg='white', relief=tk.FLAT, state='readonly')
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        
        # Список файлов
        tree_frame = tk.Frame(content, bg='#1c1c1e')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        tree = ttk.Treeview(tree_frame, columns=('type',), show='tree headings')
        tree.heading('#0', text='Имя')
        tree.heading('type', text='Тип')
        tree.column('#0', width=400)
        tree.column('type', width=100)
        
        # Настройка стиля
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background='#1c1c1e',
                       foreground='white', fieldbackground='#1c1c1e')
        style.configure("Treeview.Heading", background='#3a3a3a',
                       foreground='white')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh():
            tree.delete(*tree.get_children())
            items = self.vfs.list_dir()
            for item in items:
                icon = "📁" if item['type'] == 'dir' else "📄"
                tree.insert('', 'end', text=f"{icon} {item['name']}",
                           values=('Папка' if item['type'] == 'dir' else 'Файл',))
        
        refresh()
        
        def on_double_click(event):
            item = tree.selection()[0]
            name = tree.item(item, 'text')[2:]
            if self.vfs.change_dir(name):
                path_var.set(self.vfs.get_path())
                refresh()
        
        tree.bind("<Double-1>", on_double_click)
    
    def explorer_back(self, tree, path_var):
        if self.vfs.go_up():
            path_var.set(self.vfs.get_path())
            tree.delete(*tree.get_children())
            items = self.vfs.list_dir()
            for item in items:
                icon = "📁" if item['type'] == 'dir' else "📄"
                tree.insert('', 'end', text=f"{icon} {item['name']}",
                           values=('Папка' if item['type'] == 'dir' else 'Файл',))
    
    def open_terminal(self):
        window = AppWindow(self, "Терминал", 800, 500)
        content = window.get_content()
        
        output = tk.Text(content, bg='black', fg='#00ff00',
                        font=('Consolas', 11), insertbackground='#00ff00')
        output.pack(fill=tk.BOTH, expand=True)
        
        output.insert('end', "AnonkisOS Terminal v2.0\n")
        output.insert('end', "=" * 50 + "\n\n")
        output.insert('end', "Доступные команды: help, clear, ls, pwd, exit\n\n")
        
        input_frame = tk.Frame(content, bg='black')
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        prompt = tk.Label(input_frame, text="$ ", bg='black', fg='#00ff00',
                         font=('Consolas', 11, 'bold'))
        prompt.pack(side=tk.LEFT)
        
        cmd_input = tk.Entry(input_frame, bg='black', fg='#00ff00',
                            font=('Consolas', 11), insertbackground='#00ff00',
                            relief=tk.FLAT)
        cmd_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        def execute(event=None):
            cmd = cmd_input.get().strip()
            output.insert('end', f"$ {cmd}\n")
            
            if cmd == 'help':
                output.insert('end', "  help  - показать справку\n")
                output.insert('end', "  clear - очистить экран\n")
                output.insert('end', "  ls    - список файлов\n")
                output.insert('end', "  pwd   - текущий путь\n")
                output.insert('end', "  exit  - закрыть терминал\n\n")
            elif cmd == 'clear':
                output.delete('1.0', 'end')
            elif cmd == 'ls':
                items = self.vfs.list_dir()
                for item in items:
                    output.insert('end', f"  {item['name']}\n")
                output.insert('end', "\n")
            elif cmd == 'pwd':
                output.insert('end', f"  {self.vfs.get_path()}\n\n")
            elif cmd == 'exit':
                window.close()
            elif cmd:
                output.insert('end', f"  Команда не найдена: {cmd}\n\n")
            
            output.see('end')
            cmd_input.delete(0, 'end')
        
        cmd_input.bind('<Return>', execute)
    
    def open_media_player(self):
        window = AppWindow(self, "Медиаплеер", 700, 500)
        content = window.get_content()
        
        main_frame = tk.Frame(content, bg='#1c1c1e')
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Иконка
        icon = tk.Label(main_frame, text="🎵", bg='#1c1c1e',
                       fg=self.accent_color, font=('Segoe UI', 80))
        icon.pack(pady=40)
        
        tk.Label(main_frame, text="Медиаплеер", bg='#1c1c1e',
                fg='white', font=('Arial', 18, 'bold')).pack()
        
        tk.Label(main_frame, text="Выберите медиафайл для воспроизведения",
                bg='#1c1c1e', fg='gray', font=('Arial', 11)).pack(pady=10)
        
        def select_file():
            filename = filedialog.askopenfilename(
                title="Выбрать медиафайл",
                filetypes=[("Аудио", "*.mp3 *.wav"), ("Видео", "*.mp4")]
            )
            if filename:
                messagebox.showinfo("Медиаплеер", f"Воспроизведение: {os.path.basename(filename)}")
        
        tk.Button(main_frame, text="📁 Выбрать файл", command=select_file,
                 bg=self.accent_color, fg='white', relief=tk.FLAT,
                 padx=30, pady=10, font=('Arial', 12)).pack(pady=20)
    
    def open_settings(self):
        window = AppWindow(self, "Настройки", 800, 550)
        content = window.get_content()
        
        # Создание вкладок
        notebook = ttk.Notebook(content)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        style = ttk.Style()
        style.configure("TNotebook", background='#1c1c1e')
        style.configure("TNotebook.Tab", background='#3a3a3a',
                       foreground='white', padding=[10, 5])
        style.map("TNotebook.Tab", background=[("selected", self.accent_color)])
        
        # Вкладка "Система"
        system_tab = tk.Frame(notebook, bg='#1c1c1e')
        notebook.add(system_tab, text="⚙️ Система")
        
        tk.Label(system_tab, text="Информация о системе", bg='#1c1c1e',
                fg='white', font=('Arial', 16, 'bold')).pack(anchor='w', pady=15, padx=20)
        
        info = [
            ("ОС:", "AnonkisOS 2.0"),
            ("Версия:", "Dark Edition"),
            ("Процессор:", "AMD Ryzen 9 7950X"),
            ("Оперативная память:", "32 GB DDR5"),
            ("Видеокарта:", "NVIDIA RTX 4080"),
            ("Накопитель:", "2 TB NVMe SSD"),
            ("Разрешение:", f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}")
        ]
        
        for label, value in info:
            frame = tk.Frame(system_tab, bg='#1c1c1e')
            frame.pack(fill=tk.X, padx=20, pady=5)
            tk.Label(frame, text=label, bg='#1c1c1e', fg='gray',
                    width=20, anchor='w', font=('Arial', 11)).pack(side=tk.LEFT)
            tk.Label(frame, text=value, bg='#1c1c1e', fg='white',
                    anchor='w', font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        
        # Вкладка "Внешний вид"
        appearance_tab = tk.Frame(notebook, bg='#1c1c1e')
        notebook.add(appearance_tab, text="🎨 Внешний вид")
        
        tk.Label(appearance_tab, text="Персонализация", bg='#1c1c1e',
                fg='white', font=('Arial', 16, 'bold')).pack(anchor='w', pady=15, padx=20)
        
        def change_color():
            color = colorchooser.askcolor(self.accent_color)[1]
            if color:
                self.accent_color = color
                self.start_btn.configure(bg=color)
        
        color_frame = tk.Frame(appearance_tab, bg='#1c1c1e')
        color_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(color_frame, text="Цвет акцента:", bg='#1c1c1e',
                fg='white').pack(anchor='w')
        
        tk.Button(color_frame, text="Выбрать цвет", command=change_color,
                 bg=self.accent_color, fg='white', relief=tk.FLAT,
                 padx=20, pady=5).pack(pady=10)
        
        # Вкладка "Активация"
        activation_tab = tk.Frame(notebook, bg='#1c1c1e')
        notebook.add(activation_tab, text="🔓 Активация")
        
        status_frame = tk.Frame(activation_tab, bg='#1c1c1e')
        status_frame.pack(expand=True)
        
        tk.Label(status_frame, text="✓", bg='#1c1c1e',
                fg='#00ff00', font=('Segoe UI', 48)).pack(pady=20)
        
        tk.Label(status_frame, text="Система активирована", bg='#1c1c1e',
                fg='#00ff00', font=('Arial', 14, 'bold')).pack()
        
        tk.Label(status_frame, text="Лицензия: AnonkisOS Dark Edition", 
                bg='#1c1c1e', fg='gray', font=('Arial', 11)).pack(pady=10)
    
    def show_power_menu(self):
        if messagebox.askyesno("Выключение", "Вы уверены, что хотите выключить систему?"):
            self.shutdown()
    
    def shutdown(self):
        self.root.quit()
        self.root.destroy()
        sys.exit(0)
    
    def update_clock(self):
        current = datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=current)
        self.root.after(1000, self.update_clock)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = AnonkisOS()
        app.run()
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")