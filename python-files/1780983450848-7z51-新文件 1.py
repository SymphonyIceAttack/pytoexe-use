# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def import_config():
    path = filedialog.askopenfilename(filetypes=[("OVPN Config", "*.ovpn")])
    if not path:
        return
    with open(path, "r", encoding="utf-8") as f:
        text.delete(1.0, tk.END)
        text.insert(tk.END, f.read())

def save_exe_config():
    cfg = text.get(1.0, tk.END).strip()
    if len(cfg) < 10:
        messagebox.showerror("错误", "配置不能为空")
        return

    with open("config.ovpn", "w", encoding="utf-8") as f:
        f.write(cfg)

    with open("start.vbs", "w", encoding="utf-8") as f:
        f.write('CreateObject("WScript.Shell").Run "openvpn.exe --config config.ovpn", 0')

    messagebox.showinfo("成功", "已生成：config.ovpn + start.vbs\n\n请与官方 openvpn.exe 一起打包为 EXE！")

# ==================== UI 界面 ====================
win = tk.Tk()
win.title("OpenVPN 客户端 EXE 生成器 —— 完整版")
win.geometry("700x600")

# 标题
ttk.Label(win, text="OpenVPN 客户端 EXE 生成器", font=("黑体", 16, "bold")).pack(pady=10)

# 按钮区
frame = ttk.Frame(win)
frame.pack(pady=5)

ttk.Button(frame, text="导入 .ovpn 配置文件", command=import_config).grid(row=0, column=0, padx=5)
ttk.Button(frame, text="生成 EXE 所需文件", command=save_exe_config).grid(row=0, column=1, padx=5)

# 编辑框
ttk.Label(win, text="可直接修改配置内容：").pack()
text = tk.Text(win, width=85, height=28, font=("Consolas", 10))
text.pack(pady=5, padx=10)

# 默认配置模板
default_config = """client
dev tun
proto udp
remote 你的域名或IP 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
verb 3
tun-ipv6
route-ipv6 ::/0
"""
text.insert(tk.END, default_config)

win.mainloop()