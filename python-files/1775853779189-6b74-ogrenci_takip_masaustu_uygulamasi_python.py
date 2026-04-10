"""
Öğrenci Takip Sistemi (Profesyonel UI)
- Modern tablo görünümü (Treeview)
- Arama / filtreleme
- EXE uyumlu (PyInstaller fix dahil)
"""

import json
import os
import sys
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

# ----------------------
# PATH AYARI (HATA FIX)
# ----------------------
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)

    # __file__ yoksa fallback kullan
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:
        return os.path.dirname(os.path.abspath(sys.argv[0]))

APP_DIR = get_app_dir()
DATA_FILE = os.path.join(APP_DIR, "students.json")
PDF_FILE = os.path.join(APP_DIR, "ogrenciler.pdf")

# ----------------------
# VERİ
# ----------------------
try:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        students = json.load(f)
except:
    students = []


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(students, f, ensure_ascii=False, indent=2)


# ----------------------
# PDF
# ----------------------
def create_pdf():
    data = [["Ad Soyad", "Sınıf", "Numara", "Harçlık"]]
    for s in students:
        data.append([s['name'], s['class'], s['number'], str(s['allowance']) + "₺"])

    pdf = SimpleDocTemplate(PDF_FILE)
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ]))

    pdf.build([table])


# ----------------------
# GUI
# ----------------------
def run_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox

    def refresh_table(data=None):
        for row in tree.get_children():
            tree.delete(row)
        source = data if data else students
        for i, s in enumerate(source):
            tree.insert("", "end", iid=i, values=(s['name'], s['class'], s['number'], s['allowance']))

    def add_student():
        name = entry_name.get()
        cls = entry_class.get()
        num = entry_number.get()
        allowance = entry_allowance.get()

        if not name:
            messagebox.showwarning("Hata", "Ad boş olamaz")
            return

        students.append({
            "name": name,
            "class": cls,
            "number": num,
            "allowance": allowance
        })

        save_data()
        refresh_table()

    def delete_student():
        selected = tree.selection()
        if not selected:
            return
        idx = int(selected[0])
        if 0 <= idx < len(students):
            students.pop(idx)
            save_data()
            refresh_table()

    def search_student():
        keyword = entry_search.get().lower()
        filtered = [s for s in students if keyword in s['name'].lower()]
        refresh_table(filtered)

    root = tk.Tk()
    root.title("Öğrenci Takip Sistemi")
    root.geometry("700x500")

    # FORM
    form = tk.Frame(root)
    form.pack(pady=10)

    tk.Label(form, text="Ad Soyad").grid(row=0, column=0)
    entry_name = tk.Entry(form)
    entry_name.grid(row=1, column=0)

    tk.Label(form, text="Sınıf").grid(row=0, column=1)
    entry_class = tk.Entry(form)
    entry_class.grid(row=1, column=1)

    tk.Label(form, text="Numara").grid(row=0, column=2)
    entry_number = tk.Entry(form)
    entry_number.grid(row=1, column=2)

    tk.Label(form, text="Harçlık").grid(row=0, column=3)
    entry_allowance = tk.Entry(form)
    entry_allowance.grid(row=1, column=3)

    tk.Button(root, text="Ekle", command=add_student).pack(pady=5)
    tk.Button(root, text="Sil", command=delete_student).pack(pady=5)
    tk.Button(root, text="PDF Oluştur", command=create_pdf).pack(pady=5)

    # ARAMA
n    search_frame = tk.Frame(root)
    search_frame.pack(pady=5)

    entry_search = tk.Entry(search_frame)
    entry_search.pack(side=tk.LEFT)
    tk.Button(search_frame, text="Ara", command=search_student).pack(side=tk.LEFT)
    tk.Button(search_frame, text="Temizle", command=lambda: refresh_table()).pack(side=tk.LEFT)

    # TABLO
    columns = ("Ad Soyad", "Sınıf", "Numara", "Harçlık")
    tree = ttk.Treeview(root, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    tree.pack(fill="both", expand=True)

    refresh_table()
    root.mainloop()


# ----------------------
# TESTLER
# ----------------------
def run_tests():
    # Test veri ekleme
    students.clear()
    students.append({"name": "Test", "class": "1A", "number": "1", "allowance": "10"})
    save_data()

    # Veri yükleme testi
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 1

    # PDF testi
    create_pdf()
    assert os.path.exists(PDF_FILE)

    print("Tüm testler başarılı!")


# ----------------------
# BAŞLAT
# ----------------------
if __name__ == "__main__":
    if "--test" in sys.argv:
        run_tests()
    else:
        try:
            import tkinter
            run_gui()
        except Exception as e:
            print("GUI başlatılamadı:", e)


# ======================
# TEK TIK EXE OLUŞTUR (.BAT)
# ======================
"""
@echo off
pip install pyinstaller
rmdir /s /q build
rmdir /s /q dist
del *.spec
pyinstaller --onefile --noconsole app.py
echo EXE hazir: dist klasoru icinde
pause
"""
