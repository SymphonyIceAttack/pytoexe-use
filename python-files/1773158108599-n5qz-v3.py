import base64
import json
import os
import subprocess
import threading
import time
import webbrowser
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from queue import Queue, Empty

import mss
import numpy as np
import cv2

import pyautogui
import pyttsx3
import requests
import speech_recognition as sr
from colorama import Fore, Style, init as colorama_init
import tkinter as tk
from tkinter import scrolledtext, BooleanVar


# -------- CONFIG: DeepSeek (OpenAI-style) --------
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

MEMORY_FILE = "v3_memory.json"


SYSTEM_PROMPT = """
You are V3, a JSON-only, conversational, proactive, tool-using autonomous agent
for a Windows PC and a professional day-trading assistant.

You always receive:
- The user's Bangla+English mixed request as TEXT (voice or chat).
- The LATEST cropped screenshot of the user's TRADING CHART region (if enabled).
- A short MEMORY SUMMARY of the last interactions, including past signals, confidence,
  reasons, user preferences, and "learned" notes.

Your behavior MUST be:

1) PERSISTENT & CONTEXT-AWARE:
   - Use the MEMORY SUMMARY to remember previous decisions, trading bias, timeframes,
     risk appetite, and any user preferences (e.g., prefers scalping, avoids leverage,
     likes certain websites, has specific shortcuts, etc.).
   - If the current request conflicts with recent decisions or preferences, mention it
     in your reasoning and ask for clarification if needed.
   - When the user explicitly says to "teach you" something (e.g., how THEY trade),
     treat that as persistent knowledge and reference it later in your reasoning.

2) PROACTIVE & CLARIFICATION-ORIENTED:
   - If a task is complex or ambiguous (e.g., file downloads with multiple buttons,
     multiple possible links, unclear chart direction), DO NOT just guess.
   - You MUST ask a clarifying question like:
       "Should I click the main Download button or the Mirror link on the left?"
     or
       "Do you want a scalp BUY or a swing SELL here?"
   - Use the fields `needs_clarification` and `clarification_question` to request this.

3) TRADING / CHART ANALYSIS INTELLIGENCE:
   If the request is about TRADING / CHART ANALYSIS:
   - Use ONLY the cropped chart image (if provided) to:
     - Read candlestick patterns (engulfing, pin bar, doji, inside bar, etc.),
     - Estimate local trend (uptrend, downtrend, range),
     - Identify approximate support/resistance levels visible in the crop,
     - Combine this with the user's intent and MEMORY SUMMARY (e.g., recent trades).
   - Then produce:
     - A trading SIGNAL: "BUY", "SELL", or "NONE",
     - A numeric CONFIDENCE between 0.0 and 1.0,
     - A short REASON in English.
   - Also plan a SEQUENCE OF PC/WEB actions (if needed) to help execute the trade
     (for example, move mouse near BUY button, click, type quantity, etc.).

4) GENERAL PC CONTROL & TOOL USE:
   If the request is about GENERAL PC CONTROL, CODING, BROWSER CONTROL, or LOGIC:
   - Set: "signal": "NONE", "confidence": 0.0 (or very low),
   - Still plan a SEQUENCE OF actions.
   - You have access to the following TOOL ACTIONS:

     PC / UI:
       - "run_program"   → Start a desktop program by name.
       - "close_program" → Close active window (via hotkey).
       - "shell"         → Run a shell command (VERY DANGEROUS).
       - "type_text"     → Type text at current cursor.
       - "keypress"      → Press a single key (e.g. 'enter', 'tab', 'esc', 'f5').
       - "key_hold"      → Press and hold a key for N seconds.
       - "hotkey"        → Press combination keys (e.g., ['ctrl', 'l'], ['alt', 'tab']).
       - "mouse_move"    → Move mouse to coordinates.
       - "mouse_click"   → Click at current mouse position.
       - "mouse_drag"    → Drag from one point to another.
       - "mouse_scroll"  → Scroll up/down.
       - "find_and_click"→ Use template-image based search to click UI elements.

     WEB / NETWORK:
       - "open_url"      → Open a website in the default browser.
       - "http_get"      → Simple HTTP GET to a URL.
       - "http_post"     → Simple HTTP POST to a URL with JSON body.

     FILESYSTEM & LOGIC:
       - "list_dir"          → List files/directories in a given path.
       - "read_file_snippet" → Read a short snippet of a file for inspection.
       - "none"              → No external action, pure reasoning/explanation.

5) CHAIN-OF-THOUGHT STYLE PLANNING:
   - BEFORE listing `actions`, you MUST think step-by-step and output this plan
     in a "thinking" field as a short bullet-style reasoning (in English).
   - Example:
       "thinking": "1) Check if chart shows strong uptrend. 2) Identify last support.
        3) Prepare BUY bias with tight stop. 4) Move mouse near BUY button and wait."
   - If you are uncertain, set `needs_clarification = true` and craft a specific
     `clarification_question` for the user.

6) RISK AWARENESS:
   - Include a boolean `is_risky` field.
   - If the user explicitly says this is "final", "no confirmation", "ঝুঁকিপূর্ণ",
     "risky", etc., and the action may change positions, close programs, or modify files,
     then set `is_risky = true`.
   - Otherwise, set `is_risky = false` for normal operations.

7) SELF-LEARNING BEHAVIOR (within this session + memory file):
   - When the user says that you should "learn trading", "learn this method", or similar,
     you may plan WEB research actions (http_get, open_url) to gather info.
   - Summarize what you learned and include a short "learned_note" in the JSON so that
     the caller can store it in persistent memory.
   - In future responses, reference these "learned_note" items from MEMORY SUMMARY.

You MUST respond with a single JSON object in this exact shape:

{
  "signal": "BUY" | "SELL" | "NONE",
  "confidence": 0.0-1.0,
  "reason": "short explanation in English",
  "is_risky": true | false,
  "thinking": "short step-by-step internal reasoning in English",
  "needs_clarification": true | false,
  "clarification_question": "question to ask user if needs_clarification is true, else empty string",
  "learned_note": "short optional note about what you learned here, or empty string",
  "actions": [
    {
      "action": "run_program" | "close_program" | "shell" | "open_url" |
                "type_text" | "keypress" | "key_hold" | "hotkey" |
                "mouse_move" | "mouse_click" | "mouse_drag" | "mouse_scroll" |
                "http_get" | "http_post" |
                "find_and_click" |
                "list_dir" | "read_file_snippet" |
                "none",
      "params": { ... }
    },
    ...
  ]
}

RULES:
- Always plan the full multi-step sequence in "actions" (even if it's just 1 step).
- If something is unclear or too dangerous (like deleting files, sending real money without explicit details),
  set "signal": "NONE", "confidence": 0.0, and keep "actions" empty or minimal.
- Return VALID JSON ONLY.
- NO markdown, NO backticks, NO extra text.
""".strip()


