import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import calendar

DB_NAME = "pool_service.db"

ru_months = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

# ---------------------- DATABASE ----------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            doc_type TEXT NOT NULL,
            specialist TEXT,
            rate REAL,
            rate_prev_year REAL,
            rate_prev2_year REAL,
            comment TEXT,
            is_summer INTEGER DEFAULT 0
        )
    ''')
    for col in ('rate_prev_year', 'rate_prev2_year', 'is_summer'):
        try:
            if 'rate' in col:
                c.execute(f"ALTER TABLE clients ADD COLUMN {col} REAL")
            else:
                c.execute(f"ALTER TABLE clients ADD COLUMN {col} INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    c.execute('''
        CREATE TABLE IF NOT EXISTS monthly_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            month_year TEXT NOT NULL,
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

def add_client(name, doc_type, specialist='', rate=0.0, rate_prev_year=0.0, rate_prev2_year=0.0, comment='', is_summer=0):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO clients (name, doc_type, specialist, rate, rate_prev_year, rate_prev2_year, comment, is_summer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, doc_type, specialist, rate, rate_prev_year, rate_prev2_year, comment, is_summer))
    conn.commit()
    conn.close()

def update_client(client_id, name, doc_type, specialist, rate, rate_prev_year, rate_prev2_year, comment, is_summer):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        UPDATE clients SET name=?, doc_type=?, specialist=?, rate=?, rate_prev_year=?, rate_prev2_year=?, comment=?, is_summer=?
        WHERE id=?
    """, (name, doc_type, specialist, rate, rate_prev_year, rate_prev2_year, comment, is_summer, client_id))
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
        c.execute("SELECT invoice, act, docs_returned, visits FROM monthly_data WHERE client_id=? AND month_year=?", (client_id, month_year))
        row = c.fetchone()
        conn.close()
        return row if row else (0,0,0,0)
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

def get_all_months():
    today = date.today()
    start = today.replace(day=1)
    end = date(2030, 12, 1)
    months = []
    current = start
    while current <= end:
        months.append(current.strftime('%Y-%m'))
        if current.month == 12:
            current = current.replace(year=current.year+1, month=1)
        else:
            current = current.replace(month=current.month+1)
    return months

def get_total_visits(client_ids, year):
    if not client_ids:
        return 0
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    placeholders = ','.join('?' * len(client_ids))
    query = f'''
        SELECT SUM(visits) FROM monthly_data
        WHERE client_id IN ({placeholders}) AND month_year LIKE ?
    '''
    c.execute(query, client_ids + [f'{year}-%'])
    total = c.fetchone()[0]
    conn.close()
    return total if total else 0

def get_total_cost(client_ids, year):
    if not client_ids:
        return 0
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total_cost = 0
    for cid in client_ids:
        c.execute("SELECT rate FROM clients WHERE id=?", (cid,))
        rate_row = c.fetchone()
        rate = rate_row[0] if rate_row else 0
        visits = get_total_visits([cid], year)
        total_cost += rate * visits
    conn.close()
    return total_cost

def format_month(month_str):
    year, month = map(int, month_str.split('-'))
    return f"{ru_months[month-1]} {year} года"

def display_name(client):
    name = client[1]
    if client[8] == 1:
        return f"{name} Летний"
    return name

# ---------------------- DIALOGS ----------------------
class ClientEditDialog(tk.Toplevel):
    def __init__(self, parent, title, client=None):
        super().__init__(parent)
        self.title(title)
        self.client = client
        self.result = None
        self.geometry("500x550")
        self.resizable(False, False)

        row = 0
        tk.Label(self, text="Имя клиента:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.name_entry = tk.Entry(self, width=40)
        self.name_entry.grid(row=row, column=1, padx=10, pady=5)
        self._enable_copy_paste(self.name_entry)
        row += 1

        self.is_summer_var = tk.IntVar(value=0)
        tk.Checkbutton(self, text="Летний (добавить 'Летний' к имени)", variable=self.is_summer_var).grid(row=row, column=0, columnspan=2, sticky='w', padx=10, pady=5)
        row += 1

        tk.Label(self, text="Тип документов:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.doc_type_var = tk.StringVar(value='begin')
        doc_types = [('Начало месяца', 'begin'), ('Конец месяца', 'end'), ('Начало и конец', 'both')]
        frame_dt = tk.Frame(self)
        frame_dt.grid(row=row, column=1, sticky='w', padx=10, pady=5)
        for text, val in doc_types:
            tk.Radiobutton(frame_dt, text=text, variable=self.doc_type_var, value=val).pack(anchor='w')
        row += 1

        tk.Label(self, text="Сервисный специалист:").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.specialist_entry = tk.Entry(self, width=40)
        self.specialist_entry.grid(row=row, column=1, padx=10, pady=5)
        self._enable_copy_paste(self.specialist_entry)
        row += 1

        tk.Label(self, text="Ставка СО (руб):").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.rate_entry = tk.Entry(self, width=40)
        self.rate_entry.grid(row=row, column=1, padx=10, pady=5)
        self._enable_copy_paste(self.rate_entry)
        row += 1

        tk.Label(self, text="Ставка прошлый год (руб):").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.rate_prev_entry = tk.Entry(self, width=40)
        self.rate_prev_entry.grid(row=row, column=1, padx=10, pady=5)
        self._enable_copy_paste(self.rate_prev_entry)
        row += 1

        tk.Label(self, text="Ставка позапрошлый год (руб):").grid(row=row, column=0, sticky='w', padx=10, pady=5)
        self.rate_prev2_entry = tk.Entry(self, width=40)
        self.rate_prev2_entry.grid(row=row, column=1, padx=10, pady=5)
        self._enable_copy_paste(self.rate_prev2_entry)
        row += 1

        tk.Label(self, text="Комментарий:").grid(row=row, column=0, sticky='nw', padx=10, pady=5)
        self.comment_text = tk.Text(self, height=5, width=35)
        self.comment_text.grid(row=row, column=1, padx=10, pady=5)
        self._enable_copy_paste(self.comment_text)
        row += 1

        if client:
            self.name_entry.insert(0, client[1])
            self.is_summer_var.set(client[8] if len(client) > 8 else 0)
            self.doc_type_var.set(client[2])
            self.specialist_entry.insert(0, client[3] if client[3] else '')
            self.rate_entry.insert(0, str(client[4]) if client[4] else '0')
            self.rate_prev_entry.insert(0, str(client[5]) if client[5] else '0')
            self.rate_prev2_entry.insert(0, str(client[6]) if client[6] else '0')
            self.comment_text.insert('1.0', client[7] if client[7] else '')

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=20)
        tk.Button(btn_frame, text="Сохранить", command=self.save).pack(side='left', padx=10)
        tk.Button(btn_frame, text="Отмена", command=self.destroy).pack(side='left', padx=10)

    def _enable_copy_paste(self, widget):
        def copy(event):
            widget.event_generate('<<Copy>>')
            return "break"
        def cut(event):
            widget.event_generate('<<Cut>>')
            return "break"
        def paste(event):
            widget.event_generate('<<Paste>>')
            return "break"
        widget.bind('<Control-c>', copy)
        widget.bind('<Control-x>', cut)
        widget.bind('<Control-v>', paste)

        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Копировать", command=lambda: widget.event_generate('<<Copy>>'))
        menu.add_command(label="Вырезать", command=lambda: widget.event_generate('<<Cut>>'))
        menu.add_command(label="Вставить", command=lambda: widget.event_generate('<<Paste>>'))
        def show_menu(e):
            menu.tk_popup(e.x_root, e.y_root)
        widget.bind('<Button-3>', show_menu)

    def save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Имя клиента обязательно")
            return
        try:
            rate = float(self.rate_entry.get()) if self.rate_entry.get() else 0.0
            rate_prev = float(self.rate_prev_entry.get()) if self.rate_prev_entry.get() else 0.0
            rate_prev2 = float(self.rate_prev2_entry.get()) if self.rate_prev2_entry.get() else 0.0
        except ValueError:
            messagebox.showwarning("Ошибка", "Ставки должны быть числами")
            return
        is_summer = self.is_summer_var.get()
        self.result = (name, self.doc_type_var.get(), self.specialist_entry.get().strip(),
                       rate, rate_prev, rate_prev2, self.comment_text.get('1.0', 'end').strip(), is_summer)
        self.destroy()

# ---------------------- MAIN APPLICATION ----------------------
class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Астрал-групп. СО")
        self.root.geometry("1400x750")
        self.root.minsize(1100, 650)
        self.root.configure(bg='#20B2AA')  # просто цвет морской волны, без узора

        init_db()

        self.current_client = None
        self.create_notebook()
        self.create_journal_tab()
        self.create_stats_tab()
        self.create_cost_tab()
        self.refresh_client_lists()

    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

    def create_journal_tab(self):
        self.journal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.journal_frame, text="Журнал")

        # Левая панель - увеличена ширина
        left_frame = ttk.Frame(self.journal_frame, width=450)
        left_frame.pack(side='left', fill='y', padx=5, pady=5)
        left_frame.pack_propagate(False)

        # Документы в начале месяца
        begin_frame = ttk.LabelFrame(left_frame, text="Документы в начале месяца", padding=5)
        begin_frame.pack(fill='both', expand=True, pady=5)
        
        begin_list_frame = ttk.Frame(begin_frame)
        begin_list_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        scrollbar_begin_h = ttk.Scrollbar(begin_list_frame, orient='horizontal')
        scrollbar_begin_v = ttk.Scrollbar(begin_list_frame, orient='vertical')
        self.begin_listbox = tk.Listbox(begin_list_frame, height=8, bg='#E0FFFF', selectbackground='#20B2AA',
                                        xscrollcommand=scrollbar_begin_h.set, yscrollcommand=scrollbar_begin_v.set)
        scrollbar_begin_h.config(command=self.begin_listbox.xview)
        scrollbar_begin_v.config(command=self.begin_listbox.yview)
        
        self.begin_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_begin_v.pack(side='right', fill='y')
        scrollbar_begin_h.pack(side='bottom', fill='x')
        
        self.begin_listbox.bind('<<ListboxSelect>>', lambda e: self.on_client_select('begin'))
        
        btn_begin_add = ttk.Button(begin_frame, text="Добавить", command=lambda: self.add_client('begin'))
        btn_begin_add.pack(side='left', padx=5, pady=2)
        btn_begin_del = ttk.Button(begin_frame, text="Удалить", command=lambda: self.delete_client('begin'))
        btn_begin_del.pack(side='left', padx=5, pady=2)

        # Документы в конце месяца
        end_frame = ttk.LabelFrame(left_frame, text="Документы в конце месяца", padding=5)
        end_frame.pack(fill='both', expand=True, pady=5)
        
        end_list_frame = ttk.Frame(end_frame)
        end_list_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        scrollbar_end_h = ttk.Scrollbar(end_list_frame, orient='horizontal')
        scrollbar_end_v = ttk.Scrollbar(end_list_frame, orient='vertical')
        self.end_listbox = tk.Listbox(end_list_frame, height=8, bg='#E0FFFF', selectbackground='#20B2AA',
                                      xscrollcommand=scrollbar_end_h.set, yscrollcommand=scrollbar_end_v.set)
        scrollbar_end_h.config(command=self.end_listbox.xview)
        scrollbar_end_v.config(command=self.end_listbox.yview)
        
        self.end_listbox.pack(side='left', fill='both', expand=True)
        scrollbar_end_v.pack(side='right', fill='y')
        scrollbar_end_h.pack(side='bottom', fill='x')
        
        self.end_listbox.bind('<<ListboxSelect>>', lambda e: self.on_client_select('end'))
        
        btn_end_add = ttk.Button(end_frame, text="Добавить", command=lambda: self.add_client('end'))
        btn_end_add.pack(side='left', padx=5, pady=2)
        btn_end_del = ttk.Button(end_frame, text="Удалить", command=lambda: self.delete_client('end'))
        btn_end_del.pack(side='left', padx=5, pady=2)

        # Правая панель
        right_frame = ttk.Frame(self.journal_frame)
        right_frame.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Карточка клиента
        client_card = ttk.LabelFrame(right_frame, text="Данные клиента", padding=10)
        client_card.pack(fill='x', pady=5)

        self.client_name_var = tk.StringVar()
        ttk.Label(client_card, text="Клиент:").grid(row=0, column=0, sticky='w')
        ttk.Label(client_card, textvariable=self.client_name_var).grid(row=0, column=1, sticky='w', padx=5)

        ttk.Label(client_card, text="Специалист:").grid(row=1, column=0, sticky='w', pady=5)
        self.specialist_var = tk.StringVar()
        self.specialist_entry = ttk.Entry(client_card, textvariable=self.specialist_var, width=30)
        self.specialist_entry.grid(row=1, column=1, sticky='w', padx=5)
        self.specialist_entry.bind('<FocusOut>', lambda e: self.save_client_field('specialist'))
        self._enable_copy_paste(self.specialist_entry)

        ttk.Label(client_card, text="Ставка СО (руб):").grid(row=2, column=0, sticky='w', pady=5)
        self.rate_var = tk.StringVar()
        self.rate_entry = ttk.Entry(client_card, textvariable=self.rate_var, width=15)
        self.rate_entry.grid(row=2, column=1, sticky='w', padx=5)
        self.rate_entry.bind('<FocusOut>', lambda e: self.save_client_field('rate'))
        self._enable_copy_paste(self.rate_entry)

        ttk.Label(client_card, text="Ставка прошлый год:").grid(row=2, column=2, sticky='w', padx=10)
        self.rate_prev_var = tk.StringVar()
        self.rate_prev_entry = ttk.Entry(client_card, textvariable=self.rate_prev_var, width=15)
        self.rate_prev_entry.grid(row=2, column=3, sticky='w', padx=5)
        self.rate_prev_entry.bind('<FocusOut>', lambda e: self.save_client_field('rate_prev'))
        self._enable_copy_paste(self.rate_prev_entry)

        ttk.Label(client_card, text="Ставка позапрошлый год:").grid(row=2, column=4, sticky='w', padx=10)
        self.rate_prev2_var = tk.StringVar()
        self.rate_prev2_entry = ttk.Entry(client_card, textvariable=self.rate_prev2_var, width=15)
        self.rate_prev2_entry.grid(row=2, column=5, sticky='w', padx=5)
        self.rate_prev2_entry.bind('<FocusOut>', lambda e: self.save_client_field('rate_prev2'))
        self._enable_copy_paste(self.rate_prev2_entry)

        ttk.Label(client_card, text="Комментарий:").grid(row=3, column=0, sticky='nw', pady=5)
        self.comment_text = tk.Text(client_card, height=3, width=70, bg='#E0FFFF')
        self.comment_text.grid(row=3, column=1, columnspan=5, sticky='ew', padx=5, pady=5)
        self.comment_text.bind('<FocusOut>', lambda e: self.save_client_field('comment'))
        self._enable_copy_paste(self.comment_text)

        ttk.Button(client_card, text="Редактировать клиента", command=self.edit_current_client).grid(row=4, column=0, columnspan=6, pady=10)

        # Таблица месяцев
        months_frame = ttk.LabelFrame(right_frame, text="Обслуживание по месяцам", padding=5)
        months_frame.pack(fill='both', expand=True, pady=5)

        control_frame = ttk.Frame(months_frame)
        control_frame.pack(fill='x', pady=5)
        self.hide_past_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(control_frame, text="Скрыть прошедшие месяцы", variable=self.hide_past_var,
                        command=self.refresh_months_table).pack(side='left', padx=5)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background="#E0FFFF", fieldbackground="#E0FFFF", foreground="black", font=('Segoe UI', 10))
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))

        columns = ('month', 'invoice', 'act', 'docs_returned', 'visits')
        self.month_tree = ttk.Treeview(months_frame, columns=columns, show='headings', height=15, style="Treeview")
        self.month_tree.heading('month', text='Месяц')
        self.month_tree.heading('invoice', text='Счёт')
        self.month_tree.heading('act', text='Акт')
        self.month_tree.heading('docs_returned', text='Вернул доки')
        self.month_tree.heading('visits', text='Выезды')
        self.month_tree.column('month', width=140, anchor='center')
        self.month_tree.column('invoice', width=120, anchor='center')
        self.month_tree.column('act', width=120, anchor='center')
        self.month_tree.column('docs_returned', width=120, anchor='center')
        self.month_tree.column('visits', width=80, anchor='center')

        self.month_tree.bind('<Double-1>', self.on_cell_edit)

        scrollbar = ttk.Scrollbar(months_frame, orient='vertical', command=self.month_tree.yview)
        self.month_tree.configure(yscrollcommand=scrollbar.set)

        self.month_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.month_tree.tag_configure('current_month', background='#90EE90')

    def create_stats_tab(self):
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="Статистика выездов")

        client_frame = ttk.LabelFrame(stats_frame, text="Выберите клиентов (Ctrl+Shift для нескольких)", padding=10)
        client_frame.pack(fill='x', padx=10, pady=10)

        self.stats_listbox = tk.Listbox(client_frame, selectmode=tk.MULTIPLE, height=10, bg='#E0FFFF', font=('Segoe UI', 9))
        self.stats_listbox.pack(fill='x', padx=5, pady=5)

        year_frame = ttk.Frame(stats_frame)
        year_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(year_frame, text="Год:").pack(side='left', padx=5)
        self.stats_year_var = tk.StringVar(value=str(datetime.now().year))
        years = [str(y) for y in range(datetime.now().year-2, datetime.now().year+3)]
        self.stats_year_combo = ttk.Combobox(year_frame, textvariable=self.stats_year_var, values=years, width=10)
        self.stats_year_combo.pack(side='left', padx=5)
        ttk.Button(year_frame, text="Показать", command=self.update_stats).pack(side='left', padx=10)

        result_frame = ttk.LabelFrame(stats_frame, text="Результат", padding=20)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.stats_label = tk.Label(result_frame, text="", font=('Segoe Script', 14, 'bold'), fg='#00688B', bg='#F0F8FF')
        self.stats_label.pack(pady=20)

        self.refresh_stats_clients()

    def create_cost_tab(self):
        cost_frame = ttk.Frame(self.notebook)
        self.notebook.add(cost_frame, text="Стоимость выездов")

        client_frame = ttk.LabelFrame(cost_frame, text="Выберите клиентов (Ctrl+Shift для нескольких)", padding=10)
        client_frame.pack(fill='x', padx=10, pady=10)

        self.cost_listbox = tk.Listbox(client_frame, selectmode=tk.MULTIPLE, height=10, bg='#E0FFFF', font=('Segoe UI', 9))
        self.cost_listbox.pack(fill='x', padx=5, pady=5)

        btn_frame = ttk.Frame(cost_frame)
        btn_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(btn_frame, text="Рассчитать за текущий год", command=self.calculate_cost).pack(side='left', padx=5)

        result_frame = ttk.LabelFrame(cost_frame, text="Результат", padding=20)
        result_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.cost_label = tk.Label(result_frame, text="", font=('Segoe Script', 14, 'bold'), fg='#00688B', bg='#F0F8FF')
        self.cost_label.pack(pady=20)

        self.refresh_cost_clients()

    def refresh_cost_clients(self):
        clients = get_clients()
        self.cost_listbox.delete(0, tk.END)
        self.cost_clients_list = clients
        for c in clients:
            name_disp = display_name(c)
            self.cost_listbox.insert(tk.END, f"{name_disp} (ставка: {c[4]} руб)")

    def calculate_cost(self):
        selected_indices = self.cost_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Информация", "Выберите хотя бы одного клиента")
            return
        year = datetime.now().year
        client_ids = [self.cost_clients_list[i][0] for i in selected_indices]
        total_cost = get_total_cost(client_ids, year)

        if len(client_ids) == 1:
            client = self.cost_clients_list[selected_indices[0]]
            name_disp = display_name(client)
            text = f"Стоимость выездов для {name_disp} за {year} год: {total_cost:.2f} руб."
        else:
            text = f"Суммарная стоимость выездов для {len(client_ids)} клиентов за {year} год: {total_cost:.2f} руб."
        self.cost_label.config(text=text)

    def refresh_stats_clients(self):
        clients = get_clients()
        self.stats_listbox.delete(0, tk.END)
        self.clients_list = clients
        for c in clients:
            name_disp = display_name(c)
            self.stats_listbox.insert(tk.END, f"{name_disp} (спец: {c[3] if c[3] else 'не указан'})")

    def update_stats(self):
        selected_indices = self.stats_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Информация", "Выберите хотя бы одного клиента")
            return
        year = self.stats_year_var.get()
        client_ids = [self.clients_list[i][0] for i in selected_indices]
        total_visits = get_total_visits(client_ids, year)

        if len(client_ids) == 1:
            client = self.clients_list[selected_indices[0]]
            specialist = client[3] if client[3] else "специалист"
            text1 = f"Всего {specialist} за {year} год совершил {total_visits} выездов."
            text2 = f"{specialist} МОЛОДЕЦ !!!"
        else:
            text1 = f"Всего сервисными специалистами за {year} год совершено {total_visits} выездов."
            text2 = "МОЛОДЦЫ !!!"

        self.stats_label.config(text=f"{text1}\n\n{text2}")

    # ---------------------- HELPERS ----------------------
    def _enable_copy_paste(self, widget):
        def copy(event):
            widget.event_generate('<<Copy>>')
            return "break"
        def cut(event):
            widget.event_generate('<<Cut>>')
            return "break"
        def paste(event):
            widget.event_generate('<<Paste>>')
            return "break"
        widget.bind('<Control-c>', copy)
        widget.bind('<Control-x>', cut)
        widget.bind('<Control-v>', paste)

        menu = tk.Menu(widget, tearoff=0)
        menu.add_command(label="Копировать", command=lambda: widget.event_generate('<<Copy>>'))
        menu.add_command(label="Вырезать", command=lambda: widget.event_generate('<<Cut>>'))
        menu.add_command(label="Вставить", command=lambda: widget.event_generate('<<Paste>>'))
        def show_menu(e):
            menu.tk_popup(e.x_root, e.y_root)
        widget.bind('<Button-3>', show_menu)

    def refresh_client_lists(self):
        self.begin_listbox.delete(0, tk.END)
        self.end_listbox.delete(0, tk.END)

        self.begin_clients = get_clients('begin')
        self.end_clients = get_clients('end')

        for c in self.begin_clients:
            self.begin_listbox.insert(tk.END, display_name(c))
        for c in self.end_clients:
            self.end_listbox.insert(tk.END, display_name(c))

    def on_client_select(self, list_type):
        if list_type == 'begin':
            sel = self.begin_listbox.curselection()
            if sel:
                idx = sel[0]
                client = self.begin_clients[idx]
                self.load_client(client)
        else:
            sel = self.end_listbox.curselection()
            if sel:
                idx = sel[0]
                client = self.end_clients[idx]
                self.load_client(client)

    def load_client(self, client):
        self.current_client = client
        self.client_name_var.set(display_name(client))
        self.specialist_var.set(client[3] if client[3] else '')
        self.rate_var.set(str(client[4]) if client[4] else '0')
        self.rate_prev_var.set(str(client[5]) if client[5] else '0')
        self.rate_prev2_var.set(str(client[6]) if client[6] else '0')
        self.comment_text.delete('1.0', tk.END)
        self.comment_text.insert('1.0', client[7] if client[7] else '')
        self.refresh_months_table()

    def save_client_field(self, field):
        if not self.current_client:
            return
        cid = self.current_client[0]
        if field == 'specialist':
            new_val = self.specialist_var.get()
            update_client(cid, self.current_client[1], self.current_client[2], new_val,
                          self.current_client[4], self.current_client[5], self.current_client[6], self.current_client[7], self.current_client[8])
        elif field == 'rate':
            try:
                new_val = float(self.rate_var.get())
            except:
                new_val = 0.0
            update_client(cid, self.current_client[1], self.current_client[2], self.current_client[3],
                          new_val, self.current_client[5], self.current_client[6], self.current_client[7], self.current_client[8])
        elif field == 'rate_prev':
            try:
                new_val = float(self.rate_prev_var.get())
            except:
                new_val = 0.0
            update_client(cid, self.current_client[1], self.current_client[2], self.current_client[3],
                          self.current_client[4], new_val, self.current_client[6], self.current_client[7], self.current_client[8])
        elif field == 'rate_prev2':
            try:
                new_val = float(self.rate_prev2_var.get())
            except:
                new_val = 0.0
            update_client(cid, self.current_client[1], self.current_client[2], self.current_client[3],
                          self.current_client[4], self.current_client[5], new_val, self.current_client[7], self.current_client[8])
        elif field == 'comment':
            new_val = self.comment_text.get('1.0', 'end').strip()
            update_client(cid, self.current_client[1], self.current_client[2], self.current_client[3],
                          self.current_client[4], self.current_client[5], self.current_client[6], new_val, self.current_client[8])

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT * FROM clients WHERE id=?", (cid,))
        self.current_client = c.fetchone()
        conn.close()

    def edit_current_client(self):
        if not self.current_client:
            messagebox.showinfo("Информация", "Сначала выберите клиента")
            return
        dlg = ClientEditDialog(self.root, "Редактирование клиента", self.current_client)
        self.root.wait_window(dlg)
        if dlg.result:
            name, doc_type, specialist, rate, rate_prev, rate_prev2, comment, is_summer = dlg.result
            update_client(self.current_client[0], name, doc_type, specialist, rate, rate_prev, rate_prev2, comment, is_summer)
            self.refresh_client_lists()
            self.refresh_stats_clients()
            self.refresh_cost_clients()
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT * FROM clients WHERE id=?", (self.current_client[0],))
            self.current_client = c.fetchone()
            conn.close()
            self.load_client(self.current_client)

    def add_client(self, doc_list_type):
        dlg = ClientEditDialog(self.root, "Новый клиент")
        self.root.wait_window(dlg)
        if dlg.result:
            name, doc_type, specialist, rate, rate_prev, rate_prev2, comment, is_summer = dlg.result
            add_client(name, doc_type, specialist, rate, rate_prev, rate_prev2, comment, is_summer)
            self.refresh_client_lists()
            self.refresh_stats_clients()
            self.refresh_cost_clients()

    def delete_client(self, list_type):
        if list_type == 'begin':
            sel = self.begin_listbox.curselection()
            if not sel:
                return
            client = self.begin_clients[sel[0]]
        else:
            sel = self.end_listbox.curselection()
            if not sel:
                return
            client = self.end_clients[sel[0]]

        if messagebox.askyesno("Подтверждение", f"Удалить клиента {display_name(client)}?"):
            delete_client(client[0])
            if self.current_client and self.current_client[0] == client[0]:
                self.current_client = None
                self.client_name_var.set("")
                self.specialist_var.set("")
                self.rate_var.set("")
                self.rate_prev_var.set("")
                self.rate_prev2_var.set("")
                self.comment_text.delete('1.0', tk.END)
                self.month_tree.delete(*self.month_tree.get_children())
            self.refresh_client_lists()
            self.refresh_stats_clients()
            self.refresh_cost_clients()

    def refresh_months_table(self):
        if not self.current_client:
            return
        all_months = get_all_months()
        data = {row[0]: (row[1], row[2], row[3], row[4]) for row in get_monthly_data(self.current_client[0])}
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
            inv_text = self._invoice_text(inv)
            act_text = self._act_text(act)
            docs_text = self._docs_text(docs)
            month_display = format_month(m)
            item_id = self.month_tree.insert('', 'end', values=(month_display, inv_text, act_text, docs_text, visits))
            if m == current_year_month:
                self.month_tree.item(item_id, tags=('current_month',))

    def _invoice_text(self, val):
        return {0: "", 1: "Отправлен", 2: "Напечатан"}.get(val, "")
    def _act_text(self, val):
        return {0: "", 1: "Отправлен", 2: "Напечатан"}.get(val, "")
    def _docs_text(self, val):
        return {0: "Нет", 1: "Да"}.get(val, "")

    def on_cell_edit(self, event):
        if not self.current_client:
            return
        region = self.month_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.month_tree.identify_column(event.x)
        col_index = int(column[1:]) - 1
        item = self.month_tree.identify_row(event.y)
        if not item:
            return
        values = self.month_tree.item(item, 'values')
        month_display = values[0]
        month_year = None
        all_months = get_all_months()
        for m in all_months:
            if format_month(m) == month_display:
                month_year = m
                break
        if not month_year:
            return

        inv, act, docs, visits = get_monthly_data(self.current_client[0], month_year)

        if col_index == 1:
            self._show_option_menu(event, ["Отправлен", "Напечатан", "Очистить"],
                                   lambda val: self._save_cell(month_year, col_index, val, inv, act, docs, visits))
        elif col_index == 2:
            self._show_option_menu(event, ["Отправлен", "Напечатан", "Очистить"],
                                   lambda val: self._save_cell(month_year, col_index, val, inv, act, docs, visits))
        elif col_index == 3:
            self._show_option_menu(event, ["Да", "Нет", "Очистить"],
                                   lambda val: self._save_cell(month_year, col_index, val, inv, act, docs, visits))
        elif col_index == 4:
            numbers = [str(i) for i in range(1, 11)] + ["Очистить"]
            self._show_option_menu(event, numbers,
                                   lambda val: self._save_cell(month_year, col_index, val, inv, act, docs, visits))

    def _show_option_menu(self, event, options, callback):
        menu = tk.Menu(self.root, tearoff=0)
        for opt in options:
            menu.add_command(label=opt, command=lambda v=opt: callback(v))
        menu.tk_popup(event.x_root, event.y_root)

    def _save_cell(self, month_year, col_index, value, inv, act, docs, visits):
        if value == "Очистить":
            if col_index == 1:
                inv = 0
            elif col_index == 2:
                act = 0
            elif col_index == 3:
                docs = 0
            elif col_index == 4:
                visits = 0
        else:
            if col_index == 1:
                inv = 1 if value == "Отправлен" else 2 if value == "Напечатан" else 0
            elif col_index == 2:
                act = 1 if value == "Отправлен" else 2 if value == "Напечатан" else 0
            elif col_index == 3:
                docs = 1 if value == "Да" else 0
            elif col_index == 4:
                visits = int(value)
        set_monthly_data(self.current_client[0], month_year, inv, act, docs, visits)
        self.refresh_months_table()


if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()