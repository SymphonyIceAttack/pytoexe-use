import time
import psutil
import subprocess

# ==================== 配置区 ====================
URL = "http://1.1.1.3"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
CHECK_INTERVAL = 0.5
# =================================================

def open_edge():
    subprocess.Popen([
        EDGE_PATH,
        URL
    ])

def edge_is_running():
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and "msedge" in p.info["name"].lower():
                return True
        except:
            continue
    return False

if __name__ == "__main__":
    open_edge()
    while True:
        if not edge_is_running():
            open_edge()
        time.sleep(CHECK_INTERVAL)