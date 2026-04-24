import sqlite3
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, simpledialog, scrolledtext
from datetime import datetime

DB_NAME = "reactives.db"

def init_db():
    """Создаёт таблицы, если их нет."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS reactives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            unit TEXT,
            initial_quantity REAL,
            current_quantity REAL,
            location TEXT,
            manufacturer TEXT,
            expiry_date TEXT,
            notes TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reactive_id INTEGER,
            operation_type TEXT,
            quantity REAL,
            date TEXT,
            notes TEXT,
            FOREIGN KEY (reactive_id) REFERENCES reactives(id) ON DELETE CASCADE
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

class ReactiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Учёт реактивов — испытательная лаборатория")
        self.root.geometry("1100x600")

        self.apply_settings()

        # Создаём меню
        menubar = tk.Menu(root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Настройки интерфейса", command=self.open_settings_dialog)
        menubar.add_cascade(label="Параметры", menu=settings_menu)

        # Пункт "Библиотека методик"
        menubar.add_command(label="Библиотека методик", command=self.open_methods_window)

        root.config(menu=menubar)

        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(self.top_frame, text="Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.top_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(self.top_frame, text="Искать", command=self.load_reactives).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(self.top_frame, text="Сброс", command=self.reset_search).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(self.top_frame)
        btn_frame.pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Добавить реактив", command=self.add_reactive).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_reactive).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_reactive).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Приход", command=self.income_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Расход", command=self.outcome_operation).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="История", command=self.show_history).pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(self.main_frame, columns=("id", "name", "unit", "current", "location", "manufacturer", "expiry"), show="headings", height=20)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Наименование")
        self.tree.heading("unit", text="Ед.изм.")
        self.tree.heading("current", text="Текущее кол-во")
        self.tree.heading("location", text="Место хранения")
        self.tree.heading("manufacturer", text="Производитель")
        self.tree.heading("expiry", text="Срок годности")
        self.tree.column("id", width=40)
        self.tree.column("name", width=250)
        self.tree.column("unit", width=60)
        self.tree.column("current", width=100)
        self.tree.column("location", width=120)
        self.tree.column("manufacturer", width=150)
        self.tree.column("expiry", width=100)
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(5, 0))

        self.load_reactives()

    def apply_settings(self):
        style = ttk.Style()
        theme = get_setting("theme", "default")
        if theme == "dark":
            style.theme_use("clam")
            bg = "#2e2e2e"
            fg = "#ffffff"
            self.root.configure(bg=bg)
            style.configure(".", background=bg, foreground=fg, fieldbackground=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TFrame", background=bg)
            style.configure("TButton", background="#444", foreground=fg)
            style.map("TButton", background=[("active", "#555")])
            style.configure("Treeview", background="#3c3c3c", foreground=fg, fieldbackground="#3c3c3c")
            style.configure("Treeview.Heading", background="#555", foreground=fg)
        elif theme == "light":
            style.theme_use("clam")
            bg = "#f0f0f0"
            fg = "#000000"
            self.root.configure(bg=bg)
            style.configure(".", background=bg, foreground=fg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TFrame", background=bg)
            style.configure("TButton", background="#e1e1e1", foreground=fg)
            style.map("TButton", background=[("active", "#c0c0c0")])
            style.configure("Treeview", background="white", foreground=fg)
            style.configure("Treeview.Heading", background="#d9d9d9", foreground=fg)
        else:
            if "vista" in style.theme_names():
                style.theme_use("vista")
            else:
                style.theme_use("default")
        scale = get_setting("font_scale", "0")
        try:
            scale = int(scale)
        except:
            scale = 0
        default_font = tkfont.nametofont("TkDefaultFont")
        new_size = default_font.cget("size") + scale
        default_font.configure(size=new_size)
        self.root.option_add("*Font", default_font)

    def open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройки интерфейса")
        dialog.geometry("400x250")
        dialog.transient(self.root)
        dialog.grab_set()

        current_theme = get_setting("theme", "default")
        current_scale = get_setting("font_scale", "0")

        ttk.Label(dialog, text="Тема оформления:").pack(pady=(10, 0))
        theme_var = tk.StringVar(value=current_theme)
        theme_combo = ttk.Combobox(dialog, textvariable=theme_var, values=["default", "light", "dark"], state="readonly")
        theme_combo.pack(pady=5)

        ttk.Label(dialog, text="Размер шрифта (от -5 до +5):").pack(pady=(10, 0))
        scale_var = tk.StringVar(value=current_scale)
        scale_spin = ttk.Spinbox(dialog, from_=-5, to=5, textvariable=scale_var, width=5)
        scale_spin.pack(pady=5)

        def save_settings():
            new_theme = theme_var.get()
            new_scale = scale_var.get()
            set_setting("theme", new_theme)
            set_setting("font_scale", new_scale)
            self.apply_settings()
            self.refresh_ui()
            dialog.destroy()
            messagebox.showinfo("Настройки", "Настройки сохранены и применены.")

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def refresh_ui(self):
        search_text = self.search_var.get()
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Menu):
                continue
            widget.destroy()
        self.__init__(self.root)
        self.search_var.set(search_text)
        self.load_reactives()

    def open_methods_window(self):
        MethodsWindow(self.root)

    def reset_search(self):
        self.search_var.set("")
        self.load_reactives()

    def load_reactives(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        search = self.search_var.get().strip()
        if search:
            cur.execute("SELECT id, name, unit, current_quantity, location, manufacturer, expiry_date FROM reactives WHERE name LIKE ? ORDER BY name",
                        (f"%{search}%",))
        else:
            cur.execute("SELECT id, name, unit, current_quantity, location, manufacturer, expiry_date FROM reactives ORDER BY name")
        rows = cur.fetchall()
        for r in rows:
            self.tree.insert("", tk.END, values=r)
        conn.close()
        self.status_var.set(f"Всего записей: {len(rows)}")

    def get_selected_reactive_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбран реактив.")
            return None
        item = self.tree.item(selected[0])
        return item['values'][0]

    def add_reactive(self):
        self._edit_reactive_dialog()

    def edit_reactive(self):
        reactive_id = self.get_selected_reactive_id()
        if reactive_id is None:
            return
        self._edit_reactive_dialog(reactive_id)

    def _edit_reactive_dialog(self, reactive_id=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Реактив" if reactive_id is None else "Редактирование реактива")
        dialog.geometry("500x450")
        dialog.transient(self.root)
        dialog.grab_set()

        labels = ["Наименование*", "Единица измерения", "Начальное количество", "Место хранения",
                  "Производитель", "Срок годности (ГГГГ-ММ-ДД)", "Примечание"]
        entries = []

        for i, label in enumerate(labels):
            ttk.Label(dialog, text=label).grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
            entry = ttk.Entry(dialog, width=50)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries.append(entry)

        if reactive_id:
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT name, unit, initial_quantity, location, manufacturer, expiry_date, notes FROM reactives WHERE id=?", (reactive_id,))
            row = cur.fetchone()
            conn.close()
            if row:
                entries[0].insert(0, row[0])
                entries[1].insert(0, row[1] or "")
                entries[2].insert(0, str(row[2]) if row[2] is not None else "")
                entries[3].insert(0, row[3] or "")
                entries[4].insert(0, row[4] or "")
                entries[5].insert(0, row[5] or "")
                entries[6].insert(0, row[6] or "")

        def save():
            name = entries[0].get().strip()
            if not name:
                messagebox.showerror("Ошибка", "Наименование обязательно!")
                return
            unit = entries[1].get().strip()
            init_qty_str = entries[2].get().strip()
            init_qty = None
            if init_qty_str:
                try:
                    init_qty = float(init_qty_str)
                except ValueError:
                    messagebox.showerror("Ошибка", "Начальное количество должно быть числом.")
                    return
            location = entries[3].get().strip()
            manufacturer = entries[4].get().strip()
            expiry = entries[5].get().strip()
            notes = entries[6].get().strip()

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            if reactive_id is None:
                cur.execute('''
                    INSERT INTO reactives (name, unit, initial_quantity, current_quantity, location, manufacturer, expiry_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, unit, init_qty, init_qty, location, manufacturer, expiry, notes))
                new_id = cur.lastrowid
                if init_qty and init_qty > 0:
                    cur.execute('''
                        INSERT INTO operations (reactive_id, operation_type, quantity, date, notes)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (new_id, 'приход', init_qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Начальный остаток"))
            else:
                cur.execute('''
                    UPDATE reactives SET name=?, unit=?, location=?, manufacturer=?, expiry_date=?, notes=?
                    WHERE id=?
                ''', (name, unit, location, manufacturer, expiry, notes, reactive_id))
            conn.commit()
            conn.close()
            self.load_reactives()
            dialog.destroy()

        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=len(labels), column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Сохранить", command=save).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=dialog.destroy).pack(side=tk.LEFT)

    def delete_reactive(self):
        reactive_id = self.get_selected_reactive_id()
        if reactive_id is None:
            return
        if messagebox.askyesno("Подтверждение", "Удалить реактив и всю историю операций?"):
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("DELETE FROM reactives WHERE id=?", (reactive_id,))
            conn.commit()
            conn.close()
            self.load_reactives()

    def _quantity_operation(self, op_type):
        reactive_id = self.get_selected_reactive_id()
        if reactive_id is None:
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT current_quantity, name FROM reactives WHERE id=?", (reactive_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return
        current_qty, name = row
        conn.close()

        title = "Приход реактива" if op_type == "приход" else "Расход реактива"
        qty_str = simpledialog.askstring(title, f"Введите количество ({op_type}):\nРеактив: {name}\nТекущий остаток: {current_qty}")
        if not qty_str:
            return
        try:
            qty = float(qty_str)
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть числом.")
            return
        if qty <= 0:
            messagebox.showerror("Ошибка", "Количество должно быть положительным.")
            return
        if op_type == "расход" and qty > current_qty:
            messagebox.showerror("Ошибка", f"Недостаточно реактива (доступно {current_qty})")
            return

        notes = simpledialog.askstring("Примечание", "Примечание (необязательно):")
        if notes is None:
            notes = ""

        new_qty = current_qty + qty if op_type == "приход" else current_qty - qty
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("UPDATE reactives SET current_quantity=? WHERE id=?", (new_qty, reactive_id))
        cur.execute('''
            INSERT INTO operations (reactive_id, operation_type, quantity, date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (reactive_id, op_type, qty, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes))
        conn.commit()
        conn.close()
        self.load_reactives()
        messagebox.showinfo("Успех", f"{op_type.capitalize()} выполнен. Новый остаток: {new_qty}")

    def income_operation(self):
        self._quantity_operation("приход")

    def outcome_operation(self):
        self._quantity_operation("расход")

    def show_history(self):
        reactive_id = self.get_selected_reactive_id()
        if reactive_id is None:
            return
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name FROM reactives WHERE id=?", (reactive_id,))
        name = cur.fetchone()[0]
        cur.execute("SELECT operation_type, quantity, date, notes FROM operations WHERE reactive_id=? ORDER BY date", (reactive_id,))
        rows = cur.fetchall()
        conn.close()

        hist_win = tk.Toplevel(self.root)
        hist_win.title(f"История операций: {name}")
        hist_win.geometry("700x400")
        tree = ttk.Treeview(hist_win, columns=("type", "qty", "date", "notes"), show="headings")
        tree.heading("type", text="Тип")
        tree.heading("qty", text="Количество")
        tree.heading("date", text="Дата")
        tree.heading("notes", text="Примечание")
        tree.column("type", width=80)
        tree.column("qty", width=100)
        tree.column("date", width=150)
        tree.column("notes", width=300)
        tree.pack(fill=tk.BOTH, expand=True)
        for r in rows:
            tree.insert("", tk.END, values=r)
        ttk.Button(hist_win, text="Закрыть", command=hist_win.destroy).pack(pady=10)


# ====================== НОВЫЙ РАЗДЕЛ: БИБЛИОТЕКА МЕТОДИК ======================

class MethodsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Библиотека методик")
        self.window.geometry("800x500")
        self.window.transient(parent)
        self.window.grab_set()

        # Основной фрейм
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Таблица со списком методик
        self.tree = ttk.Treeview(main_frame, columns=("id", "name", "created"), show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("name", text="Название методики")
        self.tree.heading("created", text="Дата создания")
        self.tree.column("id", width=40)
        self.tree.column("name", width=400)
        self.tree.column("created", width=150)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Добавить методику", command=self.add_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Редактировать", command=self.edit_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить", command=self.delete_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Просмотр", command=self.view_method).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)

        # Загружаем список методик
        self.load_methods()

        # Двойной клик для просмотра
        self.tree.bind("<Double-1>", lambda e: self.view_method())

    def load_methods(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at FROM methods ORDER BY name")
        rows = cur.fetchall()
        for r in rows:
            self.tree.insert("", tk.END, values=r)
        conn.close()

    def get_selected_method_id(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Не выбрана методика.")
            return None
        item = self.tree.item(selected[0])
        return item['values'][0]

    def add_method(self):
        MethodEditDialog(self.window, self.load_methods)

    def edit_method(self):
        method_id = self.get_selected_method_id()
        if method_id:
            MethodEditDialog(self.window, self.load_methods, method_id)

    def delete_method(self):
        method_id = self.get_selected_method_id()
        if not method_id:
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранную методику?"):
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("DELETE FROM methods WHERE id=?", (method_id,))
            conn.commit()
            conn.close()
            self.load_methods()
            messagebox.showinfo("Успех", "Методика удалена.")

    def view_method(self):
        method_id = self.get_selected_method_id()
        if method_id:
            MethodViewWindow(self.window, method_id)


class MethodEditDialog:
    def __init__(self, parent, refresh_callback, method_id=None):
        self.parent = parent
        self.refresh_callback = refresh_callback
        self.method_id = method_id

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавление методики" if method_id is None else "Редактирование методики")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Поля
        ttk.Label(self.dialog, text="Название методики:").pack(anchor=tk.W, padx=10, pady=(10, 0))
        self.name_entry = ttk.Entry(self.dialog, width=80)
        self.name_entry.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Label(self.dialog, text="Описание (текст методики):").pack(anchor=tk.W, padx=10, pady=(0, 0))
        self.text_area = scrolledtext.ScrolledText(self.dialog, wrap=tk.WORD, height=25)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Кнопки
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(btn_frame, text="Сохранить", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Если редактируем, загружаем данные
        if method_id:
            self.load_method_data()

    def load_method_data(self):
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, description FROM methods WHERE id=?", (self.method_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            self.name_entry.insert(0, row[0])
            self.text_area.insert("1.0", row[1] if row[1] else "")

    def save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Название методики обязательно!")
            return
        description = self.text_area.get("1.0", tk.END).strip()
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        if self.method_id is None:
            cur.execute("INSERT INTO methods (name, description, created_at) VALUES (?, ?, ?)",
                        (name, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        else:
            cur.execute("UPDATE methods SET name=?, description=? WHERE id=?",
                        (name, description, self.method_id))
        conn.commit()
        conn.close()
        self.refresh_callback()
        self.dialog.destroy()
        messagebox.showinfo("Успех", "Методика сохранена.")


class MethodViewWindow:
    def __init__(self, parent, method_id):
        self.parent = parent
        self.method_id = method_id

        # Получаем данные
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        cur.execute("SELECT name, description, created_at FROM methods WHERE id=?", (method_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            messagebox.showerror("Ошибка", "Методика не найдена.")
            return

        name, description, created = row

        self.window = tk.Toplevel(parent)
        self.window.title(f"Методика: {name}")
        self.window.geometry("800x600")
        self.window.transient(parent)

        # Заголовок
        ttk.Label(self.window, text=name, font=("TkDefaultFont", 14, "bold")).pack(pady=10)
        ttk.Label(self.window, text=f"Дата создания: {created}", font=("TkDefaultFont", 9)).pack(pady=(0, 10))

        # Текст
        text_frame = ttk.Frame(self.window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, state=tk.NORMAL)
        text_widget.insert("1.0", description if description else "Описание отсутствует.")
        text_widget.config(state=tk.DISABLED)  # только для чтения
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Кнопка закрыть
        ttk.Button(self.window, text="Закрыть", command=self.window.destroy).pack(pady=10)


# ====================== ЗАПУСК ======================

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = ReactiveApp(root)
    root.mainloop()