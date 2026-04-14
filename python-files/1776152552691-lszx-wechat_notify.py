import win32gui
import win32con
import time
import re
from win10toast import ToastNotifier

toaster = ToastNotifier()
WECHAT_KEY = "微信"
last_shown = {}
COOLDOWN = 2

FILTER = [
    "文件传输助手", "图片", "表情", "语音", "视频", "拍了拍",
    "转账", "红包", "公众号", "服务通知", "微信", "腾讯新闻"
]

def clean(s):
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:23] + "..." if len(s) > 26 else s

def show(title, msg):
    try:
        toaster.show_toast(title, msg, duration=3, threaded=True)
    except:
        pass

def callback(hwnd, _):
    if not win32gui.IsWindowVisible(hwnd):
        return True
    t = win32gui.GetWindowText(hwnd).strip()
    if WECHAT_KEY not in t or len(t) < 6:
        return True
    if any(k in t for k in FILTER):
        return True
    if '-' not in t:
        return True

    user, content = t.split('-', 1)
    user = user.strip()
    content = content.strip()
    key = f"{user}{content}"
    now = time.time()

    if key in last_shown and now - last_shown[key] < COOLDOWN:
        return True

    last_shown[key] = now
    show(f"💬 {user}", clean(content))
    return True

print("✅ 微信消息预览已运行（Win11）")
print("⏹ 关闭此窗口 或 任务管理器结束进程即可关闭")
print("="*50)

while True:
    try:
        win32gui.EnumWindows(callback, None)
        time.sleep(1)
    except KeyboardInterrupt:
        break
    except:
        time.sleep(1)