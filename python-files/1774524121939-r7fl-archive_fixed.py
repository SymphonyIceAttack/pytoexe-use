import sqlite3
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import os
import sys
from datetime import datetime
from io import BytesIO

class ArchiveSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("نظام الأرشيف الإلكتروني")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f0f0f0')
        
        # تحديد المسار الصحيح للملفات (لما يكون EXE)
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(__file__)
        
        self.db_path = os.path.join(self.base_path, 'archive.db')
        
        # إنشاء قاعدة البيانات
        self.create_database()
        
        # تصميم الواجهة
        self.setup_ui()
        
        # عرض جميع المعاملات
        self.show_all_transactions()
    
    def create_database(self):
        """إنشاء قاعدة بيانات SQLite"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # إنشاء جدول المعاملات
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_number TEXT UNIQUE,
                transaction_date TEXT,
                customer_name TEXT,
                customer_phone TEXT,
                transaction_type TEXT,
                amount REAL,
                notes TEXT,
                image_data BLOB,
                created_at TEXT
            )
        ''')
        
        # إنشاء جدول للمرفقات الإضافية
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                file_name TEXT,
                file_data BLOB,
                file_type TEXT,
                upload_date TEXT,
                FOREIGN KEY (transaction_id) REFERENCES transactions (id)
            )
        ''')
        
        self.conn.commit()
    
    def setup_ui(self):
        """تصميم الواجهة الرئيسية"""
        # إطار الإدخال (الجانب الأيمن)
        input_frame = tk.Frame(self.root, bg='white', relief=tk.RAISED, borderwidth=2)
        input_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        
        # عنوان
        tk.Label(input_frame, text="إضافة معاملة جديدة", 
                font=('Arial', 16, 'bold'), bg='white').pack(pady=10)
        
        # حقول الإدخال
        fields = [
            ('رقم المعاملة:', 'entry_number'),
            ('التاريخ (YYYY-MM-DD):', 'entry_date'),
            ('اسم العميل:', 'entry_customer'),
            ('تليفون العميل:', 'entry_phone'),
            ('نوع المعاملة:', 'entry_type'),
            ('المبلغ:', 'entry_amount')
        ]
        
        self.entries = {}
        for label, key in fields:
            frame = tk.Frame(input_frame, bg='white')
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=label, width=15, anchor='w', 
                    bg='white').pack(side=tk.LEFT)
            
            if key == 'entry_type':
                self.entries[key] = ttk.Combobox(frame, values=['بيع', 'شراء', 'استرجاع', 'صيانة'])
                self.entries[key].pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                self.entries[key] = tk.Entry(frame)
                self.entries[key].pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # ملاحظات
        tk.Label(input_frame, text="الملاحظات:", bg='white').pack(anchor='w', padx=10, pady=5)
        self.notes_text = scrolledtext.ScrolledText(input_frame, height=5, width=40)
        self.notes_text.pack(padx=10, pady=5)
        
        # إضافة صورة
        tk.Button(input_frame, text="إضافة صورة للمعاملة", 
                 command=self.add_image, bg='lightblue', 
                 font=('Arial', 10)).pack(pady=10)
        self.image_path = None
        self.image_preview = None
        
        # إضافة مرفقات
        tk.Button(input_frame, text="إضافة مرفقات (ملفات)", 
                 command=self.add_attachment, bg='lightgreen',
                 font=('Arial', 10)).pack(pady=5)
        self.attachments = []
        
        # زر الحفظ
        tk.Button(input_frame, text="حفظ المعاملة", 
                 command=self.save_transaction, bg='green', fg='white',
                 font=('Arial', 12, 'bold')).pack(pady=20)
        
        # إطار عرض البيانات (الجانب الأيسر)
        display_frame = tk.Frame(self.root, bg='white')
        display_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # شريط البحث
        search_frame = tk.Frame(display_frame, bg='white')
        search_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(search_frame, text="بحث:", bg='white').pack(side=tk.LEFT, padx=5)
        self.search_entry = tk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="بحث", command=self.search_transactions).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="عرض الكل", command=self.show_all_transactions).pack(side=tk.LEFT, padx=5)
        
        # جدول عرض المعاملات
        columns = ('id', 'رقم المعاملة', 'التاريخ', 'العميل', 'النوع', 'المبلغ')
        self.tree = ttk.Treeview(display_frame, columns=columns, show='headings', height=20)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.column('id', width=50)
        self.tree.column('رقم المعاملة', width=120)
        self.tree.column('العميل', width=150)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # ربط حدث النقر على الصف
        self.tree.bind('<ButtonRelease-1>', self.on_row_click)
        
        # إطار لعرض التفاصيل والصورة
        details_frame = tk.Frame(display_frame, bg='lightgray', height=200)
        details_frame.pack(fill=tk.X, pady=10)
        
        self.details_text = tk.Text(details_frame, height=8, width=50)
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.image_label = tk.Label(details_frame, bg='lightgray', text="لا توجد صورة")
        self.image_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def add_image(self):
        """إضافة صورة للمعاملة"""
        file_path = filedialog.askopenfilename(
            title="اختر صورة",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.bmp")]
        )
        if file_path:
            self.image_path = file_path
            messagebox.showinfo("تم", "تم إضافة الصورة بنجاح")
    
    def add_attachment(self):
        """إضافة مرفقات"""
        files = filedialog.askopenfilenames(
            title="اختر المرفقات",
            filetypes=[("All files", "*.*")]
        )
        for file in files:
            self.attachments.append(file)
        messagebox.showinfo("تم", f"تم إضافة {len(files)} مرفق")
    
    def save_transaction(self):
        """حفظ المعاملة في قاعدة البيانات"""
        try:
            # جمع البيانات
            trans_number = self.entries['entry_number'].get()
            trans_date = self.entries['entry_date'].get()
            customer = self.entries['entry_customer'].get()
            phone = self.entries['entry_phone'].get()
            trans_type = self.entries['entry_type'].get()
            amount = self.entries['entry_amount'].get()
            notes = self.notes_text.get("1.0", tk.END).strip()
            
            if not trans_number:
                messagebox.showwarning("تنبيه", "رقم المعاملة مطلوب")
                return
            
            # تحويل الصورة إلى BLOB
            image_blob = None
            if self.image_path and os.path.exists(self.image_path):
                with open(self.image_path, 'rb') as f:
                    image_blob = f.read()
            
            # إدخال المعاملة
            self.cursor.execute('''
                INSERT INTO transactions 
                (transaction_number, transaction_date, customer_name, customer_phone, 
                 transaction_type, amount, notes, image_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (trans_number, trans_date, customer, phone, trans_type, 
                  float(amount) if amount else 0, notes, image_blob, 
                  datetime.now().isoformat()))
            
            transaction_id = self.cursor.lastrowid
            
            # إضافة المرفقات
            for file_path in self.attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    self.cursor.execute('''
                        INSERT INTO attachments (transaction_id, file_name, file_data, file_type, upload_date)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (transaction_id, os.path.basename(file_path), file_data, 
                          os.path.splitext(file_path)[1], datetime.now().isoformat()))
            
            self.conn.commit()
            
            messagebox.showinfo("نجاح", "تم حفظ المعاملة بنجاح!")
            self.clear_form()
            self.show_all_transactions()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ: {str(e)}")
    
    def clear_form(self):
        """مسح حقول الإدخال"""
        for key, entry in self.entries.items():
            if isinstance(entry, tk.Entry):
                entry.delete(0, tk.END)
            elif isinstance(entry, ttk.Combobox):
                entry.set('')
        self.notes_text.delete("1.0", tk.END)
        self.image_path = None
        self.attachments = []
        self.image_label.config(image='', text="لا توجد صورة")
    
    def show_all_transactions(self):
        """عرض جميع المعاملات في الجدول"""
        # مسح الجدول
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # جلب البيانات
        self.cursor.execute('''
            SELECT id, transaction_number, transaction_date, customer_name, 
                   transaction_type, amount 
            FROM transactions 
            ORDER BY id DESC
        ''')
        
        for row in self.cursor.fetchall():
            self.tree.insert('', tk.END, values=row)
    
    def search_transactions(self):
        """البحث عن المعاملات"""
        search_text = self.search_entry.get()
        
        # مسح الجدول
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # البحث في عدة أعمدة
        self.cursor.execute('''
            SELECT id, transaction_number, transaction_date, customer_name, 
                   transaction_type, amount 
            FROM transactions 
            WHERE transaction_number LIKE ? 
               OR customer_name LIKE ? 
               OR customer_phone LIKE ?
            ORDER BY id DESC
        ''', (f'%{search_text}%', f'%{search_text}%', f'%{search_text}%'))
        
        for row in self.cursor.fetchall():
            self.tree.insert('', tk.END, values=row)
    
    def on_row_click(self, event):
        """عند النقر على صف في الجدول"""
        selected = self.tree.selection()
        if not selected:
            return
        
        # جلب ID المعاملة
        item = self.tree.item(selected[0])
        trans_id = item['values'][0]
        
        # جلب التفاصيل كاملة
        self.cursor.execute('''
            SELECT * FROM transactions WHERE id = ?
        ''', (trans_id,))
        
        trans = self.cursor.fetchone()
        
        if trans:
            # عرض التفاصيل
            details = f"""
رقم المعاملة: {trans[1]}
التاريخ: {trans[2]}
العميل: {trans[3]}
التليفون: {trans[4]}
النوع: {trans[5]}
المبلغ: {trans[6]}
الملاحظات: {trans[7]}
تاريخ الإضافة: {trans[9]}
            """
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert("1.0", details)
            
            # عرض الصورة إن وجدت
            if trans[8]:  # image_data
                try:
                    image_data = trans[8]
                    img = Image.open(BytesIO(image_data))
                    img.thumbnail((200, 200))
                    photo = ImageTk.PhotoImage(img)
                    self.image_label.config(image=photo, text="")
                    self.image_label.image = photo
                except Exception as e:
                    self.image_label.config(image='', text=f"خطأ: {str(e)}")
            else:
                self.image_label.config(image='', text="لا توجد صورة")

# تشغيل البرنامج
if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveSystem(root)
    root.mainloop()