import time
import sys
import os
from datetime import datetime, timedelta

def play_sound():
    """跨平台声音提醒"""
    if sys.platform == "win32":
        import winsound
        winsound.Beep(1000, 1500)
    elif sys.platform == "darwin":  # macOS
        os.system('say "下班时间到"')
    elif sys.platform.startswith("linux"):
        os.system('spd-say "下班时间到"')

def set_work_alarm(off_time_str="18:00", remind_minutes=5):
    """
    设置下班闹钟
    off_time_str: 下班时间，格式 "HH:MM"
    remind_minutes: 提前多少分钟提醒
    """
    today = datetime.now().date()
    off_time = datetime.strptime(off_time_str, "%H:%M").replace(
        year=today.year, month=today.month, day=today.day
    )
    remind_time = off_time - timedelta(minutes=remind_minutes)
    
    print("=" * 40)
    print("⏰ 下班闹钟已启动！")
    print(f"📅 今日下班时间: {off_time.strftime('%H:%M')}")
    print(f"🔔 提前 {remind_minutes} 分钟提醒 ({remind_time.strftime('%H:%M')})")
    print("=" * 40)
    print("程序运行中... 按 Ctrl+C 可退出")
    
    reminded = False
    
    while True:
        now = datetime.now()
        
        # 提前提醒
        if not reminded and now >= remind_time:
            print(f"\n⏰ [{now.strftime('%H:%M:%S')}] 还有 {remind_minutes} 分钟下班！")
            play_sound()
            reminded = True
        
        # 下班提醒
        if now >= off_time:
            print(f"\n🎉 [{now.strftime('%H:%M:%S')}] 下班时间到！祝您有愉快的夜晚！")
            for _ in range(3):
                play_sound()
                time.sleep(0.5)
            break
        
        time.sleep(1)

if __name__ == "__main__":
    # 设置你的下班时间
    set_work_alarm(off_time_str="18:00", remind_minutes=5)
    
    # 程序结束后等待用户关闭
    input("\n按回车键退出...")