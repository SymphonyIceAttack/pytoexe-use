"""
Raw Input Buffer for Windows

Single-file source. Build on Windows with:
    py -m pip install pystray pynput pillow pyinstaller
    pyinstaller --onefile --noconsole --name RawInputBuffer raw_input_buffer.py

This utility records local activity metadata only. It does not inject/replay input,
transmit data, or record printable key text. Pause it before handling sensitive work.
"""

from __future__ import annotations

import json
import os
import queue
import threading
import time
import tkinter as tk
from collections import deque
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import pystray
    from PIL import Image, ImageDraw
    from pynput import keyboard, mouse
except ImportError as exc:
    raise SystemExit(
        "Missing dependency. Install with: py -m pip install pystray pynput pillow"
    ) from exc

APP_NAME = "Raw Input Buffer"
MAX_EVENTS = 2000


class RawInputBuffer:
    def __init__(self) -> None:
        self.events: deque[dict] = deque(maxlen=MAX_EVENTS)
        self.lock = threading.Lock()
        self.paused = False
        self.running = True
        self.ui_queue: queue.Queue[str] = queue.Queue()
        self.root: tk.Tk | None = None
        self.tray: pystray.Icon | None = None
        self.keyboard_listener: keyboard.Listener | None = None
        self.mouse_listener: mouse.Listener | None = None

    def add(self, kind: str, detail: str) -> None:
        if self.paused or not self.running:
            return
        item = {
            "time": datetime.now().astimezone().isoformat(timespec="milliseconds"),
            "type": kind,
            "detail": detail,
        }
        with self.lock:
            self.events.append(item)
        self.ui_queue.put("refresh")

    @staticmethod
    def key_label(key) -> str:
        # Deliberately avoid recording printable characters or text content.
        if isinstance(key, keyboard.KeyCode):
            return "printable-key"
        return getattr(key, "name", str(key).replace("Key.", ""))

    def on_key_press(self, key) -> None:
        self.add("keyboard", f"down:{self.key_label(key)}")

    def on_key_release(self, key) -> None:
        self.add("keyboard", f"up:{self.key_label(key)}")

    def on_move(self, x: int, y: int) -> None:
        self.add("mouse", f"move:{x},{y}")

    def on_click(self, x: int, y: int, button, pressed: bool) -> None:
        name = getattr(button, "name", str(button))
        self.add("mouse", f"{'down' if pressed else 'up'}:{name}@{x},{y}")

    def on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self.add("mouse", f"scroll:{dx},{dy}@{x},{y}")

    def clear(self) -> None:
        with self.lock:
            self.events.clear()
        self.ui_queue.put("refresh")

    def snapshot(self) -> list[dict]:
        with self.lock:
            return list(self.events)

    def export(self) -> None:
        if self.root is None:
            return
        destination = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export input buffer",
            defaultextension=".jsonl",
            filetypes=[("JSON Lines", "*.jsonl"), ("Text", "*.txt")],
        )
        if not destination:
            return
        try:
            with open(destination, "w", encoding="utf-8") as handle:
                for item in self.snapshot():
                    handle.write(json.dumps(item, ensure_ascii=False) + "\n")
            messagebox.showinfo(APP_NAME, f"Exported {len(self.snapshot())} events.", parent=self.root)
        except OSError as exc:
            messagebox.showerror(APP_NAME, str(exc), parent=self.root)

    def show_window(self) -> None:
        if self.root is None:
            return
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.refresh_window()

    def refresh_window(self) -> None:
        if self.root is None or not self.root.winfo_exists():
            return
        text = self.root.event_text
        text.delete("1.0", tk.END)
        for item in self.snapshot()[-500:]:
            text.insert(tk.END, f"{item['time']}  {item['type']:<8} {item['detail']}\n")
        status = "PAUSED" if self.paused else "RECORDING"
        self.root.status_var.set(f"{status} | {len(self.snapshot())}/{MAX_EVENTS} events")

    def build_window(self) -> None:
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("900x500")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        bar = ttk.Frame(self.root, padding=8)
        bar.pack(fill=tk.X)
        self.root.status_var = tk.StringVar()
        ttk.Label(bar, textvariable=self.root.status_var).pack(side=tk.LEFT)
        ttk.Button(bar, text="Pause/Resume", command=self.toggle_pause).pack(side=tk.RIGHT, padx=3)
        ttk.Button(bar, text="Clear", command=self.clear).pack(side=tk.RIGHT, padx=3)
        ttk.Button(bar, text="Export", command=self.export).pack(side=tk.RIGHT, padx=3)

        frame = ttk.Frame(self.root, padding=(8, 0, 8, 8))
        frame.pack(fill=tk.BOTH, expand=True)
        self.root.event_text = tk.Text(frame, wrap=tk.NONE, state=tk.NORMAL)
        scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.root.event_text.yview)
        self.root.event_text.configure(yscrollcommand=scroll.set)
        self.root.event_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.refresh_window()
        self.root.withdraw()
        self.root.after(250, self.process_queue)

    def process_queue(self) -> None:
        if self.root is None or not self.root.winfo_exists():
            return
        try:
            while True:
                self.ui_queue.get_nowait()
        except queue.Empty:
            pass
        self.refresh_window()
        self.root.after(250, self.process_queue)

    def hide_window(self) -> None:
        if self.root:
            self.root.withdraw()

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        self.refresh_window()
        self.update_tray_menu()

    def update_tray_menu(self) -> None:
        if self.tray:
            self.tray.menu = self.make_menu()

    def make_menu(self):
        return pystray.Menu(
            pystray.MenuItem("Open buffer", lambda: self.show_window()),
            pystray.MenuItem("Pause recording" if not self.paused else "Resume recording", lambda: self.toggle_pause()),
            pystray.MenuItem("Clear buffer", lambda: self.clear()),
            pystray.MenuItem("Exit", lambda: self.shutdown()),
        )

    def icon_image(self):
        image = Image.new("RGBA", (64, 64), (30, 90, 160, 255))
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((10, 10, 54, 54), radius=8, fill=(245, 245, 245, 255))
        draw.rectangle((18, 20, 46, 25), fill=(30, 90, 160, 255))
        draw.rectangle((18, 30, 46, 35), fill=(30, 90, 160, 255))
        draw.rectangle((18, 40, 38, 45), fill=(30, 90, 160, 255))
        return image

    def start_listeners(self) -> None:
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.mouse_listener = mouse.Listener(on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll)
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def enable_startup(self) -> None:
        # Startup is enabled by placing a shortcut or executable in the user's
        # Startup folder; this menu action is intentionally omitted from the
        # single-file runtime to avoid silently changing system settings.
        pass

    def shutdown(self) -> None:
        self.running = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.tray:
            self.tray.stop()
        if self.root:
            self.root.quit()

    def run(self) -> None:
        self.build_window()
        self.start_listeners()
        self.tray = pystray.Icon(APP_NAME, self.icon_image(), APP_NAME, self.make_menu())
        tray_thread = threading.Thread(target=self.tray.run, daemon=True)
        tray_thread.start()
        assert self.root is not None
        self.root.mainloop()


if __name__ == "__main__":
    RawInputBuffer().run()

# Startup shortcut target (Windows):
# shell:startup -> create a shortcut to RawInputBuffer.exe.
# This explicit step keeps startup behavior visible and user-controlled.
