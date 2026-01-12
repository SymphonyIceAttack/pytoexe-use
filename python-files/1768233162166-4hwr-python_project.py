import tkinter as tk
import random
import time
import threading
import winsound

def run_animation():
    winsound.MessageBeep()  # bum bum sound
    time.sleep(1)

    canvas.itemconfigure(head, state="normal")
    canvas.itemconfigure(eyes, state="normal")
    canvas.itemconfigure(mouth, state="normal")

    text.set("Taigi taigi")
    time.sleep(3)

    text.set("Noriu pasakyti, nesakysiu kazka,\nbet neerzink manes,\nas turiu problemu,\nnu blogu problemu")
    time.sleep(5)

    # Make him mad (angry eyes)
    canvas.itemconfigure(eyes, fill="red")

    # Random size
    scale = random.uniform(0.5, 1.5)
    canvas.scale("all", 150, 150, scale, scale)

root = tk.Tk()
root.title("Mad Stickman")
root.geometry("300x300")

canvas = tk.Canvas(root, width=300, height=300, bg="white")
canvas.pack()

# Stickman head
head = canvas.create_oval(100, 80, 200, 180, outline="black", width=3, state="hidden")
eyes = canvas.create_oval(125, 110, 135, 120, fill="black", state="hidden")
canvas.create_oval(165, 110, 175, 120, fill="black", state="hidden")
mouth = canvas.create_line(130, 155, 170, 145, width=3, state="hidden")  # angry mouth

text = tk.StringVar()
label = tk.Label(root, textvariable=text, font=("Arial", 10), wraplength=280)
label.pack()

threading.Thread(target=run_animation, daemon=True).start()

root.mainloop()
