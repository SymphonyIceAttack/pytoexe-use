# ماشین حساب گرافیکی با تم صورتی
# هانیه طحانیان

import tkinter as tk

class CalculatorApp:
    def __init__(self):
        # ایجاد پنجره اصلی
        self.window = tk.Tk()
        self.window.title("هانیه طحانیان")
        self.window.geometry("350x500")
        self.window.resizable(False, False)
        self.window.configure(bg="#FFB7C5")  # صورتی ملایم
        
        # متغیر نگهداری عبارت محاسباتی
        self.expression = ""
        
        # ایجاد نمایشگر (Entry)
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        
        self.display = tk.Entry(
            self.window,
            textvariable=self.display_var,
            font=("Segoe UI", 28, "bold"),
            bg="#FFF0F5",  # صورتی خیلی روشن (Lavender Blush)
            fg="#C2185B",  # صورتی پررنگ و شیک
            borderwidth=0,
            justify="right",
            state="readonly",
            relief="flat",
            highlightthickness=0
        )
        self.display.pack(fill="both", padx=15, pady=(30, 15), ipady=18)
        
        # فریم دکمه‌ها
        self.button_frame = tk.Frame(self.window, bg="#FFB7C5")
        self.button_frame.pack(fill="both", expand=True, padx=12, pady=(0, 15))
        
        # تعریف چیدمان دکمه‌ها
        buttons = [
            ["C", "⌫", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["00", "0", ".", "="]
        ]
        
        # رنگ‌های تم صورتی
        pink_dark = "#E91E63"      # صورتی سیر برای دکمه‌های عملیات
        pink_light = "#F48FB1"      # صورتی روشن برای اعداد
        pink_erase = "#FF4081"      # صورتی پررنگ برای دکمه پاک کردن
        pink_equal = "#FF8A80"      # صورتی-قرمز ملایم برای تساوی
        
        # ایجاد دکمه‌ها
        for row_idx, row in enumerate(buttons):
            self.button_frame.grid_rowconfigure(row_idx, weight=1)
            for col_idx, btn_text in enumerate(row):
                self.button_frame.grid_columnconfigure(col_idx, weight=1)
                
                # تعیین رنگ و استایل دکمه بر اساس نوع
                if btn_text in ["C", "⌫"]:
                    btn_color = pink_erase
                    btn_fg = "white"
                    font_size = 16
                elif btn_text in ["+", "-", "*", "/", "%", "="]:
                    if btn_text == "=":
                        btn_color = pink_equal
                        btn_fg = "white"
                    else:
                        btn_color = pink_dark
                        btn_fg = "white"
                    font_size = 18
                else:
                    btn_color = pink_light
                    btn_fg = "#880E4F"  # شرابی تیره برای متن اعداد
                    font_size = 18
                
                btn = tk.Button(
                    self.button_frame,
                    text=btn_text,
                    font=("Segoe UI", font_size, "bold"),
                    bg=btn_color,
                    fg=btn_fg,
                    activebackground="#FFB6C1",
                    activeforeground="white",
                    borderwidth=0,
                    relief="flat",
                    cursor="hand2",
                    command=lambda text=btn_text: self.on_button_click(text)
                )
                btn.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="nsew")
                
                # اضافه کردن گوشه‌های گرد به دکمه‌ها (با افکت)
                btn.config(highlightthickness=0)
    
    def on_button_click(self, button_text):
        """مدیریت کلیک روی دکمه‌ها"""
        
        if button_text == "C":
            self.expression = ""
            self.update_display("0")
        
        elif button_text == "⌫":
            self.expression = self.expression[:-1]
            if self.expression == "":
                self.update_display("0")
            else:
                self.update_display(self.expression)
        
        elif button_text == "=":
            try:
                if not self.expression:
                    return
                
                expr = self.expression.replace("÷", "/").replace("×", "*")
                result = eval(expr)
                
                # فرمت کردن نتیجه برای نمایش بهتر
                if isinstance(result, float) and result.is_integer():
                    result = int(result)
                elif isinstance(result, float):
                    result = round(result, 10)
                
                self.expression = str(result)
                self.update_display(self.expression)
                
            except ZeroDivisionError:
                self.update_display("نمیشه تقسیم بر صفر کرد 🥺")
                self.expression = ""
            except Exception:
                self.update_display("اوپس! یه چیزی اشتباه شد 💗")
                self.expression = ""
        
        elif button_text == "%":
            try:
                if self.expression:
                    # محاسبه درصد آخرین عدد وارد شده
                    current = eval(self.expression)
                    result = current / 100
                    self.expression = str(result)
                    self.update_display(self.expression)
            except:
                pass
        
        else:
            current_display = self.display_var.get()
            if current_display in ["0", "نمیشه تقسیم بر صفر کرد 🥺", "اوپس! یه چیزی اشتباه شد 💗"] and button_text not in ["+", "-", "*", "/", "%", "=", "00"]:
                self.expression = button_text
            else:
                self.expression += button_text
            
            self.update_display(self.expression)
    
    def update_display(self, value):
        """به‌روزرسانی نمایشگر"""
        self.display_var.set(value)
    
    def run(self):
        """اجرای برنامه"""
        self.window.mainloop()


# اجرای برنامه
if __name__ == "__main__":
    app = CalculatorApp()
    app.run()