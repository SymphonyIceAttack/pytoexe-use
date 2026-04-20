import tkinter as tk
import ctypes
import sys

def is_windows():
    return sys.platform.startswith("win")

root = tk.Tk()
root.title("定位线")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-alpha", 0.3)

sw = root.winfo_screenwidth()
sh = root.winfo_screenheight()

# 竖线
v_line = tk.Frame(root, bg="#ff0000", width=1)
v_line.place(x=sw//2, y=0, height=sh)

# 横线
h_line = tk.Frame(root, bg="#ff0000", height=1)
h_line.place(x=0, y=sh//2, width=sw)

# 鼠标穿透（Windows）
if is_windows():
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.SetWindowLongPtrW(hwnd, -20, 0x80000 | 0x20)

root.bind("<Escape>", lambda e: root.destroy())
root.mainloop()