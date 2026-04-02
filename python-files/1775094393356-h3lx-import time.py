import time

WORK_TIME = 25 * 60   # 25分鐘
BREAK_TIME = 5 * 60   # 5分鐘

def countdown(seconds, mode):
    while seconds > 0:
        mins = seconds // 60
        secs = seconds % 60
        print(f"{mode} {mins:02d}:{secs:02d}", end="\r")
        time.sleep(1)
        seconds -= 1
    print(f"\n{mode}結束！")

while True:
    countdown(WORK_TIME, "🍅 專注時間")
    print("休息一下吧 ☕")
    countdown(BREAK_TIME, "💤 休息時間")

    again = input("再來一輪嗎？(y/n): ")
    if again.lower() != "y":
        break

print("結束，辛苦了！")
input("按 Enter 離開...")
import winsound

def beep():
    winsound.Beep(1000, 1000)
    beep()