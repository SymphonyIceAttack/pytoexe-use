import os
import time
import tempfile
import tkinter as tk
from tkinter import ttk, messagebox

# 防休眠核心函数
def keep_drive_active(drive_letter, interval=10):
    """
    向指定硬盘写入临时文件，防止机械硬盘休眠
    :param drive_letter: 硬盘盘符（如 E:）
    :param interval: 写入间隔（秒），默认10秒
    """
    if not running_status.get():
        return
    
    # 检查硬盘是否存在
    if not os.path.exists(drive_letter):
        messagebox.showerror("错误", f"硬盘 {drive_letter} 不存在！")
        stop_program()
        return

    try:
        # 在硬盘根目录创建临时文件（自动删除）
        with tempfile.NamedTemporaryFile(dir=drive_letter, delete=True) as f:
            # 写入1字节数据，触发硬盘工作
            f.write(b'1')
            f.flush()
        
        # 更新状态日志
        log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] 已激活硬盘 {drive_letter}\n")
        log_text.see(tk.END)  # 自动滚动到最新日志
    except PermissionError:
        messagebox.showerror("权限错误", "请以管理员身份运行程序！")
        stop_program()
        return
    except Exception as e:
        log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] 异常：{str(e)}\n")
        log_text.see(tk.END)

    # 循环执行
    root.after(interval * 1000, lambda: keep_drive_active(drive_letter, interval))

# 启动程序
def start_program():
    drive = drive_var.get().strip()
    if not drive:
        messagebox.showwarning("提示", "请选择硬盘盘符！")
        return
    
    # 格式化盘符（自动补全冒号）
    if not drive.endswith(':'):
        drive = f"{drive}:"
    
    running_status.set(True)
    start_btn.config(state=tk.DISABLED)
    stop_btn.config(state=tk.NORMAL)
    log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] 开始保护硬盘 {drive}，间隔10秒\n")
    log_text.see(tk.END)
    
    # 启动防休眠
    keep_drive_active(drive)

# 停止程序
def stop_program():
    running_status.set(False)
    start_btn.config(state=tk.NORMAL)
    stop_btn.config(state=tk.DISABLED)
    log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] 已停止保护\n")
    log_text.see(tk.END)

# 获取电脑所有硬盘盘符
def get_all_drives():
    drives = []
    for char in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
        drive = f"{char}:"
        if os.path.exists(drive):
            drives.append(drive)
    return drives

# ------------------- GUI界面 -------------------
root = tk.Tk()
root.title("移动机械硬盘防休眠工具")
root.geometry("500x350")
root.resizable(False, False)

# 全局状态
running_status = tk.BooleanVar(value=False)
drive_var = tk.StringVar()

# 界面组件
tk.Label(root, text="选择移动硬盘盘符：", font=("微软雅黑", 10)).place(x=20, y=20)
drive_combo = ttk.Combobox(root, textvariable=drive_var, values=get_all_drives(), width=8, font=("微软雅黑", 10))
drive_combo.place(x=180, y=20)
drive_combo.current(0)  # 默认选中第一个

start_btn = ttk.Button(root, text="启动保护", command=start_program)
start_btn.place(x=100, y=60, width=120)

stop_btn = ttk.Button(root, text="停止保护", command=stop_program, state=tk.DISABLED)
stop_btn.place(x=260, y=60, width=120)

# 日志框
tk.Label(root, text="运行日志：", font=("微软雅黑", 10)).place(x=20, y=100)
log_text = tk.Text(root, width=58, height=12, font=("微软雅黑", 9))
log_text.place(x=20, y=120)

# 启动界面
root.mainloop()
