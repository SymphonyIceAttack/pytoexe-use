# -*- coding: utf-8 -*-
"""
سیم لوک (SimLoc)
یک محیط لوکال هاست شبیه XAMPP با رابط کاربری آبی مدرن
ساخته شده توسط محمد حسین رضی
"""

import os
import sys
import queue
import shutil
import socket
import threading
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_NAME = "سیم لوک"
APP_NAME_EN = "SimLoc"
AUTHOR_LINE = "ساخته شده توسط سیملانگ استودیو"
DEFAULT_PORT = 8080

# ---------- رنگ‌بندی آبی مدرن ----------
COLOR_BG = "#0F1B2D"          # پس‌زمینه تیره آبی
COLOR_PANEL = "#16233B"       # پنل‌ها
COLOR_PANEL_LIGHT = "#1C2C4A"
COLOR_ACCENT = "#2E8BFF"      # آبی روشن اصلی
COLOR_ACCENT_DARK = "#1565C0"
COLOR_TEXT = "#EAF2FF"
COLOR_TEXT_MUTED = "#8FA6C9"
COLOR_GREEN = "#22C55E"
COLOR_RED = "#EF4444"
COLOR_LOG_BG = "#0A1424"


def resource_path(relative):
    """مسیر صحیح فایل چه در حالت اجرای عادی چه در حالت exe ساخته‌شده با PyInstaller"""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative)


def find_executable(names):
    """جستجوی یک برنامه در PATH سیستم از بین چند نام احتمالی"""
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return None


def is_port_free(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect((host, port))
            return False  # پورت اشغال است چون توانستیم وصل شویم
        except Exception:
            return True


class ServiceRunner:
    """اجرای یک سرویس (مثل سرور PHP یا وب‌سرور استاتیک) به صورت پروسه جدا و خواندن خروجی آن"""

    def __init__(self, name, log_queue):
        self.name = name
        self.process = None
        self.thread = None
        self.log_queue = log_queue
        self.running = False

    def start(self, cmd, cwd=None):
        if self.running:
            return
        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW
            self.process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )
        except FileNotFoundError as e:
            self.log_queue.put(f"[{self.name}] خطا: برنامه اجرایی پیدا نشد ({e})")
            return
        except Exception as e:
            self.log_queue.put(f"[{self.name}] خطا در اجرا: {e}")
            return

        self.running = True
        self.log_queue.put(f"[{self.name}] سرویس آغاز شد.")
        self.thread = threading.Thread(target=self._read_output, daemon=True)
        self.thread.start()

    def _read_output(self):
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            self.log_queue.put(f"[{self.name}] {line.rstrip()}")
        self.running = False
        self.log_queue.put(f"[{self.name}] سرویس متوقف شد.")

    def stop(self):
        if self.process and self.running:
            try:
                self.process.terminate()
            except Exception:
                pass
        self.running = False


class SimLocApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - SimLoc")
        self.root.geometry("880x620")
        self.root.minsize(760, 560)
        self.root.configure(bg=COLOR_BG)

        self.log_queue = queue.Queue()
        self.web_service = ServiceRunner("وب‌سرور", self.log_queue)
        self.www_dir = tk.StringVar(value=resource_path("www"))
        self.port_var = tk.StringVar(value=str(DEFAULT_PORT))
        self.status_text = tk.StringVar(value="متوقف")
        self.mysql_status_text = tk.StringVar(value="نامشخص")

        os.makedirs(self.www_dir.get(), exist_ok=True)
        self._ensure_sample_site()

        self._setup_style()
        self._build_ui()
        self._poll_log_queue()

    # ---------------------------------------------------------------- UI
    def _setup_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)

        style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                         font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MUTED,
                         font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT,
                         font=("Segoe UI", 11, "bold"))
        style.configure("PanelMuted.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT_MUTED,
                         font=("Segoe UI", 9))
        style.configure("Status.TLabel", background=COLOR_PANEL, foreground=COLOR_GREEN,
                         font=("Segoe UI", 11, "bold"))
        style.configure("Footer.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MUTED,
                         font=("Segoe UI", 9))

        style.configure("Accent.TButton", background=COLOR_ACCENT, foreground="white",
                         font=("Segoe UI", 10, "bold"), padding=8, borderwidth=0)
        style.map("Accent.TButton",
                  background=[("active", COLOR_ACCENT_DARK), ("disabled", "#3A4A66")])

        style.configure("Ghost.TButton", background=COLOR_PANEL_LIGHT, foreground=COLOR_TEXT,
                         font=("Segoe UI", 9), padding=6, borderwidth=0)
        style.map("Ghost.TButton", background=[("active", COLOR_ACCENT_DARK)])

        style.configure("Danger.TButton", background=COLOR_RED, foreground="white",
                         font=("Segoe UI", 10, "bold"), padding=8, borderwidth=0)
        style.map("Danger.TButton", background=[("active", "#B91C1C")])

        style.configure("Blue.TEntry", fieldbackground=COLOR_PANEL_LIGHT, foreground=COLOR_TEXT,
                         insertcolor=COLOR_TEXT, borderwidth=0)

    def _build_ui(self):
        # ------- هدر -------
        header = ttk.Frame(self.root, style="TFrame", padding=(24, 20, 24, 10))
        header.pack(fill="x")

        ttk.Label(header, text=f"{APP_NAME}  (SimLoc)", style="Title.TLabel").pack(anchor="e")
        ttk.Label(header, text="محیط لوکال هاست اینترنت، مشابه XAMPP", style="Subtitle.TLabel").pack(anchor="e")

        # ------- پنل اصلی سرویس‌ها -------
        body = ttk.Frame(self.root, style="TFrame", padding=(24, 10))
        body.pack(fill="both", expand=True)

        web_panel = ttk.Frame(body, style="Panel.TFrame", padding=18)
        web_panel.pack(fill="x", pady=(0, 14))
        self._build_web_panel(web_panel)

        mysql_panel = ttk.Frame(body, style="Panel.TFrame", padding=18)
        mysql_panel.pack(fill="x", pady=(0, 14))
        self._build_mysql_panel(mysql_panel)

        log_panel = ttk.Frame(body, style="Panel.TFrame", padding=(14, 10))
        log_panel.pack(fill="both", expand=True)
        self._build_log_panel(log_panel)

        # ------- فوتر -------
        footer = ttk.Frame(self.root, style="TFrame", padding=(24, 6, 24, 14))
        footer.pack(fill="x")
        ttk.Label(footer, text=AUTHOR_LINE, style="Footer.TLabel").pack(anchor="e")

    def _build_web_panel(self, parent):
        top = ttk.Frame(parent, style="Panel.TFrame")
        top.pack(fill="x")

        ttk.Label(top, text="وب‌سرور محلی (Apache / PHP)", style="Panel.TLabel").pack(side="right")
        self.web_status_lbl = ttk.Label(top, textvariable=self.status_text, style="Status.TLabel")
        self.web_status_lbl.pack(side="left")

        row1 = ttk.Frame(parent, style="Panel.TFrame")
        row1.pack(fill="x", pady=(14, 6))

        ttk.Label(row1, text="پوشه سایت (www):", style="PanelMuted.TLabel").pack(side="right", padx=(0, 8))
        entry = ttk.Entry(row1, textvariable=self.www_dir, style="Blue.TEntry", justify="left")
        entry.pack(side="right", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row1, text="انتخاب پوشه...", style="Ghost.TButton",
                   command=self._choose_folder).pack(side="right")

        row2 = ttk.Frame(parent, style="Panel.TFrame")
        row2.pack(fill="x", pady=6)
        ttk.Label(row2, text="پورت:", style="PanelMuted.TLabel").pack(side="right", padx=(0, 8))
        port_entry = ttk.Entry(row2, textvariable=self.port_var, style="Blue.TEntry", width=8, justify="center")
        port_entry.pack(side="right")

        row3 = ttk.Frame(parent, style="Panel.TFrame")
        row3.pack(fill="x", pady=(14, 0))

        self.start_btn = ttk.Button(row3, text="▶  شروع سرور", style="Accent.TButton",
                                     command=self._start_web_server)
        self.start_btn.pack(side="right", padx=(0, 8))

        self.stop_btn = ttk.Button(row3, text="■  توقف سرور", style="Danger.TButton",
                                    command=self._stop_web_server, state="disabled")
        self.stop_btn.pack(side="right", padx=(0, 8))

        ttk.Button(row3, text="باز کردن در مرورگر", style="Ghost.TButton",
                   command=self._open_browser).pack(side="right", padx=(0, 8))

        ttk.Button(row3, text="باز کردن پوشه سایت", style="Ghost.TButton",
                   command=self._open_www_folder).pack(side="right")

    def _build_mysql_panel(self, parent):
        top = ttk.Frame(parent, style="Panel.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="پایگاه داده (MySQL / MariaDB)", style="Panel.TLabel").pack(side="right")
        ttk.Label(top, textvariable=self.mysql_status_text, style="PanelMuted.TLabel").pack(side="left")

        note = ttk.Label(
            parent,
            text="در صورت نصب بودن MySQL یا MariaDB روی سیستم، می‌توانید سرویس آن را از این‌جا مدیریت کنید.",
            style="PanelMuted.TLabel", wraplength=760, justify="right",
        )
        note.pack(fill="x", pady=(10, 10), anchor="e")

        row = ttk.Frame(parent, style="Panel.TFrame")
        row.pack(fill="x")
        ttk.Button(row, text="▶  شروع MySQL", style="Accent.TButton",
                   command=lambda: self._mysql_control("start")).pack(side="right", padx=(0, 8))
        ttk.Button(row, text="■  توقف MySQL", style="Danger.TButton",
                   command=lambda: self._mysql_control("stop")).pack(side="right", padx=(0, 8))
        ttk.Button(row, text="بررسی وضعیت", style="Ghost.TButton",
                   command=self._check_mysql_status).pack(side="right")

    def _build_log_panel(self, parent):
        ttk.Label(parent, text="گزارش رویدادها", style="Panel.TLabel").pack(anchor="e", pady=(0, 6))
        self.log_text = tk.Text(
            parent, height=10, bg=COLOR_LOG_BG, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
            relief="flat", wrap="word", font=("Consolas", 9),
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        self._log(f"{APP_NAME} آماده است. {AUTHOR_LINE}")

    # ------------------------------------------------------------ منطق
    def _ensure_sample_site(self):
        index_path = os.path.join(self.www_dir.get(), "index.php")
        if not os.path.exists(index_path):
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(
                    "<!DOCTYPE html>\n<html lang=\"fa\" dir=\"rtl\">\n<head>\n"
                    "<meta charset=\"utf-8\"><title>سیم لوک</title></head>\n<body "
                    "style=\"font-family:Tahoma;background:#0F1B2D;color:#EAF2FF;"
                    "text-align:center;padding-top:80px\">\n"
                    "<h1>سیم لوک با موفقیت اجرا شد!</h1>\n"
                    "<p>ساخته شده توسط سیملانگ استودیو</p>\n"
                    "<p>PHP نسخه: <?php echo phpversion(); ?></p>\n</body></html>\n"
                )

    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.www_dir.get())
        if folder:
            self.www_dir.set(folder)

    def _open_www_folder(self):
        path = self.www_dir.get()
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            self._log(f"خطا در باز کردن پوشه: {e}")

    def _open_browser(self):
        port = self.port_var.get().strip() or str(DEFAULT_PORT)
        webbrowser.open(f"http://localhost:{port}/")

    def _start_web_server(self):
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            messagebox.showerror(APP_NAME, "شماره پورت نامعتبر است.")
            return

        if not is_port_free(port):
            messagebox.showwarning(APP_NAME, f"پورت {port} در حال حاضر مشغول است.")
            return

        www = self.www_dir.get()
        os.makedirs(www, exist_ok=True)

        php_path = find_executable(["php", "php.exe"])
        if php_path:
            cmd = [php_path, "-S", f"127.0.0.1:{port}", "-t", www]
            self._log("سرور توسعه PHP یافت شد؛ در حال اجرا با پشتیبانی کامل PHP.")
        else:
            cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1",
                   "--directory", www]
            self._log("PHP روی سیستم یافت نشد؛ اجرا با سرور استاتیک پایتون (بدون اجرای PHP).")

        self.web_service.start(cmd, cwd=www)
        self.status_text.set("در حال اجرا")
        self.web_status_lbl.configure(foreground=COLOR_GREEN)
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def _stop_web_server(self):
        self.web_service.stop()
        self.status_text.set("متوقف")
        self.web_status_lbl.configure(foreground=COLOR_RED)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _mysql_control(self, action):
        service_names = ["MySQL", "MySQL80", "MariaDB"]
        if os.name != "nt":
            self._log("مدیریت مستقیم سرویس MySQL فقط روی ویندوز پشتیبانی می‌شود.")
            return
        for name in service_names:
            try:
                result = subprocess.run(
                    ["sc", "query", name], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    verb = "start" if action == "start" else "stop"
                    subprocess.run(["net", verb, name], capture_output=True, text=True, timeout=15)
                    self._log(f"دستور {action} برای سرویس {name} ارسال شد.")
                    self._check_mysql_status()
                    return
            except Exception as e:
                self._log(f"خطا در بررسی سرویس {name}: {e}")
        self._log("هیچ سرویس MySQL/MariaDB نصب‌شده‌ای روی سیستم پیدا نشد.")

    def _check_mysql_status(self):
        if os.name != "nt":
            self.mysql_status_text.set("فقط در ویندوز قابل بررسی است")
            return
        for name in ["MySQL", "MySQL80", "MariaDB"]:
            try:
                result = subprocess.run(["sc", "query", name], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    running = "RUNNING" in result.stdout
                    self.mysql_status_text.set(f"{name}: {'در حال اجرا' if running else 'متوقف'}")
                    return
            except Exception:
                continue
        self.mysql_status_text.set("یافت نشد")

    def _log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self._log(msg)
        except queue.Empty:
            pass
        self.root.after(200, self._poll_log_queue)

    def on_close(self):
        self.web_service.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SimLocApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
