import time
import os
import sys
import tkinter as tk
from tkinter import simpledialog
import ctypes
import subprocess

class TimerApp:
    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.sound_files = {
            'start': os.path.join(self.base_dir, '现在计时开始.mp3'),
            'two_minutes': os.path.join(self.base_dir, '两分钟.mp3'),
            'countdown': os.path.join(self.base_dir, '54321.mp3'),
            'asax': os.path.join(self.base_dir, 'ASax.mp3'),
            'eye_exercise': os.path.join(self.base_dir, '眼保健操.mp3'),
            'take_me_hand': os.path.join(self.base_dir, 'take me hand.mp3'),
            'sunny_day': os.path.join(self.base_dir, '晴天。（1）.mp3')
        }
    
    def play_sound(self, sound_key):
        """用Windows自带播放器播放MP3"""
        try:
            sound_file = self.sound_files.get(sound_key)
            if sound_file and os.path.exists(sound_file):
                print(f"播放: {sound_key}")
                # 用系统默认播放器打开（后台播放）
                os.startfile(sound_file)
                # 等待2秒让播放器启动
                time.sleep(2)
                return True
            else:
                print(f"音频文件 {sound_key} 不存在")
                return False
        except Exception as e:
            print(f"播放出错: {e}")
            return False
    
    def lock_screen(self):
        try:
            ctypes.windll.user32.LockWorkStation()
            print("屏幕已锁定")
        except:
            try:
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                print("屏幕已锁定")
            except:
                print("锁屏失败")
    
    def get_minutes(self):
        root = tk.Tk()
        root.withdraw()
        minutes = simpledialog.askinteger("计时器", "请输入分钟数：", minvalue=1, maxvalue=120)
        root.destroy()
        return minutes
    
    def run(self):
        print("=" * 50)
        print("计时器程序")
        print("=" * 50)
        
        minutes = self.get_minutes()
        if not minutes:
            return
        
        total_seconds = minutes * 60
        print(f"设定时间: {minutes} 分钟")
        
        self.play_sound('start')
        print("计时开始...")
        
        start_time = time.time()
        two_minute_played = False
        countdown_triggered = False
        
        while True:
            elapsed = time.time() - start_time
            time_remaining = total_seconds - elapsed
            
            if time_remaining <= 0:
                break
            
            if int(elapsed) % 5 == 0:
                print(f"\r剩余时间: {int(time_remaining//60)}分{int(time_remaining%60)}秒", end="")
            
            if time_remaining <= 120 and not two_minute_played:
                print("\n")
                self.play_sound('two_minutes')
                two_minute_played = True
            
            if time_remaining <= 10 and not countdown_triggered:
                print("\n最后10秒!")
                self.play_sound('countdown')
                countdown_triggered = True
                self.lock_screen()
                
                for sound in ['asax', 'eye_exercise', 'asax', 'take_me_hand', 'asax', 'sunny_day']:
                    self.play_sound(sound)
                
                print("全部播放完成！")
                input("按回车退出...")
                break
            
            time.sleep(0.1)

if __name__ == "__main__":
    app = TimerApp()
    app.run()