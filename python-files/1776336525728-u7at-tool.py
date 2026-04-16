import tkinter as tk
import time
import threading
import ctypes
import keyboard

# 全局变量
running = False
record_mode = False
current_map = -1
record_clicks = []

# 5个地图
maps = [
    {"name": "地图一", "check": tk.BooleanVar(), "clicks": []},
    {"name": "地图二", "check": tk.BooleanVar(), "clicks": []},
    {"name": "地图三", "check": tk.BooleanVar(), "clicks": []},
    {"name": "地图四", "check": tk.BooleanVar(), "clicks": []},
    {"name": "地图五", "check": tk.BooleanVar(), "clicks": []},
]

# 模拟鼠标点击
def mouse_click(x, y):
    ctypes.windll.user32.SetCursorPos(x, y)
    ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)
    time.sleep(0.2)

# 开始录制
def start_record(idx):
    global record_mode, current_map, record_clicks
    record_mode = True
    current_map = idx
    record_clicks = []
    tip_label.config(text=f"请点击2次 → {maps[idx]['name']}")

# 监听鼠标点击
def check_click():
    global record_mode, record_clicks
    if not record_mode:
        return
    import sys
    if sys.platform == "win32":
        import win32api
        while True:
            if win32api.GetKeyState(0x01) < 0:
                x, y = win32api.GetCursorPos()
                record_clicks.append((x, y))
                tip_label.config(text=f"已录 {len(record_clicks)} 次")
                time.sleep(0.3)
                if len(record_clicks) >= 2:
                    maps[current_map]['clicks'] = record_clicks.copy()
                    record_mode = False
                    tip_label.config(text=f"✅ {maps[current_map]['name']} 录制完成")
                break

# 执行地图任务
def run_map(m):
    # 两次点击
    p1, p2 = m['clicks']
    mouse_click(p1[0], p1[1])
    mouse_click(p2[0], p2[1])
    time.sleep(1)

    # 进入地图按一次
    keyboard.press_and_release("ctrl+alt+x")
    time.sleep(1)

    # 挂机点击
    mouse_click(p1[0], p1[1])

# 循环
def task_loop():
    while running:
        for m in maps:
            if not running: break
            if not m['check'].get(): continue
            if len(m['clicks']) < 2: continue

            tip_label.config(text=f"执行：{m['name']}")
            run_map(m)

            # 等待时间
            try:
                wait = int(interval_entry.get())
            except:
                wait = 600

            # 最后3秒按一次退出
            for i in range(wait):
                if not running: break
                time.sleep(1)
                if i == wait - 3:
                    keyboard.press_and_release("ctrl+alt+x")
                    time.sleep(1)

            tip_label.config(text="切换地图")

# 启动
def start():
    global running
    running = True
    threading.Thread(target=task_loop, daemon=True).start()
    tip_label.config(text="✅ 已启动 F9=启动 F10=停止")

# 停止
def stop():
    global running
    running = False
    tip_label.config(text="⏹ 已停止")

# 界面
root = tk.Tk()
root.title("地图挂机工具")
root.geometry("470x350")

# 地图
for i, m in enumerate(maps):
    tk.Checkbutton(root, text=m["name"], variable=m["check"]).place(x=30, y=30 + i*35)
    tk.Button(root, text="录制", command=lambda idx=i: start_record(idx)).place(x=150, y=30 + i*35)

# 间隔
tk.Label(root, text="间隔秒数：").place(x=30, y=230)
interval_entry = tk.Entry(root, width=8)
interval_entry.place(x=120, y=230)
interval_entry.insert(0, "600")

# 提示
tip_label = tk.Label(root, text="F9 启动 / F10 停止", fg="green", font=("黑体", 11))
tip_label.place(x=30, y=270)

# 监听
threading.Thread(target=check_click, daemon=True).start()

# 热键
keyboard.add_hotkey("f9", start)
keyboard.add_hotkey("f10", stop)

root.mainloop()