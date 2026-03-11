import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import pyautogui
import pickle
import zlib
import base64
from PIL import Image
import io
import sys
import time

class RemoteClient:
    def __init__(self, root):
        self.root = root
        self.root.title("远程协助 - 被控端")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        
        # 连接状态
        self.is_connected = False
        self.server_socket = None
        self.conn = None
        self.addr = None
        
        # 创建UI
        self._create_widgets()

    def _create_widgets(self):
        # 端口配置
        ttk.Label(self.root, text="监听端口:").grid(row=0, column=0, padx=10, pady=15, sticky="e")
        self.port_entry = ttk.Entry(self.root, width=20)
        self.port_entry.grid(row=0, column=1, padx=10, pady=15)
        self.port_entry.insert(0, "5000")

        # 控制按钮
        self.start_btn = ttk.Button(self.root, text="启动被控端", command=self.start_server)
        self.start_btn.grid(row=1, column=0, padx=10, pady=10)
        
        self.stop_btn = ttk.Button(self.root, text="停止被控端", command=self.stop_server, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=1, padx=10, pady=10)

        # 状态日志
        ttk.Label(self.root, text="运行状态:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.status_text = tk.Text(self.root, width=45, height=5)
        self.status_text.grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        self.status_text.config(state=tk.DISABLED)

    def _log(self, msg):
        """状态日志输出"""
        self.status_text.config(state=tk.NORMAL)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.status_text.insert(tk.END, f"[{current_time}] {msg}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def _send_screen(self):
        """截取并发送屏幕数据"""
        try:
            while self.is_connected:
                # 截取屏幕
                screenshot = pyautogui.screenshot()
                # 压缩图片
                img_byte_arr = io.BytesIO()
                screenshot.save(img_byte_arr, format='JPEG', quality=50)
                img_byte_arr = img_byte_arr.getvalue()
                # 压缩数据
                compressed_data = zlib.compress(img_byte_arr)
                # 序列化
                data = pickle.dumps(compressed_data)
                # 发送数据长度 + 数据
                data_len = len(data)
                self.conn.sendall(pickle.dumps(data_len))
                self.conn.sendall(data)
                time.sleep(0.05)  # 控制帧率，降低带宽占用
        except Exception as e:
            if self.is_connected:
                self._log(f"屏幕传输异常: {str(e)}")
                self.is_connected = False

    def _handle_control(self):
        """处理控制端的鼠标/键盘指令"""
        try:
            while self.is_connected:
                # 接收指令
                cmd_data = self.conn.recv(4096)
                if not cmd_data:
                    break
                cmd = pickle.loads(cmd_data)
                
                # 解析指令
                if cmd["type"] == "mouse_move":
                    pyautogui.moveTo(cmd["x"], cmd["y"])
                elif cmd["type"] == "mouse_click":
                    pyautogui.click(cmd["x"], cmd["y"], button=cmd["button"])
                elif cmd["type"] == "mouse_scroll":
                    pyautogui.scroll(cmd["delta"], x=cmd["x"], y=cmd["y"])
                elif cmd["type"] == "keyboard":
                    pyautogui.press(cmd["key"])
        except Exception as e:
            if self.is_connected:
                self._log(f"控制指令处理异常: {str(e)}")
                self.is_connected = False

    def _accept_connection(self):
        """等待控制端连接"""
        while self.is_connected:
            try:
                self.conn, self.addr = self.server_socket.accept()
                self._log(f"控制端已连接: {self.addr[0]}:{self.addr[1]}")
                self.is_connected = True
                
                # 启动屏幕传输线程
                screen_thread = threading.Thread(target=self._send_screen)
                screen_thread.daemon = True
                screen_thread.start()
                
                # 启动控制指令处理线程
                control_thread = threading.Thread(target=self._handle_control)
                control_thread.daemon = True
                control_thread.start()
            except Exception as e:
                if self.is_connected:
                    self._log(f"接收连接异常: {str(e)}")

    def start_server(self):
        """启动被控端"""
        # 参数校验
        try:
            port = int(self.port_entry.get())
            if not (1 <= port <= 65535):
                messagebox.showerror("错误", "端口号必须在1-65535之间！")
                return
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字！")
            return

        # 启动监听
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", port))
            self.server_socket.listen(5)
            self.is_connected = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self._log(f"被控端已启动，监听端口: {port}")
            
            # 启动连接接收线程
            accept_thread = threading.Thread(target=self._accept_connection)
            accept_thread.daemon = True
            accept_thread.start()
        except Exception as e:
            self._log(f"启动失败: {str(e)}")
            messagebox.showerror("错误", f"启动失败: {str(e)}")

    def stop_server(self):
        """停止被控端"""
        self.is_connected = False
        # 关闭连接
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        # 关闭监听socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        # 重置UI
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self._log("被控端已停止")

    def on_closing(self):
        """窗口关闭事件"""
        if self.is_connected:
            self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = RemoteClient(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()