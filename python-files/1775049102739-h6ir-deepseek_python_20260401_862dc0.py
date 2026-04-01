import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, date
from calendar import month_abbr
import itertools

try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ---------------------- DATABASE ----------------------
DB_NAME = "pool_service.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Клиенты
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            doc_type TEXT NOT NULL,   -- 'begin', 'end', 'both'
            specialist TEXT,
            rate REAL,
            comment TEXT
        )
    ''')
    # Месячные данные
    c.execute('''
        CREATE TABLE IF NOT EXISTS monthly_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            month_year TEXT NOT NULL,   -- '2026-02'
            invoice INTEGER DEFAULT 0,
            act INTEGER DEFAULT 0,
            docs_returned INTEGER DEFAULT 0,
            visits INTEGER DEFAULT 0,
            FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE,
            UNIQUE(client_id, month_year)
        )
    ''')
    conn.commit()
    conn.close()

def get_clients(doc_type=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if doc_type:
        if doc_type == 'begin':
            c.execute("SELECT * FROM clients WHERE doc_type IN ('begin', 'both') ORDER BY name")
        elif doc_type == 'end':
            c.execute("SELECT * FROM clients WHERE doc_type IN ('end', 'both') ORDER BY name")
        else:
            c.execute("SELECT * FROM clients ORDER BY name")
    else:
        c.execute("SELECT * FROM clients ORDER BY name")
    rows = c.fetchall()
    conn.close()
    return rows

def add_client(name, doc_type, specialist='', rate=0.0, comment=''):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO clients (name, doc_type, specialist, rate, comment) VALUES (?, ?, ?, ?, ?)",
              (name, doc_type, specialist, rate, comment))
    conn.commit()
    conn.close()

def update_client(client_id, name, doc_type, specialist, rate, comment):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE clients SET name=?, doc_type=?, specialist=?, rate=?, comment=? WHERE id=?",
              (name, doc_type, specialist, rate, comment, client_id))
    conn.commit()
    conn.close()

def delete_client(client_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()

def get_monthly_data(client_id, month_year=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if month_year:
        c.execute("SELECT * FROM monthly_data WHERE client_id=? AND month_year=?", (client_id, month_year))
        row = c.fetchone()
        conn.close()
        return row
    else:
        c.execute("SELECT month_year, invoice, act, docs_returned, visits FROM monthly_data WHERE client_id=? ORDER BY month_year", (client_id,))
        rows = c.fetchall()
        conn.close()
        return rows

def set_monthly_data(client_id, month_year, invoice, act, docs_returned, visits):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO monthly_data (client_id, month_year, invoice, act, docs_returned, visits)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(client_id, month_year) DO UPDATE SET
            invoice=excluded.invoice,
            act=excluded.act,
            docs_returned=excluded.docs_returned,
            visits=excluded.visits
    ''', (client_id, month_year, invoice, act, docs_returned, visits))
    conn.commit()
    conn.close()

def get_all_months(start_month=None, end_month=None):
    """Возвращает список строк 'YYYY-MM' начиная с текущего месяца и до декабря следующего года"""
    today = date.today()
    if start_month is None:
        start = today.replace(day=1)
    else:
        start = start_month
    # до декабря следующего года
    end = date(start.year + 1, 12, 1)
    months = []
    current = start
    while current <= end:
        months.append(current.strftime('%Y-%m'))
        if current.month == 12:
            current = current.replace(year=current.year+1, month=1)
        else:
            current = current.replace(month=current.month+1)
    return months

