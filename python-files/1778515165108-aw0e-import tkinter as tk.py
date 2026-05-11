import tkinter as tk
import random

root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.geometry("120x120+500+300")

label = tk.Label(root, text="FOJŤAS", font=("Arial", 18), bg="yellow")
label.pack(expand=True, fill="both")

x = 500
y = 300

def move():
    global x, y

    x += random.randint(-20, 20)
    y += random.randint(-20, 20)

    root.geometry(f"120x120+{x}+{y}")

    root.after(300, move)

move()
root.mainloop()