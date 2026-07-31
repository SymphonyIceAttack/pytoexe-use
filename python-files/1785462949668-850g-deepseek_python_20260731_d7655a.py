import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
import winreg  # Windows 注册表操作

# 配置文件路径（保存在脚本同目录下）
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wechat_config.json")

class WeChatMultiOpen:
    def __init__(self, root):
        self.root = root
        self.root.title("微信多开工具")
        self.root.geometry("420x260")
        self.root.resizable(False, False)
        self.root.configure(bg="white")

        # 微信路径变量
        self.wechat_path = tk.StringVar()

        # 界面控件
        self.create_widgets()

        # 加载保存的路径或自动检测
        self.load_or_detect_path()

    def create_widgets(self):
        # 标题
        title = tk.Label(
            self.root, text="微信多开工具", font=("微软雅黑", 16, "bold"),
            fg="#009900", bg="white"
        )
        title.pack(pady=(20, 5))

        # 路径显示
        path_frame = tk.Frame(self.root, bg="white")
        path_frame.pack(pady=(5, 5), fill="x", padx=20)
        self.path_label = tk.Label(
            path_frame, text="微信路径: 未检测", font=("微软雅黑", 9),
            fg="gray", bg="white", anchor="w"
        )
        self.path_label.pack(fill="x")

        # 状态标签
        self.status_label = tk.Label(
            self.root, text="点击下方按钮打开新的微信实例", font=("微软雅黑", 10),
            fg="dimgray", bg="white", anchor="w"
        )
        self.status_label.pack(pady=(5, 10), fill="x", padx=20)

        # 按钮区域
        btn_frame = tk.Frame(self.root, bg="white")
        btn_frame.pack(pady=(5, 10), fill="x", padx=20)

        self.open_btn = tk.Button(
            btn_frame, text="打开新的微信", font=("微软雅黑", 12, "bold"),
            bg="#009900", fg="white", relief="flat", cursor="hand2",
            command=self.open_wechat
        )
        self.open_btn.pack(side="left", padx=(0, 10))

        self.set_btn = tk.Button(
            btn_frame, text="手动设置路径", font=("微软雅黑", 9),
            bg="lightgray", relief="flat", cursor="hand2",
            command=self.set_path
        )
        self.set_btn.pack(side="left")

        # 底部提示
        tip = tk.Label(
            self.root, text="提示: 支持微信 3.x / 4.x 版本", font=("微软雅黑", 8),
            fg="gray", bg="white"
        )
        tip.pack(pady=(10, 0))

    def load_or_detect_path(self):
        """从配置文件加载路径，若无则自动检测"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    path = data.get("wechat_path", "")
                    if os.path.isfile(path):
                        self.wechat_path.set(path)
                        self.update_path_label(path, valid=True)
                        self.status_label.config(text="就绪，点击按钮打开新的微信", fg="dimgray")
                        self.open_btn.config(state="normal")
                        return
            except:
                pass

        # 自动检测
        self.auto_detect_path()

    def auto_detect_path(self):
        """自动检测微信安装路径"""
        path = self.find_wechat_from_registry()
        if not path:
            path = self.find_wechat_from_common_paths()
        if path:
            self.wechat_path.set(path)
            self.update_path_label(path, valid=True)
            self.status_label.config(text="就绪，点击按钮打开新的微信", fg="dimgray")
            self.open_btn.config(state="normal")
            self.save_path_to_config(path)
        else:
            self.update_path_label("未自动检测到，请手动设置", valid=False)
            self.status_label.config(text="请先设置微信路径", fg="red")
            self.open_btn.config(state="disabled")

    def find_wechat_from_registry(self):
        """从注册表查找 WeChat.exe 路径"""
        reg_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WeChat.exe",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\WeChat.exe",
            r"SOFTWARE\Tencent\WeChat",
            r"SOFTWARE\WOW6432Node\Tencent\WeChat",
        ]
        for reg in reg_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg)
                # 尝试默认值
                try:
                    value, _ = winreg.QueryValueEx(key, "")
                    if value and os.path.isfile(value):
                        winreg.CloseKey(key)
                        return value
                except:
                    pass
                # 尝试 InstallDir
                try:
                    install_dir, _ = winreg.QueryValueEx(key, "InstallDir")
                    if install_dir:
                        exe = os.path.join(install_dir, "WeChat.exe")
                        if os.path.isfile(exe):
                            winreg.CloseKey(key)
                            return exe
                except:
                    pass
                winreg.CloseKey(key)
            except:
                continue
        return None

    def find_wechat_from_common_paths(self):
        """常见安装目录查找"""
        common_paths = [
            r"C:\Program Files\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"C:\Program Files\WeChat\WeChat.exe",
            r"C:\Program Files (x86)\WeChat\WeChat.exe",
            r"C:\Tencent\WeChat\WeChat.exe",
            r"D:\Program Files\Tencent\WeChat\WeChat.exe",
            r"D:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
            r"E:\Program Files\Tencent\WeChat\WeChat.exe",
            r"E:\Program Files (x86)\Tencent\WeChat\WeChat.exe",
        ]
        for path in common_paths:
            if os.path.isfile(path):
                return path
        # 尝试用户 LocalAppData
        local_app = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Tencent\WeChat\WeChat.exe")
        if os.path.isfile(local_app):
            return local_app
        return None

    def update_path_label(self, text, valid=True):
        color = "darkgreen" if valid else "red"
        self.path_label.config(text=f"微信路径: {text}", fg=color)

    def save_path_to_config(self, path):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"wechat_path": path}, f)
        except:
            pass

    def set_path(self):
        """手动选择 WeChat.exe"""
        file_path = filedialog.askopenfilename(
            title="请选择 WeChat.exe",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
            initialdir=os.environ.get("ProgramFiles", "C:\\")
        )
        if file_path and os.path.isfile(file_path):
            self.wechat_path.set(file_path)
            self.update_path_label(file_path, valid=True)
            self.status_label.config(text="路径已更新，点击按钮打开新的微信", fg="dimgray")
            self.open_btn.config(state="normal")
            self.save_path_to_config(file_path)

    def open_wechat(self):
        """尝试打开新的微信实例"""
        path = self.wechat_path.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("错误", "微信路径无效，请重新设置。")
            self.open_btn.config(state="disabled")
            return

        success = self.try_open_wechat(path)
        if success:
            # 获取最新微信进程 PID（可选）
            pid = self.get_latest_wechat_pid()
            pid_str = f" (PID: {pid})" if pid else ""
            self.status_label.config(text=f"✓ 已成功启动新的微信实例{pid_str}", fg="darkgreen")
        else:
            self.status_label.config(text="✗ 启动失败，请检查路径或微信是否正常", fg="red")
            messagebox.showwarning(
                "启动失败",
                "启动微信失败！\n\n可能的原因：\n"
                "• 微信路径不正确\n"
                "• 微信文件已损坏\n"
                "• 当前微信版本不支持多开\n\n"
                "建议：\n"
                "• 点击「手动设置路径」重新选择\n"
                "• 检查微信是否正常安装\n"
                "• 尝试关闭所有微信后再试"
            )

    def try_open_wechat(self, path):
        """使用多种参数和方法尝试启动新实例"""
        # 常用的多开参数
        args_list = [
            "-multiple",
            "-mult",
            "--multiple",
            "--mult",
            "/multiple",
            "/mult",
            "-multi",
            "--multi",
        ]

        # 先检测微信是否已在运行
        running_before = self.is_wechat_running()

        for arg in args_list:
            try:
                # 方法1：直接带参数启动
                proc = subprocess.Popen(
                    [path, arg],
                    shell=False,
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
                )
                # 等待一小会儿，看是否启动成功
                import time
                time.sleep(0.5)
                if running_before and self.is_wechat_running():
                    return True
                elif not running_before:
                    # 如果之前没运行，检查现在是否运行了
                    if self.is_wechat_running():
                        return True
                # 如果进程已退出，继续尝试下一种方法
                if proc.poll() is not None:
                    continue
                else:
                    # 进程还在，可能成功
                    return True
            except:
                continue

        # 方法2：通过 cmd /c start 启动
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "", path],
                shell=False,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            import time
            time.sleep(0.5)
            if self.is_wechat_running():
                return True
        except:
            pass

        # 方法3：使用 start /b
        try:
            subprocess.Popen(
                ["cmd.exe", "/c", "start", "/b", "", path],
                shell=False,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            import time
            time.sleep(0.5)
            if self.is_wechat_running():
                return True
        except:
            pass

        return False

    def is_wechat_running(self):
        """判断微信进程是否存在（使用 tasklist）"""
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq WeChat.exe"],
                encoding="gbk"
            )
            # 如果输出中包含 WeChat.exe 且不是表头，则认为在运行
            lines = output.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    if "WeChat.exe" in line:
                        return True
            return False
        except:
            return False

    def get_latest_wechat_pid(self):
        """获取最近启动的微信进程 PID（仅作显示）"""
        try:
            output = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq WeChat.exe", "/FO", "CSV"],
                encoding="gbk"
            )
            # 解析 CSV 取最后一行 PID
            import csv
            from io import StringIO
            reader = csv.reader(StringIO(output))
            rows = list(reader)
            if len(rows) > 1:
                # 最后一行格式: ["WeChat.exe", "PID", ...]
                last = rows[-1]
                if len(last) > 1 and last[0].strip().lower() == "wechat.exe":
                    return last[1].strip()
            return None
        except:
            return None

if __name__ == "__main__":
    root = tk.Tk()
    app = WeChatMultiOpen(root)
    root.mainloop()