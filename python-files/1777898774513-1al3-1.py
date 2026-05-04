import ctypes
import time
import threading
import tkinter as tk
from PIL import Image, ImageTk

user32 = ctypes.WinDLL("user32", use_last_error=True)
last_screen_on = True
IMAGE_FILE = "popup.jpg"
SHOW_MS = 5000

def show_image():
    root = tk.Tk()
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.configure(bg="black")

    try:
        img = Image.open(IMAGE_FILE)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        ratio = min(sw / img.width, sh / img.height)
        img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(root, image=photo, bg="black")
        label.image = photo
        label.place(relx=0.5, rely=0.5, anchor="center")
    except:
        label = tk.Label(root, text="请放入图片：popup.jpg", fg="white", bg="black", font=("微软雅黑", 24))
        label.pack(expand=True)

    root.after(SHOW_MS, root.destroy)
    root.mainloop()

def monitor():
    global last_screen_on
    while True:
        hdc = user32.GetDC(0)
        now_on = hdc != 0
        user32.ReleaseDC(0, hdc)

        if not last_screen_on and now_on:
            threading.Thread(target=show_image, daemon=True).start()

        last_screen_on = now_on
        time.sleep(0.5)

if __name__ == "__main__":
    monitor()