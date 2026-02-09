import tkinter as tk
from tkinter import simpledialog, ttk, messagebox
import os
from datetime import date, datetime
from calendar import monthrange

# ===================== COLORS =====================
BG = "#f2f4f6"
PRIMARY = "#2c3e50"
ACCENT = "#3498db"
SUCCESS = "#27ae60"
WARNING = "#f39c12"
DANGER = "#e74c3c"

# ===================== FILE STRUCTURE =====================
BASE_DIR = os.path.join(os.path.dirname(__file__), "ExpRecords")

# ===================== CATEGORIES =====================
CATEGORIES = [
    "Groceries",
    "Household & Toiletries",
    "School / Transportation / Fuel",
    "Cat Food",
    "Personal Items",
    "Emergency Savings"
]

entries_by_category = {cat: {} for cat in CATEGORIES}
category_limits = {cat: 0.0 for cat in CATEGORIES}
monthly_budget = 0.0

# ===================== DATE HELPERS =====================
def formatted_today():
    return date.today().strftime("%Y-%m-%d")

def parse_date(d):
    return datetime.strptime(d, "%Y-%m-%d")

def year_month(d):
    dt = parse_date(d)
    return dt.strftime("%Y"), dt.strftime("%B")

def shift_month(d, delta):
    dt = parse_date(d)
    m = dt.month + delta
    y = dt.year + (m - 1) // 12
    m = (m - 1) % 12 + 1
    day = min(dt.day, monthrange(y, m)[1])
    return date(y, m, day).strftime("%Y-%m-%d")

# ===================== PATH HELPERS =====================
def get_expense_file(exp_date):
    y, m = year_month(exp_date)
    path = os.path.join(BASE_DIR, y, m)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, f"{exp_date}.txt")

def get_month_budget_file(exp_date):
    y, m = year_month(exp_date)
    path = os.path.join(BASE_DIR, y, m)
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "month_budget.txt")

# ===================== SAFE WRITE =====================
def safe_write(path, content):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp, path)

# ===================== SAVE / LOAD =====================
def save_data():
    for cat, days in entries_by_category.items():
        for day, entries in days.items():
            content = "".join(f"{cat}|{e['desc']}|{e['amount']}\n" for e in entries)
            safe_write(get_expense_file(day), content)

def load_data():
    if not os.path.exists(BASE_DIR):
        return

    for year in os.listdir(BASE_DIR):
        for month in os.listdir(os.path.join(BASE_DIR, year)):
            mp = os.path.join(BASE_DIR, year, month)
            for file in os.listdir(mp):
                if file == "month_budget.txt":
                    continue
                day = file.replace(".txt", "")
                with open(os.path.join(mp, file), "r", encoding="utf-8") as f:
                    for line in f:
                        cat, desc, amt = line.strip().split("|")
                        entries_by_category.setdefault(cat, {}).setdefault(day, []).append(
                            {"desc": desc, "amount": float(amt)}
                        )

def save_budget(exp_date):
    content = f"monthly_budget|{monthly_budget}\n"
    for c, l in category_limits.items():
        content += f"{c}|{l}\n"
    safe_write(get_month_budget_file(exp_date), content)

def load_budget(exp_date):
    global monthly_budget
    monthly_budget = 0.0
    for c in CATEGORIES:
        category_limits[c] = 0.0

    path = get_month_budget_file(exp_date)
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            k, v = line.strip().split("|")
            if k == "monthly_budget":
                monthly_budget = float(v)
            elif k in CATEGORIES:
                category_limits[k] = float(v)

# ===================== UI REFRESH =====================
def refresh_listbox(cat):
    lb = listboxes[cat]
    lb.delete(0, tk.END)

    spent = 0.0
    for day in sorted(entries_by_category.get(cat, {})):
        lb.insert(tk.END, f"=== {day} ===")
        for e in entries_by_category[cat][day]:
            spent += e["amount"]
            lb.insert(tk.END, f"  {e['desc']} | ₱{e['amount']:.2f}")
        lb.insert(tk.END, "----------------")

    limit = category_limits[cat]
    remaining = limit - spent

    total_labels[cat].config(text=f"Spent: ₱{spent:.2f}")
    limit_labels[cat].config(text=f"Limit: ₱{limit:.2f}")
    remaining_labels[cat].config(
        text=f"Remaining: ₱{remaining:.2f}",
        fg=DANGER if remaining < 0 else SUCCESS
    )

    progressbars[cat]["value"] = min(100, (spent / limit * 100)) if limit else 0

    total_spent = sum(
        e["amount"]
        for c in entries_by_category.values()
        for d in c.values()
        for e in d
    )

    monthly_budget_label.config(text=f"Monthly Budget: ₱{monthly_budget:.2f}")
    monthly_remaining_label.config(
        text=f"Monthly Remaining: ₱{monthly_budget - total_spent:.2f}",
        fg=DANGER if monthly_budget - total_spent < 0 else PRIMARY
    )

def refresh_all():
    for c in CATEGORIES:
        refresh_listbox(c)

# ===================== ACTIONS =====================
def ask_monthly_budget():
    global monthly_budget
    if monthly_budget > 0:
        if not messagebox.askyesno(
            "Overwrite Monthly Budget",
            "A budget already exists for this month.\nOverwrite it?"
        ):
            return

    v = simpledialog.askfloat("Monthly Budget", "Enter monthly budget:", minvalue=0)
    if v is not None:
        monthly_budget = v
        save_budget(entry_date.get())
        refresh_all()

def set_category_limit(cat):
    if category_limits[cat] > 0:
        if not messagebox.askyesno(
            "Overwrite Category Limit",
            f"A limit already exists for {cat}.\nOverwrite it?"
        ):
            return

    v = simpledialog.askfloat("Category Limit", f"Set limit for {cat}:", minvalue=0)
    if v is not None:
        category_limits[cat] = v
        save_budget(entry_date.get())
        refresh_listbox(cat)

