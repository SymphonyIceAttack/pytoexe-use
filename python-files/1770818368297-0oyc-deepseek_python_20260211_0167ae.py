import tkinter as tk
import random

W, H = None, None
root = tk.Tk()
W, H = root.winfo_screenwidth(), root.winfo_screenheight()

root.attributes("-fullscreen", True)
root.configure(bg="#1073c2")
root.overrideredirect(True)

canvas = tk.Canvas(root, width=W, height=H, highlightthickness=0, bg="#1073c2")
canvas.pack()

def bsod():
    canvas.delete("all")
    canvas.create_text(W//2, H//2 - 150, text=":(", fill="white", font=("Arial", 120))
    canvas.create_text(W//2, H//2, text="У ВАШЕЙ СИСТЕМЫ ВОЗНИКЛА ПРОБЛЕМА", 
                      fill="white", font=("Arial", 28, "bold"))
    canvas.create_text(W//2, H//2 + 60, text="ТЕБЯ ЗАМЕТИЛИ. ОН В СИСТЕМЕ.", 
                      fill="red", font=("Arial", 32, "bold"))
    canvas.create_text(W//2, H//2 + 150, text="КОД: REAPER_0xDEADBEEF", 
                      fill="white", font=("Consolas", 20))
    canvas.create_text(W//2, H - 100, text="ТОЛЬКО ПЕРЕЗАГРУЗКА", 
                      fill="white", font=("Arial", 26, "bold"))
    root.after(100, bsod)

bsod()
root.mainloop()