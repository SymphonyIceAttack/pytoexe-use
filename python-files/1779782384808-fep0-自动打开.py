# -*- coding: utf-8 -*-
"""
定时打开网址工具 - 单文件版 v7

功能：
- 默认最大化打开
- 三栏布局：左侧网址列表，中间计划/执行状态，右侧设置和控制
- 自动保存网址和参数，重启后自动恢复
- 每一轮都会把列表里的全部网址打开一遍
- 使用后台 Google Chrome 运行，不弹出电脑浏览器窗口
- 全部网址打开并完成加载检测后，会一起停留指定秒数
- 停留结束后，再一次性关闭全部标签和后台浏览器
- 修复复制/粘贴网址时英文点号 . 被错误移除的问题

提示：
后台 Chrome 需要 Selenium。首次使用时如果未安装，软件会提示自动安装。
"""

import os
import re
import sys
import json
import time
import queue
import shutil
import subprocess
import threading
import importlib
from datetime import datetime, date, timedelta
from urllib.parse import urlparse

import tkinter as tk
from tkinter import ttk, messagebox, filedialog


APP_TITLE = "定时打开网址工具"
APP_VERSION = "v7.0"


class ChromeAutomationError(Exception):
    pass


class UrlSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1360x820")
        self.root.minsize(1180, 700)

        self.urls = []
        self.is_running = False
        self.stop_event = threading.Event()
        self.worker_thread = None
        self.ui_queue = queue.Queue()

        self.next_run_time = None
        self.save_job = None
        self.loading_config = False
        self.config_path = self.get_config_path()

        self.current_round_total = 0
        self.current_round_loaded = 0
        self.current_round_opened = 0

        self.setup_theme()
        self.build_ui()
        self.load_config()
        self.setup_auto_save()
        self.maximize_window()

        self.root.after(200, self.process_ui_queue)
        self.root.after(1000, self.update_countdown)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------- window / config -------------------------

    def maximize_window(self):
        self.root.after(120, self._maximize_window)

    def _maximize_window(self):
        try:
            self.root.state("zoomed")
            return
        except Exception:
            pass
        try:
            self.root.attributes("-zoomed", True)
            return
        except Exception:
            pass
        try:
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        except Exception:
            pass

    def get_config_path(self):
        filename = "url_scheduler_config.json"
        paths = []

        try:
            app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            paths.append(os.path.join(app_dir, filename))
        except Exception:
            pass

        if sys.platform.startswith("win"):
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            paths.append(os.path.join(base, "UrlScheduler", filename))
        else:
            paths.append(os.path.join(os.path.expanduser("~"), ".url_scheduler", filename))

        for path in paths:
            try:
                folder = os.path.dirname(path)
                if folder:
                    os.makedirs(folder, exist_ok=True)
                test_path = path + ".write_test"
                with open(test_path, "w", encoding="utf-8") as f:
                    f.write("ok")
                os.remove(test_path)
                return path
            except Exception:
                continue

        return os.path.join(os.path.expanduser("~"), filename)

    def setup_auto_save(self):
        for var in (
            self.start_time_var,
            self.end_time_var,
            self.daily_rounds_var,
            self.url_interval_var,
            self.load_timeout_var,
            self.stay_seconds_var,
            self.chrome_path_var,
        ):
            var.trace_add("write", lambda *_: self.schedule_save_config())

    def schedule_save_config(self):
        if self.loading_config:
            return
        try:
            if self.save_job is not None:
                self.root.after_cancel(self.save_job)
        except Exception:
            pass
        self.save_job = self.root.after(350, self.save_config)

    def save_config(self):
        self.save_job = None
        data = {
            "version": APP_VERSION,
            "urls": list(self.urls),
            "settings": {
                "start_time": self.start_time_var.get(),
                "end_time": self.end_time_var.get(),
                "daily_rounds": self.daily_rounds_var.get(),
                "url_interval": self.url_interval_var.get(),
                "load_timeout": self.load_timeout_var.get(),
                "stay_seconds": self.stay_seconds_var.get(),
                "chrome_path": self.chrome_path_var.get(),
            },
        }

        try:
            folder = os.path.dirname(self.config_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.config_path)
            self.set_message("已自动保存")
        except Exception:
            self.set_message("自动保存失败，请检查软件目录权限")

    def load_config(self):
        if not os.path.exists(self.config_path):
            return

        self.loading_config = True
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            urls = data.get("urls", [])
            if isinstance(urls, list):
                self.urls = []
                for item in urls:
                    url = self.normalize_url(str(item))
                    if url and self.is_valid_url(url):
                        self.urls.append(url)
                self.refresh_url_list()

            settings = data.get("settings", {})
            if isinstance(settings, dict):
                self.start_time_var.set(str(settings.get("start_time", self.start_time_var.get())))
                self.end_time_var.set(str(settings.get("end_time", self.end_time_var.get())))

                rounds = settings.get("daily_rounds", settings.get("daily_count", self.daily_rounds_var.get()))
                self.daily_rounds_var.set(str(rounds))

                interval = settings.get("url_interval", settings.get("interval", self.url_interval_var.get()))
                self.url_interval_var.set(str(interval))

                self.load_timeout_var.set(str(settings.get("load_timeout", self.load_timeout_var.get())))
                self.stay_seconds_var.set(str(settings.get("stay_seconds", self.stay_seconds_var.get())))
                self.chrome_path_var.set(str(settings.get("chrome_path", self.chrome_path_var.get())))

            self.set_message("已恢复上次保存的网址和参数")
            self.refresh_all_summaries()
        except Exception:
            self.set_message("读取保存配置失败")
        finally:
            self.loading_config = False

    # ------------------------- style / ui -------------------------

    def setup_theme(self):
        self.bg = "#f4f7fb"
        self.card = "#ffffff"
        self.border = "#d8e2ef"
        self.text = "#172033"
        self.muted = "#64748b"
        self.accent = "#0ea5e9"
        self.accent_dark = "#0284c7"
        self.danger = "#ef4444"
        self.danger_dark = "#dc2626"
        self.green = "#16a34a"
        self.orange = "#ea580c"
        self.soft = "#eef6ff"

        self.root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background=self.bg)
        style.configure("Card.TFrame", background=self.card)
        style.configure("TLabel", background=self.bg, foreground=self.text, font=("Microsoft YaHei UI", 10))
        style.configure("Title.TLabel", background=self.bg, foreground=self.text, font=("Microsoft YaHei UI", 21, "bold"))
        style.configure("Card.TLabel", background=self.card, foreground=self.text, font=("Microsoft YaHei UI", 10))
        style.configure("Muted.Card.TLabel", background=self.card, foreground=self.muted, font=("Microsoft YaHei UI", 9))

        style.configure(
            "TEntry",
            fieldbackground="#ffffff",
            foreground=self.text,
            insertcolor=self.text,
            bordercolor=self.border,
            lightcolor=self.border,
            darkcolor=self.border,
            padding=8,
        )
        style.map("TEntry", bordercolor=[("focus", self.accent)])

        style.configure(
            "TButton",
            background="#e8eef7",
            foreground=self.text,
            borderwidth=0,
            focusthickness=0,
            padding=(13, 9),
            font=("Microsoft YaHei UI", 10),
        )
        style.map("TButton", background=[("active", "#dbe7f5"), ("pressed", "#cbd8e8")])

        style.configure(
            "Accent.TButton",
            background=self.accent,
            foreground="#ffffff",
            borderwidth=0,
            padding=(13, 10),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map("Accent.TButton", background=[("active", self.accent_dark), ("pressed", "#0369a1")])

        style.configure(
            "Danger.TButton",
            background=self.danger,
            foreground="#ffffff",
            borderwidth=0,
            padding=(13, 10),
            font=("Microsoft YaHei UI", 10, "bold"),
        )
        style.map("Danger.TButton", background=[("active", self.danger_dark), ("pressed", "#b91c1c")])

        style.configure(
            "Treeview",
            background="#ffffff",
            foreground=self.text,
            fieldbackground="#ffffff",
            bordercolor=self.border,
            rowheight=28,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#edf3fb",
            foreground=self.text,
            relief="flat",
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#d7efff")], foreground=[("selected", "#075985")])

    def create_card(self, parent):
        return tk.Frame(parent, bg=self.card, highlightbackground=self.border, highlightthickness=1)

    def build_ui(self):
        outer = ttk.Frame(self.root)
        outer.pack(fill="both", expand=True, padx=20, pady=18)

        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(header, text=APP_TITLE, style="Title.TLabel").pack(side="left", anchor="w")

        self.top_summary_label = tk.Label(
            header,
            text="",
            bg=self.bg,
            fg=self.muted,
            font=("Microsoft YaHei UI", 10),
            anchor="e",
        )
        self.top_summary_label.pack(side="right", anchor="e")

        grid = ttk.Frame(outer)
        grid.pack(fill="both", expand=True)
        grid.columnconfigure(0, weight=44, uniform="cols")
        grid.columnconfigure(1, weight=34, uniform="cols")
        grid.columnconfigure(2, weight=22, uniform="cols")
        grid.rowconfigure(0, weight=1)

        left_card = self.create_card(grid)
        middle_card = self.create_card(grid)
        right_card = self.create_card(grid)

        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        middle_card.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        right_card.grid(row=0, column=2, sticky="nsew")

        self.build_left_panel(left_card)
        self.build_middle_panel(middle_card)
        self.build_right_panel(right_card)

    def build_left_panel(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame")
        panel.pack(fill="both", expand=True, padx=16, pady=16)

        title_row = ttk.Frame(panel, style="Card.TFrame")
        title_row.pack(fill="x")
        ttk.Label(title_row, text="网址列表", style="Card.TLabel", font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")
        self.url_count_label = ttk.Label(title_row, text="0 个网址", style="Muted.Card.TLabel")
        self.url_count_label.pack(side="right")

        add_row = ttk.Frame(panel, style="Card.TFrame")
        add_row.pack(fill="x", pady=(12, 12))

        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(add_row, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda event: self.add_url())
        self.url_entry.bind("<Control-v>", self.on_paste_url)
        self.url_entry.bind("<Control-V>", self.on_paste_url)
        self.url_entry.bind("<Button-3>", lambda event: self.root.after(100, self.clean_url_entry_after_paste))

        ttk.Button(add_row, text="添加", style="Accent.TButton", command=self.add_url).pack(side="left", padx=(8, 0))

        list_frame = ttk.Frame(panel, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)

        self.url_listbox = tk.Listbox(
            list_frame,
            bg="#ffffff",
            fg=self.text,
            selectbackground="#d7efff",
            selectforeground="#075985",
            activestyle="none",
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.border,
            highlightcolor=self.accent,
            font=("Consolas", 10),
        )
        self.url_listbox.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.url_listbox.yview)
        scroll.pack(side="right", fill="y")
        self.url_listbox.configure(yscrollcommand=scroll.set)

        btn_row = ttk.Frame(panel, style="Card.TFrame")
        btn_row.pack(fill="x", pady=(12, 0))
        for i in range(5):
            btn_row.columnconfigure(i, weight=1)

        ttk.Button(btn_row, text="删除选中", command=self.remove_selected).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(btn_row, text="清空列表", command=self.clear_urls).grid(row=0, column=1, sticky="ew", padx=(0, 6))
        ttk.Button(btn_row, text="导入TXT", command=self.import_txt).grid(row=0, column=2, sticky="ew", padx=(0, 6))
        ttk.Button(btn_row, text="导出TXT", command=self.export_txt).grid(row=0, column=3, sticky="ew", padx=(0, 6))
        ttk.Button(btn_row, text="去重", command=self.deduplicate_urls).grid(row=0, column=4, sticky="ew")

    def build_middle_panel(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame")
        panel.pack(fill="both", expand=True, padx=16, pady=16)
        panel.rowconfigure(1, weight=1)
        panel.rowconfigure(3, weight=2)
        panel.columnconfigure(0, weight=1)

        ttk.Label(panel, text="今日计划", style="Card.TLabel", font=("Microsoft YaHei UI", 13, "bold")).grid(row=0, column=0, sticky="w")

        schedule_frame = ttk.Frame(panel, style="Card.TFrame")
        schedule_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 14))
        schedule_frame.rowconfigure(0, weight=1)
        schedule_frame.columnconfigure(0, weight=1)

        self.schedule_tree = ttk.Treeview(
            schedule_frame,
            columns=("round", "time", "status"),
            show="headings",
            height=8,
        )
        self.schedule_tree.heading("round", text="轮次")
        self.schedule_tree.heading("time", text="时间")
        self.schedule_tree.heading("status", text="状态")
        self.schedule_tree.column("round", width=70, anchor="center", stretch=False)
        self.schedule_tree.column("time", width=150, anchor="center")
        self.schedule_tree.column("status", width=110, anchor="center", stretch=False)
        self.schedule_tree.grid(row=0, column=0, sticky="nsew")

        schedule_scroll = ttk.Scrollbar(schedule_frame, orient="vertical", command=self.schedule_tree.yview)
        schedule_scroll.grid(row=0, column=1, sticky="ns")
        self.schedule_tree.configure(yscrollcommand=schedule_scroll.set)

        exec_title = ttk.Frame(panel, style="Card.TFrame")
        exec_title.grid(row=2, column=0, sticky="ew")
        ttk.Label(exec_title, text="当前轮次：列表全部网址执行状态", style="Card.TLabel", font=("Microsoft YaHei UI", 13, "bold")).pack(side="left")
        self.round_summary_label = ttk.Label(exec_title, text="未执行", style="Muted.Card.TLabel")
        self.round_summary_label.pack(side="right")

        progress_frame = ttk.Frame(panel, style="Card.TFrame")
        progress_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        progress_frame.rowconfigure(0, weight=1)
        progress_frame.columnconfigure(0, weight=1)

        self.progress_tree = ttk.Treeview(
            progress_frame,
            columns=("idx", "url", "status"),
            show="headings",
        )
        self.progress_tree.heading("idx", text="序号")
        self.progress_tree.heading("url", text="网址")
        self.progress_tree.heading("status", text="状态")
        self.progress_tree.column("idx", width=58, anchor="center", stretch=False)
        self.progress_tree.column("url", width=320, anchor="w")
        self.progress_tree.column("status", width=110, anchor="center", stretch=False)
        self.progress_tree.grid(row=0, column=0, sticky="nsew")

        progress_scroll = ttk.Scrollbar(progress_frame, orient="vertical", command=self.progress_tree.yview)
        progress_scroll.grid(row=0, column=1, sticky="ns")
        self.progress_tree.configure(yscrollcommand=progress_scroll.set)

    def build_right_panel(self, parent):
        panel = ttk.Frame(parent, style="Card.TFrame")
        panel.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(panel, text="每日定时设置", style="Card.TLabel", font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w")

        form = ttk.Frame(panel, style="Card.TFrame")
        form.pack(fill="x", pady=(14, 10))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        self.start_time_var = tk.StringVar(value="00:00")
        self.end_time_var = tk.StringVar(value="23:59")
        self.daily_rounds_var = tk.StringVar(value="24")
        self.url_interval_var = tk.StringVar(value="5")
        self.load_timeout_var = tk.StringVar(value="60")
        self.stay_seconds_var = tk.StringVar(value="10")
        self.chrome_path_var = tk.StringVar(value="")

        ttk.Label(form, text="开始时间", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(form, text="结束时间", style="Card.TLabel").grid(row=0, column=1, sticky="w", padx=(10, 0))
        ttk.Entry(form, textvariable=self.start_time_var).grid(row=1, column=0, sticky="ew", pady=(5, 10))
        ttk.Entry(form, textvariable=self.end_time_var).grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(5, 10))

        ttk.Label(form, text="每天执行轮数", style="Card.TLabel").grid(row=2, column=0, sticky="w")
        ttk.Label(form, text="网址间隔秒数", style="Card.TLabel").grid(row=2, column=1, sticky="w", padx=(10, 0))
        ttk.Entry(form, textvariable=self.daily_rounds_var).grid(row=3, column=0, sticky="ew", pady=(5, 10))
        ttk.Entry(form, textvariable=self.url_interval_var).grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(5, 10))

        ttk.Label(form, text="加载超时秒数", style="Card.TLabel").grid(row=4, column=0, sticky="w")
        ttk.Label(form, text="加载后等待秒数", style="Card.TLabel").grid(row=4, column=1, sticky="w", padx=(10, 0))
        ttk.Entry(form, textvariable=self.load_timeout_var).grid(row=5, column=0, sticky="ew", pady=(5, 10))
        ttk.Entry(form, textvariable=self.stay_seconds_var).grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(5, 10))

        ttk.Label(form, text="Chrome路径", style="Card.TLabel").grid(row=6, column=0, columnspan=2, sticky="w")
        chrome_row = ttk.Frame(form, style="Card.TFrame")
        chrome_row.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(5, 10))
        chrome_row.columnconfigure(0, weight=1)
        ttk.Entry(chrome_row, textvariable=self.chrome_path_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(chrome_row, text="选择", command=self.pick_chrome_path).grid(row=0, column=1, padx=(8, 0))

        summary_box = tk.Frame(panel, bg=self.soft, highlightbackground="#cfe8ff", highlightthickness=1)
        summary_box.pack(fill="x", pady=(4, 12))
        s = tk.Frame(summary_box, bg=self.soft)
        s.pack(fill="x", padx=12, pady=12)

        self.status_label = tk.Label(s, text="状态：未开始", bg=self.soft, fg=self.text, anchor="w", font=("Microsoft YaHei UI", 10, "bold"))
        self.status_label.pack(fill="x")

        self.next_label = tk.Label(s, text="下次执行：--", bg=self.soft, fg=self.muted, anchor="w", font=("Microsoft YaHei UI", 9))
        self.next_label.pack(fill="x", pady=(6, 0))

        self.countdown_label = tk.Label(s, text="倒计时：--", bg=self.soft, fg=self.muted, anchor="w", font=("Microsoft YaHei UI", 9))
        self.countdown_label.pack(fill="x", pady=(6, 0))

        self.run_detail_label = tk.Label(s, text="本轮：--", bg=self.soft, fg=self.muted, anchor="w", font=("Microsoft YaHei UI", 9))
        self.run_detail_label.pack(fill="x", pady=(6, 0))

        self.message_label = tk.Label(
            s,
            text="",
            bg=self.soft,
            fg=self.muted,
            anchor="w",
            justify="left",
            wraplength=310,
            font=("Microsoft YaHei UI", 9),
        )
        self.message_label.pack(fill="x", pady=(6, 0))

        ttk.Button(panel, text="开始每日定时", style="Accent.TButton", command=self.start_daily_schedule).pack(fill="x", pady=(0, 8))
        ttk.Button(panel, text="立即执行一轮", command=self.open_one_round_now).pack(fill="x", pady=(0, 8))
        ttk.Button(panel, text="刷新今日计划", command=self.refresh_schedule_preview).pack(fill="x", pady=(0, 8))
        ttk.Button(panel, text="保存当前设置", command=self.save_config).pack(fill="x", pady=(0, 8))
        ttk.Button(panel, text="停止任务", style="Danger.TButton", command=self.stop_schedule).pack(fill="x", pady=(0, 12))

        info_box = tk.Frame(panel, bg="#fff7ed", highlightbackground="#fed7aa", highlightthickness=1)
        info_box.pack(fill="x", side="bottom")
        self.info_label = tk.Label(
            info_box,
            text="每一轮都会打开左侧列表里的全部网址。全部网址完成加载检测后，会一起等待设置的秒数，然后关闭后台 Chrome。",
            bg="#fff7ed",
            fg="#9a3412",
            justify="left",
            anchor="w",
            wraplength=310,
            font=("Microsoft YaHei UI", 9),
        )
        self.info_label.pack(fill="x", padx=12, pady=10)

    # ------------------------- url operations -------------------------

    def clean_url_text(self, raw_url, add_scheme=True):
        url = str(raw_url or "").strip()
        if not url:
            return ""

        # 只把中文/全角点号转换为英文点号，绝不删除英文点号 .
        for ch in ("。", "．", "｡", "﹒", "·"):
            url = url.replace(ch, ".")

        url = url.replace("：//", "://")
        url = re.sub(r"^hxxps://", "https://", url, flags=re.I)
        url = re.sub(r"^hxxp://", "http://", url, flags=re.I)

        # 移除不可见字符和控制字符；保留英文点号、冒号、斜杠、问号、等号等 URL 符号。
        invisible = {"\ufeff", "\u200b", "\u200c", "\u200d", "\u2060", "\u180e", "\u00ad"}
        url = "".join(ch for ch in url if ch not in invisible and (ord(ch) >= 32 or ch in "\t\r\n"))

        # 只移除空白，不移除英文点号。
        url = re.sub(r"\s+", "", url)

        if add_scheme:
            parsed = urlparse(url)
            if not parsed.scheme:
                url = "https://" + url

        return url

    def normalize_url(self, raw_url):
        return self.clean_url_text(raw_url, add_scheme=True)

    def is_valid_url(self, url):
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return False
            if not parsed.netloc:
                return False
            if "." not in parsed.netloc and parsed.netloc.lower() not in ("localhost",):
                return False
            if any(ch in parsed.netloc for ch in " <>\"'`{}|\\^"):
                return False
            return True
        except Exception:
            return False

    def on_paste_url(self, event=None):
        try:
            pasted = self.root.clipboard_get()
        except Exception:
            self.root.after(50, self.clean_url_entry_after_paste)
            return None

        cleaned = self.clean_url_text(pasted, add_scheme=False)
        if not cleaned:
            return "break"

        try:
            if self.url_entry.selection_present():
                self.url_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except Exception:
            pass

        self.url_entry.insert(tk.INSERT, cleaned)
        self.root.after(50, self.clean_url_entry_after_paste)
        return "break"

    def clean_url_entry_after_paste(self):
        current = self.url_var.get()
        cleaned = self.clean_url_text(current, add_scheme=False)
        if cleaned != current:
            pos = self.url_entry.index(tk.INSERT)
            self.url_var.set(cleaned)
            try:
                self.url_entry.icursor(min(pos, len(cleaned)))
            except Exception:
                pass

    def add_url(self):
        url = self.normalize_url(self.url_var.get())
        if not url:
            messagebox.showwarning("提示", "请输入网址。")
            return
        if not self.is_valid_url(url):
            messagebox.showwarning("提示", "网址格式不正确，请检查域名是否完整。")
            return

        self.urls.append(url)
        self.url_var.set("")
        self.refresh_url_list()
        self.refresh_progress_table()
        self.refresh_all_summaries()
        self.schedule_save_config()
        self.set_message(f"已添加：{url}")

    def refresh_url_list(self):
        self.url_listbox.delete(0, "end")
        for index, url in enumerate(self.urls, start=1):
            self.url_listbox.insert("end", f"{index:03d}. {url}")
        self.url_count_label.configure(text=f"{len(self.urls)} 个网址")

    def remove_selected(self):
        selected = list(self.url_listbox.curselection())
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的网址。")
            return

        for index in reversed(selected):
            self.urls.pop(index)

        self.refresh_url_list()
        self.refresh_progress_table()
        self.refresh_all_summaries()
        self.schedule_save_config()
        self.set_message("已删除选中的网址")

    def clear_urls(self):
        if not self.urls:
            return
        if messagebox.askyesno("确认", "确定要清空全部网址吗？"):
            self.urls.clear()
            self.refresh_url_list()
            self.refresh_progress_table()
            self.refresh_all_summaries()
            self.schedule_save_config()
            self.set_message("已清空网址列表")

    def deduplicate_urls(self):
        old_count = len(self.urls)
        seen = set()
        new_urls = []
        for url in self.urls:
            key = url.strip().lower()
            if key not in seen:
                seen.add(key)
                new_urls.append(url)
        self.urls = new_urls
        removed = old_count - len(self.urls)
        self.refresh_url_list()
        self.refresh_progress_table()
        self.refresh_all_summaries()
        self.schedule_save_config()
        self.set_message(f"已去重，删除 {removed} 个重复网址")

    def import_txt(self):
        path = filedialog.askopenfilename(
            title="选择网址 TXT 文件",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return

        text = None
        for enc in ("utf-8-sig", "utf-8", "gbk"):
            try:
                with open(path, "r", encoding=enc) as f:
                    text = f.read()
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            messagebox.showerror("错误", "文件编码无法识别，请换成 UTF-8 或 GBK 编码。")
            return

        count = 0
        skipped = 0
        for line in text.splitlines():
            url = self.normalize_url(line)
            if url and self.is_valid_url(url):
                self.urls.append(url)
                count += 1
            elif line.strip():
                skipped += 1

        self.refresh_url_list()
        self.refresh_progress_table()
        self.refresh_all_summaries()
        self.schedule_save_config()
        self.set_message(f"已导入 {count} 个网址，跳过 {skipped} 行无效内容")

    def export_txt(self):
        if not self.urls:
            messagebox.showinfo("提示", "当前没有网址可导出。")
            return

        path = filedialog.asksaveasfilename(
            title="导出网址 TXT",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
        )
        if not path:
            return

        with open(path, "w", encoding="utf-8") as f:
            for url in self.urls:
                f.write(url + "\n")

        self.set_message(f"已导出到：{path}")

    # ------------------------- settings / schedule -------------------------

    def parse_time_value(self, value, field_name):
        raw = str(value).strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(raw, fmt).time()
            except ValueError:
                pass
        raise ValueError(f"{field_name}格式错误，请使用 HH:MM 或 HH:MM:SS。")

    def parse_positive_int(self, value, field_name):
        try:
            number = int(str(value).strip())
            if number <= 0:
                raise ValueError
            return number
        except Exception:
            raise ValueError(f"{field_name}必须是大于 0 的整数。")

    def parse_nonnegative_float(self, value, field_name):
        try:
            number = float(str(value).strip())
            if number < 0:
                raise ValueError
            return number
        except Exception:
            raise ValueError(f"{field_name}必须是大于或等于 0 的数字。")

    def parse_positive_float(self, value, field_name):
        try:
            number = float(str(value).strip())
            if number <= 0:
                raise ValueError
            return number
        except Exception:
            raise ValueError(f"{field_name}必须是大于 0 的数字。")

    def get_settings(self):
        start_t = self.parse_time_value(self.start_time_var.get(), "开始时间")
        end_t = self.parse_time_value(self.end_time_var.get(), "结束时间")
        daily_rounds = self.parse_positive_int(self.daily_rounds_var.get(), "每天执行轮数")
        interval = self.parse_positive_float(self.url_interval_var.get(), "网址间隔秒数")
        load_timeout = self.parse_positive_float(self.load_timeout_var.get(), "加载超时秒数")
        stay_seconds = self.parse_nonnegative_float(self.stay_seconds_var.get(), "加载后等待秒数")
        chrome_path = self.chrome_path_var.get().strip().strip('"')

        start_dt = datetime.combine(date.today(), start_t)
        end_dt = datetime.combine(date.today(), end_t)
        if end_dt <= start_dt:
            raise ValueError("结束时间必须晚于开始时间。")

        return start_t, end_t, daily_rounds, interval, load_timeout, stay_seconds, chrome_path

    def build_slots_for_date(self, target_date):
        start_t, end_t, daily_rounds, _, _, _, _ = self.get_settings()
        start_dt = datetime.combine(target_date, start_t)
        end_dt = datetime.combine(target_date, end_t)

        if daily_rounds == 1:
            return [start_dt]

        total_seconds = (end_dt - start_dt).total_seconds()
        step = total_seconds / (daily_rounds - 1)

        return [start_dt + timedelta(seconds=round(i * step)) for i in range(daily_rounds)]

    def find_next_slot(self, now):
        today_slots = self.build_slots_for_date(now.date())
        for slot in today_slots:
            if slot >= now:
                return slot
        return self.build_slots_for_date(now.date() + timedelta(days=1))[0]

    def refresh_schedule_preview(self):
        try:
            slots = self.build_slots_for_date(date.today())
        except ValueError as e:
            messagebox.showwarning("提示", str(e))
            return

        self.schedule_tree.delete(*self.schedule_tree.get_children())

        now = datetime.now()
        for idx, slot in enumerate(slots, start=1):
            if slot < now:
                status = "已过"
            else:
                status = "待执行"
            self.schedule_tree.insert("", "end", values=(idx, slot.strftime("%H:%M:%S"), status))

        self.refresh_all_summaries()
        self.set_message(f"今日计划已刷新，共 {len(slots)} 轮")

    def refresh_progress_table(self):
        self.progress_tree.delete(*self.progress_tree.get_children())
        for idx, url in enumerate(self.urls, start=1):
            self.progress_tree.insert("", "end", iid=str(idx), values=(idx, url, "等待"))

        self.current_round_total = len(self.urls)
        self.current_round_opened = 0
        self.current_round_loaded = 0
        self.round_summary_label.configure(text="未执行")
        self.run_detail_label.configure(text="本轮：--")

    def refresh_all_summaries(self):
        try:
            _, _, rounds, interval, timeout, stay_seconds, _ = self.get_settings()
            total_daily_opens = rounds * len(self.urls)
            self.top_summary_label.configure(
                text=f"网址 {len(self.urls)} 个｜每天 {rounds} 轮｜预计每天打开 {total_daily_opens} 次｜间隔 {interval:g} 秒｜停留 {stay_seconds:g} 秒"
            )
        except Exception:
            self.top_summary_label.configure(text=f"网址 {len(self.urls)} 个")

    def pick_chrome_path(self):
        path = filedialog.askopenfilename(
            title="选择 chrome.exe",
            filetypes=[("Chrome", "chrome.exe"), ("Executable", "*.exe"), ("All Files", "*.*")],
        )
        if path:
            self.chrome_path_var.set(path)

    # ------------------------- selenium / chrome -------------------------

    def ensure_selenium_ready(self):
        try:
            importlib.import_module("selenium")
            return True
        except ImportError:
            pass

        answer = messagebox.askyesno(
            "需要安装 Selenium",
            "后台运行 Google Chrome 需要 Selenium。\n\n当前电脑未检测到 Selenium，是否现在自动安装？",
        )
        if not answer:
            messagebox.showinfo("提示", "请先在命令行运行：python -m pip install selenium")
            return False

        self.set_message("正在安装 Selenium，请稍等")
        self.root.update_idletasks()

        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "selenium"])
            importlib.import_module("selenium")
            self.set_message("Selenium 安装完成")
            return True
        except Exception as e:
            messagebox.showerror("安装失败", f"Selenium 自动安装失败：\n{e}\n\n请手动运行：python -m pip install selenium")
            self.set_message("Selenium 安装失败")
            return False

    def find_chrome_binary(self, manual_path=""):
        if manual_path:
            if os.path.exists(manual_path):
                return manual_path
            raise ChromeAutomationError(f"填写的 Chrome 路径不存在：{manual_path}")

        if sys.platform.startswith("win"):
            candidates = [
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "Application", "chrome.exe"),
            ]
            for path in candidates:
                if path and os.path.exists(path):
                    return path

            found = shutil.which("chrome") or shutil.which("chrome.exe")
            if found:
                return found

            return ""

        if sys.platform == "darwin":
            candidates = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            ]
            for path in candidates:
                if os.path.exists(path):
                    return path
            return shutil.which("google-chrome") or shutil.which("chrome") or ""

        return (
            shutil.which("google-chrome")
            or shutil.which("google-chrome-stable")
            or shutil.which("chromium-browser")
            or shutil.which("chromium")
            or ""
        )

    def create_chrome_driver(self, chrome_path, load_timeout):
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
        except Exception as e:
            raise ChromeAutomationError(f"Selenium 导入失败：{e}")

        options = Options()
        options.page_load_strategy = "none"

        # 后台无界面运行：不会弹出电脑浏览器窗口。
        options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--log-level=3")
        options.add_experimental_option("detach", False)
        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        binary = self.find_chrome_binary(chrome_path)
        if binary:
            options.binary_location = binary

        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(float(load_timeout))
            return driver
        except Exception as e:
            raise ChromeAutomationError(
                "无法启动后台 Google Chrome。\n"
                "请确认电脑已安装 Google Chrome，或在软件里手动选择 chrome.exe 路径。\n"
                f"详细错误：{e}"
            )

    def wait_tab_loaded(self, driver, handle, timeout_seconds):
        start = time.time()
        last_state = "unknown"

        while time.time() - start < timeout_seconds:
            if self.stop_event.is_set():
                return False, "已停止"

            try:
                handles = driver.window_handles
                if handle not in handles:
                    return False, "标签页不存在"

                driver.switch_to.window(handle)
                state = driver.execute_script("return document.readyState")
                last_state = str(state)
                if state == "complete":
                    return True, "complete"
            except Exception as e:
                last_state = str(e)[:80]

            time.sleep(0.35)

        return False, f"超时，最后状态：{last_state}"

    def wait_after_all_loaded(self, stay_seconds):
        stay_seconds = float(stay_seconds)
        if stay_seconds <= 0:
            self.ui_queue.put(("message", "未设置额外等待，准备关闭后台 Chrome"))
            return True

        start = time.time()
        end = start + stay_seconds

        while time.time() < end:
            if self.stop_event.is_set():
                return False

            remain = max(0, int(round(end - time.time())))
            self.ui_queue.put(("run_detail", f"本轮：全部完成，统一等待 {remain} 秒后关闭"))
            time.sleep(0.5)

        return True

    def open_all_urls_one_round(self, urls, interval, load_timeout, stay_seconds, chrome_path):
        driver = None
        tab_handles = []

        try:
            driver = self.create_chrome_driver(chrome_path, load_timeout)
            total = len(urls)

            self.ui_queue.put(("round_start", total))
            self.ui_queue.put(("message", f"本轮开始：准备打开 {total} 个网址"))

            for idx, url in enumerate(urls, start=1):
                if self.stop_event.is_set():
                    return False

                self.ui_queue.put(("url_status", (idx, "正在打开")))
                self.ui_queue.put(("run_detail", f"本轮：正在打开 {idx}/{total}"))

                try:
                    if idx == 1:
                        handle = driver.current_window_handle
                        driver.get(url)
                    else:
                        # 使用 Selenium 原生新建标签，避免 window.open 在后台模式下只打开一个网址的问题。
                        driver.switch_to.new_window("tab")
                        handle = driver.current_window_handle
                        driver.get(url)

                    tab_handles.append((idx, url, handle))
                    self.ui_queue.put(("url_status", (idx, "已打开")))
                    self.ui_queue.put(("round_opened", idx))

                except Exception as e:
                    self.ui_queue.put(("url_status", (idx, "打开失败")))
                    self.ui_queue.put(("message", f"打开失败：{url}；{str(e)[:120]}"))

                if idx < total:
                    if not self.sleep_with_stop(interval):
                        return False

            self.ui_queue.put(("message", "全部网址已打开，正在检测加载完成"))

            loaded_count = 0
            for idx, url, handle in tab_handles:
                if self.stop_event.is_set():
                    return False

                self.ui_queue.put(("url_status", (idx, "检测加载")))
                self.ui_queue.put(("run_detail", f"本轮：检测加载 {idx}/{total}"))

                ok, detail = self.wait_tab_loaded(driver, handle, load_timeout)
                if ok:
                    loaded_count += 1
                    self.ui_queue.put(("url_status", (idx, "加载完成")))
                    self.ui_queue.put(("round_loaded", loaded_count))
                else:
                    self.ui_queue.put(("url_status", (idx, "加载超时")))
                    self.ui_queue.put(("message", f"未确认加载完成：{url}；{detail}"))

            self.ui_queue.put(("run_detail", f"本轮：完成加载检测 {loaded_count}/{total}"))
            self.ui_queue.put(("message", f"加载检测完成，全部标签统一等待 {float(stay_seconds):g} 秒"))

            if not self.wait_after_all_loaded(stay_seconds):
                return False

            self.ui_queue.put(("run_detail", "本轮：等待结束，正在关闭后台 Chrome"))
            self.ui_queue.put(("message", "等待结束，正在关闭全部标签和后台 Chrome"))
            return True

        finally:
            if driver is not None:
                try:
                    driver.quit()
                    self.ui_queue.put(("message", "后台 Chrome 已关闭"))
                except Exception:
                    self.ui_queue.put(("message", "关闭后台 Chrome 时出现问题"))

    # ------------------------- scheduler -------------------------

    def start_daily_schedule(self):
        if self.is_running:
            messagebox.showinfo("提示", "任务已经在运行中。")
            return
        if not self.urls:
            messagebox.showwarning("提示", "请先添加至少一个网址。")
            return

        try:
            _, _, rounds, interval, timeout, stay_seconds, chrome_path = self.get_settings()
        except ValueError as e:
            messagebox.showwarning("提示", str(e))
            return

        self.save_config()
        if not self.ensure_selenium_ready():
            return

        self.stop_event.clear()
        self.is_running = True
        self.refresh_schedule_preview()
        self.refresh_progress_table()

        urls_snapshot = list(self.urls)
        self.worker_thread = threading.Thread(
            target=self.daily_worker,
            args=(urls_snapshot, interval, timeout, stay_seconds, chrome_path),
            daemon=True,
        )
        self.worker_thread.start()

        self.status_label.configure(text="状态：每日定时运行中")
        self.set_message(f"已启动：每天 {rounds} 轮，每轮打开 {len(urls_snapshot)} 个网址，加载后等待 {stay_seconds:g} 秒")

    def open_one_round_now(self):
        if self.is_running:
            messagebox.showinfo("提示", "任务正在运行，请先停止后再立即执行。")
            return
        if not self.urls:
            messagebox.showwarning("提示", "请先添加至少一个网址。")
            return

        try:
            _, _, _, interval, timeout, stay_seconds, chrome_path = self.get_settings()
        except ValueError as e:
            messagebox.showwarning("提示", str(e))
            return

        self.save_config()
        if not self.ensure_selenium_ready():
            return

        self.stop_event.clear()
        self.is_running = True
        self.next_run_time = datetime.now()
        self.refresh_progress_table()

        urls_snapshot = list(self.urls)
        self.worker_thread = threading.Thread(
            target=self.single_round_worker,
            args=(urls_snapshot, interval, timeout, stay_seconds, chrome_path),
            daemon=True,
        )
        self.worker_thread.start()

        self.status_label.configure(text="状态：正在立即执行一轮")
        self.next_label.configure(text="下次执行：立即")
        self.countdown_label.configure(text="倒计时：正在执行")
        self.set_message(f"立即执行一轮：会打开全部 {len(urls_snapshot)} 个网址，加载后等待 {stay_seconds:g} 秒")

    def daily_worker(self, urls, interval, timeout, stay_seconds, chrome_path):
        while not self.stop_event.is_set():
            try:
                next_slot = self.find_next_slot(datetime.now())
            except Exception as e:
                self.ui_queue.put(("message", f"计划计算失败：{e}"))
                break

            self.ui_queue.put(("next", next_slot))

            while not self.stop_event.is_set() and datetime.now() < next_slot:
                time.sleep(0.25)

            if self.stop_event.is_set():
                break

            self.ui_queue.put(("message", "到达计划时间，开始执行一轮"))
            try:
                ok = self.open_all_urls_one_round(urls, interval, timeout, stay_seconds, chrome_path)
                if not ok:
                    break
            except Exception as e:
                self.ui_queue.put(("message", f"本轮执行失败：{e}"))

            time.sleep(0.5)

        self.ui_queue.put(("stopped", None))

    def single_round_worker(self, urls, interval, timeout, stay_seconds, chrome_path):
        try:
            self.open_all_urls_one_round(urls, interval, timeout, stay_seconds, chrome_path)
            if self.stop_event.is_set():
                self.ui_queue.put(("stopped", None))
            else:
                self.ui_queue.put(("finished_single", None))
        except Exception as e:
            self.ui_queue.put(("message", f"立即执行失败：{e}"))
            self.ui_queue.put(("finished_single", None))

    def sleep_with_stop(self, seconds):
        end = time.time() + float(seconds)
        while time.time() < end:
            if self.stop_event.is_set():
                return False
            time.sleep(min(0.2, max(0.01, end - time.time())))
        return True

    def stop_schedule(self):
        if not self.is_running:
            self.set_message("当前没有正在运行的任务")
            return
        self.stop_event.set()
        self.set_message("正在停止任务，后台 Chrome 会自动关闭")

    # ------------------------- queue / UI update -------------------------

    def set_message(self, message):
        try:
            self.message_label.configure(text=str(message))
        except Exception:
            pass

    def process_ui_queue(self):
        try:
            while True:
                event, data = self.ui_queue.get_nowait()

                if event == "message":
                    self.set_message(data)

                elif event == "next":
                    self.next_run_time = data
                    self.next_label.configure(text=f"下次执行：{data.strftime('%Y-%m-%d %H:%M:%S')}")

                elif event == "round_start":
                    total = int(data)
                    self.current_round_total = total
                    self.current_round_opened = 0
                    self.current_round_loaded = 0
                    self.round_summary_label.configure(text=f"0/{total}")
                    self.run_detail_label.configure(text=f"本轮：0/{total}")
                    self.refresh_progress_table()

                elif event == "url_status":
                    idx, status = data
                    iid = str(idx)
                    if self.progress_tree.exists(iid):
                        values = list(self.progress_tree.item(iid, "values"))
                        if len(values) >= 3:
                            values[2] = status
                            self.progress_tree.item(iid, values=values)
                            self.progress_tree.see(iid)

                elif event == "round_opened":
                    self.current_round_opened = max(self.current_round_opened, int(data))
                    self.round_summary_label.configure(
                        text=f"已打开 {self.current_round_opened}/{self.current_round_total}，已加载 {self.current_round_loaded}/{self.current_round_total}"
                    )

                elif event == "round_loaded":
                    self.current_round_loaded = max(self.current_round_loaded, int(data))
                    self.round_summary_label.configure(
                        text=f"已打开 {self.current_round_opened}/{self.current_round_total}，已加载 {self.current_round_loaded}/{self.current_round_total}"
                    )

                elif event == "run_detail":
                    self.run_detail_label.configure(text=str(data))

                elif event == "finished_single":
                    self.is_running = False
                    self.next_run_time = None
                    self.status_label.configure(text="状态：已完成")
                    self.next_label.configure(text="下次执行：--")
                    self.countdown_label.configure(text="倒计时：--")
                    self.run_detail_label.configure(text="本轮：已完成")
                    self.set_message("立即执行一轮已完成")

                elif event == "stopped":
                    self.is_running = False
                    self.next_run_time = None
                    self.status_label.configure(text="状态：已停止")
                    self.next_label.configure(text="下次执行：--")
                    self.countdown_label.configure(text="倒计时：--")
                    self.run_detail_label.configure(text="本轮：已停止")
                    self.set_message("任务已停止")

        except queue.Empty:
            pass

        self.root.after(200, self.process_ui_queue)

    def update_countdown(self):
        if self.is_running and self.next_run_time:
            remaining = self.next_run_time - datetime.now()
            if remaining.total_seconds() > 0:
                seconds = int(remaining.total_seconds())
                h = seconds // 3600
                m = (seconds % 3600) // 60
                s = seconds % 60
                self.countdown_label.configure(text=f"倒计时：{h:02d}:{m:02d}:{s:02d}")
            else:
                self.countdown_label.configure(text="倒计时：正在执行")

        self.root.after(1000, self.update_countdown)

    def on_close(self):
        if self.is_running:
            if not messagebox.askyesno("确认退出", "当前任务正在运行，确定要退出吗？"):
                return
            self.stop_event.set()

        self.save_config()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = UrlSchedulerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