# -------- Conversation Memory with persistence --------
class ConversationMemory:
    def __init__(self, max_len: int = 20, path: str = MEMORY_FILE):
        self.path = path
        self.events: deque = deque(maxlen=max_len)
        self._load()

    def _load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for ev in data.get("events", []):
                self.events.append(ev)
        except Exception:
            pass

    def _save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"events": list(self.events)}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add(self, user_text: str, plan: Dict[str, Any], had_image: bool):
        self.events.append(
            {
                "user_text": user_text,
                "signal": plan.get("signal", "NONE"),
                "confidence": float(plan.get("confidence", 0.0)),
                "reason": plan.get("reason", ""),
                "had_image": had_image,
                "learned_note": plan.get("learned_note", ""),
            }
        )
        self._save()

    def summary(self, last_n: int = 15) -> str:
        if not self.events:
            return "Memory: No previous interactions."
        lines: List[str] = ["Memory: Last interactions (most recent last):"]
        for ev in list(self.events)[-last_n:]:
            ln = ev.get("learned_note", "")
            lines.append(
                f"- User: {ev['user_text'][:80]} | signal={ev['signal']} "
                f"conf={ev['confidence']:.2f} | reason={ev['reason'][:80]} "
                f"| had_image={ev['had_image']} | learned={ln[:60]}"
            )
        return "\n".join(lines)


