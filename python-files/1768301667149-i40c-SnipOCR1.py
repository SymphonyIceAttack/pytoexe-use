import tkinter as tk
from PIL import ImageGrab
import time
import os
import webbrowser
from datetime import datetime
import threading

class SnippingTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.start_x = self.start_y = self.end_x = self.end_y = 0
        self.rect = None

    def start(self):
        self.root.deiconify()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-alpha", 0.3)
        self.canvas = tk.Canvas(self.root, cursor="cross")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.root.mainloop()

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline="red", width=2
        )

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.root.destroy()
        self.capture()

    def capture(self):
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)

        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        filename = f"Screenshot_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
        img.save(filename, "JPEG")

        os.startfile(filename)

        answer = tk.messagebox.askyesno(
            "OCR",
            "هل تريد تحويل الصورة إلى نص؟"
        )

        if answer:
            webbrowser.open("https://ocr.best/")


def listen_printscreen():
    while True:
        time.sleep(0.2)

def start_snip():
    tool = SnippingTool()
    tool.start()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    root.bind("<Print>", lambda e: threading.Thread(target=start_snip).start())
    root.mainloop()
