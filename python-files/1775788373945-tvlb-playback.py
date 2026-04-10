import os
import sys
import json
import time
import tkinter as tk
from tkinter import messagebox, ttk

class PlaybackController:
    def __init__(self):
        try:
            import serial
            import serial.tools.list_ports
            self.serial = serial
        except ImportError:
            messagebox.showerror("错误", "缺少串口组件")
            sys.exit(1)
        
        self.macro_file = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "macro.json")
        
        if not os.path.exists(self.macro_file):
            messagebox.showerror("错误", "未找到宏文件 macro.json")
            sys.exit(1)
        
        self.serial_port = None
        self.connected = False
        
        self.root = tk.Tk()
        self.root.title("宏回放器")
        self.root.geometry("300x180")
        
        self.status_label = tk.Label(self.root, text="等待设备连接...", 
                                     font=("微软雅黑", 11), fg="orange")
        self.status_label.pack(pady=30)
        
        self.progress = ttk.Progressbar(self.root, mode='indeterminate', length=200)
        self.progress.pack()
        self.progress.start()
        
        tk.Label(self.root, text="正在连接 RP2040 设备...", 
                font=("微软雅黑", 9), fg="gray").pack(pady=20)
        
        self.check_connection()
    
    def check_connection(self):
        if not self.connected:
            if self.find_rp2040():
                self.connected = True
                self.status_label.config(text="已连接 - 开始回放", fg="green")
                self.progress.stop()
                self.progress.pack_forget()
                self.send_command("START")
                self.root.after(2000, self.root.quit)
        if not self.connected:
            self.root.after(1000, self.check_connection)
    
    def find_rp2040(self):
        try:
            ports = self.serial.tools.list_ports.comports()
            for port in ports:
                if any(x in str(port.description) for x in ["RP2040", "CircuitPython", "Pico", "USB Serial"]):
                    self.serial_port = self.serial.Serial(port.device, 115200, timeout=1)
                    return True
        except:
            pass
        return False
    
    def send_command(self, cmd):
        if self.serial_port:
            try:
                self.serial_port.write(f"{cmd}\n".encode())
                return True
            except:
                pass
        return False
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PlaybackController()
    app.run()