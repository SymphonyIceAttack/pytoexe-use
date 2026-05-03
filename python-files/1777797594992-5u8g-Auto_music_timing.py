#芋泥Pの作り方
import os
import json
import math
import wave
import struct
import tkinter as tk
from tkinter import filedialog, messagebox
from collections import deque

def seconds_to_time(sec):
    hours = int(sec // 3600)
    mins = int((sec % 3600) // 60)
    secs = sec % 60
    return f"{hours:02d}:{mins:02d}:{secs:06.3f}"

class AudioProcessor:
    def __init__(self):
        self.sample_rate = 44100
        self.samples = []
        self.duration = 0.0
        self.onset_times = []

    def load_wav(self, path):
        try:
            with wave.open(path, 'rb') as wf:
                sr = wf.getframerate()
                channels = wf.getnchannels()
                width = wf.getsampwidth()
                frame_count = wf.getnframes()

                if width != 2:
                    return False

                frames = wf.readframes(frame_count)
                samples = []
                total_bytes = len(frames)
                step = width * channels

                for i in range(0, total_bytes, step):
                    chunk = frames[i:i+width]
                    if len(chunk) < width:
                        break
                    s = struct.unpack('<h', chunk)[0]
                    samples.append(s)

                max_val = max((abs(x) for x in samples), default=1)
                self.samples = [x / max_val for x in samples]
                self.sample_rate = sr
                self.duration = len(self.samples) / sr
                return True
        except Exception as e:
            print(e)
            return False

    def detect_onsets(self, sensitivity=1.0):
        if not self.samples:
            return []

        win_ms = 40
        step_ms = 10
        win_size = int(self.sample_rate * win_ms / 1000)
        step_size = int(self.sample_rate * step_ms / 1000)
        min_gap_ms = 120
        min_gap_step = int(min_gap_ms / step_ms)

        energy = []
        for i in range(0, len(self.samples) - win_size, step_size):
            window = self.samples[i:i+win_size]
            e = sum(x*x for x in window) / win_size
            energy.append(math.sqrt(e))

        smooth = deque(maxlen=3)
        smooth_energy = []
        for e in energy:
            smooth.append(e)
            smooth_energy.append(sum(smooth)/len(smooth))

        mean_e = sum(smooth_energy) / len(smooth_energy)
        std_e = math.sqrt(sum((x-mean_e)**2 for x in smooth_energy) / len(smooth_energy))
        threshold = mean_e + sensitivity * std_e

        onsets = []
        last_i = -999

        for i, e in enumerate(smooth_energy):
            if e > threshold and i > last_i + min_gap_step:
                t = i * step_ms / 1000
                onsets.append(round(t, 3))
                last_i = i

        self.onset_times = onsets
        return onsets

class WaveCanvas(tk.Canvas):
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self.proc = None
        self.zoom = 1.0
        self.offset = 0.0
        self.drag_x = None
        self.configure(bg="#121220")
        self.bind("<MouseWheel>", self.on_wheel)
        self.bind("<Button-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_drag)

    def set_audio(self, proc):
        self.proc = proc
        self.zoom = 1.0
        self.offset = 0.0
        self.redraw()

    def redraw(self):
        self.delete(tk.ALL)
        if not self.proc or len(self.proc.samples) == 0:
            return

        w = self.winfo_width()
        h = self.winfo_height()
        mid = h // 2
        dur = self.proc.duration
        vis_dur = dur / self.zoom
        vis_start = self.offset
        vis_end = vis_start + vis_dur
        sr = self.proc.sample_rate

        start_idx = max(0, int(vis_start * sr))
        end_idx = min(len(self.proc.samples)-1, int(vis_end * sr))

        self.create_line(0, mid, w, mid, fill="#3399ff")

        step = max(1, (end_idx - start_idx) // w)
        for x in range(w):
            pos = start_idx + int((x / w) * (end_idx - start_idx))
            pos = min(pos, len(self.proc.samples)-1)
            val = self.proc.samples[pos]
            y = mid - val * mid * 0.85
            self.create_line(x, mid, x, y, fill="#66ccff")

        for t in self.proc.onset_times:
            if vis_start <= t <= vis_end:
                x = ((t - vis_start) / vis_dur) * w
                self.create_oval(x-4, mid-4, x+4, mid+4, fill="#3399ff", outline="")

    def on_wheel(self, e):
        if not self.proc:
            return
        delta = e.delta
        factor = 1.15 if delta > 0 else 0.87
        old_zoom = self.zoom
        self.zoom = max(1.0, min(40.0, self.zoom * factor))
        self.redraw()

    def on_press(self, e):
        self.drag_x = e.x

    def on_drag(self, e):
        if not self.proc or self.drag_x is None:
            return
        dx = e.x - self.drag_x
        w = self.winfo_width()
        dur = self.proc.duration
        vis_dur = dur / self.zoom
        shift = (dx / w) * vis_dur * -0.5
        self.offset += shift
        self.offset = max(0.0, min(dur - vis_dur, self.offset))
        self.drag_x = e.x
        self.redraw()

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("音游自动踩点工具（纯标准库）")
        self.root.geometry("1000 600")
        self.proc = AudioProcessor()
        self.path = ""

        # 波形区域
        self.canvas = WaveCanvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # 控制面板
        panel = tk.Frame(root)
        panel.pack(fill=tk.X, padx=8, pady=4)

        self.btn_load = tk.Button(panel, text="加载WAV", command=self.load_audio)
        self.btn_detect = tk.Button(panel, text="检测突出点", command=self.detect)
        self.btn_export = tk.Button(panel, text="导出JSON", command=self.export_json)
        self.sense = tk.Scale(panel, from_=50, to=300, orient=tk.HORIZONTAL)
        self.sense.set(120)
        self.label = tk.Label(panel, text="就绪")

        for c in [self.btn_load, self.btn_detect, self.btn_export, self.sense, self.label]:
            c.pack(side=tk.LEFT, padx=4)

        # 窗口大小变化重绘
        self.canvas.bind("<Configure>", lambda _: self.canvas.redraw())

    def load_audio(self):
        path = filedialog.askopenfilename(
            filetypes=[("WAV音频", "*.wav")],
            title="选择音频"
        )
        if not path:
            return
        self.path = path
        self.label.config(text="加载中...")
        self.root.update()
        ok = self.proc.load_wav(path)
        if ok:
            self.canvas.set_audio(self.proc)
            self.label.config(text=os.path.basename(path))
        else:
            messagebox.showerror("错误", "仅支持 16bit WAV 音频")
            self.label.config(text="加载失败")

    def detect(self):
        if not self.proc.samples:
            messagebox.showwarning("提示", "请先加载音频")
            return
        self.label.config(text="检测中...")
        self.root.update()
        s = self.sense.get() / 100.0
        self.proc.detect_onsets(sensitivity=s)
        self.canvas.redraw()
        self.label.config(text=f"完成：{len(self.proc.onset_times)} 个点")

    def export_json(self):
        if not self.proc.onset_times:
            messagebox.showwarning("提示", "请先检测踩点")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json")],
            title="保存"
        )
        if not path:
            return

        time_list = [seconds_to_time(t) for t in self.proc.onset_times]

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(time_list, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("成功", f"已导出 {len(time_list)} 个时间点")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()