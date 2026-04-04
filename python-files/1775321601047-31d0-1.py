import tkinter as tk
from tkinter import ttk
import time
import random

class DigitalClock:
    def __init__(self, root):
        self.root = root
        self.root.title("ساعت دیجیتال لوکس | تقدیم به سیدعبدالمصور")
        self.root.geometry("550x450")
        self.root.configure(bg='#1a1a2e')
        
        # غیرقابل تغییر اندازه
        self.root.resizable(False, False)
        
        # عنوان برنامه با اسم خاص
        title_label = tk.Label(
            root, 
            text="⏰ ساعت دیجیتال لوکس ⏰", 
            font=('Vazir', 16, 'bold'),
            bg='#1a1a2e',
            fg='#e94560'
        )
        title_label.pack(pady=10)
        
        # ========== تقدیم به سیدعبدالمصور ==========
        dedication_frame = tk.Frame(
            root,
            bg='#0f3460',
            relief=tk.RAISED,
            bd=3
        )
        dedication_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # افکت چشمک زن برای متن تقدیم
        self.dedication_label = tk.Label(
            dedication_frame,
            text="✨ تقدیم به سیدعبدالمصور عزیز ✨\nکه با نقدهای قشنگش دل ما رو روشن می‌کنه",
            font=('Vazir', 11, 'bold'),
            bg='#0f3460',
            fg='#ffd700',
            justify='center'
        )
        self.dedication_label.pack(pady=10)
        
        # متن‌های نقد برای تغییر تصادفی
        self.critique_texts = [
            "🎭 سیدعبدالمصور می‌گه: این ساعت رو دوست دارم!",
            "🔥 نقد سیدعبدالمصور: عالیه داداش! ادامه بده!",
            "⭐ سیدعبدالمصور: 5 ستاره می‌دم به این برنامه",
            "🎨 نقد حرفه‌ای: رنگ‌بندی خیلی قشنگ شده!",
            "💪 سیدعبدالمصور می‌گه: خداقوت! خیلی خوب شد!",
            "🎯 نقد: دقیقاً همون چیزی که می‌خواستم!",
            "🌟 نظر سیدعبدالمصور: بی‌نظیر بود!"
        ]
        
        self.critique_label = tk.Label(
            root,
            text=random.choice(self.critique_texts),
            font=('Vazir', 10, 'italic'),
            bg='#1a1a2e',
            fg='#00ffcc',
            wraplength=500,
            justify='center'
        )
        self.critique_label.pack(pady=5)
        
        # فریم اصلی برای ساعت
        self.clock_frame = tk.Frame(
            root, 
            bg='#16213e',
            relief=tk.RAISED,
            bd=5
        )
        self.clock_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # نمایش ساعت
        self.time_label = tk.Label(
            self.clock_frame,
            font=('DS-Digital', 60, 'bold'),
            bg='#16213e',
            fg='#0f3460'
        )
        self.time_label.pack(pady=30)
        
        # نمایش تاریخ
        self.date_label = tk.Label(
            self.clock_frame,
            font=('Vazir', 14),
            bg='#16213e',
            fg='#e94560'
        )
        self.date_label.pack(pady=10)
        
        # نمایش روز هفته
        self.day_label = tk.Label(
            self.clock_frame,
            font=('Vazir', 12),
            bg='#16213e',
            fg='#533483'
        )
        self.day_label.pack(pady=5)
        
        # دکمه خروج با طراحی زیبا
        exit_btn = tk.Button(
            root,
            text="🚪 خروج | با تشکر از سیدعبدالمصور",
            command=self.root.quit,
            font=('Vazir', 10, 'bold'),
            bg='#e94560',
            fg='white',
            activebackground='#c73d54',
            activeforeground='white',
            cursor='hand2',
            bd=0,
            padx=20,
            pady=8
        )
        exit_btn.pack(pady=10)
        
        # بروزرسانی ساعت و تغییر نقدها
        self.update_time()
        self.update_critique()  # برای تغییر خودکار نقدها
    
    def update_time(self):
        # دریافت زمان فعلی
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%Y/%m/%d")
        
        # روز هفته به فارسی
        week_days = {
            'Monday': 'دوشنبه',
            'Tuesday': 'سه‌شنبه', 
            'Wednesday': 'چهارشنبه',
            'Thursday': 'پنج‌شنبه',
            'Friday': 'جمعه',
            'Saturday': 'شنبه',
            'Sunday': 'یک‌شنبه'
        }
        
        eng_day = time.strftime("%A")
        persian_day = week_days.get(eng_day, eng_day)
        
        # تغییر رنگ ساعت بر اساس زمان
        hour = int(time.strftime("%H"))
        
        if hour < 12:
            color = '#00b4d8'  # آبی روشن (صبح)
        elif hour < 18:
            color = '#f77f00'  # نارنجی (بعدازظهر)
        else:
            color = '#e94560'  # قرمز (شب)
        
        self.time_label.config(
            text=current_time,
            fg=color
        )
        self.date_label.config(text=f"📅 {current_date}")
        self.day_label.config(text=f"📆 {persian_day}")
        
        # بروزرسانی هر ۱ ثانیه
        self.root.after(1000, self.update_time)
    
    def update_critique(self):
        # تغییر تصادفی نقد سیدعبدالمصور هر 5 ثانیه
        new_text = random.choice(self.critique_texts)
        
        # افکت محو و ظاهر شدن (اختیاری)
        def change_text():
            self.critique_label.config(text=new_text)
        
        # هر 5 ثانیه یک نقد جدید
        self.root.after(5000, lambda: self.critique_label.config(text=random.choice(self.critique_texts)))
        self.root.after(5000, self.update_critique)

# اجرای برنامه
if __name__ == "__main__":
    root = tk.Tk()
    app = DigitalClock(root)
    root.mainloop()