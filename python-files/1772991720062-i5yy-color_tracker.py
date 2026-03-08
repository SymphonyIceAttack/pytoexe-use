"""
================================================
   Over - نظام تتبع الألوان
   Color Tracker with FOV Circle & GUI
   Requirements: pip install opencv-python pyautogui numpy Pillow
================================================
"""

import tkinter as tk
from tkinter import ttk, colorchooser
import threading
import time
import math
import numpy as np
import pyautogui
import cv2
from PIL import Image, ImageTk
import ctypes
import sys
import os

# ── تجاهل DPI Scaling على Windows ──────────────────
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

pyautogui.FAILSAFE = False  # تعطيل failsafe

# ════════════════════════════════════════════════════
#  الحالة العامة
# ════════════════════════════════════════════════════
class TrackerState:
    def __init__(self):
        self.active        = False
        self.target_color  = (255, 0, 0)   # RGB
        self.tolerance     = 40
        self.fov           = 200
        self.y_offset      = 0
        self.power         = "قوي"
        self.ignore_center = 20
        self.min_pixel     = 10
        self.show_circle   = True
        self.manual_mode   = False
        self.track_mode    = "تلقائي"
        self.locked_target = None          # (x, y, w, h)
        self.lock_count    = 0
        self.scan_count    = 0

state = TrackerState()

# ════════════════════════════════════════════════════
#  نافذة الدائرة (Overlay شفافة)
# ════════════════════════════════════════════════════
class CircleOverlay:
    """نافذة شفافة فوق كل شيء ترسم دائرة FOV وإطار القفل"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("overlay")
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.01)   # شبه شفافة
        self.root.overrideredirect(True)
        self.root.configure(bg="black")

        # جعل النافذة click-through على Windows
        if sys.platform == "win32":
            hwnd = ctypes.windll.user32.FindWindowW(None, "overlay")
            style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, -20, style | 0x80000 | 0x20)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()

        self.canvas = tk.Canvas(
            self.root, width=sw, height=sh,
            bg="black", highlightthickness=0)
        self.canvas.pack()

        self.sw = sw
        self.sh = sh
        self._draw_loop()

    def _draw_loop(self):
        self.canvas.delete("all")

        if state.active and state.show_circle:
            mx, my = pyautogui.position()
            cx, cy = mx, my + state.y_offset
            r = state.fov

            # ── دائرة FOV ──────────────────────────
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="#9945FF", width=2, dash=(6, 4))

            # ── خطوط المنتصف ──────────────────────
            self.canvas.create_line(
                cx - r * 0.6, cy, cx + r * 0.6, cy,
                fill="#9945FF", width=1)
            self.canvas.create_line(
                cx, cy - r * 0.6, cx, cy + r * 0.6,
                fill="#9945FF", width=1)

            # ── نقطة المركز ───────────────────────
            self.canvas.create_oval(
                cx - 4, cy - 4, cx + 4, cy + 4,
                fill="#A855F7", outline="")

            # ── إطار القفل ────────────────────────
            if state.locked_target:
                tx, ty, tw, th = state.locked_target
                pad = 6
                x1, y1 = tx - pad, ty - pad
                x2, y2 = tx + tw + pad, ty + th + pad
                blen = 14

                # الزوايا الأربعة
                corners = [
                    (x1, y1, x1+blen, y1, x1, y1+blen),
                    (x2, y1, x2-blen, y1, x2, y1+blen),
                    (x1, y2, x1+blen, y2, x1, y2-blen),
                    (x2, y2, x2-blen, y2, x2, y2-blen),
                ]
                for ox, oy, hx, hy, vx, vy in corners:
                    self.canvas.create_line(
                        ox, oy, hx, hy, fill="#FF00AA", width=2)
                    self.canvas.create_line(
                        ox, oy, vx, vy, fill="#FF00AA", width=2)

                # خط من المركز للهدف
                tmx = tx + tw // 2
                tmy = ty + th // 2
                self.canvas.create_line(
                    mx, my, tmx, tmy,
                    fill="#FF00AA", width=1, dash=(4, 4))

        self.root.after(16, self._draw_loop)   # ~60fps

    def run(self):
        self.root.mainloop()


# ════════════════════════════════════════════════════
#  منطق التتبع (Thread منفصل)
# ════════════════════════════════════════════════════
def tracking_thread():
    power_speeds = {"قوي": 0.85, "متوسط": 0.5, "خفيف": 0.25}

    while True:
        if not state.active:
            time.sleep(0.05)
            continue

        try:
            mx, my = pyautogui.position()
            fov = state.fov
            y_off = state.y_offset

            # ── التقاط منطقة الـ FOV فقط ──────────
            sx = max(0, mx - fov)
            sy = max(0, my + y_off - fov)
            sw_cap = fov * 2
            sh_cap = fov * 2

            screenshot = pyautogui.screenshot(
                region=(sx, sy, sw_cap, sh_cap))
            img = cv2.cvtColor(
                np.array(screenshot), cv2.COLOR_RGB2BGR)

            # ── بناء فلتر اللون ──────────────────
            tr, tg, tb = state.target_color
            tol = state.tolerance

            lower = np.array([
                max(0,   tb - tol),
                max(0,   tg - tol),
                max(0,   tr - tol)], dtype=np.uint8)
            upper = np.array([
                min(255, tb + tol),
                min(255, tg + tol),
                min(255, tr + tol)], dtype=np.uint8)

            mask = cv2.inRange(img, lower, upper)

            # ── إزالة المنتصف (Ignore Center) ──
            ic = state.ignore_center
            h_img, w_img = mask.shape
            cx_loc = w_img // 2
            cy_loc = h_img // 2
            cv2.circle(mask, (cx_loc, cy_loc), ic, 0, -1)

            # ── إيجاد الكونتورات ─────────────────
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)

            best = None
            best_dist = float("inf")

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area < state.min_pixel * state.min_pixel:
                    continue

                x, y, w, h = cv2.boundingRect(cnt)
                tcx = x + w // 2
                tcy = y + h // 2
                dist = math.hypot(tcx - cx_loc, tcy - cy_loc)

                if dist < fov and dist < best_dist:
                    best_dist = dist
                    best = (x + sx, y + sy, w, h)

            state.locked_target = best
            state.scan_count += 1

            # ── تحريك الفأرة نحو الهدف ──────────
            if best and not state.manual_mode:
                if state.track_mode == "تلقائي":
                    do_move = True
                elif state.track_mode == "زر أيسر":
                    do_move = pyautogui.keyDown.__doc__ is not None  # placeholder
                else:
                    do_move = False

                if do_move:
                    bx, by, bw, bh = best
                    target_x = bx + bw // 2
                    target_y = by + bh // 2
                    speed = power_speeds.get(state.power, 0.5)

                    new_x = int(mx + (target_x - mx) * speed)
                    new_y = int(my + (target_y - my) * speed)

                    pyautogui.moveTo(new_x, new_y, _pause=False)
                    state.lock_count += 1

        except Exception as e:
            pass

        time.sleep(0.008)   # ~120 fps max


# ════════════════════════════════════════════════════
#  واجهة التحكم الرئيسية
# ════════════════════════════════════════════════════
class ControlPanel:
    DARK    = "#0A0A0F"
    DARK2   = "#12121A"
    DARK3   = "#1A1A28"
    DARK4   = "#222235"
    PURPLE  = "#8B5CF6"
    PURPLEB = "#A855F7"
    PINK    = "#FF00AA"
    TEXT    = "#E2E8F0"
    TEXTD   = "#94A3B8"
    GREEN   = "#22C55E"
    RED     = "#EF4444"

    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Over — Aim Assistant")
        self.win.geometry("420x780")
        self.win.resizable(False, False)
        self.win.configure(bg=self.DARK)
        self.win.attributes("-topmost", True)

        self._build_header()
        self._build_body()
        self._build_statusbar()

        self.win.bind("<F2>", lambda e: self._toggle_active())
        self._refresh_ui()

    # ── Header ────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.win, bg=self.DARK2,
                       height=56, relief="flat")
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text="Over", bg=self.DARK2,
                 fg=self.PURPLEB, font=("Consolas", 22, "bold")
                 ).place(x=16, y=8)
        tk.Label(hdr, text="AIM ASSISTANT", bg=self.DARK2,
                 fg=self.TEXTD, font=("Consolas", 8)
                 ).place(x=18, y=36)

        self.status_lbl = tk.Label(
            hdr, text="● غير نشط",
            bg=self.DARK2, fg=self.RED,
            font=("Tajawal", 11, "bold"))
        self.status_lbl.place(x=250, y=18)

        tk.Label(hdr, text="F2", bg=self.DARK3,
                 fg=self.PURPLEB, font=("Consolas", 10, "bold"),
                 relief="flat", padx=8, pady=2
                 ).place(x=370, y=18)

    # ── Body ──────────────────────────────────────
    def _build_body(self):
        scroll_frame = tk.Frame(self.win, bg=self.DARK)
        scroll_frame.pack(fill="both", expand=True, padx=12, pady=8)

        # ── إعدادات التتبع ────────────────────────
        self._section(scroll_frame, "⚙  إعدادات التتبع")

        self._label_row(scroll_frame, "قوة التتبع (Power)")
        self.power_var = tk.StringVar(value="قوي")
        self._styled_combo(scroll_frame, self.power_var,
                           ["قوي", "متوسط", "خفيف"],
                           lambda e: setattr(state, "power",
                                             self.power_var.get()))

        self.fov_var = tk.IntVar(value=200)
        self._slider_row(scroll_frame, "حجم الدائرة (FOV)",
                         self.fov_var, 50, 500,
                         lambda v: setattr(state, "fov", int(v)))

        self.yoff_var = tk.IntVar(value=0)
        self._slider_row(scroll_frame, "مستوى الارتفاع (Y-Offset)",
                         self.yoff_var, -100, 100,
                         lambda v: setattr(state, "y_offset", int(v)))

        self.ignore_var = tk.IntVar(value=20)
        self._slider_row(scroll_frame, "تجاهل المنتصف (Ignore Center)",
                         self.ignore_var, 0, 100,
                         lambda v: setattr(state, "ignore_center", int(v)))

        # ── فلتر الألوان ──────────────────────────
        self._section(scroll_frame, "🎨  فلتر الألوان")

        self.color_preview = tk.Label(
            scroll_frame, bg="#FF0000", width=4,
            relief="flat", cursor="hand2")
        self.color_preview.pack(side="top", anchor="w",
                                padx=4, pady=(0, 4))

        btn_pick = tk.Button(
            scroll_frame,
            text="  اضغط لاختيار لون الهدف  ",
            bg=self.DARK3, fg=self.PINK,
            font=("Tajawal", 11, "bold"),
            relief="flat", cursor="hand2",
            activebackground=self.DARK4,
            activeforeground=self.PINK,
            command=self._pick_color)
        btn_pick.pack(fill="x", padx=4, pady=2)

        self.tol_var = tk.IntVar(value=40)
        self._slider_row(scroll_frame, "حساسية اللون (Tolerance)",
                         self.tol_var, 5, 120,
                         lambda v: setattr(state, "tolerance", int(v)))

        self.minpx_var = tk.IntVar(value=10)
        self._slider_row(scroll_frame, "حجم النقطة (Min Pixel)",
                         self.minpx_var, 1, 60,
                         lambda v: setattr(state, "min_pixel", int(v)))

        # ── وضع التشغيل ───────────────────────────
        self._section(scroll_frame, "🕹  وضع التشغيل")

        self.show_circle_var = tk.BooleanVar(value=True)
        self._toggle_row(scroll_frame, "إظهار الدائرة على الشاشة",
                         self.show_circle_var,
                         lambda: setattr(state, "show_circle",
                                         self.show_circle_var.get()))

        self.manual_var = tk.BooleanVar(value=False)
        self._toggle_row(scroll_frame, "تشغيل باليد فقط (بدون حركة فأرة)",
                         self.manual_var,
                         lambda: setattr(state, "manual_mode",
                                         self.manual_var.get()))

        self._label_row(scroll_frame, "وضع التتبع")
        self.mode_var = tk.StringVar(value="تلقائي")
        self._styled_combo(scroll_frame, self.mode_var,
                           ["تلقائي", "زر أيسر", "يدوي"],
                           lambda e: setattr(state, "track_mode",
                                             self.mode_var.get()))

        # ── زر التفعيل ────────────────────────────
        self.act_btn = tk.Button(
            scroll_frame,
            text="▶  تفعيل النظام  (F2)",
            bg=self.PURPLE, fg="white",
            font=("Tajawal", 14, "bold"),
            relief="flat", cursor="hand2",
            activebackground=self.PURPLEB,
            activeforeground="white",
            command=self._toggle_active)
        self.act_btn.pack(fill="x", padx=4, pady=14)

    # ── Status Bar ────────────────────────────────
    def _build_statusbar(self):
        bar = tk.Frame(self.win, bg=self.DARK2, height=36)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.stat_fov   = self._stat_label(bar, "FOV: 200")
        self.stat_tol   = self._stat_label(bar, "TOL: 40")
        self.stat_lock  = self._stat_label(bar, "LOCK: 0")
        self.stat_scan  = self._stat_label(bar, "SCAN: 0")

    def _stat_label(self, parent, text):
        lbl = tk.Label(parent, text=text, bg=self.DARK2,
                       fg=self.PURPLEB, font=("Consolas", 9, "bold"))
        lbl.pack(side="left", padx=10)
        return lbl

    # ── Helpers ───────────────────────────────────
    def _section(self, parent, title):
        f = tk.Frame(parent, bg=self.DARK3, height=2)
        f.pack(fill="x", pady=(10, 4))
        tk.Label(parent, text=title, bg=self.DARK,
                 fg=self.PURPLEB,
                 font=("Tajawal", 10, "bold")
                 ).pack(anchor="w", padx=4)

    def _label_row(self, parent, text):
        tk.Label(parent, text=text, bg=self.DARK,
                 fg=self.TEXTD, font=("Tajawal", 10)
                 ).pack(anchor="w", padx=6, pady=(6, 0))

    def _styled_combo(self, parent, var, values, cmd):
        cb = ttk.Combobox(parent, textvariable=var,
                          values=values, state="readonly",
                          font=("Tajawal", 11))
        cb.pack(fill="x", padx=4, pady=3)
        cb.bind("<<ComboboxSelected>>", cmd)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox",
                        fieldbackground=self.DARK3,
                        background=self.DARK3,
                        foreground=self.TEXT,
                        selectbackground=self.PURPLE,
                        arrowcolor=self.PURPLEB)

    def _slider_row(self, parent, label, var, mn, mx, cmd):
        row = tk.Frame(parent, bg=self.DARK)
        row.pack(fill="x", padx=4, pady=2)

        tk.Label(row, text=label, bg=self.DARK,
                 fg=self.TEXTD, font=("Tajawal", 10),
                 width=28, anchor="w").pack(side="left")

        val_lbl = tk.Label(row, text=str(var.get()),
                           bg=self.DARK3, fg=self.PURPLEB,
                           font=("Consolas", 10, "bold"),
                           width=5)
        val_lbl.pack(side="right")

        def on_change(v):
            val_lbl.config(text=str(int(float(v))))
            cmd(v)

        sl = tk.Scale(
            parent, variable=var,
            from_=mn, to=mx, orient="horizontal",
            bg=self.DARK, fg=self.PURPLEB,
            troughcolor=self.DARK4,
            activebackground=self.PURPLEB,
            highlightthickness=0, sliderrelief="flat",
            showvalue=False, command=on_change)
        sl.pack(fill="x", padx=4)

    def _toggle_row(self, parent, label, var, cmd):
        row = tk.Frame(parent, bg=self.DARK)
        row.pack(fill="x", padx=4, pady=3)

        tk.Label(row, text=label, bg=self.DARK,
                 fg=self.TEXTD, font=("Tajawal", 10)
                 ).pack(side="right")

        def on_toggle():
            cmd()
            cb.config(
                bg=self.PURPLE if var.get() else self.DARK4)

        cb = tk.Checkbutton(
            row, variable=var, bg=self.DARK,
            activebackground=self.DARK,
            selectcolor=self.PURPLE,
            fg=self.PURPLEB, command=on_toggle,
            relief="flat", cursor="hand2")
        cb.pack(side="left")

    def _pick_color(self):
        r, g, b = state.target_color
        init_hex = "#{:02x}{:02x}{:02x}".format(r, g, b)
        result = colorchooser.askcolor(
            color=init_hex,
            title="اختر لون الهدف")
        if result[0]:
            r2, g2, b2 = [int(x) for x in result[0]]
            state.target_color = (r2, g2, b2)
            hex_c = "#{:02x}{:02x}{:02x}".format(r2, g2, b2)
            self.color_preview.config(bg=hex_c)

    def _toggle_active(self):
        state.active = not state.active
        if state.active:
            self.act_btn.config(
                text="■  إيقاف النظام  (F2)",
                bg=self.RED)
            self.status_lbl.config(
                text="● نشط", fg=self.GREEN)
        else:
            self.act_btn.config(
                text="▶  تفعيل النظام  (F2)",
                bg=self.PURPLE)
            self.status_lbl.config(
                text="● غير نشط", fg=self.RED)
            state.locked_target = None

    # ── تحديث UI كل 100ms ─────────────────────────
    def _refresh_ui(self):
        self.stat_fov.config(
            text=f"FOV: {state.fov}")
        self.stat_tol.config(
            text=f"TOL: {state.tolerance}")
        self.stat_lock.config(
            text=f"LOCK: {state.lock_count}")
        self.stat_scan.config(
            text=f"SCAN: {state.scan_count}")
        self.win.after(100, self._refresh_ui)

    def run(self):
        self.win.mainloop()


# ════════════════════════════════════════════════════
#  تشغيل كل شيء
# ════════════════════════════════════════════════════
if __name__ == "__main__":
    # Thread التتبع
    t = threading.Thread(target=tracking_thread, daemon=True)
    t.start()

    # Overlay الدائرة (Thread منفصل)
    def run_overlay():
        ov = CircleOverlay()
        ov.run()

    ov_thread = threading.Thread(target=run_overlay, daemon=True)
    ov_thread.start()

    # نافذة التحكم (الـ main thread)
    panel = ControlPanel()
    panel.run()
