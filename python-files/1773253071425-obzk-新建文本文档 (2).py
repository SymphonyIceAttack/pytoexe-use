import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import sys
import time

class PortForwarder:
    def __init__(self, root):
        self.root = root
        self.root.title("LCX端口转发工具")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 停止标志
        self.is_running = False
        self.threads = []
        
        # 创建UI组件
        self._create_widgets()

    def _create_widgets(self):
        # 1. 本地监听端口
        ttk.Label(self.root, text="本地监听端口:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.local_port = ttk.Entry(self.root, width=20)
        self.local_port.grid(row=0, column=1, padx=10, pady=10)
        self.local_port.insert(0, "8080")

        # 2. 目标IP
        ttk.Label(self.root, text="目标服务器IP:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.target_ip = ttk.Entry(self.root, width=20)
        self.target_ip.grid(row=1, column=1, padx=10, pady=10)
        self.target_ip.insert(0, "127.0.0.1")

        # 3. 目标端口
        ttk.Label(self.root, text="目标服务器端口:").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.target_port = ttk.Entry(self.root, width=20)
        self.target_port.grid(row=2, column=1, padx=10, pady=10)
        self.target_port.insert(0, "80")

        # 4. 控制按钮
        self.start_btn = ttk.Button(self.root, text="启动转发", command=self.start_forward)
        self.start_btn.grid(row=3, column=0, padx=10, pady=20)
        
        self.stop_btn = ttk.Button(self.root, text="停止转发", command=self.stop_forward, state=tk.DISABLED)
        self.stop_btn.grid(row=3, column=1, padx=10, pady=20)

        # 5. 日志显示框
        ttk.Label(self.root, text="运行日志:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.log_text = tk.Text(self.root, width=60, height=10)
        self.log_text.grid(row=5, column=0, columnspan=2, padx=10, pady=5)
        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.log_text.config(yscrollcommand=scrollbar.set)

    def _log(self, msg):
        """日志输出"""
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, f"[{current_time}] {msg}\n")
        self.log_text.see(tk.END)  # 自动滚动到最后
        self.root.update_idletasks()

    def _forward_data(self, source, dest):
        """数据转发核心函数"""
        try:
            while self.is_running:
                data = source.recv(4096)
                if not data:
                    break
                dest.sendall(data)
        except Exception as e:
            self._log(f"数据转发异常: {str(e)}")
        finally:
            source.close()
            dest.close()

    def _server_listener(self):
        """本地监听端口，接收连接并转发"""
        try:
            # 创建监听socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("0.0.0.0", int(self.local_port.get())))
            server_socket.listen(5)
            self._log(f"已启动本地监听: 0.0.0.0:{self.local_port.get()}")

            while self.is_running:
                # 等待客户端连接
                client_socket, client_addr = server_socket.accept()
                self._log(f"接收到客户端连接: {client_addr[0]}:{client_addr[1]}")

                # 连接目标服务器
                target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    target_socket.connect((self.target_ip.get(), int(self.target_port.get())))
                    self._log(f"成功连接目标服务器: {self.target_ip.get()}:{self.target_port.get()}")

                    # 启动双向转发线程
                    t1 = threading.Thread(target=self._forward_data, args=(client_socket, target_socket))
                    t2 = threading.Thread(target=self._forward_data, args=(target_socket, client_socket))
                    t1.daemon = True
                    t2.daemon = True
                    t1.start()
                    t2.start()
                    self.threads.append(t1)
                    self.threads.append(t2)

                except Exception as e:
                    self._log(f"连接目标服务器失败: {str(e)}")
                    client_socket.close()
                    target_socket.close()

        except Exception as e:
            if self.is_running:  # 非主动停止时的异常才输出
                self._log(f"监听异常: {str(e)}")
        finally:
            if 'server_socket' in locals():
                server_socket.close()

    def start_forward(self):
        """启动端口转发"""
        # 参数校验
        try:
            local_port = int(self.local_port.get())
            target_port = int(self.target_port.get())
            if not (1 <= local_port <= 65535 and 1 <= target_port <= 65535):
                messagebox.showerror("错误", "端口号必须在1-65535之间！")
                return
            if not self.target_ip.get().strip():
                messagebox.showerror("错误", "目标IP不能为空！")
                return
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字！")
            return

        # 启动转发
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self._log("开始启动端口转发...")

        # 启动监听线程
        listener_thread = threading.Thread(target=self._server_listener)
        listener_thread.daemon = True
        listener_thread.start()
        self.threads.append(listener_thread)

    def stop_forward(self):
        """停止端口转发"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
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