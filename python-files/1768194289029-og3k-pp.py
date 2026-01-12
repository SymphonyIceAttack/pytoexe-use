import tkinter as tk
import threading
import time

def fuck_you_popup():
    while True:
        window = tk.Tk()
        window.title("惊喜大礼包")
        label = tk.Label(window, text="烦死你", font=("Arial", 24))
        label.pack(padx=50, pady=50)
        # 他妈的这个窗口关不掉才刺激
        window.attributes('-topmost', True)
        window.mainloop()

# 开十个线程同时弹窗，爽翻天
for i in range(10):
    threading.Thread(target=fuck_you_popup).start()
