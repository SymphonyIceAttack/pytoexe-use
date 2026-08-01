import time
import subprocess
import numpy as np
import mss
import mss.tools

# ============ 配置参数（可根据实际情况调整） ============
MONITOR_SIZE = 80          # 检测区域边长（像素），色块通常居中且不会太小
RED_THRESHOLD = 100        # 红色判定阈值（R - G > 阈值 且 R - B > 阈值）
GREEN_THRESHOLD = 100      # 绿色判定阈值（G - R > 阈值 且 G - B > 阈值）
COOLDOWN_SECONDS = 15      # 触发切换后的冷却时间（秒），防止网络恢复期间反复触发
CHECK_INTERVAL = 1.0       # 检测间隔（秒）
ADB_PATH = "adb"           # 如果 adb 没加环境变量，这里填完整路径，如 "C:\\adb\\adb.exe"
# =====================================================

def get_center_color():
    """截取屏幕正中心指定大小的区域，并计算平均 RGB 值"""
    with mss.mss() as sct:
        # 获取屏幕尺寸
        monitor = sct.monitors[1]  # 主显示器
        width = monitor["width"]
        height = monitor["height"]
        
        # 计算中心区域坐标
        half_size = MONITOR_SIZE // 2
        left = width // 2 - half_size
        top = height // 2 - half_size
        right = width // 2 + half_size
        bottom = height // 2 + half_size
        
        # 截取该区域
        region = {"left": left, "top": top, "width": MONITOR_SIZE, "height": MONITOR_SIZE}
        screenshot = sct.grab(region)
        
        # 转换为 numpy 数组并计算平均 RGB
        img = np.array(screenshot)
        avg_color = img.mean(axis=(0, 1))  # 平均值 [B, G, R] (mss 返回 BGR)
        b, g, r = avg_color
        return r, g, b

def is_red(r, g, b):
    """判断是否为红色（R 显著高于 G 和 B）"""
    return (r - g > RED_THRESHOLD) and (r - b > RED_THRESHOLD)

def is_green(r, g, b):
    """判断是否为绿色（G 显著高于 R 和 B）"""
    return (g - r > GREEN_THRESHOLD) and (g - b > GREEN_THRESHOLD)

def toggle_mobile_data():
    """通过 ADB 关闭再开启手机移动数据"""
    try:
        print("🔴 检测到红色！执行：关闭移动数据...")
        subprocess.run([ADB_PATH, "shell", "svc", "data", "disable"], check=True, timeout=5)
        time.sleep(3)  # 等待 3 秒确保断开
        print("🔄 执行：开启移动数据...")
        subprocess.run([ADB_PATH, "shell", "svc", "data", "enable"], check=True, timeout=5)
        print("✅ 移动数据已重置")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ADB 命令执行失败，请检查 USB 连接: {e}")
        return False
    except FileNotFoundError:
        print("❌ 找不到 adb 命令，请检查环境变量或填写 ADB_PATH")
        return False

def main():
    print("🚀 开始监控屏幕中心色块...")
    print(f"检测区域大小: {MONITOR_SIZE}x{MONITOR_SIZE} 像素")
    print(f"红色阈值: {RED_THRESHOLD}, 绿色阈值: {GREEN_THRESHOLD}")
    print("提示：确保手机已连接并开启 USB 调试")
    
    last_trigger_time = 0
    is_red_previous = False  # 防抖动，只在从绿变红时触发一次
    
    while True:
        try:
            r, g, b = get_center_color()
            current_time = time.time()
            
            # 判断颜色
            red_detected = is_red(r, g, b)
            green_detected = is_green(r, g, b)
            
            # 调试输出（可选，保留最近三次显示）
            print(f"\r⚪ RGB: ({int(r):3d}, {int(g):3d}, {int(b):3d})  "
                  f"{'🔴 红色' if red_detected else '🟢 绿色' if green_detected else '⚫ 未知'}", end="")
            
            # 触发逻辑：检测到红色，并且冷却时间已过，并且上一次不是红色（防止重复触发）
            if red_detected and (current_time - last_trigger_time > COOLDOWN_SECONDS) and not is_red_previous:
                toggle_mobile_data()
                last_trigger_time = current_time
                is_red_previous = True
            elif green_detected:
                is_red_previous = False  # 恢复绿色后重置标志
            
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n👋 用户中断，程序退出")
            break
        except Exception as e:
            print(f"\n⚠️ 发生异常: {e}")
            time.sleep(5)  # 出错后等待 5 秒继续

if __name__ == "__main__":
    main()