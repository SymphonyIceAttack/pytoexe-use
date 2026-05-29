import tkinter as tk
from tkinter import ttk
import time
import requests
from datetime import datetime, timedelta
import threading

# ====================== 配置区 ======================
# 和风天气Key（免费申请：https://dev.qweather.com/）
WEATHER_KEY = ""
CITY_ID = "101120101"  # 济南
# 课程时间表 (开始时间, 结束时间, 时段名称)
SCHEDULE = [
    ("07:40", "08:20", "早读"),
    ("08:30", "09:10", "第一节"),
    ("09:40", "10:20", "第二节"),
    ("10:30", "11:10", "第三节"),
    ("11:20", "12:00", "第四节"),
    ("12:00", "12:30", "午饭"),
    ("12:30", "13:00", "午自习"),
    ("13:00", "13:50", "午休"),
    ("14:00", "14:40", "第五节"),
    ("15:00", "15:40", "第六节"),
    ("15:50", "16:30", "第七节"),
    ("16:40", "17:20", "第八节")
]
# 完整课程表 (0=周一, 1=周二, 2=周三, 3=周四, 4=周五)
COURSE_TABLE = {
    0: ["语文", "语文", "英语", "数学", "信息", "数学", "传统", "数学", "语文", "数学"],
    1: ["语文", "数学", "语文", "英语", "数学", "语文", "音乐", "数学", "综合", "语文"],
    2: ["语文", "语文", "科学", "体育", "英语", "英语", "数学", "科学", "数学", "语文"],
    3: ["数学", "数学", "语文", "美术", "语文", "数学", "体育", "传统", "英语", "英语"],
    4: ["英语", "英语", "数学", "语文", "语文", "语文", "综合", "体育", "数学", "语文"]
}
# 三状态常量
STATE_HIDE = 0      # 隐藏：完全消失
STATE_SLEEP = 1     # 休眠：不置顶、半透明、可被覆盖
STATE_SHOW = 2      # 显示：置顶、半透明、覆盖所有窗口
STATE_CALENDAR = 3  # 日历模式：点击展开
# 中文星期映射
WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
# 动画配置
ANIMATION_DURATION = 0.3  # 动画时长（秒）
SLIDE_DISTANCE = 10       # 滑入动画距离（像素）
ZOOM_FACTOR = 1.05        # 悬停放大倍数
# ====================================================

# 全局变量
island_running = False
island_window = None
time_label = None
weather_text = "加载中"
current_state = STATE_HIDE
reminder_triggered = set()  # 防止重复触发提醒
current_date = datetime.now().date()  # 每日自动重置标记
is_showing_reminder = False  # 是否正在显示提示信息
last_activity_time = None    # 最后活动时间，用于自动休眠
animation_id = None          # 用于取消Tkinter动画

def sync_network_time():
    """启动时自动校准网络时间（使用阿里云NTP时间）"""
    try:
        res = requests.get("http://api.m.taobao.com/rest/api3.do?api=mtop.common.getTimestamp", timeout=5)
        data = res.json()
        timestamp = int(data["data"]["t"]) / 1000
        network_time = datetime.fromtimestamp(timestamp)
        print(f"网络时间校准成功：{network_time.strftime('%Y-%m-%d %H:%M:%S')}")
        return network_time
    except:
        print("网络时间校准失败，使用本地时间")
        return datetime.now()

def get_weather():
    """获取实时天气"""
    global weather_text
    if not WEATHER_KEY:
        weather_text = "无天气Key"
        return
    try:
        url = f"https://devapi.qweather.com/v7/weather/now?location={CITY_ID}&key={WEATHER_KEY}"
        res = requests.get(url, timeout=4)
        data = res.json()
        temp = data["now"]["temp"]
        cond = data["now"]["text"]
        weather_text = f"{cond} {temp}℃"
    except:
        weather_text = "天气获取失败"

def set_island_state(new_state):
    """切换灵动岛三状态"""
    global current_state, island_window, last_activity_time
    if current_state == new_state:
        return
    current_state = new_state
    last_activity_time = time.time()  # 更新活动时间
    
    if new_state == STATE_HIDE:
        island_window.withdraw()  # 完全隐藏
    elif new_state == STATE_SLEEP:
        # 从其他状态切换到休眠，播放缩小动画
        animate_size(island_window.winfo_width(), island_window.winfo_height(), 
                     300, 30, ANIMATION_DURATION)
        island_window.attributes("-topmost", False)  # 取消置顶，可被覆盖
        island_window.attributes("-alpha", 0.75)
        island_window.deiconify()
    elif new_state == STATE_SHOW:
        # 从休眠状态切换到显示，播放滑入和放大动画
        if current_state == STATE_SLEEP:
            animate_slide_in()
        else:
            island_window.deiconify()
        island_window.attributes("-topmost", True)   # 置顶覆盖所有窗口
        island_window.attributes("-alpha", 0.92)
    elif new_state == STATE_CALENDAR:
        # 从显示状态切换到日历，播放拉伸动画
        animate_size(island_window.winfo_width(), island_window.winfo_height(), 
                     750, 750, ANIMATION_DURATION, show_calendar)
        island_window.attributes("-topmost", True)   # 置顶覆盖所有窗口
        island_window.attributes("-alpha", 0.92)

