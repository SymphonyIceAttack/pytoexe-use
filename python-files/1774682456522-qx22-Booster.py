import tkinter as tk
from tkinter import messagebox

# 卡密
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
        winmm = ctypes.WDLL("winmm")
        real_vol = min(int(p), 100)
        vol = ctypes.c_int(real_vol * 65535 // 100)
        winmm.waveOutSetVolume(0, vol)
        winmm.waveOutSetVolume(1, vol)
    except:
        pass

def check():
    k = entry.get().strip()
    if k in KEYS:
        messagebox.showinfo("Booster", "✅ 激活成功\n模式：ProMax 狂暴版")
        win.destroy()
        main_win()
    else:
        messagebox.showerror("Booster", "❌ 卡密无效")

def main_win():
    w = tk.Tk()
    w.title("Booster")
    w.geometry("440x360")
    w.resizable(0,0)
    w.configure(bg="#121212")
    # 半透明（0~1，越小越透）
    w.attributes("-alpha", 0.85)

    tk.Label(w, text="ProMax 狂暴版", font=("微软雅黑",18,"bold"),
             bg="#121212", fg="#FF4081").pack(pady=15)

    tk.Label(w, text="音量增益控制", bg="#121212", fg="white").pack()

    s = tk.Scale(w, from_=0, to=1000, orient="horizontal", length=340,
                 bg="#121212", fg="white", troughcolor="#4FC3F7")
    s.set(200)
    s.pack(pady=10)

    lab = tk.Label(w, text="音量：200%", bg="#121212", fg="white")
    lab.pack()

    def apply():
        v = s.get()
        set_vol(v)
        lab.config(text=f"音量：{v}%")

    tk.Button(w, text="应用音量", bg="#7C4DFF", fg="white",
              padx=20, pady=5, command=apply).pack(pady=10)

    w.mainloop()

# 登录界面
win = tk.Tk()
win.title("Booster")
win.geometry("440x300")
win.resizable(0,0)
win.configure(bg="#121212")
# 登录页也半透明
win.attributes("-alpha", 0.85)

tk.Label(win, text="Booster", font=("Impact",32,"bold"),
         bg="#121212", fg="#4FC3F7").pack(pady=40)

frame = tk.Frame(win, bg="#121212")
frame.pack(pady=5)
tk.Label(frame, text="卡密:", bg="#121212", fg="white").grid(row=0,column=0,padx=5)
entry = tk.Entry(frame, width=28)
entry.grid(row=0,column=1)
entry.bind("<Return>", lambda e:check())

tk.Button(win, text="验 证", bg="#2196F3", fg="white",
          padx=25, pady=6, command=check).pack(pady=20)

win.mainloop()