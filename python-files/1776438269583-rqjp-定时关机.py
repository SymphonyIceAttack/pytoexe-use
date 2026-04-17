import time
import os
from datetime import datetime

os.system("title 定时自动关机工具")
os.system("mode con cols=50 lines=15")

print("===== 电脑定时关机工具 =====")
print("请输入关机时间 格式：时:分")
print("示例：23:50 、02:30\n")

target = input("请输入目标关机时间：").strip()

print(f"\n设置完成！{target} 自动关机")
print("请勿关闭窗口，最小化即可后台运行\n")

while True:
    now = datetime.now().strftime("%H:%M")
    if now == target:
        os.system("shutdown /s /t 0")
        break
    time.sleep(15)
