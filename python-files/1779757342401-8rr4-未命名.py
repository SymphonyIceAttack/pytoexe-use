import sounddevice as sd
import numpy as np
import tkinter as tk
from tkinter import ttk, scrolledtext
import time
from datetime import datetime
import threading

# -------------------------- 晚自习分贝标准设置 --------------------------
# 安静自习：≤40dB 绿色
# 正常允许：40~45dB 黄色
# 超标吵闹：>45dB 红色
QUIET_MAX = 40
WARNING_MAX = 45

# 全局变量
decibel_value = 0
over_log = []

# -------------------------- 分贝计算核心 --------------------------
def calculate_decibel(indata, frames, time, status):
    global decibel_value
    if status:
        print(status)
    # 计算音量 RMS → 转换成分贝
    rms = np.sqrt(np.mean(np.square(indata)))
    if rms == 0:
        decibel_value = 0
    else:
        # 校准系数（教室环境通用，可微调）
        decibel_value = 20 * np.log10(rms) + 50

def start_audio_stream():
    # 持续监听麦克风
    with sd.InputStream(callback=calculate_decibel):
        while True:
            time.sleep(0.05)

# -------------------------- UI 界面（晚自习专用） --------------------------
class DecibelMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("晚自习分贝监测仪")
        self.root.geometry("800x500")
        self.root.configure(bg="#f5f5f5")

        # 标题
        title_label = tk.Label(
            root, text="📚 晚自习分贝实时监测",
            font=("微软雅黑", 24, "bold"), bg="#f5f5f5"
        )
        title_label.pack(pady=10)

        # 实时分贝显示
        self.db_label = tk.Label(
            root, text="0 dB",
            font=("微软雅黑", 60, "bold"),
            fg="green", bg="#f5f5f5"
        )
        self.db_label.pack(pady=20)

        # 状态提示
        self.status_label = tk.Label(
            root, text="✅ 安静",
            font=("微软雅黑", 20),
            bg="#f5f5f5"
        )
        self.status_label.pack(pady=5)

        # 超标记录区域
        log_frame = ttk.LabelFrame(root, text="超标记录（>45dB）")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, font=("微软雅黑", 11))
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # 启动实时更新
        self.update_display()

    def update_display(self):
        db = round(decibel_value)
        now = datetime.now().strftime("%H:%M:%S")

        # 颜色与状态
        if db <= QUIET_MAX:
            color = "green"
            status = "✅ 安静"
        elif db <= WARNING_MAX:
            color = "orange"
            status = "⚠️ 正常"
        else:
            color = "red"
            status = "❌ 吵闹"
            # 记录超标
            msg = f"【{now}】 超标：{db} dB"
            if len(over_log) == 0 or over_log[-1] != msg:
                over_log.append(msg)
                self.log_text.insert(tk.END, msg + "\n")
                self.log_text.see(tk.END)

        # 更新界面
        self.db_label.config(text=f"{db} dB", fg=color)
        self.status_label.config(text=status, fg=color)

        # 循环刷新
        self.root.after(100, self.update_display)

# -------------------------- 启动软件 --------------------------
if __name__ == "__main__":
    print("🎧 正在启动晚自习分贝监测仪...")
    print("📊 标准：≤40dB 安静 | 40~45dB 正常 | >45dB 吵闹")
    print("------------------------------------------------")

    # 启动音频监听线程
    thread = threading.Thread(target=start_audio_stream, daemon=True)
    thread.start()

    # 启动界面
    window = tk.Tk()
    app = DecibelMonitor(window)
    window.mainloop()
