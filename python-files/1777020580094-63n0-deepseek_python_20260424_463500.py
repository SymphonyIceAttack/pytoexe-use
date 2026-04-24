import os
import re
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# -------------------- 爬虫核心 --------------------
class ImageCrawler:
    def __init__(self, start_url, save_dir, max_workers=5, log_callback=None):
        self.start_url = start_url
        self.save_dir = save_dir
        self.max_workers = max_workers
        self.log = log_callback if log_callback else print

        # 解析域名，限定爬取范围
        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc
        self.base_scheme = parsed.scheme

        # 去重集合
        self.visited_pages = set()      # 已爬取的页面 URL
        self.downloaded_images = set()  # 已下载的图片 URL（或归一化后的 URL）

        # 停止事件
        self.stop_event = threading.Event()

        # 线程池
        self.executor = None

        # 设置请求头，模拟浏览器
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/125.0.0.0 Safari/537.36'
        })

        # 可选：读取 robots.txt（礼貌爬取）
        self.rp = None
        try:
            robots_url = f"{self.base_scheme}://{self.base_domain}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            self.rp = rp
        except Exception:
            pass

    def can_fetch(self, url):
        """检查 robots.txt 是否允许爬取"""
        if self.rp is None:
            return True
        try:
            return self.rp.can_fetch(self.session.headers['User-Agent'], url)
        except Exception:
            return True

    def normalize_url(self, url):
        """去除 URL 片段，用于去重"""
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ''))

    def is_same_domain(self, url):
        """检查是否属于同一域名"""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain

    def is_image_url(self, url):
        """简单判断 URL 是否指向图片（也可以后续用 Content-Type 确认）"""
        image_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in image_ext)

    def download_image(self, img_url):
        """下载单张图片，若成功则保存"""
        if self.stop_event.is_set():
            return

        # 去重（归一化后比较）
        norm = self.normalize_url(img_url)
        if norm in self.downloaded_images:
            return
        self.downloaded_images.add(norm)

        try:
            resp = self.session.get(img_url, stream=True, timeout=10)
            if resp.status_code != 200:
                self.log(f"[下载失败] 状态码 {resp.status_code}: {img_url}")
                return

            # 确认 Content-Type 是图片
            content_type = resp.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                self.log(f"[跳过] 非图片内容类型 {content_type}: {img_url}")
                return

            # 从 URL 或 Content-Type 推断扩展名
            ext = self.get_extension(img_url, content_type)
            # 生成文件名（使用 URL 的哈希避免重名）
            import hashlib
            name = hashlib.md5(img_url.encode()).hexdigest()[:12] + ext
            filepath = os.path.join(self.save_dir, name)

            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    if self.stop_event.is_set():
                        return
                    f.write(chunk)
            self.log(f"[下载成功] {img_url} -> {name}")
        except Exception as e:
            self.log(f"[下载异常] {img_url}: {e}")

    def get_extension(self, url, content_type):
        """根据 URL 或 Content-Type 获取文件扩展名"""
        # 优先从 URL 提取
        parsed = urlparse(url)
        path = parsed.path.lower()
        ext_map = {
            '.jpg': '.jpg', '.jpeg': '.jpg',
            '.png': '.png', '.gif': '.gif',
            '.bmp': '.bmp', '.webp': '.webp',
            '.svg': '.svg'
        }
        for ext, target in ext_map.items():
            if path.endswith(ext):
                return target
        # 从 Content-Type 推断
        ct_map = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/svg+xml': '.svg'
        }
        return ct_map.get(content_type.split(';')[0].strip(), '.jpg')

    def extract_images_and_links(self, html, page_url):
        """从 HTML 中提取图片链接和下一页链接"""
        soup = BeautifulSoup(html, 'html.parser')
        images = []
        links = []

        # 提取所有 <img> 标签的 src
        for img in soup.find_all('img', src=True):
            src = img['src']
            full_url = urljoin(page_url, src)
            if self.is_image_url(full_url):
                images.append(full_url)

        # 提取“下一页”链接
        # 常见模式：rel="next"，文本包含“下一页”“>”“»”“next”
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip().lower()
            rel = a.get('rel', [])
            if 'next' in rel:
                next_url = urljoin(page_url, href)
                if self.is_same_domain(next_url):
                    links.append(next_url)
                    continue

            # 文本匹配
            if any(kw in text for kw in ['next', '下一页', '>', '»', '后页', '下页']):
                next_url = urljoin(page_url, href)
                if self.is_same_domain(next_url):
                    links.append(next_url)
        return images, links

    def crawl_page(self, url):
        """爬取单个页面：下载图片，返回发现的子页面链接"""
        if self.stop_event.is_set():
            return []

        if not self.can_fetch(url):
            self.log(f"[跳过] robots.txt 禁止访问: {url}")
            return []

        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code != 200:
                self.log(f"[页面错误] 状态码 {resp.status_code}: {url}")
                return []
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' not in content_type:
                return []  # 非 HTML 页面不解析
            html = resp.text
        except Exception as e:
            self.log(f"[页面请求异常] {url}: {e}")
            return []

        images, next_links = self.extract_images_and_links(html, url)

        # 下载当前页面中的图片（多线程）
        if images:
            self.log(f"[页面图片] 发现 {len(images)} 张图片: {url}")
            futures = []
            for img_url in images:
                if self.stop_event.is_set():
                    break
                futures.append(self.executor.submit(self.download_image, img_url))
            # 等待完成，但不阻塞停止检测
            for f in as_completed(futures):
                if self.stop_event.is_set():
                    break
                try:
                    f.result()
                except Exception:
                    pass

        return next_links

    def start(self):
        """主爬虫逻辑：广度优先遍历页面"""
        if not os.path.isdir(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        # 使用队列进行 BFS
        queue = [self.start_url]
        self.visited_pages.add(self.normalize_url(self.start_url))

        while queue and not self.stop_event.is_set():
            current_url = queue.pop(0)
            self.log(f"[正在爬取页面] {current_url}")
            next_links = self.crawl_page(current_url)
            for link in next_links:
                norm_link = self.normalize_url(link)
                if norm_link not in self.visited_pages:
                    self.visited_pages.add(norm_link)
                    queue.append(link)

        self.executor.shutdown(wait=True)
        if self.stop_event.is_set():
            self.log("[已停止] 用户中止了爬虫。")
        else:
            self.log("[完成] 所有页面已爬取完毕。")

    def stop(self):
        """停止爬虫"""
        self.stop_event.set()
        self.log("[停止] 正在停止，请稍候...")

# -------------------- 图形界面 --------------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("通用图片爬虫 v1.0")
        self.root.geometry("700x550")
        self.root.resizable(True, True)

        self.crawler = None
        self.crawl_thread = None

        # 主框架
        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # URL 输入
        ttk.Label(main_frame, text="网站链接:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar(value="https://example.com")
        url_entry = ttk.Entry(main_frame, textvariable=self.url_var, width=60)
        url_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W+tk.E, padx=5)

        # 保存目录
        ttk.Label(main_frame, text="保存目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dir_var = tk.StringVar(value=os.path.join(os.getcwd(), "downloaded_images"))
        dir_entry = ttk.Entry(main_frame, textvariable=self.dir_var, width=50)
        dir_entry.grid(row=1, column=1, sticky=tk.W+tk.E, padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_dir).grid(row=1, column=2, sticky=tk.W)

        # 线程数
        ttk.Label(main_frame, text="线程数:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.thread_var = tk.IntVar(value=5)
        thread_spin = ttk.Spinbox(main_frame, from_=1, to=20, textvariable=self.thread_var, width=5)
        thread_spin.grid(row=2, column=1, sticky=tk.W, padx=5)

        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        self.start_btn = ttk.Button(btn_frame, text="开始爬取", command=self.start_crawl)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self.stop_crawl, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # 日志区域
        ttk.Label(main_frame, text="日志:").grid(row=4, column=0, sticky=tk.W)
        self.log_text = scrolledtext.ScrolledText(main_frame, height=20, state='normal')
        self.log_text.grid(row=5, column=0, columnspan=3, sticky=tk.NSEW, pady=5)

        # 让界面可伸缩
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)

        self.log("欢迎使用图片爬虫。请设置链接、目录和线程数，然后点击“开始爬取”。")

    def browse_dir(self):
        directory = filedialog.askdirectory(initialdir=self.dir_var.get())
        if directory:
            self.dir_var.set(directory)

    def log(self, message):
        """线程安全地添加日志"""
        def _append():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def start_crawl(self):
        url = self.url_var.get().strip()
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("错误", "请输入有效的网址（以 http:// 或 https:// 开头）")
            return
        save_dir = self.dir_var.get().strip()
        if not save_dir:
            messagebox.showerror("错误", "请选择保存目录")
            return
        threads = self.thread_var.get()
        if threads < 1:
            messagebox.showerror("错误", "线程数至少为1")
            return

        # 创建爬虫实例
        self.crawler = ImageCrawler(url, save_dir, max_workers=threads, log_callback=self.log)
        # 启动爬虫线程（避免阻塞 GUI）
        self.crawl_thread = threading.Thread(target=self.crawler.start, daemon=True)
        self.crawl_thread.start()

        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.log(f"[启动] 开始爬取: {url}")

        # 监控爬虫线程是否结束
        self.monitor_thread()

    def stop_crawl(self):
        if self.crawler:
            self.crawler.stop()
        self.stop_btn.config(state=tk.DISABLED)

    def monitor_thread(self):
        """定期检查爬虫线程是否结束，以便恢复按钮状态"""
        if self.crawl_thread and self.crawl_thread.is_alive():
            self.root.after(500, self.monitor_thread)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.log("[状态] 爬虫已停止或完成。")

# -------------------- 程序入口 --------------------
if __name__ == "__main__":
    # 检查必要的第三方库
    try:
        import requests
        import bs4
    except ImportError:
        import sys
        print("请先安装依赖：pip install requests beautifulsoup4")
        sys.exit(1)

    root = tk.Tk()
    app = App(root)
    root.mainloop()