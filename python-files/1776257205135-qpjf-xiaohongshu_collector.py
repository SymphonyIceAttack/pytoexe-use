"""
小红书爆款文案自动采集工具
功能：
1. 自动搜索指定类目的笔记
2. 筛选爆款内容（点赞≥1000）
3. 提取标题、内容、互动数据
4. 导出到 Excel 文件
5. 支持定时每周更新

作者：卢冲
创建时间：2026-04-15
"""

import asyncio
import csv
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


# ==================== 配置区域 ====================
class Config:
    """采集配置"""
    
    # 搜索关键词列表
    KEYWORDS = [
        "家居布艺",
        "家纺", 
        "图片绘画",
        "家装",
        "软装",
        "氛围感"
    ]
    
    # 爆款判定标准（点赞数阈值）
    MIN_LIKES = 1000
    
    # 每个关键词采集的笔记数量上限
    MAX_NOTES_PER_KEYWORD = 50
    
    # 输出目录
    OUTPUT_DIR = Path(__file__).parent / "xiaohongshu_data"
    
    # 输出文件格式
    OUTPUT_FORMAT = "excel"  # 可选："excel", "csv", "markdown"
    
    # 浏览器设置
    HEADLESS = False  # True 为无头模式，False 显示浏览器窗口
    TIMEOUT = 60000  # 页面加载超时时间（毫秒）
    
    # 请求延迟（避免被封）
    REQUEST_DELAY = 2  # 秒
    SCROLL_DELAY = 1  # 秒


