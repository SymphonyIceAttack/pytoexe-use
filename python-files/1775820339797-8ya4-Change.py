import os
import requests
import ctypes

IMAGE_URL = "https://www.cnpc.com.cn/cnpc/xhtml/cnpc2016/images/index2016/qywhImagec.jpg"

SAVE_FOLDER = r"D:\WallPaper"
IMAGE_PATH = os.path.join(SAVE_FOLDER, "wallpaper.jpg")

os.makedirs(SAVE_FOLDER, exist_ok=True)

try:
    resp = requests.get(IMAGE_URL, timeout=15)
    resp.raise_for_status()

    with open(IMAGE_PATH, "wb") as f:
        f.write(resp.content)

    SPI_SETDESKWALLPAPER = 0x0014
    ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        IMAGE_PATH,
        0x01 | 0x02
    )

except Exception as e:
    print(f"出错了: {e}")