# -------- Global state --------
latest_roi_image_b64: Optional[str] = None
roi_box: Optional[Tuple[int, int, int, int]] = None
capture_stop_event = threading.Event()
main_stop_event = threading.Event()
roi_lock = threading.Lock()
memory = ConversationMemory(max_len=20)
vision_enabled = True  # toggled by GUI
chat_queue: "Queue[str]" = Queue()


def kill_switch_triggered() -> bool:
    x, y = pyautogui.position()
    return x <= 2 and y <= 2


def screen_capture_worker(interval: float = 1.0):
    global latest_roi_image_b64, roi_box, vision_enabled

    with mss.mss() as sct:
        while not capture_stop_event.is_set():
            if kill_switch_triggered():
                main_stop_event.set()
                break

            if not vision_enabled:
                time.sleep(interval)
                continue

            with roi_lock:
                box = roi_box

            if box is not None:
                x, y, w, h = box
                mon = {"left": x, "top": y, "width": w, "height": h}
                shot = sct.grab(mon)
            else:
                shot = sct.grab(sct.monitors[1])

            img = np.array(shot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            ok, buf = cv2.imencode(".png", img)
            if ok:
                b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
                latest_roi_image_b64 = b64

            time.sleep(interval)


def select_roi_once() -> None:
    global roi_box

    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[1])
        img = np.array(shot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    clone = img.copy()
    r = cv2.selectROI("Select Trading Chart Area", clone, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow("Select Trading Chart Area")

    x, y, w, h = r
    if w > 0 and h > 0:
        with roi_lock:
            roi_box = (x, y, w, h)
        print(f"ROI set to x={x}, y={y}, w={w}, h={h}")
    else:
        print("ROI selection cancelled or invalid; using full screen.")


# -------- DeepSeek client --------
class DeepSeekClient:
    def __init__(self, api_key: Optional[str], memory: ConversationMemory):
        if not api_key:
            raise RuntimeError(
                f"{DEEPSEEK_API_KEY_ENV} is not set. Set your DeepSeek API key first."
            )
        self.api_key = api_key
        self.system_prompt = SYSTEM_PROMPT
        self.memory = memory

    def ask(self, user_text: str) -> Dict[str, Any]:
        global latest_roi_image_b64, vision_enabled

        img_b64 = latest_roi_image_b64 if vision_enabled else None
        image_content: List[Dict[str, Any]] = []
        if img_b64:
            image_content.append(
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
            )

        memory_summary = self.memory.summary()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": memory_summary},
            {
                "role": "user",
                "content": [{"type": "text", "text": user_text}] + image_content,
            },
        ]

        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": messages,
            "temperature": 0.25,
        }

        resp = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()

        try:
            obj = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = content[start : end + 1]
                obj = json.loads(snippet)
            else:
                raise

        return obj


