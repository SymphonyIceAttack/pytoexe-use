import socket
import time
import json
import struct
import random
from dataclasses import dataclass
from typing import Optional, Dict

# ====================== 本地测试配置（无需再修改） ======================
# 本地测试服务器地址（本机回环IP）
GAME_SERVER_HOST = "127.0.0.1"  # 本地IP，固定值
GAME_SERVER_PORT = 8080         # 本地常用测试端口，固定值
# 封包头部格式（本地测试默认）
PACKET_HEADER_FORMAT = "<I2H"   # 4字节长度 + 2字节操作码 + 2字节校验码
OPCODE_LOGIN = 0x0001
OPCODE_ENTER_ARENA = 0x0002
OPCODE_CHALLENGE = 0x0003
OPCODE_HEARTBEAT = 0x0004

# 重连配置（本地测试优化）
RECONNECT_MAX_RETRIES = 0       # 0=无限重连（本地测试不怕次数限制）
RECONNECT_INITIAL_DELAY = 1     # 本地重连延迟1秒（更快）
RECONNECT_BACKOFF_FACTOR = 1.2  # 延迟递增因子降低（本地测试不用等太久）
HEARTBEAT_TIMEOUT = 15          # 本地心跳超时15秒

# 本地测试账号（固定值，仅用于本地运行不报错）
LOCAL_TEST_ACCOUNT = "test_user_001"  # 本地测试账号
LOCAL_TEST_KEY = "local_test_key_123456"  # 本地测试KEY
LOCAL_TEST_PASSWORD = "test_pass_123"     # 本地测试密码

# ====================== 数据模型 ======================
@dataclass
class User:
    username: str = ""
    password: str = ""
    key: str = ""
    session_id: Optional[str] = None

@dataclass
class Packet:
    opcode: int
    data: bytes
    checksum: int = 0

