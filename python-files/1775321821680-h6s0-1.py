import tkinter as tk
from tkinter import ttk, messagebox
import jdatetime
from datetime import datetime
import random

class DateConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("مبدل تاریخ | با نقدهای سیدعبدالمصور")
        self.root.geometry("600x550")
        self.root.configure(bg='#2d2d44')
        self.root.resizable(False, False)
        
        # متن‌های نقد سیدعبدالمصور
        self.praise_texts = [
            "🔥 سیدعبدالمصور: این مبدل تاریخ عالیه!",
            "⭐ نظر سیدعبدالمصور: ۱۰ از ۱۰! ادامه بده!",
            "🎯 سیدعبدالمصور می‌گه: دقیقاً همون چیزی که می‌خواستم!",
            "💪 نقد حرفه‌ای: خیلی کاربردی و قشنگه!",
            "🎨 سیدعبدالمصور: رنگ‌بندی و دیزاینش بی‌نظره!",
            "🌟 سیدعبدالمصور: دمت گرم داداش! عالی کار می‌کنی!",
            "⚡ نظر سید: سریع و دقیق! عالیه!",
            "🏆 سیدعبدالمصور: این برنامه حرفه‌ای ساخته شده!",
            "🎭 بازم سید: خیلی به دردم خورد! ممنون!",
            "✨ سیدعبدالمصور: ایول داداش! به این می‌گن برنامه!"
        ]
        
        # عنوان اصلی
        title_frame = tk.Frame(root, bg='#1e1e2e', relief=tk.RAISED, bd=3)
        title_frame.pack(pady=15, padx=20, fill=tk.X)
        
        title_label = tk.Label(
            title_frame,
            text="📅 مبدل تاریخ شمسی به میلادی و برعکس 📅",
            font=('Vazir', 16, 'bold'),
            bg='#1e1e2e',
            fg='#ff6b6b'
        )
        title_label.pack(pady=10)
        
        # ========== بخش تقدیم به سیدعبدالمصور ==========
        dedication_frame = tk.Frame(root, bg='#4a2c5e', relief=tk.RAISED, bd=2)
        dedication_frame.pack(pady=10, padx=20, fill=tk.X)
        
        dedication_label = tk.Label(
            dedication_frame,
            text="✨ تقدیم به استاد بزرگ، سیدعبدالمصور ✨\nکه با نقدهای قشنگش باعث دلگرمی ماست",
            font=('Vazir', 10, 'bold'),
            bg='#4a2c5e',
            fg='#ffd93d',
            justify='center'
        )
        dedication_label.pack(pady=8)
        
        # نقد زنده سیدعبدالمصور
        self.critique_label = tk.Label(
            root,
            text=random.choice(self.praise_texts),
            font=('Vazir', 10, 'italic'),
            bg='#2d2d44',
            fg='#6c5ce7',
            wraplength=550,
            justify='center',
            relief=tk.SUNKEN,
            bd=1
        )
        self.critique_label.pack(pady=8, padx=20, fill=tk.X)
        
        # فریم اصلی
        main_frame = tk.Frame(root, bg='#2d2d44')
        main_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # بخش تبدیل شمسی به میلادی
        solar_frame = tk.LabelFrame(
            main_frame,
            text="🌞 تبدیل تاریخ شمسی به میلادی",
            font=('Vazir', 12, 'bold'),
            bg='#3d3d5c',
            fg='#00cec9',
            relief=tk.RIDGE,
            bd=3
        )
        solar_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # ورودی شمسی
        solar_input_frame = tk.Frame(solar_frame, bg='#3d3d5c')
        solar_input_frame.pack(pady=10)
        
        tk.Label(solar_input_frame, text="سال:", font=('Vazir', 10), bg='#3d3d5c', fg='white').grid(row=0, column=0, padx=5)
        self.solar_year = tk.Entry(solar_input_frame, width=10, font=('Vazir', 10), justify='center')
        self.solar_year.grid(row=0, column=1, padx=5)
        
        tk.Label(solar_input_frame, text="ماه:", font=('Vazir', 10), bg='#3d3d5c', fg='white').grid(row=0, column=2, padx=5)
        self.solar_month = tk.Entry(solar_input_frame, width=10, font=('Vazir', 10), justify='center')
        self.solar_month.grid(row=0, column=3, padx=5)
        
        tk.Label(solar_input_frame, text="روز:", font=('Vazir', 10), bg='#3d3d5c', fg='white').grid(row=0, column=4, padx=5)
        self.solar_day = tk.Entry(solar_input_frame, width=10, font=('Vazir', 10), justify='center')
        self.solar_day.grid(row=0, column=5, padx=5)
        
        # دکمه تبدیل شمسی به میلادی
        solar_btn = tk.Button(
            solar_frame,
            text="🔄 تبدیل به میلادی",
            command=self.convert_solar_to_gregorian,
            font=('Vazir', 10, 'bold'),
            bg='#00b894',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=20,
            pady=5
        )
        solar_btn.pack(pady=10)
        
        # نتیجه شمسی به میلادی
        self.solar_result = tk.Label(
            solar_frame,
            text="نتیجه: ---",
            font=('Vazir', 11, 'bold'),
            bg='#2d2d44',
            fg='#fdcb6e',
            pady=10
        )
        self.solar_result.pack()
        
        # جداکننده
        separator = tk.Frame(main_frame, height=2, bg='#ff7675')
        separator.pack(fill=tk.X, pady=10)
        
        # بخش تبدیل میلادی به شمسی
        gregorian_frame = tk.LabelFrame(
            main_frame,
            text="🌍 تبدیل تاریخ میلادی به شمسی",
            font=('Vazir', 12, 'bold'),
            bg='#3d3d5c',
            fg='#fd79a8',
            relief=tk.RIDGE,
            bd=3
        )
        gregorian_frame.pack(pady=10, padx=10, fill=tk.X)
        
        # ورودی میلادی
        gregorian_input_frame = tk.Frame(gregorian_frame, bg='#3d3d5c')
        gregorian_input_frame.pack(pady=10)
        
        tk.Label(gregorian_input_frame, text="سال:", font=('Vazir', 10), bg='#3d3d5c', fg='white').grid(row=0, column=0, padx=5)
        self.gregorian_year = tk.Entry(gregorian_input_frame, width=10, font=('Vazir', 10), justify='center')
        self.gregorian_year.grid(row=0, column=1, padx=5)
        
        tk.Label(gregorian_input_frame, text="ماه:", font=('Vazir', 10), bg='#3d3d5c', fg='white').grid(row=0, column=2, padx=5)
        self.gregorian_month = tk.Entry(gregorian_input_frame, width=10, font=('Vazir', 10), justify='center')
        self.gregorian_month.grid(row=0, column=3, padx=5)
        
        tk.Label(gregorian_input_frame, text="روز:", font=('Vazir', 10), bg='#3d3d5c', fg='white').grid(row=0, column=4, padx=5)
        self.gregorian_day = tk.Entry(gregorian_input_frame, width=10, font=('Vazir', 10), justify='center')
        self.gregorian_day.grid(row=0, column=5, padx=5)
        
        # دکمه تبدیل میلادی به شمسی
        gregorian_btn = tk.Button(
            gregorian_frame,
            text="🔄 تبدیل به شمسی",
            command=self.convert_gregorian_to_solar,
            font=('Vazir', 10, 'bold'),
            bg='#e17055',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=20,
            pady=5
        )
        gregorian_btn.pack(pady=10)
        
        # نتیجه میلادی به شمسی
        self.gregorian_result = tk.Label(
            gregorian_frame,
            text="نتیجه: ---",
            font=('Vazir', 11, 'bold'),
            bg='#2d2d44',
            fg='#fdcb6e',
            pady=10
        )
        self.gregorian_result.pack()
        
        # دکمه خروج
        exit_btn = tk.Button(
            root,
            text="🚪 خروج | با تشکر از سیدعبدالمصور",
            command=self.exit_app,
            font=('Vazir', 10, 'bold'),
            bg='#d63031',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=20,
            pady=8
        )
        exit_btn.pack(pady=15)
        
        # بروزرسانی خودکار نقدها
        self.update_critique()
    
    def convert_solar_to_gregorian(self):
        try:
            year = int(self.solar_year.get())
            month = int(self.solar_month.get())
            day = int(self.solar_day.get())
            
            # تبدیل تاریخ شمسی به میلادی
            gregorian_date = jdatetime.date(year, month, day).togregorian()
            
            result_text = f"📅 نتیجه: {gregorian_date.year}/{gregorian_date.month:02d}/{gregorian_date.day:02d}"
            self.solar_result.config(text=result_text, fg='#00cec9')
            
            # نقد خوشحال کننده از سیدعبدالمصور
            self.show_temporary_praise()
            
        except Exception as e:
            messagebox.showerror("خطا", "تاریخ شمسی نامعتبر است!\nلطفاً تاریخ صحیح وارد کنید.")
            self.solar_result.config(text="نتیجه: ❌ خطا در تبدیل", fg='#ff7675')
    
    def convert_gregorian_to_solar(self):
        try:
            year = int(self.gregorian_year.get())
            month = int(self.gregorian_month.get())
            day = int(self.gregorian_day.get())
            
            # تبدیل تاریخ میلادی به شمسی
            gregorian_date = datetime(year, month, day)
            solar_date = jdatetime.date.fromgregorian(date=gregorian_date)
            
            # نمایش به صورت شمسی
            month_names = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                          'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
            
            result_text = f"📅 نتیجه: {solar_date.year} {month_names[solar_date.month-1]} {solar_date.day}"
            self.gregorian_result.config(text=result_text, fg='#fd79a8')
            
            # نقد خوشحال کننده از سیدعبدالمصور
            self.show_temporary_praise()
            
        except Exception as e:
            messagebox.showerror("خطا", "تاریخ میلادی نامعتبر است!\nلطفاً تاریخ صحیح وارد کنید.")
            self.gregorian_result.config(text="نتیجه: ❌ خطا در تبدیل", fg='#ff7675')
    
    def show_temporary_praise(self):
        # ذخیره متن قبلی
        old_text = self.critique_label.cget("text")
        praise = random.choice(self.praise_texts)
        self.critique_label.config(text=f"🎉 {praise} 🎉", fg='#00ffcc')
        # برگشت به حالت عادی بعد از 3 ثانیه
        self.root.after(3000, lambda: self.critique_label.config(text=random.choice(self.praise_texts), fg='#6c5ce7'))
    
    def update_critique(self):
        # تغییر تصادفی نقد سیدعبدالمصور هر 6 ثانیه
        new_text = random.choice(self.praise_texts)
        self.critique_label.config(text=new_text)
        self.root.after(6000, self.update_critique)
    
    def exit_app(self):
        # پیام خداحافظی با سیدعبدالمصور
        messagebox.showinfo(
            "خداحافظی",
            "👋 سیدعبدالمصور جان!\n"
            "ممنون که از مبدل تاریخ استفاده کردی.\n"
            "بازم به ما سر بزن! 😊"
        )
        self.root.quit()

# نصب کتابخانه مورد نیاز
# قبل از اجرا، jdatetime رو نصب کن: pip install jdatetime

if __name__ == "__main__":
    root = tk.Tk()
    app = DateConverter(root)
    root.mainloop()