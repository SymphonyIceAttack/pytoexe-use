import pyperclip
import pygame
import time
import sys
import os
from threading import Thread

# ========== 配置 ==========
# 提示音文件路径（你可以换成自己喜欢的wav/mp3）
SOUND_FILE = "notification.wav"

# 如果没有这个文件，程序会自动生成一个柔和音效（用内置方式）
# ==========================

class ClipboardMonitor:
    def __init__(self):
        self.last_content = pyperclip.paste()
        self.running = True
        
        # 初始化音频
        pygame.mixer.init()
        
        # 如果没有声音文件，使用pygame生成一个柔和音调
        if not os.path.exists(SOUND_FILE):
            self._generate_soft_sound()
    
    def _generate_soft_sound(self):
        """用pygame生成一段柔和的提示音（类似风铃/木琴）"""
        import numpy as np
        
        sample_rate = 44100
        duration = 0.3  # 秒
        
        # 生成两个柔和频率叠加（C6 + E6，听起来像风铃）
        t = np.linspace(0, duration, int(sample_rate * duration))
        freq1, freq2 = 523.25, 659.25  # C6, E6
        
        # 正弦波叠加，加一点衰减让声音更柔
        wave = (np.sin(2 * np.pi * freq1 * t) * 0.3 + 
                np.sin(2 * np.pi * freq2 * t) * 0.2)
        
        # 淡入淡出（消除爆音）
        fade_len = int(0.05 * sample_rate)
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        envelope = np.ones(len(t))
        envelope[:fade_len] = fade_in
        envelope[-fade_len:] = fade_out
        wave = wave * envelope
        
        # 转为16位整数
        wave_int16 = (wave * 32767).astype(np.int16)
        
        # 保存为wav
        import wave
        with wave.open(SOUND_FILE, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(wave_int16.tobytes())
    
    def play_sound(self):
        """播放提示音（非阻塞）"""
        try:
            sound = pygame.mixer.Sound(SOUND_FILE)
            sound.play()
        except:
            # 如果播放失败，用系统beep（备选）
            import winsound
            winsound.Beep(600, 150)  # 600Hz, 150ms
    
    def check_clipboard(self):
        """检查剪贴板是否变化（复制动作）"""
        try:
            current = pyperclip.paste()
            if current != self.last_content and current != "":
                # 剪贴板内容变化 → 说明执行了复制
                self.play_sound()
                self.last_content = current
        except:
            pass  # 某些应用可能访问剪贴板失败
    
    def run(self):
        """主循环"""
        print("✅ 剪贴板监听已启动...")
        print("💡 每次 Ctrl+C 复制内容，都会播放提示音")
        print("🔴 按 Ctrl+Shift+Q 退出程序\n")
        
        while self.running:
            self.check_clipboard()
            time.sleep(0.15)  # 每150ms检查一次，很省资源
    
    def stop(self):
        self.running = False


# ========== 启动 ==========
if __name__ == "__main__":
    monitor = ClipboardMonitor()
    
    # 启动监听（在后台线程运行）
    try:
        monitor.run()
    except KeyboardInterrupt:
        monitor.stop()
        print("\n👋 程序已退出")