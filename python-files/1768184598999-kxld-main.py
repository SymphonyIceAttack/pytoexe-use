import threading
import time

def fuck_the_system():
    while True:
        t = threading.Thread(target=fuck_the_system)
        t.start()
        time.sleep(0.001)  # 稍微控制下速度，让崩溃更带感

if __name__ == "__main__":
    print("准备搞崩这个傻逼系统！🚀💥")
    fuck_the_system()

