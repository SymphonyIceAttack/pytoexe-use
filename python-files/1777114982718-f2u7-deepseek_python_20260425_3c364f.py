import tkinter as tk
import random
from PIL import Image, ImageTk
import requests
from io import BytesIO

# ЗАМЕНИТЕ ЭТИ ССЫЛКИ НА ПРЯМЫЕ URL (ПРОВЕРЬТЕ В БРАУЗЕРЕ)
BACKGROUND_URL = "https://i.pinimg.com/736x/4c/ae/cf/4caecf9a70cbea9df3db1216fe664260.jpg"  # ФОН
TARAKAN_URL = "https://i.ibb.co/fYDBsfYW/vecteezy-cockroach-handdrawn-watercolor-style-illustration-15100252.png"  # СТРАНИЦА, НЕ ПРЯМАЯ ССЫЛКА! ЗАМЕНИТЕ!

class Tarakan:
    def __init__(self, canvas, x, y, img):
        self.canvas = canvas
        self.id = canvas.create_image(x, y, image=img, anchor='center')
        self.dx = random.choice([-3, -2, 2, 3])
        self.dy = random.choice([-2, -1, 1, 2])

    def move(self, w, h):
        x, y = self.canvas.coords(self.id)
        if x <= 0 or x >= w: self.dx = -self.dx
        if y <= 0 or y >= h: self.dy = -self.dy
        self.canvas.move(self.id, self.dx, self.dy)

def animate():
    for t in tarakans:
        t.move(canvas.winfo_width(), canvas.winfo_height())
    root.after(30, animate)

def load_image(url, size=None):
    resp = requests.get(url)
    img = Image.open(BytesIO(resp.content))
    if size:
        img = img.resize(size, Image.Resampling.LANCZOS)
    return ImageTk.PhotoImage(img)

# Окно
root = tk.Tk()
root.attributes("-fullscreen", True)

# Фон
try:
    bg_img = load_image(BACKGROUND_URL)
    canvas = tk.Canvas(root, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)
    canvas.create_image(0, 0, image=bg_img, anchor='nw')
    # Привязываем изображение, чтобы оно не удалилось сборщиком мусора
    canvas.bg_img = bg_img
except:
    # Если фон не загрузился, просто чёрный холст
    canvas = tk.Canvas(root, bg='black', highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

# Надпись
label = tk.Label(root, text="WINDOWS ЗАБЛОКИРОВАН прекрасным великолепным красивым и неповторимым Muravejchik'ом",
                 font=("Arial", 28, "bold"), fg="red", bg='black')
label.place(relx=0.5, rely=0.5, anchor="center")

# Кнопка выхода
btn = tk.Button(root, text="Выход", command=root.destroy, width=6, height=1)
btn.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

# Загрузка картинки таракана (прямая ссылка!)
try:
    bug_img = load_image(TARAKAN_URL, size=(60,60))
except:
    bug_img = None

# Создаём 15 тараканов
tarakans = []
for _ in range(15):
    x = random.randint(50, root.winfo_screenwidth() - 50)
    y = random.randint(50, root.winfo_screenheight() - 50)
    if bug_img:
        tarakans.append(Tarakan(canvas, x, y, bug_img))
    else:
        # Круг-заглушка, если картинка не загрузилась
        circ = canvas.create_oval(x-15, y-15, x+15, y+15, fill='#5D3A1A', outline='#3A2410')
        tarakans.append(Tarakan(canvas, x, y, circ))

animate()
root.mainloop()
