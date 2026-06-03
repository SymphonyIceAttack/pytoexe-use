import tkinter as tk
from tkinter import ttk
import serial
import threading
import time

root = tk.Tk()
root.title("COIN 自动发送工具")
root.geometry("380x320")

ser = None
running = False

def open_serial():
    global ser
    try:
        ser = serial.Serial(com_var.get(), int(baud_var.get()), timeout=1)
        status.config(text="串口已打开", fg="green")
        return True
    except Exception as e:
        status.config(text=f"失败: {e}", fg="red")
        return False

def send():
    global running
    if not ser and not open_serial():
        return
    running = True
    threading.Thread(target=worker, daemon=True).start()
    status.config(text="发送中...", fg="orange")

def stop():
    global running
    running = False
    status.config(text="已停止", fg="red")

def worker():
    s, e = int(start_var.get()), int(end_var.get())
    delay = float(interval_var.get()) / 1000
    for i in range(s, e + 1):
        if not running: break
        ser.write(f"COIN={i:04d}\r\n".encode())
        progress.config(text=f"COIN={i:04d}")
        time.sleep(delay)
    status.config(text="完成", fg="blue")

# UI
frm = ttk.Frame(root, padding=10)
frm.pack()

ttk.Label(frm, text="COM").grid(row=0, column=0)
com_var = tk.StringVar(value="COM3")
ttk.Entry(frm, textvariable=com_var, width=10).grid(row=0, column=1)

ttk.Label(frm, text="波特率").grid(row=1, column=0)
baud_var = tk.StringVar(value="38400")
ttk.Entry(frm, textvariable=baud_var, width=10).grid(row=1, column=1)

ttk.Label(frm, text="起始").grid(row=2, column=0)
start_var = tk.StringVar(value="0")
ttk.Entry(frm, textvariable=start_var, width=10).grid(row=2, column=1)

ttk.Label(frm, text="结束").grid(row=3, column=0)
end_var = tk.StringVar(value="9999")
ttk.Entry(frm, textvariable=end_var, width=10).grid(row=3, column=1)

ttk.Label(frm, text="间隔(ms)").grid(row=4, column=0)
interval_var = tk.StringVar(value="500")
ttk.Entry(frm, textvariable=interval_var, width=10).grid(row=4, column=1)

ttk.Button(frm, text="开始", command=send).grid(row=5, column=0, pady=10)
ttk.Button(frm, text="停止", command=stop).grid(row=5, column=1, pady=10)

progress = ttk.Label(frm, text="未开始")
progress.grid(row=6, column=0, columnspan=2)

status = ttk.Label(frm, text="未连接", foreground="gray")
status.grid(row=7, column=0, columnspan=2)

root.mainloop()