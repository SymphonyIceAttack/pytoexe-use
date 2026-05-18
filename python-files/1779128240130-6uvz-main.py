import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class DatabaseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление отделами и сотрудниками")
        self.root.geometry("800x550")

        self.conn = sqlite3.connect("main.db")
        self.create_tables()

        self.create_widgets()

        self.refresh_departments_tree()
        self.refresh_employees_tree()
        self.populate_department_combos()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
            )
        """)
        self.conn.commit()

    def execute_query(self, query, params=(), fetch=False):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        if fetch:
            result = cursor.fetchall()
        else:
            self.conn.commit()
            result = None
        return result

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.frame_dep = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_dep, text="Отделы")
        self.build_departments_tab()

        self.frame_emp = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_emp, text="Сотрудники")
        self.build_employees_tab()

    def build_departments_tab(self):
        input_frame = ttk.Frame(self.frame_dep)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Название отдела:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.dep_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.dep_name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="Добавить", command=self.add_department).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(input_frame, text="Обновить", command=self.update_department).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(input_frame, text="Удалить", command=self.delete_department).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(input_frame, text="Очистить", command=self.clear_department_fields).grid(row=0, column=5, padx=5, pady=5)

        search_frame = ttk.Frame(self.frame_dep)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(search_frame, text="Поиск по названию:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.dep_search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.dep_search_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(search_frame, text="Найти", command=self.search_departments).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(search_frame, text="Сбросить", command=self.refresh_departments_tree).grid(row=0, column=3, padx=5, pady=5)

        columns = ("id", "name")
        self.dep_tree = ttk.Treeview(self.frame_dep, columns=columns, show="headings", selectmode="browse")
        self.dep_tree.heading("id", text="ID")
        self.dep_tree.heading("name", text="Название отдела")
        self.dep_tree.column("id", width=50, anchor=tk.CENTER)
        self.dep_tree.column("name", width=200)
        self.dep_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self.frame_dep, orient=tk.VERTICAL, command=self.dep_tree.yview)
        self.dep_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.dep_tree.bind("<<TreeviewSelect>>", self.on_department_select)

    def on_department_select(self, event):
        selected = self.dep_tree.selection()
        if selected:
            values = self.dep_tree.item(selected[0], "values")
            self.dep_name_var.set(values[1])
            self.selected_dep_id = values[0]
        else:
            self.clear_department_fields()

    def clear_department_fields(self):
        self.dep_name_var.set("")
        self.selected_dep_id = None
        self.dep_tree.selection_remove(self.dep_tree.selection())

    def add_department(self):
        name = self.dep_name_var.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите название отдела")
            return
        self.execute_query("INSERT INTO departments (name) VALUES (?)", (name,))
        self.refresh_departments_tree()
        self.populate_department_combos()
        self.clear_department_fields()

    def update_department(self):
        if not hasattr(self, 'selected_dep_id') or not self.selected_dep_id:
            messagebox.showwarning("Предупреждение", "Выберите отдел для обновления")
            return
        name = self.dep_name_var.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите новое название отдела")
            return
        self.execute_query("UPDATE departments SET name=? WHERE id=?", (name, self.selected_dep_id))
        self.refresh_departments_tree()
        self.populate_department_combos()
        self.clear_department_fields()

    def delete_department(self):
        if not hasattr(self, 'selected_dep_id') or not self.selected_dep_id:
            messagebox.showwarning("Предупреждение", "Выберите отдел для удаления")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранный отдел? Сотрудники останутся без отдела."):
            self.execute_query("DELETE FROM departments WHERE id=?", (self.selected_dep_id,))
            self.refresh_departments_tree()
            self.populate_department_combos()
            self.clear_department_fields()

    def refresh_departments_tree(self):
        for row in self.dep_tree.get_children():
            self.dep_tree.delete(row)
        departments = self.execute_query("SELECT id, name FROM departments ORDER BY id", fetch=True)
        for dep in departments:
            self.dep_tree.insert("", tk.END, values=dep)

    def search_departments(self):
        search_term = self.dep_search_var.get().strip()
        if not search_term:
            self.refresh_departments_tree()
            return
        for row in self.dep_tree.get_children():
            self.dep_tree.delete(row)
        departments = self.execute_query(
            "SELECT id, name FROM departments WHERE name LIKE ? ORDER BY id",
            (f"%{search_term}%",), fetch=True
        )
        for dep in departments:
            self.dep_tree.insert("", tk.END, values=dep)

    def build_employees_tab(self):
        input_frame = ttk.Frame(self.frame_emp)
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text="Имя сотрудника:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.emp_name_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=self.emp_name_var, width=30).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Отдел:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.emp_dep_combo = ttk.Combobox(input_frame, state="readonly", width=28)
        self.emp_dep_combo.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(input_frame, text="Добавить", command=self.add_employee).grid(row=2, column=0, padx=5, pady=10)
        ttk.Button(input_frame, text="Обновить", command=self.update_employee).grid(row=2, column=1, padx=5, pady=10)
        ttk.Button(input_frame, text="Удалить", command=self.delete_employee).grid(row=2, column=2, padx=5, pady=10)
        ttk.Button(input_frame, text="Очистить", command=self.clear_employee_fields).grid(row=2, column=3, padx=5, pady=10)

        filter_frame = ttk.Frame(self.frame_emp)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(filter_frame, text="Фильтр по отделу:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.filter_dep_combo = ttk.Combobox(filter_frame, state="readonly", width=28)
        self.filter_dep_combo.grid(row=0, column=1, padx=5, pady=5)
        self.filter_dep_combo.bind("<<ComboboxSelected>>", self.apply_filter)
        ttk.Button(filter_frame, text="Показать всех", command=self.refresh_employees_tree).grid(row=0, column=2, padx=5, pady=5)

        columns = ("id", "name", "department", "dep_id")
        self.emp_tree = ttk.Treeview(self.frame_emp, columns=columns, show="headings", selectmode="browse")
        self.emp_tree.heading("id", text="ID")
        self.emp_tree.heading("name", text="Имя сотрудника")
        self.emp_tree.heading("department", text="Отдел")
        self.emp_tree.column("id", width=50, anchor=tk.CENTER)
        self.emp_tree.column("name", width=150)
        self.emp_tree.column("department", width=150)
        self.emp_tree["displaycolumns"] = ("id", "name", "department")
        self.emp_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(self.frame_emp, orient=tk.VERTICAL, command=self.emp_tree.yview)
        self.emp_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.emp_tree.bind("<<TreeviewSelect>>", self.on_employee_select)

    def on_employee_select(self, event):
        selected = self.emp_tree.selection()
        if selected:
            values = self.emp_tree.item(selected[0], "values")
            self.emp_name_var.set(values[1])  # name
            dep_id = values[3] if values[3] != "None" else None
            if dep_id is not None:
                dep_dict = getattr(self, 'departments_dict', {})
                dep_name = dep_dict.get(int(dep_id), "")
                if dep_name:
                    self.emp_dep_combo.set(dep_name)
                else:
                    self.emp_dep_combo.set("")
            else:
                self.emp_dep_combo.set("")
            self.selected_emp_id = values[0]
        else:
            self.clear_employee_fields()

    def clear_employee_fields(self):
        self.emp_name_var.set("")
        self.emp_dep_combo.set("")
        self.selected_emp_id = None
        self.emp_tree.selection_remove(self.emp_tree.selection())

    def add_employee(self):
        name = self.emp_name_var.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите имя сотрудника")
            return
        dep_name = self.emp_dep_combo.get()
        dep_id = self.get_department_id_by_name(dep_name) if dep_name else None
        self.execute_query("INSERT INTO employees (name, department_id) VALUES (?, ?)", (name, dep_id))
        self.refresh_employees_tree()
        self.clear_employee_fields()

    def update_employee(self):
        if not hasattr(self, 'selected_emp_id') or not self.selected_emp_id:
            messagebox.showwarning("Предупреждение", "Выберите сотрудника для обновления")
            return
        name = self.emp_name_var.get().strip()
        if not name:
            messagebox.showwarning("Предупреждение", "Введите имя сотрудника")
            return
        dep_name = self.emp_dep_combo.get()
        dep_id = self.get_department_id_by_name(dep_name) if dep_name else None
        self.execute_query("UPDATE employees SET name=?, department_id=? WHERE id=?", (name, dep_id, self.selected_emp_id))
        self.refresh_employees_tree()
        self.clear_employee_fields()

    def delete_employee(self):
        if not hasattr(self, 'selected_emp_id') or not self.selected_emp_id:
            messagebox.showwarning("Предупреждение", "Выберите сотрудника для удаления")
            return
        if messagebox.askyesno("Подтверждение", "Удалить выбранного сотрудника?"):
            self.execute_query("DELETE FROM employees WHERE id=?", (self.selected_emp_id,))
            self.refresh_employees_tree()
            self.clear_employee_fields()

    def refresh_employees_tree(self, department_id=None):
        for row in self.emp_tree.get_children():
            self.emp_tree.delete(row)
        if department_id is not None:
            query = """
                SELECT e.id, e.name, IFNULL(d.name, 'Без отдела') as department, e.department_id
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                WHERE e.department_id = ?
                ORDER BY e.id
            """
            employees = self.execute_query(query, (department_id,), fetch=True)
        else:
            query = """
                SELECT e.id, e.name, IFNULL(d.name, 'Без отдела') as department, e.department_id
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                ORDER BY e.id
            """
            employees = self.execute_query(query, fetch=True)
        for emp in employees:
            self.emp_tree.insert("", tk.END, values=emp)

    def apply_filter(self, event=None):
        dep_name = self.filter_dep_combo.get()
        if dep_name == "Все" or dep_name == "":
            self.refresh_employees_tree()
        else:
            dep_id = self.get_department_id_by_name(dep_name)
            self.refresh_employees_tree(department_id=dep_id)

    def get_department_id_by_name(self, name):
        result = self.execute_query("SELECT id FROM departments WHERE name=?", (name,), fetch=True)
        return result[0][0] if result else None

    def populate_department_combos(self):
        departments = self.execute_query("SELECT id, name FROM departments ORDER BY name", fetch=True)
        dep_names = [dep[1] for dep in departments]
        self.departments_dict = {dep[0]: dep[1] for dep in departments}

        self.emp_dep_combo['values'] = dep_names
        self.filter_dep_combo['values'] = ["Все"] + dep_names
        if self.filter_dep_combo.get() == "":
            self.filter_dep_combo.set("Все")

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseApp(root)
    root.mainloop()