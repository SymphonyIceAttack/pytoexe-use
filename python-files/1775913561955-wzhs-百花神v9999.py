import tkinter as tk
from tkinter import ttk, messagebox
import random

class BaiHuaShen:
    def __init__(self, root):
        self.root = root
        self.root.title("白花神v9999")
        self.root.geometry("700x550")
        self.root.configure(bg='#f0f0f0')
        
        self.banned = []
        
        nb = ttk.Notebook(self.root)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tab1 = tk.Frame(nb, bg='#f0f0f0')
        tab2 = tk.Frame(nb, bg='#f0f0f0')
        tab3 = tk.Frame(nb, bg='#f0f0f0')
        tab4 = tk.Frame(nb, bg='#f0f0f0')
        
        nb.add(tab1, text="自瞄")
        nb.add(tab2, text="透视")
        nb.add(tab3, text="移动")
        nb.add(tab4, text="暴力")
        
        funcs1 = [("360°自瞄", self.f1), ("逆向自瞄", self.f2), ("检测对方什么挂", self.f3), ("距离优先", self.f4), ("反向自瞄", self.f5), ("反后坐力", self.f6)]
        funcs2 = [("方框透视", self.f7), ("骨骼透视", self.f8), ("血条显示", self.f9), ("发光特效", self.f10), ("切换模型", self.f11), ("距离显示", self.f12)]
        funcs3 = [("暴力连跳", self.f13), ("子弹加速", self.f14), ("快速急停", self.f15), ("低重力", self.f16), ("速度修改", self.f17), ("飞天", self.f18)]
        funcs4 = [("子弹追踪", self.f19), ("穿墙击杀", self.f20), ("全图吸人", self.f21), ("秒杀爆头", self.f22), ("无后坐力", self.f23), ("无限子弹", self.f24)]
        
        for i, (name, func) in enumerate(funcs1):
            btn = tk.Button(tab1, text=name, width=14, bg='white', relief=tk.GROOVE, command=func)
            btn.grid(row=i//2, column=i%2, padx=8, pady=5)
        
        for i, (name, func) in enumerate(funcs2):
            btn = tk.Button(tab2, text=name, width=14, bg='white', relief=tk.GROOVE, command=func)
            btn.grid(row=i//2, column=i%2, padx=8, pady=5)
        
        for i, (name, func) in enumerate(funcs3):
            btn = tk.Button(tab3, text=name, width=14, bg='white', relief=tk.GROOVE, command=func)
            btn.grid(row=i//2, column=i%2, padx=8, pady=5)
        
        for i, (name, func) in enumerate(funcs4):
            btn = tk.Button(tab4, text=name, width=14, bg='white', relief=tk.GROOVE, command=func)
            btn.grid(row=i//2, column=i%2, padx=8, pady=5)
        
        ban_frame = tk.LabelFrame(self.root, text="BAN人系统", bg='#f0f0f0', font=("微软雅黑", 9))
        ban_frame.pack(fill=tk.X, padx=10, pady=(0,10))
        
        for i in range(1, 6):
            btn = tk.Button(ban_frame, text=f"{i}号", width=6, bg='#ff4444', fg='white', command=lambda x=i: self.ban_num(x))
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.ban_entry = tk.Entry(ban_frame, width=15)
        self.ban_entry.pack(side=tk.LEFT, padx=5)
        self.ban_entry.insert(0, "输入玩家名")
        
        tk.Button(ban_frame, text="BAN", width=6, bg='#ff4444', fg='white', command=self.ban_name).pack(side=tk.LEFT, padx=5)
        tk.Button(ban_frame, text="名单", width=6, bg='#444444', fg='white', command=self.show_ban_list).pack(side=tk.LEFT, padx=5)
        
        self.status = tk.Label(self.root, text="白花神v9999 | 已注入", bg='#e0e0e0', anchor=tk.W)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
    
    def log(self, msg):
        messagebox.showinfo("白花神v9999", msg)
    
    def ban_num(self, num):
        self.banned.append(f"{num}号玩家")
        self.log(f"已封禁 {num}号玩家")
    
    def ban_name(self):
        name = self.ban_entry.get()
        if name and name != "输入玩家名":
            self.banned.append(name)
            self.log(f"已封禁 {name}")
    
    def show_ban_list(self):
        if self.banned:
            messagebox.showinfo("封禁名单", "\n".join(self.banned))
        else:
            messagebox.showinfo("封禁名单", "暂无封禁")
    
    def f1(self): self.log("[360°自瞄] 已开启")
    def f2(self): self.log("[暴力自瞄] 已开启")
    def f3(self): self.log("[检测对面什么挂] 已开启")
    def f4(self): self.log("[距离优先] 已开启")
    def f5(self): self.log("[反向自瞄] 按Alt激活")
    def f6(self): self.log("[反后坐力] 已开启")
    def f7(self): self.log("[方框透视] 已开启")
    def f8(self): self.log("[骨骼透视] 已开启")
    def f9(self): self.log("[血条显示] 已开启")
    def f10(self): self.log("[发光特效] 已开启")
    def f11(self): self.log("[雷达透视] 已开启")
    def f12(self): self.log("[距离显示] 已开启")
    def f13(self): self.log("[暴力连跳] 已开启")
    def f14(self): self.log("[子弹加速] 已开启")
    def f15(self): self.log("[快速急停] 已开启")
    def f16(self): self.log("[低重力] 已开启")
    def f17(self): self.log("[速度修改] 已开启")
    def f18(self): self.log("[飞天] 已开启")
    def f19(self): self.log("[子弹追踪] 逆天已开")
    def f20(self): self.log("[穿墙击杀] 逆天已开")
    def f21(self): self.log("[全图吸人] 逆天已开")
    def f22(self): self.log("[秒杀爆头] 逆天已开")
    def f23(self): self.log("[无后坐力] 已开启")
    def f24(self): self.log("[无限子弹] 已开启")

if __name__ == "__main__":
    root = tk.Tk()
    app = BaiHuaShen(root)
    root.mainloop()