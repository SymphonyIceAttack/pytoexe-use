import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
import socket
import time
import threading
import json
import os
import random
import re
from datetime import datetime

# ========== 配置 ==========
# 配置文件直接保存在程序所在目录（不依赖系统权限）
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
NETWORK_FILE = os.path.join(CONFIG_DIR, "network.json")
RTU_FILE = os.path.join(CONFIG_DIR, "rtu_list.json")
TIMESYNC_FILE = os.path.join(CONFIG_DIR, "timesync.json")

DEFAULT_TEMPLATE = ("*(01{STATION}0068AA32B600K ST {STATION} TT {TT} PN05 {RAIN} Z {LEVEL} "
                    "PJ 0.0 PT 121.0 PN10 0.0 P1 0.0 VT 11.66 0D{SEQ})")

class RtuSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("河南水库RTU模拟器 - 多机版 (模板可配置)")
        self.root.geometry("1050x820")
        
        # 数据
        self.rtu_list = []
        self.running = False
        self.timers = {}
        self.selected_id = None
        
        # 校时
        self.timesync_enabled = False
        self.timesync_interval = 3600
        self.timesync_template = "*({STATION} TIME {TT} {RANDOM:6})"
        self.timesync_station = "417K0018"
        self.last_sync_time = None
        self.sync_result = "未校时"
        self.sync_timer = None
        
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.load_network()
        self.load_rtu_list()
        self.load_timesync()
        
        self.build_ui()
        self.refresh_table()
        self.log("程序启动，就绪。")
        self.log(f"加载了 {len(self.rtu_list)} 个RTU配置。")
        self.update_sync_status()
    
    # ========== UI构建 ==========
    def build_ui(self):
        # ---- 顶部：网络参数 ----
        frame_net = tk.LabelFrame(self.root, text="网络参数", padx=5, pady=5)
        frame_net.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame_net, text="服务器:").grid(row=0, column=0, sticky="e")
        self.entry_host = tk.Entry(frame_net, width=30)
        self.entry_host.grid(row=0, column=1, padx=5)
        self.entry_host.insert(0, self.host)
        
        tk.Label(frame_net, text="端口:").grid(row=0, column=2, sticky="e")
        self.entry_port = tk.Entry(frame_net, width=8)
        self.entry_port.grid(row=0, column=3, padx=5)
        self.entry_port.insert(0, str(self.port))
        
        tk.Button(frame_net, text="保存网络参数", command=self.save_network).grid(row=0, column=4, padx=10)
        tk.Button(frame_net, text="手动发送全部", command=self.manual_send_all).grid(row=0, column=5, padx=5)
        tk.Button(frame_net, text="手动发送选中", command=self.manual_send_selected).grid(row=0, column=6, padx=5)
        
        # ---- 校时配置 ----
        frame_sync = tk.LabelFrame(self.root, text="校时配置 (公共)", padx=5, pady=5)
        frame_sync.pack(fill="x", padx=10, pady=5)
        
        row_sync1 = tk.Frame(frame_sync)
        row_sync1.pack(fill="x", pady=2)
        self.sync_enabled_var = tk.IntVar(value=1 if self.timesync_enabled else 0)
        tk.Checkbutton(row_sync1, text="启用校时", variable=self.sync_enabled_var, command=self.on_sync_enable_toggle).pack(side="left", padx=5)
        tk.Label(row_sync1, text="校时间隔(秒):").pack(side="left", padx=5)
        self.entry_sync_interval = tk.Entry(row_sync1, width=8)
        self.entry_sync_interval.pack(side="left", padx=5)
        self.entry_sync_interval.insert(0, str(self.timesync_interval))
        tk.Label(row_sync1, text="校时站址:").pack(side="left", padx=5)
        self.entry_sync_station = tk.Entry(row_sync1, width=14)
        self.entry_sync_station.pack(side="left", padx=5)
        self.entry_sync_station.insert(0, self.timesync_station)
        tk.Button(row_sync1, text="立即校时", command=self.manual_sync).pack(side="left", padx=10)
        
        row_sync2 = tk.Frame(frame_sync)
        row_sync2.pack(fill="x", pady=2)
        tk.Label(row_sync2, text="校时请求模板:").pack(anchor="w", padx=5)
        self.sync_template_text = scrolledtext.ScrolledText(frame_sync, height=2, wrap=tk.NONE, font=("Consolas", 10))
        self.sync_template_text.pack(fill="x", pady=2, padx=5)
        self.sync_template_text.insert(tk.END, self.timesync_template)
        
        self.sync_status_label = tk.Label(frame_sync, text="上次校时: 未进行", fg="#8ab4e8")
        self.sync_status_label.pack(anchor="w", padx=5, pady=2)
        
        # ---- RTU表格 ----
        frame_table = tk.LabelFrame(self.root, text="RTU列表", padx=5, pady=5)
        frame_table.pack(fill="both", expand=True, padx=10, pady=5)
        
        columns = ("id", "name", "station", "rainfall", "water_level", "auto", "interval")
        self.tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=6)
        self.tree.heading("id", text="序号")
        self.tree.heading("name", text="名称")
        self.tree.heading("station", text="测站编码")
        self.tree.heading("rainfall", text="雨量 (mm)")
        self.tree.heading("water_level", text="水位 (m)")
        self.tree.heading("auto", text="自动变化")
        self.tree.heading("interval", text="间隔(秒)")
        self.tree.column("id", width=50)
        self.tree.column("name", width=100)
        self.tree.column("station", width=120)
        self.tree.column("rainfall", width=80)
        self.tree.column("water_level", width=80)
        self.tree.column("auto", width=70)
        self.tree.column("interval", width=80)
        
        scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # ---- 编辑区域 ----
        frame_edit = tk.LabelFrame(self.root, text="编辑选中RTU", padx=5, pady=5)
        frame_edit.pack(fill="x", padx=10, pady=5)
        
        row1 = tk.Frame(frame_edit)
        row1.pack(fill="x", pady=2)
        tk.Label(row1, text="名称:").pack(side="left", padx=2)
        self.entry_edit_name = tk.Entry(row1, width=12)
        self.entry_edit_name.pack(side="left", padx=2)
        tk.Label(row1, text="站址:").pack(side="left", padx=2)
        self.entry_edit_station = tk.Entry(row1, width=14)
        self.entry_edit_station.pack(side="left", padx=2)
        tk.Label(row1, text="雨量:").pack(side="left", padx=2)
        self.entry_edit_rain = tk.Entry(row1, width=8)
        self.entry_edit_rain.pack(side="left", padx=2)
        tk.Label(row1, text="水位:").pack(side="left", padx=2)
        self.entry_edit_level = tk.Entry(row1, width=10)
        self.entry_edit_level.pack(side="left", padx=2)
        self.auto_var = tk.IntVar()
        tk.Checkbutton(row1, text="自动变化", variable=self.auto_var).pack(side="left", padx=5)
        tk.Label(row1, text="间隔(秒):").pack(side="left", padx=2)
        self.entry_edit_interval = tk.Entry(row1, width=8)
        self.entry_edit_interval.pack(side="left", padx=2)
        self.entry_edit_interval.insert(0, "3600")
        
        row2 = tk.Frame(frame_edit)
        row2.pack(fill="x", pady=5)
        tk.Label(row2, text="报文模板 (支持占位符: {STATION} {TT} {RAIN} {LEVEL} {SEQ} {RANDOM:n} {FIXED:值})").pack(anchor="w")
        self.template_text = scrolledtext.ScrolledText(frame_edit, height=4, wrap=tk.NONE, font=("Consolas", 10))
        self.template_text.pack(fill="x", pady=2)
        
        row3 = tk.Frame(frame_edit)
        row3.pack(fill="x", pady=2)
        tk.Button(row3, text="更新RTU", command=self.update_rtu).pack(side="left", padx=5)
        tk.Button(row3, text="恢复默认模板", command=self.reset_template).pack(side="left", padx=5)
        tk.Button(row3, text="测试模板", command=self.test_template).pack(side="left", padx=5)
        
        # ---- 底部按钮 ----
        frame_btn = tk.Frame(self.root)
        frame_btn.pack(fill="x", padx=10, pady=5)
        tk.Button(frame_btn, text="添加RTU", command=self.add_rtu).pack(side="left", padx=5)
        tk.Button(frame_btn, text="删除选中", command=self.delete_rtu).pack(side="left", padx=5)
        tk.Button(frame_btn, text="启动定时", command=self.start_all).pack(side="left", padx=5)
        tk.Button(frame_btn, text="停止定时", command=self.stop_all).pack(side="left", padx=5)
        tk.Button(frame_btn, text="保存配置", command=self.save_all_config).pack(side="left", padx=5)
        
        # ---- 日志 ----
        frame_log = tk.LabelFrame(self.root, text="日志", padx=5, pady=5)
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(frame_log, height=10, state="normal")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.config(state="disabled")
        
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w")
        status_bar.pack(fill="x", padx=10, pady=5)
    
    # ========== 配置读写 ==========
    def load_network(self):
        if os.path.exists(NETWORK_FILE):
            with open(NETWORK_FILE, 'r') as f:
                net = json.load(f)
                self.host = net.get("host", "data.skaqjc.com")
                self.port = net.get("port", 9888)
        else:
            self.host = "data.skaqjc.com"
            self.port = 9888
    
    def save_network(self):
        self.host = self.entry_host.get().strip()
        self.port = int(self.entry_port.get().strip())
        with open(NETWORK_FILE, 'w') as f:
            json.dump({"host": self.host, "port": self.port}, f, indent=2)
        self.log("网络参数已保存")
    
    def load_rtu_list(self):
        if os.path.exists(RTU_FILE):
            with open(RTU_FILE, 'r') as f:
                self.rtu_list = json.load(f)
            for rtu in self.rtu_list:
                if "template" not in rtu:
                    rtu["template"] = DEFAULT_TEMPLATE
                if "seq" not in rtu:
                    rtu["seq"] = 0
        else:
            self.rtu_list = [{
                "id": 1,
                "name": "月山水库",
                "station": "417K0018",
                "rainfall": 0.0,
                "water_level": 110.232,
                "auto": True,
                "interval": 3600,
                "seq": 0,
                "template": DEFAULT_TEMPLATE
            }]
    
    def save_rtu_list(self):
        with open(RTU_FILE, 'w') as f:
            json.dump(self.rtu_list, f, indent=2)
    
    def save_all_config(self):
        self.save_rtu_list()
        self.save_network()
        self.save_timesync()
        self.log("所有配置已保存")
    
    # ========== 校时相关 ==========
    def load_timesync(self):
        if os.path.exists(TIMESYNC_FILE):
            with open(TIMESYNC_FILE, 'r') as f:
                data = json.load(f)
                self.timesync_enabled = data.get("enabled", False)
                self.timesync_interval = data.get("interval", 3600)
                self.timesync_template = data.get("template", "*({STATION} TIME {TT} {RANDOM:6})")
                self.timesync_station = data.get("station", "417K0018")
        else:
            self.timesync_enabled = False
            self.timesync_interval = 3600
            self.timesync_template = "*({STATION} TIME {TT} {RANDOM:6})"
            self.timesync_station = "417K0018"
    
    def save_timesync(self):
        data = {
            "enabled": self.timesync_enabled,
            "interval": self.timesync_interval,
            "template": self.timesync_template,
            "station": self.timesync_station
        }
        with open(TIMESYNC_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def on_sync_enable_toggle(self):
        self.timesync_enabled = bool(self.sync_enabled_var.get())
        if self.timesync_enabled:
            self.log("校时功能已启用")
            self.start_sync_timer()
        else:
            self.log("校时功能已禁用")
            if self.sync_timer:
                self.sync_timer.cancel()
                self.sync_timer = None
        self.save_timesync()
    
    def start_sync_timer(self):
        if self.sync_timer:
            self.sync_timer.cancel()
        if not self.timesync_enabled:
            return
        interval = self.get_sync_interval()
        self.sync_timer = threading.Timer(interval, self.sync_timer_callback)
        self.sync_timer.daemon = True
        self.sync_timer.start()
    
    def sync_timer_callback(self):
        self.root.after(0, self.do_sync)
        if self.timesync_enabled:
            self.start_sync_timer()
    
    def get_sync_interval(self):
        try:
            val = int(self.entry_sync_interval.get().strip())
            if val > 0:
                return val
        except:
            pass
        return self.timesync_interval
    
    def get_sync_station(self):
        station = self.entry_sync_station.get().strip()
        if station:
            return station
        return self.timesync_station
    
    def manual_sync(self):
        self.do_sync()
    
    def do_sync(self):
        if not self.timesync_enabled:
            self.log("校时功能未启用，无法校时", "warn")
            return
        station = self.get_sync_station()
        if not station:
            self.log("校时站址为空", "err")
            return
        template = self.sync_template_text.get(1.0, tk.END).strip()
        if not template:
            template = "*({STATION} TIME {TT} {RANDOM:6})"
        msg = self.build_message_from_template(template, station, 0, 0, seq=None, random_len=6)
        self.log(f"校时发送: {msg}", "info")
        reply = self.send_raw(msg)
        if reply:
            self.last_sync_time = datetime.now()
            self.sync_result = f"成功 (回复: {reply[:50]}...)"
            self.log(f"校时回复: {reply}", "rx")
        else:
            self.sync_result = "失败 (无回复或超时)"
        self.update_sync_status()
        self.save_timesync()
    
    def update_sync_status(self):
        if self.last_sync_time:
            time_str = self.last_sync_time.strftime("%Y-%m-%d %H:%M:%S")
            status = f"上次校时: {time_str} 结果: {self.sync_result}"
        else:
            status = "上次校时: 未进行"
        self.sync_status_label.config(text=status)
    
    # ========== 报文构造通用 ==========
    def build_message_from_template(self, template, station, rainfall, water_level, seq=None, random_len=4):
        now = datetime.now()
        tt = now.strftime("%y%m%d%H%M")
        if seq is None:
            seq_str = ''.join(random.choice('0123456789ABCDEF') for _ in range(4))
        else:
            seq_str = format(seq, '04X')
        def random_repl(match):
            n = int(match.group(1)) if match.group(1) else 4
            return ''.join(random.choice('0123456789ABCDEF') for _ in range(n))
        msg = template
        msg = msg.replace('{STATION}', station)
        msg = msg.replace('{TT}', tt)
        msg = msg.replace('{RAIN}', f"{rainfall:.1f}")
        msg = msg.replace('{LEVEL}', f"{water_level:.3f}")
        msg = msg.replace('{SEQ}', seq_str)
        msg = re.sub(r'\{RANDOM:(\d+)\}', random_repl, msg)
        msg = re.sub(r'\{RANDOM\}', lambda m: ''.join(random.choice('0123456789ABCDEF') for _ in range(4)), msg)
        msg = re.sub(r'\{FIXED:([^}]+)\}', r'\1', msg)
        return msg
    
    # ========== 网络发送通用 ==========
    def send_raw(self, msg):
        host = self.entry_host.get().strip()
        port = int(self.entry_port.get().strip())
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.sendall(msg.encode('ascii'))
            try:
                resp = sock.recv(1024)
                sock.close()
                if resp:
                    return resp.decode('ascii', errors='replace')
                else:
                    return None
            except socket.timeout:
                sock.close()
                return None
        except Exception as e:
            self.log(f"发送失败: {e}", "err")
            return None
    
    # ========== RTU相关 ==========
    def build_message_for_rtu(self, rtu):
        template = rtu.get("template", DEFAULT_TEMPLATE)
        if "seq" not in rtu:
            rtu["seq"] = 0
        rtu["seq"] = (rtu["seq"] + 1) % 65536
        return self.build_message_from_template(
            template,
            station=rtu["station"],
            rainfall=rtu["rainfall"],
            water_level=rtu["water_level"],
            seq=rtu["seq"],
            random_len=4
        )
    
    def send_rtu(self, rtu):
        msg = self.build_message_for_rtu(rtu)
        self.log(f"[{rtu['name']}] 发送: {msg}", "tx")
        reply = self.send_raw(msg)
        if reply:
            self.log(f"[{rtu['name']}] 回复: {reply}", "rx")
        else:
            self.log(f"[{rtu['name']}] 无回复或超时", "warn")
        self.save_rtu_list()
    
    # ========== 表格交互 ==========
    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for rtu in self.rtu_list:
            self.tree.insert("", "end", values=(
                rtu["id"],
                rtu["name"],
                rtu["station"],
                f"{rtu['rainfall']:.1f}",
                f"{rtu['water_level']:.3f}",
                "✓" if rtu["auto"] else "",
                rtu["interval"]
            ))
    
    def on_tree_select(self, event):
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self.tree.item(item, "values")
        rtu_id = int(values[0])
        for rtu in self.rtu_list:
            if rtu["id"] == rtu_id:
                self.selected_id = rtu_id
                self.entry_edit_name.delete(0, tk.END)
                self.entry_edit_name.insert(0, rtu["name"])
                self.entry_edit_station.delete(0, tk.END)
                self.entry_edit_station.insert(0, rtu["station"])
                self.entry_edit_rain.delete(0, tk.END)
                self.entry_edit_rain.insert(0, str(rtu["rainfall"]))
                self.entry_edit_level.delete(0, tk.END)
                self.entry_edit_level.insert(0, str(rtu["water_level"]))
                self.auto_var.set(1 if rtu["auto"] else 0)
                self.entry_edit_interval.delete(0, tk.END)
                self.entry_edit_interval.insert(0, str(rtu["interval"]))
                self.template_text.delete(1.0, tk.END)
                self.template_text.insert(tk.END, rtu.get("template", DEFAULT_TEMPLATE))
                break
    
    def update_rtu(self):
        if self.selected_id is None:
            messagebox.showwarning("警告", "请先在表格中选中一个RTU")
            return
        try:
            name = self.entry_edit_name.get().strip()
            station = self.entry_edit_station.get().strip()
            rainfall = float(self.entry_edit_rain.get())
            water_level = float(self.entry_edit_level.get())
            auto = bool(self.auto_var.get())
            interval = int(self.entry_edit_interval.get())
            if interval <= 0:
                raise ValueError
            template = self.template_text.get(1.0, tk.END).strip()
            if not template:
                template = DEFAULT_TEMPLATE
        except ValueError:
            messagebox.showerror("错误", "输入数据格式不正确，请检查数字和间隔")
            return
        for rtu in self.rtu_list:
            if rtu["id"] == self.selected_id:
                rtu["name"] = name
                rtu["station"] = station
                rtu["rainfall"] = rainfall
                rtu["water_level"] = water_level
                rtu["auto"] = auto
                rtu["interval"] = interval
                rtu["template"] = template
                break
        self.refresh_table()
        self.save_rtu_list()
        self.log(f"已更新RTU: {name}")
    
    def reset_template(self):
        if self.selected_id is None:
            messagebox.showwarning("警告", "请先选中一个RTU")
            return
        self.template_text.delete(1.0, tk.END)
        self.template_text.insert(tk.END, DEFAULT_TEMPLATE)
        self.log("已恢复默认模板")
    
    def test_template(self):
        if self.selected_id is None:
            messagebox.showwarning("警告", "请先选中一个RTU")
            return
        rtu = next((r for r in self.rtu_list if r["id"] == self.selected_id), None)
        if not rtu:
            return
        template = self.template_text.get(1.0, tk.END).strip()
        if not template:
            template = DEFAULT_TEMPLATE
        try:
            msg = self.build_message_from_template(
                template,
                station=rtu["station"],
                rainfall=rtu["rainfall"],
                water_level=rtu["water_level"],
                seq=0x1234,
                random_len=4
            )
            self.log(f"测试生成的报文: {msg}", "info")
            messagebox.showinfo("测试结果", f"生成的报文为:\n{msg}")
        except Exception as e:
            messagebox.showerror("模板错误", f"模板解析失败: {e}")
    
    def add_rtu(self):
        max_id = max([r["id"] for r in self.rtu_list]) if self.rtu_list else 0
        new_id = max_id + 1
        name = simpledialog.askstring("添加RTU", "请输入RTU名称:", initialvalue=f"RTU-{new_id}")
        if not name:
            return
        station = simpledialog.askstring("添加RTU", "请输入测站编码:", initialvalue="417K0018")
        if not station:
            return
        new_rtu = {
            "id": new_id,
            "name": name,
            "station": station,
            "rainfall": 0.0,
            "water_level": 100.0,
            "auto": False,
            "interval": 3600,
            "seq": 0,
            "template": DEFAULT_TEMPLATE
        }
        self.rtu_list.append(new_rtu)
        self.refresh_table()
        self.save_rtu_list()
        self.log(f"已添加RTU: {name} ({station})")
    
    def delete_rtu(self):
        if self.selected_id is None:
            messagebox.showwarning("警告", "请先在表格中选中一个RTU")
            return
        rtu = next((r for r in self.rtu_list if r["id"] == self.selected_id), None)
        if not rtu:
            return
        if messagebox.askyesno("确认删除", f"确定要删除RTU {rtu['name']} 吗？"):
            self.rtu_list = [r for r in self.rtu_list if r["id"] != self.selected_id]
            self.selected_id = None
            self.refresh_table()
            self.save_rtu_list()
            self.log(f"已删除RTU: {rtu['name']}")
    
    # ========== 手动发送 ==========
    def manual_send_all(self):
        if not self.rtu_list:
            self.log("没有RTU可发送", "warn")
            return
        for rtu in self.rtu_list:
            self.send_rtu(rtu)
            time.sleep(0.2)
    
    def manual_send_selected(self):
        if self.selected_id is None:
            messagebox.showwarning("警告", "请先选中一个RTU")
            return
        rtu = next((r for r in self.rtu_list if r["id"] == self.selected_id), None)
        if rtu:
            self.send_rtu(rtu)
    
    # ========== 自动变化 ==========
    def update_auto_data(self):
        for rtu in self.rtu_list:
            if rtu["auto"]:
                rtu["rainfall"] += random.uniform(-0.2, 0.5)
                if rtu["rainfall"] < 0:
                    rtu["rainfall"] = 0
                rtu["water_level"] += random.uniform(-0.02, 0.03)
                if rtu["water_level"] < 80:
                    rtu["water_level"] = 80
                if rtu["water_level"] > 120:
                    rtu["water_level"] = 120
        self.refresh_table()
        if self.running:
            self.root.after(10000, self.update_auto_data)
    
    # ========== 定时调度 ==========
    def start_all(self):
        if self.running:
            return
        self.running = True
        self.status_var.set("定时上报运行中")
        self.log("启动定时上报...")
        self.update_auto_data()
        for rtu in self.rtu_list:
            self.schedule_rtu(rtu)
        if self.timesync_enabled:
            self.start_sync_timer()
    
    def schedule_rtu(self, rtu):
        if not self.running:
            return
        interval = rtu["interval"]
        timer = threading.Timer(interval, self.timer_callback, [rtu])
        timer.daemon = True
        timer.start()
        self.timers[rtu["id"]] = timer
    
    def timer_callback(self, rtu):
        self.root.after(0, lambda: self.send_rtu(rtu))
        if self.running and rtu["id"] in [r["id"] for r in self.rtu_list]:
            self.schedule_rtu(rtu)
    
    def stop_all(self):
        self.running = False
        for timer in self.timers.values():
            timer.cancel()
        self.timers.clear()
        if self.sync_timer:
            self.sync_timer.cancel()
            self.sync_timer = None
        self.status_var.set("已停止")
        self.log("定时上报已停止")
    
    # ========== 日志 ==========
    def log(self, msg, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, line)
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()
    
    # ========== 窗口关闭 ==========
    def on_close(self):
        self.stop_all()
        self.save_all_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RtuSimulator(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()