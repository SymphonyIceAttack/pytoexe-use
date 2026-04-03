import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess

def get_desktop_path():
    """获取当前用户的桌面路径"""
    return os.path.join(os.environ['USERPROFILE'], 'Desktop')

def get_current_desktop_items():
    """获取桌面上现有的文件和快捷方式"""
    desktop = get_desktop_path()
    try:
        return [f for f in os.listdir(desktop) if f.lower() != "desktop.ini"]
    except Exception:
        return []

def load_desktop_items():
    """刷新并加载桌面文件到表格中"""
    # 清空现有表格
    for item in tree.get_children():
        tree.delete(item)
    
    # 重新获取并插入
    items = get_current_desktop_items()
    for item in items:
        # 默认全部打勾（保留）
        tree.insert('', tk.END, values=('☑', item))

def toggle_check(event):
    """处理表格点击事件，切换勾选状态"""
    region = tree.identify("region", event.x, event.y)
    if region == "cell":
        col = tree.identify_column(event.x)
        # 只有点击第一列（状态列）时才切换状态
        if col == '#1':
            item_id = tree.identify_row(event.y)
            if item_id:
                values = tree.item(item_id, 'values')
                new_status = '☐' if values[0] == '☑' else '☑'
                tree.item(item_id, values=(new_status, values[1]))

def set_all_status(check=True):
    """全选或全不选"""
    status = '☑' if check else '☐'
    for item_id in tree.get_children():
        values = tree.item(item_id, 'values')
        tree.item(item_id, values=(status, values[1]))

def apply_settings():
    """生成脚本并注册定时任务"""
    # 1. 遍历表格，找出被勾选的保留名单
    keep_list = []
    for item_id in tree.get_children():
        values = tree.item(item_id, 'values')
        if values[0] == '☑':
            keep_list.append(values[1])
            
    # 2. 获取并格式化时间
    try:
        h = int(hour_var.get())
        m = int(min_var.get())
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError
        run_time = f"{h:02d}:{m:02d}"
    except ValueError:
        messagebox.showerror("时间错误", "时间格式不正确，请输入有效的时和分！")
        return

    # 3. 准备脚本保存路径
    appdata_dir = os.environ['APPDATA']
    save_dir = os.path.join(appdata_dir, 'DesktopCleanerApp')
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    ps1_path = os.path.join(save_dir, 'clean_desktop.ps1')

    # 4. 生成 PowerShell 脚本内容
    ps_array = ",\n".join([f'"{item}"' for item in keep_list])
    ps1_content = f"""
$desktopPath = [Environment]::GetFolderPath("Desktop")
$keepList = @(
{ps_array}
)
$items = Get-ChildItem -Path $desktopPath
foreach ($item in $items) {{
    if ($keepList -notcontains $item.Name) {{
        Remove-Item -Path $item.FullName -Recurse -Force
    }}
}}
"""
    # 写入文件
    try:
        with open(ps1_path, 'w', encoding='utf-8') as f:
            f.write(ps1_content)
    except Exception as e:
        messagebox.showerror("错误", f"无法生成清理脚本: {e}")
        return

    # 5. 配置 Windows 定时任务
    command = (
        f'schtasks /create /tn "AutoDesktopCleaner" '
        f'/tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File \\"{ps1_path}\\"" '
        f'/sc daily /st {run_time} /f'
    )
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        messagebox.showinfo("设置成功", f" 搞定！\n系统每天将在 {run_time} 自动清理桌面。\n打勾的文件将被安全保留。")
    else:
        messagebox.showerror("任务创建失败", f"无法设置系统定时任务:\n{result.stderr}")


# ================= GUI 界面设计 =================
root = tk.Tk()
root.title("桌面定时清理管家 2.0")
root.geometry("500x600")
root.resizable(False, False)

# 设置主题风格
style = ttk.Style()
style.theme_use('clam') 

# 标题区域
frame_header = tk.Frame(root, bg="#2b579a", pady=15)
frame_header.pack(fill=tk.X)
tk.Label(frame_header, text=" 桌面自动清理管家 ", font=("Microsoft YaHei", 16, "bold"), fg="white", bg="#2b579a").pack()

# 提示说明
tk.Label(root, text="请在下方勾选【不想被删除】的重要文件：", font=("Microsoft YaHei", 10), pady=10).pack(anchor="w", padx=20)

# 列表操作按钮区域
frame_actions = tk.Frame(root)
frame_actions.pack(fill=tk.X, padx=20, pady=2)
ttk.Button(frame_actions, text="☑ 全选", command=lambda: set_all_status(True)).pack(side=tk.LEFT, padx=(0, 5))
ttk.Button(frame_actions, text="☐ 全不选", command=lambda: set_all_status(False)).pack(side=tk.LEFT)
ttk.Button(frame_actions, text="🔄 刷新桌面列表", command=load_desktop_items).pack(side=tk.RIGHT)

# 表格区域 (带滚动条)
frame_tree = tk.Frame(root)
frame_tree.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)

scrollbar = ttk.Scrollbar(frame_tree)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# 定义两列：状态 和 文件名
tree = ttk.Treeview(frame_tree, columns=('Status', 'Name'), show='headings', yscrollcommand=scrollbar.set)
tree.heading('Status', text='状态 (点击切换)')
tree.heading('Name', text='文件/快捷方式名称')
tree.column('Status', width=100, anchor='center')
tree.column('Name', width=340, anchor='w')
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.config(command=tree.yview)

# 绑定点击事件用于切换勾选状态
tree.bind('', toggle_check)

# 底部时间设置区域
frame_bottom = ttk.LabelFrame(root, text=" 定时执行设置 ", padding=15)
frame_bottom.pack(padx=20, pady=15, fill=tk.X)

tk.Label(frame_bottom, text="每天自动清理时间:", font=("Microsoft YaHei", 10)).pack(side=tk.LEFT, padx=10)

hour_var = tk.StringVar(value="18")
min_var = tk.StringVar(value="00")

# 时间微调框
ttk.Spinbox(frame_bottom, from_=0, to=23, textvariable=hour_var, width=4, font=("Consolas", 11), format="%02.0f").pack(side=tk.LEFT)
tk.Label(frame_bottom, text=":", font=("Microsoft YaHei", 10, "bold")).pack(side=tk.LEFT, padx=2)
ttk.Spinbox(frame_bottom, from_=0, to=59, textvariable=min_var, width=4, font=("Consolas", 11), format="%02.0f").pack(side=tk.LEFT)

# 执行按钮
btn_apply = tk.Button(root, text="保存并启用计划", font=("Microsoft YaHei", 12, "bold"), 
                      bg="#2b579a", fg="white", activebackground="#1e3e6e", activeforeground="white",
                      width=18, command=apply_settings)
btn_apply.pack(pady=10)

# 初始化加载桌面文件
load_desktop_items()

root.mainloop()
