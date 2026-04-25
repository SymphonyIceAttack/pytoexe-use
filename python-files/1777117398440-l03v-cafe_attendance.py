import tkinter as tk
from tkinter import messagebox, filedialog
import cv2
import datetime
import os
import json
from PIL import Image, ImageTk
import threading

# إنشاء 20 موظف بأرقام سرية تبدأ من 2320 بفارق 5
الموظفون = {}
for i in range(1, 21):
    الرقم_السري = 2320 + (i - 1) * 5
    الموظفون[str(الرقم_السري)] = f"موظف {i}"

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("قهوتنا كافيه - نظام الحضور والانصراف")
        self.root.geometry("650x700")
        self.root.configure(bg='#8B4513')  # بني غامق (قهوة)
        
        # تعطيل تغيير حجم النافذة
        self.root.resizable(False, False)
        
        # تحميل إعدادات المجلد المحفوظة
        self.settings_file = "attendance_settings.json"
        self.save_folder = self.load_folder_setting()
        
        # إطار رئيسي
        main_frame = tk.Frame(root, bg='#D2691E', padx=20, pady=20)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # عنوان الكافيه
        title = tk.Label(main_frame, text="☕ قهوتنا كافيه ☕", 
                         font=('Arial', 26, 'bold'), 
                         bg='#D2691E', fg='#FFF8DC')
        title.pack(pady=15)
        
        # شعار توضيحي
        subtitle = tk.Label(main_frame, text="نظام تسجيل الحضور والانصراف", 
                            font=('Arial', 13), 
                            bg='#D2691E', fg='#FFE4B5')
        subtitle.pack(pady=5)
        
        # إطار اختيار مجلد الحفظ
        folder_frame = tk.Frame(main_frame, bg='#D2691E', relief='ridge', bd=2)
        folder_frame.pack(pady=15, fill='x')
        
        folder_label = tk.Label(folder_frame, text="📁 مجلد حفظ الصور:", 
                                 font=('Arial', 11, 'bold'), 
                                 bg='#D2691E', fg='white')
        folder_label.pack(side='left', padx=10, pady=5)
        
        self.folder_path_label = tk.Label(folder_frame, text=self.save_folder, 
                                          font=('Arial', 9), 
                                          bg='#D2691E', fg='#FFE4B5',
                                          wraplength=350)
        self.folder_path_label.pack(side='left', padx=10, pady=5, fill='x', expand=True)
        
        self.browse_btn = tk.Button(folder_frame, text="اختر مجلد", 
                                     font=('Arial', 9), 
                                     bg='#A0522D', fg='white',
                                     command=self.browse_folder,
                                     cursor="hand2")
        self.browse_btn.pack(side='right', padx=10, pady=5)
        
        # إطار إدخال الرقم السري
        input_frame = tk.Frame(main_frame, bg='#D2691E')
        input_frame.pack(pady=30)
        
        label_pin = tk.Label(input_frame, text="الرقم السري:", 
                             font=('Arial', 14, 'bold'), 
                             bg='#D2691E', fg='white')
        label_pin.grid(row=0, column=0, padx=10)
        
        self.pin_entry = tk.Entry(input_frame, font=('Arial', 14), width=15, show="*")
        self.pin_entry.grid(row=0, column=1, padx=10)
        self.pin_entry.bind('<Return>', self.capture_photo)  # ضغط Enter يلتقط الصورة
        
        # زر التقاط الصورة
        self.capture_btn = tk.Button(main_frame, text="📸 تسجيل الدخول", 
                                      font=('Arial', 14, 'bold'), 
                                      bg='#FFD700', fg='#8B4513',
                                      command=self.capture_photo,
                                      cursor="hand2")
        self.capture_btn.pack(pady=20)
        
        # منطقة عرض الحالة
        self.status_label = tk.Label(main_frame, text="✏️ أدخل الرقم السري واضغط Enter أو الزر", 
                                      font=('Arial', 11), 
                                      bg='#D2691E', fg='#FFE4B5')
        self.status_label.pack(pady=10)
        
        # إطار للفاصل
        separator = tk.Frame(main_frame, height=2, bg='#A0522D')
        separator.pack(fill='x', pady=15)
        
        # تذييل الصفحة (Footer)
        footer_frame = tk.Frame(main_frame, bg='#D2691E')
        footer_frame.pack(side='bottom', fill='x', pady=10)
        
        copyright_label = tk.Label(footer_frame, 
                                   text="© 2026 - قهوتنا كافيه", 
                                   font=('Arial', 9, 'bold'), 
                                   bg='#D2691E', fg='#FFD700')
        copyright_label.pack()
        
        credit_label = tk.Label(footer_frame, 
                                text="المهندس وليد درويش | powered by Eng. Walead Darweesh", 
                                font=('Arial', 8), 
                                bg='#D2691E', fg='#FFE4B5')
        credit_label.pack(pady=2)
        
        # إغلاق البرنامج
        exit_btn = tk.Button(main_frame, text="خروج", 
                             font=('Arial', 10), 
                             bg='#A0522D', fg='white',
                             command=self.safe_exit,
                             cursor="hand2")
        exit_btn.pack(pady=5)
        
        # تهيئة الكاميرا
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("خطأ", "لا يمكن الوصول إلى الكاميرا!")
            root.quit()
    
    def load_folder_setting(self):
        """تحميل إعدادات مجلد الحفظ من ملف"""
        # المجلد الافتراضي المطلوب
        default_folder = r"D:\قهوتنا كافيه\حضور الموظفين"
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    folder = settings.get("save_folder", default_folder)
                    return folder
            except:
                return default_folder
        return default_folder
    
    def save_folder_setting(self):
        """حفظ إعدادات مجلد الحفظ إلى ملف"""
        settings = {"save_folder": self.save_folder}
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except:
            pass
    
    def browse_folder(self):
        """فتح مستكشف الملفات لاختيار مجلد الحفظ"""
        folder_selected = filedialog.askdirectory(
            title="اختر مجلد حفظ صور الحضور",
            initialdir=self.save_folder if os.path.exists(self.save_folder) else os.getcwd()
        )
        
        if folder_selected:
            self.save_folder = folder_selected
            self.folder_path_label.config(text=self.save_folder)
            self.save_folder_setting()
            
            # التحقق من وجود المجلد وإنشاؤه إذا لزم الأمر
            if not os.path.exists(self.save_folder):
                os.makedirs(self.save_folder)
            
            messagebox.showinfo("تم التحديث", 
                               f"✅ تم تغيير مجلد حفظ الصور إلى:\n\n{self.save_folder}")
            self.status_label.config(text=f"📁 تم تغيير مجلد الحفظ إلى: {os.path.basename(self.save_folder)}", 
                                    fg="#FFD700")
            self.root.after(3000, self.clear_status)
    
    def capture_photo(self, event=None):
        pin = self.pin_entry.get().strip()
        
        # التحقق من الرقم السري
        if pin not in الموظفون:
            self.status_label.config(text="❌ رقم سري غير صحيح! حاول مرة أخرى", fg="red")
            # رسالة خطأ منبثقة
            messagebox.showerror("خطأ في الرقم السري", 
                                f"⚠️ الرقم السري {pin} غير صحيح!\n\nالرجاء المحاولة مرة أخرى.")
            self.pin_entry.delete(0, tk.END)
            return
        
        employee_name = الموظفون[pin]
        self.status_label.config(text=f"⏳ جاري التقاط الصورة لـ {employee_name}...", fg="yellow")
        self.root.update()
        
        # التقاط الصورة في thread منفصل
        threading.Thread(target=self.take_photo, args=(pin, employee_name)).start()
    
    def take_photo(self, pin, employee_name):
        ret, frame = self.cap.read()
        
        if ret:
            # إنشاء اسم الملف: التاريخ_الوقت_رقم_الموظف_الاسم.png
            now = datetime.datetime.now()
            filename = now.strftime(f"%Y-%m-%d_%H-%M-%S_{pin}_{employee_name}.png")
            
            # التحقق من وجود مجلد الحفظ وإنشاؤه إذا لزم الأمر
            if not os.path.exists(self.save_folder):
                os.makedirs(self.save_folder)
            
            full_path = os.path.join(self.save_folder, filename)
            cv2.imwrite(full_path, frame)
            
            # تنسيق الوقت والتاريخ للرسالة
            time_str = now.strftime("%I:%M %p")  # 12-hour format with AM/PM
            date_str = now.strftime("%Y/%m/%d")
            
            # رسالة تأكيد منبثقة للموظف (معدلة حسب الطلب)
            messagebox.showinfo("✅ تم التسجيل", 
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                                f"                     📸 قهوتنا كافيه 📸\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                                f"الموظف: {employee_name}\n"
                                f"الرقم السري: {pin}\n"
                                f"التاريخ: {date_str}\n"
                                f"الوقت: {time_str}\n\n"
                                f"✅ تم التسجيل\n\n"
                                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            # تحديث الواجهة
            self.status_label.config(text=f"✅ تم تسجيل حضور {employee_name} بنجاح!", fg="lightgreen")
            self.root.after(2000, self.clear_status)  # مسح الرسالة بعد 2 ثانية
            self.pin_entry.delete(0, tk.END)
        else:
            self.status_label.config(text="❌ فشل التقاط الصورة! تأكد من الكاميرا", fg="red")
            messagebox.showerror("خطأ في الكاميرا", 
                                "⚠️ فشل التقاط الصورة!\n\n"
                                "الرجاء التأكد من:\n"
                                "1. الكاميرا متصلة بشكل صحيح\n"
                                "2. لا يوجد برنامج آخر يستخدم الكاميرا\n"
                                "3. تم منح الإذن لاستخدام الكاميرا\n\n"
                                "ثم حاول مرة أخرى.")
    
    def clear_status(self):
        self.status_label.config(text="✏️ أدخل الرقم السري واضغط Enter أو الزر", fg="#FFE4B5")
    
    def safe_exit(self):
        if hasattr(self, 'cap'):
            self.cap.release()
        self.root.quit()
        self.root.destroy()
    
    def __del__(self):
        if hasattr(self, 'cap'):
            self.cap.release()

if __name__ == "__main__":
    root = tk.Tk()
    app = AttendanceApp(root)
    root.mainloop()