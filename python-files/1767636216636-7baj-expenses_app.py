import tkinter as tk
from tkinter import ttk, messagebox
import json, os
from datetime import date

FILE = "expenses.json"

# ================== DATA ==================
def load_data():
    if os.path.exists(FILE):
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data():
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False)

# ================== FUNCTIONS ==================
def add_expense():
    d = date_entry.get()
    desc = desc_entry.get()
    amt = amount_entry.get()

    if not d or not desc or not amt:
        messagebox.showerror("خطأ", "ادخل جميع البيانات")
        return

    try:
        amt = float(amt)
    except:
        messagebox.showerror("خطأ", "المبلغ غير صحيح")
        return

    expenses.append({"date": d, "desc": desc, "amount": amt})
    desc_entry.delete(0, tk.END)
    amount_entry.delete(0, tk.END)
    refresh()
    save_data()

def delete_expense():
    sel = tree.selection()
    if not sel:
        return
    index = tree.index(sel[0])
    expenses.pop(index)
    refresh()
    save_data()

def refresh():
    for i in tree.get_children():
        tree.delete(i)

    total = 0
    for e in expenses:
        tree.insert("", "end", values=(e["date"], e["desc"], e["amount"]))
        total += e["amount"]

    total_label.config(text=f"الإجمالي: {total} جنيه")

def toggle_theme():
    global dark
    dark = not dark
    apply_theme()

def apply_theme():
    if dark:
        bg = "#1e1e1e"
        fg = "white"
        tree_bg = "#2b2b2b"
    else:
        bg = "#e9eef3"
        fg = "black"
        tree_bg = "white"

    root.configure(bg=bg)
    top_frame.configure(bg=bg)
    total_label.configure(bg=bg, fg=fg)

    for lbl in labels:
        lbl.configure(bg=bg, fg=fg)

    style.configure("Treeview",
                    background=tree_bg,
                    foreground=fg,
                    fieldbackground=tree_bg)

# ================== UI ==================
expenses = load_data()
dark = False

root = tk.Tk()
root.title("برنامج المصاريف الشهرية")
root.geometry("650x480")

style = ttk.Style()
style.theme_use("default")

top_frame = tk.Frame(root)
top_frame.pack(padx=10, pady=10, fill="x")

labels = []

lbl = tk.Label(top_frame, text="التاريخ")
lbl.grid(row=0, column=0)
labels.append(lbl)

date_entry = ttk.Entry(top_frame)
date_entry.grid(row=1, column=0, padx=5)
date_entry.insert(0, date.today().isoformat())

lbl = tk.Label(top_frame, text="الوصف")
lbl.grid(row=0, column=1)
labels.append(lbl)

desc_entry = ttk.Entry(top_frame, width=20)
desc_entry.grid(row=1, column=1, padx=5)

lbl = tk.Label(top_frame, text="المبلغ")
lbl.grid(row=0, column=2)
labels.append(lbl)

amount_entry = ttk.Entry(top_frame)
amount_entry.grid(row=1, column=2, padx=5)

ttk.Button(top_frame, text="➕ إضافة", command=add_expense).grid(row=1, column=3, padx=5)
ttk.Button(top_frame, text="🌙 / ☀ تغيير الوضع", command=toggle_theme).grid(row=1, column=4, padx=5)

tree = ttk.Treeview(root, columns=("date", "desc", "amount"), show="headings")
tree.heading("date", text="التاريخ")
tree.heading("desc", text="الوصف")
tree.heading("amount", text="المبلغ")
tree.pack(fill="both", expand=True, padx=10, pady=10)

ttk.Button(root, text="🗑 حذف المحدد", command=delete_expense).pack(pady=5)

total_label = tk.Label(root, font=("Segoe UI", 12, "bold"))
total_label.pack(pady=5)

apply_theme()
refresh()
root.mainloop()
