import socket
import sys
import time
import ctypes
from ctypes import Structure, c_int, windll, pointer

# ========== 获取鼠标位置（无需pynput） ==========
class POINT(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]

def get_mouse_pos():
    pt = POINT()
    windll.user32.GetCursorPos(pointer(pt))
    return pt.x, pt.y

# ========== 主程序 ==========
if len(sys.argv) < 2:
    print("用法: mouse_sync.exe 手机IP [端口]")
    print("示例: mouse_sync.exe 192.168.3.76")
    sys.exit(1)

PHONE_IP = sys.argv[1]
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 6533

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(f"鼠标已同步到 {PHONE_IP}:{PORT}")
print("移动鼠标即可控制手机光标，按 Ctrl+C 停止")

try:
    while True:
        x, y = get_mouse_pos()
        msg = f"{x},{y},1,0,0"
        sock.sendto(msg.encode(), (PHONE_IP, PORT))
        time.sleep(0.016)  # 约60帧/秒
except KeyboardInterrupt:
    sock.close()
    print("\n已停止")