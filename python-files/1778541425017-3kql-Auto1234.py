from pynput import keyboard
from pynput.keyboard import Controller, Key
import time
import threading

kb = Controller()
running = False
# 按键间隔，数值越小越快，可自行修改
delay = 0.15

def loop_task():
    global running
    while running:
        for k in ['1','2','3','4']:
            if not running:
                break
            kb.press(k)
            kb.release(k)
            time.sleep(delay)

def on_press(key):
    global running
    # 按数字1开始循环
    try:
        if key.char == '1' and not running:
            running = True
            threading.Thread(target=loop_task, daemon=True).start()
    except:
        pass
    
    # 按 F12 关闭程序
    if key == Key.f12:
        return False

def on_release(key):
    global running
    # 松开数字1停止循环
    try:
        if key.char == '1':
            running = False
    except:
        pass

print("===== 按键循环工具 =====")
print("按住 数字1 开始循环 1234")
print("松开 数字1 停止")
print("按 F12 关闭程序")

with keyboard.Listener(on_press=on_press, on_release=on_release) as lsn:
    lsn.join()