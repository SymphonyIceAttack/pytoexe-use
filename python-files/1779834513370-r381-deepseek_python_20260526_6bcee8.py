import tkinter as tk
from tkinter import messagebox
import threading
import time
import psutil
import os
import sys
import ctypes

# ---------- 管理员权限检查与提权 ----------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """以管理员身份重新运行自身"""
    if sys.argv[0].endswith('.py'):
        # 如果是 .py 脚本，用 python 解释器运行
        params = f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
    else:
        params = f'"{os.path.abspath(sys.argv[0])}"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
    sys.exit()

if not is_admin():
    # 未提权则弹出UAC请求
    run_as_admin()

PROCESS_NAME = "GTA5_Enhanced.exe"
MONITOR_INTERVAL = 5  # 检查间隔（秒）
SHUTDOWN_DELAY = 0    # 关机延迟（秒），0为立即关机

class GTA5MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GTA5 进程监控 - 检测到即关机")
        self.root.geometry("400x200")
        self.root.resizable(False, False)

        self.monitoring = False
        self.thread = None

        # 状态标签
        self.status_var = tk.StringVar(value="就绪，点击「开始监控」")
        tk.Label(root, textvariable=self.status_var, font=("微软雅黑", 12), pady=10).pack()

        # 进程名显示
        tk.Label(root, text=f"目标进程: {PROCESS_NAME}", font=("微软雅黑", 10)).pack()

        # 按钮框架
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=15)

        self.start_btn = tk.Button(btn_frame, text="开始监控", width=12, command=self.start_monitor)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="停止监控", width=12, command=self.stop_monitor, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 关闭窗口时确保线程退出
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def monitor_loop(self):
        """后台监控线程"""
        while self.monitoring:
            if self.is_process_running(PROCESS_NAME):
                self.log(f"检测到 {PROCESS_NAME}，正在关机...")
                self.shutdown()
                break
            time.sleep(MONITOR_INTERVAL)
        # 如果退出循环是停止监控，则无动作

    def is_process_running(self, proc_name):
        """检查进程是否存在"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == proc_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False

    def shutdown(self):
        """执行关机命令"""
        delay = SHUTDOWN_DELAY
        if delay == 0:
            cmd = "shutdown /s /t 0"
        else:
            cmd = f"shutdown /s /t {delay} /c \"检测到GTA5 Enhanced，即将关机\""
        os.system(cmd)
        # 关机命令执行后程序可能不会自己退出，但没关系

    def start_monitor(self):
        if self.monitoring:
            return
        self.monitoring = True
        self.status_var.set("监控运行中...")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()

    def stop_monitor(self):
        self.monitoring = False
        self.status_var.set("监控已停止")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def log(self, msg):
        """安全更新状态文字"""
        self.root.after(0, lambda: self.status_var.set(msg))

    def on_close(self):
        self.monitoring = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = GTA5MonitorApp(root)
    root.mainloop()