import tkinter as tk
from tkinter import ttk, messagebox
import random
from datetime import datetime
import threading

class FortuneTeller:
    def __init__(self, root):
        self.root = root
        self.root.title("فال روز | تقدیم به سیدعبدالمصور")
        self.root.geometry("650x600")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(False, False)
        
        # مرکز کردن پنجره
        self.center_window()
        
        # دیکشنری فال‌ها بر اساس روز هفته (بیش از 30 فال)
        self.fortunes = {
            'Saturday': [  # شنبه
                "🌈 امروز روز شروع کارهای جدید است، شجاع باش!",
                "💰 یک خبر خوب مالی به زودی بهت می‌رسه!",
                "❤️ دل تو امروز آرامش می‌گیره، منتظر یه اتفاق خوب باش.",
                "📚 امروز روز یادگیری و پیشرفته، از فرصت‌ها استفاده کن.",
                "🎯 هر کاری رو امروز شروع کنی، به سرانجام می‌رسه!"
            ],
            'Sunday': [   # یک‌شنبه
                "🌟 ستاره‌های بخت امروز به نفع تو هستن!",
                "🤝 یه آشنایی جدید زندگیت رو عوض می‌کنه.",
                "💪 انرژی مثبت امروز بالاست، ازش استفاده کن!",
                "🎨 استعداد نهفته‌ات امروز شکوفا می‌شه.",
                "🏆 به یه موفقیت بزرگ نزدیک شدی، صبور باش!"
            ],
            'Monday': [    # دوشنبه
                "⚡ امروز روز پر انرژی و پویایی برات هست!",
                "💡 یه ایده ناب به ذهنت می‌رسه، یادداشتش کن!",
                "🎁 یه سورپرایز خوب در انتظارته!",
                "🌙 رویایی که دیشب دیدی، تعبیر خوبی داره!",
                "✨ نور امید امروز راهتو روشن می‌کنه!"
            ],
            'Tuesday': [   # سه‌شنبه
                "🔥 امروز روز غلبه بر مشکلاته، پیروزی از آن توست!",
                "💎 ارزش واقعیت امروز بیشتر از همیشه نمایان می‌شه!",
                "🚀 به آرزوی قدیمیت نزدیک شدی، رها نکن!",
                "🎵 موسیقی امروز حال دلت رو خوب می‌کنه!",
                "🍀 شانس با توئه، فقط باور کن!"
            ],
            'Wednesday': [ # چهارشنبه
                "🌊 آرامش امروز کلید موفقیت توئه!",
                "📞 یه تماس تلفنی خبر خوب داره!",
                "🎭 امروز روز نمایش استعدادهای توئه!",
                "💖 عشق و محبت امروز در انتظارته!",
                "⭐ یک آرزوی قدیمی امروز برآورده می‌شه!"
            ],
            'Thursday': [  # پنج‌شنبه
                "🎉 امروز روز جشن و شادی برات هست!",
                "🤲 دعای تو امروز به اجابت می‌رسه!",
                "🎓 یه خبر خوب تحصیلی یا کاری می‌رسی!",
                "💫 بخت با توئه، محکم قدم بردار!",
                "🌺 روزت پر از گل و لبخنده!"
            ],
            'Friday': [     # جمعه
                "🕊️ امروز روز آرامش و معنویته!",
                "👨‍👩‍👧‍👦 وقت گذروندن با خانواده برکت داره!",
                "🌟 نیکی امروزت فردات رو می‌سازه!",
                "💝 یه محبت بی‌چشم داشت نصیبت می‌شه!",
                "🌅 فردات روشن‌تر از امروزه، نگران نباش!"
            ]
        }
        
        # فال‌های اضافی برای تنوع (بیش از 30 تا)
        extra_fortunes = [
            "🍀 امروز روز خوبی برای شروع یه عادت خوبه!",
            "🎯 هدفی که داری، به زودی محقق می‌شه!",
            "💪 قدرت درون تو از چیزی که فکر می‌کنی بیشتره!",
            "🌈 رنگین‌کمان بعد از بارون، صبر داشته باش!",
            "🎁 زندگی امروز بهت هدیه می‌ده، پذیرا باش!",
            "🌟 نوری که داری، دنیا رو روشن می‌کنه!",
            "💎 ارزش تو از طلا بیشتره، فراموش نکن!",
            "🚪 یه در جدید به زودی به رويت باز می‌شه!",
            "📈 روزت رو به رشده، ادامه بده!",
            "🎨 خلاقیت امروزت راهگشاست!"
        ]
        
        # اضافه کردن فال‌های اضافی به هر روز
        for day in self.fortunes:
            self.fortunes[day].extend(random.sample(extra_fortunes, 2))
        
        # ========== فریم اصلی با ظاهر شدن تدریجی ==========
        self.main_frame = tk.Frame(root, bg='#0a0a0a')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # عنوان با افکت
        self.title_label = tk.Label(
            self.main_frame,
            text="🔮 فال روز حرفه‌ای 🔮",
            font=('Vazir', 20, 'bold'),
            bg='#0a0a0a',
            fg='#ff6b6b'
        )
        self.title_label.pack(pady=10)
        
        # ========== تقدیم به سیدعبدالمصور (برجسته و جذاب) ==========
        dedication_frame = tk.Frame(self.main_frame, bg='#1a1a2e', relief=tk.RAISED, bd=3)
        dedication_frame.pack(pady=15, fill=tk.X)
        
        dedication_text = """
╔══════════════════════════════════════╗
║                                      ║
║     ✨ تقدیم به استاد گرانقدر ✨     ║
║                                      ║
║        سیدعبدالمصور عزیز             ║
║                                      ║
║     که با نقدهای سازنده اش           ║
║     دل ما را روشن می‌کند             ║
║                                      ║
╚══════════════════════════════════════╝
        """
        
        dedication_label = tk.Label(
            dedication_frame,
            text=dedication_text,
            font=('Courier', 10, 'bold'),
            bg='#1a1a2e',
            fg='#ffd93d',
            justify='center'
        )
        dedication_label.pack(pady=10)
        
        # ========== بخش ورودی اطلاعات ==========
        input_frame = tk.LabelFrame(
            self.main_frame,
            text="📝 اطلاعات خود را وارد کنید",
            font=('Vazir', 12, 'bold'),
            bg='#1e1e2e',
            fg='#00cec9',
            relief=tk.RIDGE,
            bd=2
        )
        input_frame.pack(pady=15, fill=tk.X)
        
        # ورودی نام
        name_frame = tk.Frame(input_frame, bg='#1e1e2e')
        name_frame.pack(pady=10)
        
        tk.Label(name_frame, text="نام:", font=('Vazir', 11), bg='#1e1e2e', fg='white').pack(side=tk.LEFT, padx=10)
        self.name_entry = tk.Entry(name_frame, font=('Vazir', 11), width=25, justify='center')
        self.name_entry.pack(side=tk.LEFT, padx=10)
        
        # ورودی سن
        age_frame = tk.Frame(input_frame, bg='#1e1e2e')
        age_frame.pack(pady=10)
        
        tk.Label(age_frame, text="سن:", font=('Vazir', 11), bg='#1e1e2e', fg='white').pack(side=tk.LEFT, padx=10)
        self.age_entry = tk.Entry(age_frame, font=('Vazir', 11), width=25, justify='center')
        self.age_entry.pack(side=tk.LEFT, padx=10)
        
        # ========== دکمه گرفتن فال ==========
        self.get_fortune_btn = tk.Button(
            self.main_frame,
            text="🔮 گرفتن فال روز 🔮",
            command=self.get_fortune,
            font=('Vazir', 13, 'bold'),
            bg='#6c5ce7',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=30,
            pady=10,
            activebackground='#5a4ab3',
            activeforeground='white'
        )
        self.get_fortune_btn.pack(pady=15)
        
        # ========== بخش نمایش نتیجه ==========
        self.result_frame = tk.Frame(self.main_frame, bg='#0a0a0a')
        self.result_frame.pack(pady=20, fill=tk.BOTH, expand=True)
        
        # لیبل نتیجه با استایل زیبا
        self.result_label = tk.Label(
            self.result_frame,
            text="✨ منتظر فال تو هستم... ✨",
            font=('Vazir', 12),
            bg='#0a0a0a',
            fg='#a8e6cf',
            wraplength=550,
            justify='center',
            relief=tk.SUNKEN,
            bd=2
        )
        self.result_label.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # دکمه خروج
        exit_btn = tk.Button(
            self.main_frame,
            text="🚪 خروج",
            command=self.exit_app,
            font=('Vazir', 10, 'bold'),
            bg='#d63031',
            fg='white',
            cursor='hand2',
            bd=0,
            padx=20,
            pady=5
        )
        exit_btn.pack(pady=10)
        
        # افکت محو شدن تدریجی (حل مشکل صفحه سیاه)
        self.fade_in()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.root.update_idletasks()
        width = 650
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def fade_in(self):
        """افکت محو شدن تدریجی برای جلوگیری از صفحه سیاه"""
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
        """گرفتن فال بر اساس نام و سن"""
        # غیرفعال کردن دکمه در حین پردازش
        self.get_fortune_btn.config(state=tk.DISABLED, text="⏳ در حال گرفتن فال...")
        
        # استفاده از threading برای جلوگیری از lag
        def process():
            import time
            time.sleep(0.5)  # تاخیر کوتاه برای افکت حرفه‌ای
            
            name = self.name_entry.get().strip()
            age = self.age_entry.get().strip()
            
            # بررسی ورودی‌ها
            if not name:
                name = "عزیز"
            
            if not age or not age.isdigit():
                age_value = 25
                age_text = "۲۵"
            else:
                age_value = int(age)
                age_text = age
            
            # دریافت روز هفته
            weekday_num = datetime.now().weekday()
            weekdays = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            today = weekdays[weekday_num]
            
            # انتخاب فال تصادفی از فال‌های امروز
            fortune_list = self.fortunes[today]
            fortune = random.choice(fortune_list)
            
            # شخصی‌سازی فال بر اساس سن و نام
            if age_value < 18:
                personal_message = f"{name} جان {age_text} ساله عزیز"
            elif age_value < 30:
                personal_message = f"{name} گرامی {age_text} ساله"
            elif age_value < 50:
                personal_message = f"{name} بزرگوار {age_text} ساله"
            else:
                personal_message = f"{name} عزیز {age_text} ساله"
            
            # ساخت فال نهایی
            final_fortune = f"""
╔══════════════════════════════════════════════╗
║                                              ║
║  {personal_message}                   
║                                              ║
║  📅 فال روز {self.get_persian_weekday()}  
║                                              ║
║  {fortune}                                   
║                                              ║
║  ✨ با آرزوی بهترین‌ها برای تو ✨            
║                                              ║
║  {self.get_fortune_footer()}                 
║                                              ║
╚══════════════════════════════════════════════╝
            """
            
            # بروزرسانی در thread اصلی
            self.root.after(0, lambda: self.update_result(final_fortune))
        
        thread = threading.Thread(target=process)
        thread.start()
    
    def update_result(self, fortune_text):
        """بروزرسانی نتیجه در ترد اصلی"""
        self.result_label.config(text=fortune_text, fg='#ffd93d', font=('Courier', 10))
        self.get_fortune_btn.config(state=tk.NORMAL, text="🔮 گرفتن فال روز 🔮")
        
        # افکت چشمک زن برای جذابیت
        self.blink_effect()
    
    def blink_effect(self):
        """افکت چشمک زن برای نتیجه"""
        colors = ['#ffd93d', '#6c5ce7', '#00cec9', '#ff6b6b']
        def change_color(index=0):
            if index < len(colors) * 2:
                color = colors[index % len(colors)]
                self.result_label.config(fg=color)
                self.root.after(150, lambda: change_color(index + 1))
            else:
                self.result_label.config(fg='#ffd93d')
        change_color()
    
    def get_persian_weekday(self):
        """گرفتن نام روز هفته به فارسی"""
        weekdays_persian = {
            'Saturday': 'شنبه',
            'Sunday': 'یک‌شنبه',
            'Monday': 'دوشنبه',
            'Tuesday': 'سه‌شنبه',
            'Wednesday': 'چهارشنبه',
            'Thursday': 'پنج‌شنبه',
            'Friday': 'جمعه'
        }
        weekday_num = datetime.now().weekday()
        weekdays = ['Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        return weekdays_persian[weekdays[weekday_num]]
    
    def get_fortune_footer(self):
        """فوتر مخصوص فال"""
        footers = [
            "تقدیم از طرف سیدعبدالمصور",
            "با عشق از سیدعبدالمصور",
            "سیدعبدالمصور همیشه حامیته",
            "نظرتو برام بنویس، سیدعبدالمصور"
        ]
        return random.choice(footers)
    
    def exit_app(self):
        """خروج با احترام"""
        result = messagebox.askyesno("خروج", "آیا مطمئنی می‌خوای خارج بشی؟\nسیدعبدالمصور منتظر برگشتته!")
        if result:
            self.root.quit()

# نصب کتابخانه خاصی نیاز نیست، فقط tkinter که با پایتون هست

if __name__ == "__main__":
    root = tk.Tk()
    app = FortuneTeller(root)
    root.mainloop()