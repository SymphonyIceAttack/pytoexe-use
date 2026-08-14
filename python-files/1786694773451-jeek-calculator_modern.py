"""
Современный калькулятор с красивым UI
Использует tkinter с кастомными виджетами и анимациями
"""

import tkinter as tk
from tkinter import font as tkfont
import math

class ModernButton(tk.Canvas):
    """Современная кнопка с закруглёнными углами и эффектами"""
    
    def __init__(self, parent, text, command, bg_color='#2d2d44', 
                 fg_color='#ffffff', hover_color='#3d3d5c', 
                 width=80, height=80, font_size=24, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=parent.cget('bg'), **kwargs)
        
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.width = width
        self.height = height
        self.font_size = font_size
        self.is_hovered = False
        self.is_pressed = False
        
        self.draw_button()
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
        
    def draw_button(self):
        self.delete('all')
        
        # Цвет кнопки
        if self.is_pressed:
            color = self.hover_color
            offset = 2
        elif self.is_hovered:
            color = self.hover_color
            offset = 0
        else:
            color = self.bg_color
            offset = 0
        
        # Закруглённый прямоугольник
        radius = 15
        x1, y1 = 5, 5
        x2, y2 = self.width - 5, self.height - 5
        
        # Рисуем скруглённый прямоугольник
        self.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius, 
                       start=90, extent=90, fill=color, outline='')
        self.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius, 
                       start=0, extent=90, fill=color, outline='')
        self.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2, 
                       start=180, extent=90, fill=color, outline='')
        self.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2, 
                       start=270, extent=90, fill=color, outline='')
        
        self.create_rectangle(x1 + radius, y1, x2 - radius, y2, 
                             fill=color, outline='')
        self.create_rectangle(x1, y1 + radius, x2, y2 - radius, 
                             fill=color, outline='')
        
        # Тень (только если не нажата)
        if not self.is_pressed and not self.is_hovered:
            shadow_color = '#1a1a2e'
            for i in range(3, 0, -1):
                self.create_arc(x1+2, y1+i*2, x1+2*radius+2, y1+i*2+2*radius, 
                               start=90, extent=90, fill=shadow_color, outline='',
                               tags='shadow')
                self.create_arc(x2-2*radius+2, y1+i*2, x2+2, y1+i*2+2*radius, 
                               start=0, extent=90, fill=shadow_color, outline='',
                               tags='shadow')
                self.create_arc(x1+2, y2-i*2-2*radius, x1+2*radius+2, y2-i*2, 
                               start=180, extent=90, fill=shadow_color, outline='',
                               tags='shadow')
                self.create_arc(x2-2*radius+2, y2-i*2-2*radius, x2+2, y2-i*2, 
                               start=270, extent=90, fill=shadow_color, outline='',
                               tags='shadow')
                self.create_rectangle(x1+radius+2, y1+i*2, x2-radius+2, y2, 
                                     fill=shadow_color, outline='', tags='shadow')
                self.create_rectangle(x1+2, y1+i*2+radius, x2, y2-i*2-radius, 
                                     fill=shadow_color, outline='', tags='shadow')
            self.lower('shadow')
        
        # Текст по центру
        self.create_text(self.width // 2, self.height // 2 - offset, 
                        text=self.text, font=tkfont.Font(
                            family="Segoe UI", size=self.font_size, weight="bold"),
                        fill=self.fg_color)
    
    def on_enter(self, event):
        self.is_hovered = True
        self.draw_button()
        
    def on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.draw_button()
        
    def on_press(self, event):
        self.is_pressed = True
        self.draw_button()
        
    def on_release(self, event):
        if self.is_pressed:
            self.is_pressed = False
            self.draw_button()
            if self.command:
                self.command()


class ModernCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор")
        self.root.geometry("420x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#0f0f1a')
        
        # Центрирование окна
        self.center_window()
        
        self.expression = ""
        self.history = ""
        
        # Цветовая палитра
        self.colors = {
            'bg': '#0f0f1a',
            'display_bg': '#1a1a2e',
            'text_primary': '#ffffff',
            'text_secondary': '#8888aa',
            'btn_number': '#2d2d44',
            'btn_number_hover': '#3d3d5c',
            'btn_operator': '#ff6b6b',
            'btn_operator_hover': '#ff8585',
            'btn_function': '#4ecdc4',
            'btn_function_hover': '#6ee7df',
            'btn_equals': '#ffe66d',
            'btn_equals_hover': '#fff0a0',
            'btn_equals_fg': '#0f0f1a'
        }
        
        self.create_ui()
        
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')
        
    def create_ui(self):
        # Главный контейнер
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Дисплей
        self.create_display(main_frame)
        
        # Кнопки
        self.create_buttons(main_frame)
        
    def create_display(self, parent):
        # Фрейм дисплея
        display_frame = tk.Frame(parent, bg=self.colors['display_bg'])
        display_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Закругление углов дисплея через Canvas
        display_canvas = tk.Canvas(display_frame, height=150, 
                                   bg=self.colors['display_bg'],
                                   highlightthickness=0)
        display_canvas.pack(fill=tk.X, expand=True)
        
        # Рисуем скруглённый прямоугольник
        radius = 20
        x1, y1 = 0, 0
        x2, y2 = display_canvas.winfo_reqwidth() - 1, 149
        
        display_canvas.create_arc(x1, y1, x1 + 2*radius, y1 + 2*radius,
                                  start=90, extent=90, 
                                  fill=self.colors['display_bg'], outline='')
        display_canvas.create_arc(x2 - 2*radius, y1, x2, y1 + 2*radius,
                                  start=0, extent=90,
                                  fill=self.colors['display_bg'], outline='')
        display_canvas.create_arc(x1, y2 - 2*radius, x1 + 2*radius, y2,
                                  start=180, extent=90,
                                  fill=self.colors['display_bg'], outline='')
        display_canvas.create_arc(x2 - 2*radius, y2 - 2*radius, x2, y2,
                                  start=270, extent=90,
                                  fill=self.colors['display_bg'], outline='')
        display_canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2,
                                        fill=self.colors['display_bg'], outline='')
        display_canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius,
                                        fill=self.colors['display_bg'], outline='')
        
        # История вычислений
        self.history_label = tk.Label(
            display_frame,
            text="",
            font=tkfont.Font(family="Segoe UI", size=14),
            fg=self.colors['text_secondary'],
            bg=self.colors['display_bg'],
            anchor='e',
            padx=20,
            pady=(10, 0)
        )
        self.history_label.pack(fill=tk.X)
        
        # Основное отображение
        self.result_var = tk.StringVar()
        self.result_var.set("0")
        
        self.result_label = tk.Label(
            display_frame,
            textvariable=self.result_var,
            font=tkfont.Font(family="Segoe UI", size=48, weight="bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['display_bg'],
            anchor='e',
            padx=20,
            pady=(0, 20)
        )
        self.result_label.pack(fill=tk.X)
        
    def create_buttons(self, parent):
        # Фрейм для кнопок
        buttons_frame = tk.Frame(parent, bg=self.colors['bg'])
        buttons_frame.pack(fill=tk.BOTH, expand=True)
        
        # Конфигурация кнопок
        buttons_config = [
            [
                {'text': 'C', 'color': self.colors['btn_function'], 
                 'hover': self.colors['btn_function_hover'], 'command': self.clear},
                {'text': '±', 'color': self.colors['btn_function'],
                 'hover': self.colors['btn_function_hover'], 'command': self.toggle_sign},
                {'text': '%', 'color': self.colors['btn_function'],
                 'hover': self.colors['btn_function_hover'], 'command': self.percentage},
                {'text': '÷', 'color': self.colors['btn_operator'],
                 'hover': self.colors['btn_operator_hover'], 'command': lambda: self.operator('/')}
            ],
            [
                {'text': '7', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('7')},
                {'text': '8', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('8')},
                {'text': '9', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('9')},
                {'text': '×', 'color': self.colors['btn_operator'],
                 'hover': self.colors['btn_operator_hover'], 'command': lambda: self.operator('*')}
            ],
            [
                {'text': '4', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('4')},
                {'text': '5', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('5')},
                {'text': '6', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('6')},
                {'text': '−', 'color': self.colors['btn_operator'],
                 'hover': self.colors['btn_operator_hover'], 'command': lambda: self.operator('-')}
            ],
            [
                {'text': '1', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('1')},
                {'text': '2', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('2')},
                {'text': '3', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('3')},
                {'text': '+', 'color': self.colors['btn_operator'],
                 'hover': self.colors['btn_operator_hover'], 'command': lambda: self.operator('+')}
            ],
            [
                {'text': '0', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('0')},
                {'text': '.', 'color': self.colors['btn_number'],
                 'hover': self.colors['btn_number_hover'], 'command': lambda: self.number('.')},
                {'text': '⌫', 'color': self.colors['btn_function'],
                 'hover': self.colors['btn_function_hover'], 'command': self.backspace},
                {'text': '=', 'color': self.colors['btn_equals'],
                 'hover': self.colors['btn_equals_hover'], 
                 'fg': self.colors['btn_equals_fg'], 'command': self.calculate}
            ]
        ]
        
        # Настройка сетки
        for i in range(5):
            buttons_frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            buttons_frame.grid_columnconfigure(i, weight=1)
        
        # Создание кнопок
        for row_idx, row in enumerate(buttons_config):
            for col_idx, btn_config in enumerate(row):
                btn = ModernButton(
                    buttons_frame,
                    text=btn_config['text'],
                    command=btn_config['command'],
                    bg_color=btn_config['color'],
                    fg_color=btn_config.get('fg', '#ffffff'),
                    hover_color=btn_config['hover'],
                    width=90,
                    height=90,
                    font_size=28
                )
                btn.grid(row=row_idx, column=col_idx, padx=8, pady=8)
    
    # Логика калькулятора
    def number(self, num):
        if num == '.' and '.' in self.expression.split('/')[-1].split('*')[-1].split('+')[-1].split('-')[-1]:
            return
        self.expression += str(num)
        self.result_var.set(self.expression)
        
    def operator(self, op):
        if self.expression and self.expression[-1] in '+-*/':
            self.expression = self.expression[:-1] + op
        elif self.expression:
            self.expression += op
        self.result_var.set(self.expression)
        
    def clear(self):
        self.expression = ""
        self.history = ""
        self.history_label.config(text="")
        self.result_var.set("0")
        
    def backspace(self):
        if self.expression:
            self.expression = self.expression[:-1]
            if not self.expression:
                self.result_var.set("0")
            else:
                self.result_var.set(self.expression)
                
    def toggle_sign(self):
        if self.expression:
            try:
                value = float(eval(self.expression))
                self.expression = str(-value)
                self.result_var.set(self.expression)
            except:
                pass
                
    def percentage(self):
        if self.expression:
            try:
                value = float(eval(self.expression))
                self.expression = str(value / 100)
                self.result_var.set(self.expression)
            except:
                pass
                
    def calculate(self):
        if not self.expression:
            return
        try:
            # Сохраняем историю
            self.history = self.expression + " ="
            self.history_label.config(text=self.history)
            
            # Вычисляем
            eval_expr = self.expression.replace('×', '*').replace('÷', '/')
            result = eval(eval_expr)
            
            # Округление
            if isinstance(result, float):
                result = round(result, 10)
                result = float(f'{result:g}')
            
            self.expression = str(result)
            self.result_var.set(self.expression)
        except Exception as e:
            self.result_var.set("Ошибка")
            self.expression = ""
            
    def run(self):
        self.root.mainloop()


def main():
    root = tk.Tk()
    
    # Установка иконки (если есть)
    try:
        root.iconbitmap('calculator.ico')
    except:
        pass
    
    calculator = ModernCalculator(root)
    calculator.run()


if __name__ == "__main__":
    main()
