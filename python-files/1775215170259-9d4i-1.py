import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import ctypes
from ctypes import wintypes
import re

# ================= 核心逻辑：系统 API 与任务管理 =================

def get_desktop_paths():
    """获取个人桌面和公共桌面路径"""
    paths = []
    # 16 = 个人桌面, 25 = 公共桌面
    for csidl in [16, 25]:
        path_buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, path_buf)
        if path_buf.value:
            paths.append(path_buf.value)
    return paths

def get_current_desktop_items():
    """合并获取两个桌面上的所有文件"""
    all_items = set()
    for path in get_desktop_paths():
        try:
            if os.path.exists(path):
                for f in os.listdir(path):
                    if f.lower() != "desktop.ini":
                        all_items.add(f)
        except Exception:
            pass
    return sorted(list(all_items))

def get_task_info(task_name="AutoDesktopCleaner"):
    """查询 Windows 任务计划状态"""
    try:
        # /fo LIST 以列表格式输出信息
        result = subprocess.run(f'schtasks /query /tn "{task_name}" /fo LIST /v', 
                                shell=True, capture_output=True, text=True, encoding='gbk')
        if result.returncode != 0:
            return None
        
        # 使用正则表达式提取“下次运行时间”或“计划时间”
        info = {}
        for line in result.stdout.split('\n'):
            if ":" in line:
                key, _, val = line.partition(":")
                info[key.strip()] = val.strip()
        return info
    except:
        return None

# ================= GUI 类定义 =================

class DesktopCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面定时清理管家 4.0")
        self.root.geometry("550x650")
        self.file_vars = {}
        
        # 设置样式
        self.style = ttk.Style()
        if 'vista' in self.style.theme_names():
            self.style.theme_use('vista')
        
        self.setup_ui()
        self.refresh_task_status()

    def setup_ui(self):
        # 顶部蓝色标题栏
        header = tk.Frame(self.root, bg="#005a9e", pady=15)
        header.pack(fill=tk.X)
        tk.Label(header, text="✨ 桌面自动清理管家 ✨", font=("Microsoft YaHei", 16, "bold"), fg="white", bg="#005a9e").pack()

        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 选项卡 1：设置计划
        self.tab_setup = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_setup, text=" 📝 配置清理计划 ")
        self.setup_tab_setup()

        # 选项卡 2：管理计划
        self.tab_manage = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_manage, text=" ⚙️ 管理已有计划 ")
        self.setup_tab_manage()

    def setup_tab_setup(self):
        """配置页面 UI"""
        tk.Label(self.tab_setup, text="请勾选需要【保留】的文件：", font=("Microsoft YaHei", 10)).pack(anchor="w", padx=15, pady=10)
        
        # 操作按钮
        btn_frame = tk.Frame(self.tab_setup)
        btn_frame.pack(fill=tk.X, padx=15)
        ttk.Button(btn_frame, text="全选", width=8, command=lambda: self.set_all(True)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全不选", width=8, command=lambda: self.set_all(False)).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 刷新列表", command=self.load_items).pack(side=tk.RIGHT)

        # 文件列表滚动区
        list_frame = ttk.Frame(self.tab_setup, relief="solid", borderwidth=1)
        list_frame.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(list_frame, highlightthickness=0, bg="white")
        v_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas, style="White.TFrame")
        self.style.configure("White.TFrame", background="white")

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=v_scroll.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 时间设置
        time_frame = ttk.LabelFrame(self.tab_setup, text=" 执行时间 ", padding=10)
        time_frame.pack(padx=15, pady=10, fill=tk.X)
        
        self.hour_var = tk.StringVar(value="18")
        self.min_var = tk.StringVar(value="00")
        tk.Label(time_frame, text="每天定时:").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=4, format="%02.0f").pack(side=tk.LEFT)
        tk.Label(time_frame, text=":").pack(side=tk.LEFT)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.min_var, width=4, format="%02.0f").pack(side=tk.LEFT)

        # 保存按钮
        btn_save = tk.Button(self.tab_setup, text="保存并启用该计划", bg="#005a9e", fg="white", 
                             font=("Microsoft YaHei", 11, "bold"), command=self.save_task)
        btn_save.pack(pady=10, fill=tk.X, padx=100)

        self.load_items()

    def setup_tab_manage(self):
        """管理页面 UI"""
        self.manage_container = tk.Frame(self.tab_manage, pady=30)
        self.manage_container.pack(fill=tk.BOTH, expand=True)

        self.status_icon = tk.Label(self.manage_container, text="查询中...", font=("Segoe UI Emoji", 48))
        self.status_icon.pack()

        self.status_text = tk.Label(self.manage_container, text="", font=("Microsoft YaHei", 14, "bold"))
        self.status_text.pack(pady=10)

        self.detail_text = tk.Label(self.manage_container, text="", font=("Microsoft YaHei", 10), fg="#666666")
        self.detail_text.pack(pady=5)

        self.btn_delete = tk.Button(self.manage_container, text="🛑 停止并彻底删除计划", bg="#d83b01", fg="white",
                                    font=("Microsoft YaHei", 10, "bold"), command=self.delete_task, state=tk.DISABLED)
        self.btn_delete.pack(pady=20)
        
        ttk.Button(self.manage_container, text="刷新状态", command=self.refresh_task_status).pack()

    # ================= 业务逻辑函数 =================

    def load_items(self):
        for widget in self.scroll_frame.winfo_children(): widget.destroy()
        self.file_vars.clear()
        items = get_current_desktop_items()
        for item in items:
            var = tk.BooleanVar(value=True)
            self.file_vars[item] = var
            cb = ttk.Checkbutton(self.scroll_frame, text=item, variable=var, style="TCheckbutton")
            cb.pack(anchor="w", padx=10, pady=2, fill=tk.X)

    def set_all(self, status):
        for var in self.file_vars.values(): var.set(status)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def refresh_task_status(self):
        info = get_task_info()
        if info:
            self.status_icon.config(text="✅", fg="#107c10")
            self.status_text.config(text="计划任务运行中", fg="#107c10")
            time_val = info.get("上次运行时间", "未知") if "下次运行时间" not in info else info.get("下次运行时间")
            self.detail_text.config(text=f"当前设定：每天 {self.hour_var.get()}:{self.min_var.get()} 执行\n下次执行: {time_val}")
            self.btn_delete.config(state=tk.NORMAL)
        else:
            self.status_icon.config(text="❌", fg="#a80000")
            self.status_text.config(text="当前没有清理计划", fg="#a80000")
            self.detail_text.config(text="您可以前往“配置清理计划”页面新建一个。")
            self.btn_delete.config(state=tk.DISABLED)

    def save_task(self):
        # 1. 检查冲突
        if get_task_info():
            if not messagebox.askyesno("覆盖确认", "已存在清理计划，是否覆盖？"):
                return

        # 2. 生成 PowerShell 脚本
        keep_list = [name for name, var in self.file_vars.items() if var.get()]
        ps_array = ",\n".join([f'"{item}"' for item in keep_list])
        desktop_paths = ",\n".join([f'"{p}"' for p in get_desktop_paths()])
        
        ps_content = f"""
$paths = @(
{desktop_paths}
)
$keepList = @(
{ps_array}
)
foreach ($p in $paths) {{
    if (Test-Path $p) {{
        Get-ChildItem -Path $p | Where-Object {{ $keepList -notcontains $_.Name }} | Remove-Item -Recurse -Force
    }}
}}
"""
        appdata_path = os.path.join(os.environ['APPDATA'], 'DesktopCleanerApp')
        os.makedirs(appdata_path, exist_ok=True)
        ps_file = os.path.join(appdata_path, 'clean_desktop.ps1')
        
        with open(ps_file, 'w', encoding='utf-8') as f:
            f.write(ps_content)

        # 3. 创建任务计划
        run_time = f"{int(self.hour_var.get()):02d}:{int(self.min_var.get()):02d}"
        # 使用最高权限运行以确保能清理公共桌面图标
        cmd = f'schtasks /create /tn "AutoDesktopCleaner" /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File \\"{ps_file}\\"" /sc daily /st {run_time} /rl HIGHEST /f'
        
        if subprocess.run(cmd, shell=True, capture_output=True).returncode == 0:
            messagebox.showinfo("成功", f"计划已启用！每天 {run_time} 自动清理。")
            self.refresh_task_status()
            self.notebook.select(self.tab_manage)
        else:
            messagebox.showerror("失败", "权限不足或系统拒绝创建任务，请尝试以管理员身份运行此程序。")

    def delete_task(self):
        if messagebox.askyesno("确认删除", "确定要彻底删除该定时清理任务吗？"):
            res = subprocess.run('schtasks /delete /tn "AutoDesktopCleaner" /f', shell=True, capture_output=True)
            if res.returncode == 0:
                messagebox.showinfo("已删除", "定时任务已从系统中移除。")
                self.refresh_task_status()
            else:
                messagebox.showerror("错误", "删除失败。")

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopCleanerApp(root)
    root.mainloop()