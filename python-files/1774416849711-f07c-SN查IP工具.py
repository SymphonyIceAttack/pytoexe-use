import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import socket
import subprocess
import re
from queue import Queue

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "192.168.1.1"

def get_subnet(ip):
    parts = ip.split(".")
    return f"{parts[0]}.{parts[1]}.{parts[2]}."

def ping_ip(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", 100, ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except:
        return False

def get_device_info(ip):
    try:
        arp = subprocess.check_output(
            ["arp", "-a", ip],
            creationflags=subprocess.CREATE_NO_WINDOW,
            text=True
        )
        return arp.strip()
    except:
        return ""

def scan_task(sn, subnet, queue):
    queue.put(("info", f"开始扫描网段: {subnet}1~254"))
    found = False

    for i in range(1, 255):
        ip = subnet + str(i)
        if ping_ip(ip):
            info = get_device_info(ip)
            queue.put(("info", f"在线: {ip}"))

            if sn.lower() in info.lower() or sn in ip:
                queue.put(("success", f"\n找到设备！\nSN: {sn}\nIP: {ip}"))
                found = True
                break

    if not found:
        queue.put(("error", "未找到对应SN的设备IP"))

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SN查IP工具")
        self.root.geometry("600x420")
        self.sn = tk.StringVar()
        self.subnet = tk.StringVar()
        self.queue = Queue()

        ip = get_local_ip()
        self.subnet.set(get_subnet(ip))

        ttk.Label(root, text="SN序列号:").place(x=20, y=15)
        ttk.Entry(root, textvariable=self.sn, width=30).place(x=100, y=15)

        ttk.Label(root, text="IP网段:").place(x=20, y=50)
        ttk.Entry(root, textvariable=self.subnet, width=30).place(x=100, y=50)

        ttk.Button(root, text="开始扫描", command=self.start).place(x=350, y=15)
        ttk.Button(root, text="清空", command=self.clear).place(x=450, y=15)

        self.txt = scrolledtext.ScrolledText(root, width=70, height=20)
        self.txt.place(x=20, y=90)
        self.check_queue()

    def log(self, msg, color="black"):
        self.txt.config(state=tk.NORMAL)
        self.txt.insert(tk.END, msg + "\n")
        self.txt.config(state=tk.DISABLED)
        self.txt.see(tk.END)

    def start(self):
        sn = self.sn.get().strip()
        subnet = self.subnet.get().strip()
        if not sn:
            messagebox.showerror("错误", "请输入SN")
            return
        threading.Thread(target=scan_task, args=(sn, subnet, self.queue), daemon=True).start()

    def check_queue(self):
        while not self.queue.empty():
            t, m = self.queue.get()
            self.log(m, {"success":"green","error":"red"}.get(t,"black"))
        self.root.after(100, self.check_queue)

    def clear(self):
        self.txt.config(state=tk.NORMAL)
        self.txt.delete(1.0, tk.END)
        self.txt.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()