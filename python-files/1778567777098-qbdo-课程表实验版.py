import tkinter as tk
from datetime import datetime

weekday = datetime.now().weekday()
courses = [
    ("07:30", "08:00", ["英语", "语文", "英语", "语文", "历史"]),
    ("08:10", "08:55", ["物理", "数学", "数学", "物理", "语文"]),
    ("09:05", "09:50", ["地理", "英语", "英语", "数学", "英语"]),
    ("10:20", "11:05", ["数学", "语文", "历史", "语文", "道法"]),
    ("11:15", "12:00", ["英语", "道法", "生物", "音乐", "地理"]),
    ("14:50", "15:35", ["历史", "生物", "语文", "英语", "数学"]),
    ("15:45", "16:30", ["语文", "物理", "美术", "信息", "体育"]),
    ("16:30", "17:15", ["体育", "体育", "体育", "体育", "周会"]),
    ("18:20", "19:05", ["英语", "数学", "生物", "数学", "地理"]),
    ("19:15", "20:00", ["英语", "数学", "生物", "数学", "地理"]),
]

def get_info():
    now = datetime.now()
    current = "无课"
    next_lesson = "今日结课"
    remain = "00:00"  # 默认无课剩余 00:00

    # 未经允许反推死全家
    if weekday >=5:
        return "周末休息", "00:00", "周末休息"

    
    for i, (s, e, c) in enumerate(courses):
        t1 = datetime.strptime(s, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        t2 = datetime.strptime(e, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        
        if t1 <= now <= t2:
            current = c[weekday]
            delta = t2 - now
            remain = str(delta).split(".")[0][3:]
            if i+1 < len(courses):
                ns, ne, nc = courses[i+1]
                next_lesson = f"{nc[weekday]} {ns}"
            return current, remain, next_lesson

    found = False
    for s, e, c in courses:
        t1 = datetime.strptime(s, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
        if now < t1:
            delta = t1 - now
            remain = str(delta).split(".")[0][3:]
            next_lesson = f"{c[weekday]} {s}"
            found = True
            break

    # 如果所有课都结束了（跨天/无课），强制重置为 00:00
    if not found:
        remain = "00:00"
        next_lesson = "今日结课"

    return current, remain, next_lesson

def update():
    c, r, n = get_info()
    l1.config(text=f"本节：{c}")
    l2.config(text=f"剩余：暂时有问题")
    l3.config(text=f"下节：{n}")
    root.after(1000, update)

def toggle_topmost():
    global is_top
    is_top = not is_top
    root.wm_attributes("-topmost", is_top)
    btn.config(text="置顶" if not is_top else "取消置顶")

is_top = True
root = tk.Tk()
root.title("")
root.geometry("240x135+0+0")
root.wm_attributes("-topmost", is_top)
root.wm_attributes("-alpha", 0.92)
root.resizable(0,0)
root.overrideredirect(True)

l1 = tk.Label(root, text="加载中...", font=("微软雅黑",13))
l2 = tk.Label(root, text="--:--", font=("微软雅黑",13))
l3 = tk.Label(root, text="--", font=("微软雅黑",13))
btn = tk.Button(root, text="取消置顶", command=toggle_topmost, font=("微软雅黑",10))

l1.pack(anchor="w",padx=10,pady=2)
l2.pack(anchor="w",padx=10,pady=2)
l3.pack(anchor="w",padx=10,pady=2)
btn.pack(pady=5)

update()
root.mainloop()