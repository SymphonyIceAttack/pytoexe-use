#!/usr/bin/env python3
# crash_logger.py
# Simple cross-platform GUI to watch system/application error logs and save entries.
# Usage: python crash_logger.py
# pip install pyinstaller

import sys, os, threading, subprocess, queue, time, shutil, datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

POLL_INTERVAL = 5.0  # seconds (used for polling backends)

class CrashLoggerApp:
    def __init__(self, root):
        self.root = root
        root.title("Crash Logger")
        self.queue = queue.Queue()
        self.running = False
        self.proc = None
        self.seen = set()

        frm = ttk.Frame(root, padding=8)
        frm.pack(fill="both", expand=True)

        toolbar = ttk.Frame(frm)
        toolbar.pack(fill="x", pady=(0,6))
        self.start_btn = ttk.Button(toolbar, text="Start", command=self.start)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(toolbar, text="Stop", command=self.stop, state="disabled")
        self.stop_btn.pack(side="left", padx=(6,0))
        ttk.Button(toolbar, text="Save Log", command=self.save_log).pack(side="left", padx=(6,0))
        ttk.Button(toolbar, text="Clear", command=self.clear).pack(side="left", padx=(6,0))

        self.listbox = tk.Listbox(frm, height=20)
        self.listbox.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(frm, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(fill="y", side="right")
        self.listbox.config(yscrollcommand=scrollbar.set)

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(200, self.process_queue)

    def start(self):
        if self.running:
            return
        self.running = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.seen.clear()
        self.worker_thread = threading.Thread(target=self.reader_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
        except Exception:
            pass

    def clear(self):
        self.listbox.delete(0, tk.END)

    def save_log(self):
        if self.listbox.size() == 0:
            messagebox.showinfo("Save Log", "No entries to save.")
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Text", "*.txt"), ("Log", "*.log"), ("All files", "*.*")])
        if not fpath:
            return
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                for i in range(self.listbox.size()):
                    f.write(self.listbox.get(i) + "\n")
            messagebox.showinfo("Save Log", "Saved to %s" % fpath)
        except Exception as e:
            messagebox.showerror("Save Log", str(e))

    def process_queue(self):
        try:
            while True:
                item = self.queue.get_nowait()
                ts = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
                line = f"[{ts}] {item}"
                if line in self.seen:
                    continue
                self.seen.add(line)
                self.listbox.insert(tk.END, line)
                self.listbox.yview_moveto(1.0)
        except queue.Empty:
            pass
        self.root.after(200, self.process_queue)

    def on_close(self):
        self.stop()
        self.root.quit()

    def reader_loop(self):
        platform = sys.platform
        if platform.startswith("win"):
            self._reader_windows()
        elif platform.startswith("linux"):
            self._reader_journalctl()
        elif platform.startswith("darwin"):
            self._reader_tail("/var/log/system.log")
        else:
            self.queue.put("Unsupported OS: " + platform)

    def _reader_windows(self):
        # Prefer wevtutil if available; fallback to polling no-op.
        wevtutil = shutil.which("wevtutil")
        if not wevtutil:
            self.queue.put("wevtutil not found. Install Windows components or pywin32.")
            return
        # We'll poll Application channel for errors (Level=2). Use limited fetch to avoid duplicates.
        seen_texts = set()
        while self.running:
            try:
                # Query last 50 error events from Application log
                cmd = [wevtutil, "qe", "Application", "/q:*[System[Level=2]]", "/f:text", "/c:50"]
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
                out, err = p.communicate(timeout=10)
                if out:
                    entries = [e.strip() for e in out.split("\n\n") if e.strip()]
                    for e in entries:
                        key = e.splitlines()[0] if e.splitlines() else e
                        if key not in seen_texts:
                            seen_texts.add(key)
                            # shorten to first lines for list display
                            summary = key
                            self.queue.put("Windows Error: " + summary)
                time.sleep(POLL_INTERVAL)
            except subprocess.TimeoutExpired:
                p.kill()
            except Exception as ex:
                self.queue.put("Windows reader error: " + str(ex))
                time.sleep(POLL_INTERVAL)

    def _reader_journalctl(self):
        journalctl = shutil.which("journalctl")
        if not journalctl:
            # fallback to syslog file
            candidates = ["/var/log/syslog", "/var/log/messages"]
            for c in candidates:
                if os.path.exists(c):
                    return self._reader_tail(c)
            self.queue.put("journalctl not found and no syslog file available.")
            return
        # Follow journalctl for priority err and higher
        cmd = [journalctl, "-f", "-o", "short-iso", "-p", "err"]
        try:
            self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
            for line in self.proc.stdout:
                if not self.running:
                    break
                line = line.strip()
                if line:
                    self.queue.put("journalctl: " + line)
        except Exception as ex:
            self.queue.put("journalctl reader error: " + str(ex))
        finally:
            try:
                if self.proc and self.proc.poll() is None:
                    self.proc.terminate()
            except Exception:
                pass

    def _reader_tail(self, path):
        # Use tail -F if available, else poll file
        tail = shutil.which("tail")
        if tail:
            cmd = [tail, "-F", path]
            try:
                self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
                for line in self.proc.stdout:
                    if not self.running:
                        break
                    l = line.strip()
                    if l:
                        # crude filter for "crash" keywords
                        if any(k in l.lower() for k in ("crash", "segfault", "fault", "panic", "exception", "error")):
                            self.queue.put(f"{os.path.basename(path)}: {l}")
                return
            except Exception:
                pass
        # fallback: poll file's end
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                while self.running:
                    line = f.readline()
                    if not line:
                        time.sleep(POLL_INTERVAL)
                        continue
                    l = line.strip()
                    if l and any(k in l.lower() for k in ("crash", "segfault", "fault", "panic", "exception", "error")):
                        self.queue.put(f"{os.path.basename(path)}: {l}")
        except Exception as ex:
            self.queue.put("Tail reader error: " + str(ex))


if __name__ == "__main__":
    root = tk.Tk()
    app = CrashLoggerApp(root)
    root.mainloop()