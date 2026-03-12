"""
⚡ ZENITSU SCREEN RECORDER ⚡
High-performance screen recorder with Zenitsu-themed UI
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import os
import datetime
from pathlib import Path

# Try importing screen capture libraries
try:
    import mss
    import mss.tools
    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ─── ZENITSU COLOR PALETTE ───────────────────────────────────────────────────
COLORS = {
    "bg_dark":      "#0A0A0F",
    "bg_panel":     "#12121A",
    "bg_card":      "#1A1A26",
    "bg_hover":     "#22223A",
    "yellow":       "#FFD700",
    "yellow_bright":"#FFE44D",
    "yellow_dim":   "#B8960A",
    "orange":       "#FF8C00",
    "orange_dim":   "#CC6600",
    "lightning":    "#FFFACD",
    "red":          "#FF3333",
    "red_dim":      "#CC0000",
    "green":        "#00FF88",
    "green_dim":    "#00CC66",
    "text_primary": "#FFFFFF",
    "text_secondary":"#AAAACC",
    "text_dim":     "#666688",
    "border":       "#2A2A40",
    "border_yellow":"#FFD70044",
    "recording":    "#FF3333",
    "paused":       "#FF8C00",
}

# ─── FONTS ────────────────────────────────────────────────────────────────────
FONTS = {
    "title":    ("Impact", 22, "bold"),
    "subtitle": ("Consolas", 10),
    "btn":      ("Consolas", 11, "bold"),
    "btn_sm":   ("Consolas", 9, "bold"),
    "label":    ("Consolas", 9),
    "timer":    ("Consolas", 28, "bold"),
    "status":   ("Consolas", 9),
    "counter":  ("Consolas", 11),
}


class ZenitsuApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("⚡ Zenitsu Screen Recorder")
        self.geometry("520x700")
        self.resizable(False, False)
        self.configure(bg=COLORS["bg_dark"])

        # State
        self.recording = False
        self.paused = False
        self.recording_thread = None
        self.frames = []
        self.start_time = None
        self.pause_time = None
        self.total_paused = 0
        self.timer_running = False
        self.frame_count = 0
        self.screenshot_count = 0

        # Settings
        self.fps_var = tk.IntVar(value=20)
        self.quality_var = tk.StringVar(value="High")
        self.save_dir = str(Path.home() / "Videos" / "Zenitsu")
        self.save_dir_var = tk.StringVar(value=self.save_dir)
        self.audio_var = tk.BooleanVar(value=False)

        # Create save directory
        os.makedirs(self.save_dir, exist_ok=True)
        screenshots_dir = os.path.join(self.save_dir, "Screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)

        # Lightning animation state
        self.lightning_phase = 0
        self.pulse_phase = 0

        self._check_dependencies()
        self._build_ui()
        self._start_animations()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 520) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"520x700+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _check_dependencies(self):
        missing = []
        if not MSS_AVAILABLE:
            missing.append("mss")
        if not CV2_AVAILABLE:
            missing.append("opencv-python")
        if not PIL_AVAILABLE:
            missing.append("Pillow")
        self.deps_ok = len(missing) == 0
        self.missing_deps = missing

    # ─── UI BUILD ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Canvas for lightning background effects
        self.bg_canvas = tk.Canvas(self, width=520, height=700,
                                    bg=COLORS["bg_dark"], highlightthickness=0)
        self.bg_canvas.place(x=0, y=0)

        # Main container
        main = tk.Frame(self, bg=COLORS["bg_dark"])
        main.place(x=0, y=0, width=520, height=700)

        self._build_header(main)
        self._build_timer_section(main)
        self._build_controls(main)
        self._build_settings(main)
        self._build_status_bar(main)

        if not self.deps_ok:
            self._show_install_banner(main)

    def _build_header(self, parent):
        header = tk.Frame(parent, bg=COLORS["bg_dark"], height=110)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        # Lightning bolt icon (drawn with canvas)
        icon_canvas = tk.Canvas(header, width=60, height=80,
                                 bg=COLORS["bg_dark"], highlightthickness=0)
        icon_canvas.place(x=20, y=15)
        self.icon_canvas = icon_canvas
        self._draw_lightning_icon(icon_canvas)

        # Title
        tk.Label(header, text="ZENITSU", font=("Impact", 32, "bold"),
                  fg=COLORS["yellow"], bg=COLORS["bg_dark"]).place(x=90, y=10)

        tk.Label(header, text="SCREEN RECORDER",
                  font=("Consolas", 11, "bold"),
                  fg=COLORS["orange"], bg=COLORS["bg_dark"]).place(x=92, y=52)

        tk.Label(header, text="⚡  Thunder Breathing Recording Form  ⚡",
                  font=("Consolas", 8),
                  fg=COLORS["text_dim"], bg=COLORS["bg_dark"]).place(x=92, y=76)

        # Decorative line
        line = tk.Canvas(parent, height=2, bg=COLORS["bg_dark"],
                          highlightthickness=0)
        line.pack(fill="x", padx=20)
        line.create_line(0, 1, 480, 1, fill=COLORS["yellow"], width=2)
        line.create_line(0, 1, 480, 1, fill=COLORS["yellow_bright"],
                          width=1, dash=(8, 4))

    def _draw_lightning_icon(self, canvas):
        canvas.delete("all")
        # Outer glow
        points_outer = [30, 5, 15, 38, 28, 38, 12, 75, 42, 32, 26, 32]
        canvas.create_polygon(points_outer, fill=COLORS["yellow_dim"],
                               outline="", smooth=False)
        # Main bolt
        points = [30, 8, 17, 40, 29, 40, 14, 72, 43, 33, 27, 33]
        canvas.create_polygon(points, fill=COLORS["yellow"],
                               outline=COLORS["yellow_bright"], width=1)
        # Inner highlight
        points_hi = [28, 12, 20, 36, 30, 36, 22, 55]
        canvas.create_polygon(points_hi, fill=COLORS["lightning"],
                               outline="", smooth=True)
        # Record circle
        canvas.create_oval(36, 56, 52, 72, fill=COLORS["red"],
                            outline=COLORS["yellow"], width=2)
        canvas.create_oval(40, 60, 48, 68, fill="#FF6666", outline="")

    def _build_timer_section(self, parent):
        timer_frame = tk.Frame(parent, bg=COLORS["bg_card"],
                                relief="flat", bd=0)
        timer_frame.pack(fill="x", padx=20, pady=(15, 5))

        # Border effect
        border = tk.Frame(timer_frame, bg=COLORS["yellow_dim"], height=2)
        border.pack(fill="x")

        inner = tk.Frame(timer_frame, bg=COLORS["bg_card"])
        inner.pack(fill="x", padx=2, pady=2)

        # Timer display
        self.timer_label = tk.Label(inner, text="00:00:00",
                                     font=FONTS["timer"],
                                     fg=COLORS["yellow"],
                                     bg=COLORS["bg_card"])
        self.timer_label.pack(pady=(15, 2))

        # Status indicator row
        status_row = tk.Frame(inner, bg=COLORS["bg_card"])
        status_row.pack(pady=(0, 5))

        self.status_dot = tk.Canvas(status_row, width=14, height=14,
                                     bg=COLORS["bg_card"], highlightthickness=0)
        self.status_dot.pack(side="left", padx=5)
        self.status_dot.create_oval(2, 2, 12, 12, fill=COLORS["text_dim"],
                                     outline="", tags="dot")

        self.status_label = tk.Label(status_row, text="READY TO STRIKE",
                                      font=FONTS["status"],
                                      fg=COLORS["text_secondary"],
                                      bg=COLORS["bg_card"])
        self.status_label.pack(side="left")

        # Stats row
        stats_row = tk.Frame(inner, bg=COLORS["bg_card"])
        stats_row.pack(fill="x", padx=15, pady=(5, 12))

        self.frames_label = self._stat_widget(stats_row, "FRAMES", "0")
        self.fps_actual_label = self._stat_widget(stats_row, "FPS", "—")
        self.size_label = self._stat_widget(stats_row, "SIZE", "—")
        self.shots_label = self._stat_widget(stats_row, "SCREENSHOTS", "0")

    def _stat_widget(self, parent, label, value):
        frame = tk.Frame(parent, bg=COLORS["bg_panel"], padx=8, pady=5)
        frame.pack(side="left", expand=True, fill="x", padx=2)
        tk.Label(frame, text=label, font=("Consolas", 7),
                  fg=COLORS["text_dim"], bg=COLORS["bg_panel"]).pack()
        val_label = tk.Label(frame, text=value, font=("Consolas", 10, "bold"),
                              fg=COLORS["yellow"], bg=COLORS["bg_panel"])
        val_label.pack()
        return val_label

    def _build_controls(self, parent):
        ctrl_frame = tk.Frame(parent, bg=COLORS["bg_dark"])
        ctrl_frame.pack(fill="x", padx=20, pady=10)

        # Main record button
        self.record_btn = self._make_button(
            ctrl_frame,
            text="⚡  START RECORDING",
            bg=COLORS["yellow"], fg=COLORS["bg_dark"],
            hover_bg=COLORS["yellow_bright"],
            command=self._toggle_recording,
            height=50, font=("Impact", 16)
        )
        self.record_btn.pack(fill="x", pady=(0, 8))

        # Secondary buttons row
        row2 = tk.Frame(ctrl_frame, bg=COLORS["bg_dark"])
        row2.pack(fill="x")

        self.pause_btn = self._make_button(
            row2,
            text="⏸  PAUSE",
            bg=COLORS["bg_card"], fg=COLORS["orange"],
            hover_bg=COLORS["bg_hover"],
            command=self._toggle_pause,
            height=40, font=FONTS["btn"]
        )
        self.pause_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.screenshot_btn = self._make_button(
            row2,
            text="📸  SCREENSHOT",
            bg=COLORS["bg_card"], fg=COLORS["yellow"],
            hover_bg=COLORS["bg_hover"],
            command=self._take_screenshot,
            height=40, font=FONTS["btn"]
        )
        self.screenshot_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Open folder button
        row3 = tk.Frame(ctrl_frame, bg=COLORS["bg_dark"])
        row3.pack(fill="x", pady=(8, 0))

        self._make_button(
            row3,
            text="📂  OPEN RECORDINGS FOLDER",
            bg=COLORS["bg_panel"], fg=COLORS["text_secondary"],
            hover_bg=COLORS["bg_hover"],
            command=self._open_folder,
            height=32, font=FONTS["btn_sm"]
        ).pack(fill="x")

    def _make_button(self, parent, text, bg, fg, hover_bg, command,
                      height=40, font=None):
        if font is None:
            font = FONTS["btn"]
        btn = tk.Label(parent, text=text, font=font,
                        bg=bg, fg=fg, height=0, cursor="hand2",
                        relief="flat", padx=10, pady=height // 5)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
        btn._bg = bg
        btn._hover = hover_bg
        return btn

    def _build_settings(self, parent):
        # Section header
        hdr = tk.Frame(parent, bg=COLORS["bg_dark"])
        hdr.pack(fill="x", padx=20, pady=(5, 5))
        tk.Label(hdr, text="⚙  SETTINGS",
                  font=("Consolas", 9, "bold"),
                  fg=COLORS["yellow_dim"], bg=COLORS["bg_dark"]).pack(side="left")

        settings = tk.Frame(parent, bg=COLORS["bg_card"])
        settings.pack(fill="x", padx=20)

        tk.Frame(settings, bg=COLORS["yellow_dim"], height=1).pack(fill="x")
        inner = tk.Frame(settings, bg=COLORS["bg_card"], padx=15, pady=10)
        inner.pack(fill="x")

        # FPS Setting
        row = tk.Frame(inner, bg=COLORS["bg_card"])
        row.pack(fill="x", pady=3)
        tk.Label(row, text="Frame Rate:", font=FONTS["label"],
                  fg=COLORS["text_secondary"], bg=COLORS["bg_card"],
                  width=14, anchor="w").pack(side="left")

        for fps_val in [10, 15, 20, 30]:
            rb = tk.Radiobutton(row, text=f"{fps_val}fps",
                                 variable=self.fps_var, value=fps_val,
                                 font=FONTS["label"],
                                 fg=COLORS["yellow"], bg=COLORS["bg_card"],
                                 selectcolor=COLORS["bg_panel"],
                                 activebackground=COLORS["bg_card"],
                                 activeforeground=COLORS["yellow_bright"],
                                 indicatoron=True, bd=0)
            rb.pack(side="left", padx=3)

        # Quality Setting
        row2 = tk.Frame(inner, bg=COLORS["bg_card"])
        row2.pack(fill="x", pady=3)
        tk.Label(row2, text="Quality:", font=FONTS["label"],
                  fg=COLORS["text_secondary"], bg=COLORS["bg_card"],
                  width=14, anchor="w").pack(side="left")

        quality_menu = ttk.Combobox(row2, textvariable=self.quality_var,
                                     values=["Low (Fast)", "Medium", "High", "Ultra"],
                                     font=FONTS["label"], width=12, state="readonly")
        quality_menu.pack(side="left")
        self._style_combobox(quality_menu)

        # Save Directory
        row3 = tk.Frame(inner, bg=COLORS["bg_card"])
        row3.pack(fill="x", pady=3)
        tk.Label(row3, text="Save to:", font=FONTS["label"],
                  fg=COLORS["text_secondary"], bg=COLORS["bg_card"],
                  width=14, anchor="w").pack(side="left")

        dir_entry = tk.Entry(row3, textvariable=self.save_dir_var,
                              font=FONTS["label"], bg=COLORS["bg_panel"],
                              fg=COLORS["text_primary"], insertbackground=COLORS["yellow"],
                              relief="flat", bd=4, width=22)
        dir_entry.pack(side="left", padx=(0, 4))

        browse_btn = tk.Label(row3, text="Browse", font=FONTS["label"],
                               bg=COLORS["yellow_dim"], fg=COLORS["bg_dark"],
                               cursor="hand2", padx=6, pady=2)
        browse_btn.bind("<Button-1>", lambda e: self._browse_dir())
        browse_btn.pack(side="left")

    def _style_combobox(self, cb):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                         fieldbackground=COLORS["bg_panel"],
                         background=COLORS["bg_panel"],
                         foreground=COLORS["yellow"],
                         arrowcolor=COLORS["yellow"],
                         selectbackground=COLORS["bg_hover"],
                         selectforeground=COLORS["yellow"])

    def _build_status_bar(self, parent):
        # Decorative divider
        line = tk.Canvas(parent, height=2, bg=COLORS["bg_dark"],
                          highlightthickness=0)
        line.pack(fill="x", padx=20, pady=(15, 0))
        line.create_line(0, 1, 480, 1, fill=COLORS["border"], width=1)

        status_bar = tk.Frame(parent, bg=COLORS["bg_dark"])
        status_bar.pack(fill="x", padx=20, pady=5)

        self.bottom_status = tk.Label(
            status_bar,
            text="⚡ Zenitsu v1.0  |  Thunder is faster than lightning",
            font=("Consolas", 8),
            fg=COLORS["text_dim"], bg=COLORS["bg_dark"]
        )
        self.bottom_status.pack(side="left")

        # Hotkeys hint
        tk.Label(parent,
                  text="Hotkeys:  F9 = Record   F10 = Screenshot   F11 = Pause",
                  font=("Consolas", 8),
                  fg=COLORS["text_dim"], bg=COLORS["bg_dark"]).pack(pady=(0, 5))

        # Bind hotkeys
        self.bind("<F9>", lambda e: self._toggle_recording())
        self.bind("<F10>", lambda e: self._take_screenshot())
        self.bind("<F11>", lambda e: self._toggle_pause())

    def _show_install_banner(self, parent):
        banner = tk.Frame(parent, bg="#1A0A0A")
        banner.pack(fill="x", padx=20, pady=5)
        tk.Frame(banner, bg=COLORS["red"], height=2).pack(fill="x")
        msg = tk.Frame(banner, bg="#1A0A0A", padx=10, pady=8)
        msg.pack(fill="x")
        tk.Label(msg, text="⚠  Missing dependencies — install to enable recording:",
                  font=("Consolas", 8, "bold"),
                  fg=COLORS["red"], bg="#1A0A0A").pack(anchor="w")
        cmd = "pip install " + " ".join(self.missing_deps)
        tk.Label(msg, text=cmd,
                  font=("Consolas", 9, "bold"),
                  fg=COLORS["yellow"], bg="#1A0A0A").pack(anchor="w", pady=2)
        tk.Label(msg, text="Run the above in cmd/terminal, then restart Zenitsu.",
                  font=("Consolas", 8),
                  fg=COLORS["text_secondary"], bg="#1A0A0A").pack(anchor="w")

    # ─── ANIMATIONS ───────────────────────────────────────────────────────────

    def _start_animations(self):
        self._animate()

    def _animate(self):
        self.lightning_phase = (self.lightning_phase + 1) % 60
        self.pulse_phase = (self.pulse_phase + 1) % 30

        # Pulse the status dot
        if self.recording and not self.paused:
            pulse = abs(self.pulse_phase - 15) / 15
            r = int(255 * (0.5 + 0.5 * pulse))
            g = int(50 * (1 - pulse))
            color = f"#{r:02x}{g:02x}33"
            try:
                self.status_dot.itemconfig("dot", fill=color)
            except:
                pass
        elif self.paused:
            pulse = abs(self.pulse_phase - 15) / 15
            r = int(255 * (0.5 + 0.5 * pulse))
            g = int(140 * (0.5 + 0.5 * pulse))
            color = f"#{r:02x}{g:02x}00"
            try:
                self.status_dot.itemconfig("dot", fill=color)
            except:
                pass

        # Redraw lightning icon occasionally
        if self.lightning_phase % 20 == 0:
            self._draw_lightning_icon(self.icon_canvas)

        # Draw background lightning streaks
        self._draw_bg_effects()

        self.after(50, self._animate)

    def _draw_bg_effects(self):
        c = self.bg_canvas
        c.delete("lightning_bg")
        phase = self.lightning_phase

        # Subtle corner lightning
        if phase % 30 < 3:
            import random
            x, y = 0, 0
            for _ in range(4):
                nx = x + random.randint(10, 30)
                ny = y + random.randint(15, 40)
                c.create_line(x, y, nx, ny,
                               fill=COLORS["yellow_dim"],
                               width=1, tags="lightning_bg")
                x, y = nx, ny

        # Corner decorations
        size = 20
        for cx, cy in [(0, 0), (520, 0), (0, 700), (520, 700)]:
            c.create_rectangle(cx, cy, cx + (size if cx == 0 else -size),
                                cy + (size if cy == 0 else -size),
                                outline=COLORS["yellow_dim"],
                                width=1, tags="lightning_bg")

    # ─── RECORDING LOGIC ──────────────────────────────────────────────────────

    def _toggle_recording(self):
        if not self.deps_ok:
            messagebox.showerror("⚡ Missing Dependencies",
                                  f"Please install: pip install {' '.join(self.missing_deps)}")
            return

        if not self.recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        self.recording = True
        self.paused = False
        self.frames = []
        self.frame_count = 0
        self.start_time = time.time()
        self.total_paused = 0

        # Update UI
        self.record_btn.configure(
            text="⏹  STOP RECORDING",
            bg=COLORS["red"], fg=COLORS["text_primary"]
        )
        self.record_btn._bg = COLORS["red"]
        self.record_btn._hover = COLORS["red_dim"]

        self.status_label.configure(text="● RECORDING...", fg=COLORS["red"])
        self._update_timer()

        # Start capture thread
        self.recording_thread = threading.Thread(target=self._capture_loop,
                                                   daemon=True)
        self.recording_thread.start()
        self.bottom_status.configure(
            text="⚡ Recording in progress — F9 to stop"
        )

    def _stop_recording(self):
        self.recording = False
        self.paused = False

        # Update UI immediately
        self.record_btn.configure(
            text="💾  SAVING...",
            bg=COLORS["yellow_dim"], fg=COLORS["bg_dark"]
        )
        self.status_label.configure(text="SAVING VIDEO...", fg=COLORS["orange"])
        self.update()

        # Save in thread
        threading.Thread(target=self._save_video, daemon=True).start()

    def _toggle_pause(self):
        if not self.recording:
            return
        if not self.paused:
            self.paused = True
            self.pause_time = time.time()
            self.pause_btn.configure(text="▶  RESUME")
            self.status_label.configure(text="⏸ PAUSED", fg=COLORS["orange"])
        else:
            self.paused = False
            if self.pause_time:
                self.total_paused += time.time() - self.pause_time
            self.pause_time = None
            self.pause_btn.configure(text="⏸  PAUSE")
            self.status_label.configure(text="● RECORDING...", fg=COLORS["red"])

    def _capture_loop(self):
        fps = self.fps_var.get()
        interval = 1.0 / fps
        last_fps_check = time.time()
        fps_frame_count = 0

        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor

            while self.recording:
                frame_start = time.time()

                if not self.paused:
                    screenshot = sct.grab(monitor)
                    frame = np.array(screenshot)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    self.frames.append(frame)
                    self.frame_count += 1
                    fps_frame_count += 1

                    # Update FPS display every second
                    now = time.time()
                    if now - last_fps_check >= 1.0:
                        actual_fps = fps_frame_count / (now - last_fps_check)
                        fps_frame_count = 0
                        last_fps_check = now
                        size_mb = (self.frame_count * frame.nbytes) / (1024 * 1024)
                        self.after(0, self._update_stats,
                                    self.frame_count, actual_fps, size_mb)

                elapsed = time.time() - frame_start
                sleep_time = interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def _save_video(self):
        if not self.frames:
            self.after(0, self._reset_ui, "No frames captured.")
            return

        try:
            save_dir = self.save_dir_var.get()
            os.makedirs(save_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Zenitsu_{timestamp}.mp4"
            filepath = os.path.join(save_dir, filename)

            fps = self.fps_var.get()
            quality = self.quality_var.get()

            # Quality settings
            quality_map = {
                "Low (Fast)": (cv2.VideoWriter_fourcc(*"mp4v"), 18),
                "Medium":     (cv2.VideoWriter_fourcc(*"mp4v"), 23),
                "High":       (cv2.VideoWriter_fourcc(*"mp4v"), 28),
                "Ultra":      (cv2.VideoWriter_fourcc(*"mp4v"), 32),
            }
            fourcc, _ = quality_map.get(quality, quality_map["High"])

            h, w = self.frames[0].shape[:2]
            out = cv2.VideoWriter(filepath, fourcc, fps, (w, h))

            for frame in self.frames:
                out.write(frame)
            out.release()

            self.frames = []

            size = os.path.getsize(filepath) / (1024 * 1024)
            msg = f"Saved: {filename} ({size:.1f} MB)"
            self.after(0, self._reset_ui, msg)
            self.after(0, self._show_saved_notification, filepath)

        except Exception as e:
            self.after(0, self._reset_ui, f"Error saving: {str(e)}")

    def _reset_ui(self, status_msg="READY TO STRIKE"):
        self.record_btn.configure(
            text="⚡  START RECORDING",
            bg=COLORS["yellow"], fg=COLORS["bg_dark"]
        )
        self.record_btn._bg = COLORS["yellow"]
        self.record_btn._hover = COLORS["yellow_bright"]
        self.pause_btn.configure(text="⏸  PAUSE")
        self.status_label.configure(text=status_msg,
                                     fg=COLORS["text_secondary"])
        try:
            self.status_dot.itemconfig("dot", fill=COLORS["text_dim"])
        except:
            pass
        self.bottom_status.configure(
            text=f"⚡ Zenitsu v1.0  |  {status_msg}"
        )

    def _show_saved_notification(self, filepath):
        result = messagebox.askquestion(
            "⚡ Recording Saved!",
            f"Video saved successfully!\n\n{os.path.basename(filepath)}\n\nOpen folder?",
            icon="info"
        )
        if result == "yes":
            self._open_folder()

    def _update_stats(self, frames, fps, size_mb):
        self.frames_label.configure(text=str(frames))
        self.fps_actual_label.configure(text=f"{fps:.0f}")
        self.size_label.configure(text=f"{size_mb:.0f}MB")

    def _update_timer(self):
        if not self.recording:
            return
        if self.start_time:
            elapsed = time.time() - self.start_time - self.total_paused
            if self.paused and self.pause_time:
                elapsed -= (time.time() - self.pause_time)
            elapsed = max(0, elapsed)
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            self.timer_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        self.after(1000, self._update_timer)

    # ─── SCREENSHOT ───────────────────────────────────────────────────────────

    def _take_screenshot(self):
        if not self.deps_ok:
            messagebox.showerror("Missing Dependencies",
                                  f"pip install {' '.join(self.missing_deps)}")
            return
        try:
            save_dir = self.save_dir_var.get()
            shots_dir = os.path.join(save_dir, "Screenshots")
            os.makedirs(shots_dir, exist_ok=True)

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
            filename = f"Zenitsu_Screenshot_{timestamp}.png"
            filepath = os.path.join(shots_dir, filename)

            with mss.mss() as sct:
                monitor = sct.monitors[1]
                shot = sct.grab(monitor)
                mss.tools.to_png(shot.rgb, shot.size, output=filepath)

            self.screenshot_count += 1
            self.shots_label.configure(text=str(self.screenshot_count))

            # Flash notification
            self.bottom_status.configure(
                text=f"📸 Screenshot saved: {filename}",
                fg=COLORS["green"]
            )
            self.after(3000, lambda: self.bottom_status.configure(
                text="⚡ Zenitsu v1.0  |  Thunder is faster than lightning",
                fg=COLORS["text_dim"]
            ))

        except Exception as e:
            messagebox.showerror("Screenshot Error", str(e))

    # ─── UTILS ────────────────────────────────────────────────────────────────

    def _browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if d:
            self.save_dir_var.set(d)
            os.makedirs(d, exist_ok=True)
            os.makedirs(os.path.join(d, "Screenshots"), exist_ok=True)

    def _open_folder(self):
        d = self.save_dir_var.get()
        os.makedirs(d, exist_ok=True)
        os.startfile(d) if os.name == "nt" else os.system(f"xdg-open '{d}'")

    def _on_close(self):
        if self.recording:
            if messagebox.askyesno("Stop Recording?",
                                    "Recording is in progress. Stop and exit?"):
                self.recording = False
                self.destroy()
        else:
            self.destroy()


def main():
    app = ZenitsuApp()
    app.mainloop()


if __name__ == "__main__":
    main()