# -------- Executor --------
class V3Executor:
    def __init__(self):
        pyautogui.FAILSAFE = True

    def execute_plan(self, plan: Dict[str, Any]) -> str:
        if kill_switch_triggered():
            main_stop_event.set()
            return "Kill switch triggered before execution."

        actions = plan.get("actions", []) or []
        results: List[str] = []

        for step in actions:
            if main_stop_event.is_set() or kill_switch_triggered():
                results.append("Execution stopped due to kill switch/main_stop_event.")
                break
            res = self._execute_single(step)
            results.append(res)
        return "\n".join(results)

    def _execute_single(self, step: Dict[str, Any]) -> str:
        action = step.get("action", "none")
        params = step.get("params", {}) or {}

        if action == "run_program":
            return self._run_program(params)
        if action == "close_program":
            return self._close_program(params)
        if action == "shell":
            return self._shell(params)
        if action == "open_url":
            return self._open_url(params)
        if action == "type_text":
            return self._type_text(params)
        if action == "keypress":
            return self._keypress(params)
        if action == "key_hold":
            return self._key_hold(params)
        if action == "hotkey":
            return self._hotkey(params)
        if action == "mouse_move":
            return self._mouse_move(params)
        if action == "mouse_click":
            return self._mouse_click(params)
        if action == "mouse_drag":
            return self._mouse_drag(params)
        if action == "mouse_scroll":
            return self._mouse_scroll(params)
        if action == "http_get":
            return self._http_get(params)
        if action == "http_post":
            return self._http_post(params)
        if action == "find_and_click":
            return self._find_and_click(params)
        if action == "list_dir":
            return self._list_dir(params)
        if action == "read_file_snippet":
            return self._read_file_snippet(params)
        return "No action executed (none/unknown)."

    # PC tools
    def _run_program(self, params: Dict[str, Any]) -> str:
        name = params.get("name")
        if not name:
            return "run_program: missing 'name'."
        subprocess.Popen(name, shell=True)
        return f"Started program: {name}"

    def _close_program(self, params: Dict[str, Any]) -> str:
        pyautogui.hotkey("alt", "f4")
        return "Sent Alt+F4 to close active window."

    def _shell(self, params: Dict[str, Any]) -> str:
        cmd = params.get("command")
        if not cmd:
            return "shell: missing 'command'."
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=60
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        result = ""
        if out:
            result += f"OUTPUT:\n{out}\n"
        if err:
            result += f"ERROR:\n{err}\n"
        if not result:
            result = "Command finished with no output."
        return result

    def _open_url(self, params: Dict[str, Any]) -> str:
        url = params.get("url")
        if not url:
            return "open_url: missing 'url'."
        webbrowser.open(url)
        return f"Opened URL: {url}"

    def _type_text(self, params: Dict[str, Any]) -> str:
        text = params.get("text", "")
        if not text:
            return "type_text: empty text."
        pyautogui.typewrite(text, interval=0.02)
        return "Typed requested text."

    def _keypress(self, params: Dict[str, Any]) -> str:
        key = params.get("key")
        if not key:
            return "keypress: missing 'key'."
        pyautogui.press(key)
        return f"Pressed key: {key}"

    def _key_hold(self, params: Dict[str, Any]) -> str:
        key = params.get("key")
        duration = float(params.get("duration", 1.0))
        if not key:
            return "key_hold: missing 'key'."
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)
        return f"Held key '{key}' for {duration} seconds."

    def _hotkey(self, params: Dict[str, Any]) -> str:
        keys = params.get("keys") or []
        if not keys:
            return "hotkey: missing 'keys'."
        pyautogui.hotkey(*keys)
        return f"Pressed hotkey: {' + '.join(keys)}"

    def _mouse_move(self, params: Dict[str, Any]) -> str:
        try:
            x = int(params.get("x"))
            y = int(params.get("y"))
        except (TypeError, ValueError):
            return "mouse_move: invalid x/y."
        duration = float(params.get("duration", 0.5))
        pyautogui.moveTo(x, y, duration=duration)
        return f"Moved mouse to ({x}, {y}) over {duration}s."

    def _mouse_click(self, params: Dict[str, Any]) -> str:
        button = params.get("button", "left")
        clicks = int(params.get("clicks", 1))
        interval = float(params.get("interval", 0.05))
        pyautogui.click(button=button, clicks=clicks, interval=interval)
        return f"Clicked {button} {clicks} time(s)."

    def _mouse_drag(self, params: Dict[str, Any]) -> str:
        try:
            sx = int(params.get("start_x"))
            sy = int(params.get("start_y"))
            ex = int(params.get("end_x"))
            ey = int(params.get("end_y"))
        except (TypeError, ValueError):
            return "mouse_drag: invalid coordinates."
        duration = float(params.get("duration", 0.5))
        button = params.get("button", "left")
        pyautogui.moveTo(sx, sy, duration=0.1)
        pyautogui.mouseDown(button=button)
        pyautogui.moveTo(ex, ey, duration=duration)
        pyautogui.mouseUp(button=button)
        return f"Dragged mouse from ({sx},{sy}) to ({ex},{ey}) with button {button}."

    def _mouse_scroll(self, params: Dict[str, Any]) -> str:
        amount = int(params.get("amount", -500))
        pyautogui.scroll(amount)
        return f"Scrolled by {amount}."

    # Web
    def _http_get(self, params: Dict[str, Any]) -> str:
        url = params.get("url")
        if not url:
            return "http_get: missing 'url'."
        resp = requests.get(url, timeout=30)
        text = resp.text[:1000]
        return f"HTTP GET {url} → status {resp.status_code}\nBody (first 1000 chars):\n{text}"

    def _http_post(self, params: Dict[str, Any]) -> str:
        url = params.get("url")
        body = params.get("json", {})
        if not url:
            return "http_post: missing 'url'."
        resp = requests.post(url, json=body, timeout=30)
        text = resp.text[:1000]
        return f"HTTP POST {url} → status {resp.status_code}\nBody (first 1000 chars):\n{text}"

    # Search / FS
    def _find_and_click(self, params: Dict[str, Any]) -> str:
        template_name = params.get("template_name")
        if not template_name:
            return "find_and_click: missing 'template_name'."

        template_path = f"{template_name}.png"
        if not os.path.exists(template_path):
            return f"find_and_click: template file not found: {template_path}"

        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[1])
        screen = np.array(shot)
        screen = cv2.cvtColor(screen, cv2.COLOR_BGRA2BGR)

        template = cv2.imread(template_path, cv2.IMREAD_COLOR)
        if template is None:
            return f"find_and_click: cannot read template image: {template_path}"

        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        if max_val < 0.7:
            return f"find_and_click: no good match found (score={max_val:.2f})."

        th, tw = template.shape[:2]
        center_x = max_loc[0] + tw // 2
        center_y = max_loc[1] + th // 2

        pyautogui.moveTo(center_x, center_y, duration=0.3)
        pyautogui.click()
        return f"Clicked on template '{template_name}' at ({center_x}, {center_y}) with score {max_val:.2f}."

    def _list_dir(self, params: Dict[str, Any]) -> str:
        path = params.get("path", ".")
        try:
            entries = os.listdir(path)
        except Exception as e:
            return f"list_dir error for '{path}': {e}"
        entries = entries[:100]
        return f"Directory listing for {path} (first 100 entries):\n" + "\n".join(entries)

    def _read_file_snippet(self, params: Dict[str, Any]) -> str:
        path = params.get("path")
        max_chars = int(params.get("max_chars", 1000))
        if not path:
            return "read_file_snippet: missing 'path'."
        if max_chars <= 0:
            max_chars = 1000
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read(max_chars)
        except Exception as e:
            return f"read_file_snippet error for '{path}': {e}"
        return f"File snippet ({path}, first {max_chars} chars):\n{text}"


