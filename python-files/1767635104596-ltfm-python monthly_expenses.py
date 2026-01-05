import tkinter as tk
from tkinter import messagebox
import json
import os

FILE_NAME = "expenses.json"

def load_expenses():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_expenses():
    with open(FILE_NAME, "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False)

def add_expense():
    desc = desc_entry.get()
    amount = amount_entry.get()
    cat = category_var.get()

    if not desc or not amount:
        messagebox.showerror("خطأ", "ادخل البيانات كاملة")
        return

    try:
        amount = float(amount)
    except:
        messagebox.showerror("خطأ", "المبلغ غير صحيح")
        return

    expenses.append({"desc": desc, "amount": amount, "cat": cat})
    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    refresh()
    save_expenses()

def delete_expense():
    selected = listbox.curselection()
    if not selected:
        return
    expenses.pop(selected[0])
    refresh()
    save_expenses()

def refresh():
    listbox.delete(0, tk.END)
    total = 0
    for e in expenses:
        listbox.insert(tk.END, f"{e['desc']} | {e['cat']} | {e['amount']} جنيه")
        total += e["amount"]
    total_label.config(text=f"الإجمالي: {total} جنيه")

expenses = load_expenses()

root = tk.Tk()
root.title("برنامج المصاريف الشهرية")
root.geometry("400x400")

tk.Label(root, text="وصف المصروف").pack()
desc_entry = tk.Entry(root)
desc_entry.pack(fill="x", padx=10)

tk.Label(root, text="المبلغ").pack()
amount_entry = tk.Entry(root)
amount_entry.pack(fill="x", padx=10)

tk.Label(root, text="التصنيف").pack()
category_var = tk.StringVar(value="أكل")
tk.OptionMenu(root, category_var, "أكل", "مواصلات", "فواتير", "أخرى").pack()

tk.Button(root, text="إضافة مصروف", command=add_expense).pack(pady=5)

listbox = tk.Listbox(root)
listbox.pack(fill="both", expand=True, padx=10)

tk.Button(root, text="حذف المحدد", command=delete_expense).pack(pady=5)

total_label = tk.Label(root, text="الإجمالي: 0 جنيه", font=("Arial", 12, "bold"))
total_label.pack(pady=5)

refresh()
root.mainloop()
