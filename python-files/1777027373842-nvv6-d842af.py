#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纯标准库图片爬虫 - 无需安装任何第三方库
用法：python crawler.py [网址] [保存目录] [线程数]
"""

import os
import re
import sys
import time
import hashlib
import threading
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from urllib.robotparser import RobotFileParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser

# -------------------- HTML 解析器 --------------------
class ImageAndLinkParser(HTMLParser):
    """解析 HTML，提取 <img src> 和下一页链接"""
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.images = []
        self.next_links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'img':
            src = dict(attrs).get('src')
            if src:
                full_url = urljoin(self.base_url, src)
                self.images.append(full_url)
        elif tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href')
            if not href:
                return
            full_url = urljoin(self.base_url, href)
            rel = attrs_dict.get('rel', '')
            # 检查 rel="next"
            if 'next' in rel.split():
                self.next_links.append(full_url)
                return
            # 检查链接文本
            # 注意：需要获取链接文本，但 handle_data 需单独处理，这里简化直接添加
            # 稍后会在 handle_data 结合 context 完成
            self._current_a = href, full_url

    def handle_data(self, data):
        # 检查当前 <a> 标签的文本是否包含下一页关键词
        if hasattr(self, '_current_a'):
            text = data.strip().lower()
            if any(kw in text for kw in ['next', '下一页', '>', '»', '后页', '下页']):
                self.next_links.append(self._current_a[1])
            self._current_a = None

# -------------------- 爬虫核心 --------------------
class ImageCrawler:
    def __init__(self, start_url, save_dir, max_workers=5):
        self.start_url = start_url
        self.save_dir = save_dir
        self.max_workers = max_workers

        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc
        self.base_scheme = parsed.scheme

        self.visited_pages = set()
        self.downloaded_images = set()

        self.stop_event = threading.Event()
        self.executor = None

        # 设置请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/125.0.0.0 Safari/537.36'
        }

        # robots.txt 支持
        self.rp = None
        try:
            robots_url = f"{self.base_scheme}://{self.base_domain}/robots.txt"
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            self.rp = rp
        except Exception:
            pass

    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def can_fetch(self, url):
        if self.rp is None:
            return True
        try:
            return self.rp.can_fetch(self.headers['User-Agent'], url)
        except Exception:
            return True

    def normalize_url(self, url):
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, ''))

    def is_same_domain(self, url):
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain

    def is_image_url(self, url):
        image_ext = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg')
        parsed = urlparse(url)
        path = parsed.path.lower()
        return any(path.endswith(ext) for ext in image_ext)

    def download_image(self, img_url):
        if self.stop_event.is_set():
            return

        norm = self.normalize_url(img_url)
        if norm in self.downloaded_images:
            return
        self.downloaded_images.add(norm)

        try:
            req = Request(img_url, headers=self.headers)
            with urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    self.log(f"[下载失败] 状态码 {resp.status}: {img_url}")
                    return
                content_type = resp.headers.get('Content-Type', '')
                if not content_type.startswith('image/'):
                    self.log(f"[跳过] 非图片类型 {content_type}: {img_url}")
                    return

                ext = self.get_extension(img_url, content_type)
                name = hashlib.md5(img_url.encode()).hexdigest()[:12] + ext
                filepath = os.path.join(self.save_dir, name)

                with open(filepath, 'wb') as f:
                    while True:
                        if self.stop_event.is_set():
                            return
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                self.log(f"[下载成功] {img_url} -> {name}")
        except Exception as e:
            self.log(f"[下载异常] {img_url}: {e}")

    def get_extension(self, url, content_type):
        parsed = urlparse(url)
        path = parsed.path.lower()
        ext_map = {'.jpg': '.jpg', '.jpeg': '.jpg', '.png': '.png', '.gif': '.gif',
                   '.bmp': '.bmp', '.webp': '.webp', '.svg': '.svg'}
        for ext, target in ext_map.items():
            if path.endswith(ext):
                return target
        ct_map = {
            'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
            'image/bmp': '.bmp', 'image/webp': '.webp', 'image/svg+xml': '.svg'
        }
        return ct_map.get(content_type.split(';')[0].strip(), '.jpg')

    def fetch_page(self, url):
        """使用 urllib 获取页面 HTML"""
        try:
            req = Request(url, headers=self.headers)
            with urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    self.log(f"[页面错误] 状态码 {resp.status}: {url}")
                    return None
                content_type = resp.headers.get('Content-Type', '')
                if 'text/html' not in content_type:
                    return None
                html = resp.read().decode('utf-8', errors='ignore')
                return html
        except HTTPError as e:
				self.log(f"[HTTP错误] {url}: 状态码 {e.code} - {e.reason}")
		except URLError as e:
				self.log(f"[连接错误] {url}: 可能是网络不通或DNS解析失败 ({e.reason})")
		except Exception as e:
				self.log(f"[其他异常] {url}: {type(e).__name__} - {e}")
            return None

    def crawl_page(self, url):
        if self.stop_event.is_set():
            return []

        if not self.can_fetch(url):
            self.log(f"[跳过] robots.txt 禁止访问: {url}")
            return []

        html = self.fetch_page(url)
        if html is None:
            return []

        parser = ImageAndLinkParser(url)
        parser.feed(html)
        parser.close()

        images = parser.images
        next_links = [link for link in parser.next_links if self.is_same_domain(link)]

        # 过滤图片 URL（只保留明确是图片的链接）
        images = [img for img in images if self.is_image_url(img)]

        if images:
            self.log(f"[页面图片] 发现 {len(images)} 张图片: {url}")
            futures = []
            for img_url in images:
                if self.stop_event.is_set():
                    break
                futures.append(self.executor.submit(self.download_image, img_url))
            for f in as_completed(futures):
                if self.stop_event.is_set():
                    break
                try:
                    f.result()
                except Exception:
                    pass
        return next_links

    def start(self):
        if not os.path.isdir(self.save_dir):
            os.makedirs(self.save_dir, exist_ok=True)

        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        queue = [self.start_url]
        self.visited_pages.add(self.normalize_url(self.start_url))

        try:
            while queue and not self.stop_event.is_set():
                current_url = queue.pop(0)
                self.log(f"[正在爬取页面] {current_url}")
                next_links = self.crawl_page(current_url)
                for link in next_links:
                    norm_link = self.normalize_url(link)
                    if norm_link not in self.visited_pages:
                        self.visited_pages.add(norm_link)
                        queue.append(link)
        except KeyboardInterrupt:
            self.log("\n[用户中断] 正在停止所有线程...")
            self.stop_event.set()
        finally:
            self.executor.shutdown(wait=True)
            if self.stop_event.is_set():
                self.log("[已停止] 爬虫已中止。")
            else:
                self.log("[完成] 所有页面已爬取完毕。")

# -------------------- 命令行交互 --------------------
def main():
    print("=" * 60)
    print(" 图片爬虫 v2.1 (纯标准库)")
    print("=" * 60)

    # 如果提供了命令行参数，直接使用
    if len(sys.argv) >= 4:
        url = sys.argv[1]
        save_dir = sys.argv[2]
        try:
            threads = int(sys.argv[3])
        except ValueError:
            print("线程数必须为整数")
            sys.exit(1)
    else:
        # 如果无法交互（例如重定向或在线沙箱），使用默认值
        if not sys.stdin.isatty():
            print("[提示] 检测到非交互式环境，使用默认配置：")
            url = "https://manb.cc/"  # 示例，请修改为你需要的地址
            save_dir = "./images"
            threads = 5
            print(f"  网址: {url}")
            print(f"  保存目录: {os.path.abspath(save_dir)}")
            print(f"  线程数: {threads}")
        else:
            # 交互模式原样保留
            url = input("请输入目标网址: ").strip()
            if not url.startswith(('http://', 'https://')):
                print("错误：网址必须以 http:// 或 https:// 开头")
                sys.exit(1)
            save_dir = input("请输入图片保存目录 (默认: ./images): ").strip()
            if not save_dir:
                save_dir = "./images"
            threads_str = input("请输入下载线程数 (默认: 5): ").strip()
            if not threads_str:
                threads = 5
            else:
                try:
                    threads = int(threads_str)
                    if threads < 1:
                        raise ValueError
                except ValueError:
                    print("错误：线程数必须为正整数")
                    sys.exit(1)

    print(f"\n配置确认：\n  网址: {url}\n  保存目录: {os.path.abspath(save_dir)}\n  线程数: {threads}")
    print("\n按 Ctrl+C 可随时停止爬取。")

    crawler = ImageCrawler(url, save_dir, max_workers=threads)
    crawler.start()

if __name__ == "__main__":
    main()