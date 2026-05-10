import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
import time
from collections import OrderedDict
from pynput import keyboard
import queue

# ================== 网络发送器（带频率限制 + 静默期） ==================
class AsyncSender:
    def __init__(self):
        self.sock = None
        self.send_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        # 频率限制相关
        self.max_rate = None
        self.min_interval = 0.0
        self.last_sent_time = 0.0
        self.rate_lock = threading.Lock()
        # 静默期相关（发送自定义消息后阻止后续发送）
        self.silent_until = 0.0          # 时间戳，在此时间之前不允许发送
        self.silent_lock = threading.Lock()
        self.discard_callback = None

    def set_rate_limit(self, enabled, rate_per_sec):
        with self.rate_lock:
            if enabled and rate_per_sec > 0:
                self.max_rate = rate_per_sec
                self.min_interval = 1.0 / rate_per_sec
            else:
                self.max_rate = None
                self.min_interval = 0.0

    def set_silent_period(self, duration_sec):
        """设置静默期，duration_sec秒内发送的任何消息都将被丢弃"""
        with self.silent_lock:
            self.silent_until = time.time() + duration_sec
        if self.discard_callback:
            self.discard_callback(f"[静默期] 接下来 {duration_sec} 秒内的消息将被丢弃")

    def is_silent(self):
        """检查当前是否处于静默期"""
        with self.silent_lock:
            return time.time() < self.silent_until

    def connect(self, ip, port):
        self.disconnect()
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.sock.setblocking(True)
            self.running = True
            self.worker_thread = threading.Thread(target=self._sender_worker, daemon=True)
            self.worker_thread.start()
            return True, "连接成功"
        except Exception as e:
            return False, f"连接失败: {e}"

    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=0.5)

    def send(self, data: str):
        """将数据放入发送队列（线程安全），如果处于静默期则丢弃"""
        if not (self.running and self.sock):
            return
        # 静默期检查
        if self.is_silent():
            if self.discard_callback:
                self.discard_callback(f"[静默期丢弃] {data}")
            return
        self.send_queue.put(data + "\n")

    def _sender_worker(self):
        while self.running and self.sock:
            try:
                data = self.send_queue.get(timeout=0.1)
                # 频率限制检查
                if self.max_rate is not None:
                    now = time.time()
                    with self.rate_lock:
                        elapsed = now - self.last_sent_time
                        if elapsed < self.min_interval:
                            if self.discard_callback:
                                self.discard_callback(f"[限频丢弃] {data.strip()}")
                            continue
                        self.last_sent_time = now
                try:
                    self.sock.sendall(data.encode('utf-8'))
                except Exception as e:
                    print(f"发送错误: {e}")
                    self.running = False
            except queue.Empty:
                continue

