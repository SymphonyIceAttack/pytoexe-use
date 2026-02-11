import tkinter as tk
from tkinter import ttk, messagebox
from database import BankDatabase
from datetime import datetime

class ONHAFBankGUI:
    """Графический интерфейс банковской системы ONHAF"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("ONHAF Bank System v2.0")
        self.root.geometry("1000x700")
        
        # Цветовая схема
        self.colors = {
            'primary': '#1a237e',      # Темно-синий
            'secondary': '#283593',    # Синий
            'accent': '#5c6bc0',       # Светло-синий
            'success': '#2e7d32',      # Зеленый
            'error': '#c62828',        # Красный
            'warning': '#f9a825',      # Желтый
            'background': '#f5f5f5',   # Светло-серый
            'card': '#ffffff'          # Белый
        }
        
        # Шрифты
        self.fonts = {
            'title': ('Arial', 16, 'bold'),
            'header': ('Arial', 14, 'bold'),
            'normal': ('Arial', 10),
            'mono': ('Courier New', 10)
        }
        
        # Инициализация базы данных
        self.db = BankDatabase()
        self.current_user = None
        
        # Настройка фона окна
        self.root.configure(bg=self.colors['background'])
        
        # Запуск с экрана логина
        self.show_login_screen()
    
    def clear_window(self):
        """Очистка окна от всех виджетов"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def create_title(self, text, color=None):
        """Создание заголовка"""
        title_frame = tk.Frame(self.root, bg=self.colors['background'])
        title_frame.pack(pady=20)
        
        color = color or self.colors['primary']
        title = tk.Label(
            title_frame,
            text=text,
            font=self.fonts['title'],
            fg=color,
            bg=self.colors['background']
        )
        title.pack()
        
        return title_frame
    
    def show_login_screen(self):
        """Отображение экрана входа"""
        self.clear_window()
        
        # Заголовок
        self.create_title("ONHAF BANK TERMINAL", self.colors['primary'])
        
        # Фрейм для ввода данных
        login_frame = tk.Frame(self.root, bg=self.colors['background'])
        login_frame.pack(pady=50)
        
        # Поле для логина
        tk.Label(
            login_frame,
            text="Логин:",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).grid(row=0, column=0, pady=10, sticky='e')
        
        self.username_entry = tk.Entry(
            login_frame,
            width=30,
            font=self.fonts['normal']
        )
        self.username_entry.grid(row=0, column=1, pady=10, padx=10)
        self.username_entry.focus()
        self.username_entry.bind('<Return>', lambda e: self.password_entry.focus())
        
        # Поле для пароля
        tk.Label(
            login_frame,
            text="Пароль:",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).grid(row=1, column=0, pady=10, sticky='e')
        
        self.password_entry = tk.Entry(
            login_frame,
            width=30,
            show="*",
            font=self.fonts['normal']
        )
        self.password_entry.grid(row=1, column=1, pady=10, padx=10)
        self.password_entry.bind('<Return>', lambda e: self.login())
        
        # Кнопки
        button_frame = tk.Frame(self.root, bg=self.colors['background'])
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Войти в систему",
            command=self.login,
            bg=self.colors['primary'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="Регистрация",
            command=self.show_registration_screen,
            bg=self.colors['accent'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5,
            relief='flat'
        ).pack(side='left', padx=10)
        
        # Информация о демо-аккаунтах
        info_frame = tk.Frame(self.root, bg=self.colors['background'])
        info_frame.pack(pady=20)
        
        tk.Label(
            info_frame,
            text="Демо-аккаунты: admin / admin123",
            font=self.fonts['normal'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack()
    
    def login(self):
        """Обработка входа в систему"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Введите логин и пароль")
            return
        
        user = self.db.authenticate_user(username, password)
        
        if user:
            self.current_user = user
            messagebox.showinfo("Успешно", f"Добро пожаловать, {user['full_name']}!")
            self.show_main_dashboard()
        else:
            messagebox.showerror("Ошибка", "Неверный логин или пароль")
    
    def show_registration_screen(self):
        """Отображение экрана регистрации"""
        self.clear_window()
        
        self.create_title("Регистрация в ONHAF BANK", self.colors['primary'])
        
        # Фрейм для формы
        reg_frame = tk.Frame(self.root, bg=self.colors['background'])
        reg_frame.pack(pady=20)
        
        # Поля для ввода
        fields = [
            ("Имя пользователя:", "username", False),
            ("Пароль:", "password", True),
            ("Подтвердите пароль:", "confirm_password", True),
            ("Полное имя:", "full_name", False),
            ("Email:", "email", False),
            ("Телефон:", "phone", False)
        ]
        
        self.reg_entries = {}
        
        for i, (label, field, is_password) in enumerate(fields):
            tk.Label(
                reg_frame,
                text=label,
                font=self.fonts['normal'],
                fg=self.colors['secondary'],
                bg=self.colors['background']
            ).grid(row=i, column=0, pady=5, sticky='e')
            
            entry = tk.Entry(
                reg_frame,
                width=30,
                show="*" if is_password else "",
                font=self.fonts['normal']
            )
            entry.grid(row=i, column=1, pady=5, padx=10)
            self.reg_entries[field] = entry
        
        # Кнопки
        button_frame = tk.Frame(self.root, bg=self.colors['background'])
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Зарегистрироваться",
            command=self.register_user,
            bg=self.colors['primary'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="Назад",
            command=self.show_login_screen,
            bg=self.colors['accent'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5
        ).pack(side='left', padx=10)
    
    def register_user(self):
        """Регистрация нового пользователя"""
        # Проверка паролей
        if self.reg_entries['password'].get() != self.reg_entries['confirm_password'].get():
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        
        user_data = {
            'username': self.reg_entries['username'].get(),
            'password': self.reg_entries['password'].get(),
            'full_name': self.reg_entries['full_name'].get(),
            'email': self.reg_entries['email'].get(),
            'phone': self.reg_entries['phone'].get()
        }
        
        if not user_data['username']:
            messagebox.showerror("Ошибка", "Введите имя пользователя")
            return
        
        user_id = self.db.create_user(user_data)
        
        if user_id:
            messagebox.showinfo("Успешно", 
                f"Пользователь {user_data['username']} зарегистрирован!\n"
                f"Ваш начальный баланс: $1000.00")
            self.show_login_screen()
        else:
            messagebox.showerror("Ошибка", "Пользователь с таким логином уже существует")
    
    def show_main_dashboard(self):
        """Отображение главной панели"""
        self.clear_window()
        
        # Верхняя панель
        top_frame = tk.Frame(self.root, bg=self.colors['primary'])
        top_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            top_frame,
            text=f"ONHAF BANK | Пользователь: {self.current_user['full_name']}",
            bg=self.colors['primary'],
            fg='white',
            font=self.fonts['header']
        ).pack(side='left', padx=20, pady=10)
        
        tk.Button(
            top_frame,
            text="Выход",
            command=self.logout,
            bg='white',
            fg=self.colors['error'],
            font=self.fonts['normal']
        ).pack(side='right', padx=20, pady=10)
        
        # Основной контент
        main_frame = tk.Frame(self.root, bg=self.colors['background'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Создание вкладок
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Создание вкладок
        self.create_dashboard_tab()
        self.create_accounts_tab()
        self.create_cards_tab()
        self.create_transfer_tab()
        self.create_history_tab()
        
        if self.current_user['access_level'] >= 2:
            self.create_admin_tab()
    
    def create_dashboard_tab(self):
        """Создание вкладки дашборда"""
        tab = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(tab, text="Главная")
        
        # Приветствие
        tk.Label(
            tab,
            text=f"Добро пожаловать в ONHAF Bank, {self.current_user['full_name']}!",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=20)
        
        # Статистика
        stats_frame = tk.Frame(tab, bg=self.colors['background'])
        stats_frame.pack(pady=20)
        
        # Получение данных
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        total_balance = sum(acc['balance'] for acc in accounts)
        cards = self.db.get_user_cards(self.current_user['user_id'])
        
        # Отображение статистики
        stats = [
            ("Общий баланс:", f"${total_balance:,.2f}"),
            ("Количество счетов:", str(len(accounts))),
            ("Количество карт:", str(len(cards))),
            ("Статус:", "Активен"),
            ("Дата:", datetime.now().strftime("%d.%m.%Y"))
        ]
        
        for i, (label, value) in enumerate(stats):
            tk.Label(
                stats_frame,
                text=label,
                font=self.fonts['normal'],
                fg=self.colors['secondary'],
                bg=self.colors['background']
            ).grid(row=i, column=0, pady=5, sticky='e')
            
            tk.Label(
                stats_frame,
                text=value,
                font=self.fonts['normal'],
                fg=self.colors['primary'],
                bg=self.colors['background']
            ).grid(row=i, column=1, pady=5, padx=10, sticky='w')
        
        # Быстрые действия
        actions_frame = tk.Frame(tab, bg=self.colors['background'])
        actions_frame.pack(pady=30)
        
        tk.Label(
            actions_frame,
            text="Быстрые действия:",
            font=self.fonts['header'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack()
        
        buttons = [
            ("Создать новый счет", self.create_new_account),
            ("Заказать карту", self.order_new_card),
            ("Выполнить перевод", lambda: self.notebook.select(3)),
            ("Посмотреть историю", lambda: self.notebook.select(4))
        ]
        
        for text, command in buttons:
            tk.Button(
                actions_frame,
                text=text,
                command=command,
                bg=self.colors['primary'],
                fg='white',
                font=self.fonts['normal'],
                padx=20,
                pady=5
            ).pack(pady=5)
    
    def create_accounts_tab(self):
        """Создание вкладки счетов"""
        tab = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(tab, text="Мои счета")
        
        # Заголовок
        tk.Label(
            tab,
            text="Мои банковские счета",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=10)
        
        # Получение счетов
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        
        if not accounts:
            tk.Label(
                tab,
                text="У вас пока нет счетов",
                font=self.fonts['normal'],
                fg=self.colors['secondary'],
                bg=self.colors['background']
            ).pack()
        else:
            # Таблица счетов
            tree_frame = tk.Frame(tab, bg=self.colors['background'])
            tree_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            # Создаем Treeview
            columns = ("Номер счета", "Тип", "Баланс", "Валюта", "Дата создания")
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
            
            # Настройка колонок
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=150)
            
            # Добавление данных
            for acc in accounts:
                tree.insert("", "end", values=(
                    acc['account_number'],
                    acc['account_type'],
                    f"${acc['balance']:,.2f}",
                    acc['currency'],
                    acc['created_date'][:10] if acc['created_date'] else ""
                ))
            
            # Полоса прокрутки
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
        
        # Кнопка создания счета
        tk.Button(
            tab,
            text="+ Создать новый счет",
            command=self.create_new_account,
            bg=self.colors['primary'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5
        ).pack(pady=20)
    
    def create_cards_tab(self):
        """Создание вкладки карт"""
        tab = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(tab, text="Мои карты")
        
        # Заголовок
        tk.Label(
            tab,
            text="Мои банковские карты",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=10)
        
        # Получение карт
        cards = self.db.get_user_cards(self.current_user['user_id'])
        
        if not cards:
            tk.Label(
                tab,
                text="У вас пока нет карт",
                font=self.fonts['normal'],
                fg=self.colors['secondary'],
                bg=self.colors['background']
            ).pack()
        else:
            # Фрейм для карт
            cards_frame = tk.Frame(tab, bg=self.colors['background'])
            cards_frame.pack(fill='both', expand=True, padx=20, pady=10)
            
            # Отображение карт
            for i, card in enumerate(cards):
                card_frame = tk.Frame(
                    cards_frame,
                    bg=self.colors['card'],
                    relief='solid',
                    bd=1
                )
                card_frame.pack(pady=10, fill='x', padx=20)
                
                # Заголовок карты
                tk.Label(
                    card_frame,
                    text=f"Карта {card.get('card_type', 'VISA')}",
                    font=self.fonts['header'],
                    fg=self.colors['primary'],
                    bg=self.colors['card']
                ).pack(pady=(10, 5))
                
                # Номер карты
                display_num = card.get('display_number', card.get('card_number', ''))
                tk.Label(
                    card_frame,
                    text=display_num,
                    font=('Courier New', 14, 'bold'),
                    fg=self.colors['secondary'],
                    bg=self.colors['card']
                ).pack(pady=5)
                
                # Держатель и срок
                info_frame = tk.Frame(card_frame, bg=self.colors['card'])
                info_frame.pack(pady=5)
                
                tk.Label(
                    info_frame,
                    text=f"Держатель: {card.get('card_holder', '')}",
                    font=self.fonts['normal'],
                    bg=self.colors['card']
                ).pack(side='left', padx=10)
                
                tk.Label(
                    info_frame,
                    text=f"Срок: {card.get('expiry_date', '')}",
                    font=self.fonts['normal'],
                    bg=self.colors['card']
                ).pack(side='left', padx=10)
                
                # Счет
                tk.Label(
                    card_frame,
                    text=f"Привязана к счету: {card.get('account_number', '')}",
                    font=self.fonts['normal'],
                    bg=self.colors['card']
                ).pack(pady=(0, 10))
        
        # Кнопка заказа карты
        tk.Button(
            tab,
            text="+ Заказать новую карту",
            command=self.order_new_card,
            bg=self.colors['primary'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5
        ).pack(pady=20)
    
    def create_transfer_tab(self):
        """Создание вкладки переводов"""
        tab = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(tab, text="Переводы")
        
        # Заголовок
        tk.Label(
            tab,
            text="Межбанковский перевод",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=10)
        
        # Фрейм для формы
        form_frame = tk.Frame(tab, bg=self.colors['background'])
        form_frame.pack(pady=20)
        
        # Выбор счета отправителя
        tk.Label(
            form_frame,
            text="С моего счета:",
            font=self.fonts['normal'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).grid(row=0, column=0, pady=10, sticky='e')
        
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        account_numbers = [acc['account_number'] for acc in accounts]
        
        self.from_account_var = tk.StringVar()
        self.from_account_combo = ttk.Combobox(
            form_frame,
            textvariable=self.from_account_var,
            values=account_numbers,
            width=30
        )
        self.from_account_combo.grid(row=0, column=1, pady=10, padx=10)
        if account_numbers:
            self.from_account_combo.current(0)
        
        # Счет получателя
        tk.Label(
            form_frame,
            text="Счет получателя:",
            font=self.fonts['normal'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).grid(row=1, column=0, pady=10, sticky='e')
        
        self.to_account_entry = tk.Entry(
            form_frame,
            width=30,
            font=self.fonts['normal']
        )
        self.to_account_entry.grid(row=1, column=1, pady=10, padx=10)
        
        # Сумма
        tk.Label(
            form_frame,
            text="Сумма ($):",
            font=self.fonts['normal'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).grid(row=2, column=0, pady=10, sticky='e')
        
        self.amount_entry = tk.Entry(
            form_frame,
            width=20,
            font=self.fonts['normal']
        )
        self.amount_entry.grid(row=2, column=1, pady=10, padx=10, sticky='w')
        
        # Описание
        tk.Label(
            form_frame,
            text="Описание:",
            font=self.fonts['normal'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).grid(row=3, column=0, pady=10, sticky='e')
        
        self.desc_entry = tk.Entry(
            form_frame,
            width=30,
            font=self.fonts['normal']
        )
        self.desc_entry.grid(row=3, column=1, pady=10, padx=10)
        
        # Кнопка перевода
        tk.Button(
            tab,
            text="Выполнить перевод",
            command=self.make_transfer,
            bg=self.colors['primary'],
            fg='white',
            font=self.fonts['normal'],
            padx=20,
            pady=5
        ).pack(pady=30)
    
    def create_history_tab(self):
        """Создание вкладки истории"""
        tab = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(tab, text="История")
        
        # Заголовок
        tk.Label(
            tab,
            text="История операций",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=10)
        
        # Выбор счета
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        
        if not accounts:
            tk.Label(
                tab,
                text="У вас пока нет счетов",
                font=self.fonts['normal'],
                fg=self.colors['secondary'],
                bg=self.colors['background']
            ).pack()
            return
        
        selection_frame = tk.Frame(tab, bg=self.colors['background'])
        selection_frame.pack(pady=10)
        
        tk.Label(
            selection_frame,
            text="Выберите счет:",
            font=self.fonts['normal'],
            fg=self.colors['secondary'],
            bg=self.colors['background']
        ).pack(side='left')
        
        self.history_account_var = tk.StringVar()
        self.history_account_combo = ttk.Combobox(
            selection_frame,
            textvariable=self.history_account_var,
            values=[acc['account_number'] for acc in accounts],
            width=30
        )
        self.history_account_combo.pack(side='left', padx=10)
        self.history_account_combo.current(0)
        
        # Кнопка обновления
        tk.Button(
            selection_frame,
            text="Обновить",
            command=self.load_history,
            bg=self.colors['accent'],
            fg='white',
            font=self.fonts['normal']
        ).pack(side='left', padx=10)
        
        # Таблица истории
        tree_frame = tk.Frame(tab, bg=self.colors['background'])
        tree_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        columns = ("Дата", "Тип", "Сумма", "Счет отправителя", "Счет получателя", "Описание")
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=120)
        
        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Загрузка истории
        self.load_history()
    
    def create_admin_tab(self):
        """Создание вкладки администратора"""
        tab = tk.Frame(self.notebook, bg=self.colors['background'])
        self.notebook.add(tab, text="Администрирование")
        
        # Заголовок
        tk.Label(
            tab,
            text="Панель администратора",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=10)
        
        # Кнопки
        button_frame = tk.Frame(tab, bg=self.colors['background'])
        button_frame.pack(pady=20)
        
        buttons = [
            ("Системная статистика", self.show_system_stats),
            ("Резервное копирование", self.backup_database)
        ]
        
        for text, command in buttons:
            tk.Button(
                button_frame,
                text=text,
                command=command,
                bg=self.colors['primary'],
                fg='white',
                font=self.fonts['normal'],
                padx=20,
                pady=5
            ).pack(pady=5)
    
    def create_new_account(self):
        """Создание нового счета"""
        account_number = self.db.create_account(self.current_user['user_id'])
        
        if account_number:
            messagebox.showinfo("Успешно", 
                f"Новый счет создан!\n"
                f"Номер счета: {account_number}\n"
                f"Начальный баланс: $1000.00")
            self.notebook.select(1)  # Переход на вкладку счетов
        else:
            messagebox.showerror("Ошибка", "Не удалось создать счет")
    
    def order_new_card(self):
        """Заказ новой карты"""
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        
        if not accounts:
            messagebox.showerror("Ошибка", "У вас нет счетов для привязки карты")
            return
        
        # Диалоговое окно
        dialog = tk.Toplevel(self.root)
        dialog.title("Заказ новой карты")
        dialog.geometry("400x300")
        dialog.configure(bg=self.colors['background'])
        
        # Заголовок
        tk.Label(
            dialog,
            text="Заказ банковской карты",
            font=self.fonts['header'],
            fg=self.colors['primary'],
            bg=self.colors['background']
        ).pack(pady=10)
        
        # Выбор счета
        tk.Label(
            dialog,
            text="Привязать к счету:",
            font=self.fonts['normal'],
            bg=self.colors['background']
        ).pack()
        
        account_var = tk.StringVar()
        account_combo = ttk.Combobox(
            dialog,
            textvariable=account_var,
            values=[acc['account_number'] for acc in accounts],
            width=30
        )
        account_combo.pack(pady=5)
        account_combo.current(0)
        
        # Выбор типа карты
        tk.Label(
            dialog,
            text="Тип карты:",
            font=self.fonts['normal'],
            bg=self.colors['background']
        ).pack()
        
        card_type_var = tk.StringVar(value="VISA")
        card_type_combo = ttk.Combobox(
            dialog,
            textvariable=card_type_var,
            values=["VISA", "MASTERCARD"],
            width=20
        )
        card_type_combo.pack(pady=5)
        
        # Ввод PIN
        tk.Label(
            dialog,
            text="PIN-код (4 цифры):",
            font=self.fonts['normal'],
            bg=self.colors['background']
        ).pack()
        
        pin_entry = tk.Entry(dialog, show="*", width=10)
        pin_entry.pack(pady=5)
        pin_entry.insert(0, "0000")
        
        def create_card():
            """Создание карты"""
            account_number = account_var.get()
            pin = pin_entry.get()
            
            if not account_number:
                messagebox.showerror("Ошибка", "Выберите счет")
                return
            
            if not pin.isdigit() or len(pin) != 4:
                messagebox.showerror("Ошибка", "PIN должен состоять из 4 цифр")
                return
            
            # Находим account_id
            account_id = None
            for acc in accounts:
                if acc['account_number'] == account_number:
                    account_id = acc['account_id']
                    break
            
            if not account_id:
                messagebox.showerror("Ошибка", "Счет не найден")
                return
            
            # Создаем карту
            card_info = self.db.create_card(
                account_id,
                self.current_user['full_name'],
                pin,
                card_type_var.get()
            )
            
            if card_info:
                messagebox.showinfo("Успешно",
                    f"Карта создана успешно!\n\n"
                    f"Номер карты: {card_info['card_number']}\n"
                    f"Срок: {card_info['expiry_date']}\n"
                    f"CVV: {card_info['cvv']}\n"
                    f"PIN: {pin}\n\n"
                    f"Сохраните эти данные!")
                
                dialog.destroy()
                self.notebook.select(2)  # Переход на вкладку карт
            else:
                messagebox.showerror("Ошибка", "Не удалось создать карту")
        
        # Кнопки
        button_frame = tk.Frame(dialog, bg=self.colors['background'])
        button_frame.pack(pady=20)
        
        tk.Button(
            button_frame,
            text="Создать карту",
            command=create_card,
            bg=self.colors['primary'],
            fg='white'
        ).pack(side='left', padx=10)
        
        tk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy
        ).pack(side='left', padx=10)
    
    def make_transfer(self):
        """Выполнение перевода"""
        # Получение данных
        from_account = self.from_account_var.get()
        to_account = self.to_account_entry.get().strip()
        amount_str = self.amount_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        # Валидация
        if not all([from_account, to_account, amount_str]):
            messagebox.showerror("Ошибка", "Заполните все поля")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительной")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
            return
        
        # Поиск счета отправителя
        from_acc_info = None
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        for acc in accounts:
            if acc['account_number'] == from_account:
                from_acc_info = acc
                break
        
        if not from_acc_info:
            messagebox.showerror("Ошибка", "Счет отправителя не найден")
            return
        
        # Проверка баланса
        if amount > from_acc_info['balance']:
            messagebox.showerror("Ошибка", "Недостаточно средств")
            return
        
        # Поиск счета получателя
        to_acc_info = self.db.get_account_by_number(to_account)
        if not to_acc_info:
            messagebox.showerror("Ошибка", "Счет получателя не найден")
            return
        
        # Подтверждение
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Перевести ${amount:,.2f} на счет {to_account}?\n"
            f"Получатель: {to_acc_info['full_name']}"
        )
        
        if not confirm:
            return
        
        # Выполнение перевода
        try:
            # Обновление балансов
            self.db.update_balance(from_account, -amount)
            self.db.update_balance(to_account, amount)
            
            # Создание транзакции
            self.db.create_transaction(
                from_acc_info['account_id'],
                to_acc_info['account_id'],
                amount,
                description
            )
            
            messagebox.showinfo("Успешно", "Перевод выполнен!")
            
            # Очистка полей
            self.to_account_entry.delete(0, tk.END)
            self.amount_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка перевода: {e}")
    
    def load_history(self):
        """Загрузка истории операций"""
        # Очистка
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
        
        # Получение счета
        account_number = self.history_account_var.get()
        if not account_number:
            return
        
        # Поиск account_id
        accounts = self.db.get_user_accounts(self.current_user['user_id'])
        account_id = None
        for acc in accounts:
            if acc['account_number'] == account_number:
                account_id = acc['account_id']
                break
        
        if not account_id:
            return
        
        # Получение истории
        transactions = self.db.get_account_transactions(account_id)
        
        # Отображение
        for tx in transactions:
            # Определение типа операции
            if tx['from_account_id'] == account_id:
                tx_type = "Исходящий"
                amount = f"-${tx['amount']:,.2f}"
            else:
                tx_type = "Входящий"
                amount = f"+${tx['amount']:,.2f}"
            
            # Форматирование даты
            date = tx['transaction_date'][:19] if tx['transaction_date'] else ""
            
            self.history_tree.insert("", "end", values=(
                date,
                tx_type,
                amount,
                tx.get('from_account', ''),
                tx.get('to_account', ''),
                tx.get('description', '')
            ))
    
    def show_system_stats(self):
        """Показать системную статистику"""
        messagebox.showinfo("Статистика",
            f"Система ONHAF Bank v2.0\n\n"
            f"Текущий пользователь: {self.current_user['full_name']}\n"
            f"Уровень доступа: {self.current_user['access_level']}\n"
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    def backup_database(self):
        """Резервное копирование БД"""
        import shutil
        import os
        
        if os.path.exists("onhaf_bank.db"):
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2("onhaf_bank.db", backup_name)
            messagebox.showinfo("Успешно", f"Резервная копия создана: {backup_name}")
        else:
            messagebox.showerror("Ошибка", "База данных не найдена")
    
    def logout(self):
        """Выход из системы"""
        confirm = messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?")
        if confirm:
            self.current_user = None
            self.show_login_screen()