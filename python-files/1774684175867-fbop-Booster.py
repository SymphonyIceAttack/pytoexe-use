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

# 专门控制 kX 声卡 Recording Mixer 通道音量
def set_kx_mixer_gain(percent):
    try:
        import ctypes
        winmm = ctypes.WinDLL("winmm")
        # 强制推高 Recording Mixer 采集音量
        val = int(percent * 655.35)  # 0~1000 → 0~65535
        winmm.waveInSetVolume(0, ctypes.c_int(val))
        winmm.waveInSetVolume(1, ctypes.c_int(val))
    except Exception as e:
        print(f"调试信息: {e}")

def check():
    k = entry.get().strip()
    if k in KEYS:
        messagebox.showinfo("Booster", "✅ 激活成功\nkX 声卡增益已启动")
        win.destroy()
        main_win()
    else:
        messagebox.showerror("错误", "卡密无效")

def main_win():
    w = tk.Tk()
    w.title("kX 声卡增益器")
    w.geometry("440x360")
    w.resizable(0, 0)
    w.configure(bg="#121212")
    w.attributes("-alpha", 0.85)  # 半透明

    tk.Label(w, text="kX 10k1 声卡增益", font=("微软雅黑", 18, "bold"),
             bg="#121212", fg="#FF4081").pack(pady=20)

    tk.Label(w, text="Recording Mixer 增益强度", bg="#121212", fg="white").pack()

    s = tk.Scale(w, from_=0, to=1000, orient="horizontal", length=340,
                 bg="#121212", fg="white", troughcolor="#4FC3F7")
    s.set(400)
    s.pack(pady=12)

    lab = tk.Label(w, text="增益：400", bg="#121212", fg="white")
    lab.pack()

    def apply():
        v = s.get()
        set_kx_mixer_gain(v)
        lab.config(text=f"增益：{v}")

    tk.Button(w, text="应用增益", bg="#7C4DFF", fg="white",
              padx=25, pady=8, command=apply).pack(pady=20)

    w.mainloop()

# 登录界面
win = tk.Tk()
win.title("Booster")
win.geometry("440x300")
win.resizable(0, 0)
win.configure(bg="#121212")
win.attributes("-alpha", 0.85)

tk.Label(win, text="Booster", font=("Impact", 32, "bold"),
         bg="#121212", fg="#4FC3F7").pack(pady=40)

frame = tk.Frame(win, bg="#121212")
frame.pack()
tk.Label(frame, text="卡密:", fg="white", bg="#121212").grid(row=0, column=0, padx=5)
entry = tk.Entry(frame, width=28)
entry.grid(row=0, column=1)

tk.Button(win, text="激活", bg="#2196F3", fg="white", padx=30, pady=6,
          command=check).pack(pady=20)

win.mainloop()