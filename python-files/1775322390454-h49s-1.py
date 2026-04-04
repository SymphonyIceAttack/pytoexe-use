import tkinter as tk
from tkinter import messagebox
import random
from datetime import datetime
import threading

class FortuneTeller:
    def __init__(self, root):
        self.root = root
        self.root.title("فال روز")
        self.root.geometry("600x550")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(False, False)
        
        # مرکز کردن پنجره
        self.center_window()
        
        # بیش از 30 فال متنوع و جذاب
        self.all_fortunes = [
            "🌈 امروز روز خوبی برای شروع کارهای جدید است",
            "💰 یک خبر خوب مالی به زودی به تو می‌رسد",
            "❤️ قلبت امروز آرامش واقعی را تجربه می‌کند",
            "📚 امروز روز یادگیری و کشف استعدادهای نهفته توست",
            "🎯 هر کاری را امروز شروع کنی، به سرانجام می‌رسد",
            "🌟 ستاره‌های بخت امشب در آسمان زندگی تو می‌درخشند",
            "🤝 یک آشنایی جدید مسیر زندگیت را عوض می‌کند",
            "💪 انرژی مثبت امروز در بالاترین سطح خود است",
            "🎨 استعداد هنری تو امروز شکوفا می‌شود",
            "🏆 به یک موفقیت بزرگ نزدیک شده‌ای، صبور باش",
            "⚡ امروز روز پرانرژی و پویایی برای توست",
            "💡 یک ایده ناب به ذهنت می‌رسد، آن را حفظ کن",
            "🎁 یک سورپرایز خوب در انتظار توست",
            "🌙 رویای دیشب تعبیر خوبی دارد",
            "✨ نور امید امروز تمام زندگیت را روشن می‌کند",
            "🔥 قدرت غلبه بر مشکلات را داری، پیروزی از آن توست",
            "💎 ارزش واقعی تو امروز بیشتر از همیشه نمایان می‌شود",
            "🚀 به آرزوی دیرینه‌ات نزدیک شده‌ای",
            "🎵 موسیقی امروز حال دلت را خوب می‌کند",
            "🍀 شانس با توست، فقط کافیست باور کنی",
            "🌊 آرامش امروز کلید موفقیت توست",
            "📞 یک تماس تلفنی خبر خوبی برایت دارد",
            "🎭 امروز روز نمایش استعدادهای واقعی توست",
            "💖 عشق و محبت در انتظار توست",
            "⭐ یک آرزوی قدیمی امروز برآورده می‌شود",
            "🎉 امروز روز جشن و شادی برای توست",
            "🤲 دعایت امروز به اجابت می‌رسد",
            "🎓 یک خبر خوب در مورد کار یا تحصیل می‌رسی",
            "💫 بخت با توست، محکم قدم بردار",
            "🌺 روزت پر از گل و لبخند خواهد بود",
            "🕊️ امروز روز آرامش و آرامش روحی توست",
            "👨‍👩‍👧‍👦 امروز وقت گذراندن با خانواده برکت دارد",
            "💝 یک محبت بی‌چشم‌داشت نصیبت می‌شود",
            "🌅 فردایت روشن‌تر از امروز است",
            "🍀 امروز روز شروع یک عادت خوب است",
            "💪 قدرت درون تو از چیزی که فکر می‌کنی بیشتر است",
            "🌈 رنگین‌کمان بعد از باران، صبور باش",
            "🎁 زندگی امروز به تو هدیه می‌دهد",
            "🌟 نوری که داری، دنیا را روشن می‌کند",
            "💎 ارزش تو از طلا بیشتر است",
            "🚪 یک در جدید به روی تو باز می‌شود",
            "📈 روزت رو به رشد است، ادامه بده",
            "🎨 خلاقیت امروزت راهگشای تو خواهد بود",
            "🌙 ماه امشب برای تو دعا می‌کند",
            "⭐ آرزویت در آسمان ثبت شده است",
            "💫 امروز روز معجزه‌های کوچک است",
            "🔥 آتش درونت را روشن نگه دار",
            "💧 آرامش مثل آب بر زندگی تو جاری می‌شود",
            "🌬️ باد تغییرات به سود تو خواهد وزید"
        ]
        
        # ========== فریم اصلی ==========
        self.main_frame = tk.Frame(root, bg='#0a0a0a')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # عنوان با افکت
        self.title_label = tk.Label(
            self.main_frame,
            text="🔮 فال روز 🔮",
            font=('Vazir', 24, 'bold'),
            bg='#0a0a0a',
            fg='#ff6b6b'
        )
        self.title_label.pack(pady=20)
        
        # زیرنویس
        subtitle = tk.Label(
            self.main_frame,
            text="هر روز یک فال جدید و جذاب",
            font=('Vazir', 10),
            bg='#0a0a0a',
            fg='#a8e6cf'
        )
        subtitle.pack(pady=5)
        
        # ========== کادر تزئینی ==========
        decoration_frame = tk.Frame(self.main_frame, bg='#1a1a2e', relief=tk.RAISED, bd=2)
        decoration_frame.pack(pady=20, fill=tk.X)
        
        decoration_text = """
        ✨🌸✨🌸✨🌸✨🌸✨🌸✨
        🌟  امروز روز خوبی است  🌟
        ✨🌸✨🌸✨🌸✨🌸✨🌸✨
        """
        
        dec_label = tk.Label(
            decoration_frame,
            text=decoration_text,
            font=('Courier', 10, 'bold'),
            bg='#1a1a2e',
            fg='#ffd93d',
            justify='center'
        )
        dec_label.pack(pady=10)
        
        # ========== دکمه گرفتن فال ==========
        self.get_fortune_btn = tk.Button(
            self.main_frame,
            text="🔮  گرفتن فال امروز  🔮",
            command=self.get_fortune,
            font=('Vazir', 14, 'bold'),
            bg='#6c5ce7',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=40,
            pady=12,
            activebackground='#5a4ab3',
            activeforeground='white'
        )
        self.get_fortune_btn.pack(pady=25)
        
        # ========== بخش نمایش نتیجه ==========
        self.result_frame = tk.Frame(self.main_frame, bg='#0a0a0a')
        self.result_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # لیبل نتیجه با استایل زیبا
        self.result_label = tk.Label(
            self.result_frame,
            text="✨ برای گرفتن فال، دکمه را بزن ✨",
            font=('Vazir', 12),
            bg='#0a0a0a',
            fg='#a8e6cf',
            wraplength=520,
            justify='center',
            relief=tk.SUNKEN,
            bd=2,
            padx=20,
            pady=30
        )
        self.result_label.pack(fill=tk.BOTH, expand=True)
        
        # نمایش تاریخ امروز
        today_str = self.get_persian_date()
        date_label = tk.Label(
            self.main_frame,
            text=f"📅 {today_str}",
            font=('Vazir', 9),
            bg='#0a0a0a',
            fg='#a8e6cf'
        )
        date_label.pack(pady=5)
        
        # دکمه خروج
        exit_btn = tk.Button(
            self.main_frame,
            text="✖  خروج",
            command=self.exit_app,
            font=('Vazir', 9),
            bg='#2d2d44',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=15,
            pady=5,
            activebackground='#d63031'
        )
        exit_btn.pack(pady=10)
        
        # افکت محو شدن تدریجی
        self.fade_in()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.root.update_idletasks()
        width = 600
        height = 550
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def fade_in(self):
        """افکت محو شدن تدریجی"""
        alpha = 0
        self.root.attributes('-alpha', alpha)
        
        def increase_alpha():
            nonlocal alpha
            if alpha < 1:
                alpha += 0.05
                self.root.attributes('-alpha', alpha)
                self.root.after(30, increase_alpha)
        
        increase_alpha()
    
    def get_fortune(self):
        """گرفتن فال تصادفی"""
        # غیرفعال کردن دکمه در حین پردازش
        self.get_fortune_btn.config(state=tk.DISABLED, text="⏳  در حال گرفتن فال...")
        
        # افکت جذاب: تغییر رنگ متن
        self.result_label.config(text="🔮  فال در حال آماده‌سازی...  🔮", fg='#ffd93d')
        
        def process():
            import time
            time.sleep(0.3)  # تاخیر کوتاه برای افکت
            
            # انتخاب فال تصادفی
            fortune = random.choice(self.all_fortunes)
            
            # ساخت فال نهایی با قاب زیبا
            final_fortune = f"""
╔══════════════════════════════════════╗
║                                      ║
║         🔮  فال امروز تو  🔮         ║
║                                      ║
║                                      ║
║     {fortune}     ║
║                                      ║
║                                      ║
║      ✨  به امید روزهای خوب  ✨       ║
║                                      ║
╚══════════════════════════════════════╝
            """
            
            # بروزرسانی در thread اصلی
            self.root.after(0, lambda: self.update_result(final_fortune))
        
        thread = threading.Thread(target=process)
        thread.start()
    
    def update_result(self, fortune_text):
        """بروزرسانی نتیجه"""
        self.result_label.config(text=fortune_text, fg='#ffd93d', font=('Courier', 10))
        self.get_fortune_btn.config(state=tk.NORMAL, text="🔮  گرفتن فال امروز  🔮")
        
        # افکت چشمک زن
        self.blink_effect()
    
    def blink_effect(self):
        """افکت چشمک زن برای نتیجه"""
        colors = ['#ffd93d', '#6c5ce7', '#00cec9', '#ff6b6b']
        def change_color(index=0):
            if index < len(colors) * 2:
                color = colors[index % len(colors)]
                self.result_label.config(fg=color)
                self.root.after(120, lambda: change_color(index + 1))
            else:
                self.result_label.config(fg='#ffd93d')
        change_color()
    
    def get_persian_date(self):
        """گرفتن تاریخ به فارسی"""
        weekdays = ['شنبه', 'یک‌شنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
        months = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور', 
                 'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
        
        now = datetime.now()
        weekday = weekdays[now.weekday()]
        
        # اینجا برای سادگی از تاریخ میلادی استفاده می‌کنیم
        # برای تاریخ شمسی دقیق نیاز به کتابخانه jdatetime هست
        
        return f"{weekday} - {now.year}/{now.month:02d}/{now.day:02d}"
    
    def exit_app(self):
        """خروج"""
        result = messagebox.askyesno("خروج", "آیا مطمئنی می‌خوای خارج بشی؟")
        if result:
            self.root.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = FortuneTeller(root)
    root.mainloop()