def add_expense(event=None):
    exp_date = entry_date.get()
    try:
        parse_date(exp_date)
    except ValueError:
        messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format")
        return

    try:
        amt = float(entry_amt.get())
    except ValueError:
        return

    desc = entry_desc.get()
    cat = notebook.tab(notebook.select(), "text").rstrip(":")

    entries_by_category.setdefault(cat, {}).setdefault(exp_date, []).append(
        {"desc": desc, "amount": amt}
    )

    entry_desc.delete(0, tk.END)
    entry_amt.delete(0, tk.END)
    entry_desc.focus_set()

    save_data()
    refresh_listbox(cat)

def delete_selected():
    cat = notebook.tab(notebook.select(), "text").rstrip(":")
    lb = listboxes[cat]
    selected = lb.curselection()
    if not selected:
        return

    if not messagebox.askyesno("Delete Expense", f"Delete {len(selected)} selected expense(s)?"):
        return

    # Mapping listbox index -> (day, entry_index)
    mapping = []
    for day in sorted(entries_by_category.get(cat, {})):
        mapping.append((None, None))  # header
        for i in range(len(entries_by_category[cat][day])):
            mapping.append((day, i))
        mapping.append((None, None))  # divider

    for idx in sorted(selected, reverse=True):
        if idx < len(mapping):
            day, i = mapping[idx]
            if day is not None:
                entries_by_category[cat][day].pop(i)
                if not entries_by_category[cat][day]:
                    del entries_by_category[cat][day]

    save_data()
    refresh_listbox(cat)

def change_month(delta):
    new_date = shift_month(entry_date.get(), delta)
    entry_date.delete(0, tk.END)
    entry_date.insert(0, new_date)
    load_budget(new_date)
    refresh_all()

def switch_focus(event, target):
    target.focus_set()
    return "break"

# ===================== GUI =====================
root = tk.Tk()
root.title("Expense Tracker")
root.geometry("780x880")
root.configure(bg=BG)

top = tk.Frame(root, bg=BG)
top.pack(fill="x", padx=10)

monthly_budget_label = tk.Label(top, font=("Arial", 12, "bold"), bg=BG)
monthly_budget_label.pack(anchor="w")

monthly_remaining_label = tk.Label(top, font=("Arial", 12, "bold"), bg=BG)
monthly_remaining_label.pack(anchor="w")

nav = tk.Frame(top, bg=BG)
nav.pack(anchor="e")

tk.Button(nav, text="◀ Prev Month", command=lambda: change_month(-1)).pack(side="left", padx=4)
tk.Button(nav, text="Edit Monthly Budget", bg=SUCCESS, fg="white",
          relief="flat", command=ask_monthly_budget).pack(side="left", padx=6)
tk.Button(nav, text="Next Month ▶", command=lambda: change_month(1)).pack(side="left", padx=4)

entry_frame = tk.Frame(root, bg=BG)
entry_frame.pack(fill="x", padx=10)

tk.Label(entry_frame, text="Date:", bg=BG).grid(row=0, column=0)
entry_date = tk.Entry(entry_frame, width=18)
entry_date.insert(0, formatted_today())
entry_date.grid(row=0, column=1)

tk.Label(entry_frame, text="Description:", bg=BG).grid(row=1, column=0)
entry_desc = tk.Entry(entry_frame, width=20)
entry_desc.grid(row=1, column=1)

tk.Label(entry_frame, text="Amount (₱):", bg=BG).grid(row=1, column=2)
entry_amt = tk.Entry(entry_frame, width=10)
entry_amt.grid(row=1, column=3)

# ===================== CURSOR FLOW & ENTER =====================
entry_desc.bind("<Right>", lambda e: switch_focus(e, entry_amt))
entry_amt.bind("<Left>", lambda e: switch_focus(e, entry_desc))
entry_desc.bind("<Return>", lambda e: entry_amt.focus_set())  # Enter moves to Amount
entry_amt.bind("<Return>", add_expense)                        # Enter in Amount adds expense

tk.Button(entry_frame, text="Add Expense", command=add_expense).grid(row=1, column=4)
tk.Button(entry_frame, text="Delete Selected", bg=DANGER, fg="white",
          relief="flat", command=delete_selected).grid(row=1, column=5)

notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both", padx=10, pady=5)

listboxes = {}
total_labels = {}
limit_labels = {}
remaining_labels = {}
progressbars = {}

for cat in CATEGORIES:
    frame = tk.Frame(notebook)
    notebook.add(frame, text=f"{cat}:")

    pb = ttk.Progressbar(frame, maximum=100)
    pb.pack(fill="x", padx=10, pady=3)
    progressbars[cat] = pb

    # Enable multiple selection for multi-deletion
    lb = tk.Listbox(frame, selectmode=tk.EXTENDED)
    lb.pack(fill="both", expand=True, padx=10)
    listboxes[cat] = lb

    bottom = tk.Frame(frame)
    bottom.pack(fill="x", padx=10)

    limit_labels[cat] = tk.Label(bottom)
    limit_labels[cat].pack(side="left", padx=2)

    total_labels[cat] = tk.Label(bottom)
    total_labels[cat].pack(side="left", padx=10)

    remaining_labels[cat] = tk.Label(bottom)
    remaining_labels[cat].pack(side="left", padx=10)

    # Set Limit button next to Remaining
    tk.Button(bottom, text="Set Limit",
              command=lambda c=cat: set_category_limit(c)).pack(side="left", padx=5)

load_data()
load_budget(entry_date.get())
refresh_all()

root.mainloop()
