#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄小说下载器 (Tomato Novel Downloader)
基于 shareBookSource.json 配置文件的小说下载工具
支持：小说
"""

import json
import os
import sys
import time
import base64
import argparse
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from urllib.parse import urlencode, quote, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# 设置UTF-8编码（Windows兼容）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 尝试导入requests，如果不存在则给出友好提示
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("错误：需要安装 requests 库")
    print("请运行: pip install requests")
    sys.exit(1)


@dataclass
class BookInfo:
    """书籍信息数据类"""
    book_id: str
    title: str
    author: str
    cover_url: str
    abstract: str
    kind: str
    last_chapter: str
    word_count: str
    source: str = "番茄"
    tab: str = "小说"
    status: str = "未知"  # 连载状态：连载中/已完结


@dataclass
class Chapter:
    """章节信息数据类"""
    item_id: str
    title: str
    book_id: str = ""


@dataclass
class BookSource:
    """书源配置数据类"""
    name: str
    url: str
    source_type: int
    enabled: bool
    source: str = "番茄"
    tab: str = "小说"
    mode: int = 3


class BookSourceParser:
    """书源解析器"""

    def __init__(self, json_path: str):
        self.json_path = json_path
        self.sources: List[BookSource] = []
        self._parse()

    def _parse(self):
        """解析JSON配置文件"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for source_data in data:
                source = BookSource(
                    name=source_data.get('bookSourceName', 'Unknown'),
                    url=source_data.get('bookSourceUrl', ''),
                    source_type=source_data.get('bookSourceType', 0),
                    enabled=source_data.get('enabled', False),
                    source="番茄",
                    tab="小说",
                    mode=3
                )
                self.sources.append(source)

            print(f"✅ 成功加载 {len(self.sources)} 个书源")

        except FileNotFoundError:
            raise Exception(f"配置文件不存在: {self.json_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析错误: {e}")

    def get_enabled_sources(self) -> List[BookSource]:
        """获取启用的书源"""
        return [s for s in self.sources if s.enabled]

    def get_first_source(self) -> Optional[BookSource]:
        """获取第一个启用的书源"""
        enabled = self.get_enabled_sources()
        return enabled[0] if enabled else None


