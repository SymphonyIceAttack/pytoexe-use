import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Библиотека")
        self.root.geometry("800x600")

        # Соединение с базой данных SQLite
        self.conn = sqlite3.connect('library.db', check_same_thread=False)
        self.create_tables()
        self.load_data()

        # Основной контейнер Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True)

        # Первая вкладка: Каталог книг
        self.catalog_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.catalog_tab, text='Каталог книг')
        self.create_catalog_widgets()

        # Вторая вкладка: Выданные книги
        self.issued_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.issued_tab, text='Выданные книги')
        self.create_issued_widgets()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                title TEXT PRIMARY KEY,
                quantity INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS issued_books (
                title TEXT PRIMARY KEY,
                borrower TEXT,
                FOREIGN KEY(title) REFERENCES books(title)
            )
        ''')
        self.conn.commit()

    def load_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM books")
        self.books = dict(cursor.fetchall())  # Словарь: название книги => количество

        cursor.execute("SELECT * FROM issued_books")
        self.issued_books = {row[0]: row[1] for row in cursor.fetchall()}  # Словарь: название книги => читатель

    def save_data(self):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM books")
        cursor.execute("DELETE FROM issued_books")

        for title, quantity in self.books.items():
            cursor.execute("INSERT INTO books VALUES (?, ?)", (title, quantity))

        for title, borrower in self.issued_books.items():
            cursor.execute("INSERT INTO issued_books VALUES (?, ?)", (title, borrower))

        self.conn.commit()

    def create_catalog_widgets(self):
        tab = self.catalog_tab

        # Панель поиска
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill='x', pady=10)

        ttk.Label(search_frame, text="Поиск:").pack(side='left')
        self.search_var = tk.StringVar(value='')
        self.search_var.trace_add('write', self.filter_books)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side='left', padx=5)

        # Список книг
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.books_listbox = tk.Listbox(list_frame, width=70, height=20, font=('Arial', 12))
        self.books_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.books_listbox.yview)
        self.books_listbox.config(yscrollcommand=scrollbar.set)

        self.update_books_list()

        # Форма добавления книги
        add_frame = ttk.Frame(tab)
        add_frame.pack(fill='x', pady=10)

        ttk.Label(add_frame, text="Название книги:", width=20).grid(row=0, column=0, sticky='e')
        self.new_title_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_title_var, width=40).grid(row=0, column=1, padx=5)

        ttk.Label(add_frame, text="Количество:", width=20).grid(row=1, column=0, sticky='e')
        self.quantity_var = tk.IntVar(value=1)
        ttk.Spinbox(add_frame, from_=1, to=100, textvariable=self.quantity_var, width=5).grid(row=1, column=1, sticky='w', padx=5)

        ttk.Button(add_frame, text="Добавить книгу", command=self.add_book).grid(row=2, columnspan=2, pady=10)

    def filter_books(self, *args):
        search_term = self.search_var.get().strip().lower()
        self.books_listbox.delete(0, tk.END)
        for title, quantity in self.books.items():
            if search_term in title.lower():
                self.books_listbox.insert(tk.END, f'{title} ({quantity} шт.)')

    def update_books_list(self):
        self.books_listbox.delete(0, tk.END)
        for title, quantity in self.books.items():
            self.books_listbox.insert(tk.END, f'{title} ({quantity} шт.)')

    def add_book(self):
        title = self.new_title_var.get().strip()
        quantity = self.quantity_var.get()

        if not title:
            messagebox.showwarning("Внимание", "Необходимо заполнить название книги!")
            return

        if title in self.books:
            self.books[title] += quantity
        else:
            self.books[title] = quantity

        self.save_data()
        self.update_books_list()
        messagebox.showinfo("Готово", f"Книга '{title}' добавлена в каталог.")

    def create_issued_widgets(self):
        tab = self.issued_tab

        # Панель поиска выданных книг
        search_frame = ttk.Frame(tab)
        search_frame.pack(fill='x', pady=10)

        ttk.Label(search_frame, text="Поиск выданных:").pack(side='left')
        self.issued_search_var = tk.StringVar(value='')
        self.issued_search_var.trace_add('write', self.filter_issued_books)
        search_entry = ttk.Entry(search_frame, textvariable=self.issued_search_var, width=40)
        search_entry.pack(side='left', padx=5)

        # Список выданных книг
        list_frame = ttk.Frame(tab)
        list_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')

        self.issued_listbox = tk.Listbox(list_frame, width=70, height=20, font=('Arial', 12))
        self.issued_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.issued_listbox.yview)
        self.issued_listbox.config(yscrollcommand=scrollbar.set)

        self.update_issued_list()

        # Форма выдачи и возврата книг
        action_frame = ttk.Frame(tab)
        action_frame.pack(fill='x', pady=10)

        ttk.Label(action_frame, text="Название книги:", width=20).grid(row=0, column=0, sticky='e')
        self.borrow_title_var = tk.StringVar()
        ttk.Entry(action_frame, textvariable=self.borrow_title_var, width=40).grid(row=0, column=1, padx=5)

        ttk.Label(action_frame, text="Читатель:", width=20).grid(row=1, column=0, sticky='e')
        self.borrow_user_var = tk.StringVar()
        ttk.Entry(action_frame, textvariable=self.borrow_user_var, width=40).grid(row=1, column=1, padx=5)

        ttk.Button(action_frame, text="Выдать книгу", command=self.lend_book).grid(row=2, column=0, pady=10)
        ttk.Button(action_frame, text="Возврат книги", command=self.return_book).grid(row=2, column=1, pady=10)

    def filter_issued_books(self, *args):
        search_term = self.issued_search_var.get().strip().lower()
        self.issued_listbox.delete(0, tk.END)
        for title, borrower in self.issued_books.items():
            if search_term in title.lower():
                self.issued_listbox.insert(tk.END, f'{title} (у {borrower})')

    def update_issued_list(self):
        self.issued_listbox.delete(0, tk.END)
        for title, borrower in self.issued_books.items():
            self.issued_listbox.insert(tk.END, f'{title} (у {borrower})')

    def lend_book(self):
        title = self.borrow_title_var.get().strip()
        borrower = self.borrow_user_var.get().strip()

        if not title or not borrower:
            messagebox.showwarning("Внимание", "Необходимо заполнить все поля!")
            return

        if title not in self.books:
            messagebox.showerror("Ошибка", f"Книга '{title}' отсутствует в каталоге.")
            return

        if self.books[title] == 0:
            messagebox.showerror("Ошибка", f"Все экземпляры книги '{title}' уже выданы.")
            return

        if title in self.issued_books:
            messagebox.showerror("Ошибка", f"Книга '{title}' уже выдана читателю {self.issued_books[title]}.")
            return

        self.books[title] -= 1
        self.issued_books[title] = borrower

        self.save_data()
        self.update_books_list()
        self.update_issued_list()
        messagebox.showinfo("Готово", f"Книга '{title}' выдана читателю {borrower}.")

    def return_book(self):
        title = self.borrow_title_var.get().strip()

        if not title:
            messagebox.showwarning("Внимание", "Необходимо указать название книги!")
            return

        if title not in self.issued_books:
            messagebox.showerror("Ошибка", f"Книга '{title}' не была выдана.")
            return

        borrower = self.issued_books.pop(title)
        self.books[title] += 1

        self.save_data()
        self.update_books_list()
        self.update_issued_list()
        messagebox.showinfo("Готово", f"Книга '{title}', выданная читателю {borrower}, возвращена в библиотеку.")


if __name__ == "__main__":
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()
