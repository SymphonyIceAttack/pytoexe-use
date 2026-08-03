# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime

# إنشاء قاعدة البيانات وجداولها
def init_db():
    conn = sqlite3.connect('mohamah.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT,
                    notes TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    client_id INTEGER,
                    description TEXT,
                    status TEXT,
                    FOREIGN KEY(client_id) REFERENCES clients(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    case_id INTEGER,
                    date TEXT,
                    time TEXT,
                    place TEXT,
                    notes TEXT,
                    FOREIGN KEY(case_id) REFERENCES cases(id))''')
    conn.commit()
    conn.close()

# دالة مساعدة للاستعلام عن قاعدة البيانات
def db_query(query, params=()):
    conn = sqlite3.connect('mohamah.db')
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    result = c.fetchall()
    conn.close()
    return result

# الواجهة الرئيسية
class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("حليم عبيد للمحاماه - نظام إدارة القضايا")
        self.root.geometry("900x600")
        self.root.configure(bg='#1a237e')  # أزرق داكن

        # إطار علوي للعنوان (ذهبي)
        header = tk.Frame(root, bg='#ffd700', height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        title = tk.Label(header, text="نظام إدارة المحاماه - حليم عبيد", font=('Arial', 24, 'bold'), bg='#ffd700', fg='#1a237e')
        title.pack(pady=15)

        # إطار الأزرار الرئيسية
        btn_frame = tk.Frame(root, bg='#1a237e')
        btn_frame.pack(pady=10)

        btn_style = {'bg': '#ffd700', 'fg': '#1a237e', 'font': ('Arial', 12, 'bold'), 'width': 15, 'height': 1}

        tk.Button(btn_frame, text="إدارة الموكلين", command=self.show_clients, **btn_style).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="إدارة القضايا", command=self.show_cases, **btn_style).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="إدارة الجلسات", command=self.show_sessions, **btn_style).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="عرض التقارير", command=self.show_reports, **btn_style).grid(row=0, column=3, padx=5)

        # إطار لعرض البيانات (جدول)
        self.tree_frame = tk.Frame(root, bg='#1a237e')
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(self.tree_frame, columns=('col1','col2','col3','col4'), show='headings')
        self.tree.pack(fill=tk.BOTH, expand=True)

        # شريط الحالة
        self.status = tk.Label(root, text="جاهز", bg='#ffd700', fg='#1a237e', anchor='w', font=('Arial', 10))
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # عرض الموكلين افتراضياً
        self.show_clients()

    def clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def set_tree_columns(self, cols, headings):
        self.tree['columns'] = cols
        for col in cols:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=150)

    def show_clients(self):
        self.clear_tree()
        cols = ('id', 'name', 'phone', 'address')
        headings = {'id':'ID', 'name':'الاسم', 'phone':'الهاتف', 'address':'العنوان'}
        self.set_tree_columns(cols, headings)
        data = db_query("SELECT * FROM clients")
        for row in data:
            self.tree.insert('', tk.END, values=row)
        self.status.config(text="عرض الموكلين")
        self.show_action_buttons('client')

    def show_cases(self):
        self.clear_tree()
        cols = ('id', 'title', 'client_id', 'status')
        headings = {'id':'ID', 'title':'عنوان القضية', 'client_id':'رقم الموكل', 'status':'الحالة'}
        self.set_tree_columns(cols, headings)
        data = db_query("SELECT * FROM cases")
        for row in data:
            self.tree.insert('', tk.END, values=row)
        self.status.config(text="عرض القضايا")
        self.show_action_buttons('case')

    def show_sessions(self):
        self.clear_tree()
        cols = ('id', 'case_id', 'date', 'time', 'place')
        headings = {'id':'ID', 'case_id':'رقم القضية', 'date':'التاريخ', 'time':'الوقت', 'place':'المكان'}
        self.set_tree_columns(cols, headings)
        data = db_query("SELECT id, case_id, date, time, place FROM sessions")
        for row in data:
            self.tree.insert('', tk.END, values=row)
        self.status.config(text="عرض الجلسات")
        self.show_action_buttons('session')

    def show_reports(self):
        # تقرير بسيط: عدد القضايا لكل موكل
        report = "تقارير:\n"
        clients = db_query("SELECT id, name FROM clients")
        for c in clients:
            count = db_query("SELECT COUNT(*) FROM cases WHERE client_id=?", (c[0],))[0][0]
            report += f"الموكل: {c[1]} - عدد القضايا: {count}\n"
        # عدد الجلسات القادمة (من اليوم فصاعداً)
        today = datetime.now().strftime('%Y-%m-%d')
        upcoming = db_query("SELECT COUNT(*) FROM sessions WHERE date >= ?", (today,))[0][0]
        report += f"\nالجلسات القادمة (من اليوم فصاعداً): {upcoming}"
        messagebox.showinfo("التقارير", report)

    def show_action_buttons(self, table):
        # إزالة أي إطار أزرار سابق
        if hasattr(self, 'action_frame'):
            self.action_frame.destroy()
        action_frame = tk.Frame(self.root, bg='#1a237e')
        action_frame.pack(pady=5)
        tk.Button(action_frame, text="إضافة", command=lambda: self.add_record(table), bg='#ffd700', fg='#1a237e', font=('Arial',10,'bold')).grid(row=0, column=0, padx=5)
        tk.Button(action_frame, text="تعديل", command=lambda: self.edit_record(table), bg='#ffd700', fg='#1a237e', font=('Arial',10,'bold')).grid(row=0, column=1, padx=5)
        tk.Button(action_frame, text="حذف", command=lambda: self.delete_record(table), bg='#ffd700', fg='#1a237e', font=('Arial',10,'bold')).grid(row=0, column=2, padx=5)
        self.action_frame = action_frame

    def add_record(self, table):
        if table == 'client':
            name = simpledialog.askstring("إضافة موكل", "الاسم:")
            if name:
                phone = simpledialog.askstring("إضافة موكل", "الهاتف:")
                address = simpledialog.askstring("إضافة موكل", "العنوان:")
                notes = simpledialog.askstring("إضافة موكل", "ملاحظات:")
                db_query("INSERT INTO clients (name, phone, address, notes) VALUES (?,?,?,?)", (name, phone, address, notes))
                self.show_clients()
        elif table == 'case':
            title = simpledialog.askstring("إضافة قضية", "عنوان القضية:")
            if title:
                client_id = simpledialog.askinteger("إضافة قضية", "رقم الموكل:")
                description = simpledialog.askstring("إضافة قضية", "الوصف:")
                status = simpledialog.askstring("إضافة قضية", "الحالة (مفتوحة/مغلقة/قيد النظر):")
                db_query("INSERT INTO cases (title, client_id, description, status) VALUES (?,?,?,?)", (title, client_id, description, status))
                self.show_cases()
        elif table == 'session':
            case_id = simpledialog.askinteger("إضافة جلسة", "رقم القضية:")
            if case_id:
                date = simpledialog.askstring("إضافة جلسة", "التاريخ (YYYY-MM-DD):")
                time = simpledialog.askstring("إضافة جلسة", "الوقت (HH:MM):")
                place = simpledialog.askstring("إضافة جلسة", "المكان:")
                notes = simpledialog.askstring("إضافة جلسة", "ملاحظات:")
                db_query("INSERT INTO sessions (case_id, date, time, place, notes) VALUES (?,?,?,?,?)", (case_id, date, time, place, notes))
                self.show_sessions()

    def edit_record(self, table):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("تعديل", "يرجى تحديد سجل للتعديل")
            return
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        if table == 'client':
            name = simpledialog.askstring("تعديل موكل", "الاسم:", initialvalue=item['values'][1])
            phone = simpledialog.askstring("تعديل موكل", "الهاتف:", initialvalue=item['values'][2])
            address = simpledialog.askstring("تعديل موكل", "العنوان:", initialvalue=item['values'][3])
            db_query("UPDATE clients SET name=?, phone=?, address=? WHERE id=?", (name, phone, address, record_id))
            self.show_clients()
        elif table == 'case':
            title = simpledialog.askstring("تعديل قضية", "عنوان القضية:", initialvalue=item['values'][1])
            client_id = simpledialog.askinteger("تعديل قضية", "رقم الموكل:", initialvalue=item['values'][2])
            status = simpledialog.askstring("تعديل قضية", "الحالة:", initialvalue=item['values'][3])
            db_query("UPDATE cases SET title=?, client_id=?, status=? WHERE id=?", (title, client_id, status, record_id))
            self.show_cases()
        elif table == 'session':
            case_id = simpledialog.askinteger("تعديل جلسة", "رقم القضية:", initialvalue=item['values'][1])
            date = simpledialog.askstring("تعديل جلسة", "التاريخ:", initialvalue=item['values'][2])
            time = simpledialog.askstring("تعديل جلسة", "الوقت:", initialvalue=item['values'][3])
            place = simpledialog.askstring("تعديل جلسة", "المكان:", initialvalue=item['values'][4])
            db_query("UPDATE sessions SET case_id=?, date=?, time=?, place=? WHERE id=?", (case_id, date, time, place, record_id))
            self.show_sessions()

    def delete_record(self, table):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("حذف", "يرجى تحديد سجل للحذف")
            return
        if messagebox.askyesno("تأكيد الحذف", "هل أنت متأكد من حذف هذا السجل؟"):
            item = self.tree.item(selected[0])
            record_id = item['values'][0]
            if table == 'client':
                db_query("DELETE FROM clients WHERE id=?", (record_id,))
                self.show_clients()
            elif table == 'case':
                db_query("DELETE FROM cases WHERE id=?", (record_id,))
                self.show_cases()
            elif table == 'session':
                db_query("DELETE FROM sessions WHERE id=?", (record_id,))
                self.show_sessions()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()