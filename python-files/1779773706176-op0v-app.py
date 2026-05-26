import os
import re
import threading
import tkinter as tk
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import requests
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)


class DownloadEngine:
    RESOURCE_MAP = {
        "img": ["src", "data-src", "data-original"],
        "script": ["src"],
        "link": ["href"],
        "video": ["src", "poster"],
        "audio": ["src"],
        "source": ["src", "srcset"],
        "iframe": ["src"],
        "embed": ["src"],
        "object": ["data"],
        "input": ["src"],
        "track": ["src"],
    }

    LINK_REL_RESOURCES = {"stylesheet", "icon", "shortcut icon", "apple-touch-icon", "apple-touch-icon-precomposed"}

    EXT_MAP = {
        "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tiff", ".tif", ".avif"},
        "css": {".css"},
        "js": {".js"},
        "fonts": {".woff", ".woff2", ".ttf", ".otf", ".eot"},
        "media": {".mp4", ".webm", ".ogg", ".mp3", ".wav", ".flac", ".aac", ".m4a"},
    }

    def __init__(self, url, save_dir, log_callback=None, progress_callback=None):
        self.url = url
        self.save_dir = Path(save_dir)
        self.log = log_callback or print
        self.progress = progress_callback or (lambda *a: None)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        self.session.verify = False
        self.downloaded = {}
        self.failed = []
        self.total_resources = 0
        self.completed_resources = 0
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def _get_ext_from_url(self, url):
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        name = path.rstrip("/").rsplit("/", 1)[-1]
        if "." in name:
            ext = "." + name.rsplit(".", 1)[-1].lower()
            ext = ext.split("?")[0].split("#")[0]
            if len(ext) <= 10:
                return ext
        return ""

    def _get_ext_from_content_type(self, content_type):
        if not content_type:
            return ""
        ct = content_type.lower().split(";")[0].strip()
        mime_map = {
            "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
            "image/webp": ".webp", "image/svg+xml": ".svg", "image/x-icon": ".ico",
            "image/bmp": ".bmp", "image/tiff": ".tiff", "image/avif": ".avif",
            "text/css": ".css",
            "application/javascript": ".js", "text/javascript": ".js",
            "application/x-javascript": ".js",
            "font/woff": ".woff", "font/woff2": ".woff2",
            "font/ttf": ".ttf", "font/otf": ".otf",
            "application/font-woff": ".woff", "application/font-woff2": ".woff2",
            "application/x-font-ttf": ".ttf", "application/x-font-otf": ".otf",
            "application/vnd.ms-fontobject": ".eot",
            "video/mp4": ".mp4", "video/webm": ".webm", "video/ogg": ".ogg",
            "audio/mpeg": ".mp3", "audio/wav": ".wav", "audio/ogg": ".ogg",
            "audio/flac": ".flac", "audio/aac": ".aac",
        }
        return mime_map.get(ct, "")

    def _classify_resource(self, url, content_type=""):
        ext = self._get_ext_from_url(url)
        if not ext:
            ext = self._get_ext_from_content_type(content_type)
        for category, exts in self.EXT_MAP.items():
            if ext in exts:
                return category
        if ext:
            return "other"
        return "other"

    def _make_local_path(self, url, content_type=""):
        category = self._classify_resource(url, content_type)
        ext = self._get_ext_from_url(url) or self._get_ext_from_content_type(content_type)
        if not ext:
            ext = ".bin"

        parsed = urllib.parse.urlparse(url)
        name = parsed.path.rstrip("/").rsplit("/", 1)[-1]
        if "." in name:
            base_name = name.rsplit(".", 1)[0]
        else:
            base_name = name or "resource"

        base_name = re.sub(r'[<>:"/\\|?*]', '_', base_name)
        if not base_name:
            base_name = "resource"

        subdir = self.save_dir / category
        counter = 0
        filename = f"{base_name}{ext}"
        while (subdir / filename).exists():
            counter += 1
            filename = f"{base_name}_{counter}{ext}"

        return subdir / filename, category

    def _resolve_url(self, base_url, ref_url):
        if not ref_url or ref_url.startswith("data:") or ref_url.startswith("javascript:"):
            return None
        if ref_url.startswith("//"):
            ref_url = "https:" + ref_url
        try:
            return urllib.parse.urljoin(base_url, ref_url)
        except Exception:
            return None

    def _download_file(self, url, timeout=30):
        if self._stop_flag:
            return None
        if url in self.downloaded:
            return self.downloaded[url]

        try:
            resp = self.session.get(url, timeout=timeout, stream=True)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            local_path, category = self._make_local_path(url, content_type)

            local_path.parent.mkdir(parents=True, exist_ok=True)

            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if self._stop_flag:
                        return None
                    if chunk:
                        f.write(chunk)

            self.downloaded[url] = local_path
            self.completed_resources += 1
            self.progress(self.completed_resources, self.total_resources)

            rel_path = os.path.relpath(local_path, self.save_dir)
            self.log(f"  ✓ [{category}] {rel_path}")
            return local_path

        except Exception as e:
            self.failed.append(url)
            self.completed_resources += 1
            self.progress(self.completed_resources, self.total_resources)
            self.log(f"  ✗ 下载失败: {url[:80]}... ({e})")
            return None

    def _extract_css_urls(self, css_content, css_url):
        urls = []
        pattern = r'url\s*\(\s*(?:["\']?)\s*([^)]*?)\s*(?:["\']?)\s*\)'
        for match in re.finditer(pattern, css_content, re.IGNORECASE):
            ref = match.group(1).strip().strip("'\"")
            if ref.startswith("data:"):
                continue
            resolved = self._resolve_url(css_url, ref)
            if resolved:
                urls.append(resolved)
        return urls

    def _rewrite_css_urls(self, css_content, css_url):
        def replace_url(match):
            prefix = match.group(1) or ""
            ref = match.group(2).strip().strip("'\"").strip()
            suffix = match.group(3) or ""
            if ref.startswith("data:"):
                return match.group(0)
            resolved = self._resolve_url(css_url, ref)
            if resolved and resolved in self.downloaded:
                local_path = self.downloaded[resolved]
                rel_path = os.path.relpath(local_path, self.save_dir).replace("\\", "/")
                return f'{prefix}url("{rel_path}"){suffix}'
            return match.group(0)

        pattern = r'(url\s*\(\s*["\']?)(.*?)(["\']?\s*\))'
        return re.sub(pattern, replace_url, css_content, flags=re.IGNORECASE)

    def _parse_html_resources(self, soup, base_url):
        resources = []

        for tag_name, attrs in self.RESOURCE_MAP.items():
            for tag in soup.find_all(tag_name):
                for attr in attrs:
                    if tag.has_attr(attr):
                        raw_val = tag[attr]
                        if attr == "srcset":
                            srcset_urls = self._parse_srcset(raw_val, base_url)
                            for orig_url, resolved_url in srcset_urls:
                                resources.append(resolved_url)
                        else:
                            resolved = self._resolve_url(base_url, raw_val)
                            if resolved:
                                if tag_name == "link" and tag.get("rel"):
                                    rel_values = [r.lower() for r in tag.get("rel", [])]
                                    if any(r in self.LINK_REL_RESOURCES for r in rel_values):
                                        resources.append(resolved)
                                elif tag_name != "link":
                                    resources.append(resolved)

        for tag in soup.find_all("meta", property="og:image"):
            if tag.has_attr("content"):
                resolved = self._resolve_url(base_url, tag["content"])
                if resolved:
                    resources.append(resolved)

        for tag in soup.find_all(style=True):
            style_content = tag["style"]
            css_urls = self._extract_css_urls(style_content, base_url)
            resources.extend(css_urls)

        return resources

    def _parse_srcset(self, srcset_val, base_url):
        results = []
        for part in srcset_val.split(","):
            part = part.strip()
            if not part:
                continue
            tokens = part.split()
            if tokens:
                url = tokens[0]
                resolved = self._resolve_url(base_url, url)
                if resolved:
                    results.append((url, resolved))
        return results

    def _rewrite_html(self, soup, base_url):
        for tag_name, attrs in self.RESOURCE_MAP.items():
            for tag in soup.find_all(tag_name):
                for attr in attrs:
                    if tag.has_attr(attr):
                        raw_val = tag[attr]
                        if attr == "srcset":
                            new_srcset = self._rewrite_srcset(raw_val, base_url)
                            tag[attr] = new_srcset
                        else:
                            resolved = self._resolve_url(base_url, raw_val)
                            if resolved and resolved in self.downloaded:
                                local_path = self.downloaded[resolved]
                                rel_path = os.path.relpath(local_path, self.save_dir).replace("\\", "/")
                                tag[attr] = rel_path

        for tag in soup.find_all("meta", property="og:image"):
            if tag.has_attr("content"):
                resolved = self._resolve_url(base_url, tag["content"])
                if resolved and resolved in self.downloaded:
                    local_path = self.downloaded[resolved]
                    rel_path = os.path.relpath(local_path, self.save_dir).replace("\\", "/")
                    tag["content"] = rel_path

        for tag in soup.find_all(style=True):
            style_content = tag["style"]
            tag["style"] = self._rewrite_css_urls(style_content, base_url)

        base_tag = soup.find("base")
        if base_tag:
            base_tag.decompose()

    def _rewrite_srcset(self, srcset_val, base_url):
        parts = []
        for part in srcset_val.split(","):
            part = part.strip()
            if not part:
                continue
            tokens = part.split()
            if tokens:
                url = tokens[0]
                descriptor = " ".join(tokens[1:])
                resolved = self._resolve_url(base_url, url)
                if resolved and resolved in self.downloaded:
                    local_path = self.downloaded[resolved]
                    rel_path = os.path.relpath(local_path, self.save_dir).replace("\\", "/")
                    tokens[0] = rel_path
                parts.append(" ".join(tokens))
        return ", ".join(parts)

    def _download_css_resources(self, css_url, css_path):
        try:
            with open(css_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return

        css_resource_urls = self._extract_css_urls(content, css_url)
        for url in css_resource_urls:
            if url not in self.downloaded:
                self._download_file(url)

        rewritten = self._rewrite_css_urls(content, css_url)
        try:
            with open(css_path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(rewritten)
        except Exception:
            pass

    def download(self):
        self.log(f"开始下载: {self.url}")
        self.log(f"保存目录: {self.save_dir}")
        self.downloaded = {}
        self.failed = []
        self.completed_resources = 0
        self._stop_flag = False

        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.log("\n[1/4] 获取网页内容...")
        try:
            resp = self.session.get(self.url, timeout=30)
            resp.raise_for_status()
            html_content = resp.text
        except Exception as e:
            self.log(f"✗ 获取网页失败: {e}")
            return False

        base_url = self.url
        soup = BeautifulSoup(html_content, "html.parser")

        base_tag = soup.find("base", href=True)
        if base_tag:
            base_url = urllib.parse.urljoin(self.url, base_tag["href"])

        self.log("\n[2/4] 解析网页资源...")
        resources = self._parse_html_resources(soup, base_url)
        resources = list(dict.fromkeys(resources))

        self.total_resources = len(resources)
        self.log(f"  发现 {self.total_resources} 个资源文件")

        self.log("\n[3/4] 下载资源文件...")
        self.progress(0, self.total_resources)

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._download_file, url): url for url in resources}
            for future in as_completed(futures):
                if self._stop_flag:
                    executor.shutdown(wait=False)
                    break
                try:
                    future.result()
                except Exception:
                    pass

        self.log("\n[4/4] 处理CSS内嵌资源并保存网页...")
        css_files = list(self.save_dir.glob("css/**/*.css"))
        for css_path in css_files:
            for url, local_path in self.downloaded.items():
                if local_path == css_path:
                    self._download_css_resources(url, css_path)
                    break

        self._rewrite_html(soup, base_url)

        title = soup.find("title")
        page_name = "index"
        if title and title.string:
            page_name = re.sub(r'[<>:"/\\|?*]', '_', title.string.strip())[:50]
            if not page_name:
                page_name = "index"

        html_path = self.save_dir / f"{page_name}.html"
        counter = 1
        while html_path.exists():
            html_path = self.save_dir / f"{page_name}_{counter}.html"
            counter += 1

        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(str(soup))
        except Exception:
            html_path = self.save_dir / "index.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

        self.log(f"\n{'='*50}")
        self.log(f"下载完成！")
        self.log(f"  成功: {len(self.downloaded)} 个文件")
        self.log(f"  失败: {len(self.failed)} 个文件")
        self.log(f"  页面: {html_path.name}")
        if self.failed:
            self.log(f"\n失败列表:")
            for url in self.failed[:20]:
                self.log(f"  - {url[:80]}")
            if len(self.failed) > 20:
                self.log(f"  ... 还有 {len(self.failed) - 20} 个失败项")

        return True


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("网页下载器")
        self.geometry("720x520")
        self.resizable(True, True)
        self.minsize(600, 400)

        self.engine = None
        self._init_style()
        self._build_ui()
        self._center_window()

    def _init_style(self):
        style = ttk.Style(self)
        style.theme_use("vista")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 14, "bold"))
        style.configure("Info.TLabel", font=("Microsoft YaHei UI", 9))
        style.configure("Action.TButton", font=("Microsoft YaHei UI", 10, "bold"), padding=6)
        style.configure("Stop.TButton", font=("Microsoft YaHei UI", 10), padding=6)

    def _build_ui(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="网页下载器", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 15))

        url_frame = ttk.LabelFrame(main, text=" 网址 ", padding=10)
        url_frame.pack(fill=tk.X, pady=(0, 10))

        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Consolas", 10))
        url_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))
        url_entry.bind("<Control-a>", lambda e: e.widget.select_range(0, tk.END))

        ttk.Button(
            url_frame, text="粘贴", command=self._paste_url, width=6
        ).pack(side=tk.RIGHT)

        dir_frame = ttk.LabelFrame(main, text=" 下载目录 ", padding=10)
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads", "webpage"))
        dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, font=("Consolas", 10))
        dir_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 5))

        ttk.Button(
            dir_frame, text="浏览", command=self._browse_dir, width=6
        ).pack(side=tk.RIGHT)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.download_btn = ttk.Button(
            btn_frame, text="▶ 开始下载", command=self._start_download, style="Action.TButton"
        )
        self.download_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.stop_btn = ttk.Button(
            btn_frame, text="■ 停止", command=self._stop_download, style="Stop.TButton", state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)

        self.open_btn = ttk.Button(
            btn_frame, text="📂 打开目录", command=self._open_dir, style="Stop.TButton"
        )
        self.open_btn.pack(side=tk.RIGHT)

        progress_frame = ttk.LabelFrame(main, text=" 进度 ", padding=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100, mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.status_var, style="Info.TLabel").pack(anchor=tk.W)

        log_frame = ttk.LabelFrame(main, text=" 日志 ", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_inner = ttk.Frame(log_frame)
        log_inner.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_inner, wrap=tk.WORD, font=("Consolas", 9),
            bg="#1e1e1e", fg="#d4d4d4", insertbackground="#d4d4d4",
            selectbackground="#264f78", state=tk.DISABLED, relief=tk.FLAT
        )
        scrollbar = ttk.Scrollbar(log_inner, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text.tag_configure("success", foreground="#6a9955")
        self.log_text.tag_configure("error", foreground="#f44747")
        self.log_text.tag_configure("info", foreground="#569cd6")
        self.log_text.tag_configure("header", foreground="#dcdcaa")

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"+{x}+{y}")

    def _paste_url(self):
        try:
            clip = self.clipboard_get()
            if clip:
                self.url_var.set(clip.strip())
        except tk.TclError:
            pass

    def _browse_dir(self):
        current = self.dir_var.get()
        if os.path.isdir(current):
            initial = current
        else:
            initial = os.path.expanduser("~")
        chosen = filedialog.askdirectory(initialdir=initial, title="选择下载目录")
        if chosen:
            self.dir_var.set(chosen)

    def _open_dir(self):
        path = self.dir_var.get()
        if os.path.isdir(path):
            os.startfile(path)
        else:
            messagebox.showwarning("提示", "目录不存在，请先下载网页")

    def _log(self, msg, tag="info"):
        def _append():
            self.log_text.configure(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state=tk.DISABLED)
        self.after(0, _append)

    def _update_progress(self, completed, total):
        def _update():
            if total > 0:
                pct = completed / total * 100
                self.progress_var.set(pct)
                self.status_var.set(f"下载进度: {completed}/{total} ({pct:.1f}%)")
            else:
                self.status_var.set("正在解析...")
        self.after(0, _update)

    def _start_download(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入网址")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_var.set(url)

        save_dir = self.dir_var.get().strip()
        if not save_dir:
            messagebox.showwarning("提示", "请指定下载目录")
            return

        self.download_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.open_btn.configure(state=tk.DISABLED)
        self.progress_var.set(0)
        self.status_var.set("正在下载...")

        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state=tk.DISABLED)

        self.engine = DownloadEngine(
            url=url,
            save_dir=save_dir,
            log_callback=self._log,
            progress_callback=self._update_progress,
        )

        thread = threading.Thread(target=self._run_download, daemon=True)
        thread.start()

    def _run_download(self):
        try:
            success = self.engine.download()
            if success:
                self._log("\n✓ 全部完成！", "success")
                self.after(0, lambda: self.status_var.set("下载完成！"))
            else:
                self._log("\n✗ 下载失败", "error")
                self.after(0, lambda: self.status_var.set("下载失败"))
        except Exception as e:
            self._log(f"\n✗ 发生错误: {e}", "error")
            self.after(0, lambda: self.status_var.set("下载出错"))
        finally:
            self.after(0, self._download_finished)

    def _download_finished(self):
        self.download_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.open_btn.configure(state=tk.NORMAL)
        self.engine = None

    def _stop_download(self):
        if self.engine:
            self.engine.stop()
            self._log("\n■ 正在停止...", "error")
            self.status_var.set("正在停止...")


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
