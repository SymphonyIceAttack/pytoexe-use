import time
import threading
import subprocess
import psutil
import numpy as np
import cv2
from ultralytics import YOLO
import customtkinter as ctk
import json
import os
import struct
import queue

# ================== SETTINGS ==================
DEVICE = "127.0.0.1:5555"
MODEL_PATH = "best.pt"  # ضع هنا ملف YOLO المدرب على الرأس

CENTER_X, CENTER_Y = 540, 960
MIN_FIRE_DELAY = 0.02
PERF_FILE = "performance.json"
SMOOTH_FACTOR = 0.15
MAX_TARGETS = 3
MODEL_CONF = 0.6

model = YOLO(MODEL_PATH)
running = False
reaction_times = []
performance_history = []


# ================== UTILS ==================
def run(cmd):
    try:
        return subprocess.getoutput(cmd)
    except:
        return ""


def load_perf():
    if os.path.exists(PERF_FILE):
        with open(PERF_FILE, "r") as f:
            return json.load(f)
    return {"pointer": 12, "density": 280, "fps_boost": True}


def save_perf(perf):
    with open(PERF_FILE, "w") as f:
        json.dump(perf, f)


perf = load_perf()


def boost_emulator():
    cmds = [
        "settings put global window_animation_scale 0",
        "settings put global transition_animation_scale 0",
        "settings put global animator_duration_scale 0",
        f"wm density {perf['density']}",
        f"settings put system pointer_speed {perf['pointer']}",
        "input keyevent 82"
    ]
    for cmd in cmds:
        run(f"adb -s {DEVICE} shell {cmd}")


cpu_history = []
fps_history = []


def adjust_pointer_speed(cpu, fps):
    if cpu > 85 or fps < 25:
        perf['pointer'] = 10
    elif fps > 50:
        perf['pointer'] = 15
    else:
        perf['pointer'] = 12
    run(f'adb -s {DEVICE} shell "settings put system pointer_speed {perf["pointer"]}"')
    save_perf(perf)


def track_performance(cpu, fps):
    cpu_history.append(cpu)
    fps_history.append(fps)
    if len(cpu_history) > 10:
        cpu_history.pop(0)
        fps_history.pop(0)

    avg_cpu = sum(cpu_history) / len(cpu_history)
    avg_fps = sum(fps_history) / len(fps_history)

    performance_history.append((avg_cpu, avg_fps))
    if len(performance_history) > 120:
        performance_history.pop(0)

    adjust_pointer_speed(avg_cpu, avg_fps)


# ================== MINICAP OR SCREENCAP ==================
class ScreenCapture:
    def __init__(self):
        self.use_minicap = False
        self.process = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=3)
        self.target_width = 640
        self.target_height = 960
        self.check_minicap()

    def check_minicap(self):
        # تحقق إذا minicap موجود
        result = run(f"adb -s {DEVICE} shell 'which minicap'")
        if result.strip():
            self.use_minicap = True
            print("✅ Using Minicap")
        else:
            print("⚠️ Minicap not found, using ADB screencap")
            self.use_minicap = False

    def start(self):
        if self.use_minicap:
            cmd = f"adb -s {DEVICE} shell minicap -P 720x1280@720x1280/0"
            self.process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            self.running = True
            threading.Thread(target=self._capture_minicap, daemon=True).start()

    def _read_exact(self, size):
        data = b''
        while len(data) < size:
            chunk = self.process.stdout.read(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def _capture_minicap(self):
        banner = self._read_exact(24)
        if not banner:
            print("❌ Minicap failed")
            self.use_minicap = False
            return
        print("✅ Minicap Started")
        while self.running:
            header = self._read_exact(4)
            if not header:
                break
            frame_size = struct.unpack('<I', header)[0]
            frame_data = self._read_exact(frame_size)
            if not frame_data:
                break
            img = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
            if frame is None:
                continue
            frame = cv2.resize(frame, (self.target_width, self.target_height))
            if self.frame_queue.full():
                self.frame_queue.get()
            self.frame_queue.put(frame)

    def capture_screencap(self):
        result = subprocess.run(f"adb -s {DEVICE} exec-out screencap -p", shell=True, capture_output=True)
        img_array = np.frombuffer(result.stdout, dtype=np.uint8)
        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if frame is None:
            return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        frame = cv2.resize(frame, (self.target_width, self.target_height))
        return frame

    def get_frame(self):
        if self.use_minicap:
            try:
                return self.frame_queue.get_nowait()
            except:
                return np.zeros((self.target_height, self.target_width, 3), dtype=np.uint8)
        else:
            return self.capture_screencap()

    def stop(self):
        self.running = False
        if self.process:
            self.process.terminate()


cap = ScreenCapture()
cap.start()


def capture_screen():
    return cap.get_frame()


# ================== YOLO DETECTION ==================
def detect_heads(frame):
    results = model(frame, verbose=False)
    targets = []
    for r in results:
        for box in r.boxes:
            if int(box.cls[0]) == 0 and float(box.conf[0]) >= MODEL_CONF:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                head_x = (x1 + x2) // 2
                head_y = int(y1 + (y2 - y1) * 0.25)
                targets.append((head_x, head_y))
                if len(targets) >= MAX_TARGETS:
                    break
    return targets


# ================== AIM & FIRE ==================
def smooth_aim(target):
    x, y = target
    dx = int((x - CENTER_X) * SMOOTH_FACTOR)
    dy = int((y - CENTER_Y) * SMOOTH_FACTOR)
    dx = max(min(dx, 50), -50)
    dy = max(min(dy, 50), -50)
    new_x = CENTER_X + dx
    new_y = CENTER_Y + dy
    run(f'adb -s {DEVICE} shell input swipe {CENTER_X} {CENTER_Y} {new_x} {new_y} 15')


def rapid_fire():
    run(f'adb -s {DEVICE} shell input tap {CENTER_X} {CENTER_Y}')


# ================== REACTION ==================
def track_reaction(targets_detected, last_seen):
    now = time.time()
    if targets_detected and last_seen[0] is None:
        last_seen[0] = now
    elif not targets_detected and last_seen[0] is not None:
        reaction_times.append(now - last_seen[0])
        last_seen[0] = None


def stats():
    if not reaction_times: return "No Data"
    avg = sum(reaction_times) / len(reaction_times)
    if avg < 0.25:
        return "🔥 PRO"
    elif avg < 0.5:
        return "⚡ GOOD"
    else:
        return "🐢 SLOW"


# ================== OVERLAY ==================
def draw_overlay(frame, targets):
    for (x, y) in targets:
        cv2.circle(frame, (x, y), 10, (0, 0, 255), -1)
    cv2.circle(frame, (CENTER_X, CENTER_Y), 12, (255, 0, 0), 2)
    cv2.putText(frame, stats(), (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    return frame


# ================== AI LOOP ==================
def ai_loop():
    last_seen = [None]
    boost_emulator()
    ai_loop.last_time = time.time()
    frame_count = 0
    while running:
        frame = capture_screen()
        cpu = psutil.cpu_percent()
        now = time.time()
        fps = 1 / (now - ai_loop.last_time + 1e-5)
        ai_loop.last_time = now

        targets = detect_heads(frame)
        track_reaction(bool(targets), last_seen)
        track_performance(cpu, fps)

        if targets:
            for target in targets:
                smooth_aim(target)
                rapid_fire()
            status.set(f"🎯 HEADSHOT LOCK ({len(targets)} Targets)")
        else:
            status.set("🔍 SEARCH")

        frame = draw_overlay(frame, targets)
        frame_count += 1
        if frame_count % 2 == 0:
            cv2.imshow("MAX BLUE STACKS PRO AI V5", frame)
            cv2.waitKey(1)


# ================== UI ==================
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.geometry("500x700")

status = ctk.StringVar(value="Idle")
ctk.CTkLabel(app, text="🎯 MAX BLUE STACKS PRO AI V5", font=("Arial", 20)).pack(pady=10)
ctk.CTkLabel(app, textvariable=status).pack()


def start_ai():
    global running
    running = True
    threading.Thread(target=ai_loop, daemon=True).start()


def stop_ai():
    global running
    running = False
    cap.stop()
    cv2.destroyAllWindows()


ctk.CTkButton(app, text="Start", command=start_ai).pack(pady=10)
ctk.CTkButton(app, text="Stop", command=stop_ai).pack(pady=10)

app.mainloop()