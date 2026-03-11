import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import pickle
import zlib
from PIL import Image, ImageTk
import io
import pyautogui
import sys
import time

class RemoteController:
    def __init__(self, root):
        self.root = root
        self.root.title("远程协助 - 控制端")
        self.root.geometry("1000x700")
        
        # 连接状态
        self.is_connected = False
        self.client_socket = None
        self.screen_label = None
        self.screen_width = 0
        self.screen_height = 0
        
        # 创建UI
        self._create_widgets()

    def _create_widgets(self):
        # 连接配置区域
        config_frame = ttk.Frame(self.root)
        config_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(config_frame, text="被控端IP:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ip_entry = ttk.Entry(config_frame, width=20)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ip_entry.insert(0, "127.0.0.1")
        
        ttk.Label(config_frame, text="被控端端口:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.port_entry = ttk.Entry(config_frame, width=10)
        self.port_entry.grid(row=0, column=3, padx=5, pady=5)
        self.port_entry.insert(0, "5000")
        
        self.connect_btn = ttk.Button(config_frame, text="连接被控端", command=self.connect_client)
        self.connect_btn.grid(row=0, column=4, padx=10, pady=5)
        
        self.disconnect_btn = ttk.Button(config_frame, text="断开连接", command=self.disconnect_client, state=tk.DISABLED)
        self.disconnect_btn.grid(row=0, column=5, padx=10, pady=5)

        # 屏幕显示区域
        screen_frame = ttk.Frame(self.root)
        screen_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.screen_label = ttk.Label(screen_frame)
        self.screen_label.pack(fill=tk.BOTH, expand=True)
        
        # 绑定鼠标/键盘事件
        self.screen_label.bind("<Button-1>", self._on_mouse_click)
        self.screen_label.bind("<Button-3>", self._on_mouse_right_click)
        self.screen_label.bind("<Motion>", self._on_mouse_move)
        self.screen_label.bind("<MouseWheel>", self._on_mouse_scroll)
        self.root.bind("<Key>", self._on_key_press)

    def _log(self, msg, is_error=False):
        """提示信息"""
        if is_error:
            messagebox.showerror("错误", msg)
        else:
            messagebox.showinfo("提示", msg)

    def _recv_screen(self):
        """接收并显示被控端屏幕"""
        try:
            while self.is_connected:
                # 接收数据长度
                len_data = self.client_socket.recv(4096)
                if not len_data:
                    break
                data_len = pickle.loads(len_data)
                
                # 接收完整数据
                data = b""
                while len(data) < data_len:
                    packet = self.client_socket.recv(min(data_len - len(data), 4096))
                    if not packet:
                        break
                    data += packet
                
                # 解压缩并显示
                compressed_data = pickle.loads(data)
                img_data = zlib.decompress(compressed_data)
                img = Image.open(io.BytesIO(img_data))
                
                # 记录被控端屏幕尺寸
                self.screen_width, self.screen_height = img.size
                
                # 适配窗口大小
                win_width = self.screen_label.winfo_width()
                win_height = self.screen_label.winfo_height()
                if win_width > 0 and win_height > 0:
                    img = img.resize((win_width, win_height), Image.Resampling.LANCZOS)
                
                # 显示图片
                img_tk = ImageTk.PhotoImage(img)
                self.screen_label.config(image=img_tk)
                self.screen_label.image = img_tk
        except Exception as e:
            if self.is_connected:
                self._log(f"屏幕接收异常: {str(e)}", is_error=True)
                self.disconnect_client()

    def _send_cmd(self, cmd):
        """发送控制指令"""
        try:
            if self.is_connected:
                data = pickle.dumps(cmd)
                self.client_socket.sendall(data)
        except Exception as e:
            self._log(f"指令发送失败: {str(e)}", is_error=True)

    def _on_mouse_move(self, event):
        """鼠标移动事件"""
        if self.is_connected and self.screen_width > 0 and self.screen_height > 0:
            # 计算实际坐标
            x = int(event.x * self.screen_width / self.screen_label.winfo_width())
            y = int(event.y * self.screen_height / self.screen_label.winfo_height())
            cmd = {"type": "mouse_move", "x": x, "y": y}
            self._send_cmd(cmd)

    def _on_mouse_click(self, event):
        """鼠标左键点击"""
        if self.is_connected and self.screen_width > 0 and self.screen_height > 0:
            x = int(event.x * self.screen_width / self.screen_label.winfo_width())
            y = int(event.y * self.screen_height / self.screen_label.winfo_height())
            cmd = {"type": "mouse_click", "x": x, "y": y, "button": "left"}
            self._send_cmd(cmd)

    def _on_mouse_right_click(self, event):
        """鼠标右键点击"""
        if self.is_connected and self.screen_width > 0 and self.screen_height > 0:
            x = int(event.x * self.screen_width / self.screen_label.winfo_width())
            y = int(event.y * self.screen_height / self.screen_label.winfo_height())
            cmd = {"type": "mouse_click", "x": x, "y": y, "button": "right"}
            self._send_cmd(cmd)

    def _on_mouse_scroll(self, event):
        """鼠标滚轮"""
        if self.is_connected and self.screen_width > 0 and self.screen_height > 0:
            x = int(event.x * self.screen_width / self.screen_label.winfo_width())
            y = int(event.y * self.screen_height / self.screen_label.winfo_height())
            delta = event.delta // 120  # 标准化滚轮值
            cmd = {"type": "mouse_scroll", "x": x, "y": y, "delta": delta}
            self._send_cmd(cmd)

    def _on_key_press(self, event):
        """键盘按键"""
        if self.is_connected:
            key = event.keysym
            cmd = {"type": "keyboard", "key": key}
            self._send_cmd(cmd)

    def connect_client(self):
        """连接被控端"""
        # 参数校验
        ip = self.ip_entry.get().strip()
        try:
            port = int(self.port_entry.get())
            if not (1 <= port <= 65535):
                self._log("端口号必须在1-65535之间！", is_error=True)
                return
            if not ip:
                self._log("被控端IP不能为空！", is_error=True)
                return
        except ValueError:
            self._log("端口号必须是数字！", is_error=True)
            return

        # 建立连接
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
            self.is_connected = True
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
            self._log(f"成功连接被控端: {ip}:{port}")
            
            # 启动屏幕接收线程
            screen_thread = threading.Thread(target=self._recv_screen)
            screen_thread.daemon = True
            screen_thread.start()
        except Exception as e:
            self._log(f"连接失败: {str(e)}", is_error=True)

    def disconnect_client(self):
        """断开连接"""
        self.is_connected = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        self.connect_btn.config(state=tk.NORMAL)
        self.disconnect_btn.config(state=tk.DISABLED)
        self.screen_label.config(image="")
        self._log("已断开与被控端的连接")

    def on_closing(self):
        """窗口关闭事件"""
        if self.is_connected:
            self.disconnect_client()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteController(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()