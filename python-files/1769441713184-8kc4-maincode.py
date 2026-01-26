import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from threading import Thread
import time
import numpy as np
import mss
import pydirectinput
from ultralytics import YOLO
import keyboard
import sys
import cv2
import json
import os
import webbrowser  # 유튜브 링크 연결용

# === [설정] ===
# 모델 경로를 본인의 환경에 맞게 반드시 수정하세요!
MODEL_PATH = "TryHard Rod.pt"
DEFAULT_CONFIDENCE = 0.40
AURORA_INTERVAL = 12.5 * 60 
CONFIG_FILE = "config.data"

# === [이용약관 텍스트 (법적 보호 강화 버전)] ===
TERMS_OF_SERVICE = """Terms of Service (Legal & Security Notice)
Effective Date: 2025-01-27

1. Description of the Software
This software (“Program”) is a local automation tool.
To function, this Program strictly requires and performs the following actions on your computer:
- Screen Capture: Analyzes specific screen regions to detect game visuals.
- Input Simulation: Simulates mouse clicks and keyboard presses (Virtual HID).

2. Privacy and Data Security
- Local Operation Only: This Program operates 100% locally. It does NOT upload, stream, or store your screen data or keystrokes on any external server.
- No Personal Data Collection: The developer does not collect any personal information, login credentials, or financial data through this Program.

3. SECURITY WARNING (Crucial)
The official source of this Program is the developer, distributable via KakaoTalk user “Kiwoom_mossripper”.

WARNING: If you obtained this file from any other source (e.g., random Discord servers, file-sharing sites, third-party resellers):
- It is highly likely to contain MALWARE, KEYLOGGERS, or RANSOMWARE.
- The code may have been altered to steal your accounts.
- The developer assumes NO RESPONSIBILITY for damages caused by using unofficial versions.

4. Limitation of Liability
By using this Program, you acknowledge and agree that:
- Game Policy: Automation tools may violate the Terms of Service of specific games.
- User Responsibility: You are solely responsible for any consequences, including game account bans, suspensions, or penalties.
- Disclaimer: The developer is not liable for any direct or indirect damages, including hardware failure, data loss, or legal disputes arising from the use of this Program.

5. License & Distribution
- Open Source Components: This Program utilizes libraries (YOLO, OpenCV, etc.) subject to their respective licenses (AGPL-3.0, Apache 2.0, etc.).
- Redistribution: While redistribution is not strictly prohibited to comply with open-source licenses, users are strongly advised to verify the source integrity (See Section 3).

6. Attribution
This Program references concepts by Asphalt cake.
Support the creators:
- YouTube: Ayang
- YouTube: Asphalt cake

7. Acceptance
By initializing this Program, you certify that you have read this agreement, understand the privacy implications (Section 2), and accept full liability for its use."""

# ==================================================================================
# [MODULE 1] VISION SYSTEM
# ==================================================================================
class VisionSystem:
    def __init__(self, model_path):
        try:
            self.model = YOLO(model_path)
            self.model_loaded = True
            print("[SYSTEM] AI Model Loaded Successfully.")
        except Exception as e:
            self.model_loaded = False
            print(f"[CRITICAL ERROR] 모델 로드 실패: {e}")

    def detect(self, sct, capture_area, conf_threshold):
        if not self.model_loaded: return None, None
        try:
            img = np.array(sct.grab(capture_area))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except: return None, None

        results = self.model(frame, verbose=False, conf=conf_threshold)
        icon_x, bar_x = None, None
        off_x, off_y = capture_area["left"], capture_area["top"]

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                cx = (x1 + x2) / 2
                abs_box = (x1 + off_x, y1 + off_y, x2 + off_x, y2 + off_y)
                if cls_id == 0: icon_x = (cx, abs_box)
                elif cls_id == 1: bar_x = (cx, abs_box)
        return icon_x, bar_x

