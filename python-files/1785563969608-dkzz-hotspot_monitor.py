import time
import subprocess
from PIL import ImageGrab
import numpy as np

# ===== 配置（你可以按需调整） =====
MONITOR_SIZE = 80         # 检测区域边长（像素）
RED_THRESHOLD = 100       # 红色判定阈值
GREEN_THRESHOLD = 100     # 绿色判定阈值
COOLDOWN_SECONDS = 15     # 触发后冷却时间（秒）
CHECK_INTERVAL = 1.0      # 检测间隔（秒）
ADB_PATH = "adb"          # 如果 adb 没加环境变量，改成完整路径如 "C:\\adb\\adb.exe"
# =================================

def get_center_color():
    """截取屏幕正中心区域平均RGB"""
    # 获取屏幕尺寸
    screen = ImageGrab.grab()
    width, height = screen.size
    half = MONITOR_SIZE // 2
    left = width // 2 - half
    top = height // 2 - half
    # 截取中心区域并转换为numpy数组
    region = (left, top, left + MONITOR_SIZE, top + MONITOR_SIZE)
    img = ImageGrab.grab(bbox=region)
    img_np = np.array(img)
    avg = img_np.mean(axis=(0, 1))  # 返回 (R, G, B) 顺序
    r, g, b = avg
    return r, g, b

def is_red(r, g, b):
    return (r - g > RED_THRESHOLD) and (r - b > RED_THRESHOLD)

def is_green(r, g, b):
    return (g - r > GREEN_THRESHOLD) and (g - b > GREEN_THRESHOLD)

def toggle_mobile_data():
    try:
        print("🔴 关闭移动数据...")
        subprocess.run([ADB_PATH, "shell", "svc", "data", "disable"], check=True, timeout=5)
        time.sleep(3)
        print("🔄 开启移动数据...")
        subprocess.run([ADB_PATH, "shell", "svc", "data", "enable"], check=True, timeout=5)
        print("✅ 重置完成")
    except Exception as e:
        print(f"❌ 执行失败: {e}")

def main():
    print("🚀 开始监控中心色块（简化版）")
    last_time = 0
    was_red = False
    while True:
        try:
            r, g, b = get_center_color()
            now = time.time()
            red = is_red(r, g, b)
            green = is_green(r, g, b)
            print(f"\r⚪ RGB: ({int(r):3d},{int(g):3d},{int(b):3d}) "
                  f"{'🔴红' if red else '🟢绿' if green else '⚫未知'}", end="")
            if red and (now - last_time > COOLDOWN_SECONDS) and not was_red:
                toggle_mobile_data()
                last_time = now
                was_red = True
            elif green:
                was_red = False
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            print("\n👋 退出")
            break
        except Exception as e:
            print(f"\n⚠️ 错误: {e}，5秒后继续")
            time.sleep(5)

if __name__ == "__main__":
    main()