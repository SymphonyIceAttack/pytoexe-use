import socket
import threading
import json
import base64
import io
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext
import pyautogui
from PIL import Image, ImageTk

# ==================== 全局配置 ====================
QUALITY_DICT = {"低画质": 50, "中画质": 75, "高画质": 95}
CONNECT_SOCK = None
IS_CONNECT = False
SELF_SHARE = False
TARGET_IP = ""

# ==================== 合规文本 ====================
USER_AGREEMENT = """【用户使用协议】
1.本软件仅用于合法远程教学、协助、屏幕共享。
2.禁止在对方不知情、未授权下静默控制、私自安装、远程操控。
3.禁止用于黑客入侵、信息窃取、非法监控等违法行为。
4.开启屏幕共享即代表自愿授权他人控制本机设备。
5.违规使用一切法律后果由使用者自行承担。
继续使用即代表同意以上全部条款。"""

DANGER_TIP = """⚠️ 严重风险警告 ⚠️
开启屏幕共享后：
1.他人可实时查看你的全部屏幕内容
2.可操控你的鼠标、键盘、打字、打开软件
3.可执行CMD命令、读取本地文件
4.存在隐私泄露、资料被盗风险

请确认：无重要隐私、仅信任人员操控，谨慎开启！"""

# ==================== 主窗口 ====================
class ClientApp:
    def __init__(self, root):
        self.root = root
        self.root.title("屏幕共享平台 - 用户端")
        self.root.geometry("920x680")
        self.root.resizable(True, True)

        self.img_quality = 75
        self.init_ui()
        self.show_agreement()

    def init_ui(self):
        # ========== 服务器连接区域（可自由输入IP和端口） ==========
        conn_frame = ttk.LabelFrame(self.root, text="服务器连接设置")
        conn_frame.pack(fill=tk.X, padx=10, pady=6)

        ttk.Label(conn_frame, text="服务器IP：").grid(row=0, column=0, padx=5, pady=8)
        self.ip_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(conn_frame, textvariable=self.ip_var, width=28).grid(row=0, column=1, padx=3)

        ttk.Label(conn_frame, text="端口：").grid(row=0, column=2, padx=5)
        self.port_var = tk.StringVar(value="")  # 空的，让用户自己填
        ttk.Entry(conn_frame, textvariable=self.port_var, width=12).grid(row=0, column=3, padx=3)

        ttk.Label(conn_frame, text="画质：").grid(row=0, column=4, padx=5)
        self.quality_var = tk.StringVar(value="中画质")
        ttk.Combobox(conn_frame, textvariable=self.quality_var, values=list(QUALITY_DICT.keys()), width=8).grid(row=0, column=5)

        self.conn_btn = ttk.Button(conn_frame, text="连接服务器", command=self.connect_server)
        self.conn_btn.grid(row=0, column=6, padx=12)  # 这里已修复：pad → padx（你报错的地方）

        # ========== 功能按钮 ==========
        func_frame = ttk.Frame(self.root)
        func_frame.pack(fill=tk.X, padx=10, pady=4)

        self.share_btn = ttk.Button(func_frame, text="开启屏幕共享", command=self.toggle_share, state=tk.DISABLED)
        self.share_btn.pack(side=tk.LEFT, padx=5)

        self.send_msg_btn = ttk.Button(func_frame, text="发送留言", command=self.send_msg, state=tk.DISABLED)
        self.send_msg_btn.pack(side=tk.LEFT, padx=5)

        self.send_cmd_btn = ttk.Button(func_frame, text="远程CMD命令", command=self.send_cmd, state=tk.DISABLED)
        self.send_cmd_btn.pack(side=tk.LEFT, padx=5)

        # ========== 左侧在线设备 ==========
        left_frame = ttk.LabelFrame(self.root, text="在线共享设备（点击选择控制）")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        self.device_list = tk.Listbox(left_frame, width=24, height=28)
        self.device_list.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.device_list.bind("<<ListboxSelect>>", self.select_target)

        # ========== 右侧屏幕显示（已修复 bg 报错） ==========
        right_frame = ttk.LabelFrame(self.root, text="远程屏幕画面")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.configure("ScreenLabel.TLabel", background="#eeeeee")
        self.screen_label = ttk.Label(right_frame, text="未连接设备", style="ScreenLabel.TLabel")
        self.screen_label.pack(fill=tk.BOTH, expand=True)

        # 绑定控制
        self.screen_label.bind("<Motion>", self.on_mouse_move)
        self.screen_label.bind("<ButtonPress>", self.on_mouse_click)
        self.root.bind("<Key>", self.on_key_input)

        # ========== 日志 ==========
        log_frame = ttk.LabelFrame(self.root, text="运行日志")
        log_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=5, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def show_agreement(self):
        if not messagebox.askyesno("用户协议", USER_AGREEMENT):
            self.root.destroy()
            exit()

    def add_log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"▶ {text}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def connect_server(self):
        global CONNECT_SOCK, IS_CONNECT
        if IS_CONNECT:
            messagebox.showinfo("提示", "已连接服务器")
            return

        ip = self.ip_var.get().strip()
        port_str = self.port_var.get().strip()

        if not ip or not port_str:
            messagebox.showwarning("错误", "请填写IP和端口！")
            return

        try:
            port = int(port_str)
        except:
            messagebox.showerror("错误", "端口必须是数字")
            return

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(7)
            sock.connect((ip, port))

            CONNECT_SOCK = sock
            IS_CONNECT = True
            self.conn_btn.config(text="已连接", state=tk.DISABLED)
            self.share_btn.config(state=tk.NORMAL)
            self.send_msg_btn.config(state=tk.NORMAL)
            self.send_cmd_btn.config(state=tk.NORMAL)
            self.add_log(f"成功连接服务器 → {ip}:{port}")

            threading.Thread(target=self.recv_loop, daemon=True).start()
        except Exception as e:
            messagebox.showerror("连接失败", f"无法连接：{str(e)}")

    def recv_loop(self):
        global IS_CONNECT
        while IS_CONNECT:
            try:
                data = CONNECT_SOCK.recv(1024 * 16)
                if not data:
                    break
                msg = json.loads(data.decode("utf-8"))
                t = msg.get("type")

                if t == "device_list":
                    self.refresh_device(msg["data"])
                elif t == "screen_data":
                    self.refresh_screen(msg["data"])
                elif t == "mouse":
                    pyautogui.moveTo(msg["x"], msg["y"])
                    if msg.get("btn") == "left":
                        pyautogui.click()
                elif t == "keyboard":
                    pyautogui.typewrite(msg["key"])
                elif t == "msg":
                    messagebox.showinfo("收到留言", msg["content"])
                elif t == "cmd":
                    import os
                    os.popen(msg["content"])
            except:
                continue
        IS_CONNECT = False
        self.add_log("与服务器断开连接")

    def refresh_device(self, dev_list):
        self.device_list.delete(0, tk.END)
        for dev in dev_list:
            status = "🟢 已共享" if dev["share"] else "⚫ 未共享"
            self.device_list.insert(tk.END, f"{dev['ip']} | {status}")

    def select_target(self, event):
        global TARGET_IP
        idx = self.device_list.curselection()
        if not idx:
            return
        item = self.device_list.get(idx[0])
        TARGET_IP = item.split(" ")[0]
        self.add_log(f"已选择控制目标：{TARGET_IP}")

    def toggle_share(self):
        global SELF_SHARE
        if not SELF_SHARE:
            if not messagebox.askyesno("⚠️ 危险警告", DANGER_TIP):
                return
            SELF_SHARE = True
            self.share_btn.config(text="关闭屏幕共享")
            self.add_log("已开启屏幕共享")
            threading.Thread(target=self.screen_send_loop, daemon=True).start()
        else:
            SELF_SHARE = False
            self.share_btn.config(text="开启屏幕共享")
            self.add_log("已关闭屏幕共享")

        try:
            CONNECT_SOCK.send(json.dumps({"type": "set_share", "status": SELF_SHARE}).encode())
        except:
            pass

    def screen_send_loop(self):
        while SELF_SHARE and IS_CONNECT:
            try:
                img = pyautogui.screenshot()
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=QUALITY_DICT[self.quality_var.get()])
                b64 = base64.b64encode(buf.getvalue()).decode()
                packet = {
                    "type": "screen_data",
                    "target_ip": TARGET_IP if TARGET_IP else "",
                    "data": b64
                }
                CONNECT_SOCK.send(json.dumps(packet).encode())
                threading.Event().wait(0.05)
            except:
                break

    def refresh_screen(self, b64_str):
        try:
            img_bytes = base64.b64decode(b64_str)
            img = Image.open(io.BytesIO(img_bytes))
            w = self.screen_label.winfo_width()
            h = self.screen_label.winfo_height()
            if w > 50 and h > 50:
                img = img.resize((w, h), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.screen_label.config(image=self.tk_img)
        except:
            pass

    def on_mouse_move(self, event):
        if not TARGET_IP: return
        try:
            sw, sh = pyautogui.size()
            w = self.screen_label.winfo_width()
            h = self.screen_label.winfo_height()
            x = int(event.x / w * sw)
            y = int(event.y / h * sh)
            data = json.dumps({"type": "mouse", "target_ip": TARGET_IP, "x": x, "y": y, "btn": ""})
            CONNECT_SOCK.send(data.encode())
        except:
            pass

    def on_mouse_click(self, event):
        if not TARGET_IP: return
        data = json.dumps({"type": "mouse", "target_ip": TARGET_IP, "btn": "left"})
        try:
            CONNECT_SOCK.send(data.encode())
        except:
            pass

    def on_key_input(self, event):
        if not TARGET_IP: return
        data = json.dumps({"type": "keyboard", "target_ip": TARGET_IP, "key": event.keysym})
        try:
            CONNECT_SOCK.send(data.encode())
        except:
            pass

    def send_msg(self):
        if not TARGET_IP:
            messagebox.showwarning("提示", "请先选择设备")
            return
        content = simpledialog.askstring("发送留言", "输入内容：")
        if content:
            data = json.dumps({"type": "msg", "target_ip": TARGET_IP, "content": content})
            CONNECT_SOCK.send(data.encode())
            self.add_log("留言已发送")

    def send_cmd(self):
        if not TARGET_IP:
            messagebox.showwarning("提示", "请先选择设备")
            return
        cmd = simpledialog.askstring("远程CMD", "输入命令：")
        if cmd:
            data = json.dumps({"type": "cmd", "target_ip": TARGET_IP, "content": cmd})
            CONNECT_SOCK.send(data.encode())
            self.add_log(f"命令已发送：{cmd}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()