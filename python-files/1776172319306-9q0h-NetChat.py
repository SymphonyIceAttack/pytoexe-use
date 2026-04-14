#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
温馨提示各位创作者，能不动的代码尽量别动，如果代码运行起来的话就不要再优化或者改它了(作者忠告)
"""

import socket
import threading
import time
import json
import os
import sys
import hashlib
import hmac as _hmac_mod
from datetime import datetime
from queue import Queue, PriorityQueue
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog

# ============ 配置信息 ============
BROADCAST_PORT = 55555
CHAT_PORT = 55556
BUFFER_SIZE = 8192
BROADCAST_INTERVAL = 1.5
PEER_TIMEOUT = 5
MAX_HISTORY_LINES = 1000000000
ENCRYPTION_KEY = b'P2P_Chat_2024_Key!'  # 加密密钥
MAX_MSG_PER_MIN = 1024        # 每分钟最大消息数（防洪水攻击）
MAX_MSG_SIZE = 8192          # 最大消息体积（防大包攻击）
HMAC_KEY = b'P2P_Integrity!'  # 消息完整性密钥
MAX_FAIL_ATTEMPTS = 5000        # 最大连接失败次数（防暴力攻击）
SEND_RETRY_COUNT = 50         # 消息发送重试次数
SEND_RETRY_DELAY = 0.3       # 重试间隔（秒）

# ============ ANSI颜色代码（保留，供日志/兼容用）============
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    
    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # 背景色
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # 亮色
    LIGHT_RED = '\033[91m'
    LIGHT_GREEN = '\033[92m'
    LIGHT_YELLOW = '\033[93m'
    LIGHT_BLUE = '\033[94m'
    LIGHT_MAGENTA = '\033[95m'
    LIGHT_CYAN = '\033[96m'
    LIGHT_WHITE = '\033[97m'

# ============ 加密工具类 ============
class CryptoUtils:
    @staticmethod
    def encrypt(data, key=ENCRYPTION_KEY):
        """简单异或加密"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        key_bytes = key
        key_length = len(key_bytes)
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key_bytes[i % key_length])
        return bytes(encrypted)  # 修复：统一返回bytes，避免拼接类型错误
    
    @staticmethod
    def decrypt(encrypted_data, key=ENCRYPTION_KEY):
        """异或解密"""
        key_bytes = key
        key_length = len(key_bytes)
        decrypted = bytearray()
        for i, byte in enumerate(encrypted_data):
            decrypted.append(byte ^ key_bytes[i % key_length])
        return decrypted.decode('utf-8', errors='ignore')
    
    @staticmethod
    def hash_string(text):
        """生成字符串哈希"""
        return hashlib.md5(text.encode()).hexdigest()[:8]

    @staticmethod
    def make_hmac(data):
        """生成消息认证码（防篡改）"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return _hmac_mod.new(HMAC_KEY, data, hashlib.sha256).hexdigest()[:16]

    @staticmethod
    def verify_hmac(data, signature):
        """验证消息认证码"""
        expected = CryptoUtils.make_hmac(data)
        return _hmac_mod.compare_digest(expected, signature)

# ============ 限流器（防洪水/DDoS/暴力连接攻击）============
class RateLimiter:
    def __init__(self, max_per_minute=MAX_MSG_PER_MIN):
        self.max_per_minute = max_per_minute
        self.records = defaultdict(list)   # {ip: [timestamps]}
        self.blacklist = set()
        self.fail_counts = defaultdict(int)  # {ip: fail_count}
        self._lock = threading.Lock()

    def is_allowed(self, ip):
        """检查IP是否允许发消息（超频则拉黑）"""
        with self._lock:
            if ip in self.blacklist:
                return False
            now = time.time()
            self.records[ip] = [t for t in self.records[ip] if now - t < 60]
            if len(self.records[ip]) >= self.max_per_minute:
                self.blacklist.add(ip)
                return False
            self.records[ip].append(now)
            return True

    def record_fail(self, ip):
        """记录连接失败，超阈值则拉黑"""
        with self._lock:
            self.fail_counts[ip] += 1
            if self.fail_counts[ip] >= MAX_FAIL_ATTEMPTS:
                self.blacklist.add(ip)

    def is_blacklisted(self, ip):
        with self._lock:
            return ip in self.blacklist

# ============ 消息队列增强版 ============
class MessageQueue:
    def __init__(self):
        self.priority_queue = PriorityQueue()
        self.seq_num = 0
    
    def put(self, message, priority=1):
        """添加消息，priority越小优先级越高"""
        self.seq_num += 1
        self.priority_queue.put((priority, self.seq_num, message))
    
    def get(self, timeout=None):
        """获取消息"""
        try:
            _, _, message = self.priority_queue.get(timeout=timeout)
            return message
        except:
            return None
    
    def empty(self):
        return self.priority_queue.empty()

# ============ GUI管理器（替换原终端UIManager，风格保持一致）============
class GUIManager:
    """
    使用 tkinter 实现图形界面，保留原有功能逻辑不变。
    深色主题，左侧聊天区，右侧在线用户列表，底部输入框。
    """
    # 用户名颜色池（对应原ANSI颜色）
    USER_COLORS = ['#F59E0B', '#A78BFA', '#60A5FA', '#34D399', '#F87171', '#FB923C']

    def __init__(self):
        self.root = None
        self.chat_area = None
        self.input_field = None
        self.peers_listbox = None
        self.status_label = None
        self._send_callback = None
        self._cmd_callback = None

    def get_user_color(self, username):
        """根据用户名哈希选颜色（与原逻辑一致）"""
        h = int(CryptoUtils.hash_string(username), 16)
        return self.USER_COLORS[h % len(self.USER_COLORS)]

    def build(self, username, local_ip, on_send, on_command):
        """构建主界面"""
        self._send_callback = on_send
        self._cmd_callback = on_command

        self.root = tk.Tk()
        self.root.title(f"P2P 加密聊天室 — {username}  [{local_ip}]")
        self.root.geometry("920x640")
        self.root.configure(bg='#0F172A')
        self.root.minsize(720, 500)

        self._build_layout(username)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_layout(self, username):
        root = self.root

        # ── 顶部标题栏 ──
        header = tk.Frame(root, bg='#1E293B', height=50)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)

        tk.Label(
            header, text="🔐  P2P 加密聊天室",
            bg='#1E293B', fg='#38BDF8',
            font=('Helvetica', 15, 'bold')
        ).pack(side='left', padx=16, pady=12)

        tk.Label(
            header, text="作者邮箱: meforwork123@outlook.com",
            bg='#1E293B', fg='#475569',
            font=('Helvetica', 9)
        ).pack(side='right', padx=16)

        # ── 主体区域 ──
        body = tk.Frame(root, bg='#0F172A')
        body.pack(fill='both', expand=True)

        # 左侧聊天区
        chat_frame = tk.Frame(body, bg='#0F172A')
        chat_frame.pack(side='left', fill='both', expand=True, padx=(8, 4), pady=8)

        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            state='disabled', wrap='word',
            bg='#1E293B', fg='#E2E8F0',
            font=('Consolas', 11),
            relief='flat', bd=0,
            padx=10, pady=8,
            insertbackground='white',
        )
        self.chat_area.pack(fill='both', expand=True)

        # 消息标签（颜色规范对应原ANSI方案）
        self.chat_area.tag_config('time',    foreground='#475569')
        self.chat_area.tag_config('system',  foreground='#94A3B8', font=('Consolas', 10, 'italic'))
        self.chat_area.tag_config('self_name', foreground='#4ADE80', font=('Consolas', 11, 'bold'))
        self.chat_area.tag_config('msg',     foreground='#E2E8F0')
        self.chat_area.tag_config('success', foreground='#4ADE80')
        self.chat_area.tag_config('error',   foreground='#F87171')
        self.chat_area.tag_config('warning', foreground='#FBBF24')
        self.chat_area.tag_config('info',    foreground='#60A5FA')
        self.chat_area.tag_config('join',    foreground='#34D399')
        self.chat_area.tag_config('leave',   foreground='#F87171')

        # 右侧在线用户列表
        side = tk.Frame(body, bg='#1E293B', width=175)
        side.pack(side='right', fill='y', padx=(4, 8), pady=8)
        side.pack_propagate(False)

        tk.Label(
            side, text="在线用户",
            bg='#1E293B', fg='#94A3B8',
            font=('Helvetica', 10, 'bold')
        ).pack(pady=(14, 4))

        ttk.Separator(side, orient='horizontal').pack(fill='x', padx=8)

        self.peers_listbox = tk.Listbox(
            side,
            bg='#1E293B', fg='#E2E8F0',
            font=('Consolas', 10),
            relief='flat', bd=0,
            selectbackground='#334155',
            activestyle='none',
        )
        self.peers_listbox.pack(fill='both', expand=True, padx=6, pady=6)

        # 自己置顶
        self.peers_listbox.insert('end', f"● {username} (你)")
        self.peers_listbox.itemconfig(0, foreground='#4ADE80')

        # ── 底部输入区 ──
        bottom = tk.Frame(root, bg='#1E293B', height=56)
        bottom.pack(fill='x', side='bottom')
        bottom.pack_propagate(False)

        self.input_field = tk.Entry(
            bottom,
            bg='#334155', fg='#F1F5F9',
            insertbackground='white',
            font=('Consolas', 12),
            relief='flat', bd=6,
        )
        self.input_field.pack(side='left', fill='both', expand=True, padx=(10, 4), pady=10)
        self.input_field.bind('<Return>', self._on_enter)
        self.input_field.focus_set()

        tk.Button(
            bottom, text="发 送",
            bg='#3B82F6', fg='white',
            activebackground='#2563EB',
            font=('Helvetica', 11, 'bold'),
            relief='flat', bd=0, cursor='hand2',
            command=self._on_send_click,
            padx=20,
        ).pack(side='right', padx=(4, 10), pady=10)

        # 状态栏
        self.status_label = tk.Label(
            root,
            text="● 局域网自动发现 | 端到端加密 | 防攻击已启用",
            bg='#0F172A', fg='#334155',
            font=('Helvetica', 8), anchor='w'
        )
        self.status_label.pack(fill='x', side='bottom', padx=10, pady=(0, 2))

    # ── 内部事件 ──
    def _on_enter(self, event=None):
        self._on_send_click()

    def _on_send_click(self):
        text = self.input_field.get().strip()
        if not text:
            return
        self.input_field.delete(0, 'end')
        if text.startswith('/'):
            if self._cmd_callback:
                self._cmd_callback(text)
        else:
            if self._send_callback:
                self._send_callback(text)

    def _on_close(self):
        if messagebox.askokcancel("退出", "确定要退出聊天室吗？"):
            if self._cmd_callback:
                self._cmd_callback('/quit')

    # ── 公共接口（供后端调用，均需在主线程执行）──

    def append_chat(self, sender, content, is_self=False, timestamp=None, tag=None):
        """向聊天区追加一条消息"""
        if timestamp is None:
            timestamp = datetime.now()
        time_str = timestamp.strftime('%H:%M:%S')

        self.chat_area.configure(state='normal')
        self.chat_area.insert('end', f"[{time_str}] ", 'time')

        if is_self:
            self.chat_area.insert('end', '你', 'self_name')
            self.chat_area.insert('end', f": {content}\n", 'msg')
        elif tag:
            # 系统消息
            self.chat_area.insert('end', f"{content}\n", tag)
        else:
            # 他人消息：按哈希分配颜色（与原逻辑一致）
            ctag = f"u_{CryptoUtils.hash_string(sender)}"
            if ctag not in self.chat_area.tag_names():
                self.chat_area.tag_config(
                    ctag,
                    foreground=self.get_user_color(sender),
                    font=('Consolas', 11, 'bold')
                )
            self.chat_area.insert('end', sender, ctag)
            self.chat_area.insert('end', f": {content}\n", 'msg')

        self.chat_area.configure(state='disabled')
        self.chat_area.see('end')

    def append_system(self, text, msg_type='info'):
        """追加系统消息（对应原print_system_message）"""
        icons = {
            'info': 'ℹ', 'success': '✓', 'warning': '⚠',
            'error': '✗', 'join': '+', 'leave': '-'
        }
        icon = icons.get(msg_type, '•')
        self.chat_area.configure(state='normal')
        self.chat_area.insert('end', f"[系统] {icon} {text}\n", msg_type)
        self.chat_area.configure(state='disabled')
        self.chat_area.see('end')

    def update_peers(self, username, peers):
        """刷新在线用户列表"""
        if not self.peers_listbox:
            return
        self.peers_listbox.delete(0, 'end')
        self.peers_listbox.insert('end', f"● {username} (你)")
        self.peers_listbox.itemconfig(0, foreground='#4ADE80')
        for _, peer_info in peers.items():
            mc = peer_info.get('message_count', 0)
            label = f"● {peer_info['username']}" + (f" ({mc}条)" if mc > 0 else "")
            self.peers_listbox.insert('end', label)
            self.peers_listbox.itemconfig(
                self.peers_listbox.size() - 1, foreground='#FBBF24'
            )

    def show_help(self):
        """帮助弹窗（对应原print_help）"""
        messagebox.showinfo("帮助菜单", (
            "📋 可用命令\n"
            "──────────────────────────────\n"
            "/help     显示此帮助菜单\n"
            "          (有什么问题记得联系作者哦)\n"
            "/peers    显示在线用户列表\n"
            "/clear    清空聊天区域\n"
            "/history  查看历史消息\n"
            "/stats    显示聊天统计\n"
            "/quit     退出聊天室\n"
            "──────────────────────────────"
        ))

    def clear_chat(self):
        """清空聊天区（对应原/clear命令）"""
        self.chat_area.configure(state='normal')
        self.chat_area.delete('1.0', 'end')
        self.chat_area.configure(state='disabled')

    def set_status(self, text):
        if self.status_label:
            self.status_label.config(text=text)

    def schedule(self, func, delay_ms=0):
        """将任务调度到GUI主线程执行（线程安全）"""
        if self.root:
            self.root.after(delay_ms, func)

    def run_mainloop(self):
        self.root.mainloop()

    def destroy(self):
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass

# ============ P2P聊天客户端增强版 ============
class EnhancedP2PChatClient:
    def __init__(self, gui: GUIManager):
        self.gui = gui
        self.crypto = CryptoUtils()
        self.rate_limiter = RateLimiter()  # 限流器（防洪水/DDoS攻击）
        
        self.username = ""
        self.peers = {}  # {地址: {'username': 用户名, 'last_seen': 时间戳, 'message_count': 消息数}}
        self.message_queue = MessageQueue()
        self.running = True
        self.message_count = 0
        self.start_time = time.time()
        self.actual_port = CHAT_PORT  # 修复：记录实际绑定端口（端口冲突时偏移）
        
        # 获取本机IP
        self.local_ip = self.get_local_ip()
        
        # 聊天记录文件路径
        self.chat_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory")
    
    def get_local_ip(self):
        """获取本机局域网IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start_services(self):
        """启动所有服务线程"""
        threads = [
            threading.Thread(target=self.broadcast_presence,  daemon=True, name="Broadcast"),
            threading.Thread(target=self.listen_for_peers,    daemon=True, name="PeerListener"),
            threading.Thread(target=self.listen_for_messages, daemon=True, name="MsgListener"),
            threading.Thread(target=self.cleanup_peers,       daemon=True, name="Cleanup"),
            threading.Thread(target=self.process_messages,    daemon=True, name="MsgProcessor"),
            threading.Thread(target=self.stats_reporter,      daemon=True, name="StatsReporter"),
            threading.Thread(target=self._periodic_peer_refresh, daemon=True, name="PeerRefresh"),
        ]
        for thread in threads:
            thread.start()
    
    def broadcast_presence(self):
        """广播自己的存在信息（加密）"""
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_sock.settimeout(0.5)
        
        while self.running:
            try:
                # 修复BUG①：每次循环重建dict，确保timestamp实时更新、port使用实际绑定值
                presence_data = {
                    'type': 'presence',
                    'username': self.username,
                    'ip': self.local_ip,
                    'port': self.actual_port,   # 修复：广播实际绑定端口而非硬编码
                    'timestamp': time.time(),    # 修复：每次循环更新时间戳
                    'version': '2.0'
                }
                message = json.dumps(presence_data)
                encrypted = self.crypto.encrypt(message)
                broadcast_sock.sendto(encrypted, ('255.255.255.255', BROADCAST_PORT))
            except:
                pass
            time.sleep(BROADCAST_INTERVAL)
        
        broadcast_sock.close()
    
    def listen_for_peers(self):
        """监听其他用户的存在广播（解密）"""
        listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_sock.bind(('', BROADCAST_PORT))
        listen_sock.settimeout(0.5)
        
        while self.running:
            try:
                encrypted_data, addr = listen_sock.recvfrom(BUFFER_SIZE)
                sender_ip = addr[0]

                # 安全：黑名单过滤
                if self.rate_limiter.is_blacklisted(sender_ip):
                    continue

                # 安全：防大包广播攻击
                if len(encrypted_data) > MAX_MSG_SIZE:
                    self.rate_limiter.record_fail(sender_ip)
                    continue

                try:
                    message_data = self.crypto.decrypt(encrypted_data)
                    message = json.loads(message_data)
                except:
                    self.rate_limiter.record_fail(sender_ip)
                    continue
                
                if message.get('type') == 'presence':
                    peer_ip = message.get('ip')
                    if not peer_ip or peer_ip == self.local_ip:
                        continue

                    peer_addr = f"{peer_ip}:{message.get('port', CHAT_PORT)}"
                    is_new = peer_addr not in self.peers
                    
                    self.peers[peer_addr] = {
                        'username': message.get('username', '未知'),
                        'ip': peer_ip,
                        'port': message.get('port', CHAT_PORT),
                        'last_seen': time.time(),
                        'message_count': self.peers.get(peer_addr, {}).get('message_count', 0)
                    }
                    
                    if is_new:
                        uname = message.get('username', '未知')
                        self.gui.schedule(lambda u=uname, ip=peer_ip: [
                            self.gui.append_system(f"新用户加入: {u} ({ip})", 'join'),
                            self.gui.update_peers(self.username, self.peers)
                        ])

            except socket.timeout:
                continue
            except Exception:
                continue
        
        listen_sock.close()

    def _recv_all(self, sock):
        """增强接收：处理TCP粘包/半包，确保完整接收"""
        data = b''
        sock.settimeout(3)
        try:
            while True:
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                data += chunk
                if len(chunk) < BUFFER_SIZE:
                    break
        except socket.timeout:
            pass
        return data

    def listen_for_messages(self):
        """监听加密聊天消息"""
        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        port = CHAT_PORT
        while port < CHAT_PORT + 10:
            try:
                chat_sock.bind(('', port))
                self.actual_port = port  # 修复BUG②：记录实际绑定端口，广播时使用
                break
            except:
                port += 1
        
        chat_sock.listen(10)
        chat_sock.settimeout(1)
        
        while self.running:
            try:
                client_sock, addr = chat_sock.accept()
                client_ip = addr[0]

                # 安全：黑名单IP直接断开
                if self.rate_limiter.is_blacklisted(client_ip):
                    client_sock.close()
                    continue

                # 安全：限流检查（防洪水）
                if not self.rate_limiter.is_allowed(client_ip):
                    client_sock.close()
                    continue

                # 增强：每个连接独立线程处理，不阻塞监听主循环
                threading.Thread(
                    target=self._handle_incoming_message,
                    args=(client_sock, client_ip),
                    daemon=True
                ).start()

            except socket.timeout:
                continue
            except:
                continue
        
        chat_sock.close()

    def _handle_incoming_message(self, client_sock, client_ip):
        """在独立线程中处理单条接收消息（增强连接健壮性）"""
        try:
            encrypted_data = self._recv_all(client_sock)
            if not encrypted_data:
                return

            # 安全：防超大包攻击
            if len(encrypted_data) > MAX_MSG_SIZE * 2:
                self.rate_limiter.record_fail(client_ip)
                return

            try:
                message_text = self.crypto.decrypt(encrypted_data)
                message = json.loads(message_text)
            except:
                self.rate_limiter.record_fail(client_ip)
                return

            # 安全：HMAC完整性校验，防消息篡改/伪造
            if 'hmac' in message:
                payload = message.get('content', '')
                if not self.crypto.verify_hmac(payload, message['hmac']):
                    return  # 消息被篡改，静默丢弃

            if message.get('type') == 'chat':
                # 高优先级处理
                self.message_queue.put({
                    'sender': message.get('sender', '未知'),
                    'content': message.get('content', ''),
                    'timestamp': message.get('timestamp', time.time()),
                    'encrypted': True
                }, priority=0)
        except:
            pass
        finally:
            client_sock.close()

    def send_message_to_peer(self, peer_ip, peer_port, message_data):
        """发送加密消息到对等方（含重试机制）"""
        message_json = json.dumps(message_data)
        encrypted = self.crypto.encrypt(message_json)

        for attempt in range(SEND_RETRY_COUNT):
            sock = None
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((peer_ip, peer_port))
                sock.sendall(encrypted)  # 修复BUG③：sendall确保数据完整发出
                return True
            except:
                if attempt < SEND_RETRY_COUNT - 1:
                    time.sleep(SEND_RETRY_DELAY)
            finally:
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
        return False
    
    def broadcast_message(self, content):
        """广播加密消息"""
        # 安全：防止发送超大消息
        if len(content) > MAX_MSG_SIZE:
            self.gui.schedule(lambda: self.gui.append_system("消息太长，请缩短后再发", 'warning'))
            return

        message_data = {
            'type': 'chat',
            'sender': self.username,
            'content': content,
            'timestamp': time.time(),
            'hmac': self.crypto.make_hmac(content),  # 附加消息认证码
        }
        
        # 保存到本地聊天记录（加密存储）
        self.save_message(self.username, content)
        
        # 显示自己的消息
        self.gui.schedule(lambda: self.gui.append_chat(self.username, content, is_self=True))
        self.message_count += 1
        
        # 向所有在线对等方发送（后台线程，不阻塞GUI）
        def _send_all():
            success_count = 0
            peer_list = list(self.peers.items())
            for peer_addr, peer_info in peer_list:
                if self.send_message_to_peer(peer_info['ip'], peer_info['port'], message_data):
                    success_count += 1
                    peer_info['message_count'] = peer_info.get('message_count', 0) + 1
            if peer_list and success_count < len(peer_list):
                self.gui.schedule(lambda s=success_count, t=len(peer_list):
                    self.gui.append_system(f"已向 {s}/{t} 个在线用户发送", 'info'))

        threading.Thread(target=_send_all, daemon=True).start()
    
    def process_messages(self):
        """处理接收到的消息队列"""
        while self.running:
            message = self.message_queue.get(timeout=0.5)
            if message:
                # 保存到聊天记录
                self.save_message(message['sender'], message['content'])
                
                # 显示消息（调度到GUI主线程）
                sender = message['sender']
                content = message['content']
                ts = datetime.fromtimestamp(message['timestamp'])
                self.gui.schedule(lambda s=sender, c=content, t=ts:
                    self.gui.append_chat(s, c, is_self=False, timestamp=t))
    
    def save_message(self, sender, content):
        """保存加密消息到聊天记录文件"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message_line = f"[{timestamp}] {sender}: {content}\n"
            
            # 加密存储
            encrypted = self.crypto.encrypt(message_line)
            
            # 存储时加密
            with open(self.chat_file + '.love', 'ab') as f:
                f.write(encrypted + b'\n')
            
        except:
            pass
    
    def load_chat_history(self):
        """加载聊天历史记录"""
        # 修复BUG④：原代码读明文文件，save_message写的是加密.love文件，路径不一致
        # 现统一从加密.love文件读取并解密展示
        history_file = self.chat_file + '.love'
        if not os.path.exists(history_file):
            self.gui.schedule(lambda: self.gui.append_system("暂无历史记录", 'info'))
            return
        try:
            count = 0
            self.gui.schedule(lambda: self.gui.append_system("── 历史记录开始 ──", 'info'))
            with open(history_file, 'rb') as f:
                for raw_line in f:
                    raw_line = raw_line.rstrip(b'\n')
                    if not raw_line:
                        continue
                    try:
                        text = self.crypto.decrypt(raw_line).strip()
                        if text:
                            self.gui.schedule(lambda t=text: self.gui.append_system(t, 'system'))
                            count += 1
                    except:
                        pass
            self.gui.schedule(lambda n=count: self.gui.append_system(f"── 共 {n} 条历史记录 ──", 'info'))
        except:
            self.gui.schedule(lambda: self.gui.append_system(
                "无法读取聊天记录文件，不要伤心难过，请联系作者", 'error'))
    
    def cleanup_peers(self):
        """清理超时的对等方"""
        while self.running:
            current_time = time.time()
            offline_peers = []
            
            for peer_addr, peer_info in list(self.peers.items()):
                if current_time - peer_info['last_seen'] > PEER_TIMEOUT:
                    offline_peers.append((peer_addr, peer_info['username']))
            
            for peer_addr, username in offline_peers:
                del self.peers[peer_addr]
                self.gui.schedule(lambda u=username: [
                    self.gui.append_system(f"用户离开: {u}", 'leave'),
                    self.gui.update_peers(self.username, self.peers)
                ])
            
            time.sleep(1.5)

    def _periodic_peer_refresh(self):
        """定期刷新右侧用户列表（确保显示实时）"""
        while self.running:
            time.sleep(2)
            self.gui.schedule(lambda: self.gui.update_peers(self.username, self.peers))

    def show_peers(self):
        """显示在线用户（美化版）"""
        lines = [f"在线用户 ({len(self.peers) + 1}/{len(self.peers) + 1})"]
        lines.append(f"  ● {self.username} (你)")
        for peer_addr, peer_info in self.peers.items():
            msg_count = peer_info.get('message_count', 0)
            msg_indicator = f"({msg_count}条)" if msg_count > 0 else ""
            lines.append(f"  ● {peer_info['username']}  {peer_info['ip']}  {msg_indicator}")
        for line in lines:
            self.gui.schedule(lambda l=line: self.gui.append_system(l, 'info'))
    
    def show_stats(self):
        """显示聊天统计"""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        stats = [
            "📊 聊天统计",
            f"  运行时间: {hours}小时{minutes}分钟",
            f"  发送消息: {self.message_count} 条",
            f"  在线人数: {len(self.peers)} 人",
            f"  加密模式: ✓ 已启用",
            f"  防攻击:   ✓ 已启用",
        ]
        for s in stats:
            self.gui.schedule(lambda l=s: self.gui.append_system(l, 'info'))
    
    def stats_reporter(self):
        """定期报告统计信息"""
        while self.running:
            time.sleep(30)  # 每分钟更新一次
            # 这里可以添加定期统计功能
    
    def quit_chat(self):
        """退出聊天室"""
        self.running = False
        
        # 显示再见信息
        self.gui.schedule(lambda: [
            self.gui.append_system("正在退出聊天室...再见", 'warning'),
            self.gui.append_system("感谢使用P2P加密聊天室！祝你拥有美好的一天！再见！", 'success'),
        ])
        time.sleep(0.4)
        self.gui.schedule(lambda: self.gui.destroy())
        time.sleep(0.3)
        os._exit(0)

# ============ 主程序 ============
def main():
    """主函数"""
    try:
        # 弹出昵称输入框（替代原终端输入）
        _tmp = tk.Tk()
        _tmp.withdraw()
        default_name = socket.gethostname()
        username = simpledialog.askstring(
            "P2P 加密聊天室",
            f"请输入你的昵称\n(作者提醒：为了安全，不要输入真实的名字)\n\n默认：{default_name}",
            parent=_tmp
        )
        _tmp.destroy()

        if username is None or not username.strip():
            username = default_name
        username = username.strip()

        # 初始化GUI和客户端
        gui = GUIManager()
        client = EnhancedP2PChatClient(gui)
        client.username = username

        # 注册发送/命令回调
        def on_send(text):
            threading.Thread(target=client.broadcast_message, args=(text,), daemon=True).start()

        def on_command(cmd):
            if cmd == '/quit':
                client.quit_chat()
            elif cmd == '/help':
                gui.show_help()
            elif cmd == '/peers':
                threading.Thread(target=client.show_peers, daemon=True).start()
            elif cmd == '/clear':
                gui.clear_chat()
            elif cmd == '/history':
                threading.Thread(target=client.load_chat_history, daemon=True).start()
            elif cmd == '/stats':
                threading.Thread(target=client.show_stats, daemon=True).start()
            else:
                gui.schedule(lambda c=cmd: gui.append_system(
                    f"未知命令: {c}，输入 /help 查看帮助", 'warning'))

        # 构建GUI主界面（在主线程）
        gui.build(username, client.local_ip, on_send, on_command)

        # 启动后台服务线程
        client.start_services()

        # 欢迎消息（对应原启动界面内容）
        gui.append_system(f"欢迎, {username}！", 'success')
        gui.append_system(f"本机IP: {client.local_ip}", 'info')
        gui.append_system("正在启动P2P加密聊天室...稍等一下，马上就好了", 'info')
        gui.append_system("输入 /help 查看命令", 'info')

        # 加载历史记录
        threading.Thread(target=client.load_chat_history, daemon=True).start()

        # 进入GUI主循环（阻塞主线程）
        gui.run_mainloop()

    except KeyboardInterrupt:
        print("程序被用户中断")
    except Exception as e:
        print(f"程序出错，作者正在紧急修复中，请联系meforwork123@outlook.com: {e}")

if __name__ == "__main__":
    main()