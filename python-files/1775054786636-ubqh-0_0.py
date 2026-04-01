import winsound
import time
import tkinter as tk

window = tk.Tk()
img = tk.PhotoImage(file="картинка.png")
tk.Label(window, image=img).pack()
window.mainloop()

while True:
    time.sleep(0)
    winsound.PlaySound("ah.wav", winsound.SND_FILENAME)
