import sqlite3
import os
import tkinter as tk
from tkinter import ttk, messagebox, font

# ----------------------------
# مسیر دیتابیس
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "SHELL.db")

if not os.path.exists(DB_PATH):
    messagebox.showerror("خطا", "فایل SHELL.db در کنار برنامه پیدا نشد")
    raise SystemExit

# ----------------------------
# خواندن دیتابیس
# ----------------------------
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
result = cursor.fetchone()

if not result:
    messagebox.showerror("خطا", "هیچ جدولی در دیتابیس وجود ندارد")
    raise SystemExit

table_name = result[0]

cursor.execute(f'SELECT * FROM [{table_name}]')
all_rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

conn.close()

# ----------------------------
# رابط گرافیکی
# ----------------------------
root = tk.Tk()
root.title("SHELL Database Viewer")

# اندازه پنجره
width = 950
height = 560

# ----------------------------
# مرکز کردن پنجره روی مانیتور
# ----------------------------
root.update_idletasks()  # اطمینان از اینکه اندازه پنجره صحیح است
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width // 2) - (width // 2)
y = (screen_height // 2) - (height // 2)
root.geometry(f"{width}x{height}+{x}+{y}")

# ----------------------------
# فونت‌ها
# ----------------------------
table_font = font.Font(family="Segoe UI", size=11)
header_font = font.Font(family="Segoe UI", size=11, weight="bold")
search_font = font.Font(family="Segoe UI", size=13)
status_font = font.Font(family="Segoe UI", size=10)

# ----------------------------
# فریم سرچ
# ----------------------------
search_frame = tk.Frame(root)
search_frame.pack(fill="x", padx=10, pady=6)

tk.Label(search_frame, text="SEARCH : ", font=search_font).pack(side="left")

search_var = tk.StringVar()
search_entry = tk.Entry(
    search_frame,
    textvariable=search_var,
    width=35,
    font=search_font
)
search_entry.pack(side="left", padx=6)
search_entry.focus()

# ----------------------------
# ZERO QTY Checkbutton با حرف Q زیرخط دار
# ----------------------------
zero_qty_var = tk.BooleanVar(value=False)

zero_qty_check = tk.Checkbutton(
    search_frame,
    text="ZERO QTY",
    variable=zero_qty_var,
    font=search_font,
    command=lambda: load_data(),
    underline=5  # حرف Q زیرخط دار شود
)
zero_qty_check.pack(side="left", padx=15)

# ----------------------------
# جدول
# ----------------------------
tree = ttk.Treeview(root, columns=columns, show="headings")
tree.pack(fill="both", expand=True, padx=10, pady=5)

# ----------------------------
# Style و خطوط سیاه (حداکثر تفکیک با Zebra)
# ----------------------------
style = ttk.Style()
style.configure("Treeview", font=table_font, rowheight=28, borderwidth=1, relief="solid")
style.configure("Treeview.Heading", font=header_font)
style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])

tree.tag_configure("even", background="#FFFFFF")
tree.tag_configure("odd", background="#F2F2F2")

# ----------------------------
# متن دلخواه سرستون‌ها
# ----------------------------
custom_headers = {
    columns[0]: "ITEM.NO",
    columns[1]: "ITEM NAME",
    columns[2]: "QTY",
    columns[3]: "PRICE",
    columns[4]: "MADE BY"
}

for col in columns:
    display_text = custom_headers.get(col, col)
    tree.heading(col, text=display_text)
    tree.column(col, anchor="w", stretch=True, width=100)

scrollbar = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# ----------------------------
# Status Bar
# ----------------------------
status_var = tk.StringVar()
status_bar = tk.Label(
    root,
    textvariable=status_var,
    anchor="w",
    relief="sunken",
    padx=10,
    font=status_font
)
status_bar.pack(side="bottom", fill="x")

# ----------------------------
# توابع
# ----------------------------
def auto_resize_columns(rows):
    for col_index, col_name in enumerate(columns):
        max_width = header_font.measure(custom_headers.get(col_name, col_name))
        for row in rows:
            cell_width = table_font.measure(str(row[col_index]))
            if cell_width > max_width:
                max_width = cell_width
        tree.column(col_name, width=max_width + 20)

def update_status(rows):
    total_qty = 0
    for row in rows:
        try:
            total_qty += int(row[2])  # ستون سوم = QTY
        except:
            pass

    zero_status = "ON" if zero_qty_var.get() else "OFF"
    search_status = "ON" if search_var.get().strip() else "OFF"

    status_var.set(
        f"ZERO QTY: {zero_status} | "
        f"Search: {search_status} | "
        f"Rows: {len(rows)} | "
        f"Total QTY: {total_qty}"
    )

def load_data():
    tree.delete(*tree.get_children())

    query = search_var.get().strip().lower()
    zero_only = zero_qty_var.get()

    filtered_rows = []
    for row in all_rows:
        # فیلتر ZERO QTY
        try:
            qty = int(row[2])
        except:
            qty = 0
        if zero_only and qty == 0:
            continue

        # فیلتر سرچ
        if query:
            if not any(query in str(cell).lower() for cell in row):
                continue

        filtered_rows.append(row)

    for index, row in enumerate(filtered_rows):
        tag = "even" if index % 2 == 0 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))

    auto_resize_columns(filtered_rows)
    update_status(filtered_rows)

def clear_search(event=None):
    search_var.set("")
    load_data()
    search_entry.focus()

def toggle_zero_qty(event=None):
    zero_qty_var.set(not zero_qty_var.get())
    load_data()

def alt_key_handler(event):
    if event.keysym.lower() == "q":  # بدون حساسیت به حروف بزرگ/کوچک
        toggle_zero_qty()

# ----------------------------
# رویدادها
# ----------------------------
search_var.trace_add("write", lambda *args: load_data())
root.bind("<Escape>", clear_search)
root.bind_all("<Alt-KeyPress>", alt_key_handler)

# ----------------------------
# نمایش اولیه
# ----------------------------
load_data()

root.mainloop()
