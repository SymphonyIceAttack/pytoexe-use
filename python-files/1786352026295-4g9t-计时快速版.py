import time
import os
import sys
import tkinter as tk
from tkinter import simpledialog
import pygame
import ctypes
import subprocess

class TimerApp:
    def __init__(self):
        # 获取程序所在目录（支持exe打包）
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        pygame.mixer.init()
        
        # 音频文件路径
        self.sound_files = {
            'start': os.path.join(self.base_dir, '现在计时开始.mp3'),
            'two_minutes': os.path.join(self.base_dir, '两分钟.mp3'),
            'countdown': os.path.join(self.base_dir, '54321.mp3'),
            'asax': os.path.join(self.base_dir, 'ASax.mp3'),
            'eye_exercise': os.path.join(self.base_dir, '眼保健操.mp3'),
            'take_me_hand': os.path.join(self.base_dir, 'take me hand.mp3'),
            'sunny_day': os.path.join(self.base_dir, '晴天。（1）.mp3')
        }
        
    def play_sound(self, sound_key, wait=True):
        try:
            sound_file = self.sound_files.get(sound_key)
            if sound_file and os.path.exists(sound_file):
                print(f"▶ 播放: {sound_key}")
                pygame.mixer.music.load(sound_file)
                pygame.mixer.music.play()
                
                if wait:
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                return True
            else:
                print(f"⚠ 音频文件 {sound_key} 不存在")
                return False
        except Exception as e:
            print(f"✗ 播放音频 {sound_key} 时出错: {e}")
            return False
    
    def lock_screen_windows(self):
        try:
            ctypes.windll.user32.LockWorkStation()
            print("✓ 屏幕已锁定")
            return True
        except:
            try:
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                print("✓ 屏幕已锁定")
                return True
            except:
                print("✗ 锁屏失败")
                return False
    
    def get_user_input(self):
        root = tk.Tk()
        root.withdraw()
        root.title("计时器")
        
        minutes = simpledialog.askinteger(
            "计时器", 
            "请输入需要计时的时间（分钟）：\n(1-120分钟)", 
            minvalue=1, 
            maxvalue=120,
            parent=root
        )
        
        root.destroy()
        return minutes
    
    def run(self):
        print("=" * 50)
        print("          Windows 计时器程序")
        print("=" * 50)
        
        # 检查音频文件
        print("\n检查音频文件...")
        missing_files = []
        for key, path in self.sound_files.items():
            if os.path.exists(path):
                print(f"  ✓ {key}: {os.path.basename(path)}")
            else:
                print(f"  ✗ {key}: 文件不存在")
                missing_files.append(key)
        
        if missing_files:
            print(f"\n⚠ 警告: 以下音频文件缺失: {', '.join(missing_files)}")
            input("按回车键继续...")
        
        # 获取用户输入
        print("\n" + "-" * 50)
        minutes = self.get_user_input()
        
        if minutes is None:
            print("用户取消输入，程序退出")
            input("按回车键退出...")
            return
        
        total_seconds = minutes * 60
        print(f"\n✓ 设定时间: {minutes} 分钟 ({total_seconds} 秒)")
        
        self.play_sound('start')
        
        print("\n计时开始...")
        start_time = time.time()
        
        two_minute_played = False
        countdown_triggered = False
        
        try:
            while True:
                elapsed = time.time() - start_time
                time_remaining = total_seconds - elapsed
                
                if time_remaining <= 0:
                    break
                
                if int(elapsed) % 5 == 0:
                    minutes_left = int(time_remaining // 60)
                    seconds_left = int(time_remaining % 60)
                    sys.stdout.write(f"\r⏱ 剩余时间: {minutes_left:02d}:{seconds_left:02d}")
                    sys.stdout.flush()
                
                if time_remaining <= 120 and time_remaining > 119 and not two_minute_played:
                    print("\n" + "-" * 50)
                    self.play_sound('two_minutes')
                    two_minute_played = True
                
                if time_remaining <= 10 and time_remaining > 0 and not countdown_triggered:
                    print("\n" + "-" * 50)
                    print("⏰ 最后10秒倒计时!")
                    
                    self.play_sound('countdown')
                    countdown_triggered = True
                    
                    print("\n" + "-" * 50)
                    print("🔒 正在锁定屏幕...")
                    self.lock_screen_windows()
                    
                    print("\n" + "-" * 50)
                    print("播放后续音频序列...")
                    
                    audio_sequence = [
                        'asax', 'eye_exercise', 'asax',
                        'take_me_hand', 'asax', 'sunny_day'
                    ]
                    
                    for idx, sound_key in enumerate(audio_sequence, 1):
                        print(f"\n[{idx}/{len(audio_sequence)}] ", end="")
                        self.play_sound(sound_key)
                    
                    print("\n" + "=" * 50)
                    print("✓ 所有音频播放完成，程序结束")
                    input("按回车键退出...")
                    break
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            input("按回车键退出...")
        except Exception as e:
            print(f"\n程序运行出错: {e}")
            input("按回车键退出...")
        finally:
            pygame.mixer.quit()

if __name__ == "__main__":
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    app = TimerApp()
    app.run()