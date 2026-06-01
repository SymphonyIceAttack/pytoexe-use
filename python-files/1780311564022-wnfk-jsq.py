import cv2
import numpy as np
import pyautogui
import time
import tkinter as tk
from threading import Thread
from tkinter import messagebox

# 配置
COUNTDOWN_SECONDS = 14
CHECK_INTERVAL = 0.1
TEXT_COLOR = "#00FFFD"

# 全局
selected_left_area = None
selected_right_area = None
left_count = 4
right_count = 4
countdown_running = False
countdown_left = 0
overlay_x = 0
overlay_y = 0

# 选择区域
def select_area(title):
    screen = pyautogui.screenshot()
    frame = np.array(screen)
    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    roi = cv2.selectROI(title, frame, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()
    if roi[2] <= 0 or roi[3] <= 0:
        return None
    return (int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3]))

# 识别菱形数量
def count_diamonds(area):
    if not area:
        return 0
    try:
        x, y, w, h = area
        img = pyautogui.screenshot(region=(x, y, w, h))
        img = np.array(img)
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        mask = cv2.inRange(hsv, np.array([90, 100, 100]), np.array([130, 255, 255]))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnt = sum(1 for c in contours if cv2.contourArea(c) > 40)
        return cnt
    except:
        return 0

# 倒计时
def start_countdown():
    global countdown_running, countdown_left
    countdown_running = True
    countdown_left = COUNTDOWN_SECONDS
    for i in range(COUNTDOWN_SECONDS, -1, -1):
        countdown_left = i
        time.sleep(1)
    countdown_running = False

# 悬浮窗
def overlay_window():
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "white")
    root.geometry(f"200x120+{overlay_x}+{overlay_y}")
    root.config(bg="white")

    label = tk.Label(root, text="", font=("Arial", 44, "bold"), bg="white")
    label.pack(expand=True)

    def update():
        if countdown_running and countdown_left > 0:
            label.config(text=f"{countdown_left}", fg=TEXT_COLOR)
        else:
            label.config(text="")
        root.after(50, update)

    update()
    root.mainloop()

# 检测
def detection():
    global left_count, right_count, countdown_running
    while not selected_left_area or not selected_right_area:
        time.sleep(0.2)

    left_count = count_diamonds(selected_left_area)
    right_count = count_diamonds(selected_right_area)

    while True:
        now_left = count_diamonds(selected_left_area)
        now_right = count_diamonds(selected_right_area)

        if (now_left < left_count or now_right < right_count) and not countdown_running:
            Thread(target=start_countdown, daemon=True).start()

        left_count = now_left
        right_count = now_right
        time.sleep(CHECK_INTERVAL)

# 启动
if __name__ == "__main__":
    messagebox.showinfo("替身计时器", "1. 请框选【左边替身区域】\n2. 再框选【右边替身区域】")
    selected_left_area = select_area("框选左边替身")
    if not selected_left_area:
        exit()

    selected_right_area = select_area("框选右边替身")
    if not selected_right_area:
        exit()

    overlay_x = selected_left_area[0] - 40
    overlay_y = selected_left_area[1] - 70

    Thread(target=overlay_window, daemon=True).start()
    Thread(target=detection, daemon=True).start()

    while True:
        time.sleep(1)