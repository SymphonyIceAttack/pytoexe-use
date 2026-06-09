# -*- coding: utf-8 -*-
import os
import sys

# 判断是否在线打包环境，云端构建时不启动tk窗口
IS_CLOUD_BUILD = "inscode" in sys.executable.lower()

if not IS_CLOUD_BUILD:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

# 导入配置函数
def import_config():
    path = filedialog.askopenfilename(filetypes=[("OVPN Config", "*.ovpn")])
    if not path:
        return
    with open(path, "r", encoding="utf-8") as f:
        text.delete(1.0, tk.END)
        text.insert(tk.END, f.read())

# 生成文件逻辑
def save_exe_config(content):
    # 云端构建阶段直接跳过文件写入，避免沙盒权限报错
    if IS_CLOUD_BUILD:
        return
    with open("config.ovpn", "w", encoding="utf-8") as f:
        f.write(content)
    vbscript = 'CreateObject("WScript.Shell").Run "openvpn.exe --config config.ovpn", 0'
    with open("start.vbs", "w", encoding="utf-8") as f:
        f.write(vbscript)
    messagebox.showinfo("Success", "Files Generated: config.ovpn & start.vbs")

# 主入口
def main():
    if IS_CLOUD_BUILD:
        # 云端打包环境仅初始化代码逻辑，不启动UI
        print("Cloud build mode, skip GUI init, build exe normally")
        return

    # 本地Windows正常加载UI
    win = tk.Tk()
    win.title("OpenVPN Client EXE Generator")
    win.geometry("700x600")

    ttk.Label(win, text="OpenVPN Client EXE Generator", font=("Arial",16,"bold")).pack(pady=10)
    frame = ttk.Frame(win)
    frame.pack(pady=5)
    ttk.Button(frame, text="Import OVPN File", command=import_config).grid(row=0,column=0,padx=5)
    ttk.Button(frame, text="Generate Package Files", command=lambda: save_exe_config(text.get(1.0,tk.END).strip())).grid(row=0,column=1,padx=5)

    ttk.Label(win, text="Edit OpenVPN Config:").pack()
    text = tk.Text(win, width=85, height=28, font=("Consolas",10))
    text.pack(pady=5, padx=10)

    default_cfg = """client
dev tun
proto udp
remote your.domain.com 1194
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
    text.insert(tk.END, default_cfg)
    win.mainloop()

if __name__ == "__main__":
    main()