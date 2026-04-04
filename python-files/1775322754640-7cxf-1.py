import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
from datetime import datetime
import threading

class AfghanistanWeather:
    def __init__(self, root):
        self.root = root
        self.root.title("آب و هوای افغانستان")
        self.root.geometry("700x650")
        self.root.configure(bg='#0a1628')
        self.root.resizable(False, False)
        
        # مرکز کردن پنجره
        self.center_window()
        
        # شهرهای اصلی افغانستان با مختصات دقیق
        self.cities = {
            "کابل (Kabul)": {"lat": 34.5553, "lon": 69.2075},
            "هرات (Herat)": {"lat": 34.3525, "lon": 62.2042},
            "مزار شریف (Mazar-i-Sharif)": {"lat": 36.7091, "lon": 67.1109},
            "قندهار (Kandahar)": {"lat": 31.6289, "lon": 65.7372},
            "جلال‌آباد (Jalalabad)": {"lat": 34.4345, "lon": 70.4428},
            "کندز (Kunduz)": {"lat": 36.7286, "lon": 68.8678},
            "بامیان (Bamyan)": {"lat": 34.8200, "lon": 67.8200},
            "غزنی (Ghazni)": {"lat": 33.5459, "lon": 68.4174},
            "پلخمری (Pul-i-Khumri)": {"lat": 35.9500, "lon": 68.7000},
            "خوست (Khost)": {"lat": 33.3383, "lon": 69.9203}
        }
        
        # ========== فریم اصلی ==========
        self.main_frame = tk.Frame(root, bg='#0a1628')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # عنوان
        title_label = tk.Label(
            self.main_frame,
            text="🌤️ آب و هوای افغانستان 🌤️",
            font=('Vazir', 18, 'bold'),
            bg='#0a1628',
            fg='#4ecdc4'
        )
        title_label.pack(pady=10)
        
        # زیرنویس
        subtitle = tk.Label(
            self.main_frame,
            text="داده‌های دقیق هواشناسی از سراسر کشور",
            font=('Vazir', 9),
            bg='#0a1628',
            fg='#a8e6cf'
        )
        subtitle.pack(pady=5)
        
        # ========== بخش انتخاب شهر ==========
        city_frame = tk.LabelFrame(
            self.main_frame,
            text="📍 انتخاب شهر",
            font=('Vazir', 11, 'bold'),
            bg='#1a2744',
            fg='#4ecdc4',
            relief=tk.RIDGE,
            bd=2
        )
        city_frame.pack(pady=15, fill=tk.X)
        
        self.city_var = tk.StringVar()
        self.city_combo = ttk.Combobox(
            city_frame,
            textvariable=self.city_var,
            values=list(self.cities.keys()),
            font=('Vazir', 11),
            state='readonly',
            width=40
        )
        self.city_combo.pack(pady=15, padx=20)
        self.city_combo.set("کابل (Kabul)")
        
        # ========== دکمه دریافت اطلاعات ==========
        self.get_weather_btn = tk.Button(
            self.main_frame,
            text="🔍 دریافت اطلاعات آب و هوا 🔍",
            command=self.get_weather,
            font=('Vazir', 12, 'bold'),
            bg='#4ecdc4',
            fg='#0a1628',
            cursor='hand2',
            bd=0,
            padx=30,
            pady=10,
            activebackground='#3dbdb5',
            activeforeground='#0a1628'
        )
        self.get_weather_btn.pack(pady=15)
        
        # ========== بخش نمایش اطلاعات ==========
        self.result_frame = tk.Frame(self.main_frame, bg='#0a1628', relief=tk.SUNKEN, bd=2)
        self.result_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        # لیبل وضعیت
        self.status_label = tk.Label(
            self.result_frame,
            text="🌟 یک شهر را انتخاب کنید و دکمه را بزنید 🌟",
            font=('Vazir', 10),
            bg='#0a1628',
            fg='#a8e6cf',
            pady=20
        )
        self.status_label.pack()
        
        # فریم برای نمایش اطلاعات (در ابتدا خالی)
        self.info_frame = None
        
        # ========== فوتر ==========
        footer = tk.Label(
            self.main_frame,
            text="📡 منبع داده: Open-Meteo | رایگان و بدون نیاز به ثبت‌نام",
            font=('Vazir', 8),
            bg='#0a1628',
            fg='#4a5a7a'
        )
        footer.pack(pady=10)
        
        # دکمه خروج
        exit_btn = tk.Button(
            self.main_frame,
            text="🚪 خروج",
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
        exit_btn.pack()
        
        # افکت محو شدن
        self.fade_in()
    
    def center_window(self):
        """مرکز کردن پنجره"""
        self.root.update_idletasks()
        width = 700
        height = 650
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
    
    def get_weather(self):
        """دریافت اطلاعات آب و هوا از API رایگان"""
        selected_city = self.city_var.get()
        city_data = self.cities[selected_city]
        lat = city_data["lat"]
        lon = city_data["lon"]
        
        # غیرفعال کردن دکمه در حین دریافت
        self.get_weather_btn.config(state=tk.DISABLED, text="⏳ در حال دریافت اطلاعات...")
        self.status_label.config(text="🌐 در حال اتصال به سرور هواشناسی...", fg='#ffd93d')
        
        def fetch_weather():
            try:
                # API رایگان Open-Meteo - بدون نیاز به کلید [citation:1]
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation&timezone=auto"
                
                response = requests.get(url, timeout=10)
                data = response.json()
                
                if "current_weather" in data:
                    weather_data = self.process_weather_data(data, selected_city)
                    self.root.after(0, lambda: self.display_weather(weather_data))
                else:
                    self.root.after(0, lambda: self.show_error("خطا در دریافت اطلاعات"))
                    
            except requests.exceptions.RequestException as e:
                self.root.after(0, lambda: self.show_error(f"خطای اتصال به اینترنت!\nلطفاً اتصال خود را بررسی کنید."))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"خطا: {str(e)}"))
        
        thread = threading.Thread(target=fetch_weather)
        thread.start()
    
    def process_weather_data(self, data, city_name):
        """پردازش داده‌های دریافتی از API"""
        current = data.get("current_weather", {})
        hourly = data.get("hourly", {})
        
        # اطلاعات فعلی
        temperature = current.get("temperature", "N/A")
        wind_speed = current.get("windspeed", "N/A")
        wind_direction = self.get_wind_direction(current.get("winddirection", 0))
        
        # اطلاعات ساعتی (برای پیش‌بینی)
        precipitation = 0
        humidity = "N/A"
        
        if hourly and "precipitation" in hourly and len(hourly["precipitation"]) > 12:
            precipitation = sum(hourly["precipitation"][:12]) / 12
        
        if hourly and "relative_humidity_2m" in hourly and len(hourly["relative_humidity_2m"]) > 0:
            humidity = hourly["relative_humidity_2m"][0]
        
        return {
            "city": city_name,
            "temperature": temperature,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "humidity": humidity,
            "precipitation": precipitation,
            "time": current.get("time", datetime.now().strftime("%Y-%m-%d %H:%M"))
        }
    
    def get_wind_direction(self, degrees):
        """تبدیل درجه باد به جهت"""
        if degrees is None:
            return "نامشخص"
        directions = [
            ("شمال", 0, 22.5), ("شمال شرقی", 22.5, 67.5),
            ("شرق", 67.5, 112.5), ("جنوب شرقی", 112.5, 157.5),
            ("جنوب", 157.5, 202.5), ("جنوب غربی", 202.5, 247.5),
            ("غرب", 247.5, 292.5), ("شمال غربی", 292.5, 337.5)
        ]
        for name, start, end in directions:
            if start <= degrees < end:
                return name
        return "شمال"
    
    def display_weather(self, weather):
        """نمایش اطلاعات آب و هوا با دیزاین زیبا"""
        # پاک کردن فریم قبلی
        if self.info_frame:
            self.info_frame.destroy()
        
        self.info_frame = tk.Frame(self.result_frame, bg='#0a1628')
        self.info_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # نام شهر
        city_label = tk.Label(
            self.info_frame,
            text=f"🏙️ {weather['city']}",
            font=('Vazir', 16, 'bold'),
            bg='#0a1628',
            fg='#4ecdc4'
        )
        city_label.pack(pady=10)
        
        # زمان بروزرسانی
        time_label = tk.Label(
            self.info_frame,
            text=f"📅 {weather['time']}",
            font=('Vazir', 9),
            bg='#0a1628',
            fg='#a8e6cf'
        )
        time_label.pack()
        
        # خط جداکننده
        separator = tk.Frame(self.info_frame, height=2, bg='#4ecdc4')
        separator.pack(fill=tk.X, pady=15)
        
        # ========== نمایش اطلاعات اصلی ==========
        info_grid = tk.Frame(self.info_frame, bg='#0a1628')
        info_grid.pack(pady=10)
        
        # دما
        temp_color = '#ff6b6b' if weather['temperature'] > 30 else '#4ecdc4' if weather['temperature'] > 15 else '#74b9ff'
        temp_text = f"🌡️ دما: {weather['temperature']}°C"
        temp_label = tk.Label(
            info_grid, text=temp_text,
            font=('Vazir', 14, 'bold'),
            bg='#0a1628', fg=temp_color
        )
        temp_label.pack(pady=8)
        
        # رطوبت
        humidity_text = f"💧 رطوبت: {weather['humidity']}%" if weather['humidity'] != "N/A" else "💧 رطوبت: در دسترس نیست"
        humidity_label = tk.Label(
            info_grid, text=humidity_text,
            font=('Vazir', 12),
            bg='#0a1628', fg='#a8e6cf'
        )
        humidity_label.pack(pady=5)
        
        # باد
        wind_text = f"💨 باد: {weather['wind_speed']} km/h • جهت {weather['wind_direction']}"
        wind_label = tk.Label(
            info_grid, text=wind_text,
            font=('Vazir', 12),
            bg='#0a1628', fg='#a8e6cf'
        )
        wind_label.pack(pady=5)
        
        # بارش
        precipitation_text = f"☔ بارش پیش‌بینی: {weather['precipitation']:.1f} mm" if isinstance(weather['precipitation'], (int, float)) else "☔ بارش: در دسترس نیست"
        precipitation_label = tk.Label(
            info_grid, text=precipitation_text,
            font=('Vazir', 12),
            bg='#0a1628', fg='#a8e6cf'
        )
        precipitation_label.pack(pady=5)
        
        # ========== پیشنهاد بر اساس آب و هوا ==========
        suggestion_frame = tk.Frame(self.info_frame, bg='#1a2744', relief=tk.RAISED, bd=1)
        suggestion_frame.pack(fill=tk.X, pady=15)
        
        suggestion = self.get_suggestion(weather['temperature'], weather['precipitation'])
        suggestion_label = tk.Label(
            suggestion_frame,
            text=f"💡 {suggestion}",
            font=('Vazir', 10),
            bg='#1a2744',
            fg='#ffd93d',
            wraplength=500,
            pady=10
        )
        suggestion_label.pack()
        
        # بروزرسانی وضعیت
        self.status_label.config(text="✅ اطلاعات با موفقیت دریافت شد!", fg='#4ecdc4')
        self.get_weather_btn.config(state=tk.NORMAL, text="🔍 دریافت اطلاعات آب و هوا 🔍")
        
        # افکت چشمک زن
        self.blink_effect()
    
    def get_suggestion(self, temp, precip):
        """گرفتن پیشنهاد بر اساس شرایط آب و هوا"""
        if temp > 35:
            return "دمای هوا بسیار بالاست! حتماً مایعات کافی بنوشید و از حضور در آفتاب مستقیم خودداری کنید."
        elif temp > 30:
            return "هوا گرم است. لباس خنک بپوشید و کرم ضدآفتاب استفاده کنید."
        elif temp < 0:
            return "هوا سرد است! حتماً لباس گرم بپوشید و مراقب یخبندان باشید."
        elif temp < 10:
            return "هوا خنک است. یک ژاکت همراه داشته باشید."
        elif precip > 5:
            return "احتمال بارندگی وجود دارد! چتر همراه داشته باشید."
        elif precip > 0:
            return "احتمال باران کم است، اما بهتر است یک چتر همراه داشته باشید."
        else:
            return "آب و هوا مساعد است. روز خوبی داشته باشید! 🌟"
    
    def blink_effect(self):
        """افکت چشمک زن"""
        colors = ['#4ecdc4', '#ffd93d', '#74b9ff', '#ff6b6b']
        def change_color(index=0):
            if index < len(colors) * 2:
                color = colors[index % len(colors)]
                self.status_label.config(fg=color)
                self.root.after(150, lambda: change_color(index + 1))
            else:
                self.status_label.config(fg='#4ecdc4')
        change_color()
    
    def show_error(self, error_msg):
        """نمایش خطا"""
        self.status_label.config(text=f"❌ {error_msg}", fg='#ff6b6b')
        self.get_weather_btn.config(state=tk.NORMAL, text="🔍 دریافت اطلاعات آب و هوا 🔍")
        messagebox.showerror("خطا", error_msg)
    
    def exit_app(self):
        """خروج"""
        result = messagebox.askyesno("خروج", "آیا مطمئنی می‌خوای خارج بشی؟")
        if result:
            self.root.quit()

# نصب کتابخانه مورد نیاز
# قبل از اجرا: pip install requests

if __name__ == "__main__":
    root = tk.Tk()
    app = AfghanistanWeather(root)
    root.mainloop()