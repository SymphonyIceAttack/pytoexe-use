import webview
import vgamepad as vg
import time
import threading
import psutil
import mss
import cv2
import numpy as np
import base64
import json
import os
import hashlib
import platform
import requests
from pynput import keyboard
from datetime import datetime

LICENSE_SERVER = "https://web-production-1355a.up.railway.app"
SETTINGS_FILE = "xdrive_settings.json"

def get_hwid():
    raw = platform.node() + platform.machine() + platform.processor()
    return hashlib.md5(raw.encode()).hexdigest()[:16].upper()

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f:
                return json.load(f)
        except: pass
    return {}

def save_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except: pass

class xDriveApi:
    def __init__(self):
        self.pad = vg.VX360Gamepad()
        s = load_settings()
        self.square_enabled      = False
        self.square_timing       = s.get("square_timing", 0.510)
        self.square_fade_timing  = s.get("square_fade_timing", 0.510)
        self.tempo_enabled       = False
        self.tempo_timing        = s.get("tempo_timing", 0.550)
        self.tempo_fade_timing   = s.get("tempo_fade_timing", 0.700)
        self.tempo_is_fade       = False
        self.key_square          = s.get("key_square", "x")
        self.key_tempo           = s.get("key_tempo", "c")
        self.goto_enabled        = False
        self.goto_timing         = s.get("goto_timing", 0.550)
        self.goto_fade_timing    = s.get("goto_fade_timing", 0.700)
        self.key_goto            = s.get("key_goto", "b")
        self.key_fade            = s.get("key_fade", "v")
        self.sync_offset         = s.get("sync_offset", 0)
        self.sync_enabled        = s.get("sync_enabled", False)
        self._goto_lock          = threading.Lock()
        self.chiaki_active       = False
        self.authorized          = False
        self._window             = None
        self._tempo_lock         = threading.Lock()
        self.box_coords          = {"top": 400, "left": 400, "width": 250, "height": 250}
        self._train_enabled      = False
        self._train_shots        = 0
        self._train_greens       = 0
        self.days_remaining      = "?"
        self.lag_comp            = False
        self.lag_switch_on       = False
        self.base_sq_timing      = None
        self.base_tempo_timing   = None
        # Separate tracking per shot type
        self._sq_shots           = 0
        self._sq_greens          = 0
        self._tempo_shots        = 0
        self._tempo_greens       = 0
        self._last_shot_type     = "square"  # track which was last fired
        # Direction memory to avoid bouncing
        self._sq_last_dir        = None
        self._tempo_last_dir     = None

    def set_window(self, window):
        self._window = window

    def send_log(self, message):
        if self._window:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self._window.evaluate_js(f"addLog('[{timestamp}] {message}')")

    def _precise_sleep(self, duration):
        if duration <= 0: return
        coarse = duration - 0.002
        if coarse > 0: time.sleep(coarse)
        target = time.perf_counter() + 0.002
        while time.perf_counter() < target: pass

    def execute_square_shot(self):
        if not self.square_enabled or not self.authorized: return
        active_timing = self.square_fade_timing if self.tempo_is_fade else self.square_timing
        mode = "FADE" if self.tempo_is_fade else "NORMAL"
        self._last_shot_type = "sq_fade" if self.tempo_is_fade else "square"
        self.send_log(f"SQUARE {mode} Triggered (Timing: {active_timing}s)")
        self.pad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        self.pad.update(); self.pad.update()
        self._precise_sleep(active_timing)
        self.pad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        self.pad.update(); self.pad.update()

    def execute_tempo_shot(self):
        if not self.tempo_enabled or not self.authorized: return
        if not self._tempo_lock.acquire(blocking=False): return
        try:
            active_timing = self.tempo_fade_timing if self.tempo_is_fade else self.tempo_timing
            mode_label = "FADE" if self.tempo_is_fade else "STAND"
            self._last_shot_type = "tempo_fade" if self.tempo_is_fade else "tempo"
            self.send_log(f"TEMPO {mode_label} Triggered (Timing: {active_timing}s)")
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=-1.0)
            self.pad.update()
            time.sleep(0.05)
            time.sleep(active_timing)
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=1.0)
            self.pad.update()
            time.sleep(0.1)
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
            self.pad.update()
        finally:
            self._tempo_lock.release()

    def execute_tempo_shot(self):
        if not self.tempo_enabled or not self.authorized: return
        if not self._tempo_lock.acquire(blocking=False): return
        try:
            active_timing = self.tempo_fade_timing if self.tempo_is_fade else self.tempo_timing
            if self.sync_enabled:
                active_timing = max(0.1, active_timing + (self.sync_offset / 1000.0))
            mode_label = "FADE" if self.tempo_is_fade else "STAND"
            self._last_shot_type = "tempo_fade" if self.tempo_is_fade else "tempo"
            self.send_log(f"TEMPO {mode_label} Triggered (Timing: {active_timing:.3f}s)")
            # Push stick down
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=-1.0)
            self.pad.update()
            # Pulse updates every 16ms during window to keep signal strong
            elapsed = 0.0
            interval = 0.016
            while elapsed < active_timing:
                chunk = min(interval, active_timing - elapsed)
                time.sleep(chunk)
                self.pad.right_joystick_float(x_value_float=0.0, y_value_float=-1.0)
                self.pad.update()
                elapsed += chunk
            # Flick up to release
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=1.0)
            self.pad.update()
            time.sleep(0.1)
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
            self.pad.update()
        finally:
            self._tempo_lock.release()

    def execute_goto_shot(self):
        if not self.authorized: return
        self.send_log(f"GO TO Triggered (Timing: {self.goto_timing:.3f}s)")
        self.pad.right_joystick_float(x_value_float=0.0, y_value_float=1.0)
        self.pad.update()
        elapsed = 0.0
        interval = 0.016
        while elapsed < self.goto_timing:
            chunk = min(interval, self.goto_timing - elapsed)
            time.sleep(chunk)
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=1.0)
            self.pad.update()
            elapsed += chunk
        self.pad.right_joystick_float(x_value_float=0.0, y_value_float=-1.0)
        self.pad.update()
        time.sleep(0.1)
        self.pad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
        self.pad.update()

    def _build_save(self):
        return {
            "square_timing":      self.square_timing,
            "square_fade_timing": self.square_fade_timing,
            "tempo_timing":       self.tempo_timing,
            "tempo_fade_timing":  self.tempo_fade_timing,
            "key_square":         self.key_square,
            "key_tempo":          self.key_tempo,
            "goto_timing":        self.goto_timing,
            "goto_fade_timing":   self.goto_fade_timing,
            "key_goto":           self.key_goto,
            "key_fade":           self.key_fade,
            "sync_offset":        self.sync_offset,
            "sync_enabled":       self.sync_enabled,
        }

    def toggle_fade_hotkey(self):
        pass  # no longer used

    def execute_fade_shot(self):
        if not self.tempo_enabled or not self.authorized: return
        if not self._tempo_lock.acquire(blocking=False): return
        try:
            active_timing = self.tempo_fade_timing
            if self.sync_enabled:
                active_timing = max(0.1, active_timing + (self.sync_offset / 1000.0))
            self.send_log(f"TEMPO FADE Triggered (Timing: {active_timing:.3f}s)")
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=-1.0)
            self.pad.update()
            time.sleep(0.05)
            time.sleep(active_timing)
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=1.0)
            self.pad.update()
            time.sleep(0.1)
            self.pad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
            self.pad.update()
        finally:
            self._tempo_lock.release()

    def sync_settings(self, sq_on, sq_val, sq_fade_val, tempo_on, tempo_val, fade_val, is_fade=False):
        self.square_enabled     = sq_on
        self.square_timing      = float(sq_val)
        self.square_fade_timing = float(sq_fade_val)
        self.tempo_enabled      = tempo_on
        self.tempo_timing       = float(tempo_val)
        self.tempo_fade_timing  = float(fade_val)
        if isinstance(is_fade, str):
            self.tempo_is_fade = is_fade.lower() == 'true'
        else:
            self.tempo_is_fade = bool(is_fade)
        save_settings(self._build_save())
        return "SYNCED"

    def sync_goto(self, goto_on, goto_val, goto_fade_val=None):
        if isinstance(goto_on, str):
            self.goto_enabled = goto_on.lower() == 'true'
        else:
            self.goto_enabled = bool(goto_on)
        self.goto_timing = float(goto_val)
        if goto_fade_val is not None:
            self.goto_fade_timing = float(goto_fade_val)
        self.send_log(f"[GOTO] {'Enabled' if self.goto_enabled else 'Disabled'} — Timing: {self.goto_timing}s")
        save_settings(self._build_save())
        return "SYNCED"

    def set_goto_timing(self, goto_val):
        self.goto_timing = float(goto_val)
        save_settings(self._build_save())
        return "SYNCED"

    def set_sync_offset(self, offset_ms):
        self.sync_offset = int(offset_ms)
        save_settings(self._build_save())
        return "SYNCED"

    def set_sync_enabled(self, enabled):
        self.sync_enabled = bool(enabled)
        save_settings(self._build_save())
        return "SYNCED"

    def set_keybinds(self, key_sq, key_tempo, key_goto="b"):
        self.key_square = key_sq.lower().strip()
        self.key_tempo  = key_tempo.lower().strip()
        self.key_goto   = key_goto.lower().strip()
        save_settings(self._build_save())
        return "KEYS_SAVED"

    def get_settings(self):
        return self._build_save()

    def get_training_state(self):
        return {
            "shots":   self._train_shots,
            "greens":  self._train_greens,
            "enabled": self._train_enabled,
        }

    def training_toggle(self, enabled):
        self._train_enabled = bool(enabled)
        return self._train_enabled

    def training_mark(self, was_green):
        if not self._train_enabled:
            return {"status": "disabled"}

        self._train_shots += 1
        if was_green:
            self._train_greens += 1

        # Track per shot type based on last fired
        t = self._last_shot_type
        if t == "square":
            self._sq_shots += 1
            if was_green: self._sq_greens += 1
        elif t == "sq_fade":
            self._sq_shots += 1
            if was_green: self._sq_greens += 1
        elif t == "tempo":
            self._tempo_shots += 1
            if was_green: self._tempo_greens += 1
        elif t == "tempo_fade":
            self._tempo_shots += 1
            if was_green: self._tempo_greens += 1

        msg = "GREEN" if was_green else "MISS"
        self.send_log(f"[TRAIN] Shot {self._train_shots}/15: {msg} ({t})")

        if self._train_shots >= 15:
            self._auto_tune()
            self._train_shots  = 0
            self._train_greens = 0
            self._sq_shots     = 0
            self._sq_greens    = 0
            self._tempo_shots  = 0
            self._tempo_greens = 0
            return {"status": "tuned", "sq": self.square_timing, "sqFade": self.square_fade_timing,
                    "tempo": self.tempo_timing, "fade": self.tempo_fade_timing}

        return {"status": "recorded", "shots": self._train_shots, "greens": self._train_greens}

    def _auto_tune(self):
        def tune_val(current, greens, shots, mn, mx, last_dir_key):
            if shots == 0:
                return current, getattr(self, last_dir_key)
            rate = greens / shots
            # Dynamic step — bigger when far off, smaller when close
            if rate < 0.3:
                step = 0.015
            elif rate < 0.5:
                step = 0.008
            elif rate < 0.65:
                step = 0.004
            elif rate > 0.9:
                step = 0.003
            elif rate > 0.8:
                step = 0.005
            else:
                # 65-80% is the sweet spot — don't touch
                return current, getattr(self, last_dir_key)

            last_dir = getattr(self, last_dir_key)

            if rate < 0.65:
                # Too many misses — increase timing
                # But if last time we increased and still missing, try decrease instead
                if last_dir == "increased":
                    new_val = round(max(mn, current - step), 3)
                    new_dir = "decreased"
                else:
                    new_val = round(min(mx, current + step), 3)
                    new_dir = "increased"
            else:
                # Good rate — nudge down slightly to tighten
                new_val = round(max(mn, current - step), 3)
                new_dir = "decreased"

            setattr(self, last_dir_key, new_dir)
            return new_val, new_dir

        sq_rate    = self._sq_greens / max(self._sq_shots, 1)
        tempo_rate = self._tempo_greens / max(self._tempo_shots, 1)

        self.square_timing,      _ = tune_val(self.square_timing,      self._sq_greens,    self._sq_shots,    0.450, 0.600, "_sq_last_dir")
        self.square_fade_timing, _ = tune_val(self.square_fade_timing, self._sq_greens,    self._sq_shots,    0.400, 0.700, "_sq_last_dir")
        self.tempo_timing,       _ = tune_val(self.tempo_timing,       self._tempo_greens, self._tempo_shots, 0.400, 0.750, "_tempo_last_dir")
        self.tempo_fade_timing,  _ = tune_val(self.tempo_fade_timing,  self._tempo_greens, self._tempo_shots, 0.300, 0.950, "_tempo_last_dir")

        save_settings(self._build_save())
        self.send_log(f"[TRAIN] Auto-tune done — Square {sq_rate*100:.0f}% | Tempo {tempo_rate*100:.0f}%")
        self.send_log(f"[TRAIN] New values → SQ:{self.square_timing} | TEMPO:{self.tempo_timing}")
        if self._window:
            self._window.evaluate_js(
                f"onTrainTuned({self.square_timing},{self.square_fade_timing},{self.tempo_timing},{self.tempo_fade_timing})"
            )

    def training_reset(self):
        self._train_shots  = 0
        self._train_greens = 0
        return "RESET"

    def get_network_stats(self):
        import subprocess, re
        ping = None
        wifi = None
        try:
            result = subprocess.run(["ping", "-n", "1", "-w", "1000", "8.8.8.8"],
                capture_output=True, text=True, timeout=3)
            match = re.search(r"Average = (\d+)ms", result.stdout)
            if match: ping = int(match.group(1))
        except: pass
        try:
            result = subprocess.run(["netsh", "wlan", "show", "interfaces"],
                capture_output=True, text=True, timeout=3)
            match = re.search(r"Signal\s*:\s*(\d+)%", result.stdout)
            if match: wifi = int(match.group(1))
        except: pass
        adj = 0
        if self.lag_comp and ping is not None:
            base_ping = 20
            extra = max(0, ping - base_ping)
            adj = round(extra * 0.0003, 3)
            self.square_timing      = round((self.base_sq_timing    or self.square_timing)    - adj, 3)
            self.square_fade_timing = round((self.base_sq_timing    or self.square_fade_timing) - adj, 3)
            self.tempo_timing       = round((self.base_tempo_timing  or self.tempo_timing)     - adj, 3)
            self.tempo_fade_timing  = round((self.base_tempo_timing  or self.tempo_fade_timing) - adj, 3)
        return {"ping": ping, "wifi": wifi, "adj": adj}

    def toggle_lag_switch(self, enabled):
        import ctypes, signal
        self.lag_switch_on = bool(enabled)
        def do_lag():
            while self.lag_switch_on:
                try:
                    # Find Chiaki process and suspend/resume it rapidly to create lag effect
                    for proc in psutil.process_iter(['name', 'pid']):
                        if proc.info['name'] and 'chiaki' in proc.info['name'].lower():
                            handle = ctypes.windll.kernel32.OpenProcess(0x1F0FFF, False, proc.info['pid'])
                            if handle:
                                ctypes.windll.kernel32.SuspendThread(handle)
                                time.sleep(0.3)
                                ctypes.windll.kernel32.ResumeThread(handle)
                                ctypes.windll.kernel32.CloseHandle(handle)
                except: pass
                time.sleep(0.2)
        if enabled:
            threading.Thread(target=do_lag, daemon=True).start()
        return "OK"

    def toggle_lag_comp(self, enabled):
        self.lag_comp = bool(enabled)
        if self.lag_comp:
            self.base_sq_timing    = self.square_timing
            self.base_tempo_timing = self.tempo_timing
        else:
            if self.base_sq_timing:
                self.square_timing      = self.base_sq_timing
                self.square_fade_timing = self.base_sq_timing
                self.tempo_timing       = self.base_tempo_timing
                self.tempo_fade_timing  = self.base_tempo_timing
        return "OK"

    def check_access(self, key):
        try:
            hwid = get_hwid()
            r = requests.post(
                f"{LICENSE_SERVER}/validate",
                json={"license_key": key.strip().upper(), "hwid": hwid},
                timeout=10
            )
            data = r.json()
            if data.get("ok"):
                self.authorized = True
                k = key.strip().upper()
                if k.startswith("XD-L-"):
                    days = "Lifetime"
                elif k.startswith("XD-M-"):
                    days = "30"
                elif k.startswith("XD-W-"):
                    days = "7"
                else:
                    days = data.get("days_remaining") or data.get("days") or "?"
                self.days_remaining = days
                return {"ok": True, "days": days}
            else:
                return {"ok": False, "message": data.get("message", "Invalid key")}
        except Exception as e:
            return {"ok": False, "message": "Could not reach license server"}

    def start_threads(self):
        def hotkey_listener():
            import win32api
            def get_vk(char): return ord(char.upper())
            prev_sq = False; prev_tempo = False; prev_goto = False; prev_fade = False
            while True:
                try:
                    sq_down    = bool(win32api.GetAsyncKeyState(get_vk(self.key_square)) & 0x8000)
                    tempo_down = bool(win32api.GetAsyncKeyState(get_vk(self.key_tempo))  & 0x8000)
                    goto_down  = bool(win32api.GetAsyncKeyState(get_vk(self.key_goto))   & 0x8000)
                    fade_down  = bool(win32api.GetAsyncKeyState(get_vk(self.key_fade))   & 0x8000)
                    if goto_down and not prev_goto:
                        self.send_log(f"[DEBUG] B pressed key_goto={self.key_goto}")
                    if self.authorized:
                        if sq_down    and not prev_sq:    threading.Thread(target=self.execute_square_shot, daemon=True).start()
                        if tempo_down and not prev_tempo: threading.Thread(target=self.execute_tempo_shot,  daemon=True).start()
                        if goto_down  and not prev_goto:  threading.Thread(target=self.execute_goto_shot,   daemon=True).start()
                        if fade_down  and not prev_fade:  threading.Thread(target=self.execute_fade_shot,   daemon=True).start()
                    prev_sq = sq_down; prev_tempo = tempo_down; prev_goto = goto_down; prev_fade = fade_down
                except: pass
                time.sleep(0.005)

        def process_watcher():
            while True:
                is_running = any("chiaki" in p.info['name'].lower() for p in psutil.process_iter(['name']) if p.info['name'])
                if is_running != self.chiaki_active:
                    self.chiaki_active = is_running
                    if self._window: self._window.evaluate_js(f"updateChiakiStatus({str(is_running).lower()})")
                time.sleep(2)

        def screen_stream():
            sensitivity = 40
            lower_white = np.array([0, 0, 255 - sensitivity])
            upper_white = np.array([180, sensitivity, 255])
            with mss.mss() as sct:
                while True:
                    if self.chiaki_active and self._window:
                        img = np.array(sct.grab(self.box_coords))
                        frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                        mask = cv2.inRange(hsv, lower_white, upper_white)
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        border_color = (0, 0, 255)
                        if contours and max([cv2.contourArea(c) for c in contours]) > 50:
                            border_color = (0, 255, 0)
                        cv2.rectangle(frame, (0,0), (self.box_coords["width"]-2, self.box_coords["height"]-2), border_color, 2)
                        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                        jpg_text = base64.b64encode(buffer).decode('utf-8')
                        self._window.evaluate_js(f"updatePreview('{jpg_text}')")
                    time.sleep(0.03)

        threading.Thread(target=hotkey_listener, daemon=True).start()
        threading.Thread(target=process_watcher, daemon=True).start()
        threading.Thread(target=screen_stream, daemon=True).start()

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <style>
        :root { --cyan: #e60026; --red: #ff4444; --bg: #000; --surf: #0a0005; --border: rgba(230,0,38,0.18); --dim: #6d5c5c; --yellow: #f5c518; }
        * { box-sizing: border-box; font-family: 'Segoe UI', sans-serif; color: #fff; margin: 0; padding: 0; }
        body { background: var(--bg); display: flex; height: 100vh; overflow: hidden; }

        /* SIDEBAR */
        .sidebar { width: 190px; background: #06000a; border-right: 1px solid var(--border); padding: 18px 14px; display: flex; flex-direction: column; flex-shrink: 0; }
        .logo { font-size: 22px; font-weight: 900; color: var(--cyan); margin-bottom: 6px; font-style: italic; letter-spacing: 1px; }
        .logo-sub { font-size: 9px; color: var(--dim); margin-bottom: 20px; letter-spacing: 2px; text-transform: uppercase; }
        .tab { padding: 10px 12px; border-radius: 8px; color: var(--dim); cursor: pointer; margin-bottom: 3px; font-weight: 700; font-size: 12px; transition: 0.15s; display: flex; align-items: center; gap: 8px; }
        .tab .ti { font-size: 14px; }
        .tab.active { background: rgba(230,0,38,0.12); color: var(--cyan); border: 1px solid var(--border); }
        .tab:hover:not(.active) { color: #fff; background: rgba(255,255,255,0.03); }
        .sidebar-bottom { margin-top: auto; font-size: 9px; color: #2a1a1a; text-align: center; }

        /* MAIN */
        .main { flex: 1; padding: 20px 22px; overflow-y: auto; }
        .view { display: none; } .view.active { display: block; }

        /* CARDS */
        .card { background: #08000d; border: 1px solid var(--border); padding: 14px 16px; border-radius: 10px; margin-bottom: 14px; }
        .card-glow { box-shadow: 0 0 20px rgba(230,0,38,0.06); }

        /* HEADERS */
        .section-header { color: var(--cyan); font-size: 10px; font-weight: 800; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 2px; display: flex; align-items: center; gap: 6px; }
        .section-header::after { content: ''; flex: 1; height: 1px; background: var(--border); }

        /* SWITCH */
        .switch { width: 36px; height: 18px; background: #1a0010; border-radius: 20px; position: relative; cursor: pointer; border: 1px solid var(--border); flex-shrink: 0; transition: 0.2s; }
        .switch.on { background: var(--cyan); border-color: transparent; }
        .switch::after { content: ''; position: absolute; top: 2px; left: 2px; width: 12px; height: 12px; background: #fff; border-radius: 50%; transition: 0.2s; }
        .switch.on::after { left: 20px; }

        /* SLIDERS */
        input[type=range] { width: 100%; accent-color: var(--cyan); margin: 5px 0 2px; cursor: pointer; }

        /* LOGS */
        .log-container { background: #030008; border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; font-family: 'Courier New', monospace; font-size: 10px; overflow-y: auto; height: 140px; color: var(--dim); }
        .log-entry { margin-bottom: 3px; border-left: 2px solid var(--cyan); padding-left: 7px; line-height: 1.5; }

        /* MISC */
        .key-bind { background: rgba(230,0,38,0.1); padding: 1px 6px; border-radius: 4px; color: var(--cyan); font-size: 10px; border: 1px solid var(--border); }
        .key-input { background: #08000d; border: 1px solid var(--border); border-radius: 6px; color: var(--cyan); font-size: 13px; font-weight: 700; width: 40px; text-align: center; padding: 5px; outline: none; text-transform: uppercase; }
        .key-input:focus { border-color: var(--cyan); }
        .save-btn { background: var(--cyan); border: none; border-radius: 6px; color: #000; font-weight: 800; font-size: 11px; padding: 7px 14px; cursor: pointer; margin-top: 10px; transition: 0.15s; }
        .save-btn:hover { opacity: 0.85; }
        .save-btn.ghost { background: transparent; color: var(--cyan); border: 1px solid var(--border); }
        .saved-tag { font-size: 10px; color: #00ff88; margin-left: 8px; display: none; }
        .row { display: flex; justify-content: space-between; align-items: center; }
        .slider-label { font-size: 11px; color: var(--dim); }
        .slider-val { font-size: 11px; color: var(--cyan); font-weight: 700; }
        .divider { height: 1px; background: var(--border); margin: 12px 0; }
        .badge { display: inline-block; font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 10px; text-transform: uppercase; letter-spacing: 1px; }
        .badge-green { background: rgba(0,255,100,0.1); color: #00ff88; border: 1px solid rgba(0,255,100,0.2); }
        .badge-red { background: rgba(255,0,60,0.1); color: #ff4444; border: 1px solid rgba(255,0,60,0.2); }

        /* SESSION STATS BAR */
        .stats-bar { display: flex; gap: 10px; margin-bottom: 16px; }
        .stat-box { flex: 1; background: #08000d; border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; text-align: center; }
        .stat-box-num { font-size: 22px; font-weight: 900; color: var(--cyan); line-height: 1; }
        .stat-box-num.green { color: #00ff88; }
        .stat-box-label { font-size: 9px; color: var(--dim); text-transform: uppercase; letter-spacing: 1px; margin-top: 3px; }

        /* STATUS INDICATOR */
        .status-indicator { display: flex; align-items: center; gap: 7px; padding: 6px 12px; background: #08000d; border: 1px solid var(--border); border-radius: 20px; margin-bottom: 14px; width: fit-content; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--dim); flex-shrink: 0; transition: all 0.3s; }
        .status-dot.active { background: #00ff88; box-shadow: 0 0 8px rgba(0,255,136,0.6); animation: pulse 1.5s infinite; }
        .status-dot.fade-active { background: var(--cyan); box-shadow: 0 0 8px rgba(230,0,38,0.6); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .status-text { font-size: 11px; font-weight: 700; color: var(--dim); }
        .status-text.active { color: #00ff88; }
        .status-text.fade-active { color: var(--cyan); }

        /* FINE TUNE BUTTONS */
        .fine-tune-row { display: flex; align-items: center; gap: 6px; margin-top: 4px; }
        .ft-btn { background: #08000d; border: 1px solid var(--border); border-radius: 5px; color: var(--cyan); font-size: 13px; font-weight: 900; width: 26px; height: 26px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.15s; flex-shrink: 0; }
        .ft-btn:hover { background: rgba(230,0,38,0.12); border-color: var(--cyan); }
        .ft-label { font-size: 10px; color: var(--dim); flex: 1; }
        .ping-circle-wrap { display: flex; justify-content: center; margin: 16px 0; }
        .ping-circle { width: 110px; height: 110px; border-radius: 50%; background: #08000d; border: 3px solid var(--border); display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; transition: border-color 0.3s; }
        .ping-circle.good { border-color: #00ff88; box-shadow: 0 0 18px rgba(0,255,136,0.15); }
        .ping-circle.ok   { border-color: #f5c518; box-shadow: 0 0 18px rgba(245,197,24,0.15); }
        .ping-circle.bad  { border-color: #ff4444; box-shadow: 0 0 18px rgba(255,68,68,0.2); }
        .ping-circle.crazy { border-color: #ff4444; animation: pingPulse 0.3s infinite alternate; }
        @keyframes pingPulse { from { box-shadow: 0 0 10px rgba(255,68,68,0.2); } to { box-shadow: 0 0 30px rgba(255,68,68,0.6); border-color: #ff0000; } }
        .ping-num { font-size: 26px; font-weight: 900; line-height: 1; }
        .ping-label { font-size: 9px; color: var(--dim); letter-spacing: 2px; margin-top: 2px; }
        .ping-status { font-size: 8px; font-weight: 700; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }

        /* WIFI BARS */
        .wifi-bars { display: flex; gap: 3px; align-items: flex-end; height: 20px; }
        .wifi-bar { width: 8px; border-radius: 2px; background: #1a0010; transition: 0.3s; }
        .wifi-bar:nth-child(1) { height: 4px; }
        .wifi-bar:nth-child(2) { height: 8px; }
        .wifi-bar:nth-child(3) { height: 12px; }
        .wifi-bar:nth-child(4) { height: 16px; }
        .wifi-bar:nth-child(5) { height: 20px; }

        /* LAG SWITCH WARNING */
        .lag-warning { background: rgba(245,197,24,0.06); border: 1px solid rgba(245,197,24,0.3); border-radius: 8px; padding: 10px 12px; margin-top: 10px; display: flex; gap: 8px; align-items: flex-start; }
        .lag-warning-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
        .lag-warning-text { font-size: 10px; color: var(--yellow); line-height: 1.5; }

        /* JUMPERS */
        .jumper-row { display: flex; align-items: center; gap: 10px; padding: 10px 0; flex-wrap: wrap; }
        .jumper-title { font-size: 13px; font-weight: 700; flex: 1; min-width: 140px; }
        .jumper-tags { display: flex; gap: 5px; flex-wrap: wrap; }
        .jtag { background: rgba(0,242,255,0.08); border: 1px solid var(--border); border-radius: 4px; padding: 2px 7px; font-size: 10px; color: var(--cyan); font-weight: 700; }
        .jumper-btn { background: var(--cyan); border: none; border-radius: 6px; color: #000; font-size: 11px; font-weight: 800; padding: 6px 12px; cursor: pointer; white-space: nowrap; flex-shrink: 0; }
        .jumper-btn:hover { opacity: 0.85; }
        .jumper-divider { height: 1px; background: var(--border); }

        /* AUTH */
        #authScreen { position: fixed; inset: 0; background: var(--bg); z-index: 100; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        #authScreen .logo { font-size: 32px; margin-bottom: 4px; }
        #authScreen .sub { font-size: 10px; color: var(--dim); letter-spacing: 3px; margin-bottom: 28px; }
        #authKey { background: #08000d; border: 1px solid var(--border); padding: 12px 16px; border-radius: 8px; width: 280px; text-align: center; outline: none; font-size: 14px; color: #fff; }
        #authKey:focus { border-color: var(--cyan); }
        #authBtn { background: var(--cyan); border: none; padding: 11px 36px; border-radius: 8px; font-weight: 900; cursor: pointer; color: #000; font-size: 13px; margin-top: 10px; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div id="authScreen">
        <div class="logo">xDrive !</div>
        <div class="sub">PLAYSTATION EDITION</div>
        <input type="text" id="authKey" placeholder="ACCESS KEY" />
        <button id="authBtn" onclick="login()">AUTHORIZE</button>
    </div>

    <div class="sidebar">
        <div class="logo">xDrive !</div>
        <div class="logo-sub">PS Edition</div>
        <div id="daysBadge" style="display:none; background:rgba(230,0,38,0.08); border:1px solid var(--border); border-radius:8px; padding:5px 10px; margin-bottom:14px; font-size:10px; color:var(--dim); text-align:center;"></div>
        <div class="tab active" onclick="showView('shootView', this)"><span class="ti">⚡</span> Shooting</div>
        <div class="tab" onclick="showView('timingView', this)"><span class="ti">⏱</span> Timing</div>
        <div class="tab" onclick="showView('networkView', this)"><span class="ti">📡</span> Network</div>
        <div class="tab" onclick="showView('connView', this)"><span class="ti">🎮</span> Capture</div>
        <div class="tab" onclick="showView('trainView', this)"><span class="ti">🎯</span> Training</div>
        <div class="tab" onclick="showView('jumpersView', this)"><span class="ti">🏀</span> Jumpers</div>
        <div class="sidebar-bottom">xDrive v3.0</div>
    </div>

    <div class="main">

        <!-- SHOOTING TAB -->
        <div id="shootView" class="view active">

            <!-- SESSION STATS BAR -->
            <div class="stats-bar">
                <div class="stat-box">
                    <div class="stat-box-num green" id="stat-greens">0</div>
                    <div class="stat-box-label">Greens</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-num" id="stat-shots">0</div>
                    <div class="stat-box-label">Shots</div>
                </div>
                <div class="stat-box">
                    <div class="stat-box-num" id="stat-pct">--%</div>
                    <div class="stat-box-label">Green %</div>
                </div>
            </div>

            <div class="section-header">Square <span class="key-bind" id="sqKeyLabel">X</span></div>
            <div class="card card-glow">
                <!-- Status indicator -->
                <div class="status-indicator" id="sqStatusBar">
                    <div class="status-dot" id="sqStatusDot"></div>
                    <span class="status-text" id="sqStatusText">INACTIVE</span>
                </div>
                <div class="row" style="margin-bottom:12px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Auto Green</div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Press key to trigger shot</div>
                    </div>
                    <div id="sqToggle" class="switch" onclick="toggleSq()"></div>
                </div>
                <div class="row" style="margin-bottom:4px;"><span class="slider-label">Normal Shot</span><span class="slider-val" id="sqVal">0.510s</span></div>
                <input type="range" min="0.450" max="0.600" step="0.001" value="0.510" id="sqSld" oninput="sync()">
                <div class="fine-tune-row">
                    <button class="ft-btn" onclick="nudge('sqSld','sqVal',-0.001)">−</button>
                    <span class="ft-label">Fine tune ±0.001s</span>
                    <button class="ft-btn" onclick="nudge('sqSld','sqVal',0.001)">+</button>
                </div>
                <div class="row" style="margin-top:12px; margin-bottom:4px;"><span class="slider-label">Fading Shot</span><span class="slider-val" id="sqFadeVal">0.510s</span></div>
                <input type="range" min="0.400" max="0.700" step="0.001" value="0.510" id="sqFadeSld" oninput="sync()">
                <div class="fine-tune-row">
                    <button class="ft-btn" onclick="nudge('sqFadeSld','sqFadeVal',-0.001)">−</button>
                    <span class="ft-label">Fine tune ±0.001s</span>
                    <button class="ft-btn" onclick="nudge('sqFadeSld','sqFadeVal',0.001)">+</button>
                </div>
            </div>

            <div class="section-header">Tempo</div>
            <div class="card">
                <!-- Status indicator -->
                <div class="status-indicator" id="tempoStatusBar">
                    <div class="status-dot" id="tempoStatusDot"></div>
                    <span class="status-text" id="tempoStatusText">INACTIVE</span>
                </div>
                <div class="row" style="margin-bottom:12px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Auto Green (Tempo)</div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Right stick auto timing</div>
                    </div>
                    <div id="tempoToggle" class="switch" onclick="toggleTempo()"></div>
                </div>
                <div class="row" style="margin-bottom:4px;"><span class="slider-label">Stand Still <span class="key-bind" id="tempoKeyLabel">C</span></span><span class="slider-val" id="tempoVal">0.550s</span></div>
                <input type="range" min="0.400" max="0.750" step="0.001" value="0.550" id="tempoSld" oninput="sync()">
                <div class="fine-tune-row">
                    <button class="ft-btn" onclick="nudge('tempoSld','tempoVal',-0.001)">−</button>
                    <span class="ft-label">Fine tune ±0.001s</span>
                    <button class="ft-btn" onclick="nudge('tempoSld','tempoVal',0.001)">+</button>
                </div>
                <div class="divider"></div>
                <div class="status-indicator" id="fadeStatusBar">
                    <div class="status-dot" id="fadeStatusDot"></div>
                    <span class="status-text" id="fadeStatusText">INACTIVE</span>
                </div>
                <div class="row" style="margin-bottom:12px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Fading Shot <span class="key-bind">V</span></div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Enabled with Tempo — press V to fade shoot</div>
                    </div>
                </div>
                <div class="row" style="margin-bottom:4px;"><span class="slider-label">Fading Timing</span><span class="slider-val" id="fadeVal">0.700s</span></div>
                <input type="range" min="0.300" max="1.200" step="0.001" value="0.700" id="fadeSld" oninput="sync()">
                <div class="fine-tune-row">
                    <button class="ft-btn" onclick="nudge('fadeSld','fadeVal',-0.001)">−</button>
                    <span class="ft-label">Fine tune ±0.001s</span>
                    <button class="ft-btn" onclick="nudge('fadeSld','fadeVal',0.001)">+</button>
                </div>
            </div>

            <div class="section-header">Consistency Sync</div>
            <div class="card">
                <div class="row" style="margin-bottom:12px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Enable Sync</div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Applies offset on top of tempo timing</div>
                    </div>
                    <div id="syncToggle" class="switch" onclick="toggleSync()"></div>
                </div>
                <div class="row" style="margin-bottom:4px;">
                    <span class="slider-label">Excellent Offset</span>
                    <span class="slider-val" id="syncVal">0ms</span>
                </div>
                <input type="range" min="-150" max="150" step="1" value="0" id="syncSld" oninput="syncOffset()">
                <div style="font-size:10px; color:var(--dim); margin-top:6px;">Slide + if Early, slide − if Late.</div>
            </div>

            <div class="section-header">Go To Shot <span class="key-bind" id="gotoKeyLabel">B</span></div>
            <div class="card">
                <div class="status-indicator" id="gotoStatusBar">
                    <div class="status-dot" id="gotoStatusDot"></div>
                    <span class="status-text" id="gotoStatusText">INACTIVE</span>
                </div>
                <div class="row" style="margin-bottom:12px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Auto Green (Go To)</div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Stick up → hold → flick down to green</div>
                    </div>
                    <div id="gotoToggle" class="switch" onclick="toggleGoto()"></div>
                </div>
                <div class="row" style="margin-bottom:4px;"><span class="slider-label">Speed</span><span class="slider-val" id="gotoVal">0.400s</span></div>
                <input type="range" min="0.100" max="0.900" step="0.001" value="0.400" id="gotoSld" oninput="syncGoto()">
                <div class="fine-tune-row">
                    <button class="ft-btn" onclick="nudgeGoto(-0.001)">−</button>
                    <span class="ft-label">Fine tune ±0.001s</span>
                    <button class="ft-btn" onclick="nudgeGoto(0.001)">+</button>
                </div>
                <div class="fine-tune-row">
                    <button class="ft-btn" onclick="nudgeGoto(-0.001)">−</button>
                    <span class="ft-label">Fine tune ±0.001s</span>
                    <button class="ft-btn" onclick="nudgeGoto(0.001)">+</button>
                </div>
            </div>

            <div class="section-header">Keybinds</div>
            <div class="card">
                <div class="row" style="margin-bottom:10px;">
                    <span class="slider-label">Square Shot Key</span>
                    <input class="key-input" id="keySq" maxlength="1" value="X" />
                </div>
                <div class="row" style="margin-bottom:10px;">
                    <span class="slider-label">Tempo Shot Key</span>
                    <input class="key-input" id="keyTempo" maxlength="1" value="C" />
                </div>
                <div class="row">
                    <span class="slider-label">Go To Shot Key</span>
                    <input class="key-input" id="keyGoto" maxlength="1" value="B" />
                </div>
                <div style="display:flex; align-items:center;">
                    <button class="save-btn" onclick="saveKeybinds()">Save Keybinds</button>
                    <span class="saved-tag" id="savedTag">✓ Saved</span>
                </div>
            </div>

            <div class="section-header">Shot Terminal</div>
            <div class="log-container" id="logBox"></div>
        </div>

        <!-- TIMING TAB -->
        <div id="timingView" class="view">
            <div class="section-header">Square Timing</div>
            <div class="card">
                <div class="row" style="margin-bottom:4px;"><span class="slider-label">Normal Shot</span><span class="slider-val" id="t_sqVal">0.510s</span></div>
                <input type="range" min="0.450" max="0.600" step="0.001" value="0.510" id="t_sqSld" oninput="syncTiming()">
                <div class="row" style="margin-top:14px; margin-bottom:4px;"><span class="slider-label">Fading Shot</span><span class="slider-val" id="t_sqFadeVal">0.510s</span></div>
                <input type="range" min="0.400" max="0.700" step="0.001" value="0.510" id="t_sqFadeSld" oninput="syncTiming()">
            </div>
            <div class="section-header">Tempo Timing</div>
            <div class="card">
                <div class="row" style="margin-bottom:4px;"><span class="slider-label">Normal</span><span class="slider-val" id="t_tempoVal">0.550s</span></div>
                <input type="range" min="0.400" max="0.750" step="0.001" value="0.550" id="t_tempoSld" oninput="syncTiming()">
                <div class="row" style="margin-top:14px; margin-bottom:4px;"><span class="slider-label">Fading Shot</span><span class="slider-val" id="t_fadeVal">0.700s</span></div>
                <input type="range" min="0.300" max="1.200" step="0.001" value="0.700" id="t_fadeSld" oninput="syncTiming()">
            </div>
        </div>

        <!-- NETWORK TAB -->
        <div id="networkView" class="view">
            <div class="section-header">Connection</div>
            <div class="card" id="chiakiBar2" style="border-color:rgba(255,68,68,0.3); text-align:center; padding:10px;">
                <span id="chiakiTxt2" style="color:#ff4444; font-size:12px; font-weight:800;">CHIAKI: DISCONNECTED</span>
            </div>

            <div class="section-header">Ping Monitor</div>
            <div class="card" style="text-align:center;">
                <div class="ping-circle-wrap">
                    <div class="ping-circle" id="pingCircle">
                        <div class="ping-num" id="pingNum" style="color:#00ff88;">--</div>
                        <div class="ping-label">MS</div>
                        <div class="ping-status" id="pingStatus" style="color:#00ff88;">GOOD</div>
                    </div>
                </div>
                <div class="row" style="margin-top:8px;">
                    <span class="slider-label">WiFi Signal</span>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div class="wifi-bars">
                            <div class="wifi-bar" id="wb1"></div>
                            <div class="wifi-bar" id="wb2"></div>
                            <div class="wifi-bar" id="wb3"></div>
                            <div class="wifi-bar" id="wb4"></div>
                            <div class="wifi-bar" id="wb5"></div>
                        </div>
                        <span id="wifiVal" style="font-size:12px; font-weight:700; color:var(--cyan);">--%</span>
                    </div>
                </div>
            </div>

            <div class="section-header">Lag Compensation</div>
            <div class="card">
                <div class="row">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Auto Adjust Timing</div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Adapts to ping spikes</div>
                    </div>
                    <div id="lagToggle" class="switch" onclick="toggleLag()"></div>
                </div>
                <div class="row" style="margin-top:10px;">
                    <span class="slider-label">Adjustment</span>
                    <span id="lagAdjVal" style="font-size:12px; color:var(--cyan); font-weight:700;">0ms</span>
                </div>
            </div>

            <div class="section-header">⚡ Lag Switch</div>
            <div class="card">
                <div class="row" style="margin-bottom:10px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Lag Switch</div>

                    </div>
                    <div id="lagSwitchToggle" class="switch" onclick="toggleLagSwitch()"></div>
                </div>
                <div class="lag-warning">
                    <div class="lag-warning-icon">⚠️</div>
                    <div class="lag-warning-text">WARNING: Lag switch can spike ping up to 800ms and may remove you from the game. Use at your own risk.</div>
                </div>
            </div>
        </div>

        <!-- CAPTURE TAB -->
        <div id="connView" class="view">
            <div class="section-header">Remote Play</div>
            <div class="card" id="chiakiBar" style="border-color:rgba(255,68,68,0.3); text-align:center; padding:10px;">
                <span id="chiakiTxt" style="color:#ff4444; font-size:12px; font-weight:800;">CHIAKI: DISCONNECTED</span>
            </div>
            <div class="section-header">Detection Feed</div>
            <div class="card" style="text-align:center; background:#000; padding:12px;">
                <img id="liveFeed" style="width:100%; max-width:300px; height:auto; border:1px solid var(--border); border-radius:8px;">
                <p style="font-size:10px; color:var(--dim); margin-top:8px;">Align white meter bar inside the box.</p>
            </div>
        </div>

        <!-- TRAINING TAB -->
        <div id="trainView" class="view">
            <div class="section-header">Training Mode</div>
            <div class="card">
                <div class="row" style="margin-bottom:10px;">
                    <div>
                        <div style="font-weight:800; font-size:13px;">Enable Training</div>
                        <div style="font-size:10px; color:var(--dim); margin-top:2px;">Auto-tunes after 15 shots</div>
                    </div>
                    <div id="trainToggle" class="switch" onclick="toggleTrain()"></div>
                </div>
            </div>
            <div class="section-header">Stats</div>
            <div class="card">
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Shots</span><span class="slider-val" id="tr_shots">0 / 15</span></div>
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Greens</span><span class="slider-val" id="tr_greens">0</span></div>
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Green Rate</span><span class="slider-val" id="tr_rate">0%</span></div>
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Square Rate</span><span class="slider-val" id="tr_sq_rate">—</span></div>
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Tempo Rate</span><span class="slider-val" id="tr_tempo_rate">—</span></div>
                <div class="row"><span class="slider-label">Status</span><span class="slider-val" id="tr_status" style="color:var(--dim);">Waiting...</span></div>
            </div>
            <div class="section-header">Values Being Tuned</div>
            <div class="card">
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Square Normal</span><span class="slider-val" id="tr_sq">—</span></div>
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Square Fading</span><span class="slider-val" id="tr_sqFade">—</span></div>
                <div class="row" style="margin-bottom:8px;"><span class="slider-label">Tempo Normal</span><span class="slider-val" id="tr_tempo">—</span></div>
                <div class="row"><span class="slider-label">Tempo Fading</span><span class="slider-val" id="tr_tempFade">—</span></div>
            </div>
            <div class="section-header">Actions</div>
            <div class="card">
                <div class="row" style="margin-bottom:10px;">
                    <button class="save-btn" onclick="trainGreen()" style="margin-top:0; margin-right:8px;">✓ Mark GREEN</button>
                    <button class="save-btn" onclick="trainMiss()" style="margin-top:0; background:#ff003c;">✗ Mark MISS</button>
                </div>
                <div style="font-size:10px; color:var(--dim); margin-bottom:10px;">Mark each shot so training can tune your timing.</div>
                <button class="save-btn ghost" onclick="trainReset()">Reset Training</button>
            </div>
            <div class="section-header">Training Log</div>
            <div class="log-container" id="trainLog"></div>
        </div>

        <!-- JUMPERS TAB -->
        <div id="jumpersView" class="view">
            <div class="section-header">6'5 and Under</div>
            <div class="card" style="margin-bottom:10px;">
                <div style="font-size:11px; color:var(--dim); font-style:italic;">Coming soon...</div>
            </div>
            <div class="section-header">6'5 and Over</div>
            <div class="card" style="margin-bottom:10px;">
                <div style="font-size:10px; color:var(--dim); margin-bottom:12px;">RECOMMENDED TIMING: <span style="color:var(--cyan); font-weight:800;">0.575s</span></div>
                <div class="jumper-row">
                    <div class="jumper-title">Grimes / Shepard / Shepard</div>
                    <div class="jumper-tags"><span class="jtag">50/50</span><span class="jtag">4/4</span><span class="jtag">Push</span></div>
                    <button class="jumper-btn" onclick="applyJumper(0.575)">Apply</button>
                </div>
                <div class="jumper-divider"></div>
                <div class="jumper-row">
                    <div class="jumper-title">Grimes / Brooks / Brooks</div>
                    <div class="jumper-tags"><span class="jtag">50/50</span><span class="jtag">4/4</span><span class="jtag">Push</span></div>
                    <button class="jumper-btn" onclick="applyJumper(0.575)">Apply</button>
                </div>
                <div class="jumper-divider"></div>
                <div class="jumper-row">
                    <div class="jumper-title">Grimes / Hauser / Hauser</div>
                    <div class="jumper-tags"><span class="jtag">50/50</span><span class="jtag">4/4</span><span class="jtag">Push</span></div>
                    <button class="jumper-btn" onclick="applyJumper(0.575)">Apply</button>
                </div>
            </div>
            <div class="section-header">7ft</div>
            <div class="card">
                <div style="font-size:11px; color:var(--dim); font-style:italic;">Coming soon...</div>
            </div>
            <div id="jumperApplied" style="display:none; background:rgba(0,255,136,0.06); border:1px solid rgba(0,255,136,0.2); border-radius:8px; padding:10px 14px; margin-top:12px; font-size:12px; color:#00ff88; font-weight:700; text-align:center;">
                ✓ Timing Applied — Check Shooting Tab
            </div>
        </div>

    </div>

    <script>
        let sqOn = false, tempoOn = false, fadeOn = false, gotoOn = false, lagOn = false, lagSwitchOn = false;
        let lagSwitchInterval = null;

        function addLog(msg) {
            const box = document.getElementById('logBox');
            const d = document.createElement('div'); d.className = 'log-entry'; d.innerText = msg;
            box.prepend(d); if (box.children.length > 20) box.lastChild.remove();
        }
        function showView(id, el) {
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(id).classList.add('active'); el.classList.add('active');
        }
        function login() {
            const key = document.getElementById('authKey').value;
            pywebview.api.check_access(key).then(result => {
                if (result === true || (result && result.ok)) {
                    document.getElementById('authScreen').style.display = 'none';
                    loadSaved();
                    const days = result && result.days ? result.days : null;
                    const db = document.getElementById('daysBadge');
                    if (days) {
                        db.innerText = days === 'Lifetime' ? '♾ Lifetime Access' : days + ' days remaining';
                        db.style.display = 'block';
                        db.style.color = days === 'Lifetime' ? 'var(--cyan)' : parseInt(days) <= 3 ? 'var(--red)' : parseInt(days) <= 7 ? '#ffaa00' : 'var(--cyan)';
                    }
                } else { alert((result && result.message) || result || "Invalid key"); }
            });
        }
        function loadSaved() {
            pywebview.api.get_settings().then(s => {
                if (!s) return;
                document.getElementById('sqSld').value = s.square_timing;       document.getElementById('sqVal').innerText = s.square_timing + "s";
                document.getElementById('sqFadeSld').value = s.square_fade_timing; document.getElementById('sqFadeVal').innerText = s.square_fade_timing + "s";
                document.getElementById('tempoSld').value = s.tempo_timing;     document.getElementById('tempoVal').innerText = s.tempo_timing + "s";
                document.getElementById('fadeSld').value = s.tempo_fade_timing; document.getElementById('fadeVal').innerText = s.tempo_fade_timing + "s";
                document.getElementById('t_sqSld').value = s.square_timing;     document.getElementById('t_sqVal').innerText = s.square_timing + "s";
                document.getElementById('t_sqFadeSld').value = s.square_fade_timing; document.getElementById('t_sqFadeVal').innerText = s.square_fade_timing + "s";
                document.getElementById('t_tempoSld').value = s.tempo_timing;   document.getElementById('t_tempoVal').innerText = s.tempo_timing + "s";
                document.getElementById('t_fadeSld').value = s.tempo_fade_timing; document.getElementById('t_fadeVal').innerText = s.tempo_fade_timing + "s";
                const sq = s.key_square.toUpperCase(); const tp = s.key_tempo.toUpperCase(); const gt = (s.key_goto || 'b').toUpperCase();
                document.getElementById('keySq').value = sq; document.getElementById('keyTempo').value = tp; document.getElementById('keyGoto').value = gt;
                document.getElementById('sqKeyLabel').innerText = sq; document.getElementById('tempoKeyLabel').innerText = tp; document.getElementById('gotoKeyLabel').innerText = gt;
                if (s.sync_offset !== undefined) {
                    document.getElementById('syncSld').value = s.sync_offset;
                    const v = parseInt(s.sync_offset);
                    document.getElementById('syncVal').innerText = (v > 0 ? '+' : '') + v + 'ms';
                }
                if (s.sync_enabled) {
                    syncOn = true;
                    document.getElementById('syncToggle').classList.add('on');
                }
                if (s.goto_timing !== undefined) {
                    document.getElementById('gotoSld').value = s.goto_timing;
                    document.getElementById('gotoVal').innerText = parseFloat(s.goto_timing).toFixed(3) + "s";
                    pywebview.api.set_goto_timing(s.goto_timing);
                }
                // Sync Python with current slider values WITHOUT resetting toggle states
                pywebview.api.sync_settings(sqOn, s.square_timing, s.square_fade_timing, tempoOn, s.tempo_timing, s.tempo_fade_timing, fadeOn);
            });
        }
        // Session stats
        let sessionShots = 0, sessionGreens = 0;
        function recordShot(wasGreen) {
            sessionShots++;
            if (wasGreen) sessionGreens++;
            document.getElementById('stat-shots').innerText = sessionShots;
            document.getElementById('stat-greens').innerText = sessionGreens;
            const pct = sessionShots > 0 ? Math.round(sessionGreens / sessionShots * 100) : 0;
            document.getElementById('stat-pct').innerText = pct + '%';
            document.getElementById('stat-pct').style.color = pct >= 70 ? '#00ff88' : pct >= 40 ? '#f5c518' : '#ff4444';
        }

        // Nudge fine tune
        function nudge(sliderId, valId, delta) {
            const sld = document.getElementById(sliderId);
            const newVal = Math.round((parseFloat(sld.value) + delta) * 1000) / 1000;
            const mn = parseFloat(sld.min), mx = parseFloat(sld.max);
            sld.value = Math.min(mx, Math.max(mn, newVal));
            document.getElementById(valId).innerText = parseFloat(sld.value).toFixed(3) + "s";
            sync();
        }

        // Status indicator helper
        function updateStatusIndicator(dotId, textId, on, label) {
            const dot = document.getElementById(dotId);
            const txt = document.getElementById(textId);
            dot.className = 'status-dot' + (on ? ' active' : '');
            txt.className = 'status-text' + (on ? ' active' : '');
            txt.innerText = on ? label : 'INACTIVE';
        }

        function toggleSq() {
            sqOn = !sqOn;
            document.getElementById('sqToggle').classList.toggle('on');
            updateStatusIndicator('sqStatusDot', 'sqStatusText', sqOn, 'ACTIVE');
            sync();
        }
        function toggleTempo() {
            tempoOn = !tempoOn;
            document.getElementById('tempoToggle').classList.toggle('on');
            updateStatusIndicator('tempoStatusDot', 'tempoStatusText', tempoOn, 'ACTIVE');
            updateStatusIndicator('fadeStatusDot', 'fadeStatusText', tempoOn, 'ACTIVE');
            sync();
        }
        function toggleFade() {} // no longer used — V key shoots fade directly
        function onFadeHotkeyToggle(isOn) {} // no longer used
        function applyJumper(timing) {
            document.getElementById('tempoSld').value = timing;
            document.getElementById('tempoVal').innerText = timing.toFixed(3) + "s";
            if (document.getElementById('t_tempoSld')) {
                document.getElementById('t_tempoSld').value = timing;
                document.getElementById('t_tempoVal').innerText = timing.toFixed(3) + "s";
            }
            sync();
            const tag = document.getElementById('jumperApplied');
            tag.style.display = 'block';
            setTimeout(() => tag.style.display = 'none', 3000);
        }
        function toggleGoto() {
            gotoOn = !gotoOn;
            document.getElementById('gotoToggle').classList.toggle('on');
            updateStatusIndicator('gotoStatusDot', 'gotoStatusText', gotoOn, 'ACTIVE');
            syncGoto();
        }
        function syncGoto() {
            const v = document.getElementById('gotoSld').value;
            document.getElementById('gotoVal').innerText = parseFloat(v).toFixed(3) + "s";
            pywebview.api.sync_goto(gotoOn, v);
        }
        function nudgeGoto(delta) {
            const sld = document.getElementById('gotoSld');
            const newVal = Math.round((parseFloat(sld.value) + delta) * 1000) / 1000;
            const mn = parseFloat(sld.min), mx = parseFloat(sld.max);
            sld.value = Math.min(mx, Math.max(mn, newVal));
            document.getElementById('gotoVal').innerText = parseFloat(sld.value).toFixed(3) + "s";
            pywebview.api.sync_goto(gotoOn, sld.value);
        }
        function syncOffset() {
            const v = parseInt(document.getElementById('syncSld').value);
            document.getElementById('syncVal').innerText = (v > 0 ? '+' : '') + v + 'ms';
            pywebview.api.set_sync_offset(v);
        }
        function getVals() { return { sq: document.getElementById('sqSld').value, sqFade: document.getElementById('sqFadeSld').value, tempo: document.getElementById('tempoSld').value, fade: document.getElementById('fadeSld').value }; }
        function sync() {
            const v = getVals();
            document.getElementById('sqVal').innerText = v.sq + "s"; document.getElementById('sqFadeVal').innerText = v.sqFade + "s";
            document.getElementById('tempoVal').innerText = v.tempo + "s"; document.getElementById('fadeVal').innerText = v.fade + "s";
            document.getElementById('t_sqSld').value = v.sq; document.getElementById('t_sqVal').innerText = v.sq + "s";
            document.getElementById('t_sqFadeSld').value = v.sqFade; document.getElementById('t_sqFadeVal').innerText = v.sqFade + "s";
            document.getElementById('t_tempoSld').value = v.tempo; document.getElementById('t_tempoVal').innerText = v.tempo + "s";
            document.getElementById('t_fadeSld').value = v.fade; document.getElementById('t_fadeVal').innerText = v.fade + "s";
            pywebview.api.sync_settings(sqOn, v.sq, v.sqFade, tempoOn, v.tempo, v.fade, false);
        }
        function syncTiming() {
            const sq = document.getElementById('t_sqSld').value, sqFade = document.getElementById('t_sqFadeSld').value;
            const tempo = document.getElementById('t_tempoSld').value, fade = document.getElementById('t_fadeSld').value;
            document.getElementById('t_sqVal').innerText = sq + "s"; document.getElementById('t_sqFadeVal').innerText = sqFade + "s";
            document.getElementById('t_tempoVal').innerText = tempo + "s"; document.getElementById('t_fadeVal').innerText = fade + "s";
            document.getElementById('sqSld').value = sq; document.getElementById('sqVal').innerText = sq + "s";
            document.getElementById('sqFadeSld').value = sqFade; document.getElementById('sqFadeVal').innerText = sqFade + "s";
            document.getElementById('tempoSld').value = tempo; document.getElementById('tempoVal').innerText = tempo + "s";
            document.getElementById('fadeSld').value = fade; document.getElementById('fadeVal').innerText = fade + "s";
            pywebview.api.sync_settings(sqOn, sq, sqFade, tempoOn, tempo, fade, fadeOn);
        }
        function saveKeybinds() {
            const sq   = document.getElementById('keySq').value.toLowerCase().trim();
            const tp   = document.getElementById('keyTempo').value.toLowerCase().trim();
            const gt   = document.getElementById('keyGoto').value.toLowerCase().trim();
            if (!sq || !tp || !gt) return;
            document.getElementById('sqKeyLabel').innerText    = sq.toUpperCase();
            document.getElementById('tempoKeyLabel').innerText = tp.toUpperCase();
            document.getElementById('gotoKeyLabel').innerText  = gt.toUpperCase();
            pywebview.api.set_keybinds(sq, tp, gt).then(() => {
                const tag = document.getElementById('savedTag'); tag.style.display = 'inline';
                setTimeout(() => tag.style.display = 'none', 2000);
            });
        }
        function updatePreview(data) { document.getElementById('liveFeed').src = "data:image/jpeg;base64," + data; }
        function updateChiakiStatus(active) {
            ['chiakiBar','chiakiBar2'].forEach(id => {
                const bar = document.getElementById(id);
                if (bar) bar.style.borderColor = active ? 'rgba(0,255,136,0.3)' : 'rgba(255,68,68,0.3)';
            });
            ['chiakiTxt','chiakiTxt2'].forEach(id => {
                const txt = document.getElementById(id);
                if (txt) { txt.style.color = active ? '#00ff88' : '#ff4444'; txt.innerText = active ? 'CHIAKI: CONNECTED' : 'CHIAKI: DISCONNECTED'; }
            });
        }

        // ===== NETWORK =====
        function toggleLag() {
            lagOn = !lagOn;
            document.getElementById('lagToggle').classList.toggle('on');
            pywebview.api.toggle_lag_comp(lagOn);
        }

        // ===== LAG SWITCH =====
        function toggleLagSwitch() {
            lagSwitchOn = !lagSwitchOn;
            document.getElementById('lagSwitchToggle').classList.toggle('on');
            pywebview.api.toggle_lag_switch(lagSwitchOn);
            if (lagSwitchOn) {
                lagSwitchInterval = setInterval(() => {
                    const fakePing = Math.floor(Math.random() * 700) + 100;
                    updatePingCircle(fakePing);
                }, 200);
            } else {
                clearInterval(lagSwitchInterval);
                lagSwitchInterval = null;
            }
        }

        function updatePingCircle(ping) {
            const circle = document.getElementById('pingCircle');
            const num    = document.getElementById('pingNum');
            const status = document.getElementById('pingStatus');
            num.innerText = ping === null ? '--' : ping;
            circle.className = 'ping-circle';
            if (ping === null) {
                num.style.color = '#fff'; status.style.color = '#fff'; status.innerText = '---';
            } else if (lagSwitchOn) {
                circle.classList.add('crazy');
                num.style.color = '#ff4444'; status.style.color = '#ff4444'; status.innerText = 'SPIKING';
            } else if (ping < 30) {
                circle.classList.add('good'); num.style.color = '#00ff88'; status.style.color = '#00ff88'; status.innerText = 'EXCELLENT';
            } else if (ping < 80) {
                circle.classList.add('ok');   num.style.color = '#f5c518'; status.style.color = '#f5c518'; status.innerText = 'GOOD';
            } else {
                circle.classList.add('bad');  num.style.color = '#ff4444'; status.style.color = '#ff4444'; status.innerText = 'HIGH';
            }
        }

        function pollNetwork() {
            if (lagSwitchOn) return;
            pywebview.api.get_network_stats().then(s => {
                if (!s) return;
                updatePingCircle(s.ping);
                const wifi = s.wifi;
                if (wifi !== null && wifi !== undefined) {
                    document.getElementById('wifiVal').innerText = wifi + '%';
                    const bars = Math.ceil(wifi / 20);
                    const wc = wifi > 70 ? '#00ff88' : wifi > 40 ? '#f5c518' : '#ff4444';
                    for (let i = 1; i <= 5; i++) {
                        const b = document.getElementById('wb' + i);
                        b.style.background = i <= bars ? wc : '#1a0010';
                    }
                }
                if (s.adj !== undefined) {
                    document.getElementById('lagAdjVal').innerText = lagOn ? '-' + Math.round(s.adj * 1000) + 'ms' : '0ms';
                }
            }).catch(() => {});
        }
        setInterval(pollNetwork, 5000);

        // ===== TRAINING =====
        let trainOn = false;
        function toggleTrain() {
            trainOn = !trainOn;
            document.getElementById('trainToggle').classList.toggle('on');
            pywebview.api.training_toggle(trainOn).then(() => {
                document.getElementById('tr_status').innerText = trainOn ? 'Active' : 'Waiting...';
                document.getElementById('tr_status').style.color = trainOn ? 'var(--cyan)' : 'var(--dim)';
                addTrainLog(trainOn ? 'Training enabled.' : 'Training disabled.');
            });
            refreshTrainValues();
        }
        function refreshTrainValues() {
            pywebview.api.get_settings().then(s => {
                if (!s) return;
                document.getElementById('tr_sq').innerText = s.square_timing + 's';
                document.getElementById('tr_sqFade').innerText = s.square_fade_timing + 's';
                document.getElementById('tr_tempo').innerText = s.tempo_timing + 's';
                document.getElementById('tr_tempFade').innerText = s.tempo_fade_timing + 's';
            });
        }
        function trainGreen() { if (!trainOn) { addTrainLog('Enable Training first.'); return; } pywebview.api.training_mark(true).then(r => updateTrainUI(r, true)); }
        function trainMiss()  { if (!trainOn) { addTrainLog('Enable Training first.'); return; } pywebview.api.training_mark(false).then(r => updateTrainUI(r, false)); }
        function updateTrainUI(r, wasGreen) {
            if (!r) return;
            if (r.status === 'disabled') { addTrainLog('Training is disabled.'); return; }
            if (r.status === 'recorded') {
                document.getElementById('tr_shots').innerText = r.shots + ' / 15';
                document.getElementById('tr_greens').innerText = r.greens;
                const rate = r.shots > 0 ? Math.round(r.greens / r.shots * 100) : 0;
                document.getElementById('tr_rate').innerText = rate + '%';
                addTrainLog((wasGreen ? '✓ GREEN' : '✗ MISS') + ' — ' + r.shots + '/15');
            }
            if (r.status === 'tuned') {
                document.getElementById('tr_shots').innerText = '0 / 15'; document.getElementById('tr_greens').innerText = '0';
                document.getElementById('tr_rate').innerText = '0%'; document.getElementById('tr_sq_rate').innerText = '—'; document.getElementById('tr_tempo_rate').innerText = '—';
                document.getElementById('tr_status').innerText = 'Tuned!'; document.getElementById('tr_status').style.color = 'var(--cyan)';
                addTrainLog('Auto-tune complete!'); refreshTrainValues(); loadSaved();
                setTimeout(() => { document.getElementById('tr_status').innerText = 'Active'; }, 3000);
            }
        }
        function onTrainTuned(sq, sqFade, tempo, fade) {
            document.getElementById('tr_sq').innerText = sq + 's'; document.getElementById('tr_sqFade').innerText = sqFade + 's';
            document.getElementById('tr_tempo').innerText = tempo + 's'; document.getElementById('tr_tempFade').innerText = fade + 's';
        }
        function trainReset() {
            pywebview.api.training_reset().then(() => {
                document.getElementById('tr_shots').innerText = '0 / 15'; document.getElementById('tr_greens').innerText = '0';
                document.getElementById('tr_rate').innerText = '0%'; document.getElementById('tr_sq_rate').innerText = '—'; document.getElementById('tr_tempo_rate').innerText = '—';
                document.getElementById('tr_status').innerText = trainOn ? 'Active' : 'Waiting...';
                addTrainLog('Training reset.');
            });
        }
        function addTrainLog(msg) {
            const box = document.getElementById('trainLog');
            if (!box) return;
            const d = document.createElement('div'); d.className = 'log-entry';
            const now = new Date();
            const ts = now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0') + ':' + now.getSeconds().toString().padStart(2,'0');
            d.innerText = '[' + ts + '] ' + msg; box.prepend(d);
            if (box.children.length > 20) box.lastChild.remove();
        }
        // ===== SYNC =====
        let syncOn = false;
        function toggleSync() {
            syncOn = !syncOn;
            document.getElementById('syncToggle').classList.toggle('on');
            pywebview.api.set_sync_enabled(syncOn);
        }
        function syncOffset() {
            const v = parseInt(document.getElementById('syncSld').value);
            document.getElementById('syncVal').innerText = (v > 0 ? '+' : '') + v + 'ms';
            pywebview.api.set_sync_offset(v);
        }
        // ===== GO TO SHOT =====
        function toggleGoto() {
            gotoOn = !gotoOn;
            document.getElementById('gotoToggle').classList.toggle('on');
            updateStatusIndicator('gotoStatusDot', 'gotoStatusText', gotoOn, 'ACTIVE');
            syncGoto();
        }
        function syncGoto() {
            const val = document.getElementById('gotoSld').value;
            document.getElementById('gotoVal').innerText = parseFloat(val).toFixed(3) + "s";
            pywebview.api.set_goto_timing(val);
        }
        function nudgeGoto(delta) {
            const sld = document.getElementById('gotoSld');
            const newVal = Math.round((parseFloat(sld.value) + delta) * 1000) / 1000;
            const mn = parseFloat(sld.min), mx = parseFloat(sld.max);
            sld.value = Math.min(mx, Math.max(mn, newVal));
            document.getElementById('gotoVal').innerText = parseFloat(sld.value).toFixed(3) + "s";
            pywebview.api.set_goto_timing(sld.value);
        }

    </script>
</body>
</html>
"""
if __name__ == '__main__':
    api = xDriveApi()
    window = webview.create_window('xDrive v2.1', html=HTML_CONTENT, js_api=api, width=820, height=750, resizable=False)
    api.set_window(window); api.start_threads(); webview.start()