def animate_slide_in():
    """滑入动画：从屏幕顶端滑下"""
    start_y = -island_window.winfo_height()
    end_y = SLIDE_DISTANCE
    island_window.geometry(f"+{island_window.winfo_x()}+{start_y}")
    island_window.deiconify()
    
    start_time = time.time()
    def step():
        elapsed = time.time() - start_time
        progress = min(elapsed / ANIMATION_DURATION, 1.0)
        current_y = start_y + (end_y - start_y) * progress
        island_window.geometry(f"+{island_window.winfo_x()}+{current_y}")
        if progress < 1.0:
            global animation_id
            animation_id = island_window.after(16, step)  # ~60fps
    
    step()

def animate_size(start_width, start_height, end_width, end_height, duration, callback=None):
    """尺寸变化动画"""
    start_time = time.time()
    current_width, current_height = start_width, start_height
    
    def step():
        nonlocal current_width, current_height
        elapsed = time.time() - start_time
        progress = min(elapsed / duration, 1.0)
        # 缓动函数，使动画更流畅
        ease_progress = progress * progress * (3 - 2 * progress)
        current_width = start_width + (end_width - start_width) * ease_progress
        current_height = start_height + (end_height - start_height) * ease_progress
        island_window.geometry(f"{int(current_width)}x{int(current_height)}")
        if progress < 1.0:
            global animation_id
            animation_id = island_window.after(16, step)  # ~60fps
        else:
            if callback:
                callback()
    
    step()

def show_calendar():
    """显示日历界面"""
    global time_label
    # 清空原有内容
    for widget in island_window.winfo_children():
        widget.destroy()
    
    # 获取当前日期
    now = datetime.now()
    year, month = now.year, now.month
    today = now.day
    weekday = now.weekday()  # 0=周一, 6=周日
    
    # 创建主框架
    main_frame = ttk.Frame(island_window, style="Calendar.TFrame")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # 时间显示
    time_str = now.strftime("%H:%M:%S")
    date_str = now.strftime("%Y年%m月%d日 星期%w").replace("星期0", "星期日")
    time_label = ttk.Label(main_frame, text=time_str, font=("微软雅黑", 48, "bold"), foreground="white")
    time_label.pack(pady=(0, 10))
    date_label = ttk.Label(main_frame, text=date_str, font=("微软雅黑", 16), foreground="#bbbbbb")
    date_label.pack(pady=(0, 20))
    
    # 日历网格
    cal_frame = ttk.Frame(main_frame)
    cal_frame.pack(fill=tk.BOTH, expand=True)
    
    # 星期标题
    week_days = ["日", "一", "二", "三", "四", "五", "六"]
    for col, day in enumerate(week_days):
        lbl = ttk.Label(cal_frame, text=day, font=("微软雅黑", 12), foreground="#bbbbbb")
        lbl.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
    
    # 调整列权重
    for col in range(7):
        cal_frame.grid_columnconfigure(col, weight=1)
    
    # 获取当月第一天是星期几
    first_day = datetime(year, month, 1).weekday()  # 0=周一, 6=周日
    # 当月的天数
    if month == 2:
        days_in_month = 29 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 28
    else:
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1]
    
    # 填充日历
    row = 1
    col = first_day
    for day in range(1, days_in_month + 1):
        # 今日特殊样式
        if day == today:
            lbl = ttk.Label(cal_frame, text=str(day), font=("微软雅黑", 12, "bold"), 
                             foreground="white", background="#007AFF", borderwidth=0, relief="flat")
            lbl.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        else:
            lbl = ttk.Label(cal_frame, text=str(day), font=("微软雅黑", 12), foreground="white")
            lbl.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        
        col += 1
        if col > 6:
            col = 0
            row += 1
    
    # 调整行权重
    for r in range(1, row+1):
        cal_frame.grid_rowconfigure(r, weight=1)
    
    # 绑定鼠标事件
    main_frame.bind("<Enter>", on_mouse_enter)
    main_frame.bind("<Leave>", on_mouse_leave)
    main_frame.bind("<Button-1>", on_mouse_click)

