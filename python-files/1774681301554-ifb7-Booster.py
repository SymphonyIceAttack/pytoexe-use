import tkinter as tk
from tkinter import messagebox

# 你的卡密
KEYS = {
    "plmoknijb/90",
    "uhvygctfx/90",
    "qazwsxedc/90",
    "poiuytrew/90",
    "lkjhgfdsa/90",
    "mnbvcxzlk/90",
    "iwhisjduc/90",
    "lxheouxis/90",
    "kdbjebych/90",
    "ishkebixb/90",
    "lsbixbieb/90"
}

def set_vol(p):
    try:
        import ctypes
        winmm = ctypes.WinDLL("winmm")
        vol = ctypes.c_int(int(p) * 65535 // 100)
        winmm.waveOutSetVolume(0, vol)
        winmm.waveOutSetVolume(1, vol)
    except:
        pass

def check():
    k = entry.get().strip()
    if k in KEYS:
        messagebox.showinfo("", "激活成功 ProMax")
        win.destroy()
        main_win()
    else:
        messagebox.showerror("", "卡密错误")

def main_win():
    w = tk.Tk()
    w.title("音量增强")
    w.geometry("400x200")
    tk.Label(w, text="ProMax 音量增强", font=("", 16)).pack(pady=10)
    s = tk.Scale(w, from_=100, to=300, orient='horizontal', length=300)
    s.set(150)
    s.pack()
    tk.Button(w, text="应用音量", command=lambda: set_vol(s.get())).pack(pady=10)
    w.mainloop()

win = tk.Tk()
win.title("激活")
win.geometry("400x150")
tk.Label(win, text="输入卡密", font=("", 14)).pack(pady=5)
entry = tk.Entry(win, width=30)
entry.pack()
tk.Button(win, text="激活", command=check).pack(pady=10)
win.mainloop()