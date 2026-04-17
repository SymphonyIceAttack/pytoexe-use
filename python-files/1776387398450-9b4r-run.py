import pyautogui
import time
from pynput import keyboard

# 全局控制开关
running = True

def on_key_press(key):
    global running
    try:
        # 按 F12 停止程序
        if key == keyboard.Key.f12:
            running = False
            print("\n✅ F12 按下，程序准备停止...")
    except AttributeError:
        pass

def main():
    print("===== 自动程序已启动 =====")
    print("功能：循环 点击 → Ctrl+W")
    print("停止方式：按 F12 键\n")

    # 启动键盘监听
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()

    try:
        while running:
            # 鼠标点击
            pyautogui.click()
            time.sleep(0.5)
            
            # 关闭当前窗口
            pyautogui.hotkey('ctrl', 'w')
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n🛑 Ctrl+C 停止")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
    finally:
        listener.stop()
        print("✅ 程序已停止")

if __name__ == "__main__":
    main()