import tkinter as tk
from tkinter import messagebox
import pyaudio
import wave
import threading
import time
import os
from datetime import datetime
import collections

# --- 配置参数 ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
THRESHOLD_DB = 45  # 噪音阈值
SILENCE_DB = 5    # 安静阈值
BUFFER_SECONDS = 5 # 录音回溯时长（秒）

# --- 确保录音文件夹存在 ---
SAVE_DIR = "ClassRecordings"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

class ClassManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("系统时钟") 
        self.root.geometry("800x600")
        self.root.configure(bg="#1a1a1a")
        
        # 隐藏窗口标题栏
        self.root.overrideredirect(True) 
        # 设置窗口置顶
        self.root.attributes('-topmost', True)

        # --- 界面组件 (伪装成时钟) ---
        self.time_label = tk.Label(root, text="00:00:00", font=("Courier New", 80, "bold"), bg="#1a1a1a", fg="#666")
        self.time_label.pack(expand=True)
        
        self.date_label = tk.Label(root, text="Loading...", font=("Courier New", 16), bg="#1a1a1a", fg="#444")
        self.date_label.pack(pady=20)

        # 状态指示灯
        self.status_dot = tk.Label(root, text="●", font=("Arial", 10), bg="#1a1a1a", fg="#333")
        self.status_dot.place(x=10, y=10)

        # --- 管理员面板 (仅用于查看状态，不再需要保存按钮) ---
        self.admin_panel = tk.Frame(root, bg="black", bd=2, relief="groove")
        self.admin_panel.place(x=600, y=10, width=180, height=200) # 高度减小
        self.is_panel_visible = False
        
        self.log_text = tk.Text(self.admin_panel, height=12, width=20, bg="black", fg="#0f0", font=("Consolas", 10))
        self.log_text.pack()
        
        self.db_label = tk.Label(self.admin_panel, text="音量: 0 dB", bg="black", fg="#0f0")
        self.db_label.pack()

        # --- 音频处理变量 ---
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.is_monitoring = False
        
        # 环形缓冲区
        self.audio_buffer = collections.deque(maxlen=RATE * BUFFER_SECONDS)
        
        # 当前录音片段
        self.current_recording = []
        self.recording_start_time = 0

        # --- 启动逻辑 ---
        self.update_clock()
        self.start_monitoring()

        # --- 快捷键绑定 ---
        self.root.bind('<Escape>', self.toggle_admin)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_clock(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M:%S"))
        self.date_label.config(text=now.strftime("%Y-%m-%d %A"))
        self.root.after(1000, self.update_clock)

    def toggle_admin(self, event=None):
        if self.is_panel_visible:
            self.admin_panel.place_forget()
        else:
            self.admin_panel.place(x=600, y=10, width=180, height=200)
        self.is_panel_visible = not self.is_panel_visible

    def log(self, message):
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
        except:
            pass # 防止面板关闭时报错

    def start_monitoring(self):
        self.is_monitoring = True
        thread = threading.Thread(target=self.audio_loop)
        thread.daemon = True
        thread.start()

    def audio_loop(self):
        try:
            self.stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
            self.log("系统后台运行中...")
            self.status_dot.config(fg="#0f0") 

            while self.is_monitoring:
                data = self.stream.read(CHUNK, exception_on_overflow=False)
                
                # 1. 加入缓冲区
                self.audio_buffer.extend(data)
                
                # 2. 计算音量
                volume = self.calculate_db(data)
                
                # 3. 更新界面
                self.db_label.config(text=f"音量: {volume} dB")

                # 4. 逻辑判断
                self.check_volume_logic(volume)

        except Exception as e:
            self.log(f"错误: {e}")

    def calculate_db(self, data):
        import struct
        import math
        count = len(data) // 2
        shorts = struct.unpack(f"{count}h", data)
        max_amplitude = max(abs(x) for x in shorts)
        if max_amplitude == 0: return 0
        db = 20 * math.log10(max_amplitude / 32768)
        return int(db + 60) 

    def check_volume_logic(self, db):
        # 触发录音
        if db > THRESHOLD_DB:
            if not self.is_recording:
                self.start_recording(db)
            self.root.configure(bg="#330000") # 背景微红
        else:
            self.root.configure(bg="#1a1a1a") # 恢复背景
            # 停止录音
            if self.is_recording and db < (THRESHOLD_DB - 10):
                self.stop_recording()

    def start_recording(self, trigger_db):
        self.is_recording = True
        self.recording_start_time = time.time()
        # 复制缓冲区数据（回溯前5秒）
        self.current_recording = list(self.audio_buffer)
        self.log(f"⚠️ 触发录音 (音量 {trigger_db}dB)...")

    def stop_recording(self):
        self.is_recording = False
        duration = time.time() - self.recording_start_time
        self.log(f"✅ 录音结束，自动保存中...")
        
        # --- 关键修改：直接调用保存函数，无需人工干预 ---
        # 为了防止界面卡顿，可以在新线程保存，但 wav 写入很快，直接调用也没问题
        self.save_wav()

    def save_wav(self):
        # 自动生成文件名：例如 record_143025.wav (代表14点30分25秒触发)
        filename = os.path.join(SAVE_DIR, f"record_{datetime.now().strftime('%H%M%S')}.wav")
        
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(self.current_recording))
            wf.close()
            self.log(f"💾 已保存: {filename}")
        except Exception as e:
            self.log(f"❌ 保存失败: {e}")

    def on_closing(self):
        if messagebox.askokcancel("退出", "确定要关闭监控吗？"):
            self.is_monitoring = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            self.audio.terminate()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClassManagerApp(root)
    root.mainloop()