def get_total_visits(client_id, year):
    """Суммарное количество выездов за год"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        SELECT SUM(visits) FROM monthly_data
        WHERE client_id=? AND month_year LIKE ?
    ''', (client_id, f'{year}-%'))
    total = c.fetchone()[0]
    conn.close()
    return total if total else 0

# ---------------------- GUI ----------------------
class ClientEditDialog(tk.Toplevel):
    def __init__(self, parent, title, client=None):
        super().__init__(parent)
        self.title(title)
        self.client = client
        self.result = None
        self.geometry("400x350")
        self.resizable(False, False)

        tk.Label(self, text="Имя клиента:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self, text="Тип документов:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.doc_type_var = tk.StringVar(value='begin')
        doc_types = [('Начало месяца', 'begin'), ('Конец месяца', 'end'), ('Начало и конец', 'both')]
        frame_dt = tk.Frame(self)
        frame_dt.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        for text, val in doc_types:
            tk.Radiobutton(frame_dt, text=text, variable=self.doc_type_var, value=val).pack(anchor='w')

        tk.Label(self, text="Сервисный специалист:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.specialist_entry = tk.Entry(self, width=40)
        self.specialist_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self, text="Ставка СО (руб):").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.rate_entry = tk.Entry(self, width=40)
        self.rate_entry.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(self, text="Комментарий:").grid(row=4, column=0, sticky='nw', padx=10, pady=5)
        self.comment_text = tk.Text(self, height=4, width=30)
        self.comment_text.grid(row=4, column=1, padx=10, pady=5)

        if client:
            self.name_entry.insert(0, client[1])
            self.doc_type_var.set(client[2])
            self.specialist_entry.insert(0, client[3] if client[3] else '')
            self.rate_entry.insert(0, str(client[4]) if client[4] else '0')
            self.comment_text.insert('1.0', client[5] if client[5] else '')

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side='left', padx=10)

    def save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Имя клиента обязательно")
            return
        try:
            rate = float(self.rate_entry.get()) if self.rate_entry.get() else 0.0
        except:
            messagebox.showwarning("Ошибка", "Ставка должна быть числом")
            return
        self.result = (name, self.doc_type_var.get(), self.specialist_entry.get().strip(),
                       rate, self.comment_text.get('1.0', 'end').strip())
        self.destroy()


class MonthEditDialog(tk.Toplevel):
    def __init__(self, parent, month_year, data):
        super().__init__(parent)
        self.title(f"Редактирование {month_year}")
        self.data = data  # (invoice, act, docs_returned, visits)
        self.result = None
        self.geometry("300x250")
        self.resizable(False, False)

        tk.Label(self, text=f"Месяц: {month_year}", font=('', 10, 'bold')).pack(pady=10)

        self.invoice_var = tk.IntVar(value=data[0])
        self.act_var = tk.IntVar(value=data[1])
        self.docs_var = tk.IntVar(value=data[2])

        chk_inv = tk.Checkbutton(self, text="Счёт", variable=self.invoice_var, onvalue=1, offvalue=0)
        chk_inv.pack(anchor='w', padx=20, pady=5)
        chk_act = tk.Checkbutton(self, text="Акт", variable=self.act_var, onvalue=1, offvalue=0)
        chk_act.pack(anchor='w', padx=20, pady=5)
        chk_docs = tk.Checkbutton(self, text="Вернул доки", variable=self.docs_var, onvalue=1, offvalue=0)
        chk_docs.pack(anchor='w', padx=20, pady=5)

        tk.Label(self, text="Кол-во выездов:").pack(anchor='w', padx=20, pady=5)
        self.visits_entry = tk.Entry(self, width=10)
        self.visits_entry.insert(0, str(data[3]))
        self.visits_entry.pack(anchor='w', padx=20)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side='left', padx=10)

    def save(self):
        try:
            visits = int(self.visits_entry.get())
        except:
            messagebox.showwarning("Ошибка", "Количество выездов должно быть целым числом")
            return
        self.result = (self.invoice_var.get(), self.act_var.get(), self.docs_var.get(), visits)
        self.destroy()


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("ASTRAL-GROP.SO.01")
        self.root.geometry("1300x700")
        self.root.minsize(1000, 600)

        # Устанавливаем фон морской волны с узором
        self.set_background()

        # Инициализация БД
        init_db()

        # Переменные
        self.current_client = None

        # Создание интерфейса
        self.create_notebook()
        self.create_journal_tab()
        self.create_stats_tab()

        # Загрузка данных в левую панель
        self.refresh_client_lists()

    def set_background(self):
        """Устанавливает фон с узором морской волны (если есть Pillow) или просто цвет"""
        if PIL_AVAILABLE:
            # Создаем текстуру с геометрическим узором (сетка)
            size = 400
            img = Image.new('RGB', (size, size), '#20B2AA')  # морская волна
            draw = ImageDraw.Draw(img)
            # Рисуем светлые линии
            step = 20
            for i in range(0, size, step):
                draw.line([(i, 0), (i, size)], fill='#40E0D0', width=1)
                draw.line([(0, i), (size, i)], fill='#40E0D0', width=1)
            # Добавляем точки
            for x in range(step//2, size, step):
                for y in range(step//2, size, step):
                    draw.ellipse((x-2, y-2, x+2, y+2), fill='#E0FFFF')
            self.bg_image = ImageTk.PhotoImage(img)
            bg_label = tk.Label(self.root, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            bg_label.lower()
        else:
            self.root.configure(bg='#20B2AA')

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

    def create_journal_tab(self):
        self.journal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.journal_frame, text="Журнал")

        # Левая панель со списками клиентов
        left_frame = ttk.Frame(self.journal_frame, width=300)
        left_frame.pack(side='left', fill='y', padx=5, pady=5)
        left_frame.pack_propagate(False)

        # Документы в начале месяца
        begin_frame = ttk.LabelFrame(left_frame, text="Документы в начале месяца", padding=5)
        begin_frame.pack(fill='both', expand=True, pady=5)
        self.begin_listbox = tk.Listbox(begin_frame, height=8, bg='#E0FFFF', selectbackground='#20B2AA')
        self.begin_listbox.pack(fill='both', expand=True, padx=2, pady=2)
        self.begin_listbox.bind('<<ListboxSelect>>', lambda e: self.on_client_select('begin'))
        btn_begin_add = ttk.Button(begin_frame, text="Добавить", command=lambda: self.add_client('begin'))
        btn_begin_add.pack(side='left', padx=5, pady=2)
        btn_begin_del = ttk.Button(begin_frame, text="Удалить", command=lambda: self.delete_client('begin'))
        btn_begin_del.pack(side='left', padx=5, pady=2)

        # Документы в конце месяца
        end_frame = ttk.LabelFrame(left_frame, text="Документы в конце месяца", padding=5)
        end_frame.pack(fill='both', expand=True, pady=5)
        self.end_listbox = tk.Listbox(end_frame, height=8, bg='#E0FFFF', selectbackground='#20B2AA')
        self.end_listbox.pack(fill='both', expand=True, padx=2, pady=2)
        self.end_listbox.bind('<<ListboxSelect>>', lambda e: self.on_client_select('end'))
        btn_end_add = ttk.Button(end_frame, text="Добавить", command=lambda: self.add_client('end'))
        btn_end_add.pack(side='left', padx=5, pady=2)
        btn_end_del = ttk.Button(end_frame, text="Удалить", command=lambda: self.delete_client('end'))
        btn_end_del.pack(side='left', padx=5, pady=2)

        # Правая панель с деталями клиента и таблицей месяцев
        right_frame = ttk.Frame(self.journal_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Карточка клиента
        client_card = ttk.LabelFrame(right_frame, text="Данные клиента", padding=10)
        client_card.pack(fill='x', pady=5)

        # Поля
        self.client_name_var = tk.StringVar()
        ttk.Label(client_card, text="Клиент:").grid(row=0, column=0, sticky='w')
        ttk.Label(client_card, textvariable=self.client_name_var).grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(client_card, text="Специалист:").grid(row=1, column=0, sticky='w', pady=5)
        self.specialist_var = tk.StringVar()
        self.specialist_entry = ttk.Entry(client_card, textvariable=self.specialist_var, width=30)
        self.specialist_entry.grid(row=1, column=1, sticky='w', padx=5)
        self.specialist_entry.bind('<FocusOut>', lambda e: self.save_client_field('specialist'))

        ttk.Label(client_card, text="Ставка СО:").grid(row=2, column=0, sticky='w', pady=5)
        self.rate_var = tk.StringVar()
        self.rate_entry = ttk.Entry(client_card, textvariable=self.rate_var, width=30)
        self.rate_entry.grid(row=2, column=1, sticky='w', padx=5)
        self.rate_entry.bind('<FocusOut>', lambda e: self.save_client_field('rate'))

        ttk.Label(client_card, text="Комментарий:").grid(row=3, column=0, sticky='nw', pady=5)
        self.comment_text = tk.Text(client_card, height=3, width=40, bg='#E0FFFF')
        self.comment_text.grid(row=3, column=1, sticky='w', padx=5, pady=5)
        self.comment_text.bind('<FocusOut>', lambda e: self.save_client_field('comment'))

        # Кнопка для редактирования всех данных клиента
        ttk.Button(client_card, text="Редактировать клиента", command=self.edit_current_client).grid(row=4, column=0, columnspan=2, pady=10)

        # Таблица месяцев
        months_frame = ttk.LabelFrame(right_frame, text="Обслуживание по месяцам", padding=5)
        months_frame.pack(fill='both', expand=True, pady=5)

        # Панель управления таблицей
        control_frame = ttk.Frame(months_frame)
        control_frame.pack(fill='x', pady=5)

        self.hide_past_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Скрыть прошедшие месяцы", variable=self.hide_past_var,
                        command=self.refresh_months_table).pack(side='left', padx=5)

        # Treeview для месяцев
        columns = ('month', 'invoice', 'act', 'docs_returned', 'visits')
        self.month_tree = ttk.Treeview(months_frame, columns=columns, show='headings', height=12)
        self.month_tree.heading('month', text='Месяц')
        self.month_tree.heading('invoice', text='Счёт')
        self.month_tree.heading('act', text='Акт')
        self.month_tree.heading('docs_returned', text='Вернул доки')
        self.month_tree.heading('visits', text='Выезды')
        self.month_tree.column('month', width=100, anchor='center')
        self.month_tree.column('invoice', width=80, anchor='center')
        self.month_tree.column('act', width=80, anchor='center')
        self.month_tree.column('docs_returned', width=100, anchor='center')
        self.month_tree.column('visits', width=80, anchor='center')

        # Привязываем двойной клик для редактирования месяца
        self.month_tree.bind('<Double-1>', self.edit_month)

        scrollbar = ttk.Scrollbar(months_frame, orient='vertical', command=self.month_tree.yview)
        self.month_tree.configure(yscrollcommand=scrollbar.set)

        self.month_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Изначально нет выбранного клиента
        self.client_name_var.set("")
        self.specialist_var.set("")
        self.rate_var.set("")
        self.comment_text.delete('1.0', tk.END)

    def create_stats_tab(self):
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Статистика выездов")

        # Выбор клиента
        client_frame = ttk.LabelFrame(stats_frame, text="Выберите клиента", padding=10)
        client_frame.pack(fill='x', padx=10, pady=10)

        self.stats_client_var = tk.StringVar()
        self.stats_client_combo = ttk.Combobox(client_frame, textvariable=self.stats_client_var, width=50)
        self.stats_client_combo.pack(side='left', padx=5)
        self.stats_client_combo.bind('<<ComboboxSelected>>', self.update_stats)

        # Выбор года
        year_frame = ttk.LabelFrame(stats_frame, text="Год", padding=10)
        year_frame.pack(fill='x', padx=10, pady=10)
        self.stats_year_var = tk.StringVar(value=str(datetime.now().year))
        years = [str(y) for y in range(datetime.now().year-2, datetime.now().year+2)]
        self.stats_year_combo = ttk.Combobox(year_frame, textvariable=self.stats_year_var, values=years, width=10)
        self.stats_year_combo.pack(side='left', padx=5)
        self.stats_year_combo.bind('<<ComboboxSelected>>', self.update_stats)

        # Результат
        result_frame = ttk.LabelFrame(stats_frame, text="Результат", padding=10)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        self.stats_label = ttk.Label(result_frame, text="", font=('', 12))
        self.stats_label.pack(pady=20)

        # Заполним список клиентов
        self.refresh_stats_clients()

    def refresh_stats_clients(self):
        clients = get_clients()
        self.stats_client_combo['values'] = [c[1] for c in clients]
        if clients:
            self.stats_client_var.set(clients[0][1])
            self.update_stats()

    def update_stats(self, event=None):
        client_name = self.stats_client_var.get()
        if not client_name:
            return
        year = self.stats_year_var.get()
        # Найдем id клиента
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM clients WHERE name=?", (client_name,))
        row = c.fetchone()
        conn.close()
        if row:
            total = get_total_visits(row[0], year)
            self.stats_label.config(text=f"Всего выездов за {year} год: {total}")
        else:
            self.stats_label.config(text="Клиент не найден")

    def refresh_client_lists(self):
        # Очистка списков
        self.begin_listbox.delete(0, tk.END)
        self.end_listbox.delete(0, tk.END)

        clients_begin = get_clients('begin')
        clients_end = get_clients('end')

        self.begin_clients = clients_begin
        self.end_clients = clients_end

        for c in clients_begin:
            self.begin_listbox.insert(tk.END, c[1])
        for c in clients_end:
            self.end_listbox.insert(tk.END, c[1])

    def on_client_select(self, list_type):
        if list_type == 'begin':
            selection = self.begin_listbox.curselection()
            if selection:
                idx = selection[0]
                client = self.begin_clients[idx]
                self.load_client(client)
        else:
            selection = self.end_listbox.curselection()
            if selection:
                idx = selection[0]
                client = self.end_clients[idx]
                self.load_client(client)

    def load_client(self, client):
        self.current_client = client
        self.client_name_var.set(client[1])
        self.specialist_var.set(client[3] if client[3] else '')
        self.rate_var.set(str(client[4]) if client[4] else '0')
        self.comment_text.delete('1.0', tk.END)
        self.comment_text.insert('1.0', client[5] if client[5] else '')
        self.refresh_months_table()

    def save_client_field(self, field):
        if not self.current_client:
            return
        client_id = self.current_client[0]
        if field == 'specialist':
            new_val = self.specialist_var.get()
            update_client(client_id, self.current_client[1], self.current_client[2], new_val,
                          self.current_client[4], self.current_client[5])
        elif field == 'rate':
            try:
                new_val = float(self.rate_var.get())
            except:
                new_val = 0
            update_client(client_id, self.current_client[1], self.current_client[2],
                          self.current_client[3], new_val, self.current_client[5])
        elif field == 'comment':
            new_val = self.comment_text.get('1.0', 'end').strip()
            update_client(client_id, self.current_client[1], self.current_client[2],
                          self.current_client[3], self.current_client[4], new_val)
        # Обновляем текущего клиента после сохранения
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM clients WHERE id=?", (client_id,))
        self.current_client = c.fetchone()
        conn.close()

    def edit_current_client(self):
        if not self.current_client:
            messagebox.showinfo("Информация", "Сначала выберите клиента")
            return
        dlg = ClientEditDialog(self.root, "Редактирование клиента", self.current_client)
        self.root.wait_window(dlg)
        if dlg.result:
            name, doc_type, specialist, rate, comment = dlg.result
            update_client(self.current_client[0], name, doc_type, specialist, rate, comment)
            self.refresh_client_lists()
            # Перезагружаем текущего клиента
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM clients WHERE id=?", (self.current_client[0],))
            self.current_client = c.fetchone()
            conn.close()
            self.load_client(self.current_client)

    def add_client(self, doc_list_type):
        # doc_list_type: 'begin' или 'end' – для предустановки типа документов
        dlg = ClientEditDialog(self.root, "Новый клиент")
        self.root.wait_window(dlg)
        if dlg.result:
            name, doc_type, specialist, rate, comment = dlg.result
            # Если добавляли через кнопку в начале/конце, можно принудительно установить соответствующий doc_type
            # Но диалог уже содержит выбор, оставим как есть
            add_client(name, doc_type, specialist, rate, comment)
            self.refresh_client_lists()

    def delete_client(self, list_type):
        if list_type == 'begin':
            selection = self.begin_listbox.curselection()
            if not selection:
                messagebox.showinfo("Информация", "Выберите клиента для удаления")
                return
            idx = selection[0]
            client = self.begin_clients[idx]
        else:
            selection = self.end_listbox.curselection()
            if not selection:
                messagebox.showinfo("Информация", "Выберите клиента для удаления")
                return
            idx = selection[0]
            client = self.end_clients[idx]

        if messagebox.askyesno("Подтверждение", f"Удалить клиента {client[1]}?"):
            delete_client(client[0])
            if self.current_client and self.current_client[0] == client[0]:
                self.current_client = None
                self.client_name_var.set("")
                self.specialist_var.set("")
                self.rate_var.set("")
                self.comment_text.delete('1.0', tk.END)
                self.month_tree.delete(*self.month_tree.get_children())
            self.refresh_client_lists()

    def refresh_months_table(self):
        if not self.current_client:
            return
        # Получаем все возможные месяцы
        all_months = get_all_months()
        # Данные из БД
        data = {row[0]: (row[1], row[2], row[3], row[4]) for row in get_monthly_data(self.current_client[0])}
        # Отфильтровываем прошедшие, если нужно
        today = date.today()
        current_year_month = today.strftime('%Y-%m')
        months_to_show = []
        for m in all_months:
            if self.hide_past_var.get() and m < current_year_month:
                continue
            months_to_show.append(m)

        self.month_tree.delete(*self.month_tree.get_children())
        for m in months_to_show:
            inv, act, docs, visits = data.get(m, (0, 0, 0, 0))
            # Отображаем галочки текстом ✓ или ✗
            inv_str = "✓" if inv else "✗"
            act_str = "✓" if act else "✗"
            docs_str = "✓" if docs else "✗"
            self.month_tree.insert('', 'end', values=(m, inv_str, act_str, docs_str, visits), tags=(m,))

        # Для зелёных галочек
        self.month_tree.tag_configure('✓', foreground='green')
        # Но тэги не работают прямо так, можно настроить через стиль, но оставим пока просто текст.

    def edit_month(self, event):
        if not self.current_client:
            return
        selected = self.month_tree.selection()
        if not selected:
            return
        item = selected[0]
        values = self.month_tree.item(item, 'values')
        month_year = values[0]
        # Получаем текущие значения из БД (для точности)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT invoice, act, docs_returned, visits FROM monthly_data WHERE client_id=? AND month_year=?",
                  (self.current_client[0], month_year))
        row = c.fetchone()
        conn.close()
        if row is None:
            current_data = (0, 0, 0, 0)
        else:
            current_data = row
        dlg = MonthEditDialog(self.root, month_year, current_data)
        self.root.wait_window(dlg)
        if dlg.result:
            inv, act, docs, visits = dlg.result
            set_monthly_data(self.current_client[0], month_year, inv, act, docs, visits)
            self.refresh_months_table()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()