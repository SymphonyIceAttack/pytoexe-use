import tkinter as tk
from time import strftime

root = tk.Tk()
root.title("置顶大时钟")
root.geometry("800x350")
root.configure(bg="black")
root.wm_attributes("-topmost", 1)
root.wm_attributes("-alpha", 0.9)
root.resizable(False, False)

def drag_start(event):
    root.x = event.x
    root.y = event.y

def drag_motion(event):
    x = root.winfo_x() - root.x + event.x
    y = root.winfo_y() - root.y + event.y
    root.geometry(f"+{x}+{y}")

root.bind("<Button-1>", drag_start)
root.bind("<B1-Motion>", drag_motion)

label = tk.Label(root, font=("DS-Digital", 140, "bold"), background="black", foreground="cyan")
label.pack(expand=True)

def time():
    t = strftime("%H:%M:%S")
    label.config(text=t)
    label.after(1000, time)

time()
root.mainloop()