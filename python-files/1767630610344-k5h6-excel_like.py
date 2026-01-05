import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import re

class BetterExcel:
    def __init__(self, root):
        self.root = root
        self.root.title("محرر جداول متقدم - يشبه Microsoft Excel 365")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f0f0")

        self.rows = 30
        self.cols = 15
        self.cells = {}
        self.data = [["" for _ in range(self.cols)] for _ in range(self.rows)]

        # Ribbon (تبويبات زي Excel)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="x")

        home_tab = ttk.Frame(self.notebook)
        insert_tab = ttk.Frame(self.notebook)
        formulas_tab = ttk.Frame(self.notebook)
        self.notebook.add(home_tab, text="الرئيسية (Home)")
        self.notebook.add(insert_tab, text="إدراج (Insert)")
        self.notebook.add(formulas_tab, text="صيغ (Formulas)")

        # أدوات Home
        toolbar = ttk.Frame(home_tab)
        toolbar.pack(fill="x", padx=5, pady=5)
        ttk.Button(toolbar, text="فتح CSV", command=self.open_csv).pack(side="left", padx=5)
        ttk.Button(toolbar, text="حفظ CSV", command=self.save_csv).pack(side="left", padx=5)
        ttk.Button(toolbar, text="حساب الكل", command=self.calculate_all).pack(side="left", padx=5)

        # Formula Bar (شريط الصيغ)
        formula_frame = ttk.Frame(self.root)
        formula_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(formula_frame, text="fx", font=("Arial", 10, "bold"), background="white", relief="sunken", anchor="center", width=5).pack(side="left")
        self.formula_entry = ttk.Entry(formula_frame)
        self.formula_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.formula_entry.bind("<Return>", self.apply_formula)

        # الجدول
        table_frame = ttk.Frame(self.root)
        table_frame.pack(expand=True, fill="both", padx=10, pady=10)

        # رؤوس أعمدة
        for c in range(self.cols):
            label = ttk.Label(table_frame, text=chr(65 + c), font=("Arial", 10, "bold"), background="#d0d0d0", relief="solid", borderwidth=1, anchor="center", width=15)
            label.grid(row=0, column=c+1)

        # أرقام صفوف
        for r in range(self.rows):
            label = ttk.Label(table_frame, text=str(r+1), font=("Arial", 10, "bold"), background="#d0d0d0", relief="solid", borderwidth=1, anchor="center", width=6)
            label.grid(row=r+1, column=0)

        # خلايا
        for r in range(self.rows):
            for c in range(self.cols):
                entry = ttk.Entry(table_frame, font=("Arial", 10), justify="center", relief="solid", borderwidth=1)
                entry.grid(row=r+1, column=c+1, padx=0, pady=0, ipadx=5, ipady=5)
                entry.bind("<FocusOut>", lambda e, rr=r, cc=c: self.on_cell_change(rr, cc))
                entry.bind("<Return>", lambda e, rr=r, cc=c: self.on_cell_change(rr, cc))
                entry.bind("<FocusIn>", lambda e, rr=r, cc=c: self.show_formula(rr, cc))
                self.cells[(r, c)] = entry

        self.calculate_all()

    def show_formula(self, r, c):
        self.formula_entry.delete(0, tk.END)
        self.formula_entry.insert(0, self.data[r][c])

    def apply_formula(self, event=None):
        # لو عايز تضيف صيغة من الشريط
        pass  # ممكن نطورها بعدين

    def on_cell_change(self, r, c):
        text = self.cells[(r, c)].get()
        self.data[r][c] = text
        self.calculate_all()

    # باقي الدوال زي السابق (get_cell_value, evaluate_formula, etc.) - انسخها من الكود السابق

    # ... (انسخ باقي الدوال من الكود اللي فات: get_cell_value, evaluate_formula, cell_to_rc, calculate_all, open_csv, save_csv)

if __name__ == "__main__":
    root = tk.Tk()
    app = BetterExcel(root)
    root.mainloop()