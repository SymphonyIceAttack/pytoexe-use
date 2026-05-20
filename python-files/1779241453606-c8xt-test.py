import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import re
import time

class SerialMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("USB串口 数据监控端")
        self.root.geometry("550x350")
        self.root.resizable(False, False)

        self.serial_conn = None
        self.is_reading = False

        self.setup_ui()

    def setup_ui(self):
        # 顶部控制面板
        ctrl_frame = ttk.Frame(self.root, padding="10")
        ctrl_frame.pack(fill=tk.X)

        ttk.Label(ctrl_frame, text="串口号:").pack(side=tk.LEFT)
        self.port_cbox = ttk.Combobox(ctrl_frame, width=10, state="readonly")
        self.port_cbox.pack(side=tk.LEFT, padx=5)
        self.refresh_ports()

        ttk.Button(ctrl_frame, text="刷新", command=self.refresh_ports, width=5).pack(side=tk.LEFT)

        ttk.Label(ctrl_frame, text="波特率:").pack(side=tk.LEFT, padx=(15, 5))
        # 默认设定为要求的 1115200，并加入常用波特率备选
        self.baud_cbox = ttk.Combobox(ctrl_frame, width=10)
        self.baud_cbox['values'] = ["1115200", "115200", "9600", "1500000"] 
        self.baud_cbox.set("1115200")
        self.baud_cbox.pack(side=tk.LEFT, padx=5)

        self.btn_connect = ttk.Button(ctrl_frame, text="打开串口", command=self.toggle_serial)
        self.btn_connect.pack(side=tk.LEFT, padx=15)

        # 数据显示面板
        data_frame = ttk.LabelFrame(self.root, text="实时数据 (解析格式: 000 1=... 000)", padding="15")
        data_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.val_labels = []
        titles = ["通道 1 (温度)", "通道 2 (温度)", "通道 3 (温度)", "通道 4 (温度)", "通道 5 (温度)", "通道 6 (电量)"]
        self.units = [" ℃", " ℃", " ℃", " ℃", " ℃", " %"]

        # 使用 Grid 布局排版 6 个数据
        for i in range(6):
            row = i // 2
            col = (i % 2) * 2

            ttk.Label(data_frame, text=f"{titles[i]}:", font=("微软雅黑", 12)).grid(row=row, column=col, sticky=tk.E, pady=15, padx=(10, 5))
            
            # 数值标签，初始显示 --
            val_label = ttk.Label(data_frame, text="--.---" + self.units[i], font=("Arial", 14, "bold"), foreground="#0055AA", width=10)
            val_label.grid(row=row, column=col+1, sticky=tk.W, pady=15, padx=(0, 20))
            self.val_labels.append(val_label)

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_cbox['values'] = ports
        if ports:
            self.port_cbox.current(0)
        else:
            self.port_cbox.set("")

    def toggle_serial(self):
        if self.serial_conn is None or not self.serial_conn.is_open:
            port = self.port_cbox.get()
            baud = self.baud_cbox.get()
            
            if not port:
                messagebox.showwarning("警告", "请先选择一个有效的串口！")
                return

            try:
                self.serial_conn = serial.Serial(port, int(baud), timeout=0.5)
                self.is_reading = True
                self.btn_connect.config(text="关闭串口")
                self.port_cbox.config(state="disabled")
                self.baud_cbox.config(state="disabled")
                
                # 开启后台读取线程
                threading.Thread(target=self.read_serial_data, daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"无法打开串口:\n{e}")
        else:
            self.close_serial()

    def close_serial(self):
        self.is_reading = False
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.btn_connect.config(text="打开串口")
        self.port_cbox.config(state="readonly")
        self.baud_cbox.config(state="normal")
        
        # 恢复默认显示
        for i, lbl in enumerate(self.val_labels):
            lbl.config(text="--.---" + self.units[i])

    def read_serial_data(self):
        buffer = ""
        # 匹配格式: 1=24.45,2=45.32,3=56.56,4=34.4,5=33.56,6=45.3
        # 使用正则表达式容错提取，只要符合这个结构即可忽略前后的脏字符
        pattern = re.compile(r'1=([\d.]+),2=([\d.]+),3=([\d.]+),4=([\d.]+),5=([\d.]+),6=([\d.]+)')
        
        while self.is_reading and self.serial_conn.is_open:
            try:
                if self.serial_conn.in_waiting:
                    # 读取 ASCII 数据，忽略无法解析的字节
                    data = self.serial_conn.read(self.serial_conn.in_waiting).decode('ascii', errors='ignore')
                    buffer += data
                    
                    # 防止由于硬件发送错误导致内存爆满，保留最后500个字符即可
                    if len(buffer) > 500:
                        buffer = buffer[-500:]

                    # 查找符合结构的数据段
                    match = pattern.search(buffer)
                    if match:
                        # 提取6个数据
                        values = match.groups()
                        
                        # 使用after方法在主线程更新UI
                        self.root.after(0, self.update_ui_values, values)
                        
                        # 清理已经解析过的数据，寻找下一个 000 结束符之后的数据
                        buffer = buffer[match.end():]
                else:
                    time.sleep(0.01) # 降低CPU占用
            except Exception:
                self.root.after(0, self.close_serial)
                break

    def update_ui_values(self, values):
        for i in range(6):
            self.val_labels[i].config(text=f"{values[i]}{self.units[i]}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialMonitorApp(root)
    
    # 设置Windows DPI适配，解决界面模糊问题
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
        
    root.mainloop()