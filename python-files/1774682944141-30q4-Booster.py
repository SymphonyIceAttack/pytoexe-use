import tkinter as tk
from tkinter import messagebox

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

# 麦克风增益核心（真正放大你说话的声音）
def set_mic_gain(level):
    try:
        from ctypes import cast, POINTER, py_object
        import comtypes
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetMicrophone()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        max_db = 35.0   # 最大增益
        target_db = min((level / 1000) * max_db, max_db)
        volume.SetMasterVolumeLevel(target_db, None)
    except:
        pass

def check():
    k = entry.get().strip()
    if k in KEYS:
        messagebox.showinfo("Booster", "✅ 激活成功\n麦克风增益已启动")
        win.destroy()
        main_win()
    else:
        messagebox.showerror("错误", "卡密无效")

def main_win():
    w = tk.Tk()
    w.title("麦克风增益")
    w.geometry("440x360")
    w.resizable(0,0)
    w.configure(bg="#121212")
    w.attributes("-alpha", 0.85)

    tk.Label(w, text="麦克风增益控制", font=("微软雅黑",18,"bold"),
             bg="#121212", fg="#4FC3F7").pack(pady=20)

    s = tk.Scale(w, from_=0, to=1000, orient="horizontal", length=340,
                 bg="#121212", fg="white", troughcolor="#7C4DFF")
    s.set(300)
    s.pack(pady=15)

    lab = tk.Label(w, text="增益强度：300", bg="#121212", fg="white")
    lab.pack()

    def apply():
        v = s.get()
        set_mic_gain(v)
        lab.config(text=f"增益强度：{v}")

    tk.Button(w, text="应用麦克风增益", bg="#FF4081", fg="white",
              padx=25, pady=8, command=apply).pack(pady=20)
    w.mainloop()

# 登录界面
win = tk.Tk()
win.title("Booster")
win.geometry("440x300")
win.resizable(0,0)
win.configure(bg="#121212")
win.attributes("-alpha", 0.85)

tk.Label(win, text="Booster", font=("Impact",32,"bold"),
         bg="#121212", fg="#4FC3F7").pack(pady=40)

frame = tk.Frame(win, bg="#121212")
frame.pack()
tk.Label(frame, text="卡密:", fg="white", bg="#121212").grid(row=0,column=0,padx=5)
entry = tk.Entry(frame, width=28)
entry.grid(row=0,column=1)
tk.Button(win, text="激活", bg="#2196F3", fg="white", padx=30,pady=6,
          command=check).pack(pady=20)

win.mainloop()