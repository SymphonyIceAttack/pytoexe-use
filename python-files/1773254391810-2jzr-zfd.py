import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import sys

class PortForwarder:
    def __init__(self, root):
        self.root = root
        self.root.title("LCX端口转发 - 转发端")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # 运行状态
        self.is_running = False
        self.local_socket = None
        self.threads = []
        
        # 创建UI
        self._create_widgets()

    def _create_widgets(self):
        # 本地监听端口
        ttk.Label(self.root, text="本地监听端口:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.local_port = ttk.Entry(self.root, width=20)
        self.local_port.grid(row=0, column=1, padx=10, pady=10)
        self.local_port.insert(0, "8888")

        # 监听端IP
        ttk.Label(self.root, text="监听端IP:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.listener_ip = ttk.Entry(self.root, width=20)
        self.listener_ip.grid(row=1, column=1, padx=10, pady=10)
        self.listener_ip.insert(0, "127.0.0.1")

        # 监听端端口
        ttk.Label(self.root, text="监听端端口:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.listener_port = ttk.Entry(self.root, width=20)
        self.listener_port.grid(row=2, column=1, padx=10, pady=10)
        self.listener_port.insert(0, "9999")

        # 控制按钮
        self.start_btn = ttk.Button(self.root, text="启动转发", command=self.start_forward)
        self.start_btn.grid(row=3, column=0, padx=10, pady=20)
        
        self.stop_btn = ttk.Button(self.root, text="停止转发", command=self.stop_forward, state=tk.DISABLED)
        self.stop_btn.grid(row=3, column=1, padx=10, pady=20)

        # 日志区域
        ttk.Label(self.root, text="运行日志:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.log_text = tk.Text(self.root, width=60, height=12)
        self.log_text.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _log(self, msg):
        """日志输出"""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, f"[{current_time}] {msg}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _forward_data(self, source, dest, tag):
        """双向数据转发"""
        try:
            while self.is_running:
                data = source.recv(4096)
                if not data:
                    self._log(f"{tag} 连接断开")
                    break
                dest.sendall(data)
        except Exception as e:
            if self.is_running:
                self._log(f"{tag} 转发异常: {str(e)}")
        finally:
            source.close()
            dest.close()

    def _local_listener(self):
        """本地端口监听"""
        try:
            self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.local_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.local_socket.bind(("0.0.0.0", int(self.local_port.get())))
            self.local_socket.listen(5)
            self._log(f"本地监听已启动: 0.0.0.0:{self.local_port.get()}")

            while self.is_running:
                # 接收本地客户端连接
                local_client, local_addr = self.local_socket.accept()
                self._log(f"本地客户端连接: {local_addr[0]}:{local_addr[1]}")

                # 连接监听端
                listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    listener_socket.connect((self.listener_ip.get(), int(self.listener_port.get())))
                    self._log(f"成功连接监听端: {self.listener_ip.get()}:{self.listener_port.get()}")

                    # 启动双向转发
                    t1 = threading.Thread(target=self._forward_data, 
                                        args=(local_client, listener_socket, "本地→监听端"))
                    t2 = threading.Thread(target=self._forward_data, 
                                        args=(listener_socket, local_client, "监听端→本地"))
                    t1.daemon = True
                    t2.daemon = True
                    t1.start()
                    t2.start()
                    self.threads.extend([t1, t2])
                except Exception as e:
                    self._log(f"连接监听端失败: {str(e)}")
                    local_client.close()
                    listener_socket.close()
        except Exception as e:
            if self.is_running:
                self._log(f"本地监听异常: {str(e)}")

    def start_forward(self):
        """启动转发"""
        # 参数校验
        try:
            local_port = int(self.local_port.get())
            listener_port = int(self.listener_port.get())
            if not (1 <= local_port <= 65535 and 1 <= listener_port <= 65535):
                messagebox.showerror("错误", "端口号必须在1-65535之间！")
                return
            if not self.listener_ip.get().strip():
                messagebox.showerror("错误", "监听端IP不能为空！")
                return
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字！")
            return

        # 启动转发
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._log("开始启动端口转发...")

        # 启动本地监听线程
        local_thread = threading.Thread(target=self._local_listener)
        local_thread.daemon = True
        local_thread.start()
        self.threads.append(local_thread)

    def stop_forward(self):
        """停止转发"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # 关闭本地socket
        if self.local_socket:
            try:
                self.local_socket.close()
            except:
                pass
        
        # 等待线程结束
        for t in self.threads:
            if t.is_alive():
                t.join(timeout=1)
        self.threads.clear()
        
        self._log("端口转发已停止")

    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            self.stop_forward()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PortForwarder(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()