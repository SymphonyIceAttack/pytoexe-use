import sys
import time
import random
import threading
import os
import json
from pathlib import Path

try:
    import cv2
    import numpy as np
    import mss
    import pydirectinput 
    import keyboard
    import tkinter as tk
    from tkinter import ttk
except ModuleNotFoundError as e:
    print(f"\n❌ 缺少库: {e.name}，请先运行: pip install pydirectinput mss opencv-python numpy keyboard")
    input("按回车退出...")
    sys.exit()

# ================= 配置核心（调校关键） =================
# 🎯 判定区域位置配置（可自由调整）
TOP_LEFT = [720, 210]      # [X坐标, Y坐标] 判定区域左上角
Y_COMPENSATION = 50        # Y轴偏移补偿值（正数向下移，负数向上移）
# 注意：最终Y坐标 = TOP_LEFT[1] + Y_COMPENSATION

REG_WIDTH = 550            # 判定区域宽度
REG_HEIGHT = 100            # 判定区域高度

# 🎹 新的按键映射
COLORS = {
    "d": "#C24B99",   # 左
    "f": "#00FFFF",   # 下
    "j": "#12FA05",   # 上
    "k": "#F9393F",   # 右
}
TOLERANCE = 2 

# 🎲 按下时机的随机抖动（单位：秒）
PRESS_DELAY_RANGE = (0.00, 0.00) 

# 🔧 轨道宽度扩大倍数（1=原始大小，3=扩大3倍）
LANE_EXPAND_MULTIPLIER = 3

# 📈 重叠箭头检测参数（防误触优化）
AREA_JUMP_THRESHOLD = 30      # 面积绝对增量阈值（像素数），检测新箭头重叠
AREA_JUMP_RATIO = 1.2         # 面积增长比例阈值（当前面积 / 上一帧面积）
COOLDOWN_FRAMES = 3           # 触发后冷却帧数，防止波动误触
# =======================================================

# ================= 配置文件管理 =================
def get_config_filename():
    """获取当前脚本文件名（不含扩展名）"""
    script_name = Path(__file__).stem
    return f"{script_name}_config.json"

