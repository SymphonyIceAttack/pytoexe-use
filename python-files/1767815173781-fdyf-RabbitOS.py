import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import os
import webbrowser
import random

class RabbitOS:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🐰 RabbitOS")
        
        # Получаем размеры экрана
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Устанавливаем размеры окна в полный экран
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Простой цвет фона вместо сложной графики
        self.root.configure(bg='#0078d4')
        
        # Создаем интерфейс
        self.create_desktop()
        self.create_taskbar()
        
        # Бинды клавиш
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
        
        # Показываем приветствие
        self.show_welcome()
    
    def create_desktop(self):
        """Создаем рабочий стол с иконками"""
        # Фон рабочего стола
        self.desktop = tk.Frame(self.root, bg='#0078d4')
        self.desktop.pack(fill='both', expand=True)
        
        # Заголовок в центре
        title = tk.Label(
            self.desktop,
            text="🐰 RabbitOS",
            font=("Arial", 48, "bold"),
            bg='#0078d4',
            fg='white'
        )
        title.place(relx=0.5, rely=0.2, anchor='center')
        
        # Подзаголовок
        subtitle = tk.Label(
            self.desktop,
            text="Операционная система на Python",
            font=("Arial", 16),
            bg='#0078d4',
            fg='white'
        )
        subtitle.place(relx=0.5, rely=0.28, anchor='center')
        
        # Создаем кнопки приложений
        self.create_app_buttons()
    
    def create_app_buttons(self):
        """Создает кнопки приложений на рабочем столе"""
        apps = [
            ("📁", "Файлы", self.open_file_manager),
            ("🌐", "Браузер", self.open_browser),
            ("📝", "Текстовый редактор", self.open_text_editor),
            ("🧮", "Калькулятор", self.open_calculator),
            ("🎨", "Paint", self.open_paint),
            ("🛒", "Магазин", self.open_app_store),
            ("🎮", "Игры", self.open_games_menu),
            ("⚙️", "Настройки", self.open_settings)
        ]
        
        # Фрейм для кнопок
        frame = tk.Frame(self.desktop, bg='#0078d4')
        frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Создаем сетку 2x4
        for i, (icon, name, command) in enumerate(apps):
            row = i // 4
            col = i % 4
            
            # Создаем красивую кнопку
            btn = tk.Button(
                frame,
                text=f"{icon}\n{name}",
                font=("Arial", 11),
                bg='white',
                fg='#0078d4',
                relief='raised',
                bd=3,
                width=15,
                height=4,
                command=command
            )
            btn.grid(row=row, column=col, padx=10, pady=10)
    
    def create_taskbar(self):
        """Создает панель задач"""
        self.taskbar = tk.Frame(self.root, bg='#00000080', height=48)
        self.taskbar.pack(side='bottom', fill='x')
        
        # Кнопка Пуск
        start_btn = tk.Button(
            self.taskbar,
            text=" 🐰 Пуск",
            font=("Arial", 11, "bold"),
            bg='#0078d4',
            fg='white',
            relief='flat',
            command=self.show_start_menu
        )
        start_btn.pack(side='left', padx=10, pady=5)
        
        # Быстрые приложения
        quick_frame = tk.Frame(self.taskbar, bg='transparent')
        quick_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        quick_apps = ["📁", "🌐", "📝", "🎨"]
        for icon in quick_apps:
            btn = tk.Button(
                quick_frame,
                text=icon,
                font=("Arial", 14),
                bg='#00000040',
                fg='white',
                relief='flat',
                width=3
            )
            btn.pack(side='left', padx=2)
        
        # Часы
        from datetime import datetime
        
        self.clock_label = tk.Label(
            self.taskbar,
            font=("Arial", 11),
            bg='transparent',
            fg='white'
        )
        self.clock_label.pack(side='right', padx=10, pady=5)
        
        # Обновляем время
        def update_time():
            now = datetime.now().strftime("%H:%M:%S")
            self.clock_label.config(text=now)
            self.root.after(1000, update_time)
        
        update_time()
    
    def show_welcome(self):
        """Показывает приветственное сообщение"""
        welcome = tk.Toplevel(self.root)
        welcome.title("Добро пожаловать!")
        welcome.geometry("400x300")
        welcome.configure(bg='white')
        
        # Центрируем окно
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 300) // 2
        welcome.geometry(f"+{x}+{y}")
        
        # Содержимое
        tk.Label(
            welcome,
            text="🐰",
            font=("Arial", 40),
            bg='white'
        ).pack(pady=20)
        
        tk.Label(
            welcome,
            text="Добро пожаловать в RabbitOS!",
            font=("Arial", 16, "bold"),
            bg='white'
        ).pack()
        
        tk.Label(
            welcome,
            text="Нажмите 'Пуск' для открытия меню приложений",
            font=("Arial", 10),
            bg='white',
            fg='gray'
        ).pack(pady=20)
        
        tk.Button(
            welcome,
            text="Начать",
            font=("Arial", 12),
            bg='#0078d4',
            fg='white',
            command=welcome.destroy
        ).pack(pady=20)
    
    def show_start_menu(self):
        """Показывает меню Пуск"""
        menu = tk.Toplevel(self.root)
        menu.title("Меню")
        menu.geometry("300x400")
        menu.configure(bg='#1c1c1c')
        menu.overrideredirect(True)
        
        # Позиционируем
        x = self.root.winfo_rootx() + 10
        y = self.root.winfo_rooty() + self.root.winfo_height() - 448
        menu.geometry(f"+{x}+{y}")
        
        # Заголовок
        header = tk.Frame(menu, bg='#0078d4', height=60)
        header.pack(fill='x')
        
        tk.Label(
            header,
            text="🐰 RabbitOS",
            font=("Arial", 16, "bold"),
            bg='#0078d4',
            fg='white'
        ).pack(pady=15)
        
        # Элементы меню
        menu_items = [
            ("📁", "Файловый менеджер", self.open_file_manager),
            ("🌐", "Браузер", self.open_browser),
            ("📝", "Текстовый редактор", self.open_text_editor),
            ("🧮", "Калькулятор", self.open_calculator),
            ("🎨", "Paint", self.open_paint),
            ("🛒", "Магазин приложений", self.open_app_store),
            ("🎮", "Игры", self.open_games_menu),
            ("⚙️", "Настройки", self.open_settings),
            ("🚪", "Выход", self.root.quit)
        ]
        
        for icon, name, command in menu_items:
            btn = tk.Button(
                menu,
                text=f"   {icon} {name}",
                font=("Arial", 11),
                bg='#1c1c1c',
                fg='white',
                relief='flat',
                anchor='w',
                command=lambda c=command: (menu.destroy(), c())
            )
            btn.pack(fill='x', pady=2, padx=10)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#0078d4'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#1c1c1c'))
        
        # Закрываем при клике вне меню
        menu.bind("<FocusOut>", lambda e: menu.destroy())
    
    def create_window(self, title, width=800, height=600):
        """Создает окно приложения"""
        window = tk.Toplevel(self.root)
        window.title(f"🐰 {title}")
        
        # Центрируем
        x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        window.configure(bg='white')
        
        # Заголовок окна
        title_bar = tk.Frame(window, bg='#0078d4', height=35)
        title_bar.pack(fill='x')
        
        tk.Label(
            title_bar,
            text=title,
            font=("Arial", 10, "bold"),
            bg='#0078d4',
            fg='white'
        ).pack(side='left', padx=10)
        
        close_btn = tk.Button(
            title_bar,
            text=" × ",
            font=("Arial", 14),
            bg='#0078d4',
            fg='white',
            relief='flat',
            command=window.destroy
        )
        close_btn.pack(side='right', padx=5)
        close_btn.bind("<Enter>", lambda e: close_btn.config(bg='red'))
        close_btn.bind("<Leave>", lambda e: close_btn.config(bg='#0078d4'))
        
        return window
    
    # ========== ПРИЛОЖЕНИЯ ==========
    
    def open_file_manager(self):
        """Открывает файловый менеджер"""
        window = self.create_window("Файловый менеджер", 800, 500)
        
        # Панель инструментов
        toolbar = tk.Frame(window, bg='#f0f0f0')
        toolbar.pack(fill='x', padx=5, pady=5)
        
        buttons = ["📁 Новая папка", "📄 Новый файл", "💾 Сохранить", "🗑️ Удалить"]
        for text in buttons:
            btn = tk.Button(toolbar, text=text, font=("Arial", 9), bg='white', relief='groove')
            btn.pack(side='left', padx=5)
        
        # Список файлов
        listbox = tk.Listbox(window, font=("Arial", 11))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Показываем файлы
        for item in os.listdir('.'):
            listbox.insert('end', item)
    
    def open_browser(self):
        """Открывает браузер"""
        window = self.create_window("Браузер", 900, 600)
        
        # Панель навигации
        nav_frame = tk.Frame(window, bg='#f0f0f0')
        nav_frame.pack(fill='x', padx=10, pady=10)
        
        url_entry = tk.Entry(nav_frame, font=("Arial", 11), width=50)
        url_entry.pack(side='left', fill='x', expand=True, padx=5)
        url_entry.insert(0, "https://www.google.com")
        
        def navigate():
            url = url_entry.get()
            webbrowser.open(url)
        
        go_btn = tk.Button(nav_frame, text="Перейти", command=navigate)
        go_btn.pack(side='left', padx=5)
        
        # Область просмотра
        browser_text = scrolledtext.ScrolledText(window, font=("Arial", 11))
        browser_text.pack(fill='both', expand=True, padx=10, pady=10)
        
        browser_text.insert('1.0', 
            "🌐 Rabbit Browser\n\n"
            "Введите URL выше и нажмите 'Перейти'\n\n"
            "Примеры:\n"
            "• google.com\n"
            "• youtube.com\n"
            "• github.com")
    
    def open_text_editor(self):
        """Открывает текстовый редактор"""
        window = self.create_window("Текстовый редактор", 700, 500)
        
        # Текстовая область
        text_area = scrolledtext.ScrolledText(window, font=("Consolas", 12))
        text_area.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Меню
        menubar = tk.Menu(window)
        window.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        def open_file():
            file_path = filedialog.askopenfilename()
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text_area.delete('1.0', 'end')
                        text_area.insert('1.0', f.read())
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")
        
        def save_file():
            file_path = filedialog.asksaveasfilename(defaultextension=".txt")
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text_area.get('1.0', 'end-1c'))
                    messagebox.showinfo("Успех", "Файл сохранен!")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
        
        file_menu.add_command(label="Открыть", command=open_file)
        file_menu.add_command(label="Сохранить", command=save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=window.destroy)
        
        # Пример текста
        text_area.insert('1.0', "Добро пожаловать в текстовый редактор!\n\n")
    
    def open_calculator(self):
        """Открывает калькулятор"""
        window = self.create_window("Калькулятор", 300, 400)
        
        # Дисплей
        display_var = tk.StringVar(value="0")
        display = tk.Entry(window, textvariable=display_var, 
                          font=("Arial", 24), justify='right',
                          bd=10, relief='sunken')
        display.pack(fill='x', padx=10, pady=10)
        
        # Кнопки
        buttons_frame = tk.Frame(window)
        buttons_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        buttons = [
            ['7', '8', '9', '/'],
            ['4', '5', '6', '*'],
            ['1', '2', '3', '-'],
            ['0', '.', '=', '+'],
            ['C']
        ]
        
        def button_click(value):
            current = display_var.get()
            
            if value == '=':
                try:
                    result = eval(current)
                    display_var.set(str(result))
                except:
                    display_var.set("Ошибка")
            elif value == 'C':
                display_var.set("0")
            else:
                if current == "0" or current == "Ошибка":
                    display_var.set(value)
                else:
                    display_var.set(current + value)
        
        for i, row in enumerate(buttons):
            for j, value in enumerate(row):
                btn = tk.Button(buttons_frame, text=value, font=("Arial", 14),
                              command=lambda v=value: button_click(v))
                btn.grid(row=i, column=j, sticky='nsew', padx=2, pady=2)
                buttons_frame.grid_columnconfigure(j, weight=1)
            buttons_frame.grid_rowconfigure(i, weight=1)
    
    def open_paint(self):
        """Открывает Paint"""
        window = self.create_window("Paint", 800, 600)
        
        # Холст
        canvas = tk.Canvas(window, bg='white')
        canvas.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Инструменты
        toolbar = tk.Frame(window, bg='#f0f0f0')
        toolbar.pack(fill='x', padx=5, pady=5)
        
        tools = ["✏️", "⬜", "⬤", "📏", "🧽", "🌈"]
        for tool in tools:
            btn = tk.Button(toolbar, text=tool, font=("Arial", 14))
            btn.pack(side='left', padx=2)
        
        # Рисуем пример
        canvas.create_rectangle(100, 100, 300, 300, fill='blue', outline='black')
        canvas.create_oval(400, 150, 600, 350, fill='red', outline='black')
        canvas.create_text(350, 450, text="🎨 Paint", font=("Arial", 20))
    
    def open_app_store(self):
        """Открывает магазин приложений"""
        window = self.create_window("Магазин приложений", 800, 600)
        
        # Заголовок
        tk.Label(window, text="🛒 Магазин RabbitOS", 
                font=("Arial", 24, "bold")).pack(pady=20)
        
        # Приложения
        apps = [
            ("📸", "Фоторедактор", "Редактирование фото"),
            ("📊", "Офис", "Офисный пакет"),
            ("🎬", "Видеоплеер", "Просмотр видео"),
            ("📒", "Заметки", "Заметки и списки"),
            ("📧", "Почта", "Электронная почта"),
            ("🗺️", "Карты", "Карты и навигация")
        ]
        
        frame = tk.Frame(window)
        frame.pack(pady=20)
        
        for i, (icon, name, desc) in enumerate(apps):
            row = i // 3
            col = i % 3
            
            app_frame = tk.Frame(frame, relief='groove', bd=2)
            app_frame.grid(row=row, column=col, padx=10, pady=10)
            
            tk.Label(app_frame, text=icon, font=("Arial", 30)).pack(pady=10)
            tk.Label(app_frame, text=name, font=("Arial", 12, "bold")).pack()
            tk.Label(app_frame, text=desc, font=("Arial", 9)).pack(pady=5)
            
            tk.Button(app_frame, text="Установить", bg='#0078d4', fg='white').pack(pady=10)
    
    def open_games_menu(self):
        """Открывает меню игр"""
        window = self.create_window("Игры", 700, 500)
        
        # Заголовок
        tk.Label(window, text="🎮 Игровой центр", 
                font=("Arial", 24, "bold")).pack(pady=20)
        
        # Игры
        games = [
            ("🐍", "Змейка", "Классическая змейка"),
            ("⬜", "Тетрис", "Собирайте фигуры"),
            ("🏓", "Пинг-понг", "Аркадная игра"),
            ("🏎️", "Гонки", "Гоночный симулятор"),
            ("🧩", "Пазлы", "Собери картинку"),
            ("🔴", "Арканоид", "Разбей все блоки")
        ]
        
        frame = tk.Frame(window)
        frame.pack(pady=20)
        
        for i, (icon, name, desc) in enumerate(games):
            row = i // 3
            col = i % 3
            
            game_frame = tk.Frame(frame, relief='groove', bd=2)
            game_frame.grid(row=row, column=col, padx=10, pady=10)
            
            tk.Label(game_frame, text=icon, font=("Arial", 30)).pack(pady=10)
            tk.Label(game_frame, text=name, font=("Arial", 12, "bold")).pack()
            tk.Label(game_frame, text=desc, font=("Arial", 9)).pack(pady=5)
            
            tk.Button(game_frame, text="Играть", bg='green', fg='white').pack(pady=10)
    
    def open_settings(self):
        """Открывает настройки"""
        window = self.create_window("Настройки", 500, 400)
        
        # Заголовок
        tk.Label(window, text="⚙️ Настройки системы", 
                font=("Arial", 20, "bold")).pack(pady=20)
        
        # Темы
        theme_frame = tk.LabelFrame(window, text="Тема оформления", padx=10, pady=10)
        theme_frame.pack(fill='x', padx=20, pady=10)
        
        themes = ["🔵 Синяя", "🌙 Темная", "☀️ Светлая", "🟢 Зеленая"]
        for theme in themes:
            tk.Radiobutton(theme_frame, text=theme).pack(anchor='w', pady=5)
        
        # О системе
        info_frame = tk.LabelFrame(window, text="О системе", padx=10, pady=10)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(info_frame, text="🐰 RabbitOS v1.0").pack()
        tk.Label(info_frame, text="Создано на Python + Tkinter").pack()
    
    def toggle_fullscreen(self):
        """Переключает полноэкранный режим"""
        if self.root.attributes('-fullscreen'):
            self.root.attributes('-fullscreen', False)
        else:
            self.root.attributes('-fullscreen', True)
    
    def run(self):
        """Запускает систему"""
        print("🐰 RabbitOS запущен!")
        print("F11 - Полноэкранный режим")
        print("Esc - Выход")
        self.root.mainloop()

# Запуск системы
if __name__ == "__main__":
    # Проверяем, работает ли tkinter
    try:
        # Простая проверка
        test = tk.Tk()
        test.destroy()
        
        # Запускаем систему
        print("Запуск RabbitOS...")
        os_system = RabbitOS()
        os_system.run()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        print("\nВозможные решения:")
        print("1. Убедитесь, что Python установлен корректно")
        print("2. Попробуйте запустить в командной строке: python -m tkinter")
        print("3. Если tkinter не работает, переустановите Python")
        input("Нажмите Enter для выхода...")