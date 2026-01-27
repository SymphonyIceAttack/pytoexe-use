import tkinter as tk
from tkinter import messagebox
import winreg

REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"

def read_proxy():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
        server, _ = winreg.QueryValueEx(key, "ProxyServer")
        winreg.CloseKey(key)
        if enabled and server:
            if ":" in server:
                ip, port = server.split(":")
            else:
                ip, port = server, ""
            return ip, port
        return "", ""
    except:
        return "", ""

def set_proxy(ip, port):
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 1)
    winreg.SetValueEx(key, "ProxyServer", 0, winreg.REG_SZ, f"{ip}:{port}")
    winreg.CloseKey(key)

def disable_proxy():
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "ProxyEnable", 0, winreg.REG_DWORD, 0)
    winreg.CloseKey(key)

def update_ui():
    ip, port = read_proxy()
    ip_entry.delete(0, tk.END)
    port_entry.delete(0, tk.END)
    ip_entry.insert(0, ip)
    port_entry.insert(0, port)
    if ip and port:
        btn.config(text="STOP", bg="#e53935")
    else:
        btn.config(text="START", bg="#43a047")

def toggle():
    if btn.cget("text") == "START":
        ip = ip_entry.get().strip()
        port = port_entry.get().strip()
        if not ip or not port:
            messagebox.showwarning("Warning", "IP و PORT را وارد کنید")
            return
        set_proxy(ip, port)
    else:
        disable_proxy()
    update_ui()

root = tk.Tk()
root.title("Proxy Controller")
root.geometry("320x200")
root.resizable(False, False)

bg = "#f5f5f5"
root.configure(bg=bg)

tk.Label(root, text="IP", bg=bg).pack(pady=(20,5))
ip_entry = tk.Entry(root, width=30, relief="flat")
ip_entry.pack()

tk.Label(root, text="PORT", bg=bg).pack(pady=(10,5))
port_entry = tk.Entry(root, width=30, relief="flat")
port_entry.pack()

btn = tk.Button(root, text="START", width=20, command=toggle,
                fg="white", bg="#43a047", relief="flat")
btn.pack(pady=20)

update_ui()
root.mainloop()
