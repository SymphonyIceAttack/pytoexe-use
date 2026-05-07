import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox


class Database:
    def __init__(self):
        self.conn = sqlite3.connect("employees.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            salary REAL,
            comment TEXT,
            hire_date TEXT,
            post TEXT,
            education TEXT
        )
        """)
        self.conn.commit()

    def add(self, name, salary, comment, hire_date, post, education):
        self.cursor.execute(
            "INSERT INTO employees (name, salary, comment, hire_date, post, education) VALUES (?, ?, ?, ?, ?, ?)",
            (name, salary, comment, hire_date, post, education)
        )
        self.conn.commit()

    def get_all(self):
        self.cursor.execute("SELECT * FROM employees")
        return self.cursor.fetchall()

    def delete(self, id):
        self.cursor.execute("DELETE FROM employees WHERE id=?", (id,))
        self.conn.commit()

    def update(self, id, name, salary, comment, hire_date, post, education):
        self.cursor.execute(
            "UPDATE employees SET name=?, salary=?, comment=?, hire_date=?, post=?, education=? WHERE id=?",
            (name, salary, comment, hire_date, post, education, id)
        )
        self.conn.commit()


class App:
    def __init__(self, root):
        self.db = Database()
        self.root = root
        self.root.title("Учёт сотрудников")

        tk.Label(root, text="Имя").grid(row=0, column=0)
        self.name = tk.Entry(root)
        self.name.grid(row=0, column=1)

        tk.Label(root, text="Зарплата").grid(row=1, column=0)
        self.salary = tk.Entry(root)
        self.salary.grid(row=1, column=1)

        tk.Label(root, text="Комментарий").grid(row=2, column=0)
        self.comment = tk.Entry(root)
        self.comment.grid(row=2, column=1)

        tk.Label(root, text="Должность").grid(row=3, column=0)
        self.post = tk.Entry(root)
        self.post.grid(row=3, column=1)

        tk.Label(root, text="Дата приёма").grid(row=4, column=0)
        self.hire_date = tk.Entry(root)
        self.hire_date.grid(row=4, column=1)

        tk.Label(root, text="Образование").grid(row=5, column=0)
        self.education = ttk.Combobox(root, values=[
            "Среднее неполное",
            "Среднее полное",
            "Высшее"
        ])
        self.education.grid(row=5, column=1)

        tk.Button(root, text="Добавить", command=self.add).grid(row=6, column=0)
        tk.Button(root, text="Изменить", command=self.update).grid(row=6, column=1)
        tk.Button(root, text="Удалить", command=self.delete).grid(row=6, column=2)

        self.tree = ttk.Treeview(
            root,
            columns=("№", "ID", "Имя", "Зарплата", "Комментарий", "Должность", "Дата", "Образование"),
            show="headings"
        )

        for col in ("№", "ID", "Имя", "Зарплата", "Комментарий", "Должность", "Дата", "Образование"):
            self.tree.heading(col, text=col)

        self.tree.grid(row=7, column=0, columnspan=3)
        self.tree.bind("<<TreeviewSelect>>", self.select)

        self.selected_id = None
        self.show()

    def show(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for index, row in enumerate(self.db.get_all(), start=1):
            self.tree.insert("", "end", values=(index, *row))

    def add(self):
        try:
            name = self.name.get().strip()
            salary = float(self.salary.get().strip().replace(',', '.'))
            comment = self.comment.get().strip()
            post = self.post.get().strip()
            hire_date = self.hire_date.get().strip()
            education = self.education.get().strip()

            self.db.add(name, salary, comment, hire_date, post, education)
            self.show()
            self.clear()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите данные")

    def delete(self):
        if self.selected_id is None:
            messagebox.showwarning("Ошибка", "Выберите сотрудника")
            return

        self.db.delete(self.selected_id)
        self.show()
        self.clear()

    def update(self):
        if self.selected_id is None:
            messagebox.showwarning("Ошибка", "Выберите сотрудника")
            return

        try:
            name = self.name.get().strip()
            salary = float(self.salary.get().strip().replace(',', '.'))
            comment = self.comment.get().strip()
            post = self.post.get().strip()
            hire_date = self.hire_date.get().strip()
            education = self.education.get().strip()

            self.db.update(self.selected_id, name, salary, comment, hire_date, post, education)
            self.show()
            self.clear()
        except ValueError:
            messagebox.showerror("Ошибка", "Введите данные")

    def select(self, event):
        item = self.tree.focus()
        data = self.tree.item(item, "values")

        if data:
            self.selected_id = int(data[1])

            self.name.delete(0, tk.END)
            self.name.insert(0, data[2])

            self.salary.delete(0, tk.END)
            self.salary.insert(0, data[3])

            self.comment.delete(0, tk.END)
            self.comment.insert(0, data[4])

            self.post.delete(0, tk.END)
            self.post.insert(0, data[6])

            self.hire_date.delete(0, tk.END)
            self.hire_date.insert(0, data[5])

            self.education.set(data[7])

    def clear(self):
        self.name.delete(0, tk.END)
        self.salary.delete(0, tk.END)
        self.comment.delete(0, tk.END)
        self.post.delete(0, tk.END)
        self.hire_date.delete(0, tk.END)
        self.education.set("")
        self.selected_id = None


root = tk.Tk()
app = App(root)
root.mainloop()