class TomatoAPI:
    """番茄小说API客户端"""

    def __init__(self, source: BookSource, timeout: int = 30):
        self.source = source
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """创建带有重试机制的HTTP会话"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # 设置请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
        })

        return session

    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """发送HTTP请求并返回JSON数据"""
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 网络请求失败: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return None

    def search(self, keyword: str, page: int = 1) -> List[BookInfo]:
        """搜索书籍"""
        url = f"{self.source.url}/search"
        params = {
            'q': keyword,
            'source': self.source.source,
            'tab': self.source.tab,
            'page': page
        }

        print(f"🔍 正在搜索: {keyword} ...")
        data = self._make_request(url, params)

        if not data or 'results' not in data:
            print("⚠️ 未找到结果")
            return []

        books = []
        for item in data['results']:
            book = BookInfo(
                book_id=str(item.get('book_id', '')),
                title=item.get('title', 'Unknown'),
                author=item.get('author', 'Unknown'),
                cover_url=item.get('cover_url', ''),
                abstract=item.get('abstract', ''),
                kind=item.get('kind', ''),
                last_chapter=item.get('last_chapter', ''),
                word_count=item.get('word_count', ''),
                source=self.source.source,
                tab=self.source.tab
            )
            books.append(book)

        print(f"✅ 找到 {len(books)} 本书")
        return books

    def get_book_detail(self, book_id: str) -> Optional[BookInfo]:
        """获取书籍详情"""
        url = f"{self.source.url}/detail"
        params = {
            'book_id': book_id,
            'source': self.source.source,
            'tab': self.source.tab
        }

        print(f"📖 获取书籍详情: {book_id} ...")
        data = self._make_request(url, params)

        if not data or 'data' not in data:
            return None

        item = data['data']
        return BookInfo(
            book_id=str(item.get('book_id', book_id)),
            title=item.get('title', 'Unknown'),
            author=item.get('author', 'Unknown'),
            cover_url=item.get('cover_url', ''),
            abstract=item.get('abstract', ''),
            kind=item.get('kind', ''),
            last_chapter=item.get('last_chapter', ''),
            word_count=item.get('word_count', ''),
            source=self.source.source,
            tab=self.source.tab
        )

    def get_chapters(self, book_id: str) -> List[Chapter]:
        """获取章节列表"""
        url = f"{self.source.url}/catalog"
        params = {
            'book_id': book_id,
            'source': self.source.source,
            'tab': self.source.tab
        }

        print(f"📑 获取章节列表: {book_id} ...")
        data = self._make_request(url, params)

        if not data or 'chapters' not in data:
            print("⚠️ 未找到章节")
            return []

        chapters = []
        for item in data['chapters']:
            chapter = Chapter(
                item_id=str(item.get('item_id', '')),
                title=item.get('title', 'Unknown'),
                book_id=book_id
            )
            chapters.append(chapter)

        print(f"✅ 找到 {len(chapters)} 个章节")
        return chapters

    def get_content(self, book_id: str, item_id: str) -> Optional[str]:
        """获取章节内容"""
        url = f"{self.source.url}/content"
        params = {
            'book_id': book_id,
            'item_id': item_id,
            'source': self.source.source,
            'tab': self.source.tab
        }

        data = self._make_request(url, params)

        if not data or not data.get('success') or 'data' not in data:
            return None

        content = data['data']

        # 处理不同类型的内容
        if self.source.tab == '短剧':
            # 短剧返回视频链接
            return f"[视频链接] {content}"
        elif self.source.tab == '听书':
            # 听书返回音频链接
            return f"[音频链接] {content}"
        else:
            # 小说、漫画返回HTML内容
            return content

    def check_vip_status(self, book_id: str) -> Dict:
        """检查书籍的VIP/付费状态"""
        url = f"{self.source.url}/detail"
        params = {
            'book_id': book_id,
            'source': self.source.source,
            'tab': self.source.tab
        }

        data = self._make_request(url, params)
        
        vip_info = {
            'is_vip': False,
            'free_chapters': 0,
            'total_chapters': 0,
            'has_paid': False,
            'message': ''
        }
        
        if not data or 'data' not in data:
            vip_info['message'] = '无法获取VIP信息'
            return vip_info
        
        book_data = data['data']
        
        # 检查是否有VIP标识或付费信息
        vip_info['is_vip'] = book_data.get('is_vip', False) or book_data.get('need_pay', False)
        vip_info['free_chapters'] = book_data.get('free_chapter_count', 0)
        vip_info['total_chapters'] = book_data.get('chapter_count', 0)
        vip_info['has_paid'] = book_data.get('has_purchased', False)
        
        if vip_info['is_vip']:
            if vip_info['free_chapters'] > 0:
                vip_info['message'] = f"该书为VIP小说，前{vip_info['free_chapters']}章免费，后续章节需要付费"
            else:
                vip_info['message'] = "该书为VIP小说，所有章节需要付费"
        else:
            vip_info['message'] = "该书为免费小说"
        
        return vip_info


class NovelDownloader:
    """小说下载器主类"""

    def __init__(self, source_parser: BookSourceParser, output_dir: str = "downloads"):
        self.source_parser = source_parser
        self.output_dir = output_dir
        self.api: Optional[TomatoAPI] = None
        self._setup_output_dir()

    def parse_fanqie_url(self, url: str) -> Optional[str]:
        """解析番茄小说链接，提取book_id
        
        支持的链接格式：
        - https://fanqienovel.com/page/7143038691944959011
        - https://fanqienovel.com/page/7143038691944959011?enter_from=...
        - https://changdunovel.com/t/GkUmePmt_bE/ (分享短链接)
        - 纯数字ID: 7143038691944959011
        """
        if not url:
            return None
        
        # 如果是纯数字，直接返回
        if url.isdigit():
            return url
        
        try:
            # 解析URL
            parsed = urlparse(url)
            path = parsed.path
            
            # 提取page后面的数字ID
            match = re.search(r'/page/(\d+)', path)
            if match:
                return match.group(1)
            
            # 处理changdunovel.com分享短链接
            if 'changdunovel.com' in parsed.netloc and '/t/' in path:
                print(f"⚠️  检测到分享短链接，需要访问获取真实ID")
                print(f"   短链接: {url}")
                print(f"   提示：请手动访问该链接，从跳转后的URL中获取book_id")
                print(f"   或使用完整URL格式: https://fanqienovel.com/page/BOOK_ID")
                return None
            
            # 尝试从查询参数中获取
            query_params = parse_qs(parsed.query)
            if 'book_id' in query_params:
                return query_params['book_id'][0]
            
            return None
        except Exception as e:
            print(f"❌ 解析链接失败: {e}")
            return None

    def _setup_output_dir(self):
        """创建输出目录"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📁 创建下载目录: {self.output_dir}")

    def select_source(self) -> bool:
        """选择书源"""
        sources = self.source_parser.get_enabled_sources()

        if not sources:
            print("❌ 没有可用的书源")
            return False

        if len(sources) == 1:
            self.api = TomatoAPI(sources[0])
            print(f"✅ 使用书源: {sources[0].name}")
            return True

        print("\n📚 可用书源:")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source.name} ({source.url})")

        while True:
            try:
                choice = input("\n请选择书源 (输入数字): ").strip()
                index = int(choice) - 1
                if 0 <= index < len(sources):
                    self.api = TomatoAPI(sources[index])
                    print(f"✅ 已选择: {sources[index].name}")
                    return True
                else:
                    print("⚠️ 无效的选择")
            except ValueError:
                print("⚠️ 请输入数字")

    def set_novel_mode(self):
        """设置为小说模式（默认）"""
        self.api.source.tab = "小说"
        self.api.source.mode = 3
        print("📖 内容类型: 小说")

    def analyze_links(self, urls: List[str], auto_download: bool = False, max_workers: int = 10):
        """分析一个或多个番茄小说链接，显示详细信息
        
        Args:
            urls: 链接列表
            auto_download: 是否自动下载，默认False
            max_workers: 并发下载线程数，默认10
        """
        if not self.api:
            print("❌ 请先选择书源")
            return False
        
        self.set_novel_mode()
        
        print("\n" + "=" * 80)
        print("🔗 番茄小说链接分析器")
        if auto_download:
            print("⚡ 模式: 自动下载")
        else:
            print("📋 模式: 仅分析")
        print("=" * 80)
        
        success_count = 0
        failed_count = 0
        downloaded_books = []
        
        for idx, url in enumerate(urls, 1):
            print(f"\n[{idx}/{len(urls)}] 正在分析: {url}")
            print("-" * 80)
            
            # 解析book_id
            book_id = self.parse_fanqie_url(url)
            if not book_id:
                print(f"❌ 无法解析链接: {url}")
                failed_count += 1
                continue
            
            print(f"✅ 解析成功，Book ID: {book_id}")
            
            # 获取书籍详情
            book = self.api.get_book_detail(book_id)
            if not book:
                print(f"❌ 无法获取书籍信息: {book_id}")
                failed_count += 1
                continue
            
            # 检查VIP状态
            vip_info = self.api.check_vip_status(book_id)
            
            # 确定连载状态
            if '完结' in book.last_chapter or '完本' in book.kind:
                book.status = "已完结"
            elif '连载' in book.kind:
                book.status = "连载中"
            else:
                # 根据章节数判断（如果有数据）
                if vip_info['total_chapters'] > 0:
                    book.status = "连载中" if vip_info['total_chapters'] < 1000 else "已完结"
                else:
                    book.status = "未知"
            
            # 显示详细信息表格
            self.display_book_info_table(book, vip_info)
            
            success_count += 1
            
            # 如果开启自动下载，直接开始下载
            if auto_download:
                print("\n⚡ 自动下载模式：开始下载...")
                try:
                    downloader_result = self.download_book(book, max_workers=max_workers)
                    if downloader_result:
                        downloaded_books.append(book.title)
                        print(f"✅ 《{book.title}》下载完成")
                    else:
                        print(f"❌ 《{book.title}》下载失败")
                        failed_count += 1
                except Exception as e:
                    print(f"❌ 下载《{book.title}》时出错: {e}")
                    failed_count += 1
            
            # 如果不是最后一个，添加分隔线
            if idx < len(urls) and not auto_download:
                print("\n")
        
        # 总结
        print("\n" + "=" * 80)
        print("📊 分析总结")
        print("=" * 80)
        print(f"总计: {len(urls)} 个链接")
        print(f"成功: {success_count} 个")
        print(f"失败: {failed_count} 个")
        
        if auto_download and downloaded_books:
            print(f"\n✅ 已自动下载 {len(downloaded_books)} 本小说:")
            for title in downloaded_books:
                print(f"   📖 {title}")
        
        print("=" * 80)
        
        return success_count > 0

    def search_books(self, keyword: str) -> List[BookInfo]:
        """搜索书籍"""
        if not self.api:
            print("❌ 请先选择书源")
            return []
        return self.api.search(keyword)

    def display_books(self, books: List[BookInfo]):
        """显示书籍列表"""
        if not books:
            print("📭 没有找到书籍")
            return

        print("\n" + "=" * 80)
        print(f"{'序号':<6}{'书名':<30}{'作者':<20}{'分类':<15}")
        print("=" * 80)

        for i, book in enumerate(books, 1):
            title = book.title[:28] + ".." if len(book.title) > 30 else book.title
            author = book.author[:18] + ".." if len(book.author) > 20 else book.author
            kind = book.kind[:13] + ".." if len(book.kind) > 15 else book.kind
            print(f"{i:<6}{title:<30}{author:<20}{kind:<15}")

        print("=" * 80)

    def display_book_info_table(self, book: BookInfo, vip_info: Dict = None):
        """以表格形式显示单本书的详细信息"""
        print("\n" + "=" * 80)
        print("📖 小说信息详情")
        print("=" * 80)
        
        # 基本信息表格
        print(f"\n{'项目':<20}{'内容'}")
        print("-" * 80)
        print(f"{'书名':<20}{book.title}")
        print(f"{'作者':<20}{book.author}")
        print(f"{'小说ID':<20}{book.book_id}")
        print(f"{'分类':<20}{book.kind}")
        print(f"{'字数':<20}{book.word_count}")
        print(f"{'最新章节':<20}{book.last_chapter}")
        print(f"{'连载状态':<20}{book.status}")
        
        # VIP信息
        if vip_info:
            print(f"{'付费状态':<20}{vip_info['message']}")
            if vip_info['is_vip']:
                print(f"{'免费章节':<20}{vip_info['free_chapters']} 章")
                print(f"{'总章节数':<20}{vip_info['total_chapters']} 章")
        
        print("-" * 80)
        
        # 文件命名建议
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', book.title)
        safe_author = re.sub(r'[\\/*?:"<>|]', '_', book.author)
        suggested_filename = f"{safe_title} - {safe_author}.txt"
        print(f"\n💾 建议文件名: {suggested_filename}")
        
        # VIP提醒
        if vip_info and vip_info['is_vip']:
            print("\n⚠️  VIP/付费提醒:")
            print(f"   {vip_info['message']}")
            if vip_info['free_chapters'] > 0:
                print(f"   前 {vip_info['free_chapters']} 章可以免费下载")
                print(f"   后续章节需要付费或VIP权限")
            else:
                print(f"   所有章节都需要付费或VIP权限")
            print("   提示：本工具只能下载免费章节，付费章节无法下载")
        
        print("=" * 80)

    def select_book(self, books: List[BookInfo]) -> Optional[BookInfo]:
        """从列表中选择书籍"""
        if not books:
            return None

        while True:
            try:
                choice = input("\n请选择书籍 (输入数字, 0返回搜索): ").strip()
                if choice == "0":
                    return None
                index = int(choice) - 1
                if 0 <= index < len(books):
                    book = books[index]
                    print(f"\n📖 选中书籍:")
                    print(f"   书名: {book.title}")
                    print(f"   作者: {book.author}")
                    print(f"   分类: {book.kind}")
                    print(f"   简介: {book.abstract[:100]}...")
                    return book
                else:
                    print("⚠️ 无效的选择")
            except ValueError:
                print("⚠️ 请输入数字")

    def download_book(self, book: BookInfo, max_workers: int = 10, progress_callback: Callable = None):
        """下载整本书（并发版本）

        Args:
            book: 书籍信息
            max_workers: 并发下载线程数，默认10
            progress_callback: 进度回调函数
        """
        if not self.api:
            print("❌ API未初始化")
            return False

        # 获取章节列表
        chapters = self.api.get_chapters(book.book_id)
        if not chapters:
            print("❌ 无法获取章节列表")
            return False

        # 创建书籍目录
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", book.title)
        book_dir = os.path.join(self.output_dir, safe_title)
        if not os.path.exists(book_dir):
            os.makedirs(book_dir)

        # 创建章节目录
        chapter_dir = os.path.join(book_dir, "chapters")
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        # 保存书籍信息
        self._save_book_info(book, book_dir)

        print(f"\n📥 开始下载: {book.title}")
        print(f"   共 {len(chapters)} 章")
        print(f"   并发数: {max_workers}")
        print("-" * 50)

        # 用于线程安全的计数器和锁
        success_count = [0]
        failed_chapters = []
        progress_lock = threading.Lock()
        print_lock = threading.Lock()
        completed_count = [0]

        def print_progress():
            """打印进度条"""
            with print_lock:
                percent = completed_count[0] / len(chapters) * 100
                bar_length = 30
                filled = int(bar_length * completed_count[0] / len(chapters))
                bar = '█' * filled + '░' * (bar_length - filled)
                print(f"\r  📊 [{bar}] {completed_count[0]}/{len(chapters)} ({percent:.1f}%)", end='', flush=True)

        def download_single_chapter(args):
            """下载单个章节的任务函数"""
            index, chapter = args
            try:
                content = self.api.get_content(book.book_id, chapter.item_id)

                if content:
                    self._save_chapter(book_dir, chapter, content)
                    with progress_lock:
                        success_count[0] += 1
                    return True
                else:
                    with progress_lock:
                        failed_chapters.append(chapter)
                    return False

            except Exception as e:
                with progress_lock:
                    failed_chapters.append(chapter)
                return False
            finally:
                with progress_lock:
                    completed_count[0] += 1
                print_progress()

        # 使用线程池并发下载
        start_time = time.time()
        print_progress()  # 显示初始进度

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            futures = {executor.submit(download_single_chapter, (i+1, ch)): i
                      for i, ch in enumerate(chapters)}

            # 等待所有任务完成
            for future in as_completed(futures):
                if progress_callback:
                    idx = futures[future]
                    progress_callback(idx + 1, len(chapters), chapters[idx].title)

        elapsed_time = time.time() - start_time
        print()  # 换行
        print("-" * 50)
        print(f"✅ 下载完成: {success_count[0]}/{len(chapters)} 章成功")
        print(f"⏱️  用时: {elapsed_time:.2f} 秒")
        print(f"🚀 平均速度: {len(chapters)/elapsed_time:.2f} 章/秒")

        if failed_chapters:
            print(f"⚠️ {len(failed_chapters)} 章下载失败")
            self._save_failed_chapters(book_dir, failed_chapters)

        # 合并为单文件
        self._merge_chapters(book_dir, book, chapters)

        return True

    def _save_book_info(self, book: BookInfo, book_dir: str):
        """保存书籍信息"""
        info_path = os.path.join(book_dir, "book_info.txt")
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"书名: {book.title}\n")
            f.write(f"作者: {book.author}\n")
            f.write(f"分类: {book.kind}\n")
            f.write(f"字数: {book.word_count}\n")
            f.write(f"最新章节: {book.last_chapter}\n")
            f.write(f"简介: {book.abstract}\n")
            f.write(f"封面: {book.cover_url}\n")

    def _save_chapter(self, book_dir: str, chapter: Chapter, content: str):
        """保存单个章节"""
        # 清理文件名
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", chapter.title)
        filename = f"{chapter.item_id}_{safe_title}.txt"
        filepath = os.path.join(book_dir, "chapters", filename)

        # 创建章节目录
        chapter_dir = os.path.join(book_dir, "chapters")
        if not os.path.exists(chapter_dir):
            os.makedirs(chapter_dir)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"{chapter.title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(content)

    def _save_failed_chapters(self, book_dir: str, chapters: List[Chapter]):
        """保存下载失败的章节列表"""
        failed_path = os.path.join(book_dir, "failed_chapters.txt")
        with open(failed_path, 'w', encoding='utf-8') as f:
            for ch in chapters:
                f.write(f"{ch.item_id}: {ch.title}\n")

    def _merge_chapters(self, book_dir: str, book: BookInfo, chapters: List[Chapter]):
        """合并所有章节为单个文件，并删除单章文件"""
        merged_path = os.path.join(book_dir, f"{re.sub(r'[\\\\/*?:\"<>|]', '_', book.title)}_完整版.txt")

        print(f"\n📄 正在合并章节...")

        with open(merged_path, 'w', encoding='utf-8') as f:
            f.write(f"《{book.title}》\n")
            f.write(f"作者: {book.author}\n")
            f.write(f"{'=' * 50}\n\n")

            for chapter in chapters:
                safe_title = re.sub(r'[\\/*?:"<>|]', "_", chapter.title)
                chapter_path = os.path.join(book_dir, "chapters", f"{chapter.item_id}_{safe_title}.txt")

                if os.path.exists(chapter_path):
                    with open(chapter_path, 'r', encoding='utf-8') as cf:
                        f.write(cf.read())
                    f.write("\n\n")

        print(f"✅ 已合并为单文件: {merged_path}")

        # 删除单章文件和chapters目录
        chapter_dir = os.path.join(book_dir, "chapters")
        if os.path.exists(chapter_dir):
            deleted_count = 0
            for chapter in chapters:
                safe_title = re.sub(r'[\\/*?:"<>|]', "_", chapter.title)
                chapter_path = os.path.join(chapter_dir, f"{chapter.item_id}_{safe_title}.txt")
                if os.path.exists(chapter_path):
                    try:
                        os.remove(chapter_path)
                        deleted_count += 1
                    except Exception:
                        pass

            # 尝试删除chapters目录
            try:
                os.rmdir(chapter_dir)
                print(f"🗑️  已清理临时文件: {deleted_count} 个单章文件已删除")
            except Exception:
                print(f"🗑️  已清理 {deleted_count} 个单章文件")


