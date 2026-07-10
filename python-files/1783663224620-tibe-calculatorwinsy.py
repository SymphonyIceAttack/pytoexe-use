import tkinter as tk
from tkinter import font as tkfont

# Импорт Pillow для иконки, если есть
try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class SimpleCalc:
    def __init__(self, root):
        self.root = root
        self.root.title("Wailtrum Simple")
        self.root.geometry("380x520")
        self.root.resizable(False, False)

        # Цветовая схема
        self.bg = "#1e1e26"
        self.btn_bg = "#2b2b33"
        self.fg = "#ffffff"
        self.accent = "#c84bff"
        self.btn_hover = "#5e5e7e"

        self.root.configure(bg=self.bg)

        # Шрифт
        self.font_display = ("Consolas", 24, "bold")
        self.font_buttons = ("Consolas", 16, "bold")

        # --- Дисплей ---
        self.expression = ""
        self.display_var = tk.StringVar(value="0")
        display = tk.Label(
            root, textvariable=self.display_var,
            font=self.font_display,
            fg=self.accent, bg=self.btn_bg,
            anchor="e", padx=20, pady=15
        )
        display.pack(fill="x", padx=10, pady=(10, 5))
        display.config(relief="ridge", bd=2, borderwidth=2)

        # --- Кнопки ---
        buttons_frame = tk.Frame(root, bg=self.bg)
        buttons_frame.pack(padx=10, pady=5)

        btns = [
            ["C", "±", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "=", "←"]
        ]

        # Создаем кнопки с плавным эффектом
        for r, row in enumerate(btns):
            for c, char in enumerate(row):
                btn = tk.Button(
                    buttons_frame, text=char,
                    font=self.font_buttons,
                    bg=self.btn_bg, fg=self.fg,
                    activebackground=self.btn_hover, activeforeground="#fff",
                    bd=0, width=5, height=2,
                    relief="raised",
                    command=lambda ch=char: self.on_button(ch)
                )
                btn.grid(row=r, column=c, padx=4, pady=4)
                # Эффект при наведении
                btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.btn_hover))
                btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.btn_bg))

        # --- История ---
        hist_lbl = tk.Label(root, text="История", fg="#888", bg=self.bg, font=("Arial", 10))
        hist_lbl.pack(anchor="w", padx=10)

        self.history_text = tk.Text(root, height=4, width=31,
                                    font=("Consolas", 10), bg="#25252e", fg="#aaa",
                                    bd=0, padx=5, pady=3)
        self.history_text.pack(anchor="w", padx=10)
        self.history_text.config(state=tk.DISABLED)

        self.history = []

        # Клавиши
        root.bind("<Key>", self.on_key)
        root.bind("<Escape>", lambda e: root.destroy())

    def on_button(self, ch):
        if ch == "C":
            self.expression = ""
            self.display_var.set("0")
        elif ch == "←":
            self.expression = self.expression[:-1]
            self.display_var.set(self.expression if self.expression else "0")
        elif ch == "=":
            self.calculate()
        elif ch == "±":
            if self.expression and self.expression != "0":
                if self.expression.startswith("-"):
                    self.expression = self.expression[1:]
                else:
                    self.expression = "-" + self.expression
                self.display_var.set(self.expression)
        else:
            if ch in "0123456789.+-*/%":
                self.expression += ch
                self.display_var.set(self.expression)

    def on_key(self, event):
        ch = event.char
        ks = event.keysym
        if ch in "0123456789.+-*/%":
            self.on_button(ch)
        elif ks == "Return":
            self.calculate()
        elif ks == "BackSpace":
            self.on_button("←")
        elif ks == "Escape":
            self.root.destroy()

    def calculate(self):
        try:
            # Обработка процента
            expr = self.expression.replace("%", "/100")
            result = eval(expr)
            result_str = str(result)
            if "." in result_str and result_str.endswith(".0"):
                result_str = result_str[:-2]
            self.add_history(f"{self.expression} = {result_str}")
            self.display_var.set(result_str)
            self.expression = result_str
        except Exception:
            self.display_var.set("Ошибка")
            self.expression = ""

    def add_history(self, entry):
        self.history.append(entry)
        if len(self.history) > 5:
            self.history.pop(0)
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        for line in self.history:
            self.history_text.insert(tk.END, line + "\n")
        self.history_text.config(state=tk.DISABLED)

def create_icon_image():
    """Рисует стильную иконку калькулятора"""
    size = 64
    img = Image.new("RGBA", (size, size), (70, 20, 191, 255))
    draw = ImageDraw.Draw(img)
    # рамка
    draw.rectangle([2, 2, size-2, size-2], outline=(100, 30, 220), width=2)
    # дисплей
    draw.rectangle([6, 8, size-6, 22], fill=(40, 40, 50), outline=(60, 60, 70))
    # кнопки
    btn_size = 12
    start_x = 6
    start_y = 26
    gap = 3
    for r in range(5):
        for c in range(4):
            x = start_x + c * (btn_size + gap)
            y = start_y + r * (btn_size + gap)
            draw.rectangle([x, y, x+btn_size, y+btn_size], fill=(50, 50, 60), outline=(150, 100, 200))
    return img

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleCalc(root)

    # Установка иконки
    if PIL_AVAILABLE:
        try:
            icon_img = create_icon_image()
            icon_tk = ImageTk.PhotoImage(icon_img)
            root.iconphoto(False, icon_tk)
            app.icon_ref = icon_tk  # удерживаем ссылку
        except Exception as e:
            print(f"Ошибка при установке иконки: {e}")

    root.mainloop()