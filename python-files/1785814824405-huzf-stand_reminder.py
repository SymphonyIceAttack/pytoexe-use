import time
import threading
from pynput.mouse import Listener
from plyer import notification

# ========== 可自定义参数 ==========
REMIND_INTERVAL = 30 * 60      # 提醒间隔（秒），30分钟
IDLE_THRESHOLD = 120           # 鼠标空闲多少秒视为“已站立”（2分钟）
CHECK_INTERVAL = 10            # 检查鼠标空闲状态的间隔（秒）
REMIND_REPEAT_INTERVAL = 60    # 提醒后若仍在工作，每隔多少秒再提醒（秒）
# ===================================

last_move_time = time.time()   # 鼠标最后一次移动的时间戳
timer = None                   # 全局定时器
is_waiting_for_idle = False    # 是否处于“等待鼠标空闲”状态

def on_move(x, y):
    """鼠标移动回调，更新最后移动时间"""
    global last_move_time
    last_move_time = time.time()

def start_listener():
    """在独立线程中启动鼠标监听"""
    with Listener(on_move=on_move) as listener:
        listener.join()

def send_notification(title, message):
    """发送系统通知"""
    try:
        notification.notify(
            title=title,
            message=message,
            timeout=10          # 通知显示10秒
        )
    except Exception as e:
        print(f"[通知错误] {e}")

def check_idle():
    """检查鼠标是否空闲超过阈值"""
    return (time.time() - last_move_time) > IDLE_THRESHOLD

def schedule_next():
    """安排下一次提醒（30分钟后）"""
    global timer, is_waiting_for_idle
    is_waiting_for_idle = False
    if timer:
        timer.cancel()
    timer = threading.Timer(REMIND_INTERVAL, remind)
    timer.start()
    print(f"⏰ 下次提醒在 {REMIND_INTERVAL//60} 分钟后")

def remind():
    """提醒主逻辑"""
    global is_waiting_for_idle

    # 1. 检查当前是否空闲（已站立）
    if check_idle():
        print("🟢 鼠标空闲，用户可能已站立，跳过本次提醒，重置计时器")
        schedule_next()
        return

    # 2. 发出提醒
    send_notification("🧘 健康提醒", "请站立活动 5 分钟，并喝杯水！")
    print("🔔 提醒已发出，等待鼠标空闲（代表用户站立）...")
    is_waiting_for_idle = True

    # 3. 进入“等待空闲”循环，直到鼠标停止移动
    while is_waiting_for_idle:
        if check_idle():
            print("✅ 鼠标空闲，用户已站立，任务完成，重置计时器")
            is_waiting_for_idle = False
            schedule_next()
            break

        # 如果一直没空闲，等待 REMIND_REPEAT_INTERVAL 秒再检查一次
        # 期间每 CHECK_INTERVAL 秒检查一次空闲，以便快速响应
        for _ in range(int(REMIND_REPEAT_INTERVAL / CHECK_INTERVAL)):
            if not is_waiting_for_idle:   # 可能被取消
                break
            time.sleep(CHECK_INTERVAL)
            if check_idle():
                is_waiting_for_idle = False
                schedule_next()
                break

        # 如果仍在工作，再次提醒（循环继续）
        if is_waiting_for_idle:
            send_notification("⏳ 健康提醒", "还在工作吗？请务必站立活动 5 分钟并喝水！")

if __name__ == "__main__":
    # 启动鼠标监听线程（daemon 随主线程退出）
    listener_thread = threading.Thread(target=start_listener, daemon=True)
    listener_thread.start()
    print("🟢 健康提醒程序已启动，每30分钟检查一次。")

    # 安排第一次提醒
    schedule_next()

    # 主线程保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        if timer:
            timer.cancel()
        print("👋 程序已退出")