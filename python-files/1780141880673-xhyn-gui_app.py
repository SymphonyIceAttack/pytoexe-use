import tkinter as tk
from tkinter import messagebox
import socket
import time

HOST = "app.shoppingzhou.qzz.io"
PORT = 8080
DEBUG = True
TIMEOUT = 3
MAX_RETRY = 3

def http_send(msg: str) -> str:
    for _ in range(MAX_RETRY):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(TIMEOUT)
            sock.connect((HOST, PORT))
            local_ip = socket.gethostbyname(socket.gethostname())
            req = (
                f"GET /?msg={msg}&clientip={local_ip} HTTP/1.1\r\n"
                f"Host: {HOST}\r\n"
                "Connection: close\r\n\r\n"
            )
            sock.sendall(req.encode("utf-8"))
            resp = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk: break
                resp += chunk
            sock.close()
            resp_text = resp.decode("utf-8", errors="ignore")
            body = resp_text.split("\r\n\r\n", 1)[1].strip() if "\r\n\r\n" in resp_text else resp_text.strip()
            print("服务器真实返回 →", body)
            return body
        except Exception:
            continue
    return ""

# ======================
# 全局变量
# ======================
root = tk.Tk()
root.title("登录注册")
root.geometry("540x360")

reg = 0# 1=注册模式，0=登录模式
X = 170
login_name = ""
token = ""

switch_btn = None
username_entry = None
pwd_entry = None

# ======================
# 工具函数
# ======================
def show_warn():
    messagebox.showwarning("警告", "输入不能为空！")

def clear_window(win):
    for widget in win.winfo_children():
        widget.destroy()

def show_token():
    if token:
        messagebox.showinfo("你的Token", token)
    else:
        messagebox.showwarning("提示", "token 为空！\n查看控制台服务器返回！")

# ======================
# 登录界面
# ======================
def create_login_ui():
    global switch_btn, username_entry, pwd_entry
    clear_window(root)
    
    switch_btn = tk.Button(root, text="登录", command=switch_mode, padx=20, pady=1)
    switch_btn.place(x=X + 90, y=160)

    tk.Label(root, text="用户名", font=("等线", 12)).place(x=X - 60, y=80)
    tk.Label(root, text="密码", font=("等线", 12)).place(x=X - 55, y=120)

    username_entry = tk.Entry(root, font=("等线", 12))
    username_entry.place(x=X, y=80)

    pwd_entry = tk.Entry(root, font=("等线", 12))
    pwd_entry.place(x=X, y=120)

    tk.Button(root, text="提交", command=submit, padx=20, pady=1).place(x=X, y=160)

def switch_mode():
    global reg
    if reg == 1:
        switch_btn.config(text="登录")
        reg = 0
    else:
        switch_btn.config(text="注册")
        reg = 1

# ======================
# 提交登录（核心修复）
# ======================
def submit():
    global login_name, token
    user = username_entry.get()
    pwd = pwd_entry.get()

    if not user or not pwd:
        show_warn()
        return

    if reg == 1:
        res = http_send(f"testreg.{user}.{pwd}.")
        if res == 'ro':
            messagebox.showinfo("成功", "注册成功！")
        elif res == 'sn':
            messagebox.showerror("错误", "重名啦")
        else:
            messagebox.showerror("错误", "服务器未连接！")
    else:
        res = http_send(f"testlogin.{user}.{pwd}.")
        
        # ==============================================
        # ✅ 核心修复：强制把服务器返回的所有内容当 token 测试
        # ==============================================
        if res and "lo" in res:
            messagebox.showinfo("成功", "登录成功！")
            
            temp = res.split(".")
            print("分割后结果：", temp)
            
            # 自动找 token（不管在哪一位）
            if len(temp) >= 2:
                token = temp[1]
            else:
                token = res  # 兜底：直接把返回值当 token
            
            login_name = user
            
            clear_window(root)
            tk.Label(root, text=f"欢迎 {login_name}", font=("等线",14)).place(x=200,y=120)
            tk.Button(root, text="退出登录", command=back_login).place(x=170,y=180)
            tk.Button(root, text="显示token", command=show_token).place(x=250,y=180)
            return
        else:
            messagebox.showerror("错误", "用户名或密码错误！")

    username_entry.delete(0, tk.END)
    pwd_entry.delete(0, tk.END)

# ======================
# 退出登录
# ======================
def back_login():
    global login_name, token, reg
    login_name = ""
    token = ""
    reg = 1
    create_login_ui()

# ======================
# 启动
# ======================
create_login_ui()

# ======================
# 主循环
# ======================
while True:
    root.update()
    time.sleep(0.01)