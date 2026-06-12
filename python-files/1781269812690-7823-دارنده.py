import tkinter as tk
import math

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Coded By A-Darandeh")  # اسم برنامه کنار لوگوی تکینتر
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#0a0a0a')
        
        # متغیرهای برنامه
        self.current_input = ""
        self.result_var = tk.StringVar()
        self.result_var.set("0")
        self.memory = 0
        self.is_new_calculation = False
        
        # ساخت ویجت‌ها
        self.create_widgets()
        
        # اتصال کلیدهای صفحه کلید
        self.bind_keyboard()
        
    def create_widgets(self):
        # فریم اصلی
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        # عنوان به انگلیسی
        title_frame = tk.Frame(main_frame, bg='#0a0a0a')
        title_frame.pack(fill='x', pady=(0, 10))
        
        title_en = tk.Label(
            title_frame,
            text="CALCULATOR",
            font=('Segoe UI', 20, 'bold'),
            bg='#0a0a0a',
            fg='#ffd700'
        )
        title_en.pack()
        
        # عنوان فارسی
        title_fa = tk.Label(
            title_frame,
            text="ماشین حساب طلایی",
            font=('Segoe UI', 14),
            bg='#0a0a0a',
            fg='#ffb700'
        )
        title_fa.pack()
        
        # صفحه نمایش پیشرفته
        display_frame = tk.Frame(
            main_frame, 
            bg='#1a1a1a', 
            highlightbackground='#ffd700', 
            highlightthickness=3,
            relief='ridge',
            bd=3
        )
        display_frame.pack(pady=15, padx=15, fill='both')
        
        # نمایش عبارت محاسباتی
        self.expression_label = tk.Label(
            display_frame,
            text="",
            font=('Segoe UI', 12, 'italic'),
            bg='#1a1a1a',
            fg='#ffd700',
            anchor='e',
            height=1
        )
        self.expression_label.pack(fill='x', padx=15, pady=(15, 5))
        
        # خط جداکننده طلایی
        separator = tk.Frame(display_frame, height=2, bg='#ffd700')
        separator.pack(fill='x', padx=15, pady=5)
        
        # نمایش نتیجه با فونت بزرگ
        self.result_entry = tk.Entry(
            display_frame,
            textvariable=self.result_var,
            font=('Segoe UI', 42, 'bold'),
            bg='#1a1a1a',
            fg='#ffd700',
            bd=0,
            justify='right',
            state='readonly',
            readonlybackground='#1a1a1a'
        )
        self.result_entry.pack(fill='x', padx=15, pady=(5, 15), ipady=20)
        
        # دکمه‌های حافظه
        memory_frame = tk.Frame(main_frame, bg='#0a0a0a')
        memory_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        memory_buttons = [
            ('MC', '#333333', '#ffd700'),
            ('MR', '#333333', '#ffd700'),
            ('M+', '#333333', '#ffd700'),
            ('M-', '#333333', '#ffd700')
        ]
        
        for i, (text, bg, fg) in enumerate(memory_buttons):
            btn = tk.Button(
                memory_frame,
                text=text,
                font=('Segoe UI', 10, 'bold'),
                bg=bg,
                fg=fg,
                activebackground='#444444',
                activeforeground='#ffd700',
                bd=1,
                relief='raised',
                cursor='hand2',
                command=lambda x=text: self.memory_function(x)
            )
            btn.grid(row=0, column=i, padx=4, pady=4, sticky='nsew')
        
        for i in range(4):
            memory_frame.grid_columnconfigure(i, weight=1)
        
        # فریم دکمه‌های اصلی
        buttons_frame = tk.Frame(main_frame, bg='#0a0a0a')
        buttons_frame.pack(pady=10, padx=15, fill='both', expand=True)
        
        # دکمه‌های پیشرفته
        buttons = [
            ['(', ')', 'x²', '√'],
            ['C', '⌫', '%', '/'],
            ['7', '8', '9', '*'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '.', '=', '±']
        ]
        
        # رنگ‌بندی متنوع و حرفه‌ای
        for i, row in enumerate(buttons):
            for j, btn_text in enumerate(row):
                if btn_text == '':
                    continue
                
                # رنگ‌بندی پیشرفته
                if btn_text in ['C', '⌫']:
                    bg_color = '#cc0000'
                    fg_color = 'white'
                    active_bg = '#ff0000'
                    font_size = 16
                elif btn_text in ['(', ')', 'x²', '√', '%']:
                    bg_color = '#2c2c2c'
                    fg_color = '#ffd700'
                    active_bg = '#3c3c3c'
                    font_size = 14
                elif btn_text in ['/', '*', '-', '+']:
                    bg_color = '#ff8c00'
                    fg_color = 'black'
                    active_bg = '#ffa500'
                    font_size = 20
                elif btn_text == '=':
                    bg_color = '#ffd700'
                    fg_color = 'black'
                    active_bg = '#ffed4a'
                    font_size = 22
                elif btn_text == '±':
                    bg_color = '#333333'
                    fg_color = '#ffd700'
                    active_bg = '#444444'
                    font_size = 14
                else:
                    bg_color = '#1f1f1f'
                    fg_color = '#ffffff'
                    active_bg = '#2f2f2f'
                    font_size = 18
                
                # ایجاد دکمه با افکت سه بعدی
                btn = tk.Button(
                    buttons_frame,
                    text=btn_text,
                    font=('Segoe UI', font_size, 'bold'),
                    bg=bg_color,
                    fg=fg_color,
                    activebackground=active_bg,
                    activeforeground=fg_color,
                    bd=2,
                    relief='raised',
                    cursor='hand2',
                    command=lambda x=btn_text: self.advanced_click(x)
                )
                
                btn.grid(row=i, column=j, padx=5, pady=5, sticky='nsew')
        
        # تنظیم وزن ستون‌ها و ردیف‌ها
        for i in range(6):
            buttons_frame.grid_rowconfigure(i, weight=1)
        for j in range(4):
            buttons_frame.grid_columnconfigure(j, weight=1)
        
        # اسم سازنده در پایین (دیگر لازم نیست چون در title پنجره هست، ولی برای احتیاط میذارم)
        credit_frame = tk.Frame(main_frame, bg='#0a0a0a')
        credit_frame.pack(side='bottom', fill='x', pady=(10, 0))
        
        line = tk.Frame(credit_frame, height=2, bg='#ffd700')
        line.pack(fill='x', padx=20, pady=(0, 8))
        
        credit_label = tk.Label(
            credit_frame,
            text="Coded By A-Darandeh",
            font=('Segoe UI', 11, 'bold'),
            bg='#0a0a0a',
            fg='#ffd700',
            pady=5
        )
        credit_label.pack()
    
    def memory_function(self, cmd):
        try:
            current = float(self.result_var.get()) if self.result_var.get() != "Error" else 0
        except:
            current = 0
            
        if cmd == 'MC':
            self.memory = 0
        elif cmd == 'MR':
            self.result_var.set(str(self.memory))
            self.current_input = str(self.memory)
            self.update_display()
        elif cmd == 'M+':
            self.memory += current
        elif cmd == 'M-':
            self.memory -= current
    
    def advanced_click(self, value):
        if value == 'C':
            self.clear()
        elif value == '⌫':
            self.backspace()
        elif value == '=':
            self.calculate()
        elif value == 'x²':
            self.square()
        elif value == '√':
            self.square_root()
        elif value == '±':
            self.negate()
        elif value in ['/', '*', '-', '+', '%']:
            self.add_operator(value)
        elif value in ['(', ')']:
            self.add_parenthesis(value)
        else:
            self.add_number(value)
    
    def add_parenthesis(self, paren):
        self.current_input += paren
        self.update_display()
    
    def square(self):
        try:
            current = float(self.result_var.get())
            result = current ** 2
            self.result_var.set(str(result))
            self.current_input = str(result)
            self.update_display()
        except:
            self.result_var.set("Error")
    
    def square_root(self):
        try:
            current = float(self.result_var.get())
            if current >= 0:
                result = math.sqrt(current)
                self.result_var.set(str(result))
                self.current_input = str(result)
                self.update_display()
            else:
                self.result_var.set("Error")
        except:
            self.result_var.set("Error")
    
    def negate(self):
        try:
            current = float(self.result_var.get())
            result = -current
            self.result_var.set(str(result))
            self.current_input = str(result)
            self.update_display()
        except:
            pass
    
    def add_number(self, num):
        if self.result_var.get() == "Error":
            self.clear()
        
        if num == '.':
            parts = self.current_input.split()
            if parts and '.' in parts[-1]:
                return
        
        self.current_input += str(num)
        self.update_display()
        self.live_calc()
    
    def add_operator(self, op):
        if self.current_input == "" and op == '-':
            self.current_input = '-'
            self.update_display()
            return
        
        if self.current_input == "":
            return
        
        if self.current_input[-1] in ['+', '-', '*', '/', '%']:
            self.current_input = self.current_input[:-1] + op
        else:
            self.current_input += op
        
        self.update_display()
        self.live_calc()
    
    def live_calc(self):
        if not self.current_input:
            return
        
        if self.current_input[-1] in ['+', '-', '*', '/', '%']:
            return
        
        try:
            expr = self.current_input.replace('x²', '**2')
            result = eval(expr)
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 8)
            self.result_var.set(str(result))
        except:
            pass
    
    def calculate(self):
        if not self.current_input:
            return
        
        if self.current_input[-1] in ['+', '-', '*', '/', '%']:
            self.current_input = self.current_input[:-1]
        
        if not self.current_input:
            return
        
        try:
            expr = self.current_input.replace('x²', '**2')
            result = eval(expr)
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 8)
            self.result_var.set(str(result))
            self.current_input = str(result)
            self.update_display()
        except:
            self.result_var.set("Error")
            self.current_input = ""
            self.update_display()
    
    def clear(self):
        self.current_input = ""
        self.result_var.set("0")
        self.update_display()
    
    def backspace(self):
        self.current_input = self.current_input[:-1]
        self.update_display()
        if self.current_input == "":
            self.result_var.set("0")
        else:
            self.live_calc()
    
    def update_display(self):
        display_text = self.current_input.replace('*', '×').replace('/', '÷')
        self.expression_label.config(text=display_text)
    
    def bind_keyboard(self):
        self.root.bind('<Key>', self.key_press)
    
    def key_press(self, event):
        key = event.char
        
        if key.isdigit() or key == '.':
            self.add_number(key)
        elif key in ['+', '-', '*', '/', '%']:
            self.add_operator(key)
        elif key == '(' or key == ')':
            self.add_parenthesis(key)
        elif key == '\r':
            self.calculate()
        elif event.keysym == 'BackSpace':
            self.backspace()
        elif event.keysym == 'Escape':
            self.clear()


if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()