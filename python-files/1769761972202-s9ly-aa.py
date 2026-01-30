import time
import random
import threading
from pynput import keyboard

# 全局变量控制自动按键的状态
is_running = False
auto_press_thread = None
keyboard_controller = keyboard.Controller()

def auto_press_2():
    """自动按2键的核心函数"""
    global is_running
    while is_running:
        try:
            # 模拟按下并释放2键
            keyboard_controller.press(keyboard.KeyCode(char='2'))
            keyboard_controller.release(keyboard.KeyCode(char='2'))
            
            # 生成100-200毫秒之间的随机间隔
            delay = random.uniform(0.1, 0.2)
            time.sleep(delay)
        except Exception as e:
            print(f"出错: {e}")
            break

def on_press(key):
    """键盘按下事件处理"""
    global is_running, auto_press_thread
    
    try:
        if key.char == '2':
            if not is_running:
                is_running = True
                print("✅ 开始自动按2键 (间隔100-200ms)")
                auto_press_thread = threading.Thread(target=auto_press_2)
                auto_press_thread.daemon = True
                auto_press_thread.start()
            else:
                is_running = False
                print("❌ 停止自动按2键")
                if auto_press_thread is not None:
                    auto_press_thread.join(timeout=1)
    
    except AttributeError:
        pass

def main():
    print("=====================================")
    print("      自动连按2键工具 v1.0")
    print("=====================================")
    print("🔧 操作说明：")
    print("   按下 2 键 → 开始自动连按")
    print("   再次按 2 键 → 停止自动连按")
    print("   按 Ctrl+C → 退出程序")
    print("=====================================\n")
    
    # 创建键盘监听器
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    # 保持程序运行
    try:
        while listener.is_alive():
            listener.join(1)
    except KeyboardInterrupt:
        print("\n👋 程序正在退出...")
        is_running = False
        listener.stop()

if __name__ == "__main__":
    main()