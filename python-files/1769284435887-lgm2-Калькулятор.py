import tkinter as tk
from tkinter import messagebox

class ElegantCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Элегантный калькулятор")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # Переменные
        self.expression = ""
        self.entry_var = tk.StringVar()
        self.entry_var.set("0")

        self.create_widgets()

    def create_widgets(self):
        # --- Дисплей ---
        display_frame = tk.Frame(
            self.root,
            bg="#1a1a2e",
            highlightbackground="#4e4e6d",
            highlightthickness=1,
            bd=0
        )
        display_frame.place(x=20, y=30, width=360, height=80)

        self.display = tk.Label(
            display_frame,
            textvariable=self.entry_var,
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg="#1a1a2e",
            anchor="e",
            padx=10
        )
        self.display.pack(fill="both", expand=True)

        # --- Кнопки ---
        btn_frame = tk.Frame(self.root, bg="#f0f0f0")
        btn_frame.place(x=20, y=130, width=360, height=420)

        # Макет кнопок
        buttons = [
            ['C', '←', '√', '/'],
            ['7', '8', '9', '*'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['0', '.', '±', '=']
        ]

        for row_idx, row in enumerate(buttons):
            for col_idx, text in enumerate(row):
                btn = tk.Button(
                    btn_frame,
                    text=text,
                    font=("Segoe UI", 14),
                    relief="flat",
                    bd=0,
                    width=4,
                    height=2,
                    command=lambda t=text: self.on_button_click(t)
                )
                btn.grid(row=row_idx, column=col_idx, padx=5, pady=5, sticky="nsew")

                # Цветовая схема
                if text in '0123456789.':
                    btn.config(
                        bg="#ffffff", fg="#2c3e50",
                        activebackground="#e0e0e0",
                        activeforeground="#2c3e50"
                    )
                elif text in '+-*/√':
                    btn.config(
                        bg="#3498db", fg="white",
                        activebackground="#2980b9",
                        activeforeground="white"
                    )
                elif text == 'C':
                    btn.config(
                        bg="#e74c3c", fg="white",
                        activebackground="#c0392b",
                        activeforeground="white"
                    )
                elif text == '←':
                    btn.config(
                        bg="#95a5a6", fg="white",
                        activebackground="#7f8c8d",
                        activeforeground="white"
                    )
                elif text == '±':
                    btn.config(
                        bg="#9b59b6", fg="white",
                        activebackground="#8e44ad",
                        activeforeground="white"
                    )
                elif text == '=':
                    btn.config(
                        bg="#27ae60", fg="white",
                        activebackground="#219a52",
                        activeforeground="white",
                        font=("Segoe UI", 14, "bold")
                    )

            btn_frame.grid_rowconfigure(row_idx, weight=1)
            btn_frame.grid_columnconfigure(col_idx, weight=1)

    def on_button_click(self, char):
        if char == 'C':
            self.expression = ""
            self.entry_var.set("0")
        elif char == '←':
            self.expression = self.expression[:-1]
            self.update_display()
        elif char == '=':
            try:
                # Обработка корня
                expr = self.expression.replace('√', '**0.5')
                result = eval(expr)
                # Форматирование
                if isinstance(result, float):
                    if result.is_integer():
                        result = int(result)
                    else:
                        result = round(result, 8)  # Ограничиваем знаки после запятой
                self.expression = str(result)
                self.update_display(big=True)  # Крупный шрифт для результата
            except Exception:
                messagebox.showerror("Ошибка", "Некорректное выражение")
                self.expression = ""
                self.entry_var.set("Ошибка")
        elif char == '±':
            if self.expression and self.expression[-1].isdigit():
                # Меняем знак последнего числа
                import re
                parts = re.split(r'([+\-*/])', self.expression)
                last_num = parts[-1]
                if last_num.replace('.', '').isdigit():
                    new_num = str(-float(last_num))
                    self.expression = ''.join(parts[:-1]) + new_num
                    self.update_display()
        else:
            # Цифры и операции
            if char == '.' and '.' in self.get_last_number():
                return  # Только одна точка в числе
            self.expression += char
            self.update_display()

    def get_last_number(self):
        """Возвращает последнее число в выражении"""
        import re
        parts = re.findall(r'\d+\.?\d*', self.expression)
        return parts[-1] if parts else ""

    def update_display(self, big=False):
        text = self.expression if self.expression else "0"
        self.entry_var.set(text)
        # Изменение размера шрифта для результата
        if big:
            self.display.config(font=("Segoe UI", 24, "bold"))
        else:
            self.display.config(font=("Segoe UI", 20, "bold"))

# Запуск
if __name__ == "__main__":
    root = tk.Tk()
    app = ElegantCalculator(root)
    root.mainloop()