# -------- Voice IO --------
class VoiceIO:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.tts = pyttsx3.init()
        rate = self.tts.getProperty("rate")
        self.tts.setProperty("rate", int(rate * 0.9))

    def speak(self, text: str):
        print(Fore.CYAN + f"V3 (voice): {text}" + Style.RESET_ALL)
        self.tts.say(text)
        self.tts.runAndWait()

    def listen_bangla(
        self, timeout: int = 7, phrase_time_limit: int = 12
    ) -> Optional[str]:
        if main_stop_event.is_set():
            return None
        with sr.Microphone() as source:
            print(Fore.YELLOW + "Listening... বলুন:" + Style.RESET_ALL)
            self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
            try:
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )
            except sr.WaitTimeoutError:
                print("No speech detected.")
                return None

        try:
            text = self.recognizer.recognize_google(audio, language="bn-BD")
            print(Fore.GREEN + f"You (voice): {text}" + Style.RESET_ALL)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None


# -------- Tkinter GUI with chat --------
class V3GUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("V3 Assistant")
        self.root.geometry("480x360")
        self.root.resizable(False, False)

        self.vision_var: BooleanVar = BooleanVar(value=True)

        self.status = tk.Label(root, text="Last signal: NONE (0.00)", justify="left")
        self.status.pack(pady=2, anchor="w")

        self.vision_chk = tk.Checkbutton(
            root,
            text="Use Screen Vision (ROI)",
            variable=self.vision_var,
            command=self._on_vision_toggle,
        )
        self.vision_chk.pack(pady=2, anchor="w")

        self.chat_log = scrolledtext.ScrolledText(root, state="disabled", height=12)
        self.chat_log.pack(fill="both", expand=True, padx=5, pady=5)

        bottom = tk.Frame(root)
        bottom.pack(fill="x", padx=5, pady=5)

        self.entry = tk.Entry(bottom)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._on_send)

        send_btn = tk.Button(bottom, text="Send", command=self._on_send)
        send_btn.pack(side="left", padx=5)

        stop_button = tk.Button(
            root, text="Stop V3", command=self.stop_all, bg="#ff5555", fg="white"
        )
        stop_button.pack(pady=4)

        self._tick()

    def append_chat(self, who: str, text: str):
        self.chat_log.config(state="normal")
        self.chat_log.insert("end", f"{who}: {text}\n")
        self.chat_log.see("end")
        self.chat_log.config(state="disabled")

    def update_status(self, signal: str, confidence: float):
        self.status.config(text=f"Last signal: {signal} ({confidence:.2f})")

    def _on_send(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.append_chat("You", text)
        try:
            chat_queue.put_nowait(text)
        except Exception:
            pass

    def _on_vision_toggle(self):
        global vision_enabled
        vision_enabled = bool(self.vision_var.get())

    def stop_all(self):
        main_stop_event.set()
        capture_stop_event.set()
        self.root.after(100, self.root.destroy)

    def _tick(self):
        if kill_switch_triggered():
            main_stop_event.set()
            capture_stop_event.set()
            self.root.after(100, self.root.destroy)
            return
        if not main_stop_event.is_set():
            self.root.after(200, self._tick)
        else:
            self.root.after(100, self.root.destroy)


# -------- Shared turn handler --------
def handle_user_turn(
    user_text: str,
    client: DeepSeekClient,
    executor: V3Executor,
    voice: VoiceIO,
    gui: Optional[V3GUI],
):
    global latest_roi_image_b64

    low = user_text.strip().lower()
    if any(word in low for word in ["bondho", "bandho", "exit", "quit", " বন্ধ "]):
        voice.speak("Thik ache, ami bondho hocchi.")
        main_stop_event.set()
        return

    user_marked_risky = any(
        kw in low for kw in ["final", "no confirmation", "ঝুঁকিপূর্ণ", "risky"]
    )

    had_image = latest_roi_image_b64 is not None and vision_enabled

    try:
        plan = client.ask(user_text)
    except Exception as e:
        print(Fore.RED + f"[DeepSeek error] {e}" + Style.RESET_ALL)
        voice.speak("DeepSeek theke response pete problem holo.")
        return

    memory.add(user_text, plan, had_image)

    print(Fore.MAGENTA + "\n[PLAN JSON]")
    print(json.dumps(plan, indent=2))
    print(Style.RESET_ALL)

    signal = plan.get("signal", "NONE")
    confidence = float(plan.get("confidence", 0.0))
    reason = plan.get("reason", "")
    thinking = plan.get("thinking", "")
    is_risky = bool(plan.get("is_risky", False))
    needs_clar = bool(plan.get("needs_clarification", False))
    clar_q = plan.get("clarification_question", "") or ""
    actions = plan.get("actions", []) or []

    if gui is not None:
        gui.update_status(signal, confidence)
        gui.append_chat("V3-plan", f"{signal} ({confidence:.2f}): {reason}")

    voice.speak(f"Signal: {signal}, confidence: {confidence:.2f}. Karon: {reason}.")
    if thinking:
        voice.speak(f"Amar chinta dhara holo: {thinking[:200]}")

    if needs_clar and clar_q.strip() and not main_stop_event.is_set():
        voice.speak(clar_q)
        clar_answer = voice.listen_bangla(timeout=8, phrase_time_limit=10)
        if clar_answer:
            if gui is not None:
                gui.append_chat("You-clar", clar_answer)
            clar_text = f"{user_text}\nClarification answer: {clar_answer}"
            try:
                plan = client.ask(clar_text)
                memory.add(clar_text, plan, had_image)
                print(
                    Fore.MAGENTA
                    + "\n[UPDATED PLAN JSON AFTER CLARIFICATION]"
                )
                print(json.dumps(plan, indent=2))
                print(Style.RESET_ALL)
                signal = plan.get("signal", "NONE")
                confidence = float(plan.get("confidence", 0.0))
                reason = plan.get("reason", "")
                thinking = plan.get("thinking", "")
                is_risky = bool(plan.get("is_risky", False))
                actions = plan.get("actions", []) or []
                if gui is not None:
                    gui.update_status(signal, confidence)
                    gui.append_chat(
                        "V3-plan",
                        f"UPDATED {signal} ({confidence:.2f}): {reason}",
                    )
                voice.speak(
                    f"Update hoye gelo. New signal: {signal}, confidence: {confidence:.2f}."
                )
            except Exception as e:
                print(Fore.RED + f"[DeepSeek error after clar] {e}" + Style.RESET_ALL)
                voice.speak("Clarification er pore plan nite problem holo.")
                return

    strong_trade = (
        confidence > 0.85
        and any(a.get("action") in {"mouse_click", "mouse_drag", "http_post"} for a in actions)
    )

    skip_confirmation = is_risky and user_marked_risky

    if skip_confirmation:
        voice.speak(
            "Tumi eti final/risky bolecho, tai ami kono extra confirmation chara execute korchi."
        )
        confirmed = True
    else:
        if strong_trade:
            voice.speak("Ami ekta strong trading signal peyechi. Aage barabo?")
        else:
            voice.speak("Ei plan execute korbo? Yes bolle korbo, no bolle na.")

        confirm_text = voice.listen_bangla(timeout=5, phrase_time_limit=4)
        confirmed = False
        if confirm_text:
            ct = confirm_text.lower()
            if any(x in ct for x in ["yes", "ha", "haan", "হ্যা", "হ্যাঁ"]):
                confirmed = True
            elif any(x in ct for x in ["no", "na", "না"]):
                confirmed = False

        if not confirmed and not main_stop_event.is_set():
            ans = input(
                Fore.YELLOW + "Execute plan? (y/n, s = show JSON again): " + Style.RESET_ALL
            ).strip().lower()
            if ans == "s":
                print(json.dumps(plan, indent=2))
                ans = input("Execute now? (y/n): ").strip().lower()
            confirmed = ans == "y"

    if not confirmed or main_stop_event.is_set():
        voice.speak("Thik ache, ei action cancel kore dilam.")
        return

    result = executor.execute_plan(plan)
    print(Fore.CYAN + "RESULT:\n" + result + "\n" + Style.RESET_ALL)
    if gui is not None:
        gui.append_chat("V3-result", result[:800])

    if not main_stop_event.is_set():
        voice.speak("Kaj sesh. Ar kichu korte bolben?")


# -------- Conversation worker (voice + chat) --------
def conversation_worker(gui: Optional[V3GUI]):
    # API key directly embedded (as requested)
    api_key = "sk-d19c2fc0c45249358b4965fa413314d4"
    client = DeepSeekClient(api_key, memory)
    executor = V3Executor()
    voice = VoiceIO()

    voice.speak(
        "Ami V3. ROI select kore trading screen show korun, tarpor Bangla-English mix e kotha bolun."
    )

    print("\nPress ENTER in console to select trading chart ROI (or skip for full screen).")
    try:
        input()
        select_roi_once()
    except EOFError:
        pass

    while not main_stop_event.is_set():
        text_from_chat = None
        try:
            text_from_chat = chat_queue.get_nowait()
        except Empty:
            pass

        if text_from_chat:
            handle_user_turn(text_from_chat, client, executor, voice, gui)
            continue

        user = voice.listen_bangla()
        if not user:
            continue
        if gui is not None:
            gui.append_chat("You-voice", user)
        handle_user_turn(user, client, executor, voice, gui)


# -------- MAIN ENTRY --------
def main():
    colorama_init(autoreset=True)
    pyautogui.FAILSAFE = True

    cap_thread = threading.Thread(
        target=screen_capture_worker, args=(1.0,), daemon=True
    )
    cap_thread.start()

    root = tk.Tk()
    gui = V3GUI(root)

    conv_thread = threading.Thread(
        target=conversation_worker, args=(gui,), daemon=True
    )
    conv_thread.start()

    root.mainloop()

    main_stop_event.set()
    capture_stop_event.set()
    conv_thread.join(timeout=2.0)


if __name__ == "__main__":
    main()