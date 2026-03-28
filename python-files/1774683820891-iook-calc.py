import tkinter as tk
from tkinter import font as tkfont

class Windows11Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Калькулятор Wicr 1.1")
        self.root.geometry("360x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#1c1c1c')

        # Шрифты
        self.display_font = tkfont.Font(family="Segoe UI", size=24, weight="bold")
        self.button_font = tkfont.Font(family="Segoe UI", size=14)

        # Переменные
        self.current = "0"
        self.previous = ""
        self.operator = ""
        self.new_number = True

        self.create_widgets()

    def create_widgets(self):
        # Дисплей
        self.display_frame = tk.Frame(self.root, bg='#1c1c1c', padx=10, pady=10)
        self.display_frame.pack(fill=tk.X)

        self.display = tk.Label(
            self.display_frame,
            text=self.current,
            font=self.display_font,
            bg='#1c1c1c',
            fg='white',
            anchor='e'
        )
        self.display.pack(fill=tk.X)

        # Кнопки
        self.buttons_frame = tk.Frame(self.root, bg='#1c1c1c')
        self.buttons_frame.pack(pady=10)

        # Расположение кнопок (как в Windows 11)
        buttons = [
            ['C', '±', '%', '÷'],
            ['7', '8', '9', '×'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '', '.', '=']
        ]

        colors = {
            'C': '#a5a5a5', '±': '#a5a5a5', '%': '#a5a5a5',
            '÷': '#f99100', '×': '#f99100', '-': '#f99100',
            '+': '#f99100', '=': '#f99100'
        }

        for i, row in enumerate(buttons):
            for j, text in enumerate(row):
                if text == '':  # Пустая ячейка для растяжения нуля
                    continue

                # Настройка ширины для кнопки 0
                width = 8 if text == '0' else 4
                if text == '0':
                    btn = tk.Button(
                        self.buttons_frame,
                        text=text,
                        font=self.button_font,
                        bg=colors.get(text, '#303030'),
                        fg='white',
                        border=0,
                        width=17,  # Растягиваем на 2 колонки
                        height=2,
                        command=lambda t=text: self.button_click(t)
                    )
                    btn.grid(row=i, column=j, columnspan=2, padx=5, pady=5)
                else:
                    bg_color = colors.get(text, '#303030')
                    btn = tk.Button(
                        self.buttons_frame,
                        text=text.replace('÷', '/').replace('×', '*'),
                        font=self.button_font,
                        bg=bg_color,
                        fg='white',
                        border=0,
                        width=width,
                        height=2,
                        command=lambda t=text: self.button_click(t)
                    )
                    btn.grid(row=i, column=j, padx=5, pady=5)

    def button_click(self, value):
        if value.isdigit():
            if self.new_number:
                self.current = value
                self.new_number = False
            else:
                if self.current == "0":
                    self.current = value
                else:
                    self.current += value
        elif value == '.':
            if '.' not in self.current:
                self.current += '.'
        elif value in ['+', '-', '*', '/']:
            self.previous = self.current
            self.operator = value.replace('×', '*').replace('÷', '/')
            self.new_number = True
        elif value == '=':
            if self.operator and self.previous:
                try:
                    result = eval(f"{self.previous} {self.operator} {self.current}")
                    self.current = str(result)
                    self.previous = ""
                    self.operator = ""
                    self.new_number = True
                except:
                    self.current = "Ошибка"
                    self.new_number = True
        elif value == 'C':
            self.current = "0"
            self.previous = ""
            self.operator = ""
            self.new_number = True
        elif value == '±':
            if self.current != "0":
                if self.current.startswith('-'):
                    self.current = self.current[1:]
                else:
                    self.current = '-' + self.current
        elif value == '%':
            try:
                self.current = str(float(self.current) / 100)
            except:
                self.current = "Ошибка"

        self.update_display()

    def update_display(self):
        # Ограничиваем длину текста на дисплее
        if len(self.current) > 12:
            try:
                num = float(self.current)
                self.display.config(text=f"{num:.8g}")
            except:
                self.display.config(text=self.current[:12])
        else:
            self.display.config(text=self.current)


def main():
    root = tk.Tk()
    app = Windows11Calculator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