# ==================== 数据采集器 ====================
class XiaohongshuCollector:
    """小红书数据采集器"""
    
    def __init__(self, config: Config):
        self.config = config
        self.output_dir = config.OUTPUT_DIR
        self.output_dir.mkdir(exist_ok=True)
        
        # 数据存储
        self.collected_notes: List[Dict] = []
        
    async def collect(self):
        """执行采集任务"""
        print(f"\n{'='*60}")
        print(f"小红书爆款文案采集工具")
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config.HEADLESS,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            page = await context.new_page()
            
            try:
                for keyword in self.config.KEYWORDS:
                    print(f"\n📌 正在采集关键词：【{keyword}】")
                    notes = await self._search_and_collect(page, keyword)
                    self.collected_notes.extend(notes)
                    print(f"✅ 完成【{keyword}】，采集到 {len(notes)} 篇笔记")
                    
                    # 关键词之间延迟
                    if keyword != self.config.KEYWORDS[-1]:
                        await asyncio.sleep(self.config.REQUEST_DELAY)
                        
            except Exception as e:
                print(f"\n❌ 采集过程中出错：{e}")
                import traceback
                traceback.print_exc()
            finally:
                await browser.close()
        
        # 保存数据
        self._save_data()
        
        print(f"\n{'='*60}")
        print(f"采集完成！")
        print(f"总计采集：{len(self.collected_notes)} 篇笔记")
        print(f"保存位置：{self.output_dir}")
        print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
    async def _search_and_collect(self, page: Page, keyword: str) -> List[Dict]:
        """搜索并采集指定关键词的笔记"""
        notes = []
        
        try:
            # 构建搜索 URL
            search_url = f"https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_notes"
            
            # 访问搜索页面
            await page.goto(search_url, timeout=self.config.TIMEOUT, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)  # 等待页面加载
            
            # 滚动页面加载更多笔记
            await self._scroll_to_load_more(page, scroll_times=5)
            
            # 提取笔记列表
            note_elements = await page.query_selector_all('.note-item')
            
            if not note_elements:
                # 尝试其他选择器（小红书可能更新 DOM 结构）
                note_elements = await page.query_selector_all('[data-type="note"]')
            
            print(f"   找到 {len(note_elements)} 个笔记元素")
            
            for i, element in enumerate(note_elements[:self.config.MAX_NOTES_PER_KEYWORD]):
                try:
                    note_data = await self._extract_note_data(element, page, keyword)
                    if note_data and self._is_baokuan(note_data):
                        notes.append(note_data)
                        print(f"   ✓ 爆款 #{len(notes)}: {note_data['title'][:30]}... (点赞:{note_data['likes']})")
                    
                    # 笔记之间延迟
                    if i < len(note_elements) - 1:
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    print(f"   ⚠ 提取第 {i+1} 个笔记失败：{e}")
                    continue
                    
        except Exception as e:
            print(f"   ❌ 搜索【{keyword}】失败：{e}")
            
        return notes
    
    async def _extract_note_data(self, element, page: Page, keyword: str) -> Optional[Dict]:
        """从笔记元素中提取数据"""
        try:
            # 提取标题
            title_elem = await element.query_selector('.title')
            title = await title_elem.inner_text() if title_elem else ""
            
            # 提取作者
            author_elem = await element.query_selector('.username')
            author = await author_elem.inner_text() if author_elem else "未知"
            
            # 提取点赞数
            like_elem = await element.query_selector('.like-count')
            like_text = await like_elem.inner_text() if like_elem else "0"
            likes = self._parse_number(like_text)
            
            # 提取收藏数
            collect_elem = await element.query_selector('.collect-count')
            collect_text = await collect_elem.inner_text() if collect_elem else "0"
            collects = self._parse_number(collect_text)
            
            # 提取评论数
            comment_elem = await element.query_selector('.comment-count')
            comment_text = await comment_elem.inner_text() if comment_elem else "0"
            comments = self._parse_number(comment_text)
            
            # 提取笔记链接
            link_elem = await element.query_selector('a')
            link = await link_elem.get_attribute('href') if link_elem else ""
            if link and not link.startswith('http'):
                link = f"https://www.xiaohongshu.com{link}"
            
            # 提取发布时间（如果有）
            time_elem = await element.query_selector('.time')
            publish_time = await time_elem.inner_text() if time_elem else ""
            
            # 尝试获取笔记正文内容（需要点击进入详情页）
            content = ""
            # 注意：这里可以选择是否点击进入详情页获取完整内容
            # 为了速度，我们先只采集列表页信息
            
            return {
                "keyword": keyword,
                "title": title.strip(),
                "author": author.strip(),
                "likes": likes,
                "collects": collects,
                "comments": comments,
                "publish_time": publish_time.strip(),
                "link": link,
                "content": content,
                "collect_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"      提取数据异常：{e}")
            return None
    
    def _parse_number(self, text: str) -> int:
        """解析数字字符串（处理 '1.2 万' 这样的格式）"""
        if not text:
            return 0
        
        text = text.strip()
        
        try:
            if '万' in text:
                num = float(text.replace('万', ''))
                return int(num * 10000)
            elif 'k' in text.lower():
                num = float(text.lower().replace('k', ''))
                return int(num * 1000)
            else:
                # 提取数字
                match = re.search(r'\d+', text)
                return int(match.group()) if match else 0
        except:
            return 0
    
    def _is_baokuan(self, note: Dict) -> bool:
        """判断是否为爆款笔记"""
        return note['likes'] >= self.config.MIN_LIKES
    
    async def _scroll_to_load_more(self, page: Page, scroll_times: int = 5):
        """滚动页面加载更多笔记"""
        for i in range(scroll_times):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(self.config.SCROLL_DELAY)
    
    def _save_data(self):
        """保存采集的数据"""
        if not self.collected_notes:
            print("\n⚠ 没有采集到数据，跳过保存")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存为 Excel
        if self.config.OUTPUT_FORMAT == "excel":
            self._save_to_excel(timestamp)
        
        # 保存为 CSV
        if self.config.OUTPUT_FORMAT in ["csv", "excel"]:
            self._save_to_csv(timestamp)
        
        # 保存为 Markdown
        if self.config.OUTPUT_FORMAT == "markdown":
            self._save_to_markdown(timestamp)
    
    def _save_to_excel(self, timestamp: str):
        """保存为 Excel 文件"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(self.collected_notes)
            
            # 重新排列列顺序
            columns_order = [
                "keyword", "title", "author", "likes", "collects", 
                "comments", "publish_time", "link", "content", "collect_date"
            ]
            df = df[columns_order]
            
            # 中文列名
            column_names = {
                "keyword": "关键词",
                "title": "标题",
                "author": "作者",
                "likes": "点赞数",
                "collects": "收藏数",
                "comments": "评论数",
                "publish_time": "发布时间",
                "link": "链接",
                "content": "正文内容",
                "collect_date": "采集时间"
            }
            df = df.rename(columns=column_names)
            
            filename = self.output_dir / f"小红书爆款文案_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            print(f"\n📊 Excel 文件已保存：{filename}")
            
        except ImportError:
            print("\n⚠ 未安装 pandas/openpyxl，跳过 Excel 导出")
            print("   请运行：pip install pandas openpyxl")
        except Exception as e:
            print(f"\n❌ Excel 保存失败：{e}")
    
    def _save_to_csv(self, timestamp: str):
        """保存为 CSV 文件"""
        try:
            filename = self.output_dir / f"小红书爆款文案_{timestamp}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = [
                    "关键词", "标题", "作者", "点赞数", "收藏数",
                    "评论数", "发布时间", "链接", "正文内容", "采集时间"
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for note in self.collected_notes:
                    row = {
                        "关键词": note["keyword"],
                        "标题": note["title"],
                        "作者": note["author"],
                        "点赞数": note["likes"],
                        "收藏数": note["collects"],
                        "评论数": note["comments"],
                        "发布时间": note["publish_time"],
                        "链接": note["link"],
                        "正文内容": note["content"],
                        "采集时间": note["collect_date"]
                    }
                    writer.writerow(row)
            
            print(f"📄 CSV 文件已保存：{filename}")
            
        except Exception as e:
            print(f"❌ CSV 保存失败：{e}")
    
    def _save_to_markdown(self, timestamp: str):
        """保存为 Markdown 文件"""
        try:
            filename = self.output_dir / f"小红书爆款文案_{timestamp}.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# 小红书爆款文案合集\n\n")
                f.write(f"**采集时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**采集关键词**: {', '.join(self.config.KEYWORDS)}\n")
                f.write(f"**爆款标准**: 点赞数 ≥ {self.config.MIN_LIKES}\n")
                f.write(f"**总计**: {len(self.collected_notes)} 篇\n\n")
                f.write("---\n\n")
                
                # 按关键词分组
                from itertools import groupby
                sorted_notes = sorted(self.collected_notes, key=lambda x: x["keyword"])
                
                for keyword, notes in groupby(sorted_notes, key=lambda x: x["keyword"]):
                    notes_list = list(notes)
                    f.write(f"## 🏷️ {keyword}\n\n")
                    f.write(f"共 {len(notes_list)} 篇\n\n")
                    
                    for i, note in enumerate(notes_list, 1):
                        f.write(f"### {i}. {note['title']}\n\n")
                        f.write(f"- **作者**: {note['author']}\n")
                        f.write(f"- **点赞**: {note['likes']} | **收藏**: {note['collects']} | **评论**: {note['comments']}\n")
                        f.write(f"- **发布**: {note['publish_time']}\n")
                        f.write(f"- **链接**: [{note['link']}]({note['link']})\n\n")
                        f.write("---\n\n")
            
            print(f"📝 Markdown 文件已保存：{filename}")
            
        except Exception as e:
            print(f"❌ Markdown 保存失败：{e}")


# ==================== 定时任务配置 ====================
def setup_weekly_task():
    """配置 Windows 定时任务（每周执行一次）"""
    import subprocess
    
    script_path = Path(__file__).absolute()
    task_name = "Xiaohongshu_Collector_Weekly"
    
    # 创建批处理文件
    bat_content = f'''@echo off
chcp 65001 >nul
cd /d "{script_path.parent}"
python "{script_path}"
pause
'''
    
    bat_path = script_path.parent / "run_collector.bat"
    with open(bat_path, 'w', encoding='gbk') as f:
        f.write(bat_content)
    
    print(f"\n💡 已创建批处理文件：{bat_path}")
    print(f"\n要设置每周自动运行，请在命令行执行以下命令：")
    print(f"schtasks /Create /TN \"{task_name}\" /Tr \"'{bat_path}'\" /F /SC WEEKLY /D MON /ST 09:00")
    print(f"\n这将设置每周一上午 9 点自动执行采集任务")


# ==================== 主函数 ====================
async def main():
    """主函数"""
    config = Config()
    collector = XiaohongshuCollector(config)
    await collector.collect()


if __name__ == "__main__":
    # 检查依赖
    try:
        import playwright
    except ImportError:
        print("❌ 缺少依赖库 playwright")
        print("请运行：pip install playwright")
        print("然后运行：playwright install chromium")
        sys.exit(1)
    
    # 运行采集
    asyncio.run(main())
