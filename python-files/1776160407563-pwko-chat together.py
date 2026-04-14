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
import select
import hashlib
from datetime import datetime
from queue import Queue, PriorityQueue
from collections import defaultdict

# ============ 配置信息 ============
BROADCAST_PORT = 55555
CHAT_PORT = 55556
BUFFER_SIZE = 8192
BROADCAST_INTERVAL = 1.5
PEER_TIMEOUT = 5
MAX_HISTORY_LINES = 1000000000
ENCRYPTION_KEY = b'P2P_Chat_2024_Key!'  # 加密密钥

# ============ ANSI颜色代码 ============
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
        return encrypted
    
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

# ============ UI美化类 ============
class UIManager:
    @staticmethod
    def clear_screen():
        """清屏"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def print_banner():
        """打印程序标题"""
        banner = f"""
{Colors.LIGHT_CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
                    P2P 加密聊天室
              (作者邮箱:meforwork123@outlook.com)                      
                  
                  局域网自动发现 | 端到端加密                
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
        print(banner)
    
    @staticmethod
    def print_message(sender, content, is_self=False, timestamp=None):
        """美化消息显示"""
        if timestamp is None:
            timestamp = datetime.now()
        
        time_str = timestamp.strftime('%H:%M:%S')
        
        if is_self:
            # 自己的消息（右对齐）
            sender_display = f"{Colors.LIGHT_GREEN}你{Colors.RESET}"
            print(f"\r{Colors.DIM}[{time_str}]{Colors.RESET} {sender_display}: {content}")
        else:
            # 他人消息（左对齐）
            sender_color = CryptoUtils.hash_string(sender)
            # 根据哈希值选择颜色
            color_map = [
                Colors.LIGHT_YELLOW, Colors.LIGHT_MAGENTA, 
                Colors.LIGHT_BLUE, Colors.LIGHT_CYAN
            ]
            color = color_map[int(sender_color, 16) % len(color_map)]
            
            # 美化消息框
            print(f"\r{Colors.DIM}[{time_str}]{Colors.RESET} {color}{Colors.BOLD}{sender}{Colors.RESET}: {content}")
    
    @staticmethod
    def print_system_message(text, msg_type="info"):
        """打印系统消息"""
        icon_map = {
            "info": f"{Colors.LIGHT_BLUE}ℹ{Colors.RESET}",
            "success": f"{Colors.LIGHT_GREEN}✓{Colors.RESET}",
            "warning": f"{Colors.LIGHT_YELLOW}⚠{Colors.RESET}",
            "error": f"{Colors.LIGHT_RED}✗{Colors.RESET}",
            "join": f"{Colors.LIGHT_GREEN}+{Colors.RESET}",
            "leave": f"{Colors.LIGHT_RED}-{Colors.RESET}"
        }
        icon = icon_map.get(msg_type, "•")
        print(f"\r{Colors.DIM}[系统]{Colors.RESET} {icon} {text}")
    
    @staticmethod
    def print_help():
        """打印帮助菜单"""
        help_text = f"""
{Colors.LIGHT_CYAN}{Colors.BOLD}📋 可用命令{Colors.RESET}
{Colors.DIM}────────────────────────────────────{Colors.RESET}
{Colors.LIGHT_GREEN}/help{Colors.RESET}     显示此帮助菜单(有什么问题记得联系作者哦)
{Colors.LIGHT_GREEN}/peers{Colors.RESET}    显示在线用户列表
{Colors.LIGHT_GREEN}/clear{Colors.RESET}    清空屏幕
{Colors.LIGHT_GREEN}/history{Colors.RESET}  查看历史消息
{Colors.LIGHT_GREEN}/stats{Colors.RESET}    显示聊天统计
{Colors.LIGHT_GREEN}/quit{Colors.RESET}     退出聊天室
{Colors.DIM}────────────────────────────────────{Colors.RESET}
"""
        print(help_text)
    
    @staticmethod
    def print_input_prompt():
        """打印输入提示符"""
        print(f"{Colors.LIGHT_CYAN}➤ {Colors.RESET}", end="", flush=True)

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

# ============ P2P聊天客户端增强版 ============
class EnhancedP2PChatClient:
    def __init__(self):
        self.ui = UIManager()
        self.crypto = CryptoUtils()
        
        self.username = self.get_username()
        self.peers = {}  # {地址: {'username': 用户名, 'last_seen': 时间戳, 'message_count': 消息数}}
        self.message_queue = MessageQueue()
        self.running = True
        self.message_count = 0
        self.start_time = time.time()
        
        # 获取本机IP
        self.local_ip = self.get_local_ip()
        
        # 聊天记录文件路径
        self.chat_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory")
        
        # 启动前清屏并显示欢迎界面
        self.ui.clear_screen()
        self.ui.print_banner()
        
        # 加载历史聊天记录
        self.load_chat_history()
        
        self.ui.print_system_message(f"欢迎, {Colors.BOLD}{self.username}{Colors.RESET}!", "success")
        self.ui.print_system_message(f"本机IP: {self.local_ip}", "info")
        self.ui.print_system_message("正在启动P2P加密聊天室...稍等一下，马上就好了", "info")
        
        # 启动各个服务线程
        self.start_services()
        
        # 显示帮助提示
        time.sleep(0.5)
        self.ui.print_system_message("输入 /help 查看命令", "info")
        print()
        self.ui.print_input_prompt()
    
    def get_username(self):
        """获取用户名（带美化）"""
        default_name = socket.gethostname()
        print(f"{Colors.LIGHT_CYAN}请输入你的昵称(作者提醒:为了安全，不要输入真实的名字){Colors.RESET} (默认: {Colors.LIGHT_GREEN}{default_name}{Colors.RESET}): ", end="")
        name = input().strip()
        if not name:
            name = default_name
        return name
    
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
            threading.Thread(target=self.broadcast_presence, daemon=True, name="Broadcast"),
            threading.Thread(target=self.listen_for_peers, daemon=True, name="PeerListener"),
            threading.Thread(target=self.listen_for_messages, daemon=True, name="MsgListener"),
            threading.Thread(target=self.cleanup_peers, daemon=True, name="Cleanup"),
            threading.Thread(target=self.process_messages, daemon=True, name="MsgProcessor"),
            threading.Thread(target=self.user_input_handler, daemon=True, name="InputHandler"),
            threading.Thread(target=self.stats_reporter, daemon=True, name="StatsReporter")
        ]
        
        for thread in threads:
            thread.start()
    
    def broadcast_presence(self):
        """广播自己的存在信息（加密）"""
        broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        broadcast_sock.settimeout(0.5)
        
        presence_data = {
            'type': 'presence',
            'username': self.username,
            'ip': self.local_ip,
            'port': CHAT_PORT,
            'timestamp': time.time(),
            'version': '2.0'
        }
        
        while self.running:
            try:
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
                try:
                    message_data = self.crypto.decrypt(encrypted_data)
                    message = json.loads(message_data)
                except:
                    continue
                
                if message['type'] == 'presence':
                    peer_ip = message['ip']
                    if peer_ip != self.local_ip:
                        peer_addr = f"{peer_ip}:{message['port']}"
                        is_new = peer_addr not in self.peers
                        
                        self.peers[peer_addr] = {
                            'username': message['username'],
                            'ip': peer_ip,
                            'port': message['port'],
                            'last_seen': time.time(),
                            'message_count': self.peers.get(peer_addr, {}).get('message_count', 0)
                        }
                        
                        if is_new:
                            print()
                            self.ui.print_system_message(
                                f"新用户加入: {Colors.LIGHT_GREEN}{message['username']}{Colors.RESET} ({peer_ip})", 
                                "join"
                            )
                            self.ui.print_input_prompt()
            except socket.timeout:
                continue
            except Exception as e:
                continue
        
        listen_sock.close()
    
    def listen_for_messages(self):
        """监听加密聊天消息"""
        chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        chat_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        port = CHAT_PORT
        while port < CHAT_PORT + 10:
            try:
                chat_sock.bind(('', port))
                break
            except:
                port += 1
        
        chat_sock.listen(10)
        chat_sock.settimeout(1)
        
        while self.running:
            try:
                client_sock, addr = chat_sock.accept()
                client_sock.settimeout(3)
                
                encrypted_data = client_sock.recv(BUFFER_SIZE)
                if encrypted_data:
                    try:
                        message_text = self.crypto.decrypt(encrypted_data)
                        message = json.loads(message_text)
                        
                        if message['type'] == 'chat':
                            # 高优先级处理
                            self.message_queue.put({
                                'sender': message['sender'],
                                'content': message['content'],
                                'timestamp': message.get('timestamp', time.time()),
                                'encrypted': True
                            }, priority=0)
                    except:
                        pass
                
                client_sock.close()
            except socket.timeout:
                continue
            except:
                continue
        
        chat_sock.close()
    
    def send_message_to_peer(self, peer_ip, peer_port, message_data):
        """发送加密消息到对等方"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((peer_ip, peer_port))
            
            message_json = json.dumps(message_data)
            encrypted = self.crypto.encrypt(message_json)
            sock.send(encrypted)
            sock.close()
            return True
        except:
            return False
    
    def broadcast_message(self, content):
        """广播加密消息"""
        message_data = {
            'type': 'chat',
            'sender': self.username,
            'content': content,
            'timestamp': time.time()
        }
        
        # 保存到本地聊天记录（加密存储）
        self.save_message(self.username, content)
        
        # 显示自己的消息
        self.ui.print_message(self.username, content, is_self=True)
        self.message_count += 1
        
        # 向所有在线对等方发送
        success_count = 0
        for peer_addr, peer_info in list(self.peers.items()):
            if self.send_message_to_peer(peer_info['ip'], peer_info['port'], message_data):
                success_count += 1
                peer_info['message_count'] = peer_info.get('message_count', 0) + 1
        
        if success_count < len(self.peers):
            print()
            self.ui.print_system_message(f"已向 {success_count}/{len(self.peers)} 个在线用户发送", "info")
    
    def process_messages(self):
        """处理接收到的消息队列"""
        while self.running:
            message = self.message_queue.get(timeout=0.5)
            if message:
                # 保存到聊天记录
                self.save_message(message['sender'], message['content'])
                
                # 显示消息
                self.ui.print_message(
                    message['sender'], 
                    message['content'], 
                    is_self=False,
                    timestamp=datetime.fromtimestamp(message['timestamp'])
                )
                self.ui.print_input_prompt()
    
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
        if os.path.exists(self.chat_file):
            try:
                with open(self.chat_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    if lines:
                        self.ui.print_system_message(f"加载 {len(lines)} 条历史记录", "info")
                        
                        # 只显示最近n条
                        recent_lines = lines[-1000000:]
                        print(f"\n{Colors.DIM}{'─' * 50}{Colors.RESET}")
                        print(f"{Colors.LIGHT_CYAN}📜 最近聊天记录{Colors.RESET}")
                        for line in recent_lines:
                            print(f"  {line.strip()}")
                        print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}\n")
            except:
                self.ui.print_system_message("无法读取聊天记录文件，不要伤心难过，请联系作者", "error")
    
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
                print()
                self.ui.print_system_message(f"用户离开: {username}", "leave")
                self.ui.print_input_prompt()
            
            time.sleep(1.5)
    
    def user_input_handler(self):
        """处理用户输入"""
        while self.running:
            try:
                user_input = input()
                
                if not user_input.strip():
                    self.ui.print_input_prompt()
                    continue
                
                if user_input == '/quit':
                    self.quit_chat()
                    break
                elif user_input == '/help':
                    self.ui.print_help()
                elif user_input == '/peers':
                    self.show_peers()
                elif user_input == '/clear':
                    self.ui.clear_screen()
                    self.ui.print_banner()
                elif user_input == '/history':
                    self.load_chat_history()
                elif user_input == '/stats':
                    self.show_stats()
                else:
                    # 发送聊天消息
                    self.broadcast_message(user_input)
                
                self.ui.print_input_prompt()
                
            except KeyboardInterrupt:
                self.quit_chat()
                break
            except Exception as e:
                continue
    
    def show_peers(self):
        """显示在线用户（美化版）"""
        print()
        self.ui.print_system_message(f"在线用户 ({len(self.peers)}/{len(self.peers)+1})", "info")
        print(f"{Colors.DIM}────────────────────────{Colors.RESET}")
        
        # 显示自己
        print(f"  {Colors.LIGHT_GREEN}●{Colors.RESET} {Colors.BOLD}{self.username}{Colors.RESET} {Colors.DIM}(你){Colors.RESET}")
        
        # 显示其他用户
        for peer_addr, peer_info in self.peers.items():
            msg_count = peer_info.get('message_count', 0)
            msg_indicator = f"{Colors.LIGHT_BLUE}({msg_count}条){Colors.RESET}" if msg_count > 0 else ""
            print(f"  {Colors.LIGHT_YELLOW}●{Colors.RESET} {Colors.BOLD}{peer_info['username']}{Colors.RESET} {Colors.DIM}{peer_info['ip']}{Colors.RESET} {msg_indicator}")
        
        print(f"{Colors.DIM}────────────────────────{Colors.RESET}\n")
    
    def show_stats(self):
        """显示聊天统计"""
        uptime = time.time() - self.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        print()
        self.ui.print_system_message("📊 聊天统计", "info")
        print(f"{Colors.DIM}────────────────────────{Colors.RESET}")
        print(f"  运行时间: {hours}小时{minutes}分钟")
        print(f"  发送消息: {self.message_count} 条")
        print(f"  在线人数: {len(self.peers)} 人")
        print(f"  加密模式: ✓ 已启用")
        print(f"{Colors.DIM}────────────────────────{Colors.RESET}\n")
    
    def stats_reporter(self):
        """定期报告统计信息"""
        while self.running:
            time.sleep(30)  # 每分钟更新一次
            # 这里可以添加定期统计功能
    
    def quit_chat(self):
        """退出聊天室"""
        print()
        self.ui.print_system_message("正在退出聊天室...再见", "warning")
        self.running = False
        
        # 显示再见信息
        print(f"\n{Colors.LIGHT_CYAN}{Colors.BOLD}感谢使用P2P加密聊天室！祝你拥有美好的一天！再见！{Colors.RESET}\n")
        time.sleep(0.5)
        os._exit(0)

# ============ 主程序 ============
def main():
    """主函数"""
    try:
        # 检查终端是否支持颜色
        if os.name == 'nt':
            # Windows启用ANSI支持
            os.system('color')
        
        client = EnhancedP2PChatClient()
        
        # 保持主线程运行
        while client.running:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n\n{Colors.LIGHT_YELLOW}程序被用户中断{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.LIGHT_RED}程序出错，作者正在紧急修复中，请联系meforwork123@outlook.com: {e}{Colors.RESET}")
    
    print(f"{Colors.RESET}")

if __name__ == "__main__":
    main()