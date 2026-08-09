import tkinter as tk
from tkinter import colorchooser
import json
import sys
import os

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор")
        self.root.geometry("380x550")
        self.root.resizable(False, False)
        self.root.configure(bg='#2C3E50')
        
        # Настройки по умолчанию
        self.settings = {
            'bg_color': '#2C3E50',
            'display_bg': '#1A252F',
            'btn_bg': '#34495E',
            'btn_fg': '#ECF0F1',
            'display_fg': '#ECF0F1',
            'operator_bg': '#E67E22',
            'operator_fg': '#FFFFFF',
            'equals_bg': '#27AE60',
            'clear_bg': '#E74C3C'
        }
        
        self.load_settings()
        self.current_input = tk.StringVar()
        self.button_widgets = {}
        self.create_widgets()
        self.create_menu()
        
    def load_settings(self):
        try:
            # Ищем файл настроек рядом с программой
            settings_path = os.path.join(os.path.dirname(sys.executable), 'calculator_settings.json')
            if not os.path.exists(settings_path):
                settings_path = 'calculator_settings.json'
            
            with open(settings_path, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                self.settings.update(saved)
        except:
            pass
            
    def save_settings(self):
        try:
            settings_path = os.path.join(os.path.dirname(sys.executable), 'calculator_settings.json')
            if not os.path.exists(os.path.dirname(sys.executable)):
                settings_path = 'calculator_settings.json'
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except:
            pass
    
    def create_widgets(self):
        # Дисплей
        self.display = tk.Entry(
            self.root,
            textvariable=self.current_input,
            font=('Segoe UI', 20),
            bg=self.settings['display_bg'],
            fg=self.settings['display_fg'],
            justify='right',
            bd=0,
            relief='flat',
            insertbackground='white'
        )
        self.display.place(x=15, y=15, width=350, height=70)
        
        # Фрейм для кнопок
        button_frame = tk.Frame(self.root, bg=self.settings['bg_color'])
        button_frame.place(x=15, y=100, width=350, height=435)
        
        # Раскладка кнопок
        buttons = [
            ('C', 0, 0, 2), ('⌫', 0, 2, 1), ('%', 0, 3, 1),
            ('7', 1, 0, 1), ('8', 1, 1, 1), ('9', 1, 2, 1), ('/', 1, 3, 1),
            ('4', 2, 0, 1), ('5', 2, 1, 1), ('6', 2, 2, 1), ('*', 2, 3, 1),
            ('1', 3, 0, 1), ('2', 3, 1, 1), ('3', 3, 2, 1), ('-', 3, 3, 1),
            ('±', 4, 0, 1), ('0', 4, 1, 1), ('.', 4, 2, 1), ('+', 4, 3, 1),
            ('=', 5, 0, 4)
        ]
        
        for (text, row, col, colspan) in buttons:
            if text in ['C', '⌫']:
                bg = self.settings['clear_bg']
                fg = '#FFFFFF'
            elif text in ['/', '*', '-', '+', '%']:
                bg = self.settings['operator_bg']
                fg = self.settings['operator_fg']
            elif text == '=':
                bg = self.settings['equals_bg']
                fg = '#FFFFFF'
            else:
                bg = self.settings['btn_bg']
                fg = self.settings['btn_fg']
            
            btn = tk.Button(
                button_frame,
                text=text,
                font=('Segoe UI', 12, 'bold'),
                bg=bg,
                fg=fg,
                activebackground=bg,
                activeforeground=fg,
                bd=0,
                relief='flat',
                cursor='hand2',
                command=lambda t=text: self.click(t)
            )
            btn.place(
                x=col*88 + col*2,
                y=row*72 + row*2,
                width=86*colspan + (colspan-1)*2,
                height=70
            )
            
            self.button_widgets[text] = btn
    
    def create_menu(self):
        menubar = tk.Menu(self.root, font=('Segoe UI', 9))
        
        # Меню настроек
        settings_menu = tk.Menu(menubar, tearoff=0, font=('Segoe UI', 9))
        settings_menu.add_command(label="🎨 Цвет фона", command=lambda: self.change_color('bg_color'))
        settings_menu.add_command(label="📺 Цвет дисплея", command=lambda: self.change_color('display_bg'))
        settings_menu.add_command(label="⌨️ Цвет кнопок", command=lambda: self.change_color('btn_bg'))
        settings_menu.add_command(label="🔤 Цвет текста кнопок", command=lambda: self.change_color('btn_fg'))
        settings_menu.add_command(label="📝 Цвет текста дисплея", command=lambda: self.change_color('display_fg'))
        settings_menu.add_separator()
        settings_menu.add_command(label="➕✖️ Цвет кнопок операций", command=lambda: self.change_color('operator_bg'))
        settings_menu.add_command(label="✅ Цвет кнопки '='", command=lambda: self.change_color('equals_bg'))
        settings_menu.add_command(label="🗑️ Цвет кнопки очистки", command=lambda: self.change_color('clear_bg'))
        settings_menu.add_separator()
        settings_menu.add_command(label="🔄 Сбросить все цвета", command=self.reset_colors)
        
        menubar.add_cascade(label="🎨 Настройки", menu=settings_menu)
        
        # Меню помощи
        help_menu = tk.Menu(menubar, tearoff=0, font=('Segoe UI', 9))
        help_menu.add_command(label="О калькуляторе", command=self.show_about)
        menubar.add_cascade(label="❓ Помощь", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def change_color(self, setting_key):
        color = colorchooser.askcolor(
            title="Выберите цвет",
            parent=self.root
        )
        if color and color[1]:
            self.settings[setting_key] = color[1]
            self.save_settings()
            self.refresh_ui()
    
    def reset_colors(self):
        self.settings = {
            'bg_color': '#2C3E50',
            'display_bg': '#1A252F',
            'btn_bg': '#34495E',
            'btn_fg': '#ECF0F1',
            'display_fg': '#ECF0F1',
            'operator_bg': '#E67E22',
            'operator_fg': '#FFFFFF',
            'equals_bg': '#27AE60',
            'clear_bg': '#E74C3C'
        }
        self.save_settings()
        self.refresh_ui()
    
    def refresh_ui(self):
        self.root.configure(bg=self.settings['bg_color'])
        self.display.configure(bg=self.settings['display_bg'], fg=self.settings['display_fg'])
        
        for text, btn in self.button_widgets.items():
            if text in ['C', '⌫']:
                btn.configure(bg=self.settings['clear_bg'], fg='#FFFFFF')
            elif text in ['/', '*', '-', '+', '%']:
                btn.configure(bg=self.settings['operator_bg'], fg=self.settings['operator_fg'])
            elif text == '=':
                btn.configure(bg=self.settings['equals_bg'], fg='#FFFFFF')
            else:
                btn.configure(bg=self.settings['btn_bg'], fg=self.settings['btn_fg'])
    
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("О калькуляторе")
        about_window.geometry("300x150")
        about_window.resizable(False, False)
        about_window.configure(bg=self.settings['bg_color'])
        
        tk.Label(
            about_window,
            text="Калькулятор v2.0",
            font=('Segoe UI', 14, 'bold'),
            bg=self.settings['bg_color'],
            fg='white'
        ).pack(pady=20)
        
        tk.Label(
            about_window,
            text="Создан с ❤️ на Python\nВсе права защищены © 2024",
            font=('Segoe UI', 10),
            bg=self.settings['bg_color'],
            fg='lightgray'
        ).pack()
        
        tk.Button(
            about_window,
            text="OK",
            command=about_window.destroy,
            bg=self.settings['equals_bg'],
            fg='white',
            font=('Segoe UI', 10, 'bold'),
            cursor='hand2'
        ).pack(pady=10)
    
    def click(self, key):
        current = self.current_input.get()
        
        if key == 'C':
            self.current_input.set('')
        elif key == '⌫':
            self.current_input.set(current[:-1])
        elif key == '±':
            if current and current not in ['0', 'Ошибка']:
                if current[0] == '-':
                    self.current_input.set(current[1:])
                else:
                    self.current_input.set('-' + current)
        elif key == '%':
            try:
                result = float(current) / 100
                if result.is_integer():
                    result = int(result)
                self.current_input.set(str(result))
            except:
                self.show_error()
        elif key == '=':
            try:
                expression = current.replace('×', '*').replace('÷', '/')
                result = eval(expression)
                if isinstance(result, float):
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = round(result, 10)
                self.current_input.set(str(result))
            except:
                self.show_error()
        else:
            if current == 'Ошибка':
                self.current_input.set(key)
            elif len(current) < 15:  # Ограничение длины
                self.current_input.set(current + key)
    
    def show_error(self):
        self.current_input.set('Ошибка')
        self.root.after(1500, lambda: self.current_input.set(''))

def main():
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
