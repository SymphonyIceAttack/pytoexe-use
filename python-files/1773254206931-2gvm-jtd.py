import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import time
import sys

class PortListener:
    def __init__(self, root):
        self.root = root
        self.root.title("LCX端口转发 - 监听端")
        self.root.geometry("500x400")
        self.root.resizable(False, False)
        
        # 运行状态
        self.is_running = False
        self.server_socket = None
        self.threads = []
        
        # 创建UI
        self._create_widgets()

    def _create_widgets(self):
        # 监听端口配置
        ttk.Label(self.root, text="监听端口:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.listen_port = ttk.Entry(self.root, width=20)
        self.listen_port.grid(row=0, column=1, padx=10, pady=10)
        self.listen_port.insert(0, "9999")

        # 控制按钮
        self.start_btn = ttk.Button(self.root, text="启动监听", command=self.start_listen)
        self.start_btn.grid(row=1, column=0, padx=10, pady=20)
        
        self.stop_btn = ttk.Button(self.root, text="停止监听", command=self.stop_listen, state=tk.DISABLED)
        self.stop_btn.grid(row=1, column=1, padx=10, pady=20)

        # 日志区域
        ttk.Label(self.root, text="运行日志:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.log_text = tk.Text(self.root, width=60, height=12)
        self.log_text.grid(row=3, column=0, columnspan=2, padx=10, pady=5)
        scrollbar = ttk.Scrollbar(self.root, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=3, column=2, sticky="ns")
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

    def _handle_client(self, client_socket, client_addr):
        """处理转发端连接"""
        self._log(f"转发端已连接: {client_addr[0]}:{client_addr[1]}")
        
        # 等待外部客户端连接（反向转发核心）
        self._log("等待外部客户端连接监听端口...")
        try:
            external_socket, external_addr = self.server_socket.accept()
            self._log(f"外部客户端已连接: {external_addr[0]}:{external_addr[1]}")
            
            # 启动双向转发线程
            t1 = threading.Thread(target=self._forward_data, 
                                args=(client_socket, external_socket, "转发端→客户端"))
            t2 = threading.Thread(target=self._forward_data, 
                                args=(external_socket, client_socket, "客户端→转发端"))
            t1.daemon = True
            t2.daemon = True
            t1.start()
            t2.start()
            self.threads.extend([t1, t2])
        except Exception as e:
            self._log(f"接收外部客户端连接失败: {str(e)}")
            client_socket.close()

    def start_listen(self):
        """启动监听"""
        # 参数校验
        try:
            port = int(self.listen_port.get())
            if not (1 <= port <= 65535):
                messagebox.showerror("错误", "端口号必须在1-65535之间！")
                return
        except ValueError:
            messagebox.showerror("错误", "端口号必须是数字！")
            return

        # 启动监听
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("0.0.0.0", port))
            self.server_socket.listen(5)
            self._log(f"监听端已启动，监听 0.0.0.0:{port}")

            # 监听转发端连接
            listen_thread = threading.Thread(target=self._accept_forwarder)
            listen_thread.daemon = True
            listen_thread.start()
            self.threads.append(listen_thread)
        except Exception as e:
            self._log(f"启动监听失败: {str(e)}")
            self.stop_listen()

    def _accept_forwarder(self):
        """接收转发端连接"""
        while self.is_running:
            try:
                client_socket, client_addr = self.server_socket.accept()
                handle_thread = threading.Thread(target=self._handle_client, 
                                                args=(client_socket, client_addr))
                handle_thread.daemon = True
                handle_thread.start()
                self.threads.append(handle_thread)
            except Exception as e:
                if self.is_running:
                    self._log(f"接收连接异常: {str(e)}")

    def stop_listen(self):
        """停止监听"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        # 关闭socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 等待线程结束
        for t in self.threads:
            if t.is_alive():
                t.join(timeout=1)
        self.threads.clear()
        
        self._log("监听端已停止")

    def on_closing(self):
        """窗口关闭事件"""
        if self.is_running:
            self.stop_listen()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PortListener(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()