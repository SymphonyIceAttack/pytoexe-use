import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import math
import re
import random
from fractions import Fraction

class AdvancedCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Расширенный Калькулятор")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Переменные
        self.current_input = tk.StringVar()
        self.history = []
        self.memory = 0
        self.deg_rad_mode = "DEG"  # DEG или RAD
        self.exact_mode = True  # Режим точных значений (дроби)
        
        # Цветовая схема
        self.colors = {
            'bg': '#2b2b2b',
            'display_bg': '#1e1e1e',
            'button_bg': '#3c3c3c',
            'number_bg': '#4a4a4a',
            'operator_bg': '#ff9500',
            'scientific_bg': '#5856d6',
            'memory_bg': '#ff2d55',
            'special_bg': '#8e8e93',
            'text': '#ffffff',
            'history_text': '#8e8e93'
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Настройка стилей
        self.root.configure(bg=self.colors['bg'])
        
        # Основной фрейм
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель с режимами
        self.create_mode_panel(main_frame)
        
        # Дисплей и история
        self.create_display(main_frame)
        
        # Панель памяти (свернутая)
        self.create_memory_panel(main_frame)
        
        # Кнопки
        self.create_buttons(main_frame)
    
    def create_mode_panel(self, parent):
        mode_frame = tk.Frame(parent, bg=self.colors['bg'])
        mode_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Кнопки режимов
        self.deg_rad_btn = tk.Button(mode_frame, text=f"Режим: {self.deg_rad_mode}", 
                                     bg=self.colors['scientific_bg'], fg=self.colors['text'],
                                     font=("Arial", 10), command=self.toggle_deg_rad)
        self.deg_rad_btn.pack(side=tk.LEFT, padx=2)
        
        self.exact_mode_btn = tk.Button(mode_frame, text="Точные значения", 
                                        bg=self.colors['scientific_bg'], fg=self.colors['text'],
                                        font=("Arial", 10), command=self.toggle_exact_mode)
        self.exact_mode_btn.pack(side=tk.LEFT, padx=2)
        
        # Индикатор памяти
        self.memory_indicator = tk.Label(mode_frame, text="Память: 0", 
                                        bg=self.colors['bg'], fg=self.colors['memory_bg'],
                                        font=("Arial", 10))
        self.memory_indicator.pack(side=tk.RIGHT, padx=2)
    
    def create_display(self, parent):
        display_frame = tk.Frame(parent, bg=self.colors['bg'])
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Поле истории
        self.history_label = tk.Label(display_frame, text="", 
                                     bg=self.colors['display_bg'], fg=self.colors['history_text'],
                                     font=("Arial", 10), anchor="e", height=2)
        self.history_label.pack(fill=tk.X, pady=(0, 2))
        
        # Основной дисплей
        display = tk.Entry(display_frame, textvariable=self.current_input, 
                          bg=self.colors['display_bg'], fg=self.colors['text'],
                          font=("Arial", 20), justify="right", bd=0)
        display.pack(fill=tk.X, ipady=10)
    
    def create_memory_panel(self, parent):
        # Панель памяти (скрываемая)
        self.memory_frame = tk.Frame(parent, bg=self.colors['memory_bg'], bd=1, relief=tk.RAISED)
        self.memory_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Заголовок с кнопкой сворачивания
        header_frame = tk.Frame(self.memory_frame, bg=self.colors['memory_bg'])
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="ПАМЯТЬ", bg=self.colors['memory_bg'], 
                fg=self.colors['text'], font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.memory_visible = True
        tk.Button(header_frame, text="▼", bg=self.colors['memory_bg'], 
                 fg=self.colors['text'], bd=0, command=self.toggle_memory).pack(side=tk.RIGHT, padx=5)
        
        # Кнопки памяти
        self.memory_buttons_frame = tk.Frame(self.memory_frame, bg=self.colors['memory_bg'])
        self.memory_buttons_frame.pack(fill=tk.X, pady=5)
        
        memory_buttons = [
            ("MC", "Очистить память"), ("MR", "Восстановить"),
            ("M+", "Добавить"), ("M-", "Вычесть"), ("MS", "Сохранить")
        ]
        
        for text, tooltip in memory_buttons:
            btn = tk.Button(self.memory_buttons_frame, text=text,
                          bg=self.colors['memory_bg'], fg=self.colors['text'],
                          font=("Arial", 9, "bold"), bd=1,
                          command=lambda t=text: self.button_click(t))
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            self.create_tooltip(btn, tooltip)
    
    def toggle_memory(self):
        if self.memory_visible:
            self.memory_buttons_frame.pack_forget()
            self.memory_visible = False
        else:
            self.memory_buttons_frame.pack(fill=tk.X, pady=5)
            self.memory_visible = True
    
    def create_buttons(self, parent):
        # Основной фрейм с кнопками
        buttons_frame = tk.Frame(parent, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Стилизованные кнопки
        button_style = {
            'font': ("Arial", 11),
            'bd': 1,
            'relief': tk.RAISED
        }
        
        # Расположение кнопок с группировкой - ИСПРАВЛЕНО
        button_groups = [
            # Группа 1: Очистка и специальные
            [("C", "special", "Очистить ввод"), ("CE", "special", "Полная очистка"), 
             ("⌫", "special", "Удалить последний"), ("±", "special", "Смена знака")],
            
            # Группа 2: Скобки и основные операции
            [("(", "operator", "Открыть скобку"), (")", "operator", "Закрыть скобку"),
             ("%", "operator", "Процент"), ("mod", "operator", "Остаток от деления")],
            
            # Группа 3: Цифры и деление
            [("7", "number"), ("8", "number"), ("9", "number"), ("÷", "operator", "Деление")],
            
            # Группа 4: Цифры и умножение
            [("4", "number"), ("5", "number"), ("6", "number"), ("×", "operator", "Умножение")],
            
            # Группа 5: Цифры и вычитание
            [("1", "number"), ("2", "number"), ("3", "number"), ("-", "operator", "Вычитание")],
            
            # Группа 6: Цифры и сложение
            [("0", "number"), (".", "number"), ("=", "operator", "Вычислить"), ("+", "operator", "Сложение")],
            
            # Группа 7: Дроби
            [("a/b", "scientific", "Ввести дробь"), ("→dec", "scientific", "В десятичную"),
             ("→frac", "scientific", "В дробь"), ("div", "operator", "Целочисленное деление")],
            
            # Группа 8: Степени и корни
            [("x²", "scientific", "Квадрат"), ("√", "scientific", "Корень"),
             ("x^y", "scientific", "Степень"), ("1/x", "scientific", "Обратное число")],
            
            # Группа 9: Тригонометрия
            [("sin", "scientific", "Синус"), ("cos", "scientific", "Косинус"),
             ("tan", "scientific", "Тангенс"), ("|x|", "scientific", "Модуль")],
            
            # Группа 10: Логарифмы и константы
            [("log", "scientific", "log₁₀"), ("ln", "scientific", "ln"),
             ("10ⁿ", "scientific", "10 в степени"), ("eⁿ", "scientific", "e в степени")],
            
            # Группа 11: Факториал и случайные числа
            [("n!", "scientific", "Факториал"), ("Случ.", "special", "Случайное число"),
             ("π", "constant", "Число Пи"), ("e", "constant", "Число Эйлера")],
            
            # Группа 12: Системные
            [("История", "system", "Просмотр истории"), ("Справка", "system", "Помощь")]
        ]
        
        for group in button_groups:
            group_frame = tk.Frame(buttons_frame, bg=self.colors['bg'])
            group_frame.pack(fill=tk.X, pady=2)
            
            for btn_info in group:
                # Обработка разного количества элементов в кортеже
                if len(btn_info) == 2:
                    text, btn_type = btn_info
                    tooltip = None
                else:  # len == 3
                    text, btn_type, tooltip = btn_info
                
                # Определение цвета
                if btn_type == "number":
                    color = self.colors['number_bg']
                elif btn_type == "operator":
                    color = self.colors['operator_bg']
                elif btn_type == "scientific":
                    color = self.colors['scientific_bg']
                elif btn_type in ["system", "special"]:
                    color = self.colors['special_bg']
                elif btn_type == "constant":
                    color = self.colors['scientific_bg']
                else:
                    color = self.colors['button_bg']
                
                btn = tk.Button(group_frame, text=text, bg=color, fg=self.colors['text'],
                              **button_style, command=lambda t=text: self.button_click(t))
                btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
                
                if tooltip:
                    self.create_tooltip(btn, tooltip)
    
    def create_tooltip(self, widget, text):
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, bg="#ffffe0", relief=tk.SOLID, borderwidth=1)
            label.pack()
            
            widget.tooltip = tooltip
            
            def hide_tooltip():
                if hasattr(widget, 'tooltip'):
                    widget.tooltip.destroy()
            
            widget.tooltip_timer = widget.after(500, hide_tooltip)
        
        def on_leave(event):
            if hasattr(widget, 'tooltip_timer'):
                widget.after_cancel(widget.tooltip_timer)
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', on_leave)
    
    def button_click(self, button_text):
        current = self.current_input.get()
        
        try:
            if button_text.isdigit() or button_text == ".":
                self.handle_number(button_text)
            elif button_text in ["+", "-", "×", "÷", "x^y", "%", "div", "mod"]:
                self.handle_operator(button_text)
            elif button_text == "=":
                self.calculate_result()
            elif button_text in ["C", "CE", "⌫", "±"]:
                self.handle_special(button_text)
            elif button_text in ["sin", "cos", "tan", "log", "ln", "√", "x²", "n!", "1/x", "|x|", "10ⁿ", "eⁿ"]:
                self.handle_scientific(button_text)
            elif button_text in ["MC", "MR", "M+", "M-", "MS"]:
                self.handle_memory(button_text)
            elif button_text == "a/b":
                self.current_input.set(current + "/")
            elif button_text == "→dec":
                self.to_decimal()
            elif button_text == "→frac":
                self.to_fraction()
            elif button_text == "π":
                self.current_input.set(current + str(math.pi))
            elif button_text == "e":
                self.current_input.set(current + str(math.e))
            elif button_text == "(":
                self.current_input.set(current + "(")
            elif button_text == ")":
                self.current_input.set(current + ")")
            elif button_text == "DEG/RAD":
                self.toggle_deg_rad()
            elif button_text == "Случ.":
                self.handle_random()
            elif button_text == "История":
                self.show_history()
            elif button_text == "Справка":
                self.show_help()
                
        except Exception as e:
            self.current_input.set("Ошибка")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
    
    def handle_number(self, number):
        current = self.current_input.get()
        if current == "0" or current == "Ошибка":
            self.current_input.set(number)
        else:
            self.current_input.set(current + number)
    
    def handle_operator(self, operator):
        current = self.current_input.get()
        operators_map = {
            "×": "*", "÷": "/", "x^y": "**", "%": "/100*", 
            "div": "//", "mod": "%"
        }
        
        if operator == "%":
            if current and current != "Ошибка":
                try:
                    # Обработка дробей для процентов
                    if '/' in current:
                        value = float(Fraction(current))
                    else:
                        value = float(current)
                    self.current_input.set(f"{value}/100*")
                except:
                    self.current_input.set("Ошибка")
        else:
            op = operators_map.get(operator, operator)
            self.current_input.set(current + op)
    
    def handle_special(self, special):
        current = self.current_input.get()
        
        if special == "C":
            self.current_input.set("0")
        elif special == "CE":
            self.current_input.set("0")
            self.history_label.config(text="")
        elif special == "⌫":
            if len(current) > 1:
                self.current_input.set(current[:-1])
            else:
                self.current_input.set("0")
        elif special == "±":
            if current and current != "0" and current != "Ошибка":
                if current[0] == "-":
                    self.current_input.set(current[1:])
                else:
                    self.current_input.set("-" + current)
    
    def handle_scientific(self, func):
        try:
            current = self.current_input.get()
            if not current or current == "Ошибка":
                return
            
            # Обработка дробей
            if '/' in current:
                value = float(Fraction(current))
            else:
                value = float(current)
            
            # Конвертация в радианы если нужно
            if self.deg_rad_mode == "DEG" and func in ["sin", "cos", "tan"]:
                rad_value = math.radians(value)
            else:
                rad_value = value
            
            result = None
            exact = None
            
            if func == "sin":
                result = math.sin(rad_value)
                if self.deg_rad_mode == "DEG":
                    exact = self.get_exact_trig_value(value, "sin")
            elif func == "cos":
                result = math.cos(rad_value)
                if self.deg_rad_mode == "DEG":
                    exact = self.get_exact_trig_value(value, "cos")
            elif func == "tan":
                result = math.tan(rad_value)
                if self.deg_rad_mode == "DEG":
                    exact = self.get_exact_trig_value(value, "tan")
            elif func == "log":
                result = math.log10(value) if value > 0 else float('nan')
            elif func == "ln":
                result = math.log(value) if value > 0 else float('nan')
            elif func == "√":
                result = math.sqrt(value) if value >= 0 else float('nan')
            elif func == "x²":
                result = value ** 2
            elif func == "n!":
                if value.is_integer() and value >= 0 and value <= 1000:
                    result = math.factorial(int(value))
                else:
                    result = float('nan')
            elif func == "1/x":
                result = 1 / value if value != 0 else float('nan')
            elif func == "|x|":
                result = abs(value)
            elif func == "10ⁿ":
                result = 10 ** value
            elif func == "eⁿ":
                result = math.exp(value)
            
            if math.isnan(result):
                self.current_input.set("Ошибка")
            else:
                if self.exact_mode and exact and exact != str(result):
                    self.current_input.set(exact)
                    self.add_to_history(f"{func}({current}°) = {exact}")
                else:
                    # Форматирование результата
                    if abs(result) < 1e-10:
                        result = 0
                    elif abs(result) > 1e10:
                        result = f"{result:.4e}"
                    else:
                        result = round(result, 10)
                        if result == int(result):
                            result = int(result)
                    
                    self.current_input.set(str(result))
                    self.add_to_history(f"{func}({current}) = {result}")
                
        except Exception as e:
            self.current_input.set("Ошибка")
    
    def get_exact_trig_value(self, angle, func):
        """Возвращает точное тригонометрическое значение для стандартных углов"""
        # Округляем до ближайшего целого для сравнения
        angle = round(angle)
        
        exact_values = {
            0: {"sin": "0", "cos": "1", "tan": "0"},
            30: {"sin": "1/2", "cos": "√3/2", "tan": "√3/3"},
            45: {"sin": "√2/2", "cos": "√2/2", "tan": "1"},
            60: {"sin": "√3/2", "cos": "1/2", "tan": "√3"},
            90: {"sin": "1", "cos": "0", "tan": "∞"},
            120: {"sin": "√3/2", "cos": "-1/2", "tan": "-√3"},
            135: {"sin": "√2/2", "cos": "-√2/2", "tan": "-1"},
            150: {"sin": "1/2", "cos": "-√3/2", "tan": "-√3/3"},
            180: {"sin": "0", "cos": "-1", "tan": "0"},
            210: {"sin": "-1/2", "cos": "-√3/2", "tan": "√3/3"},
            225: {"sin": "-√2/2", "cos": "-√2/2", "tan": "1"},
            240: {"sin": "-√3/2", "cos": "-1/2", "tan": "√3"},
            270: {"sin": "-1", "cos": "0", "tan": "∞"},
            300: {"sin": "-√3/2", "cos": "1/2", "tan": "-√3"},
            315: {"sin": "-√2/2", "cos": "√2/2", "tan": "-1"},
            330: {"sin": "-1/2", "cos": "√3/2", "tan": "-√3/3"},
            360: {"sin": "0", "cos": "1", "tan": "0"}
        }
        
        if angle in exact_values:
            return exact_values[angle].get(func)
        return None
    
    def to_decimal(self):
        """Преобразование дроби в десятичное число"""
        current = self.current_input.get()
        try:
            if '/' in current:
                frac = Fraction(current)
                self.current_input.set(str(float(frac)))
                self.add_to_history(f"{current} = {float(frac)}")
        except:
            pass
    
    def to_fraction(self):
        """Преобразование десятичного числа в дробь"""
        current = self.current_input.get()
        try:
            value = float(current)
            frac = Fraction(value).limit_denominator(1000)
            self.current_input.set(str(frac))
            self.add_to_history(f"{current} = {frac}")
        except:
            pass
    
    def handle_memory(self, memory_op):
        current = self.current_input.get()
        
        try:
            value = 0
            if current and current != "Ошибка":
                if '/' in current:
                    value = float(Fraction(current))
                else:
                    value = float(current)
            
            if memory_op == "MC":
                self.memory = 0
                messagebox.showinfo("Память", "Память очищена")
            elif memory_op == "MR":
                self.current_input.set(str(self.memory))
            elif memory_op == "M+":
                self.memory += value
                messagebox.showinfo("Память", "Добавлено к памяти")
            elif memory_op == "M-":
                self.memory -= value
                messagebox.showinfo("Память", "Вычтено из памяти")
            elif memory_op == "MS":
                self.memory = value
                messagebox.showinfo("Память", "Значение сохранено")
            
            self.memory_indicator.config(text=f"Память: {self.memory}")
        except:
            self.current_input.set("Ошибка")
    
    def handle_random(self):
        random_num = random.random()
        self.current_input.set(str(random_num))
        self.add_to_history(f"Случайное число: {random_num}")
    
    def toggle_deg_rad(self):
        self.deg_rad_mode = "RAD" if self.deg_rad_mode == "DEG" else "DEG"
        self.deg_rad_btn.config(text=f"Режим: {self.deg_rad_mode}")
    
    def toggle_exact_mode(self):
        self.exact_mode = not self.exact_mode
        self.exact_mode_btn.config(text="Точные значения" if self.exact_mode else "Десятичные")
    
    def calculate_result(self):
        try:
            expression = self.current_input.get()
            
            if not expression or expression == "Ошибка":
                return
            
            # Замена символов
            expression = (expression.replace("×", "*")
                         .replace("÷", "/")
                         .replace("^", "**")
                         .replace("//", "//")
                         .replace("mod", "%"))
            
            # Обработка процентов
            if "/100*" in expression:
                parts = expression.split("/100*")
                if len(parts) == 2:
                    base = float(parts[0])
                    percentage_of = float(parts[1]) if parts[1] else 1
                    result = base / 100 * percentage_of
                else:
                    result = eval(parts[0]) / 100
            else:
                # Безопасное вычисление
                if not self.is_safe_expression(expression):
                    self.current_input.set("Ошибка")
                    return
                
                result = eval(expression, {"__builtins__": None}, 
                             {"math": math, "pi": math.pi, "e": math.e})
            
            # Форматирование результата
            if isinstance(result, (int, float)):
                if result == int(result):
                    result = int(result)
                else:
                    result = round(result, 10)
                    if result == int(result):
                        result = int(result)
            
            self.current_input.set(str(result))
            self.add_to_history(f"{expression} = {result}")
            
        except Exception as e:
            self.current_input.set("Ошибка")
    
    def is_safe_expression(self, expression):
        safe_pattern = r'^[0-9+\-*/().\s//%]+$'
        return bool(re.match(safe_pattern, expression.replace("**", "")))
    
    def add_to_history(self, entry):
        self.history.append(entry)
        # Показываем только последние 3 записи, чтобы не загромождать
        if len(self.history) > 3:
            recent_history = "\n".join(self.history[-3:])
        else:
            recent_history = "\n".join(self.history)
        self.history_label.config(text=recent_history)
    
    def show_history(self):
        if not self.history:
            messagebox.showinfo("История вычислений", "История пуста")
            return
        
        history_window = tk.Toplevel(self.root)
        history_window.title("История вычислений")
        history_window.geometry("400x300")
        history_window.configure(bg=self.colors['bg'])
        
        text_area = scrolledtext.ScrolledText(history_window, wrap=tk.WORD, width=50, height=15,
                                             bg=self.colors['display_bg'], fg=self.colors['text'])
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        history_text = "\n".join([f"{i+1}. {entry}" for i, entry in enumerate(self.history)])
        text_area.insert(tk.INSERT, history_text)
        text_area.config(state=tk.DISABLED)
        
        clear_btn = tk.Button(history_window, text="Очистить историю",
                            bg=self.colors['special_bg'], fg=self.colors['text'],
                            command=lambda: self.clear_history(history_window))
        clear_btn.pack(pady=5)
    
    def clear_history(self, window):
        self.history.clear()
        self.history_label.config(text="")
        window.destroy()
        messagebox.showinfo("История", "История очищена")
    
    def show_help(self):
        help_text = """
РАСШИРЕННЫЙ КАЛЬКУЛЯТОР - ПОЛНАЯ СПРАВКА

🔢 ОСНОВНЫЕ ОПЕРАЦИИ:
+   - сложение
-   - вычитание  
×   - умножение
÷   - деление
=   - вычисление результата

🧮 НАУЧНЫЕ ФУНКЦИИ:
sin, cos, tan - тригонометрические функции (в градусах или радианах)
log - логарифм
ln  - натуральный логарифм
√   - квадратный корень
x²  - возведение в квадрат
x^y - возведение в степень
n!  - факториал числа
1/x - обратное число
|x| - модуль числа

📐 ТОЧНЫЕ ТРИГОНОМЕТРИЧЕСКИЕ ЗНАЧЕНИЯ:
Для стандартных углов (0°,30°,45°,60°,90°,120°,135°,150°,180°)

🔢 ДРОБИ:
a/b  - ввод дроби (например: 1/2 + 1/3)
→dec - преобразовать дробь в десятичное число
→frac - преобразовать десятичное число в дробь

🎯 ОПЕРАЦИИ С ЦЕЛЫМИ ЧИСЛАМИ:
div - целочисленное деление (7 div 2 = 3)
mod - остаток от деления (7 mod 2 = 1)

💾 ПАМЯТЬ:
MC  - очистить память
MR  - восстановить из памяти  
M+  - добавить текущее число к памяти
M-  - вычесть текущее число из памяти
MS  - сохранить текущее число в память

⚡ СПЕЦИАЛЬНЫЕ ВОЗМОЖНОСТИ:
DEG/RAD   - переключение между градусами и радианами
Точные значения - переключение между точными и десятичными значениями
π         - число Пи (3.14159...)
e         - число Эйлера (2.71828...)
Случ.     - случайное число от 0 до 1
±         - смена знака числа
⌫         - удаление последнего символа
C         - очистка текущего ввода
CE        - полная очистка (ввод + история)

📝 СИСТЕМНЫЕ:
История - просмотр всех вычислений
Справка - окно помощи

💡 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:

Тригонометрия с точными значениями:
30 sin → 1/2 (в режиме DEG)
45 cos → √2/2
60 tan → √3

Работа с дробями:
1/2 + 1/3 = 5/6
2/3 × 3/4 = 1/2

Целочисленные операции:
7 div 2 = 3
7 mod 2 = 1

Проценты:
25% от 200 = 50 (введите: 25%200 =)
150 + 10% от 150 = 165 (введите: 150 + 10%150 =)

Память:
100 MS (сохранить)
50 M+ (добавить)
MR (вызвать) → 150
        """
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Подробная справка")
        help_window.geometry("550x650")
        help_window.configure(bg=self.colors['bg'])
        
        text_area = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, width=70, height=35,
                                             bg=self.colors['display_bg'], fg=self.colors['text'])
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        text_area.insert(tk.INSERT, help_text)
        text_area.config(state=tk.DISABLED)

def main():
    root = tk.Tk()
    app = AdvancedCalculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()