import tkinter as tk
from tkinter import filedialog
import datetime
import threading
import time
import json
import os
import winsound
from win10toast import ToastNotifier
import pystray
from PIL import Image, ImageDraw

# 設定檔位置
APP_FOLDER = os.path.join(os.environ['LOCALAPPDATA'], 'alarm_app')
if not os.path.exists(APP_FOLDER):
    os.makedirs(APP_FOLDER)
SETTINGS_FILE = os.path.join(APP_FOLDER, "settings.json")

toaster = ToastNotifier()

def create_image():
    image = Image.new('RGB', (64, 64), color=(0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(255, 255, 255))
    return image

class AlarmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("定時提醒鬧鐘")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.running = False
        self.load_settings()

        # 模式
        self.mode_var = tk.StringVar(value=self.settings.get("mode", "fixed"))
        tk.Label(root, text="提醒模式").pack()
        tk.Radiobutton(root, text="固定分鐘點 (13,28,43,58)", variable=self.mode_var, value="fixed").pack(anchor="w")
        tk.Radiobutton(root, text="固定間隔 (每 15 分鐘)", variable=self.mode_var, value="interval").pack(anchor="w")

        # 固定分鐘點
        tk.Label(root, text="分鐘點（用逗號分隔）").pack()
        self.fixed_entry = tk.Entry(root)
        self.fixed_entry.pack()
        self.fixed_entry.insert(0, self.settings.get("fixed_minutes", "13,28,43,58"))

        # 間隔
        tk.Label(root, text="間隔（分鐘）").pack()
        self.interval_entry = tk.Entry(root)
        self.interval_entry.pack()
        self.interval_entry.insert(0, self.settings.get("interval", "15"))

        # 靜音
        self.silent_var = tk.BooleanVar(value=self.settings.get("silent", False))
        tk.Checkbutton(root, text="靜音（只跳通知）", variable=self.silent_var).pack(anchor="w")

        # 音效檔
        tk.Label(root, text="音效檔 (wav，可不選)").pack()
        frame = tk.Frame(root)
        frame.pack()
        self.sound_entry = tk.Entry(frame, width=30)
        self.sound_entry.pack(side="left")
        self.sound_entry.insert(0, self.settings.get("sound_file", ""))
        tk.Button(frame, text="選擇", command=self.choose_sound).pack(side="left")

        # 狀態
        self.status_label = tk.Label(root, text="狀態：關閉", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # 按鈕
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        self.start_btn = tk.Button(btn_frame, text="開啟", width=10, command=self.start)
        self.start_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(btn_frame, text="關閉", width=10, command=self.stop, state=tk.DISABLED)
        self.stop_btn.pack(side="left", padx=5)

        # 系統匣
        self.icon = pystray.Icon("alarm_app", create_image(), "鬧鐘")
        self.icon.menu = pystray.Menu(
            pystray.MenuItem("開啟視窗", lambda _: self.show_window()),
            pystray.MenuItem("停止鬧鐘", lambda _: self.stop()),
            pystray.MenuItem("退出程式", lambda _: self.exit_app())
        )
        threading.Thread(target=self.icon.run, daemon=True).start()

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.after(0, self.root.lift)

    def choose_sound(self):
        file = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file:
            self.sound_entry.delete(0, tk.END)
            self.sound_entry.insert(0, file)

    def start(self):
        if self.running:
            return
        self.save_settings()
        self.running = True
        self.status_label.config(text="狀態：運行中")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        threading.Thread(target=self.alarm_loop, daemon=True).start()
        self.hide_window()

    def stop(self):
        self.running = False
        self.status_label.config(text="狀態：關閉")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.show_window()

    def exit_app(self):
        self.stop()
        self.icon.stop()
        self.root.destroy()

    def alarm_loop(self):
        last_alert = None
        while self.running:
            now = datetime.datetime.now()
            key = now.strftime("%Y-%m-%d %H:%M")
            trigger = False

            if self.mode_var.get() == "fixed":
                try:
                    minutes = {int(m.strip()) for m in self.fixed_entry.get().split(",")}
                except:
                    minutes = set()
                if now.minute in minutes:
                    trigger = True
            else:
                try:
                    interval = int(self.interval_entry.get())
                except:
                    interval = 15
                total_minutes = now.hour * 60 + now.minute
                if total_minutes % interval == 0:
                    trigger = True

            if trigger and key != last_alert:
                last_alert = key
                self.trigger_alarm()
            time.sleep(10)  # 每 10 秒檢查一次

    def trigger_alarm(self):
        if not self.silent_var.get():
            sound_file = self.sound_entry.get().strip()
            if sound_file and os.path.exists(sound_file):
                winsound.PlaySound(sound_file, winsound.SND_FILENAME)
            else:
                winsound.Beep(1000, 800)
        toaster.show_toast("提醒鬧鐘", "時間到了！", threaded=True, icon_path=None, duration=5)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
            except:
                self.settings = {}
        else:
            self.settings = {}

    def save_settings(self):
        self.settings = {
            "mode": self.mode_var.get(),
            "fixed_minutes": self.fixed_entry.get(),
            "interval": self.interval_entry.get(),
            "silent": self.silent_var.get(),
            "sound_file": self.sound_entry.get()
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = AlarmApp(root)
    root.mainloop()