# ================== 键盘监听与逻辑核心 ==================
class KeyboardForwarder:
    def __init__(self, async_sender, status_callback, log_callback):
        self.sender = async_sender
        self.status_callback = status_callback
        self.log_callback = log_callback
        self.listener = None
        self.current_keys = OrderedDict()
        self.long_press_active = False
        self.long_press_thread = None
        self.long_press_stop_event = threading.Event()
        self.last_sent_normal_key = None
        self.idle_check_timer = None
        self.running = False

        self.sender.discard_callback = self._on_discard

    def _on_discard(self, msg):
        self.log_callback(msg)

    def start(self):
        if self.listener and self.listener.is_alive():
            return
        self.running = True
        self.listener = keyboard.Listener(on_press=self._on_press, on_release=self._on_release)
        self.listener.start()
        self._start_idle_check()
        self.status_callback("键盘监听已启动")

    def stop(self):
        self.running = False
        if self.listener:
            self.listener.stop()
        self._stop_long_press()
        if self.idle_check_timer:
            self.idle_check_timer.cancel()
        self.status_callback("已停止")

    # ------------------ 长按处理 ------------------
    def _start_long_press(self, key_value):
        self._stop_long_press()
        self.long_press_active = True
        self.long_press_stop_event.clear()

        def long_press_worker():
            while self.long_press_active and self.running and not self.long_press_stop_event.is_set():
                if self.current_keys:
                    latest_key = next(reversed(self.current_keys))
                    self.sender.send(latest_key)
                else:
                    break
                time.sleep(0.001)   # 高频轮询，实际发送速率由限频器控制
            self.long_press_active = False

        self.long_press_thread = threading.Thread(target=long_press_worker, daemon=True)
        self.long_press_thread.start()

    def _stop_long_press(self):
        self.long_press_active = False
        if self.long_press_stop_event:
            self.long_press_stop_event.set()
        if self.long_press_thread and self.long_press_thread.is_alive():
            self.long_press_thread.join(timeout=0.2)
        self.long_press_thread = None

    # ------------------ 空闲检测：持续发送空字符 ------------------
    def _start_idle_check(self):
        def check_idle():
            if not self.running:
                return
            # 空闲状态：没有按键按下
            if not self.current_keys:
                # 发送空字符串（持续发送，间隔0.3秒）
                self.sender.send("")
            # 继续下一次检测
            if self.running:
                self.idle_check_timer = threading.Timer(0.3, check_idle)
                self.idle_check_timer.start()

        if self.idle_check_timer:
            self.idle_check_timer.cancel()
        self.idle_check_timer = threading.Timer(0.3, check_idle)
        self.idle_check_timer.start()

    # ------------------ 键盘事件 ------------------
    def _on_press(self, key):
        if not self.running:
            return
        key_str = self._key_to_string(key)
        if key_str is None:
            return

        # 记录按键顺序
        if key_str in self.current_keys:
            self.current_keys.move_to_end(key_str)
        else:
            self.current_keys[key_str] = None

        # 普通按键发送（相同按键只发一次）
        if key_str != self.last_sent_normal_key:
            self.sender.send(key_str)
            self.last_sent_normal_key = key_str

        # 长按检测延迟
        if hasattr(self, '_long_press_timer'):
            self._long_press_timer.cancel()
        self._long_press_timer = threading.Timer(0.2, lambda: self._on_long_press_detected(key_str))
        self._long_press_timer.start()

    def _on_long_press_detected(self, key_str):
        if self.running and key_str in self.current_keys and not self.long_press_active:
            self._start_long_press(key_str)

    def _on_release(self, key):
        if not self.running:
            return
        key_str = self._key_to_string(key)
        if key_str is None:
            return

        if key_str in self.current_keys:
            del self.current_keys[key_str]

        if not self.current_keys:
            self._stop_long_press()
            self.last_sent_normal_key = None
            if hasattr(self, '_long_press_timer'):
                self._long_press_timer.cancel()

    @staticmethod
    def _key_to_string(key):
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char
            else:
                return str(key).replace('Key.', '')
        except:
            return None

