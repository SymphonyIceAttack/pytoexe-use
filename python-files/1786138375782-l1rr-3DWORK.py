import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import textwrap
import csv

class Form1(tk.Tk):
    def __init__(self):
        super().__init__()
        self.state('zoomed')
        self.title("3DWORK — Учёт заказов и расходов")
        self.geometry("1920x900")
        self.resizable(True, True)

        self.db_path = "orders.db"
        self.setup_database()

        self.setup_styles()
        self.create_variables()
        self.create_widgets()
        
        # Инициализация при старте
        self.refresh_orders_table()
        self.refresh_expenses_table()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Таблица заказов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_name TEXT,
                contact_info TEXT,
                order_number TEXT,
                description TEXT,
                status TEXT,
                cost REAL,
                receive_date TEXT,
                due_date TEXT
            )
        """)
        # Таблица расходов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                description TEXT,
                cost REAL,
                status TEXT,
                date TEXT
            )
        """)
        conn.commit()
        conn.close()

    def db_execute(self, query, params=()):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith("SELECT"):
                result = cursor.fetchall()
            else:
                conn.commit()
                result = []
            conn.close()
            return result
        except Exception as e:
            messagebox.showerror("Ошибка БД", str(e))
            return []

    def setup_styles(self):
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        bg = "#335894"
        fg = "#1f2933"
        accent = "#9ecaff"
        self.configure(bg=bg)
        base_font = ("Segoe UI", 10)
        style.configure(".", background=bg, foreground=fg, font=base_font)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TButton", padding=(10, 4), relief="flat", anchor="center", background="#e4e7eb", foreground=fg)
        style.map("TButton", background=[("active", "#d2d6dc"), ("disabled", "#eceef0")])
        style.configure("Accent.TButton", padding=(10, 4), relief="flat", anchor="center", background=accent, foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", accent), ("disabled", "#9fb6cc")], foreground=[("disabled", "#eef2f6")])
        style.configure("TEntry", padding=4, fieldbackground="#ffffff")
        style.configure("TCombobox", padding=4, fieldbackground="#ffffff")
        style.configure("Treeview", rowheight=25, fieldbackground=bg, background="#ffffff", foreground=fg)
        style.configure("Treeview.Heading", background=bg, foreground="#ffffff", font=("Segoe UI", 11, "bold"))

    def create_variables(self):
        # Переменные для заказов
        self.combobox1_var = tk.StringVar(value="В очереди")
        self.current_row_id = None
        self.filter_month_var = tk.StringVar()
        self.filter_status_var = tk.StringVar(value="Все")

        # Переменные для расходов
        self.exp_combobox_var = tk.StringVar(value="Заказать")
        self.exp_current_id = None
        self.exp_filter_month_var = tk.StringVar()
        self.exp_filter_status_var = tk.StringVar(value="Все")

    @staticmethod
    def wrap_text(text, width):
        if not text: return ""
        return "\n".join(textwrap.wrap(str(text), width=width))

    def create_widgets(self):
        # =========================================================
        # БЛОК 1: ФОРМА ЗАКАЗОВ (слева сверху)
        # =========================================================
        ttk.Label(self, text="📦 ЗАКАЗЫ (Доходы)", font=("Segoe UI", 14, "bold"), foreground="#ffffff").place(x=25, y=25)

        self.label1 = ttk.Label(self, text="Название заказа", anchor="w", justify="left", style="TLabel")
        self.label1.place(x=25, y=60, width=165, height=25)
        self.entry1 = ttk.Entry(self)
        self.entry1.place(x=25, y=90, width=600, height=30)

        self.label8 = ttk.Label(self, text="Контактная информация", anchor="w", justify="left", style="TLabel")
        self.label8.place(x=25, y=125, width=250, height=25)
        self.text2 = tk.Text(self, wrap="word", relief="flat", highlightthickness=1, highlightbackground="#cbd2d9", highlightcolor="#9ecaff", bg="#ffffff", font=("Segoe UI", 10))
        self.text2.place(x=25, y=155, width=250, height=50)

        self.label10 = ttk.Label(self, text="№", anchor="w", justify="left", style="TLabel")
        self.label10.place(x=330, y=125, width=50, height=25)
        self.entry5 = ttk.Entry(self)
        self.entry5.place(x=325, y=155, width=80, height=25)

        self.label2 = ttk.Label(self, text="Описание", anchor="w", justify="left", style="TLabel")
        self.label2.place(x=25, y=210, width=110, height=25)
        self.text1 = tk.Text(self, wrap="word", relief="flat", highlightthickness=1, highlightbackground="#cbd2d9", highlightcolor="#9ecaff", bg="#ffffff", font=("Segoe UI", 10))
        self.text1.place(x=25, y=240, width=600, height=150)

        self.label3 = ttk.Label(self, text="Стоимость", anchor="w", justify="left", style="TLabel")
        self.label3.place(x=25, y=400, width=105, height=25)
        self.entry2 = ttk.Entry(self, justify="center")
        self.entry2.place(x=25, y=430, width=105, height=25)
        self.label5 = ttk.Label(self, text="руб.", anchor="w", justify="left", style="TLabel")
        self.label5.place(x=135, y=430, width=70, height=25)

        self.entry3 = ttk.Entry(self, justify="center")
        self.entry3.place(x=230, y=430, width=160, height=25)
        self.label6 = ttk.Label(self, text="Дата получения", anchor="w", justify="left", style="TLabel")
        self.label6.place(x=230, y=400, width=160, height=25)

        self.combobox1 = ttk.Combobox(self, textvariable=self.combobox1_var)
        self.combobox1.place(x=495, y=155, width=95, height=25)
        self.combobox1["values"] = ("В очереди", "В работе", "Готов", "Выдан", "Отменен")
        self.label7 = ttk.Label(self, text="Статус", anchor="w", justify="left", style="TLabel")
        self.label7.place(x=495, y=125, width=70, height=25)

        self.entry4 = ttk.Entry(self, justify="center")
        self.entry4.place(x=455, y=430, width=170, height=25)
        self.label9 = ttk.Label(self, text="Дата исполнения", anchor="w", justify="left", style="TLabel")
        self.label9.place(x=455, y=400, width=170, height=25)

        # Кнопки заказов
        self.btn_save = ttk.Button(self, text="Сохранить заказ", command=self.save_order)
        self.btn_save.place(x=25, y=500, width=140, height=35)
        self.btn_refresh = ttk.Button(self, text="Обновить таблицу", command=self.refresh_orders_table)
        self.btn_refresh.place(x=180, y=500, width=150, height=35)
        self.btn_delete = ttk.Button(self, text="Удалить запись", command=self.delete_order)
        self.btn_delete.place(x=345, y=500, width=150, height=35)
        self.btn_clear_ord = ttk.Button(self, text="Очистить форму", command=self.clear_form)
        self.btn_clear_ord.place(x=510, y=500, width=140, height=35)

        # Панель фильтров заказов
        filter_frame_ord = ttk.Frame(self, style="TFrame")
        filter_frame_ord.place(x=750, y=60, width=725, height=40)
        ttk.Label(filter_frame_ord, text="Месяц (ММ.ГГГГ):", style="TLabel").place(x=10, y=10, width=130, height=25)
        self.entry_filter_month = ttk.Entry(filter_frame_ord, textvariable=self.filter_month_var, width=12)
        self.entry_filter_month.place(x=145, y=10, width=80, height=25)
        ttk.Label(filter_frame_ord, text="Статус:", style="TLabel").place(x=240, y=10, width=60, height=25)
        self.combo_filter_status = ttk.Combobox(filter_frame_ord, textvariable=self.filter_status_var, width=15)
        self.combo_filter_status["values"] = ("Все", "В очереди", "В работе", "Готов", "Выдан", "Отменен")
        self.combo_filter_status.place(x=305, y=10, width=120, height=25)
        self.btn_apply_filter = ttk.Button(filter_frame_ord, text="Фильтр", command=self.refresh_orders_table)
        self.btn_apply_filter.place(x=440, y=10, width=80, height=30)
        self.btn_export_ord = ttk.Button(filter_frame_ord, text="Экспорт CSV", command=self.export_orders_csv)
        self.btn_export_ord.place(x=535, y=10, width=120, height=30)

        self.lbl_total_cost = ttk.Label(self, text="Итого стоимость: 0 руб.", style="TLabel", font=("Segoe UI", 11, "bold"))
        self.lbl_total_cost.place(x=750, y=110, width=300, height=25)

        # Таблица заказов
        columns_ord = ("id", "order_name", "contact_info", "order_number", "description", "status", "cost", "receive_date", "due_date")
        headings_ord = ("ID", "Заказ", "Контакт", "№", "Описание", "Статус", "Стоимость", "Дата получения", "Дата исполнения")
        self.tree = ttk.Treeview(self, columns=columns_ord, show="headings", selectmode="browse")
        for col, head in zip(columns_ord, headings_ord):
            self.tree.heading(col, text=head)
            self.tree.column(col, width=100, anchor="center")
        self.tree.column("id", width=25, anchor="c") #Размер и положение ID
        self.tree.column("order_number", width=30, anchor="c") #Размер и положение №
        self.tree.column("order_name", width=180, anchor="w")
        self.tree.column("description", width=160, anchor="w")
        self.tree.column("status", width=80, anchor="c") #Размер и положение №       
        self.tree.column("cost", width=90, anchor="c")
        scrollbar_ord = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_ord.set)
        self.tree.place(x=750, y=140, width=1090, height=300)
        scrollbar_ord.place(x=1840, y=140, height=300)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)


        # =========================================================
        # БЛОК 2: ФОРМА РАСХОДОВ (слева снизу)
        # =========================================================
        ttk.Label(self, text="💸 Закупки/Услуги (Расходы)", font=("Segoe UI", 14, "bold"), foreground="#ffffff").place(x=25, y=610)

        lbl_exp_name = ttk.Label(self, text="Название товара/услуги", anchor="w", justify="left", style="TLabel")
        lbl_exp_name.place(x=25, y=650, width=180, height=25)
        self.entry_exp_name = ttk.Entry(self)
        self.entry_exp_name.place(x=25, y=680, width=400, height=30)

        lbl_exp_desc = ttk.Label(self, text="Описание", anchor="w", justify="left", style="TLabel")
        lbl_exp_desc.place(x=25, y=715, width=110, height=25)
        self.text_exp_desc = tk.Text(self, wrap="word", relief="flat", highlightthickness=1, highlightbackground="#cbd2d9", highlightcolor="#9ecaff", bg="#ffffff", font=("Segoe UI", 10))
        self.text_exp_desc.place(x=25, y=745, width=400, height=80)

        lbl_exp_cost = ttk.Label(self, text="Стоимость", anchor="w", justify="left", style="TLabel")
        lbl_exp_cost.place(x=450, y=715, width=105, height=25)
        self.entry_exp_cost = ttk.Entry(self, justify="center")
        self.entry_exp_cost.place(x=450, y=745, width=105, height=25)
        lbl_exp_rub = ttk.Label(self, text="руб.", anchor="w", justify="left", style="TLabel")
        lbl_exp_rub.place(x=560, y=745, width=70, height=25)

        lbl_exp_status = ttk.Label(self, text="Статус", anchor="w", justify="left", style="TLabel")
        lbl_exp_status.place(x=450, y=650, width=105, height=25)
        self.exp_combobox = ttk.Combobox(self, textvariable=self.exp_combobox_var)
        self.exp_combobox.place(x=450, y=680, width=105, height=25)
        self.exp_combobox["values"] = ("Заказать", "В пути", "Получено", "Отменено")

        lbl_exp_date = ttk.Label(self, text="Дата", anchor="w", justify="left", style="TLabel")
        lbl_exp_date.place(x=570, y=650, width=80, height=25)
        self.entry_exp_date = ttk.Entry(self, justify="center")
        self.entry_exp_date.place(x=570, y=680, width=100, height=25)

        # Кнопки расходов
        self.btn_save_exp = ttk.Button(self, text="Сохранить расход", command=self.save_expense)
        self.btn_save_exp.place(x=25, y=890, width=140, height=35)
        self.btn_refresh_exp = ttk.Button(self, text="Обновить таблицу", command=self.refresh_expenses_table)
        self.btn_refresh_exp.place(x=180, y=890, width=150, height=35)
        self.btn_delete_exp = ttk.Button(self, text="Удалить запись", command=self.delete_expense)
        self.btn_delete_exp.place(x=345, y=890, width=150, height=35)
        self.btn_clear_exp = ttk.Button(self, text="Очистить форму", command=self.clear_expense_form)
        self.btn_clear_exp.place(x=510, y=890, width=140, height=35)

        # Панель фильтров расходов
        filter_frame_exp = ttk.Frame(self, style="TFrame")
        filter_frame_exp.place(x=750, y=610, width=725, height=40)
        ttk.Label(filter_frame_exp, text="Месяц (ММ.ГГГГ):", style="TLabel").place(x=10, y=10, width=130, height=25)
        self.entry_exp_filter_month = ttk.Entry(filter_frame_exp, textvariable=self.exp_filter_month_var, width=12)
        self.entry_exp_filter_month.place(x=145, y=10, width=80, height=25)
        ttk.Label(filter_frame_exp, text="Статус:", style="TLabel").place(x=240, y=10, width=60, height=25)
        self.combo_exp_filter_status = ttk.Combobox(filter_frame_exp, textvariable=self.exp_filter_status_var, width=15)
        self.combo_exp_filter_status["values"] = ("Все", "Заказать", "В пути", "Получено", "Отменено")
        self.combo_exp_filter_status.place(x=305, y=10, width=120, height=25)
        self.btn_apply_exp_filter = ttk.Button(filter_frame_exp, text="Фильтр", command=self.refresh_expenses_table)
        self.btn_apply_exp_filter.place(x=440, y=10, width=80, height=30)
        self.btn_export_exp = ttk.Button(filter_frame_exp, text="Экспорт CSV", command=self.export_expenses_csv)
        self.btn_export_exp.place(x=535, y=10, width=120, height=30)

        self.lbl_total_exp_cost = ttk.Label(self, text="Итого расходы: 0 руб.", style="TLabel", font=("Segoe UI", 11, "bold"))
        self.lbl_total_exp_cost.place(x=750, y=660, width=300, height=25)

        # Таблица расходов
        columns_exp = ("id", "item_name", "description", "cost", "status", "date")
        headings_exp = ("ID", "Товар/услуга", "Описание", "Стоимость", "Статус", "Дата")
        self.tree_exp = ttk.Treeview(self, columns=columns_exp, show="headings", selectmode="browse")
        for col, head in zip(columns_exp, headings_exp):
            self.tree_exp.heading(col, text=head)
            self.tree_exp.column(col, width=100, anchor="center")
        self.tree_exp.column("item_name", width=200, anchor="w")
        self.tree_exp.column("description", width=220, anchor="w")
        self.tree_exp.column("cost", width=90, anchor="c")
        scrollbar_exp = ttk.Scrollbar(self, orient="vertical", command=self.tree_exp.yview)
        self.tree_exp.configure(yscrollcommand=scrollbar_exp.set)
        self.tree_exp.place(x=750, y=690, width=1090, height=300)
        scrollbar_exp.place(x=1840, y=690, height=300)
        self.tree_exp.bind("<<TreeviewSelect>>", self.on_tree_exp_select)

        #Чистая прибыль
        self.lbl_net_profit = ttk.Label(
            self,
            text="Чистая прибыль: 0 руб.",
            style="TLabel",
            font=("Segoe UI", 11, "bold"),
            foreground="#4caf50"  # зелёный
        )
        # Важно: поставь y так, чтобы не наезжало на таблицу расходов.
        # Если таблица расходов у тебя с y=640, поставь метку на y=615
        self.lbl_net_profit.place(x=750, y=550, width=300, height=25)


    # ---------------------------------------------------------
    # Логика заказов
    # ---------------------------------------------------------

    def update_net_profit(self):
        import re

        def get_amount(label):
            text = label.cget("text")
            # Ищем первое число в тексте метки (например, «Итого стоимость: 1234.56 руб.»)
            match = re.search(r"[-+]?\d+\.?\d*", text)
            return float(match.group()) if match else 0.0

        income = get_amount(self.lbl_total_cost)      # Итого доходов
        expenses = get_amount(self.lbl_total_exp_cost) # Итого расходов
        profit = income - expenses

        color = "#4caf50" if profit >= 0 else "#f44336"  # зелёный/красный

        self.lbl_net_profit.config(
            text=f"Чистая прибыль: {profit:.2f} руб.",
            foreground=color
        )


    def save_order(self):
        order_name = self.entry1.get().strip()
        contact_info = self.text2.get("1.0", tk.END).strip()
        order_number = self.entry5.get().strip()
        description = self.text1.get("1.0", tk.END).strip()
        status = self.combobox1_var.get()
        cost_str = self.entry2.get().strip().replace(",", ".")
        receive_date = self.entry3.get().strip()
        due_date = self.entry4.get().strip()

        if not order_name:
            messagebox.showwarning("Внимание", "Укажите название заказа")
            return

        try:
            cost = float(cost_str) if cost_str else 0.0
        except ValueError:
            messagebox.showerror("Ошибка", "Стоимость должна быть числом")
            return

        if self.current_row_id:
            # Обновление
            query = """
                UPDATE orders SET order_name=?, contact_info=?, order_number=?, description=?,
                status=?, cost=?, receive_date=?, due_date=? WHERE id=?
            """
            params = (order_name, contact_info, order_number, description, status, cost, receive_date, due_date, self.current_row_id)
        else:
            # Вставка
            query = """
                INSERT INTO orders (order_name, contact_info, order_number, description, status, cost, receive_date, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (order_name, contact_info, order_number, description, status, cost, receive_date, due_date)

        self.db_execute(query, params)
        self.clear_form()
        self.refresh_orders_table()
        self.update_net_profit()


    def delete_order(self):
        if self.current_row_id is None:
            messagebox.showinfo("Инфо", "Выберите заказ в таблице")
            return
        if messagebox.askyesno("Подтверждение", "Удалить заказ?"):
            self.db_execute("DELETE FROM orders WHERE id=?", (self.current_row_id,))
            self.clear_form()
            self.refresh_orders_table()
            self.update_net_profit()


    def clear_form(self):
        self.entry1.delete(0, tk.END)
        self.text2.delete("1.0", tk.END)
        self.entry5.delete(0, tk.END)
        self.text1.delete("1.0", tk.END)
        self.entry2.delete(0, tk.END)
        self.entry3.delete(0, tk.END)
        self.entry4.delete(0, tk.END)
        self.combobox1_var.set("В очереди")
        self.current_row_id = None

    def on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            values = item["values"]
            self.current_row_id = values[0]
            self.entry1.delete(0, tk.END); self.entry1.insert(0, values[1])
            self.text2.delete("1.0", tk.END); self.text2.insert("1.0", values[2])
            self.entry5.delete(0, tk.END); self.entry5.insert(0, values[3])
            self.text1.delete("1.0", tk.END); self.text1.insert("1.0", values[4])
            self.combobox1_var.set(values[5])
            self.entry2.delete(0, tk.END); self.entry2.insert(0, str(values[6]))
            self.entry3.delete(0, tk.END); self.entry3.insert(0, values[7])
            self.entry4.delete(0, tk.END); self.entry4.insert(0, values[8])

    def refresh_orders_table(self):
        month = self.filter_month_var.get().strip()
        status = self.filter_status_var.get()

        query = "SELECT * FROM orders"
        params = ()
        if month and status != "Все":
            query += " WHERE receive_date LIKE ? AND status = ?"
            params = (f"%{month}%", status)
        elif month:
            query += " WHERE receive_date LIKE ?"
            params = (f"%{month}%",)
        elif status != "Все":
            query += " WHERE status = ?"
            params = (status,)

        rows = self.db_execute(query, params)

        for item in self.tree.get_children():
            self.tree.delete(item)

        total = 0
        for row in rows:
            self.tree.insert("", tk.END, values=row)
            total += row[6]  # cost

        self.lbl_total_cost.config(text=f"Итого стоимость: {total:.2f} руб.")
        self.update_net_profit()


    def export_orders_csv(self):
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filename:
            return
        rows = self.db_execute("SELECT * FROM orders")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "order_name", "contact_info", "order_number", "description", "status", "cost", "receive_date", "due_date"])
            writer.writerows(rows)
        messagebox.showinfo("Успех", "Заказы экспортированы в CSV")

    # ---------------------------------------------------------
    # Логика расходов
    # ---------------------------------------------------------
    def save_expense(self):
        item_name = self.entry_exp_name.get().strip()
        description = self.text_exp_desc.get("1.0", tk.END).strip()
        cost_str = self.entry_exp_cost.get().strip().replace(",", ".")
        status = self.exp_combobox_var.get()
        date = self.entry_exp_date.get().strip()

        if not item_name:
            messagebox.showwarning("Внимание", "Укажите название товара/услуги")
            return

        try:
            cost = float(cost_str) if cost_str else 0.0
        except ValueError:
            messagebox.showerror("Ошибка", "Стоимость должна быть числом")
            return

        if self.exp_current_id:
            query = """
                UPDATE expenses SET item_name=?, description=?, cost=?, status=?, date=? WHERE id=?
            """
            params = (item_name, description, cost, status, date, self.exp_current_id)
        else:
            query = """
                INSERT INTO expenses (item_name, description, cost, status, date)
                VALUES (?, ?, ?, ?, ?)
            """
            params = (item_name, description, cost, status, date)

        self.db_execute(query, params)
        self.clear_expense_form()
        self.refresh_expenses_table()
        self.update_net_profit()

    def delete_expense(self):
        if self.exp_current_id is None:
            messagebox.showinfo("Инфо", "Выберите расход в таблице")
            return
        if messagebox.askyesno("Подтверждение", "Удалить расход?"):
            self.db_execute("DELETE FROM expenses WHERE id=?", (self.exp_current_id,))
            self.clear_expense_form()
            self.refresh_expenses_table()
            self.update_net_profit()

    def clear_expense_form(self):
        self.entry_exp_name.delete(0, tk.END)
        self.text_exp_desc.delete("1.0", tk.END)
        self.entry_exp_cost.delete(0, tk.END)
        self.exp_combobox_var.set("заказать")
        self.entry_exp_date.delete(0, tk.END)
        self.exp_current_id = None

    def on_tree_exp_select(self, event):
        selected = self.tree_exp.selection()
        if selected:
            item = self.tree_exp.item(selected[0])
            values = item["values"]
            self.exp_current_id = values[0]
            self.entry_exp_name.delete(0, tk.END); self.entry_exp_name.insert(0, values[1])
            self.text_exp_desc.delete("1.0", tk.END); self.text_exp_desc.insert("1.0", values[2])
            self.entry_exp_cost.delete(0, tk.END); self.entry_exp_cost.insert(0, str(values[3]))
            self.exp_combobox_var.set(values[4])
            self.entry_exp_date.delete(0, tk.END); self.entry_exp_date.insert(0, values[5])

    def refresh_expenses_table(self):
        month = self.exp_filter_month_var.get().strip()
        status = self.exp_filter_status_var.get()

        query = "SELECT * FROM expenses"
        params = ()
        if month and status != "Все":
            query += " WHERE date LIKE ? AND status = ?"
            params = (f"%{month}%", status)
        elif month:
            query += " WHERE date LIKE ?"
            params = (f"%{month}%",)
        elif status != "Все":
            query += " WHERE status = ?"
            params = (status,)

        rows = self.db_execute(query, params)

        for item in self.tree_exp.get_children():
            self.tree_exp.delete(item)

        total = 0
        for row in rows:
            self.tree_exp.insert("", tk.END, values=row)
            total += row[3]  # cost

        self.lbl_total_exp_cost.config(text=f"Итого расходы: {total:.2f} руб.")
        self.update_net_profit()


    def export_expenses_csv(self):
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filename:
            return
        rows = self.db_execute("SELECT * FROM expenses")
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "item_name", "description", "cost", "status", "date"])
            writer.writerows(rows)
        messagebox.showinfo("Успех", "Расходы экспортированы в CSV")


if __name__ == "__main__":
    app = Form1()
    app.mainloop()