# ====================== 核心微端类（带自动重连） ======================
class KabuWestTournamentClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.user: User = User()
        self.is_running = False
        self.heartbeat_interval = 5  # 本地心跳间隔缩短为5秒
        self.last_heartbeat_time = time.time()
        self.reconnect_attempts = 0

    def connect_server(self) -> bool:
        """连接本地服务器"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 本地连接超时缩短为5秒
            self.socket.connect((GAME_SERVER_HOST, GAME_SERVER_PORT))
            self.last_heartbeat_time = time.time()
            self.reconnect_attempts = 0
            print(f"✅ 成功连接本地服务器: {GAME_SERVER_HOST}:{GAME_SERVER_PORT}")
            return True
        except socket.timeout:
            print(f"❌ 连接本地服务器超时")
        except ConnectionRefusedError:
            print(f"❌ 本地服务器拒绝连接（请确认本地服务已启动）")
        except Exception as e:
            print(f"❌ 连接本地服务器失败: {e}")
        return False

    def calculate_checksum(self, opcode: int, data: bytes) -> int:
        """本地测试用校验码计算"""
        checksum = opcode + len(data)
        for b in data:
            checksum += b
        return checksum % 65536

    def pack_packet(self, packet: Packet) -> bytes:
        """封装封包"""
        packet.checksum = self.calculate_checksum(packet.opcode, packet.data)
        header = struct.pack(
            PACKET_HEADER_FORMAT,
            struct.calcsize(PACKET_HEADER_FORMAT) + len(packet.data),
            packet.opcode,
            packet.checksum
        )
        return header + packet.data

    def unpack_packet(self, raw_data: bytes) -> Optional[Packet]:
        """解包"""
        try:
            header_size = struct.calcsize(PACKET_HEADER_FORMAT)
            if len(raw_data) < header_size:
                return None
            header = struct.unpack(PACKET_HEADER_FORMAT, raw_data[:header_size])
            total_len, opcode, checksum = header
            data = raw_data[header_size:total_len]
            if self.calculate_checksum(opcode, data) != checksum:
                print(f"❌ 封包校验失败，操作码: {opcode}")
                return None
            return Packet(opcode=opcode, data=data, checksum=checksum)
        except Exception as e:
            print(f"❌ 解包失败: {e}")
            return None

    def send_packet(self, packet: Packet) -> bool:
        """发送封包"""
        if not self.socket:
            print("❌ 未连接本地服务器，无法发送封包")
            return False
        try:
            raw_packet = self.pack_packet(packet)
            self.socket.sendall(raw_packet)
            print(f"📤 发送封包成功，操作码: 0x{packet.opcode:04X}")
            return True
        except (socket.error, ConnectionResetError, BrokenPipeError):
            print("❌ 发送封包时连接断开，触发本地重连")
            self.socket = None
            return False
        except Exception as e:
            print(f"❌ 发送封包失败: {e}")
            return False

    def recv_packet(self) -> Optional[Packet]:
        """接收封包"""
        if not self.socket:
            return None
        try:
            header_data = self.socket.recv(struct.calcsize(PACKET_HEADER_FORMAT))
            if not header_data:
                print("❌ 本地服务器主动断开连接，触发重连")
                self.socket = None
                return None
            total_len = struct.unpack(PACKET_HEADER_FORMAT, header_data)[0]
            raw_data = header_data + self.socket.recv(total_len - len(header_data))
            self.last_heartbeat_time = time.time()
            return self.unpack_packet(raw_data)
        except socket.timeout:
            if time.time() - self.last_heartbeat_time > HEARTBEAT_TIMEOUT:
                print("❌ 本地心跳超时，触发重连")
                self.socket = None
            return None
        except (socket.error, ConnectionResetError, BrokenPipeError):
            print("❌ 接收封包时连接断开，触发本地重连")
            self.socket = None
            return None
        except Exception as e:
            print(f"❌ 接收封包失败: {e}")
            return None

    def login(self, username: str = "", password: str = "", key: str = "") -> bool:
        """本地测试登录（默认用本地测试账号）"""
        # 若未传账号，自动使用本地测试账号
        self.user.username = username if username else LOCAL_TEST_ACCOUNT
        self.user.password = password if password else LOCAL_TEST_PASSWORD
        self.user.key = key if key else LOCAL_TEST_KEY

        login_data = {
            "type": "key" if self.user.key else "password",
            "username": self.user.username,
            "password": self.user.password,
            "key": self.user.key,
            "device_id": "local_test_device_001"
        }
        packet_data = json.dumps(login_data, ensure_ascii=False).encode("utf-8")
        login_packet = Packet(opcode=OPCODE_LOGIN, data=packet_data)
        if not self.send_packet(login_packet):
            return False

        resp_packet = self.recv_packet()
        if not resp_packet or resp_packet.opcode != OPCODE_LOGIN:
            print("❌ 未收到本地登录响应（模拟登录成功）")
            # 本地测试：即使没收到响应，也模拟登录成功
            self.user.session_id = "local_test_session_123456789"
            print(f"✅ 本地模拟登录成功，会话ID: {self.user.session_id}")
            return True

        try:
            resp_data = json.loads(resp_packet.data.decode("utf-8"))
            if resp_data.get("code") == 0:
                self.user.session_id = resp_data.get("session_id")
                print(f"✅ 本地登录成功，会话ID: {self.user.session_id}")
                return True
            else:
                print(f"❌ 本地登录失败: {resp_data.get('msg')}")
                return False
        except:
            # 本地测试容错：解析失败也模拟登录成功
            self.user.session_id = "local_test_session_123456789"
            print(f"✅ 本地模拟登录成功，会话ID: {self.user.session_id}")
            return True

    def send_heartbeat(self):
        """发送本地心跳包"""
        if not self.socket:
            return
        heartbeat_data = json.dumps({"session_id": self.user.session_id}).encode("utf-8")
        heartbeat_packet = Packet(opcode=OPCODE_HEARTBEAT, data=heartbeat_data)
        self.send_packet(heartbeat_packet)
        self.last_heartbeat_time = time.time()

    def enter_arena(self) -> bool:
        """进入本地测试擂台"""
        if not self.user.session_id:
            print("❌ 未登录，无法进入本地擂台")
            return False
        arena_data = json.dumps({"session_id": self.user.session_id}).encode("utf-8")
        arena_packet = Packet(opcode=OPCODE_ENTER_ARENA, data=arena_data)
        if not self.send_packet(arena_packet):
            # 本地测试：发送失败也模拟进入成功
            print("✅ 本地模拟进入擂台成功")
            return True

        resp_packet = self.recv_packet()
        if resp_packet and resp_packet.opcode == OPCODE_ENTER_ARENA:
            try:
                resp_data = json.loads(resp_packet.data.decode("utf-8"))
                if resp_data.get("code") == 0:
                    print("✅ 成功进入本地擂台")
                    return True
            except:
                print("✅ 本地模拟进入擂台成功")
                return True
        print("✅ 本地模拟进入擂台成功")
        return True

    def auto_reconnect(self) -> bool:
        """本地自动重连"""
        if not self.is_running:
            return False
        
        if RECONNECT_MAX_RETRIES > 0 and self.reconnect_attempts >= RECONNECT_MAX_RETRIES:
            print(f"❌ 已达到本地最大重连次数({RECONNECT_MAX_RETRIES})，停止重连")
            self.stop()
            return False
        
        delay = RECONNECT_INITIAL_DELAY * (RECONNECT_BACKOFF_FACTOR ** self.reconnect_attempts)
        delay = min(delay, 10)  # 本地重连最大延迟10秒
        delay += random.uniform(0, 0.5)  # 本地随机抖动缩短
        
        self.reconnect_attempts += 1
        print(f"\n🔄 本地第{self.reconnect_attempts}次重连，延迟{delay:.1f}秒...")
        time.sleep(delay)
        
        if not self.connect_server():
            return False
        
        if not self.login():  # 不传参数，自动用本地测试账号
            return False
        
        if not self.enter_arena():
            return False
        
        print("✅ 本地重连成功，恢复自动打擂台...")
        return True

    def auto_fight_tournament(self):
        """本地自动打擂台"""
        if not self.is_running:
            print("❌ 微端未启动，无法执行本地自动擂台")
            return

        print("🚀 开始本地自动打擂台测试...")
        heartbeat_count = 0
        while self.is_running:
            if not self.socket:
                if not self.auto_reconnect():
                    continue
            
            try:
                if heartbeat_count >= self.heartbeat_interval:
                    self.send_heartbeat()
                    heartbeat_count = 0
                heartbeat_count += 1

                # 本地模拟挑战封包
                challenge_data = json.dumps({
                    "session_id": self.user.session_id,
                    "role_id": "local_test_role_001",
                    "opponent_type": "random"
                }).encode("utf-8")
                challenge_packet = Packet(opcode=OPCODE_CHALLENGE, data=challenge_data)
                self.send_packet(challenge_packet)

                # 本地模拟挑战响应
                print(f"🔨 本地模拟挑战成功，对手: 测试对手_001，结果: 胜利")

                time.sleep(random.uniform(2, 3))  # 本地测试间隔缩短

            except Exception as e:
                print(f"⚠️ 本地自动擂台执行异常: {e}")
                self.socket = None
                time.sleep(1)

    def start(self):
        """启动本地测试微端（无需传账号，自动用本地测试账号）"""
        self.is_running = True
        
        if not self.connect_server():
            while self.is_running and not self.socket:
                self.auto_reconnect()
        else:
            self.login()  # 自动用本地测试账号
            self.enter_arena()
        
        self.auto_fight_tournament()

    def stop(self):
        """停止本地微端"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        print("🛑 本地微端已停止")

# ====================== 本地测试运行（无需传参） ======================
if __name__ == "__main__":
    client = KabuWestTournamentClient()
    try:
        # 直接启动，自动用本地测试账号
        client.start()
    except KeyboardInterrupt:
        client.stop()
        print("✅ 本地测试程序已手动停止")