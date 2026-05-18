import os
import re
import json
import threading
import requests
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox, ttk

try:
    import ttkbootstrap as ttkb
    USE_BOOTSTRAP = True
except ImportError:
    USE_BOOTSTRAP = False
    print("提示: 安装 ttkbootstrap 可获得最佳视觉效果")
    print("  pip install ttkbootstrap")

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitHub-Releases-Downloader/"
}
CHUNK_SIZE = 8192

MIRROR_SOURCES = {
    "官方 (直连)": "",
    "gh-proxy.com": "https://gh-proxy.com/",
    "自定义": "__custom__"
}


class PlaceholderText(tk.Text):
    """带占位符的多行文本框"""
    def __init__(self, master=None, placeholder="", placeholder_color="gray", **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = placeholder_color
        self.normal_color = kwargs.get("fg", "black")
        self._has_placeholder = False
        self._put_placeholder()
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _put_placeholder(self):
        self.insert("1.0", self.placeholder)
        self.config(fg=self.placeholder_color)
        self._has_placeholder = True

    def _on_focus_in(self, event=None):
        if self._has_placeholder:
            self.delete("1.0", "end")
            self.config(fg=self.normal_color)
            self._has_placeholder = False

    def _on_focus_out(self, event=None):
        if not self.get("1.0", "end").strip():
            self._put_placeholder()

    def get_text(self):
        if self._has_placeholder:
            return ""
        return self.get("1.0", "end").strip()

    def set_text(self, text):
        self.delete("1.0", "end")
        self._has_placeholder = False
        self.config(fg=self.normal_color)
        if text:
            self.insert("1.0", text)
        else:
            self._put_placeholder()


class GitHubDownloader:
    def __init__(self, token=None, api_base="https://api.github.com"):
        self.token = token
        self.api_base = api_base.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        if token:
            self.session.headers["Authorization"] = f"token {token}"

    def parse_repo(self, url_or_path):
        patterns = [
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$",
            r"^([^/]+)/([^/]+?)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, url_or_path)
            if match:
                return match.group(1), match.group(2)
        return None, None

    def get_releases(self, owner, repo, per_page=100):
        url = f"{self.api_base}/repos/{owner}/{repo}/releases"
        params = {"per_page": per_page}
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def download_file(self, url, save_path, progress_callback=None,
                     total_size=None, stop_event=None):
        headers = {}
        downloaded = 0
        if os.path.exists(save_path):
            downloaded = os.path.getsize(save_path)
            headers["Range"] = f"bytes={downloaded}-"

        resp = self.session.get(url, headers=headers, stream=True, timeout=60)

        if resp.status_code == 416:
            os.remove(save_path)
            downloaded = 0
            resp = self.session.get(url, stream=True, timeout=60)
        elif resp.status_code == 200 and downloaded > 0:
            downloaded = 0

        resp.raise_for_status()

        if total_size is None:
            total_size = int(resp.headers.get("content-length", 0))
            if resp.status_code == 206:
                total_size += downloaded

        mode = "ab" if downloaded > 0 and resp.status_code == 206 else "wb"
        with open(save_path, mode) as f:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if stop_event and stop_event.is_set():
                    raise InterruptedError("下载已取消")
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total_size)
        return True


class DownloaderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Releases 批量下载器 v1.0")
        self.root.geometry("1000x800")
        self.root.minsize(880, 680)
        if not USE_BOOTSTRAP:
            self.root.configure(bg="#f0f2f5")

        self.downloader = None
        self.stop_event = threading.Event()
        self.item_data = {}
        self.checked_items = set()
        self.last_clicked_item = None

        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        # 主容器
        if USE_BOOTSTRAP:
            main_frame = ttkb.Frame(self.root, padding=10)
        else:
            main_frame = tk.Frame(self.root, bg="#f0f2f5", padx=10, pady=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # ===== 配置卡片 =====
        if USE_BOOTSTRAP:
            card1 = ttkb.Labelframe(main_frame, text="⚙️  配置", padding=10)
        else:
            card1 = tk.LabelFrame(main_frame, text=" 配置 ", bg="#f0f2f5", fg="#333",
                                   font=("Microsoft YaHei", 10, "bold"), padx=10, pady=10)
        card1.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        # --- Token 行 ---
        row1 = tk.Frame(card1, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        row1.pack(fill="x", pady=2)
        if USE_BOOTSTRAP:
            ttkb.Label(row1, text="GitHub Token", font=("Microsoft YaHei", 10), width=12).pack(side="left")
            self.token_var = tk.StringVar()
            ttkb.Entry(row1, textvariable=self.token_var, width=35, show="●").pack(side="left", padx=(4, 2))
            ttkb.Label(row1, text="提高API限额，私有仓库必填", foreground="gray").pack(side="left", padx=(2, 0))
        else:
            tk.Label(row1, text="GitHub Token", bg="#f0f2f5", font=("Microsoft YaHei", 10), width=12).pack(side="left")
            self.token_var = tk.StringVar()
            tk.Entry(row1, textvariable=self.token_var, width=35, show="●", relief="flat",
                     bg="white", highlightthickness=1, highlightbackground="#ddd").pack(side="left", padx=(4, 2))
            tk.Label(row1, text="提高API限额，私有仓库必填", bg="#f0f2f5", fg="gray").pack(side="left", padx=(2, 0))

        # --- 镜像源 行 ---
        row2 = tk.Frame(card1, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        row2.pack(fill="x", pady=2)
        if USE_BOOTSTRAP:
            ttkb.Label(row2, text="下载镜像", font=("Microsoft YaHei", 10), width=12).pack(side="left")
            self.mirror_var = tk.StringVar(value="官方 (直连)")
            self.mirror_combo = ttkb.Combobox(row2, textvariable=self.mirror_var,
                                                values=list(MIRROR_SOURCES.keys()),
                                                width=18, state="readonly")
            self.mirror_combo.pack(side="left", padx=(4, 2))
            self.mirror_combo.bind("<<ComboboxSelected>>", self._on_mirror_change)
            self.custom_mirror_var = tk.StringVar()
            self.custom_mirror_entry = ttkb.Entry(row2, textvariable=self.custom_mirror_var,
                                                   width=28, state="disabled")
            self.custom_mirror_entry.pack(side="left", padx=(2, 0))
            ttkb.Label(row2, text="仅加速下载，API不走镜像", foreground="gray").pack(side="left", padx=(4, 0))
        else:
            tk.Label(row2, text="下载镜像", bg="#f0f2f5", font=("Microsoft YaHei", 10), width=12).pack(side="left")
            self.mirror_var = tk.StringVar(value="官方 (直连)")
            self.mirror_combo = ttk.Combobox(row2, textvariable=self.mirror_var,
                                              values=list(MIRROR_SOURCES.keys()),
                                              width=18, state="readonly")
            self.mirror_combo.pack(side="left", padx=(4, 2))
            self.mirror_combo.bind("<<ComboboxSelected>>", self._on_mirror_change)
            self.custom_mirror_var = tk.StringVar()
            self.custom_mirror_entry = tk.Entry(row2, textvariable=self.custom_mirror_var,
                                                 width=28, state="disabled", relief="flat",
                                                 bg="white", highlightthickness=1, highlightbackground="#ddd")
            self.custom_mirror_entry.pack(side="left", padx=(2, 0))
            tk.Label(row2, text="仅加速下载，API不走镜像", bg="#f0f2f5", fg="gray").pack(side="left", padx=(4, 0))

        # --- 仓库地址 行 ---
        row3 = tk.Frame(card1, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        row3.pack(fill="x", pady=2)
        if USE_BOOTSTRAP:
            ttkb.Label(row3, text="仓库地址", font=("Microsoft YaHei", 10), width=12).pack(side="left", anchor="n", pady=4)
        else:
            tk.Label(row3, text="仓库地址", bg="#f0f2f5", font=("Microsoft YaHei", 10), width=12).pack(side="left", anchor="n", pady=4)

        self.repo_text = PlaceholderText(
            row3, placeholder="owner/repo 或 https://github.com/owner/repo (支持逗号/换行分隔)",
            placeholder_color="gray", fg="black",
            width=50, height=2, wrap="word", relief="flat",
            font=("Microsoft YaHei", 10),
            highlightthickness=1, highlightbackground="#ddd", highlightcolor="#2ea44f",
            bg="white", padx=5, pady=5
        )
        self.repo_text.pack(side="left", fill="x", expand=True, padx=(4, 2))

        if USE_BOOTSTRAP:
            ttkb.Button(row3, text="🚀 获取", command=self._fetch_releases,
                        bootstyle="success", width=8).pack(side="left", anchor="n", padx=(2, 0))
        else:
            tk.Button(row3, text="🚀 获取", command=self._fetch_releases,
                      bg="#2ea44f", fg="white", width=8, relief="flat",
                      activebackground="#22863a", cursor="hand2",
                      font=("Microsoft YaHei", 10, "bold")).pack(side="left", anchor="n", padx=(2, 0))

        # --- 下载目录 行 ---
        row4 = tk.Frame(card1, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        row4.pack(fill="x", pady=2)
        if USE_BOOTSTRAP:
            ttkb.Label(row4, text="下载目录", font=("Microsoft YaHei", 10), width=12).pack(side="left")
            self.path_var = tk.StringVar()
            self.path_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))
            ttkb.Entry(row4, textvariable=self.path_var, width=50).pack(side="left", fill="x", expand=True, padx=(4, 2))
            ttkb.Button(row4, text="📁", command=self._choose_dir,
                        bootstyle="secondary-outline", width=3).pack(side="left", padx=(2, 0))
        else:
            tk.Label(row4, text="下载目录", bg="#f0f2f5", font=("Microsoft YaHei", 10), width=12).pack(side="left")
            self.path_var = tk.StringVar()
            self.path_var.set(os.path.join(os.path.expanduser("~"), "Downloads"))
            tk.Entry(row4, textvariable=self.path_var, width=50, relief="flat",
                     bg="white", highlightthickness=1, highlightbackground="#ddd").pack(side="left", fill="x", expand=True, padx=(4, 2))
            tk.Button(row4, text="📁", command=self._choose_dir,
                      bg="#6c757d", fg="white", width=3, relief="flat",
                      activebackground="#5a6268", cursor="hand2").pack(side="left", padx=(2, 0))

        # ===== Releases 列表卡片 =====
        if USE_BOOTSTRAP:
            card2 = ttkb.Labelframe(main_frame, text="📦 Releases 列表", padding=8)
        else:
            card2 = tk.LabelFrame(main_frame, text=" Releases 列表 ", bg="#f0f2f5", fg="#333",
                                   font=("Microsoft YaHei", 10, "bold"), padx=8, pady=8)
        card2.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        card2.grid_rowconfigure(1, weight=1)
        card2.grid_columnconfigure(0, weight=1)

        # 工具栏
        toolbar = tk.Frame(card2, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        if USE_BOOTSTRAP:
            ttkb.Button(toolbar, text="✅ 全选", command=self._select_all,
                        bootstyle="primary-outline", width=7).pack(side="left", padx=1)
            ttkb.Button(toolbar, text="❌ 取消", command=self._deselect_all,
                        bootstyle="danger-outline", width=7).pack(side="left", padx=1)
            ttkb.Button(toolbar, text="⭐ 最新", command=self._select_latest,
                        bootstyle="warning-outline", width=7).pack(side="left", padx=1)
            ttkb.Button(toolbar, text="🔄 反选", command=self._invert_selection,
                        bootstyle="info-outline", width=7).pack(side="left", padx=1)
            ttkb.Label(toolbar, text="单击=单选 | Ctrl+单击=多选 | Shift+单击=范围选 | 版本号=全选该版",
                       foreground="gray", font=("Microsoft YaHei", 9)).pack(side="left", padx=10)
        else:
            tk.Button(toolbar, text="✅ 全选", command=self._select_all,
                      bg="#007bff", fg="white", width=7, relief="flat",
                      activebackground="#0056b3", cursor="hand2").pack(side="left", padx=1)
            tk.Button(toolbar, text="❌ 取消", command=self._deselect_all,
                      bg="#dc3545", fg="white", width=7, relief="flat",
                      activebackground="#c82333", cursor="hand2").pack(side="left", padx=1)
            tk.Button(toolbar, text="⭐ 最新", command=self._select_latest,
                      bg="#ffc107", fg="black", width=7, relief="flat",
                      activebackground="#e0a800", cursor="hand2").pack(side="left", padx=1)
            tk.Button(toolbar, text="🔄 反选", command=self._invert_selection,
                      bg="#17a2b8", fg="white", width=7, relief="flat",
                      activebackground="#138496", cursor="hand2").pack(side="left", padx=1)
            tk.Label(toolbar, text="单击=单选 | Ctrl+单击=多选 | Shift+单击=范围选 | 版本号=全选该版",
                     bg="#f0f2f5", fg="gray", font=("Microsoft YaHei", 9)).pack(side="left", padx=10)

        # Treeview
        columns = ("repo", "tag", "name", "size", "date")
        if USE_BOOTSTRAP:
            self.tree = ttkb.Treeview(card2, columns=columns, show="tree headings", height=10,
                                       bootstyle="primary")
        else:
            style = ttk.Style()
            style.configure("Custom.Treeview", rowheight=24, font=("Microsoft YaHei", 10))
            style.configure("Custom.Treeview.Heading", font=("Microsoft YaHei", 10, "bold"))
            self.tree = ttk.Treeview(card2, columns=columns, show="tree headings", height=10,
                                      style="Custom.Treeview")

        self.tree.heading("#0", text="☑")
        self.tree.heading("repo", text="仓库")
        self.tree.heading("tag", text="版本号")
        self.tree.heading("name", text="名称 / 文件名")
        self.tree.heading("size", text="大小")
        self.tree.heading("date", text="发布日期")

        self.tree.column("#0", width=45, anchor="center")
        self.tree.column("repo", width=130)
        self.tree.column("tag", width=120)
        self.tree.column("name", width=360)
        self.tree.column("size", width=80)
        self.tree.column("date", width=100)

        vsb = ttk.Scrollbar(card2, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(card2, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)
        self.tree.bind("<Control-ButtonRelease-1>", self._on_ctrl_click)
        self.tree.bind("<Shift-ButtonRelease-1>", self._on_shift_click)

        # ===== 下载进度卡片 =====
        if USE_BOOTSTRAP:
            card3 = ttkb.Labelframe(main_frame, text="📥 下载进度", padding=8)
        else:
            card3 = tk.LabelFrame(main_frame, text=" 下载进度 ", bg="#f0f2f5", fg="#333",
                                   font=("Microsoft YaHei", 10, "bold"), padx=8, pady=8)
        card3.grid(row=2, column=0, sticky="ew", pady=(0, 5))
        card3.grid_columnconfigure(0, weight=1)

        self.progress_var = tk.StringVar(value="就绪")
        if USE_BOOTSTRAP:
            ttkb.Label(card3, textvariable=self.progress_var, font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky="w")
            self.progress = ttkb.Progressbar(card3, mode="determinate", bootstyle="success-striped")
            self.progress.grid(row=1, column=0, sticky="ew", pady=4)
        else:
            tk.Label(card3, textvariable=self.progress_var, bg="#f0f2f5",
                     font=("Microsoft YaHei", 10)).grid(row=0, column=0, sticky="w")
            self.progress = ttk.Progressbar(card3, mode="determinate")
            self.progress.grid(row=1, column=0, sticky="ew", pady=4)

        # 日志区
        log_frame = tk.Frame(card3, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        log_frame.grid(row=2, column=0, sticky="ew", pady=(2, 4))
        log_frame.grid_columnconfigure(0, weight=1)
        self.log = scrolledtext.ScrolledText(log_frame, height=4, state="disabled",
                                              font=("Consolas", 9), wrap="word")
        self.log.grid(row=0, column=0, sticky="ew")

        # 按钮行
        btn_frame = tk.Frame(card3, bg="#f0f2f5" if not USE_BOOTSTRAP else "")
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(4, 0))

        if USE_BOOTSTRAP:
            self.download_btn = ttkb.Button(btn_frame, text="▶ 开始下载", command=self._start_download,
                                            bootstyle="success", width=12)
            self.download_btn.pack(side="left", padx=3)
            self.stop_btn = ttkb.Button(btn_frame, text="⏹ 停止", command=self._stop_download,
                                        bootstyle="danger", width=10, state="disabled")
            self.stop_btn.pack(side="left", padx=3)
            ttkb.Button(btn_frame, text="💾 保存配置", command=self._save_config,
                        bootstyle="secondary-outline", width=12).pack(side="right", padx=3)
            ttkb.Button(btn_frame, text="📂 加载配置", command=self._load_config,
                        bootstyle="secondary-outline", width=12).pack(side="right", padx=3)
        else:
            self.download_btn = tk.Button(btn_frame, text="▶ 开始下载", command=self._start_download,
                                          bg="#28a745", fg="white", width=12, relief="flat",
                                          activebackground="#1e7e34", cursor="hand2",
                                          font=("Microsoft YaHei", 10, "bold"))
            self.download_btn.pack(side="left", padx=3)
            self.stop_btn = tk.Button(btn_frame, text="⏹ 停止", command=self._stop_download,
                                      bg="#dc3545", fg="white", width=10, relief="flat",
                                      activebackground="#bd2130", cursor="hand2",
                                      font=("Microsoft YaHei", 10, "bold"), state="disabled")
            self.stop_btn.pack(side="left", padx=3)
            tk.Button(btn_frame, text="💾 保存配置", command=self._save_config,
                      bg="#6c757d", fg="white", width=12, relief="flat",
                      activebackground="#5a6268", cursor="hand2").pack(side="right", padx=3)
            tk.Button(btn_frame, text="📂 加载配置", command=self._load_config,
                      bg="#6c757d", fg="white", width=12, relief="flat",
                      activebackground="#5a6268", cursor="hand2").pack(side="right", padx=3)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        if USE_BOOTSTRAP:
            ttkb.Label(self.root, textvariable=self.status_var, bootstyle="secondary",
                       relief="sunken", anchor="w", padding=4).pack(side="bottom", fill="x")
        else:
            tk.Label(self.root, textvariable=self.status_var, bg="#e9ecef", fg="#495057",
                     bd=1, relief="sunken", anchor="w", padx=5, pady=2,
                     font=("Microsoft YaHei", 9)).pack(side="bottom", fill="x")

    def _on_mirror_change(self, event=None):
        if self.mirror_var.get() == "自定义":
            self.custom_mirror_entry.config(state="normal")
        else:
            self.custom_mirror_entry.config(state="disabled")
            self.custom_mirror_var.set("")

    def _get_mirror_prefix(self):
        name = self.mirror_var.get()
        if name == "自定义":
            prefix = self.custom_mirror_var.get().strip()
            return prefix if prefix else ""
        return MIRROR_SOURCES.get(name, "")

    def _apply_mirror(self, url):
        prefix = self._get_mirror_prefix()
        if not prefix:
            return url
        if url.startswith(prefix):
            return url
        return prefix + url

    def _choose_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.path_var.set(path)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_check(self, iid, checked):
        if checked:
            self.checked_items.add(iid)
            self.tree.item(iid, text="✓")
        else:
            self.checked_items.discard(iid)
            self.tree.item(iid, text="")

    def _is_checked(self, iid):
        return iid in self.checked_items

    def _toggle_item(self, iid):
        data = self.item_data.get(iid)
        if not data:
            return
        new_state = not self._is_checked(iid)

        if data["type"] == "release":
            self._set_check(iid, new_state)
            for child in data.get("children", []):
                self._set_check(child, new_state)
        else:
            self._set_check(iid, new_state)
            parent = data.get("parent")
            if parent:
                parent_data = self.item_data.get(parent)
                if parent_data:
                    all_checked = all(self._is_checked(c) for c in parent_data.get("children", []))
                    self._set_check(parent, all_checked)

    def _select_all(self):
        for iid in self.item_data:
            self._set_check(iid, True)

    def _deselect_all(self):
        for iid in list(self.checked_items):
            self._set_check(iid, False)

    def _invert_selection(self):
        for iid in self.item_data:
            self._toggle_item(iid)

    def _select_latest(self):
        self._deselect_all()
        seen_repos = set()
        for iid, data in self.item_data.items():
            if data["type"] == "release":
                repo = data.get("repo")
                if repo and repo not in seen_repos:
                    seen_repos.add(repo)
                    self._toggle_item(iid)

    def _get_visible_items(self):
        result = []
        def walk(parent=""):
            for iid in self.tree.get_children(parent):
                result.append(iid)
                walk(iid)
        walk()
        return result

    def _on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        iid = self.tree.identify_row(event.y)
        if not iid or region not in ("cell", "tree"):
            return
        self._deselect_all()
        self._toggle_item(iid)
        self.last_clicked_item = iid

    def _on_ctrl_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        iid = self.tree.identify_row(event.y)
        if not iid or region not in ("cell", "tree"):
            return
        self._toggle_item(iid)
        self.last_clicked_item = iid
        return "break"

    def _on_shift_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        iid = self.tree.identify_row(event.y)
        if not iid or region not in ("cell", "tree"):
            return

        if not self.last_clicked_item or self.last_clicked_item == iid:
            self._on_tree_click(event)
            return

        visible = self._get_visible_items()
        try:
            idx1 = visible.index(self.last_clicked_item)
            idx2 = visible.index(iid)
        except ValueError:
            self._on_tree_click(event)
            return

        start, end = min(idx1, idx2), max(idx1, idx2)
        target_state = self._is_checked(self.last_clicked_item)

        for idx in range(start, end + 1):
            cur_iid = visible[idx]
            self._set_check(cur_iid, target_state)
            data = self.item_data.get(cur_iid)
            if data and data["type"] == "release":
                for child in data.get("children", []):
                    self._set_check(child, target_state)
            elif data and data["type"] == "asset":
                parent = data.get("parent")
                if parent:
                    pd = self.item_data.get(parent)
                    if pd:
                        all_c = all(self._is_checked(c) for c in pd.get("children", []))
                        self._set_check(parent, all_c)

        self.last_clicked_item = iid
        return "break"

    def _fetch_releases(self):
        repo_input = self.repo_text.get_text()
        if not repo_input:
            messagebox.showwarning("提示", "请输入仓库地址")
            return

        token = self.token_var.get().strip() or None
        self.downloader = GitHubDownloader(token)

        repos = [r.strip() for r in re.split(r"[,\n]", repo_input) if r.strip()]

        self._clear_tree()
        self._log(f"开始获取 {len(repos)} 个仓库的 releases...")
        self.status_var.set("正在获取 releases...")
        self.root.update()

        thread = threading.Thread(target=self._fetch_thread, args=(repos,))
        thread.daemon = True
        thread.start()

    def _clear_tree(self):
        for iid in list(self.tree.get_children()):
            self.tree.delete(iid)
        self.item_data.clear()
        self.checked_items.clear()
        self.last_clicked_item = None

    def _fetch_thread(self, repos):
        total_assets = 0
        for repo_input in repos:
            owner, repo = self.downloader.parse_repo(repo_input)
            if not owner or not repo:
                self.root.after(0, lambda r=repo_input: self._log(f"❌ 无法解析仓库: {r}"))
                continue
            try:
                releases = self.downloader.get_releases(owner, repo)
                if not releases:
                    self.root.after(0, lambda r=repo: self._log(f"⚠️ {r} 没有 releases"))
                    continue
                self.root.after(0, lambda rel=releases, o=owner, r=repo:
                    self._insert_releases(rel, o, r))
                total_assets += sum(len(r.get("assets", [])) for r in releases)
            except Exception as e:
                self.root.after(0, lambda e=str(e): self._log(f"❌ 错误: {e}"))

        self.root.after(0, lambda: self.status_var.set(
            f"获取完成，共 {total_assets} 个资源文件"))

    def _insert_releases(self, releases, owner, repo):
        for release in releases:
            tag = release.get("tag_name", "N/A")
            name = release.get("name", tag)
            date = release.get("published_at", "N/A")[:10]
            assets = release.get("assets", [])

            parent_iid = f"{owner}_{repo}_{tag}"
            parent_text = f"{tag} — {name}" if name != tag else tag

            self.tree.insert("", "end", iid=parent_iid, text="",
                             values=(f"{owner}/{repo}", tag, parent_text, "", date),
                             open=True)

            children = []

            if not assets:
                for key, ext in [("zipball_url", ".zip"), ("tarball_url", ".tar.gz")]:
                    url = release.get(key)
                    if url:
                        child_iid = f"{parent_iid}_src_{ext}"
                        fname = f"{repo}-{tag}-source{ext}"
                        self.tree.insert(parent_iid, "end", iid=child_iid, text="",
                                         values=("", "", fname, "N/A", ""))
                        self.item_data[child_iid] = {
                            "type": "asset", "url": url, "filename": fname,
                            "size": 0, "repo": f"{owner}/{repo}", "tag": tag,
                            "parent": parent_iid
                        }
                        children.append(child_iid)
            else:
                for asset in assets:
                    size = asset.get("size", 0)
                    size_str = self._format_size(size)
                    aname = asset["name"]
                    child_iid = f"{parent_iid}_{aname}"
                    url = asset["browser_download_url"]
                    self.tree.insert(parent_iid, "end", iid=child_iid, text="",
                                     values=("", "", aname, size_str, ""))
                    self.item_data[child_iid] = {
                        "type": "asset", "url": url, "filename": aname,
                        "size": size, "repo": f"{owner}/{repo}", "tag": tag,
                        "parent": parent_iid
                    }
                    children.append(child_iid)

            self.item_data[parent_iid] = {
                "type": "release", "repo": f"{owner}/{repo}",
                "tag": tag, "children": children
            }

        self._select_all()

    def _format_size(self, size):
        if size == 0:
            return "N/A"
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _start_download(self):
        download_items = []
        for iid, data in self.item_data.items():
            if data["type"] == "asset" and self._is_checked(iid):
                download_items.append(data)

        if not download_items:
            messagebox.showwarning("提示", "请先选择要下载的资源（文件）")
            return

        save_dir = self.path_var.get()
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception:
                messagebox.showerror("错误", "无法创建下载目录")
                return

        self.stop_event.clear()
        self.download_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.progress["value"] = 0

        self._log(f"\n开始下载 {len(download_items)} 个文件到: {save_dir}")

        thread = threading.Thread(target=self._download_thread,
                                  args=(download_items, save_dir))
        thread.daemon = True
        thread.start()

    def _download_thread(self, items, save_dir):
        total = len(items)
        success = 0
        failed = 0

        for idx, item_data in enumerate(items, 1):
            if self.stop_event.is_set():
                self.root.after(0, lambda: self._log("⚠️ 下载已取消"))
                break

            repo = item_data["repo"]
            filename = item_data["filename"]
            url = self._apply_mirror(item_data["url"])
            tag = item_data["tag"]

            repo_dir = os.path.join(save_dir, repo.replace("/", "_"), tag)
            os.makedirs(repo_dir, exist_ok=True)
            save_path = os.path.join(repo_dir, filename)

            self.root.after(0, lambda f=filename: self._log(f"[{idx}/{total}] 下载: {f}"))
            self.root.after(0, lambda: self.progress_var.set(f"正在下载: {filename}"))

            try:
                def make_progress_cb():
                    current = [0]
                    lock = threading.Lock()
                    def cb(downloaded, total_size):
                        with lock:
                            if total_size > 0:
                                p = (downloaded / total_size) * 100
                                self.root.after(0, lambda p=p: self.progress.config(value=p))
                    return cb

                self.downloader.download_file(
                    url, save_path, make_progress_cb(),
                    item_data["size"], self.stop_event
                )
                self.root.after(0, lambda f=filename: self._log(f"✅ 完成: {f}"))
                success += 1
            except InterruptedError:
                self.root.after(0, lambda f=filename: self._log(f"⚠️ 取消: {f}"))
                break
            except Exception as e:
                self.root.after(0, lambda f=filename, e=str(e):
                    self._log(f"❌ 失败 [{f}]: {e}"))
                failed += 1

            total_percent = (idx / total) * 100
            self.root.after(0, lambda p=total_percent: self.progress.config(value=p))

        self.root.after(0, lambda: self._download_complete(success, failed, total))

    def _download_complete(self, success, failed, total):
        self.progress_var.set(f"下载完成: 成功 {success}, 失败 {failed}, 总计 {total}")
        self.status_var.set("就绪")
        self.download_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.progress.config(value=100)
        if success > 0:
            messagebox.showinfo("完成", f"下载完成！\n成功: {success}\n失败: {failed}")

    def _stop_download(self):
        self.stop_event.set()
        self._log("正在停止下载...")
        self.stop_btn.config(state="disabled")

    def _save_config(self):
        config = {
            "token": self.token_var.get(),
            "repo": self.repo_text.get_text(),
            "path": self.path_var.get(),
            "mirror": self.mirror_var.get(),
            "custom_mirror": self.custom_mirror_var.get()
        }
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON files", "*.json")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self._log(f"配置已保存: {path}")

    def _load_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.token_var.set(config.get("token", ""))
                self.repo_text.set_text(config.get("repo", ""))
                self.path_var.set(config.get("path", ""))
                mirror = config.get("mirror", "官方 (直连)")
                if mirror in MIRROR_SOURCES:
                    self.mirror_var.set(mirror)
                self.custom_mirror_var.set(config.get("custom_mirror", ""))
                self._on_mirror_change()
                self._log(f"配置已加载: {path}")
            except Exception as e:
                messagebox.showerror("错误", f"加载配置失败: {e}")


def main():
    if USE_BOOTSTRAP:
        root = ttkb.Window(themename="flatly")
    else:
        root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = DownloaderUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
