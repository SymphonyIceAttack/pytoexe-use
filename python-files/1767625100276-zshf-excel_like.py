import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
import re

class SimpleExcel:
    def __init__(self, root):
        self.root = root
        self.root.title("محرر جداول بسيط - يشبه Microsoft Excel")
        self.root.geometry("1000x600")

        self.rows = 20
        self.cols = 10
        self.cells = {}
        self.data = [["" for _ in range(self.cols)] for _ in range(self.rows)]

        # شريط أدوات
        toolbar = ttk.Frame(root)
        toolbar.pack(fill="x", padx=5, pady=5)

        ttk.Button(toolbar, text="فتح CSV", command=self.open_csv).pack(side="left", padx=5)
        ttk.Button(toolbar, text="حفظ CSV", command=self.save_csv).pack(side="left", padx=5)
        ttk.Button(toolbar, text="حساب الكل", command=self.calculate_all).pack(side="left", padx=5)

        # إنشاء الجدول
        frame = ttk.Frame(root)
        frame.pack(expand=True, fill="both")

        # رؤوس الأعمدة (A, B, C...)
        for c in range(self.cols):
            label = ttk.Label(frame, text=chr(65 + c), relief="solid", width=12, anchor="center")
            label.grid(row=0, column=c+1)

        # أرقام الصفوف
        for r in range(self.rows):
            label = ttk.Label(frame, text=str(r+1), relief="solid", width=5, anchor="center")
            label.grid(row=r+1, column=0)

        # الخلايا
        for r in range(self.rows):
            for c in range(self.cols):
                entry = ttk.Entry(frame, width=12, justify="center")
                entry.grid(row=r+1, column=c+1, padx=1, pady=1)
                entry.bind("<FocusOut>", lambda e, row=r, col=c: self.on_cell_change(row, col))
                entry.bind("<Return>", lambda e, row=r, col=c: self.on_cell_change(row, col))
                self.cells[(r, c)] = entry

        self.calculate_all()

    def get_cell_value(self, r, c):
        text = self.data[r][c]
        if text.startswith("="):
            return self.evaluate_formula(text[1:], r, c)
        try:
            return float(text) if text else 0
        except:
            return text

    def evaluate_formula(self, formula, current_r, current_c):
        # صيغ بسيطة: A1+B1 أو SUM(A1:A5)
        formula = formula.upper()

        # SUM(A1:A5)
        if formula.startswith("SUM("):
            match = re.match(r"SUM\(([A-Z]\d+):([A-Z]\d+)\)", formula)
            if match:
                start = self.cell_to_rc(match.group(1))
                end = self.cell_to_rc(match.group(2))
                total = 0
                for rr in range(start[0], end[0]+1):
                    for cc in range(start[1], end[1]+1):
                        total += self.get_cell_value(rr, cc) if isinstance(self.get_cell_value(rr, cc), (int, float)) else 0
                return total

        # A1+B1-C2
        terms = re.findall(r"[A-Z]\d+|[+\-*/]", formula)
        expr = ""
        for term in terms:
            if re.match(r"[A-Z]\d+", term):
                rc = self.cell_to_rc(term)
                if rc == (current_r, current_c):
                    return "#REF!"  # تجنب الدوران
                val = self.get_cell_value(rc[0], rc[1])
                expr += str(val) if isinstance(val, (int, float)) else "0"
            else:
                expr += term
        try:
            return eval(expr)
        except:
            return "#ERROR"

    def cell_to_rc(self, cell):
        col = ord(cell[0]) - 65
        row = int(cell[1:]) - 1
        return (row, col)

    def on_cell_change(self, r, c):
        text = self.cells[(r, c)].get()
        self.data[r][c] = text
        self.calculate_all()

    def calculate_all(self):
        for r in range(self.rows):
            for c in range(self.cols):
                entry = self.cells[(r, c)]
                text = self.data[r][c]
                if text.startswith("="):
                    value = self.get_cell_value(r, c)
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))
                else:
                    if entry.get() != text:
                        entry.delete(0, tk.END)
                        entry.insert(0, text)

    def open_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                data = list(reader)
                for r in range(min(self.rows, len(data))):
                    for c in range(min(self.cols, len(data[r]))):
                        self.cells[(r, c)].delete(0, tk.END)
                        self.cells[(r, c)].insert(0, data[r][c])
                        self.data[r][c] = data[r][c]
            self.calculate_all()

    def save_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if path:
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                for r in range(self.rows):
                    row = [self.data[r][c] for c in range(self.cols)]
                    writer.writerow(row)
            messagebox.showinfo("حفظ", "تم الحفظ بنجاح!")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleExcel(root)
    root.mainloop()