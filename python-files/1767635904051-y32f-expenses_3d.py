import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import date

FILE_NAME = "expenses_data.json"

def load_data():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data():
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False)

def add_expense():
    d = date_entry.get()
    desc = desc_entry.get()
    amount = amount_entry.get()

    if not d or not desc or not amount:
        messagebox.showerror("خطأ", "ادخل جميع البيانات")
        return

    try:
        amount = float(amount)
    except:
        messagebox.showerror("خطأ", "المبلغ غير صحيح")
        return

    expenses.append({
        "date": d,
        "desc": desc,
        "amount": amount
    })

    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    refresh()
    save_data()

def delete_expense():
    selected = tree.selection()
    if not selected:
        return
    index = tree.index(selected[0])
    expenses.pop(index)
    refresh()
    save_data()

def refresh():
    for row in tree.get_children():
        tree.delete(row)

    total = 0
    for e in expenses:
        tree.insert("", "end", values=(e["date"], e["desc"], e["amount"]))
        total += e["amount"]

    total_label.config(text=f"الإجمالي: {total} جنيه")

# ================= UI =================

expenses = load_data()

root = tk.Tk()
root.title("برنامج المصاريف الشهرية")
root.geometry("600x450")
root.configure(bg="#e9eef3")

style = ttk.Style()
style.theme_use("default")

style.configure("TButton",
    font=("Segoe UI", 10, "bold"),
    padding=6,
    relief="raised"
)

style.configure("Treeview",
    font=("Segoe UI", 10),
    rowheight=28
)

style.configure("Treeview.Heading",
    font=("Segoe UI", 10, "bold")
)

frame = tk.Frame(root, bg="#e9eef3")
frame.pack(padx=10, pady=10, fill="x")

tk.Label(frame, text="التاريخ", bg="#e9eef3").grid(row=0, column=0)
date_entry = ttk.Entry(frame)
date_entry.grid(row=1, column=0, padx=5)
date_entry.insert(0, date.today().isoformat())

tk.Label(frame, text="الوصف", bg="#e9eef3").grid(row=0, column=1)
desc_entry = ttk.Entry(frame, width=20)
desc_entry.grid(row=1, column=1, padx=5)

tk.Label(frame, text="المبلغ", bg="#e9eef3").grid(row=0, column=2)
amount_entry = ttk.Entry(frame)
amount_entry.grid(row=1, column=2, padx=5)

ttk.Button(frame, text="➕ إضافة", command=add_expense).grid(row=1, column=3, padx=5)

tree = ttk.Treeview(root, columns=("date", "desc", "amount"), show="headings")
tree.heading("date", text="التاريخ")
tree.heading("desc", text="الوصف")
tree.heading("amount", text="المبلغ")
tree.pack(fill="both", expand=True, padx=10, pady=10)

ttk.Button(root, text="🗑 حذف المحدد", command=delete_expense).pack(pady=5)

total_label = tk.Label(root, text="الإجمالي: 0 جنيه",
                       font=("Segoe UI", 12, "bold"),
                       bg="#e9eef3")
total_label.pack(pady=5)

refresh()
root.mainloop()
