import win32gui
import win32api
import win32con
import time
from pynput import mouse

游戏窗口标题 = "洛克王国世界"
录制动作列表 = []
正在录制 = False
正在播放 = False
洛克窗口句柄 = 0

def 检测洛克窗口():
    global 洛克窗口句柄
    洛克窗口句柄 = win32gui.FindWindow(None, 游戏窗口标题)
    return 洛克窗口句柄 != 0

def 后台左键点击(x,y):
    global 洛克窗口句柄
    rect = win32gui.GetWindowRect(洛克窗口句柄)
    相对x = x - rect[0]
    相对y = y - rect[1]
    参数 = win32api.MAKELONG(相对x, 相对y)
    win32gui.SendMessage(洛克窗口句柄, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 参数)
    time.sleep(0.05)
    win32gui.SendMessage(洛克窗口句柄, win32con.WM_LBUTTONUP, 0, 参数)

def 监听鼠标点击(x, y, 按键, 是否按下):
    global 录制动作列表, 正在录制
    if not 正在录制:
        return
    if 按键 == mouse.Button.left and 是否按下:
        if 检测洛克窗口():
            print(f"已录制点击坐标: {x},{y}")
            录制动作列表.append((x,y))

def 监听键盘按键(key):
    global 正在录制, 正在播放, 录制动作列表
    try:
        if key == win32con.VK_F1:
            if not 检测洛克窗口():
                print("❌ 请先打开洛克王国世界！")
                return
            正在录制 = True
            录制动作列表 = []
            print("✅ F1开始录制，在洛克里点一遍要循环的操作")
        elif key == win32con.VK_F2:
            正在录制 = False
            if len(录制动作列表)==0:
                print("❌ 没录制到动作")
                return
            正在播放 = True
            print(f"✅ F2录制完成，开始循环，每轮结束等待8秒")
        elif key == win32con.VK_F3:
            正在播放 = not 正在播放
            print("✅ F3：", "继续" if 正在播放 else "暂停")
        elif key == win32con.VK_F4:
            print("\n✅ F4退出脚本")
            return False
    except:
        pass

鼠标监听 = mouse.Listener(on_click=监听鼠标点击)
鼠标监听.start()

print("===== 洛克王国世界 后台录制循环 =====")
print("F1 = 开始录制点击动作")
print("F2 = 停止录制 + 自动无限循环")
print("F3 = 暂停 / 继续")
print("F4 = 退出脚本")
print("⚠️ 只控制洛克，后台不抢鼠标，不影响其他软件")
print("========================================\n")

try:
    while True:
        if 正在播放 and len(录制动作列表)>0 and 检测洛克窗口():
            for 坐标 in 录制动作列表:
                if not 正在播放: break
                后台左键点击(坐标[0], 坐标[1])
                time.sleep(0.3)
            time.sleep(8)
        time.sleep(0.1)
except:
    print("脚本已停止")