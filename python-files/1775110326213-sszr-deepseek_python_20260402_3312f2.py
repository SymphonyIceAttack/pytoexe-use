import sys
import struct
import csv
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusException
import serial.tools.list_ports

class ADLMeter:
    """ADL系列电能表通信类（支持ADL200N-CT / ADL400N-CT）"""
    # 寄存器地址（十六进制转十进制）
    FAST_REG = {
        'U_A': 0x2100, 'U_B': 0x2102, 'U_C': 0x2104,
        'U_AB': 0x2106, 'U_BC': 0x2108, 'U_CA': 0x210A,
        'I_A': 0x210C, 'I_B': 0x210E, 'I_C': 0x2110, 'I_N': 0x2112,
        'P_A': 0x2114, 'P_B': 0x2116, 'P_C': 0x2118, 'P_tot': 0x211A,
        'Q_A': 0x211C, 'Q_B': 0x211E, 'Q_C': 0x2120, 'Q_tot': 0x2122,
        'S_A': 0x2124, 'S_B': 0x2126, 'S_C': 0x2128, 'S_tot': 0x212A,
        'PF_A': 0x212C, 'PF_B': 0x212E, 'PF_C': 0x2130, 'PF_tot': 0x2132,
        'Freq': 0x2134
    }
    ENERGY_REG = {
        '总有功电能': 0x3000,
        '正向有功电能': 0x3004,
        '反向有功电能': 0x3008,
        '总无功电能': 0x300C,
        '正向无功电能': 0x3010,
        '反向无功电能': 0x3014,
        '视在电能': 0x3018
    }
    # 仪表信息寄存器（地址、型号识别用）
    ADDR_REG = 0x1000      # 从站地址
    MODEL_HINT_REG = 0x1010  # 网络选择，可辅助判断型号（3P4L/3P3L）

    def __init__(self, port, slave_id, baudrate=9600, timeout=1):
        self.client = ModbusSerialClient(
            method='rtu',
            port=port,
            baudrate=baudrate,
            stopbits=1,
            bytesize=8,
            parity='N',
            timeout=timeout
        )
        self.slave_id = slave_id

    def connect(self):
        return self.client.connect()

    def close(self):
        self.client.close()

    def _read_registers(self, addr, count):
        """读取保持寄存器，返回寄存器列表或None"""
        try:
            result = self.client.read_holding_registers(addr, count, slave=self.slave_id)
            if result.isError():
                return None
            return result.registers
        except ModbusException:
            return None

    def _write_registers(self, addr, values):
        """写入多个保持寄存器"""
        try:
            result = self.client.write_registers(addr, values, slave=self.slave_id)
            return not result.isError()
        except ModbusException:
            return False

    def read_float(self, addr):
        regs = self._read_registers(addr, 2)
        if regs is None:
            return None
        data = struct.pack('>HH', regs[0], regs[1])
        return struct.unpack('>f', data)[0]

    def read_double(self, addr):
        regs = self._read_registers(addr, 4)
        if regs is None:
            return None
        data = struct.pack('>HHHH', regs[0], regs[1], regs[2], regs[3])
        return struct.unpack('>d', data)[0]

    def read_slave_address(self):
        """读取仪表当前设置的从站地址"""
        regs = self._read_registers(self.ADDR_REG, 1)
        if regs:
            return regs[0]
        return None

    def write_slave_address(self, new_addr):
        """修改从站地址（谨慎使用）"""
        return self._write_registers(self.ADDR_REG, [new_addr])

    def read_all_fast(self):
        data = {}
        for name, addr in self.FAST_REG.items():
            value = self.read_float(addr)
            if value is None:
                data[name] = None
            else:
                # 格式化显示
                if name.startswith('U'):
                    data[name] = f"{value:.1f} V"
                elif name.startswith('I'):
                    data[name] = f"{value:.2f} A"
                elif name.startswith('P'):
                    data[name] = f"{value:.3f} kW"
                elif name.startswith('Q'):
                    data[name] = f"{value:.3f} kvar"
                elif name.startswith('S'):
                    data[name] = f"{value:.3f} kVA"
                elif name.startswith('PF'):
                    data[name] = f"{value:.3f}"
                elif name == 'Freq':
                    data[name] = f"{value:.2f} Hz"
                else:
                    data[name] = str(value)
        return data

    def read_all_energy(self):
        data = {}
        for name, addr in self.ENERGY_REG.items():
            value = self.read_double(addr)
            data[name] = f"{value:.3f}" if value is not None else None
        return data

    def clear_energy(self):
        """尝试将电能寄存器清零（仅当寄存器可写时有效）"""
        success = True
        for name, addr in self.ENERGY_REG.items():
            # 64位浮点数0的4个寄存器全为0
            ok = self._write_registers(addr, [0, 0, 0, 0])
            if not ok:
                success = False
        return success

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("ADL系列电能表数据读取软件（增强版）")
        self.root.geometry("900x700")
        self.meter = None
        self.running = False
        self.auto_timer = None
        self.record_file = None
        self.record_enabled = False
        self.record_lock = threading.Lock()

        # 配置区域
        config_frame = ttk.LabelFrame(root, text="通信配置", padding=10)
        config_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(config_frame, text="串口:").grid(row=0, column=0, sticky='w')
        self.port_combo = ttk.Combobox(config_frame, values=self.get_serial_ports(), width=15)
        self.port_combo.grid(row=0, column=1, padx=5)
        self.port_combo.bind('<FocusIn>', lambda e: self.refresh_ports())

        ttk.Label(config_frame, text="从站地址:").grid(row=0, column=2, sticky='w')
        self.slave_entry = ttk.Entry(config_frame, width=8)
        self.slave_entry.insert(0, "1")
        self.slave_entry.grid(row=0, column=3, padx=5)

        ttk.Label(config_frame, text="波特率:").grid(row=0, column=4, sticky='w')
        self.baud_combo = ttk.Combobox(config_frame, values=[1200,2400,4800,9600,19200,38400], width=8)
        self.baud_combo.set(9600)
        self.baud_combo.grid(row=0, column=5, padx=5)

        ttk.Label(config_frame, text="仪表型号:").grid(row=0, column=6, sticky='w')
        self.model_combo = ttk.Combobox(config_frame, values=["ADL200N-CT", "ADL400N-CT"], width=12)
        self.model_combo.set("ADL400N-CT")
        self.model_combo.grid(row=0, column=7, padx=5)

        self.connect_btn = ttk.Button(config_frame, text="连接", command=self.connect_meter)
        self.connect_btn.grid(row=0, column=8, padx=5)

        self.detect_btn = ttk.Button(config_frame, text="自动检测", command=self.auto_detect)
        self.detect_btn.grid(row=0, column=9, padx=5)

        # 刷新间隔设置
        interval_frame = ttk.Frame(config_frame)
        interval_frame.grid(row=1, column=0, columnspan=10, pady=5, sticky='w')
        ttk.Label(interval_frame, text="刷新间隔(ms):").pack(side='left')
        self.interval_var = tk.IntVar(value=1000)
        self.interval_spin = ttk.Spinbox(interval_frame, from_=500, to=10000, increment=100, textvariable=self.interval_var, width=6)
        self.interval_spin.pack(side='left', padx=5)
        ttk.Label(interval_frame, text="(建议≥1000)").pack(side='left')

        # 实时记录区域
        record_frame = ttk.LabelFrame(root, text="实时记录保存", padding=10)
        record_frame.pack(fill='x', padx=10, pady=5)
        self.record_var = tk.BooleanVar(value=False)
        self.record_check = ttk.Checkbutton(record_frame, text="启用实时记录", variable=self.record_var, command=self.toggle_record)
        self.record_check.pack(side='left', padx=5)
        self.record_path_var = tk.StringVar()
        self.record_entry = ttk.Entry(record_frame, textvariable=self.record_path_var, width=50, state='readonly')
        self.record_entry.pack(side='left', padx=5)
        self.record_browse_btn = ttk.Button(record_frame, text="选择文件", command=self.choose_record_file, state='disabled')
        self.record_browse_btn.pack(side='left', padx=5)

        # 数据显示区域（Notebook）
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)

        self.realtime_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.realtime_frame, text="实时数据")
        self.create_realtime_display()

        self.energy_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.energy_frame, text="电能累计")
        self.create_energy_display()

        # 控制按钮区域
        btn_frame = ttk.Frame(root)
        btn_frame.pack(fill='x', padx=10, pady=5)

        self.read_btn = ttk.Button(btn_frame, text="读取一次", command=self.read_once, state='disabled')
        self.read_btn.pack(side='left', padx=5)

        self.auto_read_btn = ttk.Button(btn_frame, text="开始连续读取", command=self.toggle_auto_read, state='disabled')
        self.auto_read_btn.pack(side='left', padx=5)

        self.export_btn = ttk.Button(btn_frame, text="导出当前数据", command=self.export_data, state='disabled')
        self.export_btn.pack(side='left', padx=5)

        self.clear_display_btn = ttk.Button(btn_frame, text="清除数据显示", command=self.clear_display_data, state='disabled')
        self.clear_display_btn.pack(side='left', padx=5)

        self.reset_energy_btn = ttk.Button(btn_frame, text="复位仪表电能(尝试)", command=self.reset_energy, state='disabled')
        self.reset_energy_btn.pack(side='left', padx=5)

        self.status_var = tk.StringVar(value="未连接")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken', anchor='w')
        status_bar.pack(fill='x', side='bottom')

    def get_serial_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports if ports else ["COM1", "COM2", "/dev/ttyUSB0", "/dev/ttyS0"]

    def refresh_ports(self):
        self.port_combo['values'] = self.get_serial_ports()

    def auto_detect(self):
        """自动检测：遍历串口、波特率、地址，找到第一个能正常通信的设备"""
        self.detect_btn.config(state='disabled', text='检测中...')
        def detect_task():
            found = None
            ports = self.get_serial_ports()
            baudrates = [9600, 19200, 38400, 4800, 2400, 1200]
            # 地址范围 1-10
            for port in ports:
                for baud in baudrates:
                    for addr in range(1, 11):
                        meter = ADLMeter(port, addr, baudrate=baud, timeout=0.5)
                        if meter.connect():
                            # 尝试读取电压寄存器（A相）
                            volt = meter.read_float(0x2100)
                            if volt is not None and 0 < volt < 500:
                                # 进一步读取从站地址确认
                                actual_addr = meter.read_slave_address()
                                if actual_addr is not None:
                                    addr = actual_addr
                                # 判断型号：尝试读B、C相电压
                                model = "ADL400N-CT"
                                volt_b = meter.read_float(0x2102)
                                volt_c = meter.read_float(0x2104)
                                if volt_b is None and volt_c is None:
                                    model = "ADL200N-CT"
                                found = (port, baud, addr, model)
                                meter.close()
                                break
                            meter.close()
                    if found:
                        break
                if found:
                    break
            self.root.after(0, self.on_detect_complete, found)
        threading.Thread(target=detect_task, daemon=True).start()

    def on_detect_complete(self, found):
        self.detect_btn.config(state='normal', text='自动检测')
        if found:
            port, baud, addr, model = found
            self.port_combo.set(port)
            self.baud_combo.set(str(baud))
            self.slave_entry.delete(0, tk.END)
            self.slave_entry.insert(0, str(addr))
            self.model_combo.set(model)
            messagebox.showinfo("检测成功", f"发现设备: {model}\n串口: {port} 波特率: {baud} 地址: {addr}")
            # 自动连接
            self.connect_meter()
        else:
            messagebox.showwarning("检测失败", "未检测到任何ADL电能表，请检查接线和供电")

    def connect_meter(self):
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("错误", "请选择串口")
            return
        try:
            slave = int(self.slave_entry.get())
            baud = int(self.baud_combo.get())
        except ValueError:
            messagebox.showerror("错误", "从站地址和波特率必须为整数")
            return

        if self.meter:
            self.disconnect_meter()
        self.meter = ADLMeter(port, slave, baud)
        if self.meter.connect():
            # 验证通信
            test_val = self.meter.read_float(0x2100)
            if test_val is None:
                self.meter.close()
                self.meter = None
                messagebox.showerror("错误", "连接成功但读取失败，请检查参数或接线")
                return
            self.status_var.set(f"已连接 {port} 地址{slave} 波特率{baud}")
            self.read_btn.config(state='normal')
            self.auto_read_btn.config(state='normal')
            self.export_btn.config(state='normal')
            self.clear_display_btn.config(state='normal')
            self.reset_energy_btn.config(state='normal')
            self.connect_btn.config(text="断开", command=self.disconnect_meter)
            self.record_browse_btn.config(state='normal')
            self.read_once()
        else:
            messagebox.showerror("错误", f"无法连接 {port}，请检查参数和硬件")
            self.meter = None

    def disconnect_meter(self):
        if self.auto_timer:
            self.root.after_cancel(self.auto_timer)
            self.auto_timer = None
            self.auto_read_btn.config(text="开始连续读取")
            self.running = False
        if self.meter:
            self.meter.close()
            self.meter = None
        self.status_var.set("未连接")
        self.read_btn.config(state='disabled')
        self.auto_read_btn.config(state='disabled')
        self.export_btn.config(state='disabled')
        self.clear_display_btn.config(state='disabled')
        self.reset_energy_btn.config(state='disabled')
        self.record_browse_btn.config(state='disabled')
        self.record_var.set(False)
        self.toggle_record()
        self.connect_btn.config(text="连接", command=self.connect_meter)

    def create_realtime_display(self):
        columns = ('参数', '数值')
        self.realtime_tree = ttk.Treeview(self.realtime_frame, columns=columns, show='headings', height=20)
        self.realtime_tree.heading('参数', text='参数')
        self.realtime_tree.heading('数值', text='数值')
        self.realtime_tree.column('参数', width=150)
        self.realtime_tree.column('数值', width=200)
        # 参数列表（根据型号动态显示，此处全部创建，更新时按型号过滤）
        self.realtime_params = [
            'U_A', 'U_B', 'U_C', 'U_AB', 'U_BC', 'U_CA',
            'I_A', 'I_B', 'I_C', 'I_N',
            'P_A', 'P_B', 'P_C', 'P_tot',
            'Q_A', 'Q_B', 'Q_C', 'Q_tot',
            'S_A', 'S_B', 'S_C', 'S_tot',
            'PF_A', 'PF_B', 'PF_C', 'PF_tot',
            'Freq'
        ]
        for param in self.realtime_params:
            self.realtime_tree.insert('', 'end', iid=param, values=(param, '--'))
        scrollbar = ttk.Scrollbar(self.realtime_frame, orient='vertical', command=self.realtime_tree.yview)
        self.realtime_tree.configure(yscrollcommand=scrollbar.set)
        self.realtime_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def create_energy_display(self):
        columns = ('参数', '数值 (kWh/kvarh/kVAh)')
        self.energy_tree = ttk.Treeview(self.energy_frame, columns=columns, show='headings', height=10)
        self.energy_tree.heading('参数', text='参数')
        self.energy_tree.heading('数值', text='数值')
        self.energy_tree.column('参数', width=150)
        self.energy_tree.column('数值', width=200)
        self.energy_params = [
            '总有功电能', '正向有功电能', '反向有功电能',
            '总无功电能', '正向无功电能', '反向无功电能',
            '视在电能'
        ]
        for param in self.energy_params:
            self.energy_tree.insert('', 'end', iid=param, values=(param, '--'))
        scrollbar = ttk.Scrollbar(self.energy_frame, orient='vertical', command=self.energy_tree.yview)
        self.energy_tree.configure(yscrollcommand=scrollbar.set)
        self.energy_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def read_once(self):
        if not self.meter:
            return
        def task():
            try:
                real_data = self.meter.read_all_fast()
                energy_data = self.meter.read_all_energy()
                # 获取当前型号，过滤显示
                model = self.model_combo.get()
                self.root.after(0, self.update_display, real_data, energy_data, model)
                # 实时记录
                if self.record_enabled and self.record_file:
                    self.append_to_record(real_data, energy_data)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"读取失败: {e}"))
        threading.Thread(target=task, daemon=True).start()

    def update_display(self, real_data, energy_data, model):
        # 实时数据
        for param, value in real_data.items():
            if self.realtime_tree.exists(param):
                # 根据型号隐藏不存在的相
                if model == "ADL200N-CT" and param not in ['U_A','I_A','P_A','Q_A','S_A','PF_A','Freq','P_tot','Q_tot','S_tot','PF_tot']:
                    self.realtime_tree.set(param, '数值', '仅A相有效')
                else:
                    self.realtime_tree.set(param, '数值', value if value is not None else '读取失败')
        # 电能数据
        for param, value in energy_data.items():
            if self.energy_tree.exists(param):
                self.energy_tree.set(param, '数值', value if value is not None else '读取失败')
        self.status_var.set(f"最后读取: {time.strftime('%H:%M:%S')}")

    def toggle_auto_read(self):
        if self.auto_timer:
            self.root.after_cancel(self.auto_timer)
            self.auto_timer = None
            self.auto_read_btn.config(text="开始连续读取")
            self.running = False
        else:
            self.running = True
            self.auto_read_loop()
            self.auto_read_btn.config(text="停止连续读取")

    def auto_read_loop(self):
        if self.running and self.meter:
            self.read_once()
            interval = max(500, self.interval_var.get())
            self.auto_timer = self.root.after(interval, self.auto_read_loop)
        else:
            self.auto_timer = None

    def toggle_record(self):
        self.record_enabled = self.record_var.get()
        if self.record_enabled:
            if not self.record_path_var.get():
                self.choose_record_file()
                if not self.record_path_var.get():
                    self.record_var.set(False)
                    self.record_enabled = False
                    return
            # 打开文件准备写入（追加模式）
            try:
                self.record_file = open(self.record_path_var.get(), 'a', newline='', encoding='utf-8-sig')
                # 如果文件为空，写入表头
                if self.record_file.tell() == 0:
                    writer = csv.writer(self.record_file)
                    header = ['时间戳'] + self.realtime_params + self.energy_params
                    writer.writerow(header)
                self.status_var.set("实时记录已启用")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开记录文件: {e}")
                self.record_var.set(False)
                self.record_enabled = False
        else:
            if self.record_file:
                self.record_file.close()
                self.record_file = None
            self.status_var.set("实时记录已停止")

    def choose_record_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if file_path:
            self.record_path_var.set(file_path)
            if self.record_enabled:
                # 重新打开文件
                if self.record_file:
                    self.record_file.close()
                self.record_file = open(file_path, 'a', newline='', encoding='utf-8-sig')

    def append_to_record(self, real_data, energy_data):
        with self.record_lock:
            if not self.record_file or self.record_file.closed:
                return
            writer = csv.writer(self.record_file)
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            row = [timestamp]
            # 实时数据按顺序
            for param in self.realtime_params:
                val = real_data.get(param, '')
                if val is None:
                    val = ''
                row.append(val)
            for param in self.energy_params:
                val = energy_data.get(param, '')
                if val is None:
                    val = ''
                row.append(val)
            writer.writerow(row)
            self.record_file.flush()

    def export_data(self):
        if not self.meter:
            messagebox.showwarning("警告", "未连接仪表")
            return
        # 收集当前显示数据
        real_data = {}
        for param in self.realtime_params:
            val = self.realtime_tree.set(param, '数值')
            real_data[param] = val if val != '--' else ''
        energy_data = {}
        for param in self.energy_params:
            val = self.energy_tree.set(param, '数值')
            energy_data[param] = val if val != '--' else ''
        if not any(real_data.values()) and not any(energy_data.values()):
            messagebox.showwarning("警告", "没有有效数据可导出，请先读取")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV文件", "*.csv")])
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(["实时数据"])
                writer.writerow(["参数", "数值"])
                for param, value in real_data.items():
                    writer.writerow([param, value])
                writer.writerow([])
                writer.writerow(["电能累计数据"])
                writer.writerow(["参数", "数值 (kWh/kvarh/kVAh)"])
                for param, value in energy_data.items():
                    writer.writerow([param, value])
            messagebox.showinfo("成功", f"数据已导出到 {file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

    def clear_display_data(self):
        """仅清除界面显示的数据，不影响仪表"""
        for param in self.realtime_params:
            if self.realtime_tree.exists(param):
                self.realtime_tree.set(param, '数值', '--')
        for param in self.energy_params:
            if self.energy_tree.exists(param):
                self.energy_tree.set(param, '数值', '--')
        self.status_var.set("界面数据已清除")

    def reset_energy(self):
        """尝试将仪表内部电能寄存器清零（可能不支持）"""
        if not self.meter:
            return
        if not messagebox.askyesno("确认", "此操作将尝试复位仪表内部累计电能，可能不被仪表支持。\n是否继续？"):
            return
        def task():
            success = self.meter.clear_energy()
            self.root.after(0, lambda: self.on_reset_result(success))
        threading.Thread(target=task, daemon=True).start()

    def on_reset_result(self, success):
        if success:
            messagebox.showinfo("成功", "电能寄存器已复位（若仪表支持）\n请重新读取数据确认")
            self.read_once()
        else:
            messagebox.showerror("失败", "复位失败，该仪表可能不支持写电能寄存器。\n请使用仪表本身的按键或软件进行清零。")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()