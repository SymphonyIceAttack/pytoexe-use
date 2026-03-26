import cv2
import numpy as np
import time
import qrcode
from pyzbar import pyzbar
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 动态输入网址
LIVE_URL = input("请输入直播间的网址：")

options = webdriver.EdgeOptions()
options.add_argument("--start-maximized")

driver = webdriver.Edge(
    service=Service(EdgeChromiumDriverManager().install()),
    options=options
)

driver.get(LIVE_URL)

time.sleep(6)

last = None

# 用于存储二维码的初始大小、位置
qr_pos = (100, 100)  # 初始位置
qr_size = (200, 200)  # 初始二维码大小
dragging = False  # 判断是否正在拖动
resize_mode = False  # 判断是否正在调整大小

# 鼠标回调函数，用于拖动和调整大小
def mouse_callback(event, x, y, flags, param):
    global qr_pos, qr_size, dragging, resize_mode, last

    # 判断是否按下左键，开始拖动
    if event == cv2.EVENT_LBUTTONDOWN:
        if x >= qr_pos[0] and x <= qr_pos[0] + qr_size[0] and y >= qr_pos[1] and y <= qr_pos[1] + qr_size[1]:
            dragging = True
        elif x >= qr_pos[0] + qr_size[0] - 10 and x <= qr_pos[0] + qr_size[0] and y >= qr_pos[1] + qr_size[1] - 10 and y <= qr_pos[1] + qr_size[1]:
            resize_mode = True

    # 拖动二维码
    elif event == cv2.EVENT_MOUSEMOVE:
        if dragging:
            qr_pos = (x - qr_size[0] // 2, y - qr_size[1] // 2)
        elif resize_mode:
            qr_size = (x - qr_pos[0], y - qr_pos[1])

    # 鼠标左键松开时，停止拖动或调整大小
    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False
        resize_mode = False

cv2.namedWindow("二维码预览")
cv2.setMouseCallback("二维码预览", mouse_callback)

while True:

    png = driver.get_screenshot_as_png()

    frame = cv2.imdecode(np.frombuffer(png, np.uint8), 1)

    # 截取指定区域进行二维码扫描
    roi = frame[200:900, 400:1500]

    codes = pyzbar.decode(roi)

    for c in codes:
        data = c.data.decode()

        if data != last:
            print("识别二维码:", data)

            # 生成二维码并显示在窗口中
            qr_img = qrcode.make(data)

            # 将二维码调整到适合的大小
            qr_img = qr_img.resize(qr_size)  # 使用当前大小

            # 转换为OpenCV格式
            qr_img = np.array(qr_img)
            qr_img = cv2.cvtColor(qr_img, cv2.COLOR_RGB2BGR)

            # 显示二维码
            frame[qr_pos[1]:qr_pos[1] + qr_size[1], qr_pos[0]:qr_pos[0] + qr_size[0]] = qr_img

            last = data

    # 显示直播画面
    cv2.imshow("LIVE", frame)

    # 显示二维码预览
    cv2.imshow("二维码预览", frame)

    # 按ESC退出程序
    if cv2.waitKey(1) == 27:
        break