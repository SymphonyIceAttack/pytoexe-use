import re
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

DB_NAME = "contacts.db"
DEFAULT_COUNTRY_CODE = "+372"

def normalize_phone(phone):
    if pd.isna(phone):
        return None

    phone = str(phone)
    phone = re.sub(r"[^\d+]", "", phone)

    if phone.startswith("8"):
        phone = DEFAULT_COUNTRY_CODE + phone[1:]

    if not phone.startswith("+"):
        phone = DEFAULT_COUNTRY_CODE + phone

    return phone


conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT UNIQUE
)
""")
conn.commit()


root = tk.Tk()
root.title("Контакты")
root.geometry("700x500")


columns = ("name", "phone")

tree = ttk.Treeview(root, columns=columns, show="headings")
tree.heading("name", text="Имя")
tree.heading("phone", text="Телефон")
tree.column("name", width=300)
tree.column("phone", width=200)
tree.pack(expand=True, fill="both")


def load_table(data):
    for row in tree.get_children():
        tree.delete(row)

    for name, phone in data:
        tree.insert("", tk.END, values=(name, phone))


def show_all():
    cursor.execute("SELECT name, phone FROM contacts ORDER BY name")
    load_table(cursor.fetchall())


def import_excel():
    file_paths = filedialog.askopenfilenames(filetypes=[("Excel files", "*.xlsx")])

    if not file_paths:
        return

    total = 0

    for file_path in file_paths:
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            phone = normalize_phone(row.get("phone"))

            if name and phone:
                try:
                    cursor.execute(
                        "INSERT INTO contacts (name, phone) VALUES (?, ?)",
                        (name, phone)
                    )
                    total += 1
                except sqlite3.IntegrityError:
                    pass

    conn.commit()
    show_all()
    messagebox.showinfo("Готово", f"Добавлено: {total}")


def search():
    q = entry.get()
    cursor.execute(
        "SELECT name, phone FROM contacts WHERE name LIKE ?",
        (f"%{q}%",)
    )
    load_table(cursor.fetchall())


def export_excel():
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx")]
    )

    if not file_path:
        return

    cursor.execute("SELECT name, phone FROM contacts")
    df = pd.DataFrame(cursor.fetchall(), columns=["name", "phone"])
    df.to_excel(file_path, index=False)

    messagebox.showinfo("Готово", "Экспорт завершён")


frame = tk.Frame(root)
frame.pack(pady=10)

tk.Button(frame, text="Импорт Excel", command=import_excel).grid(row=0, column=0, padx=5)
tk.Button(frame, text="Экспорт Excel", command=export_excel).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Показать все", command=show_all).grid(row=0, column=2, padx=5)

entry = tk.Entry(root, width=40)
entry.pack()

tk.Button(root, text="Поиск", command=search).pack(pady=5)

show_all()
root.mainloop()