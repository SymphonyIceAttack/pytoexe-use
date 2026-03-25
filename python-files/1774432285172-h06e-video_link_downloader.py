import os
import re
import threading
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


APP_TITLE = "公开视频链接下载器"
DEFAULT_TIMEOUT = 20
CHUNK_SIZE = 1024 * 256
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".ogv", ".ogg"}
VIDEO_CONTENT_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime",
    "video/ogg",
    "application/octet-stream",
}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


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

        title = ttk.Label(
            frame,
            text="公开视频链接下载器",
            font=("Microsoft YaHei UI", 15, "bold"),
        )
        title.pack(anchor="w", pady=(0, 10))

        hint = ttk.Label(
            frame,
            text=(
                "支持两种输入：\n"
                "1. 公开视频直链（如 .mp4 / .webm）\n"
                "2. 页面链接（程序会只提取页面中公开可见的 HTML5 视频地址）\n"
                "不支持受保护流媒体、DRM、登录后内容或绕过站点限制。"
            ),
            justify="left",
        )
        hint.pack(anchor="w", pady=(0, 12))

        url_row = ttk.Frame(frame)
        url_row.pack(fill="x", pady=6)
        ttk.Label(url_row, text="链接：", width=8).pack(side="left")
        ttk.Entry(url_row, textvariable=self.url_var).pack(side="left", fill="x", expand=True)

        dir_row = ttk.Frame(frame)
        dir_row.pack(fill="x", pady=6)
        ttk.Label(dir_row, text="保存到：", width=8).pack(side="left")
        ttk.Entry(dir_row, textvariable=self.save_dir_var).pack(side="left", fill="x", expand=True)
        ttk.Button(dir_row, text="选择文件夹", command=self.choose_dir).pack(side="left", padx=(8, 0))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x", pady=10)
        ttk.Button(btn_row, text="开始下载", command=self.start_download).pack(side="left")
        ttk.Button(btn_row, text="清空日志", command=self.clear_log).pack(side="left", padx=(8, 0))

        progress = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        progress.pack(fill="x", pady=(4, 8))

        status = ttk.Label(frame, textvariable=self.status_var)
        status.pack(anchor="w", pady=(0, 10))

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

        worker = threading.Thread(target=self._download_flow, args=(url, save_dir), daemon=True)
        worker.start()

    def _download_flow(self, input_url: str, save_dir: str):
        try:
            self.set_status("正在分析链接…")
            self.log(f"输入链接：{input_url}")

            session = requests.Session()
            session.headers.update({"User-Agent": USER_AGENT})

            if self.is_direct_video_url(input_url):
                self.log("检测为视频直链，准备直接下载。")
                self.download_file(session, input_url, save_dir)
                self.set_status("下载完成")
                return

            self.log("检测为网页链接，准备解析页面中的公开视频地址。")
            html, final_page_url = self.fetch_page(session, input_url)
            candidates = self.extract_video_candidates(html, final_page_url)

            if not candidates:
                raise RuntimeError(
                    "没有在页面里找到公开暴露的视频地址。\n"
                    "这个页面可能不是标准 HTML5 视频页，或者视频由脚本动态加载/受保护。"
                )

            self.log("找到以下候选地址：")
            for idx, item in enumerate(candidates, start=1):
                self.log(f"  {idx}. {item}")

            chosen = self.pick_best_candidate(session, candidates)
            self.log(f"最终选择：{chosen}")
            self.download_file(session, chosen, save_dir, referer=final_page_url)
            self.set_status("下载完成")

        except Exception as exc:
            self.set_status("下载失败")
            self.log(f"错误：{exc}")
            messagebox.showerror(APP_TITLE, str(exc))

    @staticmethod
    def is_direct_video_url(url: str) -> bool:
        path = urlparse(url).path.lower()
        return any(path.endswith(ext) for ext in VIDEO_EXTENSIONS)

    def fetch_page(self, session: requests.Session, url: str):
        resp = session.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        content_type = (resp.headers.get("Content-Type") or "").lower()
        if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
            raise RuntimeError(f"这个链接返回的不是普通网页，而是：{content_type or '未知类型'}")
        resp.encoding = resp.encoding or resp.apparent_encoding
        self.log(f"页面获取成功：{resp.url}")
        return resp.text, resp.url

    def extract_video_candidates(self, html: str, base_url: str):
        soup = BeautifulSoup(html, "html.parser")
        found = []

        for tag in soup.select("video[src], source[src]"):
            src = tag.get("src", "").strip()
            if src:
                found.append(urljoin(base_url, src))

        meta_selectors = [
            ('meta[property="og:video"]', "content"),
            ('meta[property="og:video:url"]', "content"),
            ('meta[name="twitter:player:stream"]', "content"),
            ('meta[name="twitter:player:stream:content_type"]', "content"),
        ]
        for selector, attr in meta_selectors:
            for tag in soup.select(selector):
                value = tag.get(attr, "").strip()
                if value.startswith("http"):
                    found.append(value)

        # 从源码中补捞常见公开视频直链
        regex = re.compile(r'https?://[^\s"\'""<>]+(?:\.mp4|\.webm|\.mov|\.m4v|\.ogv|\.ogg)(?:\?[^\s"\'""<>]*)?', re.IGNORECASE)
        found.extend(regex.findall(html))

        cleaned = []
        seen = set()
        for item in found:
            item = item.strip()
            if not item:
                continue
            if item.startswith("//"):
                item = "https:" + item
            if item.startswith("/"):
                item = urljoin(base_url, item)
            parsed = urlparse(item)
            ext = os.path.splitext(parsed.path.lower())[1]
            if ext not in VIDEO_EXTENSIONS and not item.startswith("http"):
                continue
            if item not in seen:
                seen.add(item)
                cleaned.append(item)
        return cleaned

    def pick_best_candidate(self, session: requests.Session, candidates):
        valid = []
        for url in candidates:
            try:
                info = self.probe_video(session, url)
                if info["is_video"]:
                    valid.append(info)
                    self.log(
                        f"已验证：{url} | 类型={info['content_type']} | 大小={info['content_length'] or '未知'}"
                    )
                else:
                    self.log(f"跳过非视频资源：{url}")
            except Exception as exc:
                self.log(f"探测失败，跳过：{url} | {exc}")

        if not valid:
            raise RuntimeError("虽然找到了候选地址，但都不像公开可下载的视频文件。")

        valid.sort(key=lambda x: x["content_length"] or 0, reverse=True)
        return valid[0]["url"]

    def probe_video(self, session: requests.Session, url: str):
        headers = {"User-Agent": USER_AGENT}
        try:
            resp = session.head(url, allow_redirects=True, timeout=DEFAULT_TIMEOUT, headers=headers)
            if resp.status_code >= 400 or not resp.headers:
                raise RuntimeError("HEAD 不可用")
        except Exception:
            resp = session.get(url, stream=True, allow_redirects=True, timeout=DEFAULT_TIMEOUT, headers=headers)

        content_type = (resp.headers.get("Content-Type") or "").split(";")[0].lower()
        content_length = resp.headers.get("Content-Length")
        try:
            content_length = int(content_length) if content_length else None
        except ValueError:
            content_length = None

        parsed = urlparse(resp.url)
        ext = os.path.splitext(parsed.path.lower())[1]
        is_video = content_type in VIDEO_CONTENT_TYPES or ext in VIDEO_EXTENSIONS

        if hasattr(resp, "close"):
            resp.close()

        return {
            "url": resp.url,
            "content_type": content_type,
            "content_length": content_length,
            "is_video": is_video,
        }

    def download_file(self, session: requests.Session, url: str, save_dir: str, referer: str | None = None):
        headers = {"User-Agent": USER_AGENT}
        if referer:
            headers["Referer"] = referer

        with session.get(url, stream=True, timeout=DEFAULT_TIMEOUT, headers=headers) as resp:
            resp.raise_for_status()
            total_size = resp.headers.get("Content-Length")
            try:
                total_size = int(total_size) if total_size else None
            except ValueError:
                total_size = None

            filename = self.guess_filename(resp.url, resp.headers)
            file_path = self.resolve_duplicate_name(os.path.join(save_dir, filename))
            self.log(f"保存路径：{file_path}")

            downloaded = 0
            with open(file_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    if not chunk:
                        continue
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
            name = unquote(match.group(1)).strip()
            return VideoDownloaderApp.sanitize_filename(name)

        path = urlparse(url).path
        name = os.path.basename(path) or "video.mp4"
        name = unquote(name)
        ext = os.path.splitext(name)[1].lower()
        if not ext:
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
        index = 1
        while True:
            new_path = f"{base}_{index}{ext}"
            if not os.path.exists(new_path):
                return new_path
            index += 1


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoDownloaderApp(root)
    root.mainloop()