def save_config():
    """保存当前配置到JSON文件"""
    config_data = {
        "TOP_LEFT": TOP_LEFT,
        "Y_COMPENSATION": Y_COMPENSATION,
        "REG_WIDTH": REG_WIDTH,
        "REG_HEIGHT": REG_HEIGHT,
        "LANE_EXPAND_MULTIPLIER": LANE_EXPAND_MULTIPLIER,
        "COLORS": COLORS,
        "TOLERANCE": TOLERANCE,
        "PRESS_DELAY_RANGE": PRESS_DELAY_RANGE,
        "AREA_JUMP_THRESHOLD": AREA_JUMP_THRESHOLD,
        "AREA_JUMP_RATIO": AREA_JUMP_RATIO,
        "COOLDOWN_FRAMES": COOLDOWN_FRAMES,
        "version": "1.0",
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    config_file = get_config_filename()
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        print(f"💾 配置已保存到: {config_file}")
        return True
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False

def load_config():
    """从JSON文件加载配置"""
    global TOP_LEFT, Y_COMPENSATION, REG_WIDTH, REG_HEIGHT
    global LANE_EXPAND_MULTIPLIER, COLORS, TOLERANCE, PRESS_DELAY_RANGE
    global AREA_JUMP_THRESHOLD, AREA_JUMP_RATIO, COOLDOWN_FRAMES
    
    config_file = get_config_filename()
    if not os.path.exists(config_file):
        print(f"📝 配置文件不存在，使用默认配置: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # 更新全局变量
        if "TOP_LEFT" in config_data:
            TOP_LEFT = config_data["TOP_LEFT"]
        if "Y_COMPENSATION" in config_data:
            Y_COMPENSATION = config_data["Y_COMPENSATION"]
        if "REG_WIDTH" in config_data:
            REG_WIDTH = config_data["REG_WIDTH"]
        if "REG_HEIGHT" in config_data:
            REG_HEIGHT = config_data["REG_HEIGHT"]
        if "LANE_EXPAND_MULTIPLIER" in config_data:
            LANE_EXPAND_MULTIPLIER = config_data["LANE_EXPAND_MULTIPLIER"]
        if "COLORS" in config_data:
            COLORS = config_data["COLORS"]
        if "TOLERANCE" in config_data:
            TOLERANCE = config_data["TOLERANCE"]
        if "PRESS_DELAY_RANGE" in config_data:
            PRESS_DELAY_RANGE = tuple(config_data["PRESS_DELAY_RANGE"])
        if "AREA_JUMP_THRESHOLD" in config_data:
            AREA_JUMP_THRESHOLD = config_data["AREA_JUMP_THRESHOLD"]
        if "AREA_JUMP_RATIO" in config_data:
            AREA_JUMP_RATIO = config_data["AREA_JUMP_RATIO"]
        if "COOLDOWN_FRAMES" in config_data:
            COOLDOWN_FRAMES = config_data["COOLDOWN_FRAMES"]
        
        print(f"📂 已加载配置: {config_file}")
        print(f"   保存时间: {config_data.get('saved_at', '未知')}")
        return True
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return False

def save_config_hotkey():
    if save_config():
        print("✅ 配置已保存成功！")
    else:
        print("❌ 配置保存失败！")

# =======================================================

# 尝试加载已保存的配置
load_config()

# 注释掉自动偏移，完全使用配置文件中的坐标
# TOP_LEFT[1] += Y_COMPENSATION

pydirectinput.PAUSE = 0
pydirectinput.FAILSAFE = False

print("⚡ 音游特化驱动版（100% 准确度：硬件级冲刷防粘连版）已启动！")
print(f"📁 当前脚本: {Path(__file__).name}")
print(f"💾 配置文件: {get_config_filename()}")
print(f"📍 判定区域左上角坐标: ({TOP_LEFT[0]}, {TOP_LEFT[1]})")
print(f"📍 Y轴补偿值: {Y_COMPENSATION}px (仅作记录，不自动生效)")
print(f"📐 判定区域大小: {REG_WIDTH}x{REG_HEIGHT}px")
print(f"📈 重叠检测参数: 绝对增量>{AREA_JUMP_THRESHOLD} 且 比例>{AREA_JUMP_RATIO}, 冷却{COOLDOWN_FRAMES}帧")
print("🎹 【按键映射】D = 左键 | F = 下键 | J = 上键 | K = 右键")
print("🎹 【快捷键提示】按下 F3 键可自由 [开启/暂停] 脚本工作状态")
print("🎹 【快捷键提示】按下 F4 键可 [显示/隐藏] 检测范围可视化窗口")
print("🎹 【快捷键提示】按下 F5 键可 [保存当前配置] 到配置文件")
print("👉 按 Ctrl+C 退出")

color_ranges = {}
for name, hex_c in COLORS.items():
    h = hex_c.lstrip("#")
    b = int(h[4:6], 16)
    g = int(h[2:4], 16)
    r = int(h[0:2], 16)
    color_ranges[name] = {
        "lower": np.array([max(b - TOLERANCE, 0), max(g - TOLERANCE, 0), max(r - TOLERANCE, 0)], dtype=np.uint8),
        "upper": np.array([min(b + TOLERANCE, 255), min(g + TOLERANCE, 255), min(r + TOLERANCE, 255)], dtype=np.uint8)
    }

# 轨道配置
original_lane_width = REG_WIDTH // 4
half_original = original_lane_width // 2
centers = {
    "d":  half_original,
    "f":  half_original + original_lane_width,
    "j":  half_original + original_lane_width * 2,
    "k":  half_original + original_lane_width * 3,
}
expanded_half = int(original_lane_width * (LANE_EXPAND_MULTIPLIER / 2))
lanes = {}
for name, center in centers.items():
    start = max(0, int(center - expanded_half))
    end = min(REG_WIDTH, int(center + expanded_half))
    lanes[name] = (start, end)

print(f"\n📐 原始轨道宽度: {original_lane_width:.1f}px")
print(f"📐 扩大后轨道宽度: {expanded_half * 2}px")
print(f"📐 扩大倍数: {LANE_EXPAND_MULTIPLIER:.1f}倍")
print("\n🎯 各轨道判定范围:")
for name, (start, end) in lanes.items():
    print(f"   {name}: {start:>3} ~ {end:>3} (宽度: {end - start:>3}px, 中心: {centers[name]:.1f})")

# 状态变量
last_frame_present = {name: False for name in COLORS.keys()}
last_area = {name: 0 for name in COLORS.keys()}
cooldown_counter = {name: 0 for name in COLORS.keys()}   # 冷却帧计数

# ================= 工作状态控制 =================
is_running = True

def toggle_bot():
    global is_running
    is_running = not is_running
    if is_running:
        print("\n▶️ 脚本已【开启】工作状态...")
    else:
        print("\n⏸️ 脚本已【暂停】工作状态，正在安全释放所有按键...")
        for name in COLORS.keys():
            pydirectinput.keyUp(name)
            last_frame_present[name] = False
            last_area[name] = 0
            cooldown_counter[name] = 0

# ================= 可视化拖拽窗口（完全保留） =================
show_overlay = False
overlay_window = None
overlay_canvas = None
drag_data = {"x": 0, "y": 0, "dragging": False}
overlay_running = False
overlay_lock = threading.Lock()

def create_overlay():
    global overlay_window, overlay_canvas, overlay_running, show_overlay
    with overlay_lock:
        if overlay_running:
            return
        overlay_running = True
    try:
        overlay_window = tk.Tk()
        overlay_window.title("检测范围可视化 - 拖动调整")
        overlay_window.attributes("-topmost", True)
        overlay_window.attributes("-alpha", 0.3)
        overlay_window.overrideredirect(True)
        overlay_window.geometry(f"{REG_WIDTH}x{REG_HEIGHT}+{TOP_LEFT[0]}+{TOP_LEFT[1]}")
        try:
            overlay_window.wm_attributes("-transparentcolor", "white")
        except:
            pass
        overlay_canvas = tk.Canvas(
            overlay_window, 
            width=REG_WIDTH, 
            height=REG_HEIGHT,
            bg="white",
            highlightthickness=2,
            highlightcolor="red"
        )
        overlay_canvas.pack(fill=tk.BOTH, expand=True)
        draw_detection_zones()
        overlay_canvas.bind("<ButtonPress-1>", start_drag)
        overlay_canvas.bind("<B1-Motion>", on_drag)
        overlay_canvas.bind("<ButtonRelease-1>", stop_drag)
        overlay_window.bind("<Escape>", lambda e: close_overlay())
        overlay_window.protocol("WM_DELETE_WINDOW", close_overlay)
        overlay_window.mainloop()
    except Exception as e:
        print(f"可视化窗口错误: {e}")
    finally:
        with overlay_lock:
            overlay_running = False
            overlay_window = None
            overlay_canvas = None

def draw_detection_zones():
    if overlay_canvas is None:
        return
    overlay_canvas.delete("all")
    for name, (start, end) in lanes.items():
        overlay_canvas.create_rectangle(
            start, 0, end, REG_HEIGHT,
            fill="#FF0000", outline="#FF4444", width=1,
            stipple="gray50", tags="zone"
        )
        overlay_canvas.create_text(
            (start + end) // 2, REG_HEIGHT // 2,
            text=name.upper(), fill="white",
            font=("Arial", 8, "bold"), tags="zone"
        )
    overlay_canvas.create_rectangle(0, 0, REG_WIDTH, REG_HEIGHT,
                                    outline="#FF0000", width=2, tags="border")
    overlay_canvas.create_text(
        5, 5, text=f"X:{TOP_LEFT[0]} Y:{TOP_LEFT[1]}",
        fill="white", font=("Arial", 8), anchor="nw", tags="info"
    )

def start_drag(event):
    drag_data["x"] = event.x_root - overlay_window.winfo_x()
    drag_data["y"] = event.y_root - overlay_window.winfo_y()
    drag_data["dragging"] = True
    overlay_canvas.config(cursor="fleur")

def on_drag(event):
    if not drag_data["dragging"] or overlay_window is None:
        return
    new_x = event.x_root - drag_data["x"]
    new_y = event.y_root - drag_data["y"]
    screen_width = overlay_window.winfo_screenwidth()
    screen_height = overlay_window.winfo_screenheight()
    new_x = max(0, min(new_x, screen_width - REG_WIDTH))
    new_y = max(0, min(new_y, screen_height - REG_HEIGHT))
    overlay_window.geometry(f"+{new_x}+{new_y}")
    TOP_LEFT[0] = new_x
    TOP_LEFT[1] = new_y
    draw_detection_zones()

def stop_drag(event):
    drag_data["dragging"] = False
    if overlay_canvas:
        overlay_canvas.config(cursor="")
    print(f"📍 检测范围已移动到: ({TOP_LEFT[0]}, {TOP_LEFT[1]})")
    save_config()

def toggle_overlay():
    global show_overlay, overlay_running
    show_overlay = not show_overlay
    if show_overlay:
        with overlay_lock:
            if overlay_running and overlay_window:
                try:
                    overlay_window.deiconify()
                    draw_detection_zones()
                    print("🟥 检测范围可视化已开启（拖动红色区域可调整位置）")
                except:
                    overlay_running = False
                    threading.Thread(target=create_overlay, daemon=True).start()
            else:
                threading.Thread(target=create_overlay, daemon=True).start()
                print("🟥 检测范围可视化已开启（拖动红色区域可调整位置）")
    else:
        close_overlay()
        print("⬛ 检测范围可视化已关闭")

def close_overlay():
    global overlay_running, show_overlay
    show_overlay = False
    with overlay_lock:
        if overlay_window:
            try:
                overlay_window.destroy()
            except:
                pass
            overlay_window = None
            overlay_canvas = None
            overlay_running = False

def setup_hotkeys():
    try:
        keyboard.add_hotkey('f3', toggle_bot, suppress=False)
        keyboard.add_hotkey('f4', toggle_overlay, suppress=False)
        keyboard.add_hotkey('f5', save_config_hotkey, suppress=False)
        print("✅ 快捷键注册成功 (F3: 暂停/继续, F4: 显示/隐藏可视化, F5: 保存配置)")
    except Exception as e:
        print(f"⚠️ 快捷键注册警告: {e}")

def keyboard_listener():
    try:
        keyboard.wait()
    except:
        pass

# 启动监听
listener_thread = threading.Thread(target=keyboard_listener, daemon=True)
listener_thread.start()
setup_hotkeys()

monitor = {"top": TOP_LEFT[1], "left": TOP_LEFT[0], "width": REG_WIDTH, "height": REG_HEIGHT}

def cleanup():
    close_overlay()
    for name in COLORS.keys():
        pydirectinput.keyUp(name)

print("\n" + "="*50)
print("✅ 脚本已完全启动，快捷键已就绪！")
print("="*50 + "\n")

# ================= 主循环（核心逻辑优化） =================
try:
    with mss.mss() as sct:
        frame_count = 0
        detection_count = {name: 0 for name in COLORS.keys()}
        
        while True:
            if not is_running:
                time.sleep(0.01)
                continue
            
            monitor["top"] = TOP_LEFT[1]
            monitor["left"] = TOP_LEFT[0]
            
            img = np.array(sct.grab(monitor))
            frame = img[:, :, :3]
            frame_count += 1
            
            if frame_count % 100 == 0:
                print(f"\r📊 检测统计: {detection_count}", end="")
                detection_count = {name: 0 for name in COLORS.keys()}
            
            for name in COLORS.keys():
                x_start, x_end = lanes[name]
                if x_start >= x_end:
                    continue
                    
                lane_roi = frame[:, x_start:x_end]
                mask = cv2.inRange(lane_roi, color_ranges[name]["lower"], color_ranges[name]["upper"])
                area = cv2.countNonZero(mask)
                is_present = area > 3

                # 冷却计数器递减（如果大于0）
                if cooldown_counter[name] > 0:
                    cooldown_counter[name] -= 1

                # 检测触发条件
                trigger = False
                if is_present:
                    # 情况1：新箭头进入（上一帧无颜色）
                    if last_area[name] == 0:
                        trigger = True
                    # 情况2：重叠箭头进入（面积显著增加且满足比例条件）
                    else:
                        area_increase = area - last_area[name]
                        # 必须同时满足绝对增量阈值 和 比例阈值
                        if area_increase > AREA_JUMP_THRESHOLD and area > last_area[name] * AREA_JUMP_RATIO:
                            trigger = True

                # 冷却检查：如果冷却未结束，禁止触发
                if trigger and cooldown_counter[name] > 0:
                    trigger = False  # 冷却期内不触发

                if is_present:
                    detection_count[name] += 1

                if trigger:
                    # 重置冷却计数器
                    cooldown_counter[name] = COOLDOWN_FRAMES
                    
                    # 执行按键按下
                    delay = random.uniform(PRESS_DELAY_RANGE[0], PRESS_DELAY_RANGE[1])
                    if delay > 0:
                        time.sleep(delay)
                    
                    pydirectinput.keyUp(name)
                    time.sleep(0.002)
                    pydirectinput.keyDown(name)
                
                # 更新历史状态
                last_area[name] = area
                last_frame_present[name] = is_present

except KeyboardInterrupt:
    print("\n\n👋 已安全退出")
except Exception as e:
    print(f"\n❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    input("按回车退出...") 
finally:
    cleanup()