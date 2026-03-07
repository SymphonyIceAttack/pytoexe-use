import socket
import time

class KatanaNetzwerk:
    def __init__(self):
        self.target_ip = None
        self.target_port = None

    def ping(self, target_ip, target_port):
        if target_ip is None or target_port is None:
            return False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            sock.settimeout(1)
            sock.sendto(b'\x00\x01', (target_ip, int(target_port)))
            response = sock.recvfrom(1000)
            if response:
                return True
        except Exception as e:
            print(f"Error pinging {target_ip}:{target_port}: {str(e)}")
            return False

    def run(self):
        while True:
            self.target_ip = input("Enter the target IP: ")
            self.target_port = input("Enter the target port: ")
            if self.ping(self.target_ip, self.target_port):
                print(f"Server {self.target_ip}:{self.target_port} is online!")
            else:
                print(f"Server {self.target_ip}:{self.target_port} is offline!")

grabber = KatanaNetzwerk()
grabber.run()
