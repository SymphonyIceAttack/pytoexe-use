import tkinter as tk
from tkinter import messagebox
import json
import time
import os
import requests

# 你的10张卡密
VALID_KEYS = {
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

BAN_URL = "https://raw.githubusercontent.com/seedfly/helper/main/booster_ban.txt"
VALID_SECONDS = 2592000
MAX_VOL = 300
CONFIG_FILE = "booster_activation.json"

# 音量控制
try:
    import ctypes
    winmm = ctypes.WinDLL("winmm")
    def set_system_volume(percent):
        try:
            vol = ctypes.c_int(min(percent, 300) * 65535 // 100)
            winmm.waveOutSetVolume(0, vol)
            winmm.waveOutSetVolume(1, vol)
        except:
            pass
except:
    def set_system_volume(percent):
        pass

# 封禁检查
def get_banned():
    try:
        r = requests.get(BAN_URL, timeout=3)
        return {k.strip() for k in r.text.splitlines() if k.strip()}
    except:
        return set()

# 激活时间
def load_activation():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_activation(key):
    data = load_activation()
    data[key] = time.time()
    with open(CONFIG_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f)

def is_expired(key):
    data = load_activation()
    t = data.get(key)
    if not t: return False
    return time.time()-t > VALID_SECONDS

class BoosterApp:
    def __init__(self,root):
        self.root = root
        self.root.title("Booster")
        self.root.geometry("440x360")
        self.root.resizable(0,0)
        self.root.configure(bg="#121212")
        self.activated = False
        self.current_key = None
        self.show_login()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    def show_login(self):
        self.clear()
        tk.Label(self.root,text="Booster",font=("Impact",32,"bold"),bg="#121212",fg="#4FC3F7").pack(pady=40)
        f = tk.Frame(self.root,bg="#121212")
        f.pack(pady=5)
        tk.Label(f,text="卡密:",bg="#121212",fg="white").grid(row=0,column=0,padx=5)
        self.key_entry = tk.Entry(f,width=28)
        self.key_entry.grid(row=0,column=1)
        self.key_entry.bind("<Return>",self.check_key)
        tk.Button(self.root,text="验 证",bg="#2196F3",fg="white",padx=25,pady=6,command=self.check_key).pack(pady=20)

    def check_key(self,e=None):
        key = self.key_entry.get().strip()
        if key not in VALID_KEYS:
            messagebox.showerror("Booster","❌ 卡密无效")
            return
        if key in get_banned():
            messagebox.showerror("Booster","❌ 已被管理员停用")
            return
        if is_expired(key):
            messagebox.showerror("Booster","❌ 卡密已到期（30天）")
            return
        save_activation(key)
        self.activated = True
        messagebox.showinfo("Booster","✅ 激活成功\n工作模式：ProMax\n30天有效期")
        self.show_main()

    def show_main(self):
        self.clear()
        tk.Label(self.root,text="工作模式：ProMax",font=("微软雅黑",18,"bold"),bg="#121212",fg="#FF4081").pack(pady=15)
        tk.Label(self.root,text="音量增益控制",bg="#121212",fg="white").pack()
        self.slider = tk.Scale(self.root,from_=0,to=300,orient="horizontal",length=340,bg="#121212",fg="white",troughcolor="#4FC3F7")
        self.slider.set(100)
        self.slider.pack(pady=10)
        self.lab = tk.Label(self.root,text="音量：100%",bg="#121212",fg="white")
        self.lab.pack()
        tk.Button(self.root,text="应用音量",bg="#7C4DFF",fg="white",padx=20,pady=5,command=self.apply).pack(pady=10)
        tk.Label(self.root,text="本卡密有效期30天",bg="#121212",fg="gray").pack(side="bottom",pady=5)

    def apply(self):
        if not self.activated:
            messagebox.showwarning("提示","请先激活")
            return
        v = int(self.slider.get())
        set_system_volume(v)
        self.lab.config(text=f"音量：{v}%")

if __name__=="__main__":
    root = tk.Tk()
    BoosterApp(root)
    root.mainloop()