import os
import time
import subprocess
import pyautogui


def launch_and_click():
    # 定义米哈游启动器的路径
    launcher_path = r"D:\Program Files\miHoYo Launcher\launcher.exe"

    # 1. 检查文件是否存在，避免路径错误
    if not os.path.exists(launcher_path):
        print(f"错误：找不到文件 {launcher_path}")
        return

    # 2. 启动米哈游启动器
    print("正在启动米哈游启动器...")
    try:
        # 使用subprocess启动程序，避免阻塞后续操作
        subprocess.Popen(launcher_path)
    except Exception as e:
        print(f"启动程序失败：{e}")
        return

    # 3. 等待3秒，确保程序加载完成
    print("等待3秒，确保程序加载...")
    time.sleep(3)

    # 4. 移动鼠标到指定坐标（1399,767）
    print(f"将鼠标移动到坐标 (1399, 767)...")
    pyautogui.moveTo(1399, 767, duration=0.2)  # duration=0.2表示移动过程耗时0.2秒，更贴近真人操作

    # 5. 执行鼠标左键单击
    print("执行鼠标左键单击...")
    pyautogui.click()

    print("所有操作完成！")


if __name__ == "__main__":
    # 防止pyautogui的故障保护（鼠标移到屏幕角落会触发），可根据需要关闭
    pyautogui.FAILSAFE = False
    launch_and_click()