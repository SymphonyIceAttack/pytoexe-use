import tkinter as tk
import random

# Window setup
root = tk.Tk()
root.attributes("-fullscreen", True)
root.attributes("-topmost", True)
root.overrideredirect(True)
root.configure(bg="black")

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()

butterflies = []

NUM = 10

for _ in range(NUM):
    label = tk.Label(
        root,
        text="🦋",
        font=("Segoe UI Emoji", random.randint(40, 80)),
        bg="black"
    )
    x = random.randint(0, sw)
    y = random.randint(0, sh)
    dx = random.choice([-5, -4, 4, 5])
    dy = random.choice([-5, -3, 3, 5])

    label.place(x=x, y=y)

    butterflies.append({
        "label": label,
        "x": x,
        "y": y,
        "dx": dx,
        "dy": dy
    })

def animate():
    for b in butterflies:
        b["x"] += b["dx"]
        b["y"] += b["dy"]

        if b["x"] <= 0 or b["x"] >= sw - 80:
            b["dx"] *= -1
        if b["y"] <= 0 or b["y"] >= sh - 80:
            b["dy"] *= -1

        b["label"].place(x=b["x"], y=b["y"])

    root.after(30, animate)

animate()
root.mainloop()