# ==================================================================================
# [MODULE 2] PHYSICS ENGINE
# ==================================================================================
class PhysicsEngine:
    def __init__(self):
        self.kp = 4.0
        self.ki = 0.01
        self.kd = 4.5
        self.tension = 25.0
        self.deadzone = 10.0
        self.base_deadzone = 10.0
        
        self.prev_error = 0
        self.integral = 0
        self.last_time = time.time()
        self.start_time = 0
        self.prev_icon_x = 0
        self.active = False
    
    def reset(self):
        self.prev_error = 0
        self.integral = 0
        self.last_time = time.time()
        self.start_time = time.time()
        self.active = True

    def compute(self, target_x, current_x, view_width):
        curr_time = time.time()
        dt = curr_time - self.last_time
        
        if dt > 0.1: dt = 0.05 
        if dt <= 0: return 0

        # 속도 계산
        icon_vel = abs(target_x - self.prev_icon_x) / dt
        self.prev_icon_x = target_x
        
        current_deadzone = self.base_deadzone
        if icon_vel < 30: current_deadzone = self.base_deadzone * 0.5

        error = target_x - current_x
        
        # 데드존 체크
        if abs(error) < current_deadzone:
            self.integral = 0
            self.last_time = curr_time
            return self.tension 

        self.integral += error * dt
        self.integral = max(min(self.integral, 100), -100)

        P = self.kp * error
        I = self.ki * self.integral
        D = self.kd * ((error - self.prev_error) / dt)
        
        FF_Tension = self.tension

        PID_Output = P + I + D
        
        final_output = PID_Output + FF_Tension
        self.prev_error = error
        self.last_time = curr_time
        
        return final_output

# ==================================================================================
# [MODULE 3] ACTION CONTROLLER (AURORA UPDATED)
# ==================================================================================
class ActionController:
    def __init__(self):
        self._holding = False

    def hold(self):
        if not self._holding:
            pydirectinput.mouseDown()
            self._holding = True
    
    def release(self):
        if self._holding:
            pydirectinput.mouseUp()
            self._holding = False
    
    def cast_rod(self):
        self.release()
        time.sleep(0.05)
        pydirectinput.mouseDown()
        time.sleep(0.45) 
        pydirectinput.mouseUp()
        print("[ACTION] Rod Casted.")

    def trigger_aurora(self):
        print("[ACTION] Auto Aurora Sequence Started...")
        self.release() # 낚싯대 줄 놓기
        
        # 1. 3번키 (토템) -> 클릭
        pydirectinput.press('3')
        time.sleep(0.2)
        pydirectinput.click()
        print("[ACTION] Totem Placed. Waiting 15 seconds...")
        
        # 2. 15초 대기
        time.sleep(15.0) 
        
        # 3. 4번키 (추가 아이템) -> 클릭
        pydirectinput.press('4')
        time.sleep(0.2)
        pydirectinput.click()
        time.sleep(0.2)
        
        # 4. 1번키 (낚싯대 복귀)
        pydirectinput.press('1')
        time.sleep(0.5) 
        print("[ACTION] Aurora Sequence Complete. Resuming Fishing.")

# ==================================================================================
# [MODULE 4] OVERLAY SYSTEM (DEV MODE ADDED)
# ==================================================================================
class OverlaySystem:
    def __init__(self, root):
        self.top = tk.Toplevel(root)
        self.top.attributes("-topmost", True, "-transparentcolor", "black", "-toolwindow", True)
        self.top.overrideredirect(True)
        w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        self.top.geometry(f"{w}x{h}+0+0")
        
        self.canvas = tk.Canvas(self.top, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.rects = {}
        self.text_id = self.canvas.create_text(20, 50, text="READY", fill="white", anchor="nw", font=("Consolas", 14, "bold"))
        self.aurora_id = self.canvas.create_text(20, 80, text="", fill="magenta", anchor="nw", font=("Consolas", 10))

    def draw(self, tag, coords, color, show=True):
        if not show:
            if tag in self.rects:
                self.canvas.itemconfig(self.rects[tag], state='hidden')
            return

        x1, y1, x2, y2 = coords
        if tag in self.rects:
            self.canvas.coords(self.rects[tag], x1, y1, x2, y2)
            self.canvas.itemconfig(self.rects[tag], state='normal', outline=color)
        else:
            self.rects[tag] = self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=2)

    def set_status(self, text, color="white"):
        self.canvas.itemconfig(self.text_id, text=text, fill=color)

    def set_aurora_status(self, text):
        self.canvas.itemconfig(self.aurora_id, text=text)

    def clear(self):
        for tag in self.rects: self.canvas.itemconfig(self.rects[tag], state='hidden')
        self.canvas.itemconfig(self.text_id, text="")
        self.canvas.itemconfig(self.aurora_id, text="")

