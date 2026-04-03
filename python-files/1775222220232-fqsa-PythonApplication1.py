#!/usr/bin/env python3
# -*- coding: utf-8 -*-



import os
import sys
import subprocess
import threading
import time
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class XiaonanFlasher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("墨尘小米线刷")
        self.root.geometry("900x650")
        self.root.configure(bg="white")
        self.root.resizable(True, True)

        # 变量
        self.bat_path = tk.StringVar()
        self.device_status = tk.StringVar(value="未连接")
        self.flashing = False
        self.process = None

        self.create_widgets()
        self.check_fastboot()
        self.log("欢迎使用墨尘线刷工具")
        self.log("进入Fastboot模式")
        self.log("香菜卖身 感兴趣联系我")

    def create_widgets(self):
        # 顶部：选择脚本区域
        top_frame = tk.Frame(self.root, bg="white")
        top_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(top_frame, text="选择bat (flash_all.bat):", bg="white").pack(side=tk.LEFT)
        entry = tk.Entry(top_frame, textvariable=self.bat_path, width=50, bg="white")
        entry.pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="浏览", command=self.select_bat, bg="#f0f0f0", relief=tk.RAISED).pack(side=tk.LEFT)

        # 控制按钮区域
        ctrl_frame = tk.Frame(self.root, bg="white")
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_btn = tk.Button(ctrl_frame, text="开始刷写", command=self.start_flash, width=12, bg="#f0f0f0", relief=tk.RAISED)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(ctrl_frame, text="停止", command=self.stop_flash, state=tk.DISABLED, width=12, bg="#f0f0f0", relief=tk.RAISED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.auto_reboot_var = tk.IntVar(value=0)
        self.reboot_cb = tk.Checkbutton(ctrl_frame, text="自动重启", variable=self.auto_reboot_var, bg="white", relief=tk.FLAT)
        self.reboot_cb.pack(side=tk.LEFT, padx=20)

        # 设备状态
        status_frame = tk.Frame(self.root, bg="white")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(status_frame, text="设备状态:", bg="white").pack(side=tk.LEFT)
        tk.Label(status_frame, textvariable=self.device_status, fg="blue", bg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(status_frame, text="刷新状态", command=self.refresh_device, bg="#f0f0f0", relief=tk.RAISED).pack(side=tk.LEFT, padx=10)

        # 主内容区域：左右分栏（左侧无，右侧日志）
        # 根据需求：左边没有列表，只有右边刷写记录。所以我们直接放日志区域。
        log_frame = tk.LabelFrame(self.root, text="刷写记录", bg="white", fg="black")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=25, bg="white", fg="black", font=("Consolas", 9))
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 底部状态栏
        bottom_frame = tk.Frame(self.root, bg="white", relief=tk.SUNKEN, bd=1)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(bottom_frame, text="工具状态：就绪", bg="white", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5)
        self.current_flash_label = tk.Label(bottom_frame, text="当前刷写：无", bg="white", anchor=tk.W)
        self.current_flash_label.pack(side=tk.RIGHT, padx=5)

        # 联系信息
        info_frame = tk.Frame(self.root, bg="white")
        info_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(info_frame, text="组织：1094861315   联系墨尘：3756541352", bg="white", fg="gray").pack()

    def log(self, msg):
        """添加普通日志"""
        timestamp = time.strftime("[%H:%M:%S]")
        self.log_area.insert(tk.END, f"{timestamp} {msg}\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def flash_log(self, status, partition, detail=""):
        """专门用于刷写结果日志，格式：OK 镜像名 或 FAIL 镜像名"""
        timestamp = time.strftime("[%H:%M:%S]")
        if status == "OK":
            self.log_area.insert(tk.END, f"{timestamp} OK {partition}\n")
        elif status == "FAIL":
            self.log_area.insert(tk.END, f"{timestamp} FAIL {partition} - {detail}\n")
        else:
            self.log_area.insert(tk.END, f"{timestamp} {status} {partition}\n")
        self.log_area.see(tk.END)
        self.root.update_idletasks()

    def select_bat(self):
        path = filedialog.askopenfilename(
            title="选择刷机脚本",
            filetypes=[("批处理文件", "*.bat"), ("所有文件", "*.*")]
        )
        if path:
            self.bat_path.set(path)
            self.log(f"已选择脚本: {path}")

    def refresh_device(self):
        try:
            proc = subprocess.run(["fastboot", "devices"], capture_output=True, text=True, timeout=5)
            if proc.stdout.strip():
                self.device_status.set("已连接")
            else:
                self.device_status.set("未连接")
        except:
            self.device_status.set("未连接")

    def check_fastboot(self):
        def update():
            self.refresh_device()
            self.root.after(3000, update)
        self.root.after(1000, update)

    def start_flash(self):
        bat_file = self.bat_path.get().strip()
        if not bat_file:
            messagebox.showerror("错误", "请先选择刷机脚本")
            return
        if not os.path.exists(bat_file):
            messagebox.showerror("错误", "脚本文件不存在")
            return

        if self.flashing:
            return

        self.flashing = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="工具状态：刷写中")
        self.log("开始执行刷机脚本...")
        self.log(f"脚本路径: {bat_file}")

        thread = threading.Thread(target=self.run_bat, args=(bat_file,))
        thread.daemon = True
        thread.start()

    def run_bat(self, bat_file):
        try:
            # 启动进程，实时读取输出
            self.process = subprocess.Popen(
                [bat_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='gbk',
                errors='replace',
                shell=True
            )
            # 逐行读取并解析
            for line in self.process.stdout:
                if not line.strip():
                    continue
                # 显示原始行（可选）
                # self.log(f"[输出] {line.strip()}")
                # 解析刷写结果
                self.parse_flash_line(line.strip())
            self.process.wait()
            ret = self.process.returncode
            if ret == 0:
                self.log("刷机脚本执行完成")
                if self.auto_reboot_var.get():
                    self.log("正在重启设备...")
                    subprocess.run(["fastboot", "reboot"], capture_output=True, timeout=10)
                    self.log("已发送重启命令")
            else:
                self.log(f"脚本执行异常，返回码: {ret}")
        except Exception as e:
            self.log(f"执行出错: {e}")
        finally:
            self.flashing = False
            self.process = None
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="工具状态：就绪")
            self.log("刷写流程结束")

    def parse_flash_line(self, line):
        """解析一行输出，提取分区名和刷写状态"""
        line_lower = line.lower()
        # 常见 fastboot 输出格式：
        # "Sending 'boot' (4096 KB)" 或 "OKAY [  0.123s]" 或 "Finished. Total time: ..."
        # 也有 "writing 'boot'..." 等。
        # 我们匹配常见模式：
        # 1. 如果行包含 "OKAY" 且之前有分区名，则认为是成功
        # 2. 如果行包含 "FAILED" 或 "error"，则失败
        # 为了简单，我们捕获 "Sending 'partition'" 和之后的 "OKAY" 配对。
        # 由于多行，需要维护状态。但简化：直接检测行中的分区名和结果关键词。
        
        # 方法：匹配类似 "Sending 'boot'" 或 "writing 'boot'"
        send_match = re.search(r"(?:Sending|writing)\s*'([^']+)'", line, re.I)
        if send_match:
            self.current_partition = send_match.group(1)
            # 不立即输出，等待 OKAY 或 FAIL
            return

        # 检测 OKAY
        if "okay" in line_lower:
            if hasattr(self, 'current_partition'):
                self.flash_log("OK", self.current_partition)
                del self.current_partition
            else:
                # 如果没有捕获到分区名，尝试从行中提取
                part_match = re.search(r"'([^']+)'", line)
                if part_match:
                    self.flash_log("OK", part_match.group(1))
                else:
                    self.log(f"OK (无分区信息): {line}")
            return

        # 检测 FAILED 或 error
        if "failed" in line_lower or "error" in line_lower:
            if hasattr(self, 'current_partition'):
                self.flash_log("FAIL", self.current_partition, line[:50])
                del self.current_partition
            else:
                part_match = re.search(r"'([^']+)'", line)
                if part_match:
                    self.flash_log("FAIL", part_match.group(1), line[:50])
                else:
                    self.log(f"FAIL: {line}")
            return

        # 其他行，如果包含分区名但无结果，暂时忽略
        # 可选：显示原始行用于调试
        # self.log(f"[RAW] {line}")

    def stop_flash(self):
        if self.process and self.flashing:
            self.log("正在终止刷写进程...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.log("已终止刷写进程")
            self.flashing = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="工具状态：已停止")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    try:
        subprocess.run(["fastboot", "--version"], capture_output=True, timeout=2)
    except FileNotFoundError:
        print("提示: 未找到 fastboot，设备状态检测将不可用")
    app = XiaonanFlasher()
    app.run()