def get_current_class(idx, weekday):
    """根据当前时段和星期几获取本节课内容"""
    if idx == 0: return COURSE_TABLE[weekday][0]    # 早读
    elif idx == 1: return COURSE_TABLE[weekday][1]  # 第一节
    elif idx == 2: return COURSE_TABLE[weekday][2]  # 第二节
    elif idx == 3: return COURSE_TABLE[weekday][3]  # 第三节
    elif idx == 4: return COURSE_TABLE[weekday][4]  # 第四节
    elif idx == 5: return "午饭"                    # 午饭
    elif idx == 6: return COURSE_TABLE[weekday][5]  # 午自习
    elif idx == 7: return "午休"                    # 午休
    elif idx == 8: return COURSE_TABLE[weekday][6]  # 第五节
    elif idx == 9: return COURSE_TABLE[weekday][7]  # 第六节
    elif idx == 10: return COURSE_TABLE[weekday][8] # 第七节
    elif idx == 11: return COURSE_TABLE[weekday][9] # 第八节
    return "未知"

def get_next_class(current_idx, weekday):
    """根据当前时段和星期几获取下节课内容"""
    next_idx = current_idx + 1
    if next_idx >= len(SCHEDULE):
        return None
    return get_current_class(next_idx, weekday)

def update_island_display():
    """实时更新时间+星期+天气，自适应宽度（提示时自动暂停）"""
    while island_running:
        if not is_showing_reminder and current_state in [STATE_SLEEP, STATE_SHOW]:
            now = datetime.now()
            now_str = now.strftime("%H:%M:%S")
            weekday_str = WEEKDAY_CN[now.weekday()]
            show_text = f"{now_str} {weekday_str}   {weather_text}"
            time_label.config(text=show_text)
            # 自适应宽度
            island_window.update_idletasks()
            w = time_label.winfo_width() + 35
            island_window.geometry(f"{w}x30")
        time.sleep(1)

def check_schedule_reminder():
    """核心定时提醒逻辑：上课显示本节课+下课显示下节课"""
    global island_running, reminder_triggered, current_date, is_showing_reminder
    while island_running:
        now = datetime.now()
        # 每日自动重置提醒标记
        new_date = now.date()
        if new_date != current_date:
            current_date = new_date
            reminder_triggered.clear()
        
        # 周末自动静默，不触发任何提醒
        weekday = now.weekday()
        if weekday >= 5:
            time.sleep(60)
            continue
        
        for idx, (start_str, end_str, name) in enumerate(SCHEDULE):
            # 解析上课时间
            start_h, start_m = map(int, start_str.split(":"))
            start_time = datetime(now.year, now.month, now.day, start_h, start_m)
            
            # 1. 上课前30秒：显示"上课了   本节课：XX"5秒
            class_remind_time = start_time - timedelta(seconds=30)
            remind_key = f"class_remind_{idx}"
            if now >= class_remind_time and now < class_remind_time + timedelta(seconds=1) and remind_key not in reminder_triggered:
                reminder_triggered.add(remind_key)
                is_showing_reminder = True
                current_class = get_current_class(idx, weekday)
                set_island_state(STATE_SHOW)
                time_label.config(text=f"上课了   本节课：{current_class}")
                time.sleep(5)
                is_showing_reminder = False
                set_island_state(STATE_SLEEP)
            
            # 2. 上课前10秒：切换到隐藏状态（整节课不显示）
            class_hide_time = start_time - timedelta(seconds=10)
            hide_key = f"class_hide_{idx}"
            if now >= class_hide_time and now < class_hide_time + timedelta(seconds=1) and hide_key not in reminder_triggered:
                reminder_triggered.add(hide_key)
                set_island_state(STATE_HIDE)
            
            # 3. 下课瞬间：显示"下课了   下节课：XX"或"放学了"
            end_h, end_m = map(int, end_str.split(":"))
            end_time = datetime(now.year, now.month, now.day, end_h, end_m)
            end_key = f"class_end_{idx}"
            if now >= end_time and now < end_time + timedelta(seconds=1) and end_key not in reminder_triggered:
                reminder_triggered.add(end_key)
                is_showing_reminder = True
                set_island_state(STATE_SHOW)
                # 最后一节课显示放学，其他显示下课+下节课
                if idx == len(SCHEDULE) - 1:
                    time_label.config(text="放学了")
                else:
                    next_class = get_next_class(idx, weekday)
                    time_label.config(text=f"下课了   下节课：{next_class}")
                time.sleep(5)
                is_showing_reminder = False
                set_island_state(STATE_SLEEP)
        
        time.sleep(1)

def check_idle_time():
    """检查空闲时间，自动进入休眠状态"""
    global island_running, last_activity_time, current_state
    while island_running:
        if last_activity_time and (time.time() - last_activity_time) > 5:
            if current_state in [STATE_SHOW, STATE_CALENDAR]:
                set_island_state(STATE_SLEEP)
        time.sleep(1)

def on_mouse_enter(event):
    """鼠标进入事件"""
    global last_activity_time, current_state
    last_activity_time = time.time()
    if current_state == STATE_SLEEP:
        set_island_state(STATE_SHOW)
    elif current_state == STATE_SHOW:
        # 播放悬停放大动画
        current_width, current_height = island_window.winfo_width(), island_window.winfo_height()
        target_width, target_height = current_width * ZOOM_FACTOR, current_height * ZOOM_FACTOR
        animate_size(current_width, current_height, target_width, target_height, ANIMATION_DURATION/2)

def on_mouse_leave(event):
    """鼠标离开事件"""
    global last_activity_time, current_state
    last_activity_time = time.time()
    if current_state == STATE_SHOW:
        # 播放缩小动画回到正常大小
        current_width, current_height = island_window.winfo_width(), island_window.winfo_height()
        target_width, target_height = current_width / ZOOM_FACTOR, current_height / ZOOM_FACTOR
        animate_size(current_width, current_height, target_width, target_height, ANIMATION_DURATION/2)

def on_mouse_click(event):
    """鼠标点击事件"""
    global last_activity_time, current_state
    last_activity_time = time.time()
    if current_state == STATE_SHOW:
        set_island_state(STATE_CALENDAR)
    elif current_state == STATE_CALENDAR:
        set_island_state(STATE_SHOW)

def start_island():
    """开启灵动岛：初始进入休眠状态"""
    global island_running, island_window, time_label, current_state, reminder_triggered, current_date, last_activity_time
    if island_running:
        return
    island_running = True
    reminder_triggered.clear()
    current_date = datetime.now().date()
    last_activity_time = time.time()
    
    # 创建悬浮窗口
    island_window = tk.Toplevel()
    island_window.title("灵动岛")
    island_window.attributes("-topmost", False)
    island_window.attributes("-alpha", 0.75)
    island_window.overrideredirect(True)
    island_window.configure(bg="#121212")
    
    # 屏幕顶部居中
    screen_width = island_window.winfo_screenwidth()
    init_width = 300
    init_height = 30
    x_pos = (screen_width - init_width) // 2
    island_window.geometry(f"{init_width}x{init_height}+{x_pos}+0")  # 初始位置在屏幕顶端
    
    # 文字标签
    time_label = tk.Label(
        island_window,
        text="00:00:00 周一   加载中",
        font=("微软雅黑", 10, "bold"),
        fg="white",
        bg="#121212",
        padx=12
    )
    time_label.pack(fill=tk.BOTH, expand=True)
    
    # 绑定鼠标事件
    island_window.bind("<Enter>", on_mouse_enter)
    island_window.bind("<Leave>", on_mouse_leave)
    island_window.bind("<Button-1>", on_mouse_click)
    
    # 初始进入休眠状态，并播放滑入动画
    set_island_state(STATE_SLEEP)
    animate_slide_in()
    
    # 启动后台线程
    threading.Thread(target=get_weather, daemon=True).start()
    threading.Thread(target=update_island_display, daemon=True).start()
    threading.Thread(target=check_schedule_reminder, daemon=True).start()
    threading.Thread(target=check_idle_time, daemon=True).start()

def stop_island():
    """关闭灵动岛：永久进入隐藏状态"""
    global island_running, island_window, current_state, animation_id
    island_running = False
    current_state = STATE_HIDE
    if animation_id:
        island_window.after_cancel(animation_id)
    if island_window:
        island_window.destroy()
        island_window = None

# 程序启动时自动校准时间
print("正在校准网络时间...")
network_time = sync_network_time()
print(f"当前时间：{network_time.strftime('%Y-%m-%d %H:%M:%S')}")

# 主控制面板
root = tk.Tk()
root.title("Windows智能灵动岛控制面板")
root.geometry("380x190")
root.resizable(False, False)
# 美化布局
frame = ttk.Frame(root, padding=40)
frame.pack(expand=True, fill="both")
ttk.Label(frame, text="Windows 智能灵动岛", font=("微软雅黑", 14, "bold")).pack(pady=8)
ttk.Label(frame, text="流畅动画 · 鼠标悬停 · 点击展开日历", font=("微软雅黑", 9)).pack(pady=2)
btn_on = ttk.Button(frame, text="✅ 开启灵动岛", command=start_island)
btn_on.pack(fill="x", pady=6)
btn_off = ttk.Button(frame, text="❌ 关闭灵动岛", command=stop_island)
btn_off.pack(fill="x", pady=6)
root.mainloop()