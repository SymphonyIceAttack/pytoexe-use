#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CPU & GPU 监控工具 (nvidia-smi 版) - 美化界面版
=================================================
功能：
- 实时监控 CPU 使用率、每核使用率、频率、内存使用情况
- 实时监控 NVIDIA GPU 使用率、显存使用、温度（通过 nvidia-smi）
- CPU 跑分：计算 2~50000 之间的素数个数，给出分数
- GPU 详细信息：驱动版本、CUDA 版本、BIOS 版本、PCI 总线 ID
- 动态图表：最近 60 秒的 CPU 和 GPU 使用率曲线

依赖安装：
    pip install psutil py-cpuinfo matplotlib numpy
"""

import tkinter as tk
from tkinter import ttk
import psutil
import platform
import cpuinfo
import time
import threading
import subprocess
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU & GPU 监控工具")
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # ========== 界面美化 ==========
        self.setup_styles()
        # =============================

        # 检查 nvidia-smi 是否可用
        self.nvidia_smi_available = self.check_nvidia_smi()
        self.gpu_count = 0
        if self.nvidia_smi_available:
            self.gpu_count = self.get_gpu_count_nvidia_smi()
            print(f"检测到 {self.gpu_count} 个 NVIDIA GPU")
        else:
            print("nvidia-smi 不可用，将只监控 CPU")

        # 历史数据存储（用于图表）
        self.cpu_history = [0] * 60
        self.gpu_history = [0] * 60  # 如果有多个 GPU，只取第一个用于图表

        # 创建 Notebook 选项卡
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 选项卡1：实时监控
        self.monitor_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.monitor_frame, text="📊 实时监控")
        self.create_monitor_widgets()

        # 选项卡2：跑分与信息
        self.bench_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.bench_frame, text="📈 跑分与信息")
        self.create_bench_widgets()

        # 启动定时更新
        self.update_monitor_data()

    def setup_styles(self):
        """配置 ttk 样式美化"""
        style = ttk.Style()
        # 尝试使用 clam 主题（跨平台美观），如果不可用则使用默认
        try:
            style.theme_use('clam')
        except:
            pass  # 使用默认主题

        # 设置背景色和前景色
        style.configure('TLabel', background='#f0f0f0', foreground='#333333', font=('微软雅黑', 10))
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabelframe', background='#f0f0f0', foreground='#333333', font=('微软雅黑', 10, 'bold'))
        style.configure('TNotebook', background='#f0f0f0')
        style.configure('TNotebook.Tab', font=('微软雅黑', 10))
        style.configure('TButton', font=('微软雅黑', 10), padding=5)

        # 自定义进度条颜色
        style.configure('green.Horizontal.TProgressbar', background='#4CAF50', troughcolor='#dddddd', bordercolor='#cccccc', lightcolor='#4CAF50', darkcolor='#4CAF50')
        style.configure('blue.Horizontal.TProgressbar', background='#2196F3', troughcolor='#dddddd', bordercolor='#cccccc', lightcolor='#2196F3', darkcolor='#2196F3')
        style.configure('mem.Horizontal.TProgressbar', background='#FF9800', troughcolor='#dddddd', bordercolor='#cccccc', lightcolor='#FF9800', darkcolor='#FF9800')

    # ---------- 辅助函数：检测 nvidia-smi ----------
    def check_nvidia_smi(self):
        """检查 nvidia-smi 命令是否可用"""
        try:
            subprocess.run(['nvidia-smi', '--version'],
                           capture_output=True, check=True, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def get_gpu_count_nvidia_smi(self):
        """通过 nvidia-smi 获取 GPU 数量"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=index', '--format=csv,noheader'],
                capture_output=True, text=True, check=True, timeout=5
            )
            lines = result.stdout.strip().split('\n')
            return len([line for line in lines if line.strip() != ''])
        except:
            return 0

    def get_gpu_info_nvidia_smi(self):
        """获取所有 GPU 的实时信息（使用率、显存、温度）"""
        try:
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu',
                    '--format=csv,noheader,nounits'
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            gpu_list = []
            for line in lines:
                if not line.strip():
                    continue
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 6:
                    try:
                        gpu_info = {
                            'index': int(parts[0]),
                            'name': parts[1],
                            'load': float(parts[2]),          # 使用率百分比
                            'memory_used': float(parts[3]),   # MB
                            'memory_total': float(parts[4]),  # MB
                            'temperature': float(parts[5]) if parts[5] else None,
                        }
                        gpu_info['memory_percent'] = (gpu_info['memory_used'] / gpu_info['memory_total']) * 100 if gpu_info['memory_total'] > 0 else 0
                        gpu_list.append(gpu_info)
                    except (ValueError, IndexError):
                        continue
            return gpu_list if gpu_list else None
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"获取 GPU 信息失败: {e}")
            return None

    def get_gpu_details_nvidia_smi(self):
        """获取 GPU 的静态详细信息（驱动版本、CUDA版本、BIOS版本、PCI总线）"""
        try:
            result = subprocess.run(
                [
                    'nvidia-smi',
                    '--query-gpu=index,name,driver_version,cuda_version,vbios_version,pci.bus_id',
                    '--format=csv,noheader'
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=5
            )
            lines = result.stdout.strip().split('\n')
            details = []
            for line in lines:
                if not line.strip():
                    continue
                parts = [part.strip() for part in line.split(',')]
                if len(parts) >= 6:
                    details.append({
                        'index': parts[0],
                        'name': parts[1],
                        'driver': parts[2],
                        'cuda': parts[3],
                        'vbios': parts[4],
                        'pci': parts[5]
                    })
            return details
        except Exception as e:
            print(f"获取 GPU 详细信息失败: {e}")
            return None

    # ---------- 实时监控界面 ----------
    def create_monitor_widgets(self):
        main_frame = ttk.Frame(self.monitor_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ===== CPU 部分 =====
        cpu_frame = ttk.LabelFrame(main_frame, text="💻 CPU 监控", padding="10")
        cpu_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # CPU 名称
        try:
            cpu_name = cpuinfo.get_cpu_info()['brand_raw']
        except:
            cpu_name = platform.processor() or "未知 CPU"
        ttk.Label(cpu_frame, text=f"型号: {cpu_name}").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=2)

        # 总使用率
        ttk.Label(cpu_frame, text="总使用率:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.cpu_total_var = tk.StringVar(value="0.0%")
        ttk.Label(cpu_frame, textvariable=self.cpu_total_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        self.cpu_total_bar = ttk.Progressbar(cpu_frame, length=200, mode='determinate', style='green.Horizontal.TProgressbar')
        self.cpu_total_bar.grid(row=1, column=2, padx=5)

        # 每个核心使用率
        ttk.Label(cpu_frame, text="每核使用率:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.cpu_percore_var = tk.StringVar(value="")
        ttk.Label(cpu_frame, textvariable=self.cpu_percore_var).grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5)

        # 频率
        ttk.Label(cpu_frame, text="频率:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.cpu_freq_var = tk.StringVar(value="-- MHz")
        ttk.Label(cpu_frame, textvariable=self.cpu_freq_var).grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5)

        # 内存使用
        ttk.Label(cpu_frame, text="内存使用:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.mem_var = tk.StringVar(value="0.0 GB / 0.0 GB (0.0%)")
        ttk.Label(cpu_frame, textvariable=self.mem_var).grid(row=4, column=1, sticky=tk.W, padx=5)
        self.mem_bar = ttk.Progressbar(cpu_frame, length=200, mode='determinate', style='mem.Horizontal.TProgressbar')
        self.mem_bar.grid(row=4, column=2, padx=5)

        # ===== GPU 部分 =====
        self.gpu_frames = []  # 存放每个 GPU 的界面组件
        if self.nvidia_smi_available and self.gpu_count > 0:
            for i in range(self.gpu_count):
                self.create_gpu_widget(main_frame, i)
        else:
            msg = "未检测到 NVIDIA GPU 或 nvidia-smi 不可用" if not self.nvidia_smi_available else "未检测到 GPU 设备"
            ttk.Label(main_frame, text=msg, foreground="red").pack(pady=10)

    def create_gpu_widget(self, parent, idx):
        frame = ttk.LabelFrame(parent, text=f"🎮 GPU {idx}", padding="10")
        frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # GPU 名称（初始化时先填占位符，后续更新时从 nvidia-smi 获取）
        ttk.Label(frame, text="型号: 获取中...").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=2)

        # 使用率
        ttk.Label(frame, text="使用率:").grid(row=1, column=0, sticky=tk.W, pady=2)
        gpu_util_var = tk.StringVar(value="0.0%")
        ttk.Label(frame, textvariable=gpu_util_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        gpu_util_bar = ttk.Progressbar(frame, length=200, mode='determinate', style='blue.Horizontal.TProgressbar')
        gpu_util_bar.grid(row=1, column=2, padx=5)

        # 显存
        ttk.Label(frame, text="显存使用:").grid(row=2, column=0, sticky=tk.W, pady=2)
        gpu_mem_var = tk.StringVar(value="0 MB / 0 MB (0.0%)")
        ttk.Label(frame, textvariable=gpu_mem_var).grid(row=2, column=1, sticky=tk.W, padx=5)
        gpu_mem_bar = ttk.Progressbar(frame, length=200, mode='determinate')
        gpu_mem_bar.grid(row=2, column=2, padx=5)

        # 温度
        ttk.Label(frame, text="温度:").grid(row=3, column=0, sticky=tk.W, pady=2)
        gpu_temp_var = tk.StringVar(value="-- °C")
        ttk.Label(frame, textvariable=gpu_temp_var).grid(row=3, column=1, sticky=tk.W, padx=5)

        self.gpu_frames.append({
            'frame': frame,
            'name_label': None,  # 将在第一次更新时设置
            'util_var': gpu_util_var,
            'util_bar': gpu_util_bar,
            'mem_var': gpu_mem_var,
            'mem_bar': gpu_mem_bar,
            'temp_var': gpu_temp_var
        })

    # ---------- 跑分与信息界面 ----------
    def create_bench_widgets(self):
        main_frame = ttk.Frame(self.bench_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 图表区域
        chart_frame = ttk.LabelFrame(main_frame, text="📉 使用率历史曲线", padding="5")
        chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 创建 matplotlib 图表
        self.fig = Figure(figsize=(8, 3), dpi=100, facecolor='#f0f0f0')
        self.ax = self.fig.add_subplot(111, facecolor='#fafafa')
        self.ax.set_ylim(0, 100)
        self.ax.set_xlabel("时间 (秒)", fontsize=9)
        self.ax.set_ylabel("使用率 (%)", fontsize=9)
        self.ax.set_title("CPU & GPU 使用率 (最近60秒)", fontsize=10, fontweight='bold')
        self.cpu_line, = self.ax.plot([], [], 'b-', label="CPU", linewidth=2, color='#4CAF50')
        self.gpu_line, = self.ax.plot([], [], 'r-', label="GPU", linewidth=2, color='#2196F3')
        self.ax.legend(loc="upper right", frameon=False)
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 跑分控制区域
        bench_control_frame = ttk.Frame(main_frame)
        bench_control_frame.pack(fill=tk.X, pady=10)

        ttk.Label(bench_control_frame, text="⚡ CPU 跑分:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cpu_score_var = tk.StringVar(value="未运行")
        ttk.Label(bench_control_frame, textvariable=self.cpu_score_var, width=20).grid(row=0, column=1, padx=5)
        ttk.Button(bench_control_frame, text="运行 CPU 跑分", command=self.run_cpu_benchmark).grid(row=0, column=2, padx=5)

        ttk.Label(bench_control_frame, text="🔍 GPU 详细信息:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.gpu_info_var = tk.StringVar(value="点击查看")
        ttk.Label(bench_control_frame, textvariable=self.gpu_info_var, width=20).grid(row=1, column=1, padx=5)
        self.gpu_info_btn = ttk.Button(bench_control_frame, text="获取 GPU 信息", command=self.show_gpu_details)
        self.gpu_info_btn.grid(row=1, column=2, padx=5)

        # 如果 nvidia-smi 不可用，禁用 GPU 信息按钮
        if not self.nvidia_smi_available:
            self.gpu_info_btn.config(state=tk.DISABLED)
            self.gpu_info_var.set("nvidia-smi 不可用")

        # 说明
        info_text = "CPU 跑分: 计算 2~50000 之间的素数个数，分数 = 100000 / 耗时(ms)\n" \
                    "GPU 信息: 显示驱动版本、CUDA 版本等（通过 nvidia-smi 获取）"
        ttk.Label(main_frame, text=info_text, foreground="#666666").pack(pady=5)

    def run_cpu_benchmark(self):
        """CPU 跑分：计算素数个数（在后台线程运行）"""
        def task():
            start = time.perf_counter()
            count = 0
            for num in range(2, 50001):
                is_prime = True
                for i in range(2, int(num**0.5) + 1):
                    if num % i == 0:
                        is_prime = False
                        break
                if is_prime:
                    count += 1
            elapsed_ms = (time.perf_counter() - start) * 1000
            score = 100000 / elapsed_ms if elapsed_ms > 0 else 0
            self.cpu_score_var.set(f"{score:.2f}  (素数: {count})")
        threading.Thread(target=task, daemon=True).start()

    def show_gpu_details(self):
        """显示 GPU 详细信息（在新窗口）"""
        if not self.nvidia_smi_available:
            return

        def task():
            details = self.get_gpu_details_nvidia_smi()
            if details:
                self.gpu_info_var.set(f"获取到 {len(details)} 个 GPU 信息")
                self.show_details_window(details)
            else:
                self.gpu_info_var.set("获取失败，请检查 nvidia-smi")
        threading.Thread(target=task, daemon=True).start()

    def show_details_window(self, details):
        """在新窗口中显示完整的 GPU 信息"""
        win = tk.Toplevel(self.root)
        win.title("GPU 详细信息")
        win.geometry("600x400")
        win.configure(bg='#f0f0f0')
        text = tk.Text(win, wrap=tk.WORD, font=('微软雅黑', 10), bg='#fafafa', fg='#333333')
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for gpu in details:
            text.insert(tk.END, f"GPU {gpu['index']}: {gpu['name']}\n", ('bold',))
            text.insert(tk.END, f"  驱动版本: {gpu['driver']}\n")
            text.insert(tk.END, f"  CUDA 版本: {gpu['cuda']}\n")
            text.insert(tk.END, f"  BIOS 版本: {gpu['vbios']}\n")
            text.insert(tk.END, f"  PCI 总线: {gpu['pci']}\n")
            text.insert(tk.END, "-" * 40 + "\n")
        text.tag_configure('bold', font=('微软雅黑', 10, 'bold'))
        text.config(state=tk.DISABLED)

    # ---------- 数据更新 ----------
    def update_monitor_data(self):
        # 获取 CPU 信息
        cpu_info = self.get_cpu_info()
        self.cpu_total_var.set(f"{cpu_info['total_usage']:.1f}%")
        self.cpu_total_bar['value'] = cpu_info['total_usage']

        per_core = ', '.join([f"{p:.1f}%" for p in cpu_info['per_core_usage']])
        self.cpu_percore_var.set(per_core)

        if cpu_info['freq_current']:
            self.cpu_freq_var.set(f"{cpu_info['freq_current']:.0f} MHz (min: {cpu_info['freq_min']:.0f}, max: {cpu_info['freq_max']:.0f})")
        else:
            self.cpu_freq_var.set("频率信息不可用")

        mem_str = f"{cpu_info['memory_used']:.2f} GB / {cpu_info['memory_total']:.2f} GB ({cpu_info['memory_percent']:.1f}%)"
        self.mem_var.set(mem_str)
        self.mem_bar['value'] = cpu_info['memory_percent']

        # 获取 GPU 信息（如果有）
        gpu_util = None
        if self.nvidia_smi_available and self.gpu_count > 0:
            gpu_data_list = self.get_gpu_info_nvidia_smi()
            if gpu_data_list:
                for i, gpu_data in enumerate(gpu_data_list):
                    if i < len(self.gpu_frames):
                        gpu = self.gpu_frames[i]
                        # 更新名称（仅第一次或变化时）
                        if gpu['name_label'] is None:
                            # 移除占位标签
                            for widget in gpu['frame'].grid_slaves():
                                if int(widget.grid_info()["row"]) == 0:
                                    widget.destroy()
                            name_label = ttk.Label(gpu['frame'], text=f"型号: {gpu_data['name']}")
                            name_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=2)
                            gpu['name_label'] = name_label

                        gpu['util_var'].set(f"{gpu_data['load']:.1f}%")
                        gpu['util_bar']['value'] = gpu_data['load']

                        mem_str = f"{gpu_data['memory_used']:.0f} MB / {gpu_data['memory_total']:.0f} MB ({gpu_data['memory_percent']:.1f}%)"
                        gpu['mem_var'].set(mem_str)
                        gpu['mem_bar']['value'] = gpu_data['memory_percent']

                        if gpu_data['temperature'] is not None:
                            gpu['temp_var'].set(f"{gpu_data['temperature']:.0f} °C")
                        else:
                            gpu['temp_var'].set("-- °C")

                        if i == 0:
                            gpu_util = gpu_data['load']
            else:
                # 获取失败，清空显示
                for gpu in self.gpu_frames:
                    gpu['util_var'].set("N/A")
                    gpu['util_bar']['value'] = 0
                    gpu['mem_var'].set("N/A")
                    gpu['mem_bar']['value'] = 0
                    gpu['temp_var'].set("N/A")

        # 更新历史数据
        self.cpu_history.pop(0)
        self.cpu_history.append(cpu_info['total_usage'])
        if gpu_util is not None:
            self.gpu_history.pop(0)
            self.gpu_history.append(gpu_util)
        else:
            self.gpu_history.pop(0)
            self.gpu_history.append(0)

        # 更新图表
        self.update_chart()

        self.root.after(1000, self.update_monitor_data)  # 每秒更新

    def update_chart(self):
        x_data = list(range(len(self.cpu_history)))
        self.cpu_line.set_data(x_data, self.cpu_history)
        self.gpu_line.set_data(x_data, self.gpu_history)
        self.ax.relim()
        self.ax.autoscale_view(scalex=False, scaley=True)
        self.ax.set_xlim(0, 59)
        self.canvas.draw_idle()

    def get_cpu_info(self):
        cpu_percent = psutil.cpu_percent(interval=0)
        cpu_percent_per_core = psutil.cpu_percent(interval=0, percpu=True)
        cpu_freq = psutil.cpu_freq()
        memory = psutil.virtual_memory()
        return {
            "total_usage": cpu_percent,
            "per_core_usage": cpu_percent_per_core,
            "freq_current": cpu_freq.current if cpu_freq else None,
            "freq_min": cpu_freq.min if cpu_freq else None,
            "freq_max": cpu_freq.max if cpu_freq else None,
            "memory_total": memory.total / (1024**3),
            "memory_used": memory.used / (1024**3),
            "memory_percent": memory.percent
        }

    def on_closing(self):
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = MonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
    