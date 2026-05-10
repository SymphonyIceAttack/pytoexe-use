import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import socket
import threading
import time
import os

# ---------- 配置文件路径 ----------
CONFIG_FILE = "remark_config.txt"

def load_remark():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    return content
        except:
            pass
    return "双击备注区域可修改（自动保存）"

def save_remark(remark_text):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(remark_text)
    except:
        pass

class TcpKeySender:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("TCP 键盘发送器")
        self.root.geometry("900x800")
        self.root.minsize(900, 800)
        self.root.configure(bg='#f0f2f5')
        
        # 网络变量
        self.sock = None
        self.connected = False
        self.target_ip = tk.StringVar(value="127.0.0.1")
        self.target_port = tk.StringVar(value="8080")
        self.remark = load_remark()
        
        # 日志队列（最多保留200条，显示最后20条）
        self.log_lines = []
        
        # 频率限制：上一次发送的时间（秒）
        self.last_send_time = 0
        self.send_interval = 1.0  # 每秒最多一次
        
        # 创建界面
        self.create_widgets()
        
        # 绑定全局快捷键（窗口焦点时生效）
        self.bind_hotkeys()
        
        # 更新状态显示
        self.update_status()
        
        # 启动键盘监听（独立线程）
        self.start_keyboard_listener()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    
    def create_widgets(self):
        # 标题栏
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=70)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        title_label = tk.Label(title_frame, text="⌨️ TCP 键盘发送器", font=('微软雅黑', 18, 'bold'), 
                               fg='white', bg='#2c3e50')
        title_label.pack(pady=15)
        
        # 主体区域使用 Frame 布局
        main_frame = tk.Frame(self.root, bg='#f0f2f5')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # ----- 连接配置区域 -----
        config_frame = tk.LabelFrame(main_frame, text=" 连接配置 ", font=('微软雅黑', 10, 'bold'),
                                     bg='#ffffff', fg='#2c3e50', relief=tk.GROOVE, bd=2)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # IP 行
        ip_frame = tk.Frame(config_frame, bg='#ffffff')
        ip_frame.pack(fill=tk.X, padx=15, pady=(15, 10))
        tk.Label(ip_frame, text="目标 IP：", width=10, anchor='e', bg='#ffffff', 
                 font=('微软雅黑', 10)).pack(side=tk.LEFT)
        ip_entry = tk.Entry(ip_frame, textvariable=self.target_ip, font=('Consolas', 10), 
                            bg='#fafafa', relief=tk.SUNKEN, bd=1)
        ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 端口行
        port_frame = tk.Frame(config_frame, bg='#ffffff')
        port_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        tk.Label(port_frame, text="端  口：", width=10, anchor='e', bg='#ffffff',
                 font=('微软雅黑', 10)).pack(side=tk.LEFT)
        port_entry = tk.Entry(port_frame, textvariable=self.target_port, font=('Consolas', 10),
                              bg='#fafafa', relief=tk.SUNKEN, bd=1)
        port_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # 按钮区域
        btn_frame = tk.Frame(config_frame, bg='#ffffff')
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.connect_btn = tk.Button(btn_frame, text="🔌 连接 (F2)", command=self.do_connect,
                                     bg='#3498db', fg='white', font=('微软雅黑', 10, 'bold'),
                                     relief=tk.FLAT, padx=12, pady=5, cursor='hand2')
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.disconnect_btn = tk.Button(btn_frame, text="⛔ 断开 (F3)", command=self.do_disconnect,
                                        bg='#e74c3c', fg='white', font=('微软雅黑', 10, 'bold'),
                                        relief=tk.FLAT, padx=12, pady=5, cursor='hand2')
        self.disconnect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="✏️ 修改目标 (F1)", command=self.change_target,
                  bg='#95a5a6', fg='white', font=('微软雅黑', 10, 'bold'),
                  relief=tk.FLAT, padx=12, pady=5, cursor='hand2').pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Button(btn_frame, text="📝 修改备注 (F4)", command=self.change_remark,
                  bg='#f39c12', fg='white', font=('微软雅黑', 10, 'bold'),
                  relief=tk.FLAT, padx=12, pady=5, cursor='hand2').pack(side=tk.LEFT)
        
        # ----- 备注显示区域（可编辑）-----
        remark_frame = tk.LabelFrame(main_frame, text=" 备注 ", font=('微软雅黑', 10, 'bold'),
                                     bg='#ffffff', fg='#2c3e50', relief=tk.GROOVE, bd=2)
        remark_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.remark_text = tk.Text(remark_frame, height=2, wrap=tk.WORD, font=('微软雅黑', 10),
                                   bg='#fff9e6', relief=tk.SUNKEN, bd=1)
        self.remark_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.remark_text.insert('1.0', self.remark)
        # 绑定焦点离开时自动保存
        self.remark_text.bind('<FocusOut>', self.on_remark_focus_out)
        
        # ----- 发送记录区域 -----
        log_frame = tk.LabelFrame(main_frame, text=" 发送记录 (最近20条) ", font=('微软雅黑', 10, 'bold'),
                                  bg='#ffffff', fg='#2c3e50', relief=tk.GROOVE, bd=2)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, font=('Consolas', 9),
                                                   bg='#1e272e', fg='#d2dae2', relief=tk.FLAT,
                                                   insertbackground='white')
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_area.config(state=tk.DISABLED)
        
        # ----- 状态栏 -----
        status_frame = tk.Frame(self.root, bg='#2c3e50', height=35)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = tk.Label(status_frame, text="● 未连接", font=('微软雅黑', 9),
                                     bg='#2c3e50', fg='#ecf0f1', anchor='w')
        self.status_label.pack(side=tk.LEFT, padx=15, pady=5)
        
        # 提示标签
        tip_label = tk.Label(status_frame, text="快捷键: F1-修改目标  F2-连接  F3-断开  F4-修改备注  ESC-退出 | 按键限速: 1次/秒",
                             font=('微软雅黑', 8), bg='#2c3e50', fg='#bdc3c7')
        tip_label.pack(side=tk.RIGHT, padx=15, pady=5)
    
    def bind_hotkeys(self):
        """绑定键盘快捷键"""
        self.root.bind('<F1>', lambda e: self.change_target())
        self.root.bind('<F2>', lambda e: self.do_connect())
        self.root.bind('<F3>', lambda e: self.do_disconnect())
        self.root.bind('<F4>', lambda e: self.change_remark())
        self.root.bind('<Escape>', lambda e: self.on_close())
    
    def start_keyboard_listener(self):
        """独立线程监听全局键盘（使用 pynput）"""
        try:
            from pynput import keyboard
        except ImportError:
            self.add_log("警告: pynput 未安装，无法发送按键值。请运行 pip install pynput", 'error')
            return
        
        def on_press(key):
            # 跳过功能键
            try:
                if key == keyboard.Key.f1 or key == keyboard.Key.f2 or key == keyboard.Key.f3 or key == keyboard.Key.f4 or key == keyboard.Key.esc:
                    return
                
                # 频率限制检查
                current_time = time.time()
                if current_time - self.last_send_time < self.send_interval:
                    # 距离上次发送不足1秒，丢弃本次按键
                    return
                
                # 获取按键字符
                if hasattr(key, 'char') and key.char is not None:
                    data = key.char
                else:
                    data = f"<{key.name}>"
                
                # 发送到 TCP
                if self.connected and self.sock:
                    try:
                        self.sock.sendall(data.encode('utf-8'))
                        self.last_send_time = current_time  # 更新上次发送时间
                        self.add_log(f"发送 -> {data}", 'send')
                    except Exception as e:
                        self.add_log(f"发送失败: {e}", 'error')
                        self.do_disconnect()
                else:
                    # 未连接时仍然消耗限制吗？不消耗，避免频繁提示
                    pass
            except:
                pass
        
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
    
    def add_log(self, msg, msg_type='info'):
        """添加一条记录到日志区域"""
        timestamp = time.strftime("%H:%M:%S")
        if msg_type == 'send':
            formatted = f"[{timestamp}] ✉️ {msg}"
        elif msg_type == 'error':
            formatted = f"[{timestamp}] ❌ {msg}"
        elif msg_type == 'success':
            formatted = f"[{timestamp}] ✅ {msg}"
        else:
            formatted = f"[{timestamp}] ℹ️ {msg}"
        
        self.log_lines.append(formatted)
        # 保持最多200条，显示20条
        if len(self.log_lines) > 200:
            self.log_lines.pop(0)
        
        # 更新显示
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete('1.0', tk.END)
        # 显示最近20条
        for line in self.log_lines[-20:]:
            self.log_area.insert(tk.END, line + '\n')
        self.log_area.see(tk.END)
        self.log_area.config(state=tk.DISABLED)
    
    def update_status(self):
        """更新状态栏和按钮状态"""
        if self.connected:
            self.status_label.config(text=f"● 已连接 → {self.target_ip.get()}:{self.target_port.get()}", fg='#2ecc71')
            self.connect_btn.config(state=tk.DISABLED, bg='#bdc3c7')
            self.disconnect_btn.config(state=tk.NORMAL, bg='#e74c3c')
        else:
            self.status_label.config(text="○ 未连接", fg='#e74c3c')
            self.connect_btn.config(state=tk.NORMAL, bg='#3498db')
            self.disconnect_btn.config(state=tk.DISABLED, bg='#bdc3c7')
    
    def connect_socket(self, host, port):
        """建立 TCP 连接"""
        try:
            if self.sock:
                self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(3)
            self.sock.connect((host, port))
            self.sock.settimeout(None)
            self.connected = True
            return True
        except Exception as e:
            self.connected = False
            return False
    
    def disconnect_socket(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        self.connected = False
    
    def do_connect(self):
        """连接按钮动作"""
        ip = self.target_ip.get().strip()
        port_str = self.target_port.get().strip()
        if not ip:
            messagebox.showerror("错误", "IP地址不能为空")
            return
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except:
            messagebox.showerror("错误", "端口必须是1-65535的数字")
            return
        
        self.add_log(f"正在连接 {ip}:{port} ...", 'info')
        def connect_thread():
            if self.connect_socket(ip, port):
                self.add_log(f"连接成功", 'success')
                self.root.after(0, self.update_status)
            else:
                self.add_log(f"连接失败，请检查目标服务是否开启", 'error')
                self.root.after(0, self.update_status)
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def do_disconnect(self):
        """断开连接"""
        if self.connected:
            self.disconnect_socket()
            self.add_log("已主动断开连接", 'info')
            self.update_status()
        else:
            self.add_log("当前未连接", 'info')
    
    def change_target(self):
        """修改目标 IP/端口 (F1)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改目标")
        dialog.geometry("350x180")
        dialog.resizable(False, False)
        dialog.configure(bg='white')
        
        tk.Label(dialog, text="IP 地址:", bg='white', font=('微软雅黑', 10)).pack(pady=(15,5))
        ip_var = tk.StringVar(value=self.target_ip.get())
        ip_entry = tk.Entry(dialog, textvariable=ip_var, font=('Consolas', 10), width=30)
        ip_entry.pack()
        
        tk.Label(dialog, text="端  口:", bg='white', font=('微软雅黑', 10)).pack(pady=(10,5))
        port_var = tk.StringVar(value=self.target_port.get())
        port_entry = tk.Entry(dialog, textvariable=port_var, font=('Consolas', 10), width=30)
        port_entry.pack()
        
        def save():
            new_ip = ip_var.get().strip()
            new_port_str = port_var.get().strip()
            if not new_ip:
                messagebox.showerror("错误", "IP不能为空")
                return
            try:
                new_port = int(new_port_str)
                if not (1 <= new_port <= 65535):
                    raise ValueError
            except:
                messagebox.showerror("错误", "端口无效")
                return
            self.target_ip.set(new_ip)
            self.target_port.set(new_port_str)
            self.add_log(f"目标已更改为 {new_ip}:{new_port} (未自动连接)", 'info')
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="确定", command=save, bg='#3498db', fg='white', padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, bg='#95a5a6', fg='white', padx=20).pack(side=tk.LEFT)
        
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
    
    def change_remark(self):
        """修改备注 (F4)"""
        dialog = tk.Toplevel(self.root)
        dialog.title("修改备注")
        dialog.geometry("450x200")
        dialog.configure(bg='white')
        
        tk.Label(dialog, text="备注内容:", bg='white', font=('微软雅黑', 10)).pack(pady=(10,5))
        text_widget = tk.Text(dialog, height=5, wrap=tk.WORD, font=('微软雅黑', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        text_widget.insert('1.0', self.remark)
        
        def save_remark():
            new_remark = text_widget.get('1.0', tk.END).strip()
            if new_remark:
                self.remark = new_remark
                save_remark(self.remark)
                self.remark_text.delete('1.0', tk.END)
                self.remark_text.insert('1.0', self.remark)
                self.add_log(f"备注已修改", 'success')
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "备注不能为空")
        
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="保存", command=save_remark, bg='#f39c12', fg='white', padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=dialog.destroy, bg='#95a5a6', fg='white', padx=20).pack(side=tk.LEFT)
        
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)
    
    def on_remark_focus_out(self, event):
        new_remark = self.remark_text.get('1.0', tk.END).strip()
        if new_remark and new_remark != self.remark:
            self.remark = new_remark
            save_remark(self.remark)
            self.add_log(f"备注已自动保存", 'info')
    
    def on_close(self):
        self.disconnect_socket()
        self.root.destroy()
        os._exit(0)

if __name__ == "__main__":
    TcpKeySender()