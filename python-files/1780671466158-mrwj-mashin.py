import tkinter as tk
from tkinter import ttk, messagebox, font
import math
import random
import time
from datetime import datetime
import os
import json

class SuperProfessionalCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("ماشین حساب")
        self.root.geometry("550x800")
        self.root.resizable(True, True)
        self.root.minsize(500, 700)
        
        # تم سفید شیک با رنگ‌های ملایم
        self.colors = {
            'bg': '#f8f9fa',
            'display_bg': '#ffffff',
            'button_bg': '#e9ecef',
            'button_hover': '#ff6b6b',
            'text': '#2d3436',
            'accent': '#0984e3',
            'operator': '#ff7675',
            'special': '#a29bfe',
            'equal': '#00b894',
            'success': '#00cec9',
            'warning': '#fdcb6e',
            'error': '#d63031',
            'shadow': '#dfe6e9'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # متغیرها
        self.expression = ""
        self.memory = 0
        self.history = []
        self.angle_mode = "rad"
        self.last_result = None
        self.current_theme = "light"
        self.sound_enabled = False
        self.animation_id = None
        
        self.load_settings()
        self.create_modern_ui()
        
    def load_settings(self):
        try:
            if os.path.exists("calc_settings.json"):
                with open("calc_settings.json", "r") as f:
                    settings = json.load(f)
                    self.sound_enabled = settings.get("sound", False)
        except:
            pass
    
    def save_settings(self):
        settings = {
            "theme": self.current_theme,
            "sound": self.sound_enabled
        }
        with open("calc_settings.json", "w") as f:
            json.dump(settings, f)
    
    def create_modern_ui(self):
        # هدر با طراحی مینیمال و شیک
        header_frame = tk.Frame(self.root, bg=self.colors['bg'], height=80)
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 0))
        header_frame.pack_propagate(False)
        
        # خط تزئینی بالای هدر
        top_line = tk.Frame(header_frame, bg=self.colors['accent'], height=3)
        top_line.pack(fill=tk.X, pady=(0, 10))
        
        # فریم اصلی هدر
        content_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.X, expand=True)
        
        # لوگو و اسم سازنده
        creator_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        creator_frame.pack(expand=True)
        
        # آواتار
        avatar = tk.Label(creator_frame, text="🧮", font=('Segoe UI', 28),
                         bg=self.colors['bg'], fg=self.colors['accent'])
        avatar.pack(side=tk.LEFT, padx=(0, 10))
        
        # متن سازنده
        creator_label = tk.Label(creator_frame, text="فرزانه اصغرزاده", 
                                 font=('Segoe UI', 16, 'bold'), 
                                 bg=self.colors['bg'], fg=self.colors['text'])
        creator_label.pack(side=tk.LEFT)
        
        # زیرنویس
        subtitle = tk.Label(creator_frame, text="طراح و توسعه‌دهنده", 
                           font=('Segoe UI', 9), 
                           bg=self.colors['bg'], fg=self.colors['accent'])
        subtitle.pack(side=tk.LEFT, padx=(8, 0))
        
        # دکمه تنظیمات
        settings_btn = tk.Button(content_frame, text="⚙️", font=('Segoe UI', 14),
                                 bg=self.colors['button_bg'], fg=self.colors['text'],
                                 bd=0, cursor='hand2', command=self.show_settings,
                                 relief=tk.FLAT, padx=12, pady=5)
        settings_btn.pack(side=tk.RIGHT)
        
        # صفحه نمایش با افکت سایه
        display_container = tk.Frame(self.root, bg=self.colors['bg'])
        display_container.pack(fill=tk.BOTH, padx=20, pady=15)
        
        # سایه صفحه نمایش
        shadow = tk.Frame(display_container, bg=self.colors['shadow'], height=5)
        shadow.pack(fill=tk.X, padx=10)
        
        display_frame = tk.Frame(display_container, bg=self.colors['display_bg'], 
                                 highlightthickness=1, highlightbackground=self.colors['shadow'],
                                 relief=tk.RAISED, bd=0)
        display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.history_label = tk.Label(display_frame, font=('Segoe UI', 10),
                                      bg=self.colors['display_bg'], fg=self.colors['shadow'],
                                      anchor='e', justify='right')
        self.history_label.pack(fill=tk.X, padx=20, pady=(20, 5))
        
        self.result_var = tk.StringVar(value="0")
        self.result_label = tk.Label(display_frame, textvariable=self.result_var,
                                     font=('Segoe UI', 44, 'bold'),
                                     bg=self.colors['display_bg'], fg=self.colors['text'],
                                     anchor='e', justify='right')
        self.result_label.pack(fill=tk.BOTH, padx=20, pady=(5, 20), expand=True)
        
        # نوار وضعیت
        status_frame = tk.Frame(display_frame, bg=self.colors['display_bg'])
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        self.memory_indicator = tk.Label(status_frame, text="💾 MEM", font=('Segoe UI', 9),
                                         bg=self.colors['display_bg'], fg=self.colors['warning'])
        self.memory_indicator.pack(side=tk.LEFT, padx=5)
        
        self.angle_indicator = tk.Button(status_frame, text="RAD", font=('Segoe UI', 9),
                                         bg=self.colors['display_bg'], fg=self.colors['accent'],
                                         bd=0, cursor='hand2', command=self.toggle_angle_mode,
                                         relief=tk.FLAT)
        self.angle_indicator.pack(side=tk.LEFT, padx=5)
        
        # تب‌های مدرن
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'], tabposition='nw')
        style.configure('TNotebook.Tab', background=self.colors['button_bg'], 
                       foreground=self.colors['text'], padding=[20, 8], font=('Segoe UI', 10))
        style.map('TNotebook.Tab', background=[('selected', self.colors['accent'])],
                 foreground=[('selected', 'white')])
        
        # تب‌ها
        self.basic_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.basic_tab, text="🔢 پایه")
        
        self.scientific_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.scientific_tab, text="🔬 علمی")
        
        self.programmer_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.programmer_tab, text="💻 برنامه‌نویس")
        
        self.history_tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(self.history_tab, text="📜 تاریخچه")
        
        self.create_basic_buttons()
        self.create_scientific_buttons()
        self.create_programmer_tab()
        self.create_history_tab()
    
    def toggle_angle_mode(self):
        if self.angle_mode == "rad":
            self.angle_mode = "deg"
            self.angle_indicator.config(text="DEG")
            self.animate_button(self.angle_indicator)
        else:
            self.angle_mode = "rad"
            self.angle_indicator.config(text="RAD")
            self.animate_button(self.angle_indicator)
    
    def animate_button(self, button):
        """افکت انیمیشن برای دکمه‌ها"""
        original_bg = button.cget('bg')
        button.configure(bg=self.colors['accent'], fg='white')
        self.root.after(150, lambda: button.configure(bg=original_bg, fg=self.colors['accent']))
    
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("تنظیمات")
        settings_window.geometry("350x280")
        settings_window.configure(bg=self.colors['bg'])
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        settings_window.attributes('-alpha', 0.95)
        
        tk.Label(settings_window, text="⚙️ تنظیمات ماشین حساب", 
                font=('Segoe UI', 16, 'bold'), bg=self.colors['bg'], fg=self.colors['text']).pack(pady=20)
        
        # صدا
        sound_var = tk.BooleanVar(value=self.sound_enabled)
        sound_btn = tk.Checkbutton(settings_window, text="🔊 فعال کردن صدای دکمه‌ها", variable=sound_var,
                                  bg=self.colors['bg'], fg=self.colors['text'], 
                                  selectcolor=self.colors['bg'], font=('Segoe UI', 11))
        sound_btn.pack(pady=15)
        
        def save_settings():
            self.sound_enabled = sound_var.get()
            self.save_settings()
            self.animate_button(save_btn)
            settings_window.destroy()
            messagebox.showinfo("تنظیمات", "تنظیمات با موفقیت ذخیره شد!")
        
        save_btn = tk.Button(settings_window, text="💾 ذخیره تنظیمات", command=save_settings,
                            bg=self.colors['equal'], fg='white', font=('Segoe UI', 12, 'bold'),
                            bd=0, cursor='hand2', padx=30, pady=10, relief=tk.FLAT)
        save_btn.pack(pady=20)
    
    def create_basic_buttons(self):
        buttons_frame = tk.Frame(self.basic_tab, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        buttons = [
            ('C', 0, 0, '#ff7675'), ('⌫', 0, 1, '#fab1a0'), ('%', 0, 2, '#a29bfe'), ('÷', 0, 3, '#0984e3'),
            ('7', 1, 0, '#dfe6e9'), ('8', 1, 1, '#dfe6e9'), ('9', 1, 2, '#dfe6e9'), ('×', 1, 3, '#0984e3'),
            ('4', 2, 0, '#dfe6e9'), ('5', 2, 1, '#dfe6e9'), ('6', 2, 2, '#dfe6e9'), ('-', 2, 3, '#0984e3'),
            ('1', 3, 0, '#dfe6e9'), ('2', 3, 1, '#dfe6e9'), ('3', 3, 2, '#dfe6e9'), ('+', 3, 3, '#0984e3'),
            ('±', 4, 0, '#a29bfe'), ('0', 4, 1, '#dfe6e9'), ('.', 4, 2, '#dfe6e9'), ('=', 4, 3, '#00b894'),
            ('MC', 5, 0, '#fdcb6e'), ('MR', 5, 1, '#fdcb6e'), ('M+', 5, 2, '#fdcb6e'), ('M-', 5, 3, '#fdcb6e')
        ]
        
        for btn in buttons:
            text, row, col, color = btn
            btn_widget = tk.Button(buttons_frame, text=text, font=('Segoe UI', 14, 'bold'),
                                   bg=color, fg='#2d3436' if color == '#dfe6e9' else 'white', 
                                   bd=0, relief=tk.FLAT,
                                   activebackground=self.colors['button_hover'],
                                   cursor='hand2', padx=5, pady=10)
            btn_widget.grid(row=row, column=col, padx=6, pady=6, sticky='nsew')
            btn_widget.bind('<Button-1>', lambda e, t=text: self.button_click(t))
            btn_widget.bind('<Enter>', lambda e, b=btn_widget, c=color: self.on_enter(b, c))
            btn_widget.bind('<Leave>', lambda e, b=btn_widget, c=color: self.on_leave(b, c))
        
        for i in range(6):
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)
    
    def create_scientific_buttons(self):
        canvas = tk.Canvas(self.scientific_tab, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.scientific_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scientific_buttons = [
            ('sin', 'sin(', 0, 0), ('cos', 'cos(', 0, 1), ('tan', 'tan(', 0, 2),
            ('asin', 'asin(', 0, 3), ('acos', 'acos(', 0, 4), ('atan', 'atan(', 0, 5),
            ('sinh', 'sinh(', 1, 0), ('cosh', 'cosh(', 1, 1), ('tanh', 'tanh(', 1, 2),
            ('log₁₀', 'log10(', 1, 3), ('ln', 'log(', 1, 4), ('√', 'sqrt(', 1, 5),
            ('x²', '^2', 2, 0), ('x³', '^3', 2, 1), ('xʸ', '^', 2, 2),
            ('eˣ', 'exp(', 2, 3), ('10ˣ', '10**', 2, 4), ('|x|', 'abs(', 2, 5),
            ('π', 'pi', 3, 0), ('e', 'e', 3, 1), ('Rand', 'random', 3, 2),
            ('(', '(', 3, 3), (')', ')', 3, 4), ('mod', '%', 3, 5),
            ('floor', 'floor(', 4, 0), ('ceil', 'ceil(', 4, 1), ('round', 'round(', 4, 2),
            ('deg', 'degrees(', 4, 3), ('rad', 'radians(', 4, 4), ('!', 'factorial(', 4, 5)
        ]
        
        for btn in scientific_buttons:
            text, cmd, row, col = btn
            btn_widget = tk.Button(scrollable_frame, text=text, font=('Segoe UI', 10, 'bold'),
                                  bg=self.colors['button_bg'], fg=self.colors['text'], 
                                  bd=0, relief=tk.FLAT,
                                  activebackground=self.colors['button_hover'],
                                  width=8, height=2, cursor='hand2')
            btn_widget.grid(row=row, column=col, padx=4, pady=4)
            btn_widget.bind('<Button-1>', lambda e, t=cmd: self.add_to_expression(t))
            btn_widget.bind('<Enter>', lambda e, b=btn_widget: self.on_enter_scientific(b))
            btn_widget.bind('<Leave>', lambda e, b=btn_widget: self.on_leave_scientific(b))
    
    def create_programmer_tab(self):
        converter_frame = tk.Frame(self.programmer_tab, bg=self.colors['bg'])
        converter_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header = tk.Label(converter_frame, text="مبدل مبنا", font=('Segoe UI', 16, 'bold'),
                         bg=self.colors['bg'], fg=self.colors['accent'])
        header.pack(pady=10)
        
        input_frame = tk.Frame(converter_frame, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X, pady=15)
        
        tk.Label(input_frame, text="عدد مورد نظر:", bg=self.colors['bg'], 
                fg=self.colors['text'], font=('Segoe UI', 11)).pack(anchor='w')
        
        self.convert_entry = tk.Entry(input_frame, font=('Consolas', 14),
                                      bg=self.colors['display_bg'], fg=self.colors['text'],
                                      insertbackground=self.colors['accent'],
                                      relief=tk.FLAT, highlightthickness=1,
                                      highlightcolor=self.colors['accent'],
                                      highlightbackground=self.colors['shadow'])
        self.convert_entry.pack(fill=tk.X, pady=5, ipady=8)
        
        base_frame = tk.Frame(converter_frame, bg=self.colors['bg'])
        base_frame.pack(pady=15)
        
        from_frame = tk.Frame(base_frame, bg=self.colors['bg'])
        from_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(from_frame, text="از مبنا:", bg=self.colors['bg'], fg=self.colors['text']).pack()
        self.from_base = ttk.Combobox(from_frame, values=[2, 8, 10, 16], width=8)
        self.from_base.set(10)
        self.from_base.pack(pady=5)
        
        to_frame = tk.Frame(base_frame, bg=self.colors['bg'])
        to_frame.pack(side=tk.LEFT, padx=10)
        tk.Label(to_frame, text="به مبنا:", bg=self.colors['bg'], fg=self.colors['text']).pack()
        self.to_base = ttk.Combobox(to_frame, values=[2, 8, 10, 16], width=8)
        self.to_base.set(16)
        self.to_base.pack(pady=5)
        
        def convert_base():
            try:
                num = int(self.convert_entry.get(), int(self.from_base.get()))
                result = ""
                if int(self.to_base.get()) == 2:
                    result = bin(num)[2:]
                elif int(self.to_base.get()) == 8:
                    result = oct(num)[2:]
                elif int(self.to_base.get()) == 10:
                    result = str(num)
                elif int(self.to_base.get()) == 16:
                    result = hex(num)[2:].upper()
                
                self.convert_result.config(text=f"✨ نتیجه: {result}")
                self.animate_result(self.convert_result)
            except:
                self.convert_result.config(text="❌ خطا در تبدیل!")
        
        convert_btn = tk.Button(converter_frame, text="🔄 تبدیل", command=convert_base,
                               bg=self.colors['equal'], fg='white', font=('Segoe UI', 12, 'bold'),
                               bd=0, cursor='hand2', relief=tk.FLAT, padx=30, pady=10)
        convert_btn.pack(pady=15)
        
        self.convert_result = tk.Label(converter_frame, text="✨ نتیجه: ---", 
                                       font=('Segoe UI', 13, 'bold'),
                                       bg=self.colors['bg'], fg=self.colors['success'])
        self.convert_result.pack(pady=10)
    
    def animate_result(self, label):
        original_color = label.cget('fg')
        label.config(fg=self.colors['accent'])
        self.root.after(300, lambda: label.config(fg=original_color))
    
    def create_history_tab(self):
        export_frame = tk.Frame(self.history_tab, bg=self.colors['bg'])
        export_frame.pack(fill=tk.X, padx=15, pady=15)
        
        export_btn = tk.Button(export_frame, text="📥 صادرات به فایل", command=self.export_history,
                              bg=self.colors['success'], fg='white', font=('Segoe UI', 11),
                              bd=0, cursor='hand2', relief=tk.FLAT, padx=20, pady=8)
        export_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(export_frame, text="🗑️ پاک کردن", command=self.clear_history,
                             bg=self.colors['error'], fg='white', font=('Segoe UI', 11),
                             bd=0, cursor='hand2', relief=tk.FLAT, padx=20, pady=8)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.history_text = tk.Text(self.history_tab, font=('Consolas', 11),
                                    bg=self.colors['display_bg'], fg=self.colors['text'],
                                    wrap=tk.WORD, bd=0, relief=tk.FLAT,
                                    highlightthickness=1, highlightbackground=self.colors['shadow'])
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    def on_enter(self, button, original_color):
        button.configure(bg=self.colors['button_hover'], fg='white')
    
    def on_leave(self, button, original_color):
        button.configure(bg=original_color, fg='#2d3436' if original_color == '#dfe6e9' else 'white')
    
    def on_enter_scientific(self, button):
        button.configure(bg=self.colors['button_hover'], fg='white')
    
    def on_leave_scientific(self, button):
        button.configure(bg=self.colors['button_bg'], fg=self.colors['text'])
    
    def button_click(self, value):
        if self.sound_enabled:
            self.play_sound()
        
        if value == 'C':
            self.clear()
        elif value == '⌫':
            self.backspace()
        elif value == '=':
            self.calculate()
        elif value == '±':
            self.negate()
        elif value == '%':
            self.percent()
        elif value == '÷':
            self.add_to_expression('/')
        elif value == '×':
            self.add_to_expression('*')
        elif value == 'MC':
            self.memory = 0
            self.memory_indicator.config(fg=self.colors['warning'])
        elif value == 'MR':
            self.add_to_expression(str(self.memory))
        elif value == 'M+':
            try:
                self.memory += eval(self.expression) if self.expression else 0
                self.memory_indicator.config(fg=self.colors['success'])
            except:
                pass
        elif value == 'M-':
            try:
                self.memory -= eval(self.expression) if self.expression else 0
                self.memory_indicator.config(fg=self.colors['success'])
            except:
                pass
        else:
            self.add_to_expression(value)
    
    def play_sound(self):
        pass
    
    def add_to_expression(self, value):
        if value == 'random':
            value = str(random.random())
        elif value == 'pi':
            value = str(math.pi)
        elif value == 'e':
            value = str(math.e)
        elif value == 'factorial(':
            if self.expression:
                try:
                    result = math.factorial(int(eval(self.expression)))
                    self.expression = str(result)
                    self.update_display()
                    return
                except:
                    pass
        
        self.expression += str(value)
        self.update_display()
    
    def update_display(self):
        display_text = self.expression if self.expression else "0"
        self.result_var.set(display_text)
        
        self.result_label.configure(fg=self.colors['accent'])
        self.root.after(100, lambda: self.result_label.configure(fg=self.colors['text']))
    
    def clear(self):
        self.expression = ""
        self.update_display()
    
    def backspace(self):
        self.expression = self.expression[:-1]
        self.update_display()
    
    def negate(self):
        if self.expression:
            try:
                result = -eval(self.expression)
                self.expression = str(result)
                self.update_display()
            except:
                pass
    
    def percent(self):
        if self.expression:
            try:
                result = eval(self.expression) / 100
                self.expression = str(result)
                self.update_display()
            except:
                pass
    
    def calculate(self):
        if not self.expression:
            return
        
        try:
            expr = self.expression.replace('^', '**')
            expr = expr.replace('log10(', 'math.log10(')
            expr = expr.replace('log(', 'math.log(')
            expr = expr.replace('sqrt(', 'math.sqrt(')
            
            if self.angle_mode == "deg":
                expr = expr.replace('sin(', 'math.sin(math.radians(')
                expr = expr.replace('cos(', 'math.cos(math.radians(')
                expr = expr.replace('tan(', 'math.tan(math.radians(')
                expr = expr.replace('))', ')')
            else:
                expr = expr.replace('sin(', 'math.sin(')
                expr = expr.replace('cos(', 'math.cos(')
                expr = expr.replace('tan(', 'math.tan(')
            
            expr = expr.replace('asin(', 'math.asin(')
            expr = expr.replace('acos(', 'math.acos(')
            expr = expr.replace('atan(', 'math.atan(')
            expr = expr.replace('sinh(', 'math.sinh(')
            expr = expr.replace('cosh(', 'math.cosh(')
            expr = expr.replace('tanh(', 'math.tanh(')
            expr = expr.replace('exp(', 'math.exp(')
            expr = expr.replace('abs(', 'abs(')
            expr = expr.replace('floor(', 'math.floor(')
            expr = expr.replace('ceil(', 'math.ceil(')
            expr = expr.replace('round(', 'round(')
            expr = expr.replace('degrees(', 'math.degrees(')
            expr = expr.replace('radians(', 'math.radians(')
            
            result = eval(expr)
            
            history_entry = f"{self.expression} = {result}\n"
            self.history.append(history_entry)
            self.history_text.insert(tk.END, history_entry)
            self.history_text.see(tk.END)
            
            self.expression = str(result)
            self.update_display()
            
            self.result_label.configure(fg=self.colors['success'])
            self.root.after(200, lambda: self.result_label.configure(fg=self.colors['text']))
            
        except Exception as e:
            messagebox.showerror("خطا!", f"عبارت نامعتبر است!\n{str(e)}")
            self.clear()
    
    def export_history(self):
        if not self.history:
            messagebox.showwarning("هشدار", "تاریخچه خالی است!")
            return
        
        filename = f"calc_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("📊 تاریخچه محاسبات ماشین حساب\n")
            f.write("👩‍💻 ساخته شده توسط فرزانه اصغرزاده\n")
            f.write("="*50 + "\n\n")
            f.writelines(self.history)
        
        messagebox.showinfo("موفق", f"✅ تاریخچه با موفقیت در فایل\n{filename}\nذخیره شد!")
    
    def clear_history(self):
        self.history.clear()
        self.history_text.delete(1.0, tk.END)
        messagebox.showinfo("تاریخچه", "🗑️ تاریخچه با موفقیت پاک شد!")

class SplashScreen:
    def __init__(self):
        self.splash = tk.Tk()
        self.splash.title("")
        self.splash.geometry("500x400")
        self.splash.configure(bg='#f8f9fa')
        self.splash.overrideredirect(True)
        
        self.splash.attributes('-alpha', 0.95)
        self.splash.eval('tk::PlaceWindow . center')
        
        main_frame = tk.Frame(self.splash, bg='#f8f9fa', relief=tk.RAISED, bd=0)
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        self.label = tk.Label(main_frame, text="🧮", font=('Segoe UI', 80),
                             bg='#f8f9fa', fg='#0984e3')
        self.label.pack(expand=True)
        
        self.animation_icons = ['🧮', '✨', '⭐', '🌟', '💫']
        self.anim_index = 0
        self.animate_logo()
        
        line = tk.Frame(main_frame, bg='#0984e3', height=2, width=200)
        line.pack(pady=10)
        
        title = tk.Label(main_frame, text="ماشین حساب", 
                        font=('Segoe UI', 28, 'bold'), bg='#f8f9fa', fg='#2d3436')
        title.pack(pady=5)
        
        creator_frame = tk.Frame(main_frame, bg='#0984e3', relief=tk.RAISED, bd=0)
        creator_frame.pack(pady=15)
        
        creator_label = tk.Label(creator_frame, text="✨ فرزانه اصغرزاده ✨", 
                                 font=('Segoe UI', 16, 'bold'), 
                                 bg='#0984e3', fg='white',
                                 padx=30, pady=12)
        creator_label.pack()
        
        subtitle = tk.Label(main_frame, text="طراح و توسعه‌دهنده حرفه‌ای", 
                          font=('Segoe UI', 11), bg='#f8f9fa', fg='#636e72')
        subtitle.pack()
        
        version = tk.Label(main_frame, text="نسخه 3.0", 
                          font=('Segoe UI', 9), bg='#f8f9fa', fg='#b2bec3')
        version.pack(pady=10)
        
        self.progress = ttk.Progressbar(main_frame, length=350, mode='indeterminate',
                                        style='Accent.Horizontal.TProgressbar')
        self.progress.pack(pady=20)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Accent.Horizontal.TProgressbar", background='#0984e3', 
                       troughcolor='#dfe6e9', bordercolor='#f8f9fa', lightcolor='#0984e3',
                       darkcolor='#0984e3')
        
        self.progress.start(15)
        
        self.splash.after(2500, self.finish)
        self.splash.mainloop()
    
    def animate_logo(self):
        self.label.config(text=self.animation_icons[self.anim_index])
        self.anim_index = (self.anim_index + 1) % len(self.animation_icons)
        self.splash.after(200, self.animate_logo)
    
    def finish(self):
        self.splash.destroy()
        root = tk.Tk()
        app = SuperProfessionalCalculator(root)
        root.mainloop()

if __name__ == "__main__":
    SplashScreen()