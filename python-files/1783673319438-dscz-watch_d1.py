import time, os, asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PIL import Image
from bleak import BleakClient

MAC = "10:22:33:D7:03:25"
CHAR = "AE01"
FOLDER = os.path.expanduser("~/Desktop/D1_Out")

def log(m): print(f"[{time.strftime('%H:%M:%S')}] {m}")

def img2data(path):
    img = Image.open(path).convert("L").resize((384, int(Image.open(path).height*384/Image.open(path).width)), Image.LANCZOS)
    img = img.point(lambda x: 0 if x < 128 else 255, "1")
    d, px = [], img.load()
    for y in range(img.height):
        b, c = 0, 0
        for x in range(384):
            if px[x,y]==0: b|=1<<(7-c)
            c+=1
            if c==8: d.append(b); b,c=0,0
        if c: d.append(b)
    return d

async def send(data):
    async with BleakClient(MAC) as c:
        if not c.is_connected: log("连接失败"); return
        log("已连接")
        await c.write_gatt_char(CHAR, b'\x1B\x40')
        h = len(data)//48
        await c.write_gatt_char(CHAR, bytes([0x1D,0x76,0x30,0x00,48,0x00,h&0xFF,(h>>8)&0xFF]))
        for i in range(0,len(data),20): await c.write_gatt_char(CHAR, bytes(data[i:i+20]))
        await c.write_gatt_char(CHAR, b'\x1B\x4A\x40')
        log("打印完成")

class H(FileSystemEventHandler):
    def on_created(self, e):
        if e.src_path.lower().endswith(('.png','.jpg','.jpeg','.bmp')):
            log(f"捕获: {os.path.basename(e.src_path)}")
            try: asyncio.run(send(img2data(e.src_path))); os.remove(e.src_path)
            except Exception as e: log(f"错误: {e}")

if __name__ == "__main__":
    log("D1 打印监听已启动")
    os.makedirs(FOLDER, exist_ok=True)
    log(f"监听目录: {FOLDER}")
    Observer().schedule(H(), FOLDER, False)
    Observer().start()
    while True: time.sleep(1)
