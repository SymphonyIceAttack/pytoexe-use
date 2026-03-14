import tkinter as tk
from tkinter import ttk, messagebox

def on_aimbot():
    messagebox.showinfo("提示", "✅ 自瞄开关")

def on_esp():
    messagebox.showinfo("提示", "✅ 无敌开关")

def on_esp():
    messagebox.showinfo("提示", "✅ 透视开关")

def on_speed():
    messagebox.showinfo("提示", "✅ 加速开关")

def on_no_recoil():
    messagebox.showinfo("提示", "✅ 无后坐力")

def on_exit():
    root.quit()

# 主窗口
root = tk.Tk()
root.title("和平精英 KTV辅助菜单")
root.geometry("400x500")
root.resizable(False, False)
root.configure(bg="#1a1a1a")

# 标题
title_label = tk.Label(
    root,
    text="PE Simulator Menu\n(和平精英实际功能菜单)",
    bg="#1a1a1a",
    fg="#00ff00",
    font=("微软雅黑", 14, "bold")
)
title_label.pack(pady=20)

# 框架
frame = tk.Frame(root, bg="#262626", bd=2, relief=tk.RIDGE)
frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

# 按钮样式
btn_style = {
    "bg": "#333333",
    "fg": "white",
    "font": ("微软雅黑", 11),
    "width": 20,
    "height": 2,
    "relief": tk.FLAT,
    "activebackground": "#444444"
}

# 功能按钮
btn_aim = tk.Button(frame, text="枪械锁头", command=on_aimbot, **btn_style)
btn_aim.pack(pady=8)

btn_aim = tk.Button(frame, text="人物无敌", command=on_aimbot, **btn_style)
btn_aim.pack(pady=8)

btn_esp = tk.Button(frame, text="人物透视", command=on_esp, **btn_style)
btn_esp.pack(pady=8)

btn_speed = tk.Button(frame, text="移动加速", command=on_speed, **btn_style)
btn_speed.pack(pady=8)

btn_norecoil = tk.Button(frame, text="无后坐力", command=on_no_recoil, **btn_style)
btn_norecoil.pack(pady=8)

btn_exit = tk.Button(frame, text="关闭KTV菜单", command=on_exit, bg="#cc0000", fg="white", font=("微软雅黑", 11), width=20, height=2)
btn_exit.pack(pady=15)

# 底部提示
tip = tk.Label(
    root,
    text="本程序界面\n外挂,修改游戏",
    bg="#1a1a1a",
    fg="gray",
    font=("微软雅黑", 9)
)
tip.pack(pady=10)

root.mainloop()