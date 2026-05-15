import tkinter as tk
import random

# ---------- НАСТРОЙКИ ----------
PHRASE = "alevtina lox "
FONT_FAMILY = "Consolas"
TARGET_FONT_SIZE = 14              # конечный размер букв
X_STEP = 0.055                     # увеличенный шаг → меньше букв
Y_STEP = 0.075                     # увеличенный шаг → меньше строк
SCALE = TARGET_FONT_SIZE / Y_STEP

WIDTH, HEIGHT = 800, 600
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Анимация
ADD_INTERVAL = 10     # чуть медленнее добавляем
BATCH_SIZE = 6         # меньше букв за раз
FRAME_TIME = 25        # реже кадры роста
GROW_STEP = 1.2        # плавный, но не слишком частый рост
START_SIZE = 1

BG_COLOR = "white"
START_COLOR = "#ffffff"
END_COLOR = "#ff0000"
OUTLINE_COLOR = "black"
OUTLINE_EXTRA = 2      # на сколько пунктов обводка крупнее основного текста
# --------------------------------

def inside_heart(x, y):
    return (x**2 + y**2 - 1)**3 - x**2 * y**3 <= 0

class AnimatedChar:
    """Одна буква с обводкой (2 объекта: тень + основной)."""
    def __init__(self, canvas, char, x, y, target_size):
        self.canvas = canvas
        self.char = char
        self.x = x
        self.y = y
        self.target_size = target_size
        self.current_size = START_SIZE

        # Тень (обводка) — чуть больше и всегда чёрная
        self.outline_id = canvas.create_text(
            x, y,
            text=char,
            font=(FONT_FAMILY, START_SIZE + OUTLINE_EXTRA),
            fill=OUTLINE_COLOR,
            anchor="center"
        )
        # Основной текст
        self.main_id = canvas.create_text(
            x, y,
            text=char,
            font=(FONT_FAMILY, START_SIZE),
            fill=START_COLOR,
            anchor="center"
        )
        # Убедимся, что тень ниже основного текста
        canvas.tag_lower(self.outline_id, self.main_id)
        self.done = False

    def update(self):
        if self.done:
            return False
        self.current_size += GROW_STEP
        if self.current_size >= self.target_size:
            self.current_size = self.target_size
            self.done = True

        if self.target_size > START_SIZE:
            p = (self.current_size - START_SIZE) / (self.target_size - START_SIZE)
        else:
            p = 1.0
        p = max(0.0, min(1.0, p))

        # Цвет заливки
        r = 255
        g = b = int(255 * (1 - p))
        fill_color = f"#{r:02x}{g:02x}{b:02x}"

        # Обновляем тень: её размер всегда current_size + OUTLINE_EXTRA
        outline_size = int(self.current_size + OUTLINE_EXTRA)
        self.canvas.itemconfig(self.outline_id, font=(FONT_FAMILY, outline_size))

        # Основной текст
        self.canvas.itemconfig(self.main_id, font=(FONT_FAMILY, int(self.current_size)), fill=fill_color)
        return not self.done

class HeartApp:
    def __init__(self, root):
        self.root = root
        self.root.title("")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG_COLOR)
        self.canvas.pack()
        self.chars = self.generate_chars()
        random.shuffle(self.chars)
        self.next_idx = 0
        self.active = []
        self.start_animation()

    def generate_chars(self):
        chars = []
        idx = 0
        y = 1.2
        while y >= -1.2:
            x = -1.5
            while x <= 1.5:
                if inside_heart(x, y):
                    char = PHRASE[idx % len(PHRASE)]
                    px = CENTER_X + x * SCALE
                    py = CENTER_Y - y * SCALE
                    chars.append({"char": char, "x": px, "y": py})
                    idx += 1
                x += X_STEP
            y -= Y_STEP
        return chars

    def start_animation(self):
        self.add_batch()
        self.animate()

    def add_batch(self):
        for _ in range(BATCH_SIZE):
            if self.next_idx >= len(self.chars):
                break
            item = self.chars[self.next_idx]
            ac = AnimatedChar(self.canvas, item["char"], item["x"], item["y"], TARGET_FONT_SIZE)
            self.active.append(ac)
            self.next_idx += 1
        if self.next_idx < len(self.chars):
            self.root.after(ADD_INTERVAL, self.add_batch)

    def animate(self):
        self.active = [ac for ac in self.active if ac.update()]
        if self.active or self.next_idx < len(self.chars):
            self.root.after(FRAME_TIME, self.animate)
        else:
            self.canvas.create_text(
                CENTER_X, HEIGHT - 30,
                text=")))))))",
                font=("Arial", 16, "bold"),
                fill=END_COLOR,
                anchor="s"
            )

if __name__ == "__main__":
    root = tk.Tk()
    app = HeartApp(root)
    root.mainloop()