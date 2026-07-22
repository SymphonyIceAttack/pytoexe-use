import random
import string
import os
import subprocess
import tkinter as tk
from tkinter import scrolledtext

# 固定配置
PREFIX = "hsydn"
REMOTE_ADDR = "103.236.87.50:49885"
DESKTOP_PATH = os.path.expanduser("~/Desktop/AccountList.txt")
CHAR_POOL = string.ascii_letters + string.digits

def run_cmd(cmd: str) -> tuple[int, str]:
    """执行系统命令，返回退出码+输出"""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode, res.stdout + res.stderr

def generate_account():
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    log_text.insert(tk.END, "=== 开始生成账号 ===\n")

    # 生成10位用户名 hsydn(5)+5随机字符
    suffix = ''.join(random.choice(CHAR_POOL) for _ in range(5))
    username = PREFIX + suffix
    # 生成12位密码
    password = ''.join(random.choice(CHAR_POOL) for _ in range(12))

    log_text.insert(tk.END, f"生成用户名：{username}\n")
    log_text.insert(tk.END, f"生成密码：{password}\n")
    log_text.insert(tk.END, f"远程地址：{REMOTE_ADDR}\n\n")

    # 1. 创建本地用户
    create_cmd = f'net user "{username}" "{password}" /add /comment:"Remote access account"'
    code, out = run_cmd(create_cmd)
    if code != 0:
        log_text.insert(tk.END, f"【失败】创建用户失败：{out}\n")
        log_text.config(state=tk.DISABLED)
        return
    log_text.insert(tk.END, "【成功】本地用户创建完成\n")

    # 2. 密码永不过期
    run_cmd(f'wmic useraccount where name="{username}" set passwordexpires=false')
    run_cmd(f'wmic useraccount where name="{username}" set passwordrequired=true')

    # 3. 加入远程桌面权限组
    run_cmd(f'net localgroup "Remote Desktop Users" "{username}" /add')
    log_text.insert(tk.END, "【成功】已添加远程桌面登录权限\n")

    # 4. 开启远程桌面 + 防火墙放行
    run_cmd(r'reg add "HKLM\System\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f')
    run_cmd('netsh advfirewall firewall set rule group="remote desktop" new enable=yes')
    log_text.insert(tk.END, "【成功】远程桌面已开启，防火墙放行3389\n")

    # 5. 写入桌面文件
    with open(DESKTOP_PATH, "a", encoding="utf-8") as f:
        f.write("--------------------------\n")
        f.write(f"Username: {username}\n")
        f.write(f"Password: {password}\n")
        f.write(f"Remote: {REMOTE_ADDR}\n")
        f.write("--------------------------\n\n")
    log_text.insert(tk.END, f"【完成】账号信息已保存至桌面 AccountList.txt\n")
    log_text.config(state=tk.DISABLED)

# 构建GUI窗口
window = tk.Tk()
window.title("远程账号生成工具")
window.geometry("580x420")

# 按钮
gen_btn = tk.Button(window, text="一键生成并创建账号", command=generate_account, height=2, font=("Arial",12))
gen_btn.pack(pady=10, fill=tk.X, padx=20)

# 日志输出框
log_text = scrolledtext.ScrolledText(window, font=("Consolas", 10))
log_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
log_text.config(state=tk.DISABLED)

# 底部提示
tip_label = tk.Label(window, text="⚠️ 必须右键Python/此脚本，选择【以管理员身份运行】否则创建用户失败", fg="red")
tip_label.pack(pady=5)

window.mainloop()