# ================== GUI界面 ==================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("键盘输入转发器 - 频率限制 + 静默期")
        self.root.geometry("580500")
        self.root.resizable(True, True)

        self.sender = AsyncSender()
        self.forwarder = KeyboardForwarder(self.sender, self.update_status, self.log)

        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        # 连接设置区域
        frame_conn = tk.LabelFrame(self.root, text="目标服务器设置", padx=5, pady=5)
        frame_conn.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame_conn, text="IP地址:").grid(row=0, column=0, sticky=tk.W, padx=2)
        self.ip_entry = tk.Entry(frame_conn, width=12)
        self.ip_entry.grid(row=0, column=1, padx=2)
        self.ip_entry.insert(0, "127.0.0.1")

        tk.Label(frame_conn, text="端口:").grid(row=0, column=2, sticky=tk.W, padx=2)
        self.port_entry = tk.Entry(frame_conn, width=6)
        self.port_entry.grid(row=0, column=3, padx=2)
        self.port_entry.insert(0, "8888")

        self.connect_btn = tk.Button(frame_conn, text="连接", command=self.do_connect, bg="#4CAF50", fg="white")
        self.connect_btn.grid(row=0, column=4, padx=5)

        self.status_label = tk.Label(frame_conn, text="未连接", fg="red")
        self.status_label.grid(row=0, column=5, padx=5)

        # 频率限制区域
        frame_rate = tk.LabelFrame(self.root, text="频率限制设置", padx=5, pady=5)
        frame_rate.pack(fill=tk.X, padx=10, pady=5)

        self.rate_enabled_var = tk.BooleanVar(value=True)
        self.rate_enabled_cb = tk.Checkbutton(frame_rate, text="启用频率限制", variable=self.rate_enabled_var,
                                              command=self.on_rate_config_changed)
        self.rate_enabled_cb.grid(row=0, column=0, sticky=tk.W, padx=2)

        tk.Label(frame_rate, text="最大发送次数/秒:").grid(row=0, column=1, sticky=tk.E, padx=2)
        self.rate_spinbox = tk.Spinbox(frame_rate, from_=1, to=1000, width=8, state="normal")
        self.rate_spinbox.grid(row=0, column=2, padx=2)
        self.rate_spinbox.delete(0, tk.END)
        self.rate_spinbox.insert(0, "50")
        tk.Label(frame_rate, text="次/秒 (1-1000)").grid(row=0, column=3, sticky=tk.W, padx=2)

        self.apply_rate_btn = tk.Button(frame_rate, text="应用限制", command=self.apply_rate_limit, bg="#FF9800", fg="white")
        self.apply_rate_btn.grid(row=0, column=4, padx=5)

        # 自定义消息区域
        frame_custom = tk.LabelFrame(self.root, text="自定义消息发送", padx=5, pady=5)
        frame_custom.pack(fill=tk.X, padx=10, pady=5)

        self.custom_entry = tk.Entry(frame_custom, width=40)
        self.custom_entry.pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        self.send_custom_btn = tk.Button(frame_custom, text="发送自定义消息", command=self.send_custom, bg="#2196F3", fg="white")
        self.send_custom_btn.pack(side=tk.RIGHT, padx=2)

        # 监听控制
        frame_control = tk.Frame(self.root)
        frame_control.pack(fill=tk.X, padx=10, pady=5)
        self.start_btn = tk.Button(frame_control, text="启动键盘监听", command=self.start_forward, bg="#008CBA", fg="white", width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(frame_control, text="停止监听", command=self.stop_forward, bg="#f44336", fg="white", width=15, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 日志区域
        frame_log = tk.LabelFrame(self.root, text="发送日志", padx=5, pady=5)
        frame_log.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(frame_log, height=12, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 提示
        tk.Label(self.root, text="提示：长按高频发送，受频率限制；空闲时每0.3秒发送空字符；发送自定义消息后3秒内不发送任何数据。",
                 fg="gray", font=("Arial", 9)).pack(side=tk.BOTTOM, pady=2)

        self.apply_rate_limit()

    def on_rate_config_changed(self):
        if self.rate_enabled_var.get():
            self.rate_spinbox.config(state="normal")
        else:
            self.rate_spinbox.config(state="disabled")

    def apply_rate_limit(self):
        enabled = self.rate_enabled_var.get()
        try:
            rate = int(self.rate_spinbox.get())
            if rate <= 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "请输入有效的正整数（1-1000）")
            return
        self.sender.set_rate_limit(enabled, rate)
        self.log(f"频率限制已{'启用' if enabled else '禁用'}，最大 {rate} 次/秒")

    def update_status(self, msg):
        self.root.after(0, lambda: self.status_label.config(text=msg))

    def log(self, msg):
        def _log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.root.after(0, _log)

    def do_connect(self):
        ip = self.ip_entry.get().strip()
        port_str = self.port_entry.get().strip()
        if not ip or not port_str:
            messagebox.showerror("错误", "请填写IP和端口")
            return
        try:
            port = int(port_str)
        except:
            messagebox.showerror("错误", "端口必须是整数")
            return
        success, msg = self.sender.connect(ip, port)
        if success:
            self.update_status(f"已连接到 {ip}:{port}")
            self.connect_btn.config(bg="#45a049", text="已连接", state=tk.DISABLED)
        else:
            self.update_status(f"连接失败: {msg}")
            messagebox.showerror("连接错误", msg)

    def send_custom(self):
        custom_msg = self.custom_entry.get().strip()
        if not custom_msg:
            messagebox.showwarning("警告", "自定义消息不能为空")
            return
        if not self.sender.running:
            messagebox.showwarning("警告", "还未连接到服务器，请先点击「连接」")
            return
        # 发送自定义消息
        self.sender.send(custom_msg)
        self.log(f"自定义发送: {custom_msg}")
        # 发送完成后启动3秒静默期
        self.sender.set_silent_period(3.0)

    def start_forward(self):
        if not self.sender.running:
            messagebox.showwarning("警告", "请先连接到服务器")
            return
        if self.forwarder.running:
            return
        self.forwarder.start()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

    def stop_forward(self):
        if self.forwarder.running:
            self.forwarder.stop()
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("键盘监听已停止")

    def on_closing(self):
        self.stop_forward()
        self.sender.disconnect()
        self.root.destroy()

if __name__ == "__main__":
    try:
        import pynput
    except ImportError:
        print("请先安装 pynput 库: pip install pynput")
        exit(1)
    root = tk.Tk()
    app = App(root)
    root.mainloop()