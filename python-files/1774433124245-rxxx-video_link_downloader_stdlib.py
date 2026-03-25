import os
import re
import threading
import tkinter as tk
from html.parser import HTMLParser
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urljoin, urlparse, unquote
from urllib.request import Request, urlopen


APP_TITLE = "公开视频链接下载器（标准库版）"
DEFAULT_TIMEOUT = 20
CHUNK_SIZE = 1024 * 256
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".ogv", ".ogg"}


class VideoHTMLParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.candidates = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        src = ""
        if tag in ("video", "source"):
            src = attrs.get("src", "").strip()
        elif tag == "meta":
            prop = attrs.get("property", "") or attrs.get("name", "")
            if prop in ("og:video", "og:video:url", "twitter:player:stream"):
                src = attrs.get("content", "").strip()

        if src:
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                src = urljoin(self.base_url, src)
            self.candidates.append(src)


class VideoDownloaderApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("760x560")

        self.url_var = tk.StringVar()
        self.save_dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Downloads"))
        self.status_var = tk.StringVar(value="就绪")
        self.progress_var = tk.DoubleVar(value=0)

        self._build_ui()

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=14)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=APP_TITLE,
            font=("Microsoft YaHei UI", 15, "bold"),
        ).pack(anchor="w", pady=(0, 10))

        ttk.Label(
            frame,
            text=(
                "支持两种输入：\n"
                "1. 公开视频直链（如 .mp4 / .webm）\n"
                "2. 页面链接（程序会只提取页面中公开可见的 HTML5 视频地址）\n"
                "不支持受保护流媒体、DRM、登录后内容或绕过站点限制。"
            ),
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=6)
        ttk.Label(row1, text="链接：", width=8).pack(side="left")
        ttk.Entry(row1, textvariable=self.url_var).pack(side="left", fill="x", expand=True)

        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=6)
        ttk.Label(row2, text="保存到：", width=8).pack(side="left")
        ttk.Entry(row2, textvariable=self.save_dir_var).pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="选择文件夹", command=self.choose_dir).pack(side="left", padx=(8, 0))

        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=10)
        ttk.Button(row3, text="开始下载", command=self.start_download).pack(side="left")
        ttk.Button(row3, text="清空日志", command=self.clear_log).pack(side="left", padx=(8, 0))

        ttk.Progressbar(frame, variable=self.progress_var, maximum=100).pack(fill="x", pady=(4, 8))
        ttk.Label(frame, textvariable=self.status_var).pack(anchor="w", pady=(0, 10))

        ttk.Label(frame, text="日志：").pack(anchor="w")
        self.log_text = tk.Text(frame, wrap="word", height=22)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def choose_dir(self):
        directory = filedialog.askdirectory(initialdir=self.save_dir_var.get() or os.path.expanduser("~"))
        if directory:
            self.save_dir_var.set(directory)

    def clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def log(self, message: str):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    def start_download(self):
        url = self.url_var.get().strip()
        save_dir = self.save_dir_var.get().strip()

        if not url:
            messagebox.showwarning(APP_TITLE, "请输入链接。")
            return
        if not save_dir:
            messagebox.showwarning(APP_TITLE, "请选择保存目录。")
            return

        os.makedirs(save_dir, exist_ok=True)
        self.progress_var.set(0)

        threading.Thread(target=self._download_flow, args=(url, save_dir), daemon=True).start()

    def _download_flow(self, input_url: str, save_dir: str):
        try:
            self.set_status("正在分析链接…")
            self.log(f"输入链接：{input_url}")

            if self.is_direct_video_url(input_url):
                self.log("检测为视频直链，准备直接下载。")
                self.download_file(input_url, save_dir)
                self.set_status("下载完成")
                return

            self.log("检测为网页链接，准备解析页面中的公开视频地址。")
            html, final_page_url = self.fetch_page(input_url)
            candidates = self.extract_video_candidates(html, final_page_url)

            if not candidates:
                raise RuntimeError(
                    "没有在页面里找到公开暴露的视频地址。\n"
                    "这个页面可能不是标准 HTML5 视频页，或者视频由脚本动态加载/受保护。"
                )

            self.log("找到以下候选地址：")
            for i, item in enumerate(candidates, 1):
                self.log(f"  {i}. {item}")

            chosen = candidates[0]
            self.log(f"最终选择：{chosen}")
            self.download_file(chosen, save_dir, referer=final_page_url)
            self.set_status("下载完成")

        except Exception as exc:
            self.set_status("下载失败")
            self.log(f"错误：{exc}")
            messagebox.showerror(APP_TITLE, str(exc))

    @staticmethod
    def is_direct_video_url(url: str) -> bool:
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in VIDEO_EXTENSIONS)

    def fetch_page(self, url: str):
        req = Request(url, headers={"User-Agent": self.user_agent()})
        with urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            content_type = (resp.headers.get_content_type() or "").lower()
            if content_type != "text/html":
                raise RuntimeError(f"这个链接返回的不是普通网页，而是：{content_type or '未知类型'}")
            html = resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="ignore")
            return html, resp.geturl()

    def extract_video_candidates(self, html: str, base_url: str):
        parser = VideoHTMLParser(base_url)
        parser.feed(html)

        regex = re.compile(
            r'https?://[^\s"\'<>]+(?:\.mp4|\.webm|\.mov|\.m4v|\.ogv|\.ogg)(?:\?[^\s"\'<>]*)?',
            re.IGNORECASE,
        )
        found = list(parser.candidates) + regex.findall(html)

        cleaned, seen = [], set()
        for item in found:
            item = item.strip()
            if not item:
                continue
            if item.startswith("//"):
                item = "https:" + item
            elif item.startswith("/"):
                item = urljoin(base_url, item)

            parsed = urlparse(item)
            ext = os.path.splitext(parsed.path.lower())[1]
            if ext not in VIDEO_EXTENSIONS and not item.startswith("http"):
                continue

            if item not in seen:
                seen.add(item)
                cleaned.append(item)
        return cleaned

    def download_file(self, url: str, save_dir: str, referer: str | None = None):
        headers = {"User-Agent": self.user_agent()}
        if referer:
            headers["Referer"] = referer

        req = Request(url, headers=headers)
        with urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            total_size = resp.headers.get("Content-Length")
            try:
                total_size = int(total_size) if total_size else None
            except ValueError:
                total_size = None

            filename = self.guess_filename(resp.geturl(), resp.headers)
            file_path = self.resolve_duplicate_name(os.path.join(save_dir, filename))
            self.log(f"保存路径：{file_path}")

            downloaded = 0
            with open(file_path, "wb") as f:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    self.update_progress(downloaded, total_size)

            self.progress_var.set(100)
            self.log("下载完成。")
            self.log(f"文件已保存：{file_path}")
            messagebox.showinfo(APP_TITLE, f"下载完成：\n{file_path}")

    def update_progress(self, downloaded: int, total_size: int | None):
        if total_size and total_size > 0:
            percent = min(downloaded / total_size * 100, 100)
            self.progress_var.set(percent)
            mb_done = downloaded / 1024 / 1024
            mb_total = total_size / 1024 / 1024
            self.set_status(f"下载中… {percent:.1f}% ({mb_done:.2f} / {mb_total:.2f} MB)")
        else:
            mb_done = downloaded / 1024 / 1024
            self.set_status(f"下载中… 已下载 {mb_done:.2f} MB")

    @staticmethod
    def guess_filename(url: str, headers) -> str:
        cd = headers.get("Content-Disposition", "")
        match = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, re.IGNORECASE)
        if match:
            return VideoDownloaderApp.sanitize_filename(unquote(match.group(1)).strip())

        path = urlparse(url).path
        name = os.path.basename(path) or "video.mp4"
        name = unquote(name)
        if not os.path.splitext(name)[1]:
            name += ".mp4"
        return VideoDownloaderApp.sanitize_filename(name)

    @staticmethod
    def sanitize_filename(name: str) -> str:
        name = re.sub(r'[\\/:*?"<>|]', "_", name)
        return name[:180] if len(name) > 180 else name

    @staticmethod
    def resolve_duplicate_name(path: str) -> str:
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 1
        while True:
            candidate = f"{base}_{i}{ext}"
            if not os.path.exists(candidate):
                return candidate
            i += 1

    @staticmethod
    def user_agent() -> str:
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()
