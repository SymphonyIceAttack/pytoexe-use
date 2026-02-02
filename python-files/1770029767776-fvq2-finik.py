import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as mb

class FixedFinikApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Финик. Мои деньги. Мои правила.")
        self.root.geometry("600x750")
        self.root.configure(bg='white')
        
        # 📊 Данные
        self.data = {
            'teen_balance': 150,
            'parent_balance': 1000,
            
            'goals': [
                {'name': 'Беспроводные наушники', 'target': 300, 'current': 150, 'id': 1},
                {'name': 'Новые кроссовки', 'target': 250, 'current': 80, 'id': 2},
                {'name': 'Курс по программированию', 'target': 500, 'current': 200, 'id': 3},
                {'name': 'Скейтборд', 'target': 400, 'current': 120, 'id': 4},
                {'name': 'Графический планшет', 'target': 800, 'current': 300, 'id': 5},
            ],
            
            'tasks': [
                {'name': 'Прочитать книгу (300 страниц)', 'reward': 50, 'completed': False, 'id': 1},
                {'name': 'Выучить 30 английских слов', 'reward': 30, 'completed': True, 'id': 2},
                {'name': 'Сделать уборку в комнате', 'reward': 20, 'completed': False, 'id': 3},
                {'name': 'Помочь с покупками', 'reward': 25, 'completed': False, 'id': 4},
            ]
        }
        
        # 🎨 Цвета и шрифты
        self.colors = {
            'bg': '#FFFFFF',
            'card_bg': '#F8F9FA',
            'light': "#90EE90",
            'secondary': '#7C3AED',
            'primary': "#50C878", 
            'success': '#059669' ,
            'text_dark': '#1F2937',
            'text_medium': '#4B5563',
            "jade": "#00A86B",
            'text_light': '#9CA3AF',
            'border': '#E5E7EB',
            'warning': '#F59E0B',
            'danger': '#EF4444',  # Красный цвет для кнопок удаления
            'danger_hover': '#DC2626'  # Темнее при наведении
        }
        
        self.fonts = {
            'title': ('Helvetica', 24, 'bold'),
            'subtitle': ('Helvetica', 18, 'bold'),
            'heading': ('Helvetica', 16, 'bold'),
            'body': ('Helvetica', 14),
            'small': ('Helvetica', 12),
            'caption': ('Helvetica', 11),
            'tiny': ('Helvetica', 10, 'bold')  # Жирный для крестиков
        }
        
        self.show_main_menu()

    def clear_screen(self):
        """Очистка экрана"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_scrollable_frame(self, parent):
        """Создание фрейма с прокруткой (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
        # Контейнер
        container = tk.Frame(parent, bg='white')
        container.pack(fill='both', expand=True)
        
        # Canvas и Scrollbar
        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # Прокручиваемый фрейм ВНУТРИ Canvas
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        # Создаем окно в Canvas
        window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Настраиваем прокрутку
        def configure_scroll(event):
            # Обновляем область прокрутки
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Устанавливаем ширину прокручиваемого фрейма
            canvas.itemconfig(window, width=canvas.winfo_width())
        
        # Привязываем события
        scrollable_frame.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(window, width=e.width))
        
        # Настраиваем Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Упаковка
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Прокрутка колесиком мыши
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        return scrollable_frame, canvas

    def show_main_menu(self):
        """Главное меню"""
        self.clear_screen()
        
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill='both', expand=True, padx=40, pady=40)
        
        # Заголовок
        tk.Label(main_frame, 
                text="Финик",
                font=self.fonts['title'],
                fg=self.colors['jade'],
                bg='white').pack(pady=(20, 10))
        
        tk.Label(main_frame,
                text="Мои деньги. Мои правила",
                font=self.fonts['heading'],
                fg=self.colors['text_medium'],
                bg='white').pack(pady=(0, 40))
        
        # Карточки выбора
        cards_frame = tk.Frame(main_frame, bg='white')
        cards_frame.pack(fill='both', expand=True)
        
        # Подросток
        teen_card = tk.Frame(cards_frame, bg=self.colors['card_bg'], relief='flat', bd=1)
        teen_card.pack(fill='x', pady=10)
        
        teen_content = tk.Frame(teen_card, bg=self.colors['card_bg'], padx=25, pady=25)
        teen_content.pack(fill='x')
        
        tk.Label(teen_content,
                text="👦 Я подросток",
                font=self.fonts['heading'],
                fg=self.colors['primary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        tk.Label(teen_content,
                text=f"Баланс: {self.data['teen_balance']} Br",
                font=self.fonts['body'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(anchor='w', pady=(5, 0))
        
        tk.Label(teen_content,
                text="Управление целями и накоплениями",
                font=self.fonts['small'],
                fg=self.colors['text_medium'],
                bg=self.colors['card_bg']).pack(anchor='w', pady=(10, 0))
        
        # Кнопка ВНУТРИ карточки (не привязана к карточке)
        teen_btn = tk.Button(teen_content,
                           text="Войти",
                           font=self.fonts['body'],
                           fg='white',
                           bg=self.colors['primary'],
                           bd=0,
                           padx=30,
                           pady=8,
                           cursor='hand2',
                           command=self.show_teen_dashboard)
        teen_btn.pack(anchor='e', pady=(15, 0))
        
        # Родитель
        parent_card = tk.Frame(cards_frame, bg=self.colors['card_bg'], relief='flat', bd=1)
        parent_card.pack(fill='x', pady=10)
        
        parent_content = tk.Frame(parent_card, bg=self.colors['card_bg'], padx=25, pady=25)
        parent_content.pack(fill='x')
        
        tk.Label(parent_content,
                text="👨 Родитель",
                font=self.fonts['heading'],
                fg=self.colors['secondary'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        tk.Label(parent_content,
                text=f"Бюджет: {self.data['parent_balance']} Br",
                font=self.fonts['body'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(anchor='w', pady=(5, 0))
        
        tk.Label(parent_content,
                text="Создание заданий и контроль",
                font=self.fonts['small'],
                fg=self.colors['text_medium'],
                bg=self.colors['card_bg']).pack(anchor='w', pady=(10, 0))
        
        # Кнопка ВНУТРИ карточки
        parent_btn = tk.Button(parent_content,
                              text="Войти",
                              font=self.fonts['body'],
                              fg='white',
                              bg=self.colors['secondary'],
                              bd=0,
                              padx=30,
                              pady=8,
                              cursor='hand2',
                              command=self.show_parent_dashboard)
        parent_btn.pack(anchor='e', pady=(15, 0))

    def show_teen_dashboard(self):
        """Панель подростка"""
        self.clear_screen()
        
        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Хедер (фиксированный)
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Кнопка назад
        back_btn = tk.Button(header_frame,
                           text="← На главную",
                           font=self.fonts['small'],
                           fg=self.colors['primary'],
                           bg='white',
                           bd=0,
                           cursor='hand2',
                           command=self.show_main_menu)
        back_btn.pack(side='left')
        
        # Баланс
        tk.Label(header_frame,
                text=f"Баланс: {self.data['teen_balance']} Br",
                font=self.fonts['subtitle'],
                fg=self.colors['success'],
                bg='white').pack(side='right')
        
        # Создаем прокручиваемую область
        scrollable_main, canvas = self.create_scrollable_frame(main_frame)
        
        # Задания
        tk.Label(scrollable_main,
                text="Мои задания",
                font=self.fonts['heading'],
                fg=self.colors['text_dark'],
                bg='white').pack(anchor='w', pady=(0, 15))
        
        incomplete_tasks = [t for t in self.data['tasks'] if not t['completed']]
        
        if incomplete_tasks:
            for task in incomplete_tasks:
                self.create_teen_task_card(scrollable_main, task, canvas)
        else:
            empty_frame = tk.Frame(scrollable_main, bg=self.colors['card_bg'], relief='flat', bd=1)
            empty_frame.pack(fill='x', pady=5)
            
            tk.Label(empty_frame,
                    text="🎉 Все задания выполнены!",
                    font=self.fonts['body'],
                    fg=self.colors['text_medium'],
                    bg=self.colors['card_bg'],
                    padx=20,
                    pady=25).pack()
        
        # Цели
        tk.Label(scrollable_main,
                text="Мои цели",
                font=self.fonts['heading'],
                fg=self.colors['text_dark'],
                bg='white').pack(anchor='w', pady=(30, 15))
        
        if self.data['goals']:
            for goal in self.data['goals']:
                self.create_teen_goal_card(scrollable_main, goal, canvas)
        else:
            empty_frame = tk.Frame(scrollable_main, bg=self.colors['card_bg'], relief='flat', bd=1)
            empty_frame.pack(fill='x', pady=5)
            
            tk.Label(empty_frame,
                    text="Целей пока нет",
                    font=self.fonts['body'],
                    fg=self.colors['text_medium'],
                    bg=self.colors['card_bg'],
                    padx=20,
                    pady=25).pack()
        
        # Кнопка добавления цели
        add_btn = tk.Button(scrollable_main,
                          text="+ Добавить новую цель",
                          font=self.fonts['body'],
                          fg='white',
                          bg=self.colors['primary'],
                          bd=0,
                          padx=30,
                          pady=12,
                          cursor='hand2',
                          command=self.add_goal_dialog)
        add_btn.pack(pady=30)

    def create_teen_task_card(self, parent, task, canvas=None):
        """Карточка задания"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=1)
        card.pack(fill='x', pady=5)
        
        content = tk.Frame(card, bg=self.colors['card_bg'], padx=20, pady=15)
        content.pack(fill='x')
        
        # Верхняя строка
        top_frame = tk.Frame(content, bg=self.colors['card_bg'])
        top_frame.pack(fill='x')
        
        tk.Label(top_frame,
                text=task['name'],
                font=self.fonts['body'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(side='left')
        
        # Правая часть с крестиком и наградой
        right_frame = tk.Frame(top_frame, bg=self.colors['card_bg'])
        right_frame.pack(side='right')
        
        # Крестик удаления - стилизованная кнопка без изменения цвета
        delete_btn = tk.Label(right_frame,
                              text="✕",
                              font=self.fonts['tiny'],
                              fg='white',
                              bg=self.colors['danger'],
                              padx=8,
                              pady=1,
                              cursor='hand2')
        delete_btn.bind("<Button-1>", lambda e, t=task: self.delete_task_confirm(t, 'teen'))
        delete_btn.pack(side='right', padx=(5, 0))
        
        tk.Label(right_frame,
                text=f"+{task['reward']} Br",
                font=self.fonts['body'],
                fg=self.colors['success'],
                bg=self.colors['card_bg']).pack(side='right')
        
        # Кнопка выполнения (работающая!)
        complete_btn = tk.Button(content,
                               text="Отметить выполненным",
                               font=self.fonts['small'],
                               fg='white',
                               bg=self.colors['success'],
                               bd=0,
                               padx=20,
                               pady=6,
                               cursor='hand2')
        
        # Привязываем команду ОТДЕЛЬНО
        complete_btn.configure(command=lambda t=task: self.complete_task(t))
        complete_btn.pack(anchor='e', pady=(10, 0))

    def create_teen_goal_card(self, parent, goal, canvas=None):
        """Карточка цели"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=1)
        card.pack(fill='x', pady=5)
        
        content = tk.Frame(card, bg=self.colors['card_bg'], padx=20, pady=15)
        content.pack(fill='x')
        
        # Верхняя строка с названием и крестиком
        top_frame = tk.Frame(content, bg=self.colors['card_bg'])
        top_frame.pack(fill='x')
        
        tk.Label(top_frame,
                text=goal['name'],
                font=self.fonts['body'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(side='left')
        
        # Крестик удаления - стилизованная кнопка без изменения цвета
        delete_btn = tk.Label(top_frame,
                              text="✕",
                              font=self.fonts['tiny'],
                              fg='white',
                              bg=self.colors['danger'],
                              padx=8,
                              pady=1,
                              cursor='hand2')
        delete_btn.bind("<Button-1>", lambda e, g=goal: self.delete_goal_confirm(g))
        delete_btn.pack(side='right')
        
        # Прогресс
        progress = (goal['current'] / goal['target']) * 100 if goal['target'] > 0 else 0
        
        # Прогресс-бар
        progress_frame = tk.Frame(content, bg=self.colors['border'], height=6)
        progress_frame.pack(fill='x', pady=8)
        
        progress_bar = tk.Frame(progress_frame, bg=self.colors['primary'], height=6)
        progress_bar.place(relwidth=progress/100, relheight=1)
        
        # Информация
        progress_text = f"{goal['current']} Br / {goal['target']} Br ({progress:.0f}%)"
        tk.Label(content,
                text=progress_text,
                font=self.fonts['small'],
                fg=self.colors['text_medium'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        # Кнопка добавления денег (работающая!)
        add_btn = tk.Button(content,
                          text=f"Добавить деньги",
                          font=self.fonts['small'],
                          fg=self.colors['primary'],
                          bg='white',
                          bd=1,
                          padx=15,
                          pady=5,
                          cursor='hand2')
        
        # Привязываем команду ОТДЕЛЬНО
        add_btn.configure(command=lambda g=goal: self.add_money_to_goal(g))
        add_btn.pack(anchor='e', pady=(10, 0))

    def show_parent_dashboard(self):
        """Панель родителя"""
        self.clear_screen()
        
        main_frame = tk.Frame(self.root, bg='white')
        main_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Хедер
        header_frame = tk.Frame(main_frame, bg='white')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Назад
        back_btn = tk.Button(header_frame,
                           text="← На главную",
                           font=self.fonts['small'],
                           fg=self.colors['primary'],
                           bg='white',
                           bd=0,
                           cursor='hand2',
                           command=self.show_main_menu)
        back_btn.pack(side='left')
        
        # Балансы
        balance_frame = tk.Frame(header_frame, bg='white')
        balance_frame.pack(side='right')
        
        tk.Label(balance_frame,
                text=f"Ребенок: {self.data['teen_balance']} Br",
                font=self.fonts['small'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='e')
        
        tk.Label(balance_frame,
                text=f"Мой бюджет: {self.data['parent_balance']} Br",
                font=self.fonts['heading'],
                fg=self.colors['secondary'],
                bg='white').pack(anchor='e', pady=(2, 0))
        
        # Создаем прокручиваемую область
        scrollable_main, canvas = self.create_scrollable_frame(main_frame)
        
        # Кнопки действий (ВНЕ прокрутки, но в scrollable_main)
        actions_frame = tk.Frame(scrollable_main, bg='white')
        actions_frame.pack(fill='x', pady=(0, 30))
        
        # Кнопка пополнения
        add_balance_btn = tk.Button(actions_frame,
                                  text="💳 Пополнить баланс ребенка",
                                  font=self.fonts['body'],
                                  fg='white',
                                  bg=self.colors['primary'],
                                  bd=0,
                                  padx=25,
                                  pady=12,
                                  cursor='hand2')
        add_balance_btn.configure(command=self.add_balance_dialog)
        add_balance_btn.pack(side='left', padx=(0, 10))
        
        # Кнопка добавления задания
        add_task_btn = tk.Button(actions_frame,
                               text="📝 Создать задание",
                               font=self.fonts['body'],
                               fg=self.colors['secondary'],
                               bg='white',
                               bd=1,
                               padx=25,
                               pady=12,
                               cursor='hand2')
        add_task_btn.configure(command=self.add_task_dialog)
        add_task_btn.pack(side='left')
        
        # Список всех заданий
        tk.Label(scrollable_main,
                text="Все задания",
                font=self.fonts['heading'],
                fg=self.colors['text_dark'],
                bg='white').pack(anchor='w', pady=(0, 15))
        
        if self.data['tasks']:
            for task in self.data['tasks']:
                self.create_parent_task_card(scrollable_main, task, canvas)
        else:
            empty_frame = tk.Frame(scrollable_main, bg=self.colors['card_bg'], relief='flat', bd=1)
            empty_frame.pack(fill='x', pady=5)
            
            tk.Label(empty_frame,
                    text="Заданий пока нет",
                    font=self.fonts['body'],
                    fg=self.colors['text_medium'],
                    bg=self.colors['card_bg'],
                    padx=20,
                    pady=25).pack()

    def create_parent_task_card(self, parent, task, canvas=None):
        """Карточка задания для родителя"""
        card = tk.Frame(parent, bg=self.colors['card_bg'], relief='flat', bd=1)
        card.pack(fill='x', pady=5)
        
        content = tk.Frame(card, bg=self.colors['card_bg'], padx=20, pady=15)
        content.pack(fill='x')
        
        # Статус и название
        status_color = self.colors['success'] if task['completed'] else self.colors['warning']
        status_text = "✓ Выполнено" if task['completed'] else "● В ожидании"
        
        top_frame = tk.Frame(content, bg=self.colors['card_bg'])
        top_frame.pack(fill='x')
        
        tk.Label(top_frame,
                text=task['name'],
                font=self.fonts['body'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(side='left')
        
        # Правая часть
        right_frame = tk.Frame(top_frame, bg=self.colors['card_bg'])
        right_frame.pack(side='right')
        
        # Крестик удаления - стилизованная кнопка без изменения цвета
        delete_btn = tk.Label(right_frame,
                              text="✕",
                              font=self.fonts['tiny'],
                              fg='white',
                              bg=self.colors['danger'],
                              padx=8,
                              pady=1,
                              cursor='hand2')
        delete_btn.bind("<Button-1>", lambda e, t=task: self.delete_task_confirm(t, 'parent'))
        delete_btn.pack(side='right', padx=(5, 0))
        
        tk.Label(right_frame,
                text=status_text,
                font=self.fonts['small'],
                fg=status_color,
                bg=self.colors['card_bg']).pack(anchor='e')
        
        tk.Label(right_frame,
                text=f"{task['reward']} Br",
                font=self.fonts['body'],
                fg=self.colors['success'],
                bg=self.colors['card_bg']).pack(anchor='e', pady=(2, 0))

    # 📝 Методы удаления
    def delete_goal_confirm(self, goal):
        """Подтверждение удаления цели"""
        response = mb.askyesno(
            "Удаление цели",
            f"Вы уверены, что хотите удалить цель '{goal['name']}'?\n\n"
            f"Прогресс: {goal['current']} Br / {goal['target']} Br\n"
            "⚠️ Накопленные деньги не возвращаются на баланс!"
        )
        
        if response:
            self.data['goals'] = [g for g in self.data['goals'] if g['id'] != goal['id']]
            self.show_teen_dashboard()
            mb.showinfo("Успех", f"Цель '{goal['name']}' удалена")

    def delete_task_confirm(self, task, from_view):
        """Подтверждение удаления задания"""
        if task['completed']:
            response = mb.askyesno(
                "Удаление задания",
                f"Вы уверены, что хотите удалить задание '{task['name']}'?\n\n"
                "⚠️ Это задание уже выполнено и награда была выдана."
            )
        else:
            response = mb.askyesno(
                "Удаление задания",
                f"Вы уверены, что хотите удалить задание '{task['name']}'?\n\n"
                f"Вознаграждение: {task['reward']} Br\n"
                "Задание не было выполнено."
            )
        
        if response:
            self.data['tasks'] = [t for t in self.data['tasks'] if t['id'] != task['id']]
            
            if from_view == 'teen':
                self.show_teen_dashboard()
            else:
                self.show_parent_dashboard()
                
            mb.showinfo("Успех", f"Задание '{task['name']}' удалено")

    # 📝 Методы диалогов

    def add_goal_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новая цель")
        dialog.geometry("400x250")
        dialog.configure(bg='white')
        
        content = tk.Frame(dialog, bg='white', padx=30, pady=30)
        content.pack(fill='both', expand=True)
        
        tk.Label(content,
                text="Новая цель",
                font=self.fonts['heading'],
                fg=self.colors['text_dark'],
                bg='white').pack(pady=(0, 20))
        
        tk.Label(content,
                text="Название цели:",
                font=self.fonts['body'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='w', pady=(0, 5))
        
        name_entry = tk.Entry(content, font=self.fonts['body'], width=30, bd=1, relief='solid')
        name_entry.pack(fill='x', pady=(0, 15))
        
        tk.Label(content,
                text="Целевая сумма (Br):",
                font=self.fonts['body'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='w', pady=(0, 5))
        
        amount_entry = tk.Entry(content, font=self.fonts['body'], width=30, bd=1, relief='solid')
        amount_entry.pack(fill='x', pady=(0, 25))
        
        def save():
            name = name_entry.get().strip()
            try:
                amount = int(amount_entry.get())
                if name and amount > 0:
                    new_goal = {
                        'name': name,
                        'target': amount,
                        'current': 0,
                        'id': len(self.data['goals']) + 1
                    }
                    self.data['goals'].append(new_goal)
                    dialog.destroy()
                    self.show_teen_dashboard()
                    mb.showinfo("Успех", "Цель добавлена!")
                else:
                    mb.showerror("Ошибка", "Заполните все поля")
            except ValueError:
                mb.showerror("Ошибка", "Введите корректную сумму")
        
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame,
                 text="Отмена",
                 font=self.fonts['body'],
                 fg=self.colors['text_medium'],
                 bg='white',
                 bd=1,
                 padx=20,
                 pady=8,
                 command=dialog.destroy).pack(side='left')
        
        tk.Button(btn_frame,
                 text="Сохранить",
                 font=self.fonts['body'],
                 fg='white',
                 bg=self.colors['primary'],
                 bd=0,
                 padx=20,
                 pady=8,
                 command=save).pack(side='right')
        
        name_entry.focus()

    def add_money_to_goal(self, goal):
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить деньги")
        dialog.geometry("350x220")
        dialog.configure(bg='white')
        
        content = tk.Frame(dialog, bg='white', padx=30, pady=30)
        content.pack(fill='both', expand=True)
        
        tk.Label(content,
                text=goal['name'],
                font=self.fonts['body'],
                fg=self.colors['text_dark'],
                bg='white').pack(pady=(0, 10))
        
        tk.Label(content,
                text=f"Прогресс: {goal['current']} Br / {goal['target']} Br",
                font=self.fonts['small'],
                fg=self.colors['text_medium'],
                bg='white').pack(pady=(0, 20))
        
        tk.Label(content,
                text=f"Ваш баланс: {self.data['teen_balance']} Br",
                font=self.fonts['small'],
                fg=self.colors['text_dark'],
                bg='white').pack(pady=(0, 5))
        
        tk.Label(content,
                text="Сумма для добавления (Br):",
                font=self.fonts['body'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='w', pady=(0, 5))
        
        amount_entry = tk.Entry(content, font=self.fonts['body'], width=20, bd=1, relief='solid', justify='center')
        amount_entry.pack(pady=(0, 20))
        
        def add():
            try:
                amount = int(amount_entry.get())
                if amount <= 0:
                    mb.showerror("Ошибка", "Сумма должна быть больше 0")
                    return
                
                if amount > self.data['teen_balance']:
                    mb.showerror("Ошибка", "Недостаточно средств")
                    return
                
                goal['current'] += amount
                self.data['teen_balance'] -= amount
                dialog.destroy()
                self.show_teen_dashboard()
                mb.showinfo("Успех", f"Добавлено {amount} Br к цели!")
                
            except ValueError:
                mb.showerror("Ошибка", "Введите число")
        
        tk.Button(content,
                 text="Добавить",
                 font=self.fonts['body'],
                 fg='white',
                 bg=self.colors['primary'],
                 bd=0,
                 padx=30,
                 pady=8,
                 command=add).pack()
        
        amount_entry.focus()

    def add_task_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Новое задание")
        dialog.geometry("400x280")
        dialog.configure(bg='white')
        
        content = tk.Frame(dialog, bg='white', padx=30, pady=30)
        content.pack(fill='both', expand=True)
        
        tk.Label(content,
                text="Новое задание",
                font=self.fonts['heading'],
                fg=self.colors['text_dark'],
                bg='white').pack(pady=(0, 20))
        
        tk.Label(content,
                text="Описание задания:",
                font=self.fonts['body'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='w', pady=(0, 5))
        
        desc_entry = tk.Entry(content, font=self.fonts['body'], width=30, bd=1, relief='solid')
        desc_entry.pack(fill='x', pady=(0, 15))
        
        tk.Label(content,
                text="Вознаграждение (Br):",
                font=self.fonts['body'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='w', pady=(0, 5))
        
        reward_entry = tk.Entry(content, font=self.fonts['body'], width=30, bd=1, relief='solid')
        reward_entry.pack(fill='x', pady=(0, 25))
        
        def save():
            desc = desc_entry.get().strip()
            try:
                reward = int(reward_entry.get())
                if desc and reward > 0:
                    new_task = {
                        'name': desc,
                        'reward': reward,
                        'completed': False,
                        'id': len(self.data['tasks']) + 1
                    }
                    self.data['tasks'].append(new_task)
                    dialog.destroy()
                    self.show_parent_dashboard()
                    mb.showinfo("Успех", "Задание создано!")
                else:
                    mb.showerror("Ошибка", "Заполните все поля")
            except ValueError:
                mb.showerror("Ошибка", "Введите корректную сумму")
        
        btn_frame = tk.Frame(content, bg='white')
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame,
                 text="Отмена",
                 font=self.fonts['body'],
                 fg=self.colors['text_medium'],
                 bg='white',
                 bd=1,
                 padx=20,
                 pady=8,
                 command=dialog.destroy).pack(side='left')
        
        tk.Button(btn_frame,
                 text="Создать",
                 font=self.fonts['body'],
                 fg='white',
                 bg=self.colors['secondary'],
                 bd=0,
                 padx=20,
                 pady=8,
                 command=save).pack(side='right')
        
        desc_entry.focus()

    def add_balance_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Пополнение баланса")
        dialog.geometry("350x250")
        dialog.configure(bg='white')
        
        content = tk.Frame(dialog, bg='white', padx=30, pady=30)
        content.pack(fill='both', expand=True)
        
        tk.Label(content,
                text="Пополнение баланса",
                font=self.fonts['heading'],
                fg=self.colors['text_dark'],
                bg='white').pack(pady=(0, 20))
        
        info_frame = tk.Frame(content, bg=self.colors['card_bg'], relief='flat', bd=1)
        info_frame.pack(fill='x', pady=(0, 20))
        
        info_content = tk.Frame(info_frame, bg=self.colors['card_bg'], padx=15, pady=15)
        info_content.pack(fill='x')
        
        tk.Label(info_content,
                text=f"Бюджет родителя: {self.data['parent_balance']} Br",
                font=self.fonts['small'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(anchor='w')
        
        tk.Label(info_content,
                text=f"Баланс ребенка: {self.data['teen_balance']} Br",
                font=self.fonts['small'],
                fg=self.colors['text_dark'],
                bg=self.colors['card_bg']).pack(anchor='w', pady=(5, 0))
        
        tk.Label(content,
                text="Сумма перевода (Br):",
                font=self.fonts['body'],
                fg=self.colors['text_medium'],
                bg='white').pack(anchor='w', pady=(0, 5))
        
        amount_entry = tk.Entry(content, font=self.fonts['body'], width=20, bd=1, relief='solid', justify='center')
        amount_entry.pack(pady=(0, 20))
        
        def transfer():
            try:
                amount = int(amount_entry.get())
                if amount <= 0:
                    mb.showerror("Ошибка", "Сумма должна быть больше 0")
                    return
                
                if amount > self.data['parent_balance']:
                    mb.showerror("Ошибка", "Недостаточно средств в бюджете")
                    return
                
                self.data['parent_balance'] -= amount
                self.data['teen_balance'] += amount
                dialog.destroy()
                self.show_parent_dashboard()
                mb.showinfo("Успех", f"Переведено {amount} Br!")
                
            except ValueError:
                mb.showerror("Ошибка", "Введите число")
        
        tk.Button(content,
                 text="Перевести",
                 font=self.fonts['body'],
                 fg='white',
                 bg=self.colors['primary'],
                 bd=0,
                 padx=30,
                 pady=8,
                 command=transfer).pack()
        
        amount_entry.focus()

    def complete_task(self, task):
        if not task['completed']:
            task['completed'] = True
            self.data['teen_balance'] += task['reward']
            
            self.show_teen_dashboard()
            mb.showinfo("Отлично!", 
                       f"Задание выполнено!\n\n"
                       f"Начислено: {task['reward']} Br\n"
                       f"Новый баланс: {self.data['teen_balance']} Br")

# 🚀 ЗАПУСК
if __name__ == "__main__":
    root = tk.Tk()
    app = FixedFinikApp(root)
    root.mainloop()