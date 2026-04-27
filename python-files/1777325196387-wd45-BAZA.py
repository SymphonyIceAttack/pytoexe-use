import os
import re
import sqlite3
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

DB_NAME = "contacts.db"
DEFAULT_COUNTRY_CODE = "+372"

# --- НОРМАЛИЗАЦИЯ ---
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


# --- БАЗА ---
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


# --- ИМПОРТ EXCEL ---
def import_excel():
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])

    if not file_path:
        return

    try:
        df = pd.read_excel(file_path)

        added = 0

        for _, row in df.iterrows():
            name = str(row.get("name", "")).strip()
            phone = normalize_phone(row.get("phone"))

            if name and phone:
                try:
                    cursor.execute(
                        "INSERT INTO contacts (name, phone) VALUES (?, ?)",
                        (name, phone)
                    )
                    added += 1
                except sqlite3.IntegrityError:
                    pass

        conn.commit()
        messagebox.showinfo("Готово", f"Добавлено контактов: {added}")

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))


# --- ПОИСК ---
def search():
    query = entry.get()

    cursor.execute(
        "SELECT name, phone FROM contacts WHERE name LIKE ?",
        (f"%{query}%",)
    )

    results = cursor.fetchall()

    text.delete(1.0, tk.END)

    for name, phone in results:
        text.insert(tk.END, f"{name} — {phone}\n")


# --- GUI ---
root = tk.Tk()
root.title("Контакты")
root.geometry("500x400")

btn_import = tk.Button(root, text="Импорт Excel", command=import_excel)
btn_import.pack(pady=10)

entry = tk.Entry(root, width=40)
entry.pack()

btn_search = tk.Button(root, text="Поиск", command=search)
btn_search.pack(pady=5)

text = tk.Text(root)
text.pack(expand=True, fill="both")

root.mainloop()