# ==================================================================================
# [MAIN] APPLICATION
# ==================================================================================
class FischMacroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AY_TryHard_V1.2 (DevMode)")
        self.root.geometry("500x980") # 유튜브 버튼 추가로 높이 약간 증가
        self.root.attributes("-topmost", True)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # Config 및 기본값 로드
        self.default_config = {
            "capture_area": {"top": 400, "left": 800, "width": 400, "height": 150},
            "fps": 60,
            "cast_delay": 0.1,
            "aurora_enabled": False,
            "dev_mode": True,
            "kp": 4.0,
            "ki": 0.01,
            "kd": 4.5,
            "tension": 25.0,
            "deadzone": 10.0,
            "tos_accepted": False 
        }
        
        self.config = self.load_config()
        
        # 약관 동의 체크
        if not self.config.get("tos_accepted", False):
            self.show_tos_dialog()
            if not self.config.get("tos_accepted", False):
                sys.exit()

        self.vision = VisionSystem(MODEL_PATH)
        self.physics = PhysicsEngine()
        self.action = ActionController()
        self.overlay = OverlaySystem(root)
        self.capture_area = self.config["capture_area"]

        self.running = False
        self.active_program = True
        self.game_state = "IDLE"
        self.last_seen_time = time.time()
        self.last_aurora_time = 0 

        self.setup_ui()
        
        self.thread = Thread(target=self.main_loop, daemon=True)
        self.thread.start()

        keyboard.add_hotkey('f3', self.toggle)
        keyboard.add_hotkey('q', self.on_close)
        keyboard.add_hotkey('f1', self.set_area_mode)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    print(f"[SYSTEM] Config loaded.")
                    config = self.default_config.copy()
                    config.update(data)
                    return config
            except Exception as e:
                print(f"[ERROR] Config load fail: {e}")
                return self.default_config.copy()
        else:
            return self.default_config.copy()

    def save_config(self):
        self.config["capture_area"] = self.capture_area
        self.config["fps"] = self.var_fps.get() if hasattr(self, 'var_fps') else self.config["fps"]
        self.config["cast_delay"] = self.var_cast_delay.get() if hasattr(self, 'var_cast_delay') else self.config["cast_delay"]
        self.config["aurora_enabled"] = self.var_aurora.get() if hasattr(self, 'var_aurora') else self.config["aurora_enabled"]
        self.config["dev_mode"] = self.var_dev.get() if hasattr(self, 'var_dev') else self.config["dev_mode"]
        self.config["kp"] = self.var_kp.get() if hasattr(self, 'var_kp') else self.config["kp"]
        self.config["ki"] = self.var_ki.get() if hasattr(self, 'var_ki') else self.config["ki"]
        self.config["kd"] = self.var_kd.get() if hasattr(self, 'var_kd') else self.config["kd"]
        self.config["tension"] = self.var_ten.get() if hasattr(self, 'var_ten') else self.config["tension"]
        self.config["deadzone"] = self.var_dz.get() if hasattr(self, 'var_dz') else self.config["deadzone"]

        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f, indent=4)
            print(f"[SYSTEM] Config saved.")
        except Exception as e:
            print(f"[ERROR] Save fail: {e}")

    def show_tos_dialog(self):
        self.root.withdraw()
        
        tos_win = tk.Toplevel(self.root)
        tos_win.title("Terms of Service Agreement")
        tos_win.geometry("600x700")
        tos_win.protocol("WM_DELETE_WINDOW", sys.exit)

        lbl = tk.Label(tos_win, text="Please read and accept the Terms of Service to continue.", font=("Arial", 12, "bold"))
        lbl.pack(pady=10)

        txt_area = ScrolledText(tos_win, wrap=tk.WORD, width=70, height=30)
        txt_area.insert(tk.INSERT, TERMS_OF_SERVICE)
        txt_area.configure(state='disabled')
        txt_area.pack(padx=10, pady=10, fill="both", expand=True)

        btn_frame = tk.Frame(tos_win)
        btn_frame.pack(pady=10)

        def on_agree():
            self.config["tos_accepted"] = True
            try:
                with open(CONFIG_FILE, "w") as f:
                    json.dump(self.config, f, indent=4)
            except: pass
            tos_win.destroy()
            self.root.deiconify()

        def on_decline():
            sys.exit()

        btn_agree = tk.Button(btn_frame, text="I HAVE READ AND AGREE", command=on_agree, bg="green", fg="white", font=("Arial", 10, "bold"), height=2)
        btn_agree.pack(side="left", padx=20)

        btn_decline = tk.Button(btn_frame, text="DECLINE (EXIT)", command=on_decline, bg="red", fg="white", font=("Arial", 10, "bold"), height=2)
        btn_decline.pack(side="right", padx=20)

        tos_win.grab_set()
        self.root.wait_window(tos_win)

    def on_close(self):
        self.save_config()
        self.active_program = False
        self.action.release()
        self.root.destroy()
        sys.exit()

    def show_virus_warning(self):
        warn_msg = """[CRITICAL SECURITY WARNING]

If you did not obtain this software directly from KakaoTalk user "Kiwoom_mossripper,"
THIS FILE IS LIKELY A VIRUS OR MALWARE.

Unofficial versions may contain:
- Keyloggers (password theft)
- Ransomware
- Remote Access Trojans

The developer is not responsible for any damage caused by unofficial versions.
If you do not know the source, be cautious. The developer assumes no responsibility."""
        messagebox.showwarning("SECURITY ALERT", warn_msg, parent=self.root)

    def open_url(self, url):
        webbrowser.open(url)

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # === [Header] ===
        header_frame = tk.Frame(self.root)
        header_frame.pack(fill="x", pady=10)
        
        # Title
        title = tk.Label(header_frame, text="AY_TryHard_V1.2", font=("Impact", 20), fg="#6200EA")
        title.pack(side="top")

        # [!] Security Warning Button (Top Right)
        btn_warn = tk.Button(self.root, text=" [ ! ] ", command=self.show_virus_warning, 
                             bg="red", fg="white", font=("Arial", 9, "bold"), bd=0)
        btn_warn.place(relx=1.0, x=-5, y=5, anchor="ne")

        self.status_lbl = tk.Label(self.root, text="STOPPED", font=("Arial", 14, "bold"), fg="gray")
        self.status_lbl.pack()

        # === [1] General Settings ===
        g_frame = tk.LabelFrame(self.root, text="General Settings", padx=10, pady=10)
        g_frame.pack(fill="x", padx=10, pady=5)
        
        self.var_dev = tk.BooleanVar(value=self.config.get("dev_mode", True))
        chk_dev = tk.Checkbutton(g_frame, text="Dev Mode (Show Overlay)", variable=self.var_dev, font=("Arial", 10), fg="blue")
        chk_dev.pack(anchor="w", pady=(0, 5))

        tk.Label(g_frame, text="Scan FPS").pack(anchor="w")
        self.var_fps = tk.IntVar(value=self.config["fps"])
        tk.Scale(g_frame, from_=10, to=144, orient="horizontal", variable=self.var_fps).pack(fill="x")
        
        tk.Label(g_frame, text="Auto Cast Delay (sec)").pack(anchor="w")
        self.var_cast_delay = tk.DoubleVar(value=self.config["cast_delay"])
        tk.Scale(g_frame, from_=0.1, to=5.0, resolution=0.1, orient="horizontal", variable=self.var_cast_delay).pack(fill="x")

        # === [2] Auto Aurora ===
        a_frame = tk.LabelFrame(self.root, text="Auto Aurora / Totem", padx=10, pady=10)
        a_frame.pack(fill="x", padx=10, pady=5)
        
        self.var_aurora = tk.BooleanVar(value=self.config["aurora_enabled"])
        chk_aurora = tk.Checkbutton(a_frame, text="Enable Auto Aurora (Every 12.5m)", variable=self.var_aurora, font=("Arial", 10, "bold"))
        chk_aurora.pack(anchor="w")
        tk.Label(a_frame, text="* Sequence: 3->Click->Wait 15s->4->Click", font=("Arial", 8), fg="gray").pack(anchor="w")

        # === [3] Physics Tuning ===
        f = tk.LabelFrame(self.root, text="Physics Tuning", padx=10, pady=10)
        f.pack(fill="x", padx=10, pady=5)

        tk.Label(f, text="Kp (Reaction Speed)").pack(anchor="w")
        self.var_kp = tk.DoubleVar(value=self.config["kp"])
        tk.Scale(f, from_=1.0, to=10.0, resolution=0.1, orient="horizontal", variable=self.var_kp).pack(fill="x")

        tk.Label(f, text="Ki (Error Fix)").pack(anchor="w")
        self.var_ki = tk.DoubleVar(value=self.config["ki"])
        tk.Scale(f, from_=0.0, to=1.0, resolution=0.01, orient="horizontal", variable=self.var_ki).pack(fill="x")

        tk.Label(f, text="Kd (Braking)").pack(anchor="w")
        self.var_kd = tk.DoubleVar(value=self.config["kd"])
        tk.Scale(f, from_=0.0, to=10.0, resolution=0.1, orient="horizontal", variable=self.var_kd).pack(fill="x")

        tk.Label(f, text="Tension (Gravity Bypass)").pack(anchor="w")
        self.var_ten = tk.DoubleVar(value=self.config["tension"])
        tk.Scale(f, from_=0.0, to=50.0, resolution=1.0, orient="horizontal", variable=self.var_ten).pack(fill="x")

        tk.Label(f, text="Deadzone (Anti-Jitter)").pack(anchor="w")
        self.var_dz = tk.DoubleVar(value=self.config["deadzone"])
        tk.Scale(f, from_=0.0, to=50.0, resolution=1.0, orient="horizontal", variable=self.var_dz).pack(fill="x")

        btn_area = tk.Button(self.root, text="[F1] SET CAPTURE AREA", command=self.set_area_mode, height=2, bg="#212121", fg="white")
        btn_area.pack(fill="x", padx=10, pady=10)

        # === [4] Support & Credits ===
