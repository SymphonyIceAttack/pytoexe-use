import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import minimalmodbus
import serial.tools.list_ports
import time

# 自定义 Instrument 类，用于记录原始报文
class DebugInstrument(minimalmodbus.Instrument):
    def __init__(self, port, slaveaddress, log_callback=None):
        super().__init__(port, slaveaddress)
        self.log_callback = log_callback

    def _communicate(self, request, number_of_bytes_to_read):
        if self.log_callback:
            self.log_callback(f"发送请求: {request.hex().upper()}")
        response = super()._communicate(request, number_of_bytes_to_read)
        if self.log_callback:
            self.log_callback(f"接收响应: {response.hex().upper()}")
        return response

class ModbusApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modbus 参数读写工具")
        self.root.geometry("1000x700")
        self.root.minsize(900, 600)

        self.instrument = None
        self.is_connected = False
        self.auto_read_enabled = False
        self.auto_read_id = None

        # 定义参数列表: (显示名称, 寄存器地址, 单位) - 顺序已调整
        self.params = [
            ("水位", 0x0030, "m"),
            ("水温", 0x0034, "℃"),
            ("模拟流速", 0x0032, "m/s"),
            ("超声速度", 0x0036, "m/s"),
            ("输出频率", 0x0038, "MHz")
        ]

        # 主布局：上下两栏，使用 PanedWindow 支持手动调整
        main_paned = ttk.PanedWindow(root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=3)

        log_frame = ttk.LabelFrame(main_paned, text="通讯日志 (原始报文)", padding=5)
        main_paned.add(log_frame, weight=2)

        # 让 top_frame 使用 grid 布局，并设置两列等宽（使用 uniform）
        top_frame.grid_columnconfigure(0, weight=1, uniform="group1")
        top_frame.grid_columnconfigure(1, weight=1, uniform="group1")
        top_frame.grid_rowconfigure(0, weight=1)

        # 左侧通讯配置
        left_frame = ttk.LabelFrame(top_frame, text="通讯配置", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 右侧参数读写
        right_frame = ttk.LabelFrame(top_frame, text="参数读写", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # ========== 左侧：串口参数 ==========
        serial_frame = ttk.LabelFrame(left_frame, text="串口参数", padding=5)
        serial_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(serial_frame, text="串口号:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.port_combo = ttk.Combobox(serial_frame, width=18)
        self.port_combo.grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(serial_frame, text="刷新", command=self.refresh_ports).grid(row=0, column=2, padx=5)

        ttk.Label(serial_frame, text="波特率:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.baudrate_var = tk.StringVar(value="9600")
        baud_combo = ttk.Combobox(serial_frame, textvariable=self.baudrate_var,
                                  values=[1200,2400,4800,9600,19200,38400,57600,115200], width=18)
        baud_combo.grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(serial_frame, text="数据位:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.databits_var = tk.StringVar(value="8")
        databits_combo = ttk.Combobox(serial_frame, textvariable=self.databits_var, values=[5,6,7,8], width=18)
        databits_combo.grid(row=2, column=1, padx=5, pady=2)

        ttk.Label(serial_frame, text="停止位:").grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.stopbits_var = tk.StringVar(value="1")
        stopbits_combo = ttk.Combobox(serial_frame, textvariable=self.stopbits_var, values=[1,1.5,2], width=18)
        stopbits_combo.grid(row=3, column=1, padx=5, pady=2)

        ttk.Label(serial_frame, text="校验位:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.parity_var = tk.StringVar(value="NONE")
        parity_combo = ttk.Combobox(serial_frame, textvariable=self.parity_var, values=["NONE","EVEN","ODD"], width=18)
        parity_combo.grid(row=4, column=1, padx=5, pady=2)

        # ========== 左侧：设备参数 ==========
        device_frame = ttk.LabelFrame(left_frame, text="设备参数", padding=5)
        device_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(device_frame, text="从站地址:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.slave_var = tk.StringVar(value="1")
        ttk.Entry(device_frame, textvariable=self.slave_var, width=20).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(device_frame, text="Float 顺序:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.byteorder_var = tk.StringVar(value="<CDAB (小端字交换)")
        order_combo = ttk.Combobox(device_frame, textvariable=self.byteorder_var,
                                   values=[">ABCD (大端)", "<DCBA (小端)", ">BADC (大端字交换)", "<CDAB (小端字交换)"], width=18)
        order_combo.grid(row=1, column=1, padx=5, pady=2)

        # 连接/断开按钮
        self.connect_btn = tk.Button(left_frame, text="连接设备", command=self.toggle_connection,
                                     bg="SystemButtonFace", fg="black", width=15)
        self.connect_btn.pack(pady=5)

        # 自动读取按钮
        self.auto_read_btn = tk.Button(left_frame, text="启动自动读取", command=self.toggle_auto_read,
                                       bg="SystemButtonFace", fg="black", width=15, state=tk.DISABLED)
        self.auto_read_btn.pack(pady=5)

        # 复位按钮
        self.reset_btn = tk.Button(left_frame, text="复位设备", command=self.reset_device,
                                   bg="SystemButtonFace", fg="black", width=15, state=tk.DISABLED)
        self.reset_btn.pack(pady=5)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(left_frame, textvariable=self.status_var, relief="sunken", anchor="w")
        status_label.pack(side="bottom", fill="x", pady=(10, 0))

        # ========== 右侧：参数列表 ==========
        param_canvas = tk.Canvas(right_frame, highlightthickness=0)
        param_scrollbar = ttk.Scrollbar(right_frame, orient="vertical", command=param_canvas.yview)
        param_scrollable_frame = ttk.Frame(param_canvas)

        param_scrollable_frame.bind(
            "<Configure>",
            lambda e: param_canvas.configure(scrollregion=param_canvas.bbox("all"))
        )
        param_canvas.create_window((0, 0), window=param_scrollable_frame, anchor="n", width=param_canvas.winfo_reqwidth())
        param_canvas.configure(yscrollcommand=param_scrollbar.set)

        param_canvas.pack(side="left", fill="both", expand=True)
        param_scrollbar.pack(side="right", fill="y")

        self.param_vars = {}
        for name, addr, unit in self.params:
            frame = ttk.Frame(param_scrollable_frame, padding=5)
            frame.pack(anchor="center", pady=2)

            label = ttk.Label(frame, text=f"{name} ({unit}):", width=15, anchor="e")
            label.pack(side="left", padx=5)

            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.pack(side="left", padx=5)

            read_btn = ttk.Button(frame, text="读取", command=lambda a=addr, v=var, n=name: self.read_param(a, v, n))
            read_btn.pack(side="left", padx=2)

            write_btn = ttk.Button(frame, text="写入", command=lambda a=addr, v=var, n=name: self.write_param(a, v, n))
            write_btn.pack(side="left", padx=2)

            self.param_vars[addr] = var

        # 底部日志区
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.configure(state='disabled')

        def on_canvas_configure(event):
            param_canvas.itemconfig(param_canvas.find_all()[0], width=event.width)
        param_canvas.bind("<Configure>", on_canvas_configure)

        self.refresh_ports()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log_message(self, msg):
        self.log_text.configure(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set('')
            self.status_var.set("未检测到 COM 口")
            self.log_message("未检测到任何 COM 口")

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("错误", "请选择 COM 口", parent=self.root)
            return
        try:
            baudrate = int(self.baudrate_var.get())
        except:
            messagebox.showerror("错误", "波特率必须是整数", parent=self.root)
            return
        try:
            slave_id = int(self.slave_var.get())
        except:
            messagebox.showerror("错误", "从站地址必须是整数", parent=self.root)
            return
        try:
            bytesize = int(self.databits_var.get())
        except:
            messagebox.showerror("错误", "数据位必须是整数", parent=self.root)
            return

        stopbits_str = self.stopbits_var.get()
        if stopbits_str == '1':
            stopbits = 1
        elif stopbits_str == '1.5':
            stopbits = 1.5
        elif stopbits_str == '2':
            stopbits = 2
        else:
            messagebox.showerror("错误", "停止位取值应为 1, 1.5 或 2", parent=self.root)
            return

        parity_map = {"NONE": 'N', "EVEN": 'E', "ODD": 'O'}
        parity = parity_map.get(self.parity_var.get(), 'N')

        if self.instrument:
            try:
                self.instrument.serial.close()
            except:
                pass

        try:
            self.instrument = DebugInstrument(port, slave_id, log_callback=self.log_message)
            self.instrument.serial.baudrate = baudrate
            self.instrument.serial.bytesize = bytesize
            self.instrument.serial.parity = parity
            self.instrument.serial.stopbits = stopbits
            self.instrument.serial.timeout = 1

            self.log_message(f"尝试连接 {port} 波特率={baudrate} {bytesize}{parity}{stopbits} 从站地址={slave_id}")

            test_val = self.instrument.read_register(0x001B, functioncode=3)
            self.is_connected = True
            self.connect_btn.config(text="断开设备", bg="red", fg="white")
            self.auto_read_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            self.status_var.set(f"已连接 {port} 从站{slave_id} 测试0x001B={test_val}")
            self.log_message(f"连接成功，测试寄存器 0x001B 的值 = {test_val}")
        except Exception as e:
            self.instrument = None
            self.is_connected = False
            self.status_var.set("连接失败")
            self.log_message(f"连接失败: {str(e)}")
            messagebox.showerror("连接错误", f"无法连接设备:\n{str(e)}", parent=self.root)

    def disconnect_device(self):
        if self.auto_read_enabled:
            self.stop_auto_read()
        if self.instrument:
            try:
                self.instrument.serial.close()
            except:
                pass
            self.instrument = None
        self.is_connected = False
        self.connect_btn.config(text="连接设备", bg="SystemButtonFace", fg="black")
        self.auto_read_btn.config(state=tk.DISABLED, text="启动自动读取")
        self.reset_btn.config(state=tk.DISABLED)
        self.status_var.set("已断开连接")
        for var in self.param_vars.values():
            var.set("")
        self.log_message("已断开设备连接")

    def get_float_order_code(self):
        order_map = {
            ">ABCD (大端)": minimalmodbus.BYTEORDER_BIG,
            "<DCBA (小端)": minimalmodbus.BYTEORDER_LITTLE,
            ">BADC (大端字交换)": minimalmodbus.BYTEORDER_BIG_SWAP,
            "<CDAB (小端字交换)": minimalmodbus.BYTEORDER_LITTLE_SWAP,
        }
        return order_map.get(self.byteorder_var.get(), minimalmodbus.BYTEORDER_LITTLE_SWAP)

    def read_param(self, address, var, name, silent=False):
        if not self.is_connected or self.instrument is None:
            if not silent:
                messagebox.showerror("错误", "请先连接设备", parent=self.root)
            return False
        if not silent:
            self.log_message(f"----- 读取 {name} (地址0x{address:04X}) -----")
        try:
            value = self.instrument.read_float(address, number_of_registers=2, byteorder=self.get_float_order_code())
            var.set(f"{value:.4f}")
            if not silent:
                self.status_var.set(f"读取{name}成功: {value:.4f}")
                self.log_message(f"读取结果: {value:.4f}")
            return True
        except Exception as e:
            if not silent:
                self.status_var.set(f"读取{name}失败")
                self.log_message(f"读取异常: {str(e)}")
                messagebox.showerror("读取错误", f"读取{name}失败:\n{str(e)}", parent=self.root)
            else:
                self.log_message(f"自动读取 {name} 失败: {str(e)}")
            return False
        finally:
            if not silent:
                self.log_message(f"----- 读取结束 -----")

    def write_param(self, address, var, name):
        if not self.is_connected or self.instrument is None:
            messagebox.showerror("错误", "请先连接设备", parent=self.root)
            return
        value_str = var.get().strip()
        if not value_str:
            messagebox.showerror("错误", f"请输入{name}的值", parent=self.root)
            return
        try:
            new_value = float(value_str)
        except ValueError:
            messagebox.showerror("错误", f"{name}的值必须是数字", parent=self.root)
            return

        self.log_message(f"----- 开始写入 {name} = {new_value} (地址0x{address:04X}) -----")
        try:
            self.instrument.write_float(address, new_value, number_of_registers=2, byteorder=self.get_float_order_code())
            self.log_message("写入命令已发送，开始验证...")
            verify_value = self.instrument.read_float(address, number_of_registers=2, byteorder=self.get_float_order_code())
            if abs(verify_value - new_value) < 0.0001:
                self.status_var.set(f"{name}写入并验证成功: {verify_value:.4f}")
                self.log_message(f"验证成功，当前{name} = {verify_value:.4f}")
                messagebox.showinfo("成功", f"{name}已修改为 {new_value:.4f}\n验证读取值为 {verify_value:.4f}", parent=self.root)
                self.refresh_all_params()
            else:
                self.status_var.set(f"{name}写入后验证不一致")
                self.log_message(f"验证不一致！期望 {new_value:.4f}，实际 {verify_value:.4f}")
                messagebox.showwarning("警告", f"{name}写入命令已发送，但验证读取值不一致！\n期望: {new_value:.4f}\n实际: {verify_value:.4f}", parent=self.root)
                self.refresh_all_params()
            var.set(f"{verify_value:.4f}")
        except Exception as e:
            self.status_var.set(f"{name}写入失败")
            self.log_message(f"写入异常: {str(e)}")
            messagebox.showerror("写入错误", f"写入{name}失败:\n{str(e)}", parent=self.root)
        self.log_message(f"----- 写入结束 -----")

    def reset_device(self):
        if not self.is_connected or self.instrument is None:
            messagebox.showerror("错误", "请先连接设备", parent=self.root)
            return
        if not messagebox.askyesno("确认复位", "确定要复位设备吗？复位操作会重启设备。", parent=self.root):
            return
        self.log_message("----- 开始复位设备 (地址0x1049, 写入1) -----")
        try:
            self.instrument.write_register(0x1049, 1, functioncode=6)
            self.log_message("复位命令已发送")
            self.status_var.set("复位命令已发送")
            messagebox.showinfo("复位", "复位命令已发送，设备将重启。", parent=self.root)
            self.root.after(3000, self.refresh_all_params)
        except Exception as e:
            self.status_var.set("复位失败")
            self.log_message(f"复位异常: {str(e)}")
            messagebox.showerror("复位错误", f"复位设备失败:\n{str(e)}", parent=self.root)
        self.log_message("----- 复位结束 -----")

    def refresh_all_params(self):
        if not self.is_connected or self.instrument is None:
            return
        self.log_message("刷新所有参数...")
        success_count = 0
        for name, addr, unit in self.params:
            var = self.param_vars[addr]
            if self.read_param(addr, var, name, silent=True):
                success_count += 1
        self.log_message(f"刷新完成: {success_count}/{len(self.params)} 成功")
        self.status_var.set(f"参数已刷新 ({success_count}个成功)")

    def toggle_auto_read(self):
        if self.auto_read_enabled:
            self.stop_auto_read()
        else:
            self.start_auto_read()

    def start_auto_read(self):
        if not self.is_connected:
            messagebox.showerror("错误", "请先连接设备", parent=self.root)
            return
        self.auto_read_enabled = True
        self.auto_read_btn.config(text="停止自动读取", bg="lightcoral")
        self.log_message("自动读取已启动，每2秒读取所有参数")
        self.schedule_auto_read()

    def stop_auto_read(self):
        self.auto_read_enabled = False
        if self.auto_read_id:
            self.root.after_cancel(self.auto_read_id)
            self.auto_read_id = None
        self.auto_read_btn.config(text="启动自动读取", bg="SystemButtonFace")
        self.log_message("自动读取已停止")

    def schedule_auto_read(self):
        if self.auto_read_enabled and self.is_connected:
            self.auto_read_all()
            self.auto_read_id = self.root.after(2000, self.schedule_auto_read)

    def auto_read_all(self):
        if not self.is_connected:
            if self.auto_read_enabled:
                self.stop_auto_read()
            return
        self.log_message("自动读取: 开始读取所有参数")
        success_count = 0
        for name, addr, unit in self.params:
            var = self.param_vars[addr]
            if self.read_param(addr, var, name, silent=True):
                success_count += 1
        self.log_message(f"自动读取完成: {success_count}/{len(self.params)} 成功")
        self.status_var.set(f"自动读取完成: {success_count}个参数更新")

    def on_closing(self):
        if self.auto_read_enabled:
            self.stop_auto_read()
        if self.instrument:
            try:
                self.instrument.serial.close()
            except:
                pass
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ModbusApp(root)
    root.mainloop()