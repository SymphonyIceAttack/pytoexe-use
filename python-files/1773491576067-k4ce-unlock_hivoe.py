import ctypes
import time
import os

# 定义Windows API常量
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_DELETE = 0x2E
VK_ESCAPE = 0x1B
VK_LWIN = 0x5B
KEYEVENTF_KEYUP = 0x0002

# 检测希沃易起学窗口
def is_hivoe_running():
    """检测希沃易起学是否运行"""
    user32 = ctypes.windll.user32
    hWnd = user32.FindWindowW(None, "希沃易起学")
    return hWnd != 0

# 模拟键盘按键
def press_key(key):
    """模拟按下并释放一个按键"""
    user32 = ctypes.windll.user32
    user32.keybd_event(key, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key, 0, KEYEVENTF_KEYUP, 0)

# 模拟组合键
def press_key_combination(key1, key2):
    """模拟按下并释放两个组合键"""
    user32 = ctypes.windll.user32
    user32.keybd_event(key1, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key2, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key2, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    user32.keybd_event(key1, 0, KEYEVENTF_KEYUP, 0)

# 模拟三键组合
def press_key_combination_3(key1, key2, key3):
    """模拟按下并释放三个组合键"""
    user32 = ctypes.windll.user32
    user32.keybd_event(key1, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key2, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key3, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(key3, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    user32.keybd_event(key2, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.05)
    user32.keybd_event(key1, 0, KEYEVENTF_KEYUP, 0)

# 方法1：模拟Ctrl+Alt+Del
def unlock_method1():
    """使用方法1：模拟Ctrl+Alt+Del组合键"""
    print("使用方法1：模拟Ctrl+Alt+Del组合键")
    press_key_combination_3(VK_CONTROL, VK_MENU, VK_DELETE)
    print("已发送Ctrl+Alt+Del组合键")

# 方法2：模拟ESC键
def unlock_method2():
    """使用方法2：模拟ESC键"""
    print("使用方法2：模拟ESC键")
    press_key(VK_ESCAPE)
    print("已发送ESC键")

# 方法3：模拟Windows+L组合键
def unlock_method3():
    """使用方法3：模拟Windows+L组合键"""
    print("使用方法3：模拟Windows+L组合键")
    press_key_combination(VK_LWIN, ord('L'))
    print("已发送Windows+L组合键")

# 方法4：发送窗口消息
def unlock_method4():
    """使用方法4：发送窗口消息"""
    print("使用方法4：发送窗口消息")
    user32 = ctypes.windll.user32
    hWnd = user32.FindWindowW(None, "希沃易起学")
    if hWnd:
        WM_SYSCOMMAND = 0x0112
        SC_CLOSE = 0xF060
        user32.SendMessageW(hWnd, WM_SYSCOMMAND, SC_CLOSE, 0)
        print("已发送关闭窗口消息")
    else:
        print("未找到希沃易起学窗口")

# 主函数
def main():
    print("希沃易起学键盘锁解除工具 (Python版)")
    print("===============================")
    
    if not is_hivoe_running():
        print("未检测到希沃易起学运行")
        input("请先启动希沃易起学，按任意键退出...")
        return
    
    print("检测到希沃易起学运行中")
    print("\n选择解锁方法：")
    print("1. 模拟Ctrl+Alt+Del组合键")
    print("2. 模拟ESC键")
    print("3. 模拟Windows+L组合键")
    print("4. 发送窗口消息")
    
    choice = input("请输入选项（1-4）：")
    
    if choice == '1':
        unlock_method1()
    elif choice == '2':
        unlock_method2()
    elif choice == '3':
        unlock_method3()
    elif choice == '4':
        unlock_method4()
    else:
        print("无效选项")
    
    print("\n解锁操作已完成，请检查键盘是否已解锁")
    input("按任意键退出...")

if __name__ == "__main__":
    main()