# === [4] Support & Credits ===
        c_frame = tk.LabelFrame(self.root, text="Credits & Support (Click to Subscribe)", padx=10, pady=5)
        c_frame.pack(fill="x", padx=10, pady=5)

        # 1. Developer Section
        tk.Label(c_frame, text="[ Main Developer ]", font=("Arial", 9, "bold"), fg="#333333").pack(anchor="center", pady=(5, 0))
        
        btn_ayang = tk.Button(c_frame, text="▶ Youtube: Ayang", bg="#FF0000", fg="white", font=("Arial", 10, "bold"), 
                              command=lambda: self.open_url("https://www.youtube.com/@aya.ngg8"))
        btn_ayang.pack(fill="x", pady=2)

        # 구분선 느낌의 여백
        tk.Label(c_frame, text="", font=("Arial", 2)).pack()

        # 2. Inspiration Section (명확한 구분)
        tk.Label(c_frame, text="[ Special Thanks / Concept Inspiration ]", font=("Arial", 9, "bold"), fg="gray").pack(anchor="center", pady=(5, 0))
        
        # 핵심 문구 추가: "코드는 베끼지 않았고, 영상 개념만 참고함"
        tk.Label(c_frame, text="* Code is 100% original, inspired by public video concepts.", font=("Arial", 7), fg="gray").pack(anchor="center")

        btn_asphalt = tk.Button(c_frame, text="▶ Youtube: Asphalt cake", bg="#555555", fg="white", font=("Arial", 10, "bold"), # 색상을 다르게 하여 개발자와 구분
                                command=lambda: self.open_url("https://www.youtube.com/@asphaltcake"))
        btn_asphalt.pack(fill="x", pady=2)


    def toggle(self):
        self.running = not self.running
        if self.running:
            self.status_lbl.config(text="RUNNING", fg="green")
            self.physics.reset()
            self.last_seen_time = time.time()
            if self.var_aurora.get():
                self.last_aurora_time = 0 
        else:
            self.status_lbl.config(text="STOPPED", fg="red")
            self.overlay.clear()
            self.action.release()

    def set_area_mode(self):
        self.running = False
        self.overlay.clear()
        SnippingTool(self.root, self.update_area)

    def update_area(self, x, y, w, h):
        self.capture_area = {"top": y, "left": x, "width": w, "height": h}
        print(f"[SYSTEM] Capture Area Updated: {self.capture_area}")
        self.save_config()

    def main_loop(self):
        with mss.mss() as sct:
            pydirectinput.PAUSE = 0.0
            
            while self.active_program:
                loop_start = time.time()
                
                if not self.running:
                    time.sleep(0.05)
                    continue

                # 값 갱신
                self.physics.kp = self.var_kp.get()
                self.physics.ki = self.var_ki.get()
                self.physics.kd = self.var_kd.get()
                self.physics.tension = self.var_ten.get()
                self.physics.base_deadzone = self.var_dz.get()
                
                cast_delay = self.var_cast_delay.get()
                target_fps = self.var_fps.get()
                aurora_on = self.var_aurora.get()
                is_dev_mode = self.var_dev.get()

                # Auto Aurora
                if aurora_on and self.game_state == "IDLE":
                    time_since_aurora = time.time() - self.last_aurora_time
                    if time_since_aurora >= AURORA_INTERVAL:
                        self.overlay.set_status("AUTO AURORA...", "magenta")
                        self.action.trigger_aurora()
                        self.last_aurora_time = time.time()
                        self.last_seen_time = time.time() + 1.0 
                        continue

                if aurora_on:
                    next_aurora = max(0, AURORA_INTERVAL - (time.time() - self.last_aurora_time))
                    self.overlay.set_aurora_status(f"Aurora: {int(next_aurora)}s")
                else:
                    self.overlay.set_aurora_status("")

                icon_data, bar_data = self.vision.detect(sct, self.capture_area, DEFAULT_CONFIDENCE)
                current_time = time.time()
                
                if icon_data and bar_data:
                    self.last_seen_time = current_time
                    
                    if self.game_state != "REELING":
                        self.game_state = "REELING"
                        self.physics.reset()

                    icon_cx, icon_rect = icon_data
                    bar_cx, bar_rect = bar_data
                    
                    self.overlay.draw("icon", icon_rect, "red", show=is_dev_mode)
                    self.overlay.draw("bar", bar_rect, "blue", show=is_dev_mode)

                    force = self.physics.compute(icon_cx, bar_cx, self.capture_area["width"])
                    
                    if force > 0:
                        self.action.hold()
                        status_text = f"PULL ({int(force)})"
                        color = "#00FF00"
                    else:
                        self.action.release()
                        status_text = "RELEASE"
                        color = "#FFFF00"
                    
                    self.overlay.set_status(status_text, color)
                
                else:
                    self.overlay.clear()
                    self.action.release()
                    
                    time_diff = current_time - self.last_seen_time
                    
                    if time_diff > cast_delay:
                        self.overlay.set_status("CASTING!", "cyan")
                        self.action.cast_rod()
                        self.last_seen_time = time.time() + 2.0 
                        self.game_state = "IDLE"
                    else:
                        remaining = cast_delay - time_diff
                        if remaining > 0:
                             self.overlay.set_status(f"Wait {remaining:.1f}s...", "gray")

                elapsed = time.time() - loop_start
                target_delay = 1.0 / target_fps
                if elapsed < target_delay:
                    time.sleep(target_delay - elapsed)

class SnippingTool:
    def __init__(self, root, callback):
        self.root = root; self.callback = callback
        self.top = tk.Toplevel(root)
        self.top.attributes("-fullscreen", True, "-alpha", 0.3, "-topmost", True)
        self.top.configure(bg="black")
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.top.bind("<Escape>", lambda e: self.top.destroy())
    def on_press(self, e): self.start_x, self.start_y = e.x, e.y; self.rect = self.canvas.create_rectangle(e.x, e.y, 1, 1, outline='red')
    def on_drag(self, e): self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)
    def on_release(self, e): self.top.destroy(); self.callback(min(self.start_x, e.x), min(self.start_y, e.y), abs(self.start_x - e.x), abs(self.start_y - e.y))

if __name__ == "__main__":
    root = tk.Tk()
    app = FischMacroApp(root)
    root.mainloop()