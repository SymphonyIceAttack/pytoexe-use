import tkinter as tk
from tkinter import font as tkfont
# Импортируем Pillow для рисования иконки
try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class SimpleCalc:
    def __init__(self, root):
        self.root = root
        self.root.title("Wailtrum Simple")

        # Цвета
        self.bg = "#1e1e26"
        self.btn_bg = "#2b2b33"
        self.fg = "#ffffff"
        self.accent = "#c84bff"  # Яркий неоновый фиолетовый

        self.root.configure(bg=self.bg)

        # --- ДИСПЛЕЙ ---
        self.expression = ""
        self.display_var = tk.StringVar(value="0")

        display = tk.Label(
            root, textvariable=self.display_var,
            font=("Consolas", 32, "bold"),
            fg=self.accent, bg=self.btn_bg,
            anchor="e", padx=20, pady=10
        )
        display.pack(fill="x", padx=10, pady=(10, 5))

        # --- КНОПКИ ---
        buttons_frame = tk.Frame(root, bg=self.bg)
        buttons_frame.pack(padx=10, pady=5)

        btns = [
            ["C", "±", "%", "/"],
            ["7", "8", "9", "*"],
            ["4", "5", "6", "-"],
            ["1", "2", "3", "+"],
            ["0", ".", "=", "←"]
        ]

        for r, row in enumerate(btns):
            for c, char in enumerate(row):
                btn = tk.Button(
                    buttons_frame, text=char,
                    font=("Consolas", 20, "bold"),
                    bg=self.btn_bg, fg=self.fg,
                    activebackground=self.accent, activeforeground="#000",
                    bd=0, width=4, height=2,
                    command=lambda ch=char: self.on_button(ch)
                )
                btn.grid(row=r, column=c, padx=4, pady=4)

        # --- ИСТОРИЯ ---
        hist_lbl = tk.Label(root, text="История", fg="#888", bg=self.bg, font=("Arial", 10))
        hist_lbl.pack(anchor="w", padx=10)

        self.history_text = tk.Text(root, height=4, width=25,
                                    font=("Consolas", 10), bg="#25252e", fg="#aaa",
                                    bd=0, padx=5, pady=3)
        self.history_text.pack(anchor="w", padx=10)
        self.history_text.config(state=tk.DISABLED)

        self.history = []

        # Клавиатура
        root.bind("<Key>", self.on_key)
        root.bind("<Escape>", lambda e: root.destroy())

    def on_button(self, char):
        if char == "C":
            self.expression = ""
            self.display_var.set("0")
        elif char == "←":
            self.expression = self.expression[:-1]
            self.display_var.set(self.expression if self.expression else "0")
        elif char == "=":
            self.calculate()
        elif char == "±":
            if self.expression and self.expression != "0":
                if self.expression.startswith("-"):
                    self.expression = self.expression[1:]
                else:
                    self.expression = "-" + self.expression
                self.display_var.set(self.expression)
        else:
            if char in "0123456789.+-*/%":
                self.expression += char
                self.display_var.set(self.expression)

    def on_key(self, event):
        ch = event.char
        keysym = event.keysym
        if ch in "0123456789.+-*/%":
            self.on_button(ch)
        elif keysym == "Return":
            self.calculate()
        elif keysym == "BackSpace":
            self.on_button("←")

    def calculate(self):
        try:
            expr = self.expression.replace("%", "/100")
            result = str(eval(expr))
            if "." in result and result.endswith(".0"):
                result = result[:-2]
            self.add_history(f"{self.expression} = {result}")
            self.display_var.set(result)
            self.expression = result
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
    """Рисует фиолетовую иконку калькулятора в памяти"""
    size = 64
    # Создаем изображение: фиолетовый фон
    img = Image.new("RGBA", (size, size), (70, 20, 191, 255))  # Темно-фиолетовый
    draw = ImageDraw.Draw(img)

    # Рисуем рамку калькулятора (чуть светлее)
    border_color = (100, 30, 220)
    draw.rectangle([2, 2, size-2, size-2], outline=border_color, width=2)

    # Дисплей (серый прямоугольник сверху)
    display_y = 8
    display_h = 14
    draw.rectangle([6, display_y, size-6, display_y+display_h], fill=(40, 40, 50), outline=(60, 60, 70), width=1)

    # Кнопки (сетка 4x5 маленьких квадратиков)
    btn_size = 10
    start_x = 6
    start_y = display_y + display_h + 4
    gap = 2
    
    for r in range(5):
        for c in range(4):
            x = start_x + c * (btn_size + gap)
            y = start_y + r * (btn_size + gap)
            # Цвет кнопок: темно-серый с легкой фиолетовой обводкой
            draw.rectangle([x, y, x+btn_size, y+btn_size], fill=(50, 50, 60), outline=(150, 100, 200), width=1)

    return img

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = SimpleCalc(root)

        # --- ЛОГИКА ИКОНКИ ---
        if PIL_AVAILABLE:
            try:
                # 1. Рисуем иконку
                icon_pil = create_icon_image()
                # 2. Конвертируем в формат, понятный Tkinter
                icon_tk = ImageTk.PhotoImage(icon_pil)
                # 3. Устанавливаем как иконку окна
                root.iconphoto(False, icon_tk)
                
                # Важно: сохраняем ссылку на иконку, иначе сборщик мусора её удалит и иконка пропадёт
                app.icon_reference = icon_tk
            except Exception as e:
                print(f"Не удалось установить иконку: {e}")
        else:
            print("Библиотека Pillow не найдена. Иконка не будет установлена.")
            print("Установите её командой: pip install pillow")

        root.mainloop()
    except Exception as e:
        print("Критическая ошибка:", e)
