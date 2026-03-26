
import time
import threading
import os
import sys
import ctypes
from datetime import datetime, timedelta

class AutoLockScreen:
    def __init__(self):
        self.running = True
        self.lock_duration = 10 * 60  # 10分钟锁屏时间
        self.work_duration = 60 * 60   # 1小时工作时间
        self.lock_end_time = None
        
    def lock_screen(self):
        """锁屏函数"""
        if sys.platform == "win32":
            # Windows系统锁屏
            ctypes.windll.user32.LockWorkStation()
        elif sys.platform == "darwin":
            # macOS系统锁屏
            os.system("pmset displaysleepnow")
        else:
            # Linux系统锁屏
            os.system("xdg-screensaver lock")
    
    def unlock_screen(self):
        """解锁函数（仅用于程序内部状态管理）"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 解锁屏幕")
    
    def start_lock_timer(self):
        """启动锁屏计时器"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始锁屏 {self.lock_duration} 秒")
        self.lock_end_time = datetime.now() + timedelta(seconds=self.lock_duration)
        
        # 锁屏
        self.lock_screen()
        
        # 等待解锁时间
        time.sleep(self.lock_duration)
        self.unlock_screen()
        
    def run(self):
        """主运行循环"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 定时锁屏程序启动")
        print(f"设置: 每工作 {self.work_duration} 秒，锁屏 {self.lock_duration} 秒")
        
        try:
            while self.running:
                # 等待工作时间
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始工作 {self.work_duration} 秒")
                time.sleep(self.work_duration)
                
                # 锁屏一段时间
                if self.running:
                    self.start_lock_timer()
                    
        except KeyboardInterrupt:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 程序被用户终止")
            self.running = False
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 程序出现错误: {e}")
        finally:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 程序结束")

def main():
    """程序入口函数"""
    auto_lock = AutoLockScreen()
    auto_lock.run()

if __name__ == "__main__":
    main()