def interactive_mode(downloader: NovelDownloader, default_workers: int = 10):
    """交互式模式"""
    print("\n" + "=" * 50)
    print("🍅 番茄小说下载器")
    print("=" * 50)

    # 选择书源
    if not downloader.select_source():
        return

    # 设置为小说模式
    downloader.set_novel_mode()

    # 设置并发数
    workers = default_workers
    try:
        workers_input = input(f"\n⚡ 设置并发下载线程数 (默认{default_workers}, 建议5-20): ").strip()
        if workers_input:
            workers = int(workers_input)
            if workers < 1:
                workers = 1
            elif workers > 50:
                print("⚠️ 并发数过大，已调整为50")
                workers = 50
    except ValueError:
        print(f"⚠️ 输入无效，使用默认值 {default_workers}")

    print(f"✅ 并发下载线程数: {workers}")

    while True:
        print("\n" + "-" * 50)
        print("请选择操作:")
        print("  1. 搜索小说")
        print("  2. 分析链接")
        print("  3. 退出")
        choice = input("\n请输入选项 (1/2/3): ").strip()
        
        if choice == '3' or choice.lower() == 'q':
            print("👋 再见!")
            break
        
        elif choice == '2':
            # 分析链接模式
            print("\n🔗 请输入番茄小说链接（可以输入多个，用逗号或换行分隔）")
            print("示例: https://fanqienovel.com/page/7143038691944959011")
            print("输入 'done' 或空行结束输入:\n")
            
            urls = []
            while True:
                line = input().strip()
                if line.lower() == 'done' or (not line and urls):
                    break
                if line:
                    # 支持逗号分隔的多个链接
                    parts = [p.strip() for p in line.split(',') if p.strip()]
                    urls.extend(parts)
            
            if urls:
                # 询问是否自动下载
                auto_choice = input("\n是否自动下载这些小说? (y/n, 默认n): ").strip().lower()
                auto_download = auto_choice == 'y'
                
                if auto_download:
                    downloader.analyze_links(urls, auto_download=True, max_workers=workers)
                else:
                    downloader.analyze_links(urls, auto_download=False)
            else:
                print("⚠️ 未输入任何链接")
        
        elif choice == '1':
            # 搜索模式
            keyword = input("\n🔍 请输入搜索关键词: ").strip()
            
            if not keyword:
                print("⚠️ 关键词不能为空")
                continue
            
            # 搜索书籍
            books = downloader.search_books(keyword)
            
            if not books:
                continue
            
            # 显示并选择书籍
            downloader.display_books(books)
            book = downloader.select_book(books)
            
            if not book:
                continue
            
            # 确认下载
            confirm = input(f"\n确认下载《{book.title}》? (y/n): ").strip().lower()
            if confirm == 'y':
                def progress(current, total, title):
                    pass  # 进度已在download_book中显示
                
                downloader.download_book(book, max_workers=workers, progress_callback=progress)
        
        else:
            print("⚠️ 无效的选项")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='番茄小说下载器 - 从番茄小说下载小说',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                           # 交互式模式
  %(prog)s -s "斗破苍穹"              # 搜索书籍
  %(prog)s -d <book_id>              # 直接下载指定书籍
  %(prog)s -o ./my_books             # 指定输出目录
  %(prog)s -d <book_id> -w 20        # 使用20线程并发下载
  %(prog)s -a <url1> <url2>          # 分析多个链接
  %(prog)s -a "https://fanqienovel.com/page/7143038691944959011"  # 分析单个链接
        """
    )

    parser.add_argument('-c', '--config',
                        default='shareBookSource.json',
                        help='书源配置文件路径 (默认: shareBookSource.json)')
    parser.add_argument('-o', '--output',
                        default='downloads',
                        help='下载输出目录 (默认: downloads)')
    parser.add_argument('-s', '--search',
                        help='搜索关键词')
    parser.add_argument('-d', '--download',
                        help='直接下载指定书籍ID')
    parser.add_argument('-a', '--analyze',
                        nargs='+',
                        help='分析一个或多个番茄小说链接')
    parser.add_argument('--auto-download',
                        action='store_true',
                        help='分析链接后自动下载（配合 -a 使用）')
    parser.add_argument('-w', '--workers',
                        type=int,
                        default=10,
                        help='并发下载线程数，默认10，建议5-20之间')

    args = parser.parse_args()

    # 检查配置文件路径
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)

    try:
        # 解析书源
        source_parser = BookSourceParser(config_path)

        # 创建下载器
        downloader = NovelDownloader(source_parser, args.output)

        if args.analyze:
            # 分析链接模式
            if not downloader.select_source():
                return
            downloader.analyze_links(args.analyze, auto_download=args.auto_download, max_workers=args.workers)

        elif args.search:
            # 搜索模式
            if not downloader.select_source():
                return
            downloader.set_novel_mode()
            books = downloader.search_books(args.search)
            downloader.display_books(books)

        elif args.download:
            # 直接下载模式
            if not downloader.select_source():
                return
            downloader.set_novel_mode()
            book = downloader.api.get_book_detail(args.download)
            if book:
                downloader.download_book(book, max_workers=args.workers)
            else:
                print(f"❌ 无法获取书籍信息: {args.download}")

        else:
            # 交互式模式
            interactive_mode(downloader, default_workers=args.workers)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断操作")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
