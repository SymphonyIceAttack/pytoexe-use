# تحويل_PDF_GUI.py
import os
import fitz  # PyMuPDF
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from threading import Thread
import shutil

class محولPDFإلىصور:
    def __init__(self, النافذة):
        self.النافذة = النافذة
        self.النافذة.title("محول PDF إلى صور - ترتيب الفوضى")
        self.النافذة.geometry("700x600")
        
        # محاولة تعيين الأيقونة
        try:
            self.النافذة.iconbitmap('icon.ico')
        except:
            pass
        
        self.إنشاء_الواجهة()
    
    def إنشاء_الواجهة(self):
        # الإطار الرئيسي
        الإطار_الرئيسي = ttk.Frame(self.النافذة, padding="20")
        الإطار_الرئيسي.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # العنوان
        العنوان = ttk.Label(
            الإطار_الرئيسي, 
            text="📚 محول PDF إلى صور", 
            font=('Arial', 20, 'bold')
        )
        العنوان.grid(row=0, column=0, columnspan=3, pady=20)
        
        # قسم مجلد PDF
        ttk.Label(الإطار_الرئيسي, text="مجلد PDF:", font=('Arial', 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        إطار_pdf = ttk.Frame(الإطار_الرئيسي)
        إطار_pdf.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.مسار_pdf = tk.StringVar()
        ttk.Entry(إطار_pdf, textvariable=self.مسار_pdf, width=50).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(إطار_pdf, text="استعراض", command=lambda: self.اختيار_مجلد('pdf')).pack(side=tk.LEFT)
        
        # قسم مجلد الإخراج
        ttk.Label(الإطار_الرئيسي, text="مجلد الحفظ:", font=('Arial', 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        إطار_حفظ = ttk.Frame(الإطار_الرئيسي)
        إطار_حفظ.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.مسار_الحفظ = tk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Desktop', 'صور_PDF'))
        ttk.Entry(إطار_حفظ, textvariable=self.مسار_الحفظ, width=50).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(إطار_حفظ, text="استعراض", command=lambda: self.اختيار_مجلد('حفظ')).pack(side=tk.LEFT)
        
        # خيارات إضافية
        إطار_خيارات = ttk.LabelFrame(الإطار_الرئيسي, text="خيارات التحويل", padding="10")
        إطار_خيارات.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=20)
        
        # دقة الصورة
        ttk.Label(إطار_خيارات, text="دقة الصورة:").grid(row=0, column=0, sticky=tk.W, padx=10)
        self.الدقة = tk.StringVar(value="2")
        ttk.Combobox(إطار_خيارات, textvariable=self.الدقة, values=["1", "1.5", "2", "2.5", "3"], width=10).grid(row=0, column=1, sticky=tk.W)
        ttk.Label(إطار_خيارات, text="(1 = منخفضة, 2 = عالية, 3 = فائقة)").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        # صيغة الصورة
        ttk.Label(إطار_خيارات, text="صيغة الصورة:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=10)
        self.صيغة = tk.StringVar(value="png")
        ttk.Combobox(إطار_خيارات, textvariable=self.صيغة, values=["png", "jpg", "jpeg", "bmp"], width=10).grid(row=1, column=1, sticky=tk.W)
        
        # شريط التقدم
        ttk.Label(الإطار_الرئيسي, text="التقدم:", font=('Arial', 11)).grid(row=4, column=0, sticky=tk.W, pady=10)
        self.شريط_التقدم = ttk.Progressbar(الإطار_الرئيسي, length=400, mode='determinate')
        self.شريط_التقدم.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # نص الحالة
        self.حالة_النص = tk.Text(الإطار_الرئيسي, height=10, width=80, state='disabled')
        self.حالة_النص.grid(row=5, column=0, columnspan=3, pady=10)
        
        # تمرير للنص
        تمرير = ttk.Scrollbar(الإطار_الرئيسي, orient='vertical', command=self.حالة_النص.yview)
        تمرير.grid(row=5, column=3, sticky=(tk.N, tk.S))
        self.حالة_النص['yscrollcommand'] = تمرير.set
        
        # أزرار التحكم
        إطار_أزرار = ttk.Frame(الإطار_الرئيسي)
        إطار_أزرار.grid(row=6, column=0, columnspan=3, pady=20)
        
        self.زر_بدء = ttk.Button(إطار_أزرار, text="🚀 بدء التحويل", command=self.بدء_التحويل, width=20)
        self.زر_بدء.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(إطار_أزرار, text="🧹 مسح النص", command=self.مسح_النص, width=15).pack(side=tk.LEFT, padx=10)
        
        # تكبير الأعمدة
        self.النافذة.columnconfigure(0, weight=1)
        الإطار_الرئيسي.columnconfigure(1, weight=1)
    
    def اختيار_مجلد(self, نوع):
        if نوع == 'pdf':
            مجلد = filedialog.askdirectory(title="اختر مجلد PDF")
            if مجلد:
                self.مسار_pdf.set(مجلد)
        else:
            مجلد = filedialog.askdirectory(title="اختر مجلد الحفظ")
            if مجلد:
                self.مسار_الحفظ.set(مجلد)
    
    def إضافة_نص_حالة(self, نص):
        self.حالة_النص.configure(state='normal')
        self.حالة_النص.insert(tk.END, نص + '\n')
        self.حالة_النص.see(tk.END)
        self.حالة_النص.configure(state='disabled')
        self.النافذة.update_idletasks()
    
    def مسح_النص(self):
        self.حالة_النص.configure(state='normal')
        self.حالة_النص.delete(1.0, tk.END)
        self.حالة_النص.configure(state='disabled')
    
    def بدء_التحويل(self):
        if not self.مسار_pdf.get():
            messagebox.showerror("خطأ", "الرجاء اختيار مجلد PDF")
            return
        
        if not self.مسار_الحفظ.get():
            messagebox.showerror("خطأ", "الرجاء اختيار مجلد الحفظ")
            return
        
        self.زر_بدء.configure(state='disabled')
        self.شريط_التقدم['value'] = 0
        
        # تشغيل التحويل في خيط منفصل
        خيط = Thread(target=self.تحويل)
        خيط.daemon = True
        خيط.start()
    
    def تحويل(self):
        try:
            مجلد_pdf = self.مسار_pdf.get()
            مجلد_الحفظ = self.مسار_الحفظ.get()
            
            Path(مجلد_الحفظ).mkdir(parents=True, exist_ok=True)
            
            # البحث عن ملفات PDF
            ملفات_pdf = []
            for جذر, مجلدات, ملفات in os.walk(مجلد_pdf):
                for ملف in ملفات:
                    if ملف.lower().endswith('.pdf'):
                        ملفات_pdf.append(os.path.join(جذر, ملف))
            
            if not ملفات_pdf:
                self.إضافة_نص_حالة("❌ لا توجد ملفات PDF في المجلد المحدد")
                return
            
            self.إضافة_نص_حالة(f"📊 تم العثور على {len(ملفات_pdf)} ملف PDF")
            
            عداد_الصور = 1
            اجمالي_الصفحات = 0
            
            for i, مسار_pdf in enumerate(ملفات_pdf, 1):
                اسم_الملف = os.path.basename(مسار_pdf)
                self.إضافة_نص_حالة(f"\n📄 معالجة {i}/{len(ملفات_pdf)}: {اسم_الملف}")
                
                try:
                    مستند_pdf = fitz.open(مسار_pdf)
                    عدد_الصفحات = len(مستند_pdf)
                    اجمالي_الصفحات += عدد_الصفحات
                    
                    مصفوفة = fitz.Matrix(float(self.الدقة.get()), float(self.الدقة.get()))
                    
                    for رقم_الصفحة in range(عدد_الصفحات):
                        الصفحة = مستند_pdf[رقم_الصفحة]
                        بيكسل_ماب = الصفحة.get_pixmap(matrix=مصفوفة)
                        
                        اسم_الصورة = f"صفحة_{عداد_الصور:06d}.{self.صيغة.get()}"
                        مسار_الحفظ = os.path.join(مجلد_الحفظ, اسم_الصورة)
                        
                        بيكسل_ماب.save(مسار_الحفظ)
                        
                        progress = (i - 1 + (رقم_الصفحة + 1) / عدد_الصفحات) / len(ملفات_pdf) * 100
                        self.شريط_التقدم['value'] = progress
                        
                        عداد_الصور += 1
                        
                        if رقم_الصفحة % 5 == 0:  # تحديث كل 5 صفحات
                            self.إضافة_نص_حالة(f"   ✅ تم حفظ الصفحة {رقم_الصفحة + 1}/{عدد_الصفحات}")
                    
                    مستند_pdf.close()
                    
                except Exception as خطأ:
                    self.إضافة_نص_حالة(f"   ❌ خطأ: {خطأ}")
            
            self.إضافة_نص_حالة("\n" + "=" * 50)
            self.إضافة_نص_حالة("✅ تم الانتهاء بنجاح!")
            self.إضافة_نص_حالة(f"📊 إجمالي الصور: {عداد_الصور - 1}")
            self.إضافة_نص_حالة(f"📂 الموقع: {مجلد_الحفظ}")
            self.إضافة_نص_حالة("=" * 50)
            
            messagebox.showinfo("نجاح", f"تم تحويل {عداد_الصور - 1} صورة بنجاح!")
            
        except Exception as خطأ:
            self.إضافة_نص_حالة(f"❌ خطأ عام: {خطأ}")
            messagebox.showerror("خطأ", f"حدث خطأ: {خطأ}")
        
        finally:
            self.زر_بدء.configure(state='normal')

if __name__ == "__main__":
    # التحقق من المكتبات
    try:
        import fitz
    except ImportError:
        import subprocess
        subprocess.call(['pip', 'install', 'PyMuPDF'])
        import fitz
    
    النافذة = tk.Tk()
    التطبيق = محولPDFإلىصور(النافذة)
    النافذة